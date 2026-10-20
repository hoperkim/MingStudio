@echo off
chcp 65001 >nul
title MingStudio - GitHub Push Script
setlocal

echo ============================================================
echo   🚀 MingStudio -> GitHub (hoperkim/MingStudio) 푸시 스크립트
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Git 상태 확인 중...
git status -s

echo.
echo [2/3] 원격 저장소 (origin: https://github.com/hoperkim/MingStudio.git) 설정 중...
git remote remove origin 2>nul
git remote add origin https://github.com/hoperkim/MingStudio.git
git branch -M main

echo.
echo [3/3] GitHub main 브랜치로 푸시합니다...
echo (※ GitHub 웹사이트에서 'hoperkim/MingStudio' 리포지토리가 생성되어 있어야 합니다)
echo.

git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ============================================================
    echo   🎉 GitHub (https://github.com/hoperkim/MingStudio) 푸시 성공!
    echo ============================================================
) else (
    echo.
    echo [!] 푸시에 실패했습니다. GitHub 로그인 인증 또는 저장소 존재 여부를 확인해 주세요.
)

pause
