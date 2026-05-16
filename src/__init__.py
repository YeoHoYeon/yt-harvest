__version__ = "0.1.2"

# PyInstaller frozen 환경: 동봉된 yt-dlp.exe / ffmpeg.exe를 subprocess가 찾도록 PATH 등록
import os as _os
import sys as _sys

if getattr(_sys, "frozen", False):
    _bundle = getattr(_sys, "_MEIPASS", _os.path.dirname(_sys.executable))
    _os.environ["PATH"] = _bundle + _os.pathsep + _os.environ.get("PATH", "")

