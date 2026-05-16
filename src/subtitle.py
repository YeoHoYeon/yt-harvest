"""yt-dlp로 한국어 자막 다운로드 + vtt → plain text."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


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
    """자막 받기. 반환: (transcript_text, source).

    source: "ko" (사람 단 자막) / "ko-orig" (자동 자막) / "none"
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    # ko (사람 단 자막)과 ko-orig (자동) 둘 다 시도
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        "ko.*,ko",
        "--sub-format",
        "vtt",
        "-o",
        str(out_dir / "%(id)s.%(ext)s"),
        url,
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    # 우선순위: ko (사람) > ko-orig (자동)
    ko_human = out_dir / f"{video_id}.ko.vtt"
    ko_auto = out_dir / f"{video_id}.ko-orig.vtt"

    text = ""
    source = "none"
    if ko_human.exists():
        text, source = _parse_vtt(ko_human), "ko"
    elif ko_auto.exists():
        text, source = _parse_vtt(ko_auto), "ko-orig"

    # vtt 원본 파일은 정리 (작업자에게 잡음)
    for v in (ko_human, ko_auto):
        if v.exists():
            v.unlink(missing_ok=True)

    return text, source
