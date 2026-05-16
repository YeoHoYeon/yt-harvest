"""GitHub Releases 자동 업데이트.

작업자 입장에서 보이는 건 항상 YtHarvest.exe 하나뿐:
- 새 버전은 %LOCALAPPDATA%\\yt-harvest\\pending\\YtHarvest.exe 숨김 폴더에 받음
- updater.bat도 같은 숨김 폴더에서 생성·실행
- swap 후 자기 자신(bat)도 삭제
- 바탕화면엔 YtHarvest.exe 하나만 (버전만 바뀜)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from . import __version__

REPO = "YeoHoYeon/yt-harvest"
TIMEOUT = 5


def _pending_dir() -> Path:
    """%LOCALAPPDATA%\\yt-harvest\\pending\\ (작업자 눈에 안 보이는 위치)."""
    if sys.platform == "win32":
        base = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
    else:
        base = Path.home() / ".local" / "share"
    d = base / "yt-harvest" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _bat_content(target_exe: Path) -> str:
    """target_exe = swap 대상 (현재 메인 exe 위치)."""
    return (
        "@echo off\r\n"
        "REM YtHarvest auto-update swap (auto-generated)\r\n"
        ":retry\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        f'move /Y "%~dp0YtHarvest.exe" "{target_exe}" 2>nul\r\n'
        "if errorlevel 1 goto retry\r\n"
        f'start "" "{target_exe}"\r\n'
        'del /F /Q "%~dp0updater.bat" >nul 2>&1\r\n'
        "exit\r\n"
    )


def _write_bat(pending: Path, target_exe: Path) -> Path:
    bat = pending / "updater.bat"
    try:
        bat.write_text(_bat_content(target_exe), encoding="cp949", errors="replace")
    except Exception:
        try:
            bat.write_text(_bat_content(target_exe), encoding="utf-8")
        except Exception:
            pass
    return bat


def _api(url: str) -> Optional[dict]:
    if not url.startswith("https://"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "yt-harvest"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # nosec B310  noqa: S310
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _to_tuple(v: str) -> tuple[int, ...]:
    v = v.lstrip("v")
    parts: list[int] = []
    for x in v.split("."):
        try:
            parts.append(int(x))
        except ValueError:
            break
    return tuple(parts)


def _is_newer(remote: str, local: str) -> bool:
    try:
        return _to_tuple(remote) > _to_tuple(local)
    except Exception:
        return False


def _pick_asset(release: dict) -> Optional[dict]:
    for a in release.get("assets", []):
        name = a.get("name", "")
        if sys.platform == "win32" and name.endswith(".exe"):
            return a
        if sys.platform == "darwin" and name.endswith((".dmg", ".zip", ".app.zip")):
            return a
    return None


def check_and_update(log: Callable[[str], None] = print) -> None:
    """비동기로 안전하게 업데이트 체크."""

    def _work() -> None:
        # 개발 중(non-frozen)엔 스킵
        if not getattr(sys, "frozen", False):
            return
        release = _api(f"https://api.github.com/repos/{REPO}/releases/latest")
        if not release:
            return
        ver = release.get("tag_name", "")
        if not _is_newer(ver, __version__):
            return
        asset = _pick_asset(release)
        if not asset:
            log(f"⚠ 새 버전 {ver} 있음 (수동 다운로드: {release.get('html_url','')})")
            return

        dl_url = asset["browser_download_url"]
        if not dl_url.startswith("https://"):
            log("⚠ 안전하지 않은 다운로드 URL — 스킵")
            return

        log(f"↓ 새 버전 {ver} 백그라운드 다운로드 중...")
        pending = _pending_dir()
        new_path = pending / "YtHarvest.exe"
        try:
            urllib.request.urlretrieve(dl_url, new_path)  # nosec B310  noqa: S310
        except Exception as e:
            log(f"⚠ 다운로드 실패: {e}")
            return
        log("✓ 다음 실행 시 자동 적용")

    threading.Thread(target=_work, daemon=True).start()


def swap_on_startup() -> None:
    """pending 폴더에 새 exe 있으면 swap. 현재 프로세스는 종료."""
    if sys.platform != "win32":
        return
    if not getattr(sys, "frozen", False):
        return

    pending = _pending_dir()
    new_exe = pending / "YtHarvest.exe"
    if not new_exe.exists():
        return

    current_exe = Path(sys.executable)
    bat = _write_bat(pending, current_exe)
    if not bat.exists():
        return

    try:
        # DETACHED + CREATE_NO_WINDOW (cmd 창 안 띄움)
        FLAGS = 0x00000008 | 0x08000000
        subprocess.Popen(
            [str(bat)], shell=False, cwd=str(bat.parent), creationflags=FLAGS
        )
    except Exception:
        return  # 실패하면 그냥 현재 버전 계속
    sys.exit(0)
