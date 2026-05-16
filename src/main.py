"""진입점. 인자 없으면 GUI, URL 주면 CLI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import runner


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="yt-harvest", add_help=True)
    p.add_argument("url", nargs="?", help="유튜브 URL (없으면 GUI 실행)")
    p.add_argument("--limit", type=int, default=None, help="최대 영상 수 (디폴트: 전체)")
    p.add_argument(
        "--output",
        type=Path,
        default=Path("yt-harvest-output"),
        help="출력 폴더 (디폴트: ./yt-harvest-output/)",
    )
    args = p.parse_args(argv)

    if not args.url:
        # GUI 모드
        from . import gui
        return gui.main()

    # CLI 모드
    try:
        runner.run(args.url, args.output, limit=args.limit)
    except KeyboardInterrupt:
        print("\n[중단]")
        return 130
    except Exception as e:
        print(f"[에러] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
