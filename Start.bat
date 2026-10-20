@echo off
chcp 65001 >nul
title MingStudio - Universal AI Voice Workstation
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo   🎙️ MingStudio — 차세대 로컬 AI 음성 작업실 (Ming-3.0)
echo ============================================================
echo.

:: 1. 디렉터리 준비
if not exist "%ROOT%\data\models" mkdir "%ROOT%\data\models"
if not exist "%ROOT%\data\voices" mkdir "%ROOT%\data\voices"
if not exist "%ROOT%\data\outputs" mkdir "%ROOT%\data\outputs"
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

:: 2. 파이썬 환경 탐색 (포터블 런타임 우선)
set "PY_EXE="
if exist "%ROOT%\runtime\python.exe" (
    set "PY_EXE=%ROOT%\runtime\python.exe"
) else if exist "D:\VoiceStudio\OmniVoiceStudio-Portable\runtime\project\.venv\Scripts\python.exe" (
    set "PY_EXE=D:\VoiceStudio\OmniVoiceStudio-Portable\runtime\project\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

:: 3. 백엔드 데몬 구동
echo [1/2] 고성능 로컬 AI 백엔드 가동 중... (포트 4100)
start "" /b "%PY_EXE%" "%ROOT%\backend\app.py" > "%ROOT%\logs\backend.log" 2>&1
timeout /t 2 >nul

:: 4. 프리미엄 GUI 네이티브 앱 창 실행
echo [2/2] MingStudio 인터페이스 실행 중...
set "UI_PATH=%ROOT%\frontend\index.html"

start "" msedge.exe --app="file:///%UI_PATH:\=/%" --window-size=1360,880
if %ERRORLEVEL% neq 0 (
    start "" "file:///%UI_PATH:\=/%"
)

echo [✔] MingStudio가 정상적으로 실행되었습니다.
exit /b 0
