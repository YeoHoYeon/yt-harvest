"""URL을 보고 모드 자동 감지."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Mode = Literal["video", "channel_videos", "channel_shorts", "playlist"]


@dataclass(frozen=True)
class TargetURL:
    raw: str
    mode: Mode
    canonical: str  # yt-dlp가 먹는 형태


_VIDEO_PATTERNS = [
    re.compile(r"^https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})"),
    re.compile(r"^https?://youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"^https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})"),
]
_CHANNEL_SHORTS = re.compile(
    r"^(https?://(?:www\.)?youtube\.com/(?:@[^/?\s]+|channel/UC[A-Za-z0-9_-]+))/shorts/?"
)
_CHANNEL_BASE = re.compile(
    r"^(https?://(?:www\.)?youtube\.com/(?:@[^/?\s]+|channel/UC[A-Za-z0-9_-]+))"
)
_PLAYLIST = re.compile(r"[?&]list=([A-Za-z0-9_-]+)")


def detect(url: str) -> TargetURL:
    url = url.strip()
    if not url:
        raise ValueError("빈 URL")

    # 단일 영상 (쇼츠 단일 URL 포함)
    for pat in _VIDEO_PATTERNS:
        m = pat.search(url)
        if m:
            vid = m.group(1)
            return TargetURL(
                raw=url,
                mode="video",
                canonical=f"https://www.youtube.com/watch?v={vid}",
            )

    # 재생목록
    pl = _PLAYLIST.search(url)
    if pl and "list=" in url and "/playlist" in url:
        return TargetURL(raw=url, mode="playlist", canonical=url)

    # 채널 쇼츠
    cs = _CHANNEL_SHORTS.match(url)
    if cs:
        return TargetURL(
            raw=url,
            mode="channel_shorts",
            canonical=f"{cs.group(1)}/shorts",
        )

    # 채널 일반 영상
    cb = _CHANNEL_BASE.match(url)
    if cb:
        return TargetURL(
            raw=url,
            mode="channel_videos",
            canonical=f"{cb.group(1)}/videos",
        )

    raise ValueError(f"지원하지 않는 URL: {url}")
