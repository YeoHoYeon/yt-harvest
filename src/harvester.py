"""영상 1개 처리 파이프라인: 메타 → 자막 → 댓글."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from . import comments, exporter, meta, subtitle


def process_video(
    video_id: str,
    root: Path,
    log: Callable[[str], None] = print,
    skip_if_exists: bool = True,
    title: Optional[str] = None,
    index: Optional[int] = None,
) -> dict:
    """영상 1개 처리. 결과 한 줄 dict 반환 (_stats.csv 행)."""
    # Resume: 같은 video_id 폴더 있으면 재사용
    existing = exporter.find_video_dir(root, video_id)
    if existing and skip_if_exists and (existing / "정보.json").exists() and (existing / "댓글.json").exists():
        log(f"  ⏭  {video_id} 이미 받음 → skip")
        # 기존 메타에서 stats row 복원
        try:
            import json

            m = json.loads((existing / "정보.json").read_text(encoding="utf-8"))
            v = m.get("video", {})
            # 자막 종류는 파일명에서 추론
            if (existing / "대본_사람단자막.txt").exists():
                src = "human"
            elif (existing / "대본_자동자막.txt").exists():
                src = "auto"
            else:
                src = "none"
            return _row_from_meta(v, src, existing)
        except Exception:
            pass  # 손상됐으면 다시 받음

    # 새로 받기 — 폴더는 메타 받은 후 제목 기반으로 생성
    vdir = exporter.video_dir(root, video_id, title=title, index=index)

    # 1. 메타
    log("  · 메타 받는 중...")
    raw_meta = meta.fetch_video_meta(video_id)
    if "_error" in raw_meta:
        log(f"  ⚠ 메타 실패: {raw_meta['_error']}")
        return {"id": video_id, "title": "(메타 실패)", "_error": raw_meta["_error"]}
    slim = meta.slim_video_meta(raw_meta)
    exporter.write_meta(vdir, slim)

    # 2. 자막 (raw_meta 재사용해서 extract_info 두 번 안 부름)
    log("  · 자막 받는 중...")
    text, source = subtitle.fetch(video_id, vdir, info=raw_meta)
    exporter.write_transcript(vdir, text, source)
    label = {"human": "사람단자막", "auto": "자동자막", "none": "없음"}[source]
    log(f"  · 자막 {len(text):,}자 ({label})")

    # 3. 댓글
    log("  · 댓글 받는 중...")
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
