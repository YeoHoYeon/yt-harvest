"""yt-dlp --dump-json으로 영상/채널 메타 받기."""
from __future__ import annotations

import json
import subprocess
from typing import Optional


def fetch_video_meta(video_id: str) -> dict:
    """영상 1개의 모든 메타. yt-dlp가 노출하는 모든 필드."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = ["yt-dlp", "--skip-download", "--dump-json", "--no-warnings", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return {"_error": r.stderr.strip()[:500]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        return {"_error": f"json parse: {e}"}


def slim_video_meta(raw: dict) -> dict:
    """meta.json에 저장할 깔끔한 dict."""
    if "_error" in raw:
        return raw
    return {
        "video": {
            "id": raw.get("id"),
            "title": raw.get("title"),
            "url": raw.get("webpage_url"),
            "upload_date": raw.get("upload_date"),  # YYYYMMDD
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
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--playlist-items",
        "0",
        "--dump-single-json",
        "--no-warnings",
        channel_url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return {"_error": r.stderr.strip()[:500]}
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        return {"_error": f"json parse: {e}"}
    return {
        "id": data.get("channel_id") or data.get("id"),
        "name": data.get("channel") or data.get("uploader") or data.get("title"),
        "url": data.get("channel_url") or data.get("webpage_url"),
        "subscriber_count": data.get("channel_follower_count"),
        "description": data.get("description"),
        "verified": data.get("channel_is_verified"),
    }


def list_videos(channel_url: str, limit: Optional[int] = None) -> list[dict]:
    """채널/플레이리스트의 영상 ID·제목·길이 리스트 (메타만)."""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
    ]
    if limit:
        cmd += ["--playlist-items", f"1-{limit}"]
    cmd.append(channel_url)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    items: list[dict] = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("id"):
            items.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "duration": d.get("duration"),
                    "url": d.get("url") or f"https://www.youtube.com/watch?v={d['id']}",
                }
            )
    return items
