# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for YtHarvest
import os
import sys
from pathlib import Path

block_cipher = None

# yt-dlp.exe를 venv에서 찾아서 동봉
_venv_scripts = Path('.venv') / ('Scripts' if sys.platform == 'win32' else 'bin')
_ytdlp_exe = _venv_scripts / ('yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp')
_datas = []
if _ytdlp_exe.exists():
    _datas.append((str(_ytdlp_exe), '.'))

a = Analysis(
    ['yt_harvest_entry.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'ttkbootstrap',
        'youtube_comment_downloader',
        'yt_dlp',
        'winotify',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YtHarvest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
