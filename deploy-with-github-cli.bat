@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 ДЕПЛОЙ ЧЕРЕЗ GITHUB CLI
echo ========================================
echo.
echo Запуск PowerShell скрипта...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0deploy-with-github-cli.ps1"
pause

