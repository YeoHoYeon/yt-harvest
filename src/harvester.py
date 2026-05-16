"""영상 1개 처리 파이프라인: 메타 → 자막 → 댓글."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

from . import comments, exporter, meta, subtitle


def process_video(
    video_id: str,
    root: Path,
    log: Callable[[str], None] = print,
    skip_if_exists: bool = True,
) -> dict:
    """영상 1개 처리. 결과 한 줄 dict 반환 (_stats.csv 행)."""
    vdir = exporter.video_dir(root, video_id)

    # Resume: 이미 처리된 영상이면 skip
    done_marker = vdir / "meta.json"
    if skip_if_exists and done_marker.exists() and (vdir / "comments.json").exists():
        log(f"  ⏭  {video_id} 이미 받음 → skip")
        # 기존 메타에서 stats row 복원
        try:
            import json

            m = json.loads(done_marker.read_text(encoding="utf-8"))
            v = m.get("video", {})
            src = (vdir / "transcript_source.txt").read_text(encoding="utf-8").strip() if (vdir / "transcript_source.txt").exists() else ""
            return _row_from_meta(v, src, vdir)
        except Exception:
            pass  # 손상됐으면 다시 받음

    # 1. 메타
    log(f"  · 메타 받는 중...")
    raw_meta = meta.fetch_video_meta(video_id)
    if "_error" in raw_meta:
        log(f"  ⚠ 메타 실패: {raw_meta['_error']}")
        return {"id": video_id, "title": "(메타 실패)", "_error": raw_meta["_error"]}
    slim = meta.slim_video_meta(raw_meta)
    exporter.write_meta(vdir, slim)

    # 2. 자막
    log(f"  · 자막 받는 중...")
    text, source = subtitle.fetch(video_id, vdir)
    exporter.write_transcript(vdir, text, source)
    log(f"  · 자막 {len(text):,}자 ({source})")

    # 3. 댓글
    log(f"  · 댓글 받는 중...")
    cms = comments.fetch_all(video_id)
    main_n, reply_n = comments.stats(cms)
    exporter.write_comments(vdir, cms)
    log(f"  · 댓글 {main_n}개 + 답글 {reply_n}개")

    return _row_from_meta(slim["video"], source, vdir, main_n, reply_n)


def _row_from_meta(
    v: dict,
    source: str,
    vdir: Path,
    main_n: Optional[int] = None,
    reply_n: Optional[int] = None,
) -> dict:
    if main_n is None or reply_n is None:
        # 디스크에서 재계산
        try:
            import json

            cms = json.loads((vdir / "comments.json").read_text(encoding="utf-8"))
            main_n = sum(1 for c in cms if not c.get("is_reply"))
            reply_n = sum(1 for c in cms if c.get("is_reply"))
        except Exception:
            main_n = reply_n = 0
    return {
        "id": v.get("id"),
        "title": v.get("title"),
        "upload_date": v.get("upload_date"),
        "duration_sec": v.get("duration_sec"),
        "view_count": v.get("view_count"),
        "like_count": v.get("like_count"),
        "comment_count": v.get("comment_count"),
        "transcript_source": source,
        "main_comments": main_n,
        "replies": reply_n,
    }
