@echo off
setlocal
cd /d "%~dp0"
title MingStudio - Push to GitHub
echo =======================================================================
echo   MingStudio - Push Clean Architecture to GitHub (origin/main)
echo =======================================================================
echo.
echo [*] Executing: git push -u origin main --force
echo [*] If prompted, please complete GitHub sign-in in your browser window...
echo.
git push -u origin main --force
if %errorlevel% equ 0 (
    echo.
    echo =======================================================================
    echo  [OK] Successfully pushed to https://github.com/hoperkim/MingStudio!
    echo =======================================================================
) else (
    echo.
    echo =======================================================================
    echo  [!] Push failed or cancelled (Exit code: %errorlevel%).
    echo =======================================================================
)
echo.
pause
