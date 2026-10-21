@echo off
setlocal
cd /d "%~dp0" 2>nul

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set "TRITON_CACHE_DIR=%~dp0data\.triton_cache"
set "BAILING_KDA_FUSED_RECURRENT=0"
set "BAILING_MLA_ATTN=sdpa"
set "MING_TINY_AUDIO_VAE_ATTN=sdpa"
set "FLA_USE_CUDA_KDA_FWD=0"
set "FLA_USE_CUDA_KDA_BWD=0"

echo =======================================================================
echo   MingStudio - AI Voice Workstation Launcher
echo =======================================================================
echo.

set "PY_BIN="

if exist "D:\whisperjav\python.exe" (
    set "PY_BIN=D:\whisperjav\python.exe"
    goto :START_APP
)

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_BIN=%~dp0.venv\Scripts\python.exe"
    goto :START_APP
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :START_APP
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :START_APP
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_BIN=python"
    goto :START_APP
)

echo [ERROR] Python 3.10+ was not found.
echo         Please install Python or verify PATH environment variable.
pause
exit /b 1

:START_APP
echo [OK] Python Engine: %PY_BIN%
echo [*] Launching MingStudio Backend Server (Smart Port Binding)...
echo [*] Edge Native App Mode will open automatically when ready...
echo.

"%PY_BIN%" "%~dp0backend\server.py" --launch-browser

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited with error code %errorlevel%.
    pause
)
