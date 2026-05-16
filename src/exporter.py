"""영상 처리 결과를 폴더 + 파일들로 출력. 한글 친화 이름."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Optional


_INVALID_FS_CHARS = re.compile(r'[/\\?%*:|"<>]')


def safe_dirname(name: str, max_len: int = 60) -> str:
    s = _INVALID_FS_CHARS.sub("", name).strip()
    # 윈도우 trailing dot/space 금지
    s = s.rstrip(". ")
    return s[:max_len] or "untitled"


def video_dir(root: Path, video_id: str, title: Optional[str] = None, index: Optional[int] = None) -> Path:
    """영상 폴더. 이름 = {순번_}{제목_}{ID}. ID는 항상 끝에 (resume용)."""
    # 이미 받았으면 재사용
    for existing in root.glob(f"*{video_id}"):
        if existing.is_dir():
            return existing

    parts: list[str] = []
    if index is not None:
        parts.append(f"{index:03d}")
    if title:
        parts.append(safe_dirname(title, max_len=50))
    parts.append(video_id)
    name = "_".join(parts)
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_video_dir(root: Path, video_id: str) -> Optional[Path]:
    for existing in root.glob(f"*{video_id}"):
        if existing.is_dir():
            return existing
    return None


def write_meta(dir_: Path, meta: dict) -> None:
    (dir_ / "정보.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_transcript(dir_: Path, text: str, source: str) -> None:
    """source: 'human' (사람 단 자막) / 'auto' (자동 STT) / 'none' (없음)."""
    if source == "none":
        (dir_ / "대본_없음.txt").write_text(
            "이 영상은 자막이 없습니다.", encoding="utf-8"
        )
    elif source == "human":
        (dir_ / "대본_사람단자막.txt").write_text(text, encoding="utf-8")
    else:  # "auto"
        (dir_ / "대본_자동자막.txt").write_text(text, encoding="utf-8")


def write_comments(dir_: Path, items: list[dict]) -> None:
    (dir_ / "댓글.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cols_kr = ["구분", "작성자", "내용", "좋아요", "시간", "하트", "답글수", "댓글ID", "부모댓글ID"]
    with (dir_ / "댓글.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols_kr)
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
    (root / "채널정보.json").write_text(
        json.dumps(channel, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_stats_csv(root: Path, rows: list[dict]) -> None:
    if not rows:
        return
    cols_kr = [
        ("id", "영상ID"),
        ("title", "제목"),
        ("upload_date", "업로드일"),
        ("duration_sec", "길이(초)"),
        ("view_count", "조회수"),
        ("like_count", "좋아요"),
        ("comment_count", "댓글수(원본)"),
        ("transcript_source", "자막종류"),
        ("main_comments", "수집_메인댓글"),
        ("replies", "수집_답글"),
    ]
    with (root / "전체영상목록.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([kr for _, kr in cols_kr])
        for r in rows:
            w.writerow([r.get(k, "") for k, _ in cols_kr])


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
        "| # | 제목 | 업로드 | 조회수 | 좋아요 | 댓글 |"
    )
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, start=1):
        title = (r.get("title") or "").replace("|", "\\|")[:60]
        lines.append(
            f"| {i} | {title} | {r.get('upload_date') or ''} | "
            f"{r.get('view_count') or ''} | {r.get('like_count') or ''} | "
            f"{r.get('main_comments') or 0}+{r.get('replies') or 0} |"
        )
    (root / "목차.md").write_text("\n".join(lines), encoding="utf-8")
