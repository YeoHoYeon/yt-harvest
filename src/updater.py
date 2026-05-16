"""GitHub Releases 자동 업데이트.

블로그봇 패턴:
- 시작 시 최신 릴리즈 체크
- 새 버전 있으면 .exe를 옆에 다운로드 (`YtHarvest_new.exe`)
- 다음 실행 시 updater.bat이 swap (윈도우만)
- 맥은 새 버전 알림만 (수동 다운로드)
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from . import __version__

REPO = "YeoHoYeon/yt-harvest"
TIMEOUT = 5


def _api(url: str) -> Optional[dict]:
    if not url.startswith("https://"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "yt-harvest"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # nosec B310  noqa: S310
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _to_tuple(v: str) -> tuple[int, ...]:
    v = v.lstrip("v")
    parts: list[int] = []
    for x in v.split("."):
        try:
            parts.append(int(x))
        except ValueError:
            break
    return tuple(parts)


def _is_newer(remote: str, local: str) -> bool:
    try:
        return _to_tuple(remote) > _to_tuple(local)
    except Exception:
        return False


def _pick_asset(release: dict) -> Optional[dict]:
    for a in release.get("assets", []):
        name = a.get("name", "")
        if sys.platform == "win32" and name.endswith(".exe"):
            return a
        if sys.platform == "darwin" and name.endswith((".dmg", ".zip", ".app.zip")):
            return a
    return None


def check_and_update(log: Callable[[str], None] = print) -> None:
    """비동기로 안전하게 업데이트 체크."""

    def _work() -> None:
        # 개발 중(non-frozen)엔 스킵
        if not getattr(sys, "frozen", False):
            return
        release = _api(f"https://api.github.com/repos/{REPO}/releases/latest")
        if not release:
            return
        ver = release.get("tag_name", "")
        if not _is_newer(ver, __version__):
            return
        asset = _pick_asset(release)
        if not asset:
            log(f"⚠ 새 버전 {ver} 있음 (수동 다운로드: {release.get('html_url','')})")
            return

        # 다운로드 (https만 허용)
        dl_url = asset["browser_download_url"]
        if not dl_url.startswith("https://"):
            log("⚠ 안전하지 않은 다운로드 URL — 스킵")
            return
        log(f"↓ 새 버전 {ver} 다운로드 중...")
        exe_dir = Path(sys.executable).parent
        new_path = exe_dir / "YtHarvest_new.exe"
        try:
            urllib.request.urlretrieve(dl_url, new_path)  # nosec B310  noqa: S310
        except Exception as e:
            log(f"⚠ 다운로드 실패: {e}")
            return
        log("✓ 새 버전 받음. 다음 실행 시 적용됨.")
        # updater.bat은 종료 시 또는 다음 실행 시 호출됨

    threading.Thread(target=_work, daemon=True).start()


def swap_on_startup() -> None:
    """exe 옆에 YtHarvest_new.exe가 있으면 updater.bat 호출해서 swap.

    호출 시점: GUI 진입 직전. swap 후엔 새 exe로 다시 실행되므로 이번 프로세스는 종료.
    """
    if sys.platform != "win32":
        return
    if not getattr(sys, "frozen", False):
        return
    exe_dir = Path(sys.executable).parent
    new_exe = exe_dir / "YtHarvest_new.exe"
    if not new_exe.exists():
        return
    bat = exe_dir / "updater.bat"
    if not bat.exists():
        return
    # 비동기로 bat 실행 후 이번 프로세스 종료 (shell injection 방지 위해 list 형태)
    try:
        DETACHED = 0x00000008  # subprocess.DETACHED_PROCESS (win32only)
        subprocess.Popen(
            [str(bat)], shell=False, cwd=str(bat.parent), creationflags=DETACHED
        )
    except Exception:
        return  # 실패하면 그냥 현재 버전 계속 실행
    sys.exit(0)
