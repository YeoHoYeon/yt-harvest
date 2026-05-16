"""GUI 상태 저장/복원. exe 옆에 gui_state.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def state_path() -> Path:
    if getattr(sys, "frozen", False):  # PyInstaller bundle
        base = Path(sys.executable).parent
    else:
        base = Path.cwd()
    return base / "gui_state.json"


def output_default() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "yt-harvest-output"
    return Path.cwd() / "yt-harvest-output"


def load() -> dict:
    p = state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(state: dict) -> None:
    try:
        state_path().write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
