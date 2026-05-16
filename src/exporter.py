"""영상 처리 결과를 폴더 + 파일들로 출력."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Optional


_INVALID_FS_CHARS = re.compile(r'[/\\?%*:|"<>]')


def safe_dirname(name: str, max_len: int = 60) -> str:
    s = _INVALID_FS_CHARS.sub("", name).strip()
    return s[:max_len] or "untitled"


def video_dir(root: Path, video_id: str) -> Path:
    d = root / video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_meta(dir_: Path, meta: dict) -> None:
    (dir_ / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_transcript(dir_: Path, text: str, source: str) -> None:
    (dir_ / "transcript.txt").write_text(text, encoding="utf-8")
    (dir_ / "transcript_source.txt").write_text(source, encoding="utf-8")


def write_comments(dir_: Path, items: list[dict]) -> None:
    (dir_ / "comments.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cols = [
        "kind",
        "author",
        "text",
        "votes",
        "time",
        "heart",
        "reply_count",
        "cid",
        "parent_cid",
    ]
    with (dir_ / "comments.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for c in items:
            w.writerow(
                [
                    "답글" if c["is_reply"] else "메인",
                    c.get("author"),
                    (c.get("text") or "").replace("\n", " "),
                    c.get("votes"),
                    c.get("time"),
                    "♥" if c.get("heart") else "",
                    c.get("reply_count"),
                    c.get("cid"),
                    c.get("parent_cid") or "",
                ]
            )


def write_channel(root: Path, channel: dict) -> None:
    (root / "channel.json").write_text(
        json.dumps(channel, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_stats_csv(root: Path, rows: list[dict]) -> None:
    if not rows:
        return
    cols = [
        "id",
        "title",
        "upload_date",
        "duration_sec",
        "view_count",
        "like_count",
        "comment_count",
        "transcript_source",
        "main_comments",
        "replies",
    ]
    with (root / "_stats.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])


def write_index_md(root: Path, channel: Optional[dict], rows: list[dict]) -> None:
    lines = ["# 수확 결과", ""]
    if channel:
        lines.append(f"- 채널: **{channel.get('name')}**")
        if channel.get("subscriber_count") is not None:
            lines.append(f"- 구독자: {channel['subscriber_count']:,}")
        if channel.get("url"):
            lines.append(f"- URL: {channel['url']}")
        lines.append("")
    lines.append(f"- 영상 수: {len(rows)}")
    lines.append("")
    lines.append(
        "| ID | 제목 | 업로드 | 길이(초) | 조회수 | 좋아요 | 댓글수 | 자막 |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            "| {id} | {title} | {date} | {dur} | {views} | {likes} | {cmts} | {src} |".format(
                id=r.get("id"),
                title=(r.get("title") or "").replace("|", "\\|")[:60],
                date=r.get("upload_date") or "",
                dur=r.get("duration_sec") or "",
                views=r.get("view_count") or "",
                likes=r.get("like_count") or "",
                cmts=r.get("comment_count") or "",
                src=r.get("transcript_source") or "",
            )
        )
    (root / "_index.md").write_text("\n".join(lines), encoding="utf-8")
