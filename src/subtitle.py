"""yt-dlp Python API로 한국어 자막 다운로드 + vtt → plain text."""
from __future__ import annotations

import re
from pathlib import Path

from yt_dlp import YoutubeDL


class _SilentLogger:
    """yt_dlp 콘솔 출력 완전 차단 (frozen exe에서 cmd 창 뜨는 거 방지)."""

    def debug(self, msg: str) -> None: pass
    def info(self, msg: str) -> None: pass
    def warning(self, msg: str) -> None: pass
    def error(self, msg: str) -> None: pass


_VTT_TAG_RE = re.compile(r"<[^>]+>")


def _parse_vtt(vtt_path: Path) -> str:
    text = vtt_path.read_text(encoding="utf-8", errors="ignore")
    seen: set[str] = set()
    out: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in s:
            continue
        s = _VTT_TAG_RE.sub("", s).replace("&nbsp;", " ").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return "\n".join(out)


def fetch(video_id: str, out_dir: Path) -> tuple[str, str]:
    """자막 받기. 반환: (transcript_text, source: "ko"/"ko-orig"/"none")."""
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["ko", "ko-orig"],
        "subtitlesformat": "vtt",
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": _SilentLogger(),
    }
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception:
        pass  # 자막 없을 수 있음

    ko_human = out_dir / f"{video_id}.ko.vtt"
    ko_auto = out_dir / f"{video_id}.ko-orig.vtt"

    text = ""
    source = "none"
    if ko_human.exists():
        text, source = _parse_vtt(ko_human), "ko"
    elif ko_auto.exists():
        text, source = _parse_vtt(ko_auto), "ko-orig"

    for v in (ko_human, ko_auto):
        if v.exists():
            v.unlink(missing_ok=True)

    return text, source
