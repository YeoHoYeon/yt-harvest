"""yt-dlp Python API로 한국어 자막 다운로드 + vtt → plain text.

정확한 구분:
- "human" = 영상 주인이 직접 단 자막 (info['subtitles']['ko*'])
- "auto"  = 유튜브 자동 STT (info['automatic_captions']['ko*'])
- "none"  = 둘 다 없음
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from yt_dlp import YoutubeDL


class _SilentLogger:
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


def _find_ko(d: dict) -> Optional[str]:
    """ko, ko-KR, ko-Hang 등 한국어 자막 코드 찾기."""
    for k in d:
        if k.startswith("ko"):
            return k
    return None


def fetch(
    video_id: str, out_dir: Path, info: Optional[dict] = None
) -> tuple[str, str]:
    """자막 받기. 반환: (transcript_text, source: "human"/"auto"/"none")."""
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"

    # info 없으면 새로 받음 (meta.fetch_video_meta 호출 안 한 경우)
    if info is None:
        try:
            with YoutubeDL(
                {
                    "skip_download": True,
                    "quiet": True,
                    "no_warnings": True,
                    "noprogress": True,
                    "logger": _SilentLogger(),
                }
            ) as ydl:
                info = ydl.extract_info(url, download=False) or {}
        except Exception:
            info = {}

    human_lang = _find_ko(info.get("subtitles") or {})
    auto_lang = _find_ko(info.get("automatic_captions") or {})

    if not human_lang and not auto_lang:
        return "", "none"

    # 사람 자막 우선, 없으면 자동
    use_human = bool(human_lang)
    lang = human_lang or auto_lang

    opts = {
        "skip_download": True,
        "writesubtitles": use_human,
        "writeautomaticsub": not use_human,
        "subtitleslangs": [lang],
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
        return "", "none"

    # 다운로드된 vtt 찾기
    text = ""
    for f in out_dir.glob(f"{video_id}*.vtt"):
        text = _parse_vtt(f)
        f.unlink(missing_ok=True)
        break

    return text, ("human" if use_human else "auto")
