"""yt-dlp Python API로 영상/채널 메타 받기."""
from __future__ import annotations

from typing import Optional

from yt_dlp import YoutubeDL

from .subtitle import _SilentLogger


def fetch_video_meta(video_id: str) -> dict:
    """영상 1개의 모든 메타."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with YoutubeDL(
            {"quiet": True, "no_warnings": True, "skip_download": True, "noprogress": True, "logger": _SilentLogger()}
        ) as ydl:
            return ydl.extract_info(url, download=False) or {"_error": "empty"}
    except Exception as e:
        return {"_error": str(e)[:500]}


def slim_video_meta(raw: dict) -> dict:
    if "_error" in raw:
        return raw
    return {
        "video": {
            "id": raw.get("id"),
            "title": raw.get("title"),
            "url": raw.get("webpage_url"),
            "upload_date": raw.get("upload_date"),
            "release_date": raw.get("release_date"),
            "duration_sec": raw.get("duration"),
            "view_count": raw.get("view_count"),
            "like_count": raw.get("like_count"),
            "comment_count": raw.get("comment_count"),
            "description": raw.get("description"),
            "tags": raw.get("tags") or [],
            "categories": raw.get("categories") or [],
            "chapters": raw.get("chapters") or [],
            "thumbnail": raw.get("thumbnail"),
            "language": raw.get("language"),
            "is_live": raw.get("is_live"),
            "was_live": raw.get("was_live"),
            "live_status": raw.get("live_status"),
            "age_limit": raw.get("age_limit"),
            "availability": raw.get("availability"),
        },
        "channel": {
            "id": raw.get("channel_id"),
            "name": raw.get("channel") or raw.get("uploader"),
            "url": raw.get("channel_url") or raw.get("uploader_url"),
            "subscriber_count": raw.get("channel_follower_count"),
            "verified": raw.get("channel_is_verified"),
        },
    }


def fetch_channel_meta(channel_url: str) -> dict:
    """채널 자체 메타 (구독자, 채널 설명 등)."""
    try:
        with YoutubeDL(
            {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": "in_playlist",
                "playlistend": 1,
            }
        ) as ydl:
            data = ydl.extract_info(channel_url, download=False) or {}
    except Exception as e:
        return {"_error": str(e)[:500]}
    return {
        "id": data.get("channel_id") or data.get("id"),
        "name": data.get("channel") or data.get("uploader") or data.get("title"),
        "url": data.get("channel_url") or data.get("webpage_url"),
        "subscriber_count": data.get("channel_follower_count"),
        "description": data.get("description"),
        "verified": data.get("channel_is_verified"),
    }


def list_videos(channel_url: str, limit: Optional[int] = None) -> list[dict]:
    """채널/플레이리스트의 영상 ID·제목·길이 리스트."""
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
    }
    if limit:
        opts["playlistend"] = limit
    try:
        with YoutubeDL(opts) as ydl:
            data = ydl.extract_info(channel_url, download=False) or {}
    except Exception:
        return []
    entries = data.get("entries") or []
    out: list[dict] = []
    for e in entries:
        if not e or not e.get("id"):
            continue
        out.append(
            {
                "id": e["id"],
                "title": e.get("title"),
                "duration": e.get("duration"),
                "url": e.get("url")
                or f"https://www.youtube.com/watch?v={e['id']}",
            }
        )
    return out
