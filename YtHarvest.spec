# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for YtHarvest

block_cipher = None

a = Analysis(
    ['yt_harvest_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ttkbootstrap',
        'youtube_comment_downloader',
        'yt_dlp',
        'winotify',  # Windows 한정 — 맥 빌드 시 noop
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
    console=False,         # GUI 앱이라 콘솔 안 띄움
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
