@echo off
REM yt-harvest 윈도우 빌드 스크립트
REM 사전: python -m venv .venv & .venv\Scripts\activate & pip install -r requirements.txt pyinstaller

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv가 없어. 먼저 venv 만들고 pip install -r requirements.txt 해.
  exit /b 1
)

call .venv\Scripts\activate.bat

echo [1/3] 클린...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] PyInstaller 빌드...
pyinstaller YtHarvest.spec --clean
if errorlevel 1 (
  echo [ERROR] 빌드 실패
  exit /b 1
)

echo [3/3] 완료. dist\YtHarvest.exe
dir dist\YtHarvest.exe
