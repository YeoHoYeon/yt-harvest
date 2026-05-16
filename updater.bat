@echo off
REM YtHarvest 자동 업데이트 스왑 스크립트
REM YtHarvest.exe가 종료된 후 새 exe로 교체하고 재시작

timeout /t 2 /nobreak >nul

REM 현재 exe 백업 + 새 exe로 교체
if exist "YtHarvest_old.exe" del /F /Q "YtHarvest_old.exe" >nul 2>&1
if exist "YtHarvest.exe" ren "YtHarvest.exe" "YtHarvest_old.exe" >nul 2>&1
ren "YtHarvest_new.exe" "YtHarvest.exe" >nul 2>&1

REM 새 exe 실행
start "" "YtHarvest.exe"

exit
