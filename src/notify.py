"""OS별 끝났을 때 토스트 알림."""
from __future__ import annotations

import subprocess
import sys


def toast(title: str, message: str) -> None:
    try:
        if sys.platform == "win32":
            from winotify import Notification  # type: ignore
            n = Notification(app_id="yt-harvest", title=title, msg=message)
            n.show()
        elif sys.platform == "darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], capture_output=True)
        # linux 등은 무시
    except Exception:
        pass  # 알림 실패는 무시
