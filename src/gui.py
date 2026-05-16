"""yt-harvest GUI. 단순 단계형. 한눈에 보고 바로 쓸 수 있게."""
from __future__ import annotations

import queue
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, DISABLED, END, LEFT, NORMAL, RIGHT, X, Y

from . import config, notify, runner, updater


LIMIT_CHOICES = ["전체", "100", "50", "20", "10", "5"]


class App:
    def __init__(self) -> None:
        updater.swap_on_startup()
        self.root = ttk.Window(themename="darkly", title="yt-harvest")
        self.root.geometry("520x500")
        self.root.minsize(480, 460)

        self._stop_flag = threading.Event()
        self._worker: threading.Thread | None = None
        self._log_q: queue.Queue[tuple[str, str]] = queue.Queue()  # (kind, msg)
        self._last_output_dir: Path | None = None
        self._total = 0
        self._done = 0
        self._log_open = False

        state = config.load()
        self._build_ui(state)
        self.root.after(100, self._drain_log_q)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        updater.check_and_update(self._verbose)

    # ---------- UI ----------

    def _build_ui(self, state: dict) -> None:
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill=BOTH, expand=True)

        # 헤더
        ttk.Label(outer, text="yt-harvest", font=("", 16, "bold")).pack(
            anchor="w", pady=(0, 16)
        )

        # ① URL
        ttk.Label(outer, text="①  URL", font=("", 11, "bold")).pack(anchor="w")
        self.url_var = ttk.StringVar(value=state.get("url", ""))
        url_entry = ttk.Entry(outer, textvariable=self.url_var, font=("", 11))
        url_entry.pack(fill=X, pady=(4, 14), ipady=4)

        # ② 영상 수
        ttk.Label(outer, text="②  개수", font=("", 11, "bold")).pack(anchor="w")
        self.limit_var = ttk.StringVar(value=state.get("limit", "전체"))
        ttk.Combobox(
            outer,
            textvariable=self.limit_var,
            values=LIMIT_CHOICES,
            state="readonly",
            font=("", 11),
        ).pack(fill=X, pady=(4, 18), ipady=2)

        # ③ 시작 (큰 버튼)
        self.start_btn = ttk.Button(
            outer,
            text="시작",
            command=self._start,
            bootstyle="success",
        )
        self.start_btn.pack(fill=X, ipady=8, pady=(0, 6))
        self.stop_btn = ttk.Button(
            outer,
            text="중지",
            command=self._stop,
            bootstyle="warning-outline",
            state=DISABLED,
        )
        self.stop_btn.pack(fill=X, ipady=4, pady=(0, 14))

        # 진행률
        self.pb = ttk.Progressbar(outer, mode="determinate", maximum=100, value=0)
        self.pb.pack(fill=X, pady=(0, 4))
        self.status_var = ttk.StringVar(value="대기")
        ttk.Label(outer, textvariable=self.status_var, bootstyle="secondary").pack(
            anchor="w"
        )

        # 자세한 로그 (접기)
        self.toggle_btn = ttk.Button(
            outer,
            text="▷  로그",
            command=self._toggle_log,
            bootstyle="link",
        )
        self.toggle_btn.pack(anchor="w", pady=(8, 0))
        self.log_frame = ttk.Frame(outer)
        # 처음엔 닫혀 있음
        self.log_text = ttk.Text(self.log_frame, height=8, font=("Menlo", 9))
        sb = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set, state=DISABLED)
        sb.pack(side=RIGHT, fill=Y)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

    def _toggle_log(self) -> None:
        if self._log_open:
            self.log_frame.pack_forget()
            self.toggle_btn.configure(text="▷  로그")
            self._log_open = False
        else:
            self.log_frame.pack(fill=BOTH, expand=True, pady=(6, 0))
            self.toggle_btn.configure(text="▽  로그")
            self._log_open = True

    # ---------- 실행 ----------

    def _start(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("yt-harvest", "URL 비었음")
            return

        out = config.output_default()
        out.mkdir(parents=True, exist_ok=True)

        limit_str = self.limit_var.get()
        limit = None if limit_str == "전체" else int(limit_str)

        config.save({"url": url, "limit": limit_str})

        self._stop_flag.clear()
        self._set_running(True)
        self._clear_log()
        self._total = 0
        self._done = 0
        self._verbose(f"시작: {url}")

        self._worker = threading.Thread(
            target=self._run_thread, args=(url, out, limit), daemon=True
        )
        self._worker.start()

    def _run_thread(self, url: str, out: Path, limit: int | None) -> None:
        try:
            result_dir = runner.run(
                url,
                out,
                limit=limit,
                log=self._log_callback,
                should_stop=self._stop_flag.is_set,
            )
            self._last_output_dir = result_dir
            self._log_q.put(("done", str(result_dir)))
            notify.toast("yt-harvest", "수집 완료")
        except Exception as e:
            self._log_q.put(("error", str(e)))
            notify.toast("yt-harvest", f"실패: {e}")
        finally:
            self.root.after(0, lambda: self._set_running(False))

    def _log_callback(self, msg: str) -> None:
        """runner.run이 호출하는 로그. 단순/상세 둘 다 분기."""
        s = msg.strip()
        # 채널 N개 영상
        if "개 영상" in s and s.startswith("[채널]"):
            try:
                self._total = int("".join(c for c in s if c.isdigit()))
            except ValueError:
                pass
            self._update_status()
        # [n/m] 패턴
        elif s.startswith("[") and "/" in s.split("]")[0]:
            try:
                inner = s[1 : s.index("]")]
                a, b = inner.split("/")
                self._done = int(a)
                self._total = int(b)
                title = s.split("]", 1)[1].strip()
                # vid 11자 + 공백 + 제목
                parts = title.split(maxsplit=1)
                short = parts[1] if len(parts) > 1 else parts[0]
                self._status_text(short[:50])
            except (ValueError, IndexError):
                pass
            self._update_status()
        self._verbose(s)

    def _verbose(self, s: str) -> None:
        self._log_q.put(("log", s))

    def _stop(self) -> None:
        if messagebox.askyesno("yt-harvest", "중지?"):
            self._stop_flag.set()
            self._verbose("중지 요청 - 현재 영상 끝나면 멈춤")

    def _set_running(self, running: bool) -> None:
        if running:
            self.start_btn.configure(state=DISABLED)
            self.stop_btn.configure(state=NORMAL)
            self.status_var.set("준비 중")
        else:
            self.start_btn.configure(state=NORMAL)
            self.stop_btn.configure(state=DISABLED)
            if self._last_output_dir:
                self.status_var.set("✓  완료")
                self._open_in_finder(self._last_output_dir)
            else:
                self.status_var.set("대기")

    def _update_status(self) -> None:
        if self._total:
            pct = int(self._done * 100 / self._total)
            self.pb.configure(value=pct)

    def _status_text(self, t: str) -> None:
        if self._total:
            self.status_var.set(f"{self._done}/{self._total}  ·  {t}")
        else:
            self.status_var.set(t)

    @staticmethod
    def _open_in_finder(path: Path) -> None:
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass

    # ---------- 로그 ----------

    def _drain_log_q(self) -> None:
        try:
            while True:
                kind, msg = self._log_q.get_nowait()
                if kind == "log":
                    self.log_text.configure(state=NORMAL)
                    self.log_text.insert(END, msg + "\n")
                    self.log_text.see(END)
                    self.log_text.configure(state=DISABLED)
                elif kind == "done":
                    pass  # _set_running에서 처리
                elif kind == "error":
                    messagebox.showerror("yt-harvest", f"오류:\n\n{msg}")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._drain_log_q)

    def _clear_log(self) -> None:
        self.log_text.configure(state=NORMAL)
        self.log_text.delete("1.0", END)
        self.log_text.configure(state=DISABLED)
        self.pb.configure(value=0)

    # ---------- 종료 ----------

    def _on_close(self) -> None:
        if self._worker and self._worker.is_alive():
            if not messagebox.askyesno("yt-harvest", "수집 중. 끝낼래?"):
                return
            self._stop_flag.set()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    App().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
