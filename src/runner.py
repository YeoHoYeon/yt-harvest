"""전체 실행 흐름. URL 1개를 받아서 결과 폴더 통째로 생성."""
from __future__ import annotations

import datetime as dt
import random
import time
from pathlib import Path
from typing import Callable, Optional

from . import exporter, harvester, meta, url_detect


# 보수적 차단 회피 (스피드 < 안전)
SLEEP_BETWEEN_VIDEOS = (3, 8)       # 초 (랜덤)
SLEEP_EVERY_N = 50                   # N개마다
COOLDOWN_AT_N = (45, 75)             # cool-down 초 (랜덤)


def run(
    url: str,
    output_root: Path,
    limit: Optional[int] = None,
    log: Callable[[str], None] = print,
    should_stop: Callable[[], bool] = lambda: False,
) -> Path:
    target = url_detect.detect(url)
    log(f"[모드] {target.mode}")

    is_single = target.mode == "video"

    # 채널 정보
    channel_info: Optional[dict] = None
    if not is_single:
        log("[채널] 정보 받는 중...")
        channel_info = meta.fetch_channel_meta(target.canonical)
        if "_error" in channel_info:
            log(f"⚠ 채널 정보 실패: {channel_info['_error']}")
            channel_info = None

    # 영상 리스트
    if is_single:
        # URL에서 video id 추출
        import re
        m = re.search(r"v=([A-Za-z0-9_-]{11})", target.canonical)
        if not m:
            raise ValueError(f"video id 추출 실패: {target.canonical}")
        video_list = [{"id": m.group(1), "title": "", "duration": None}]
    else:
        log("[채널] 영상 리스트 받는 중...")
        video_list = meta.list_videos(target.canonical, limit=limit)
        log(f"[채널] {len(video_list)}개 영상")

    # 출력 폴더
    folder_name = _output_folder_name(target, channel_info)
    run_root = output_root / folder_name
    run_root.mkdir(parents=True, exist_ok=True)
    if channel_info:
        exporter.write_channel(run_root, channel_info)

    log(f"[저장] {run_root}")
    log("")

    # 영상 순회
    rows: list[dict] = []
    for i, item in enumerate(video_list, start=1):
        if should_stop():
            log("[중지] 사용자 중단")
            break

        vid = item["id"]
        title = (item.get("title") or "")[:50]
        log(f"[{i}/{len(video_list)}] {vid}  {title}")
        try:
            row = harvester.process_video(vid, run_root, log=log)
            rows.append(row)
        except Exception as e:
            log(f"  ✗ 실패: {e}")
            rows.append({"id": vid, "title": title, "_error": str(e)})

        # cool-down
        if i % SLEEP_EVERY_N == 0 and i < len(video_list):
            cd = random.uniform(*COOLDOWN_AT_N)
            log(f"[cool-down] {cd:.0f}초 쉬는 중 (영상 {SLEEP_EVERY_N}개마다)")
            _sleep(cd, should_stop)
        elif i < len(video_list):
            s = random.uniform(*SLEEP_BETWEEN_VIDEOS)
            _sleep(s, should_stop)

    # 인덱스 + stats
    exporter.write_stats_csv(run_root, rows)
    exporter.write_index_md(run_root, channel_info, rows)
    log("")
    log(f"[완료] {len(rows)}개 처리. {run_root}")
    return run_root


def _output_folder_name(target: url_detect.TargetURL, channel: Optional[dict]) -> str:
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M")
    if target.mode == "video":
        base = "단일영상"
    elif channel and channel.get("name"):
        base = exporter.safe_dirname(channel["name"])
        if target.mode == "channel_shorts":
            base += "_쇼츠"
        elif target.mode == "playlist":
            base += "_재생목록"
    else:
        base = target.mode
    return f"{base}_{ts}"


def _sleep(seconds: float, should_stop: Callable[[], bool]) -> None:
    end = time.time() + seconds
    while time.time() < end:
        if should_stop():
            return
        time.sleep(min(0.5, end - time.time()))
