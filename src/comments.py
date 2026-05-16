"""youtube-comment-downloader로 댓글+답글 전체 받기."""
from __future__ import annotations

from typing import Iterator

from youtube_comment_downloader import SORT_BY_POPULAR, YoutubeCommentDownloader

_dl = YoutubeCommentDownloader()


def fetch_all(video_id: str) -> list[dict]:
    """좋아요순 메인 댓글 + 답글 모두 list로 반환.

    each item: cid, is_reply, parent_cid, author, text, votes, time, heart, reply_count
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    out: list[dict] = []
    for c in _dl.get_comments_from_url(url, sort_by=SORT_BY_POPULAR, language="ko"):
        cid = c.get("cid", "")
        is_reply = bool(c.get("reply"))
        parent_cid = cid.split(".")[0] if is_reply and "." in cid else None
        out.append(
            {
                "cid": cid,
                "is_reply": is_reply,
                "parent_cid": parent_cid,
                "author": c.get("author"),
                "text": c.get("text"),
                "votes": c.get("votes"),
                "time": c.get("time"),
                "heart": c.get("heart"),
                "reply_count": c.get("replies"),
            }
        )
    return out


def stats(items: list[dict]) -> tuple[int, int]:
    """(메인 수, 답글 수)"""
    main = sum(1 for x in items if not x["is_reply"])
    reply = sum(1 for x in items if x["is_reply"])
    return main, reply
