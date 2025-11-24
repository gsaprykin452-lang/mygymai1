@echo off
chcp 65001 >nul
title Деплой GymGenius AI через GitHub CLI
color 0A

echo.
echo ========================================
echo   🚀 ДЕПЛОЙ GYMGENIUS AI
echo ========================================
echo.
echo Этот скрипт:
echo   1. Инициализирует Git репозиторий
echo   2. Создаст GitHub репозиторий
echo   3. Загрузит код на GitHub
echo.
echo После этого вы сможете задеплоить на Render.com
echo.
pause

cd /d "%~dp0"

echo.
echo [1/5] Проверка GitHub CLI...
gh auth status
if errorlevel 1 (
    echo.
    echo ❌ Не авторизован в GitHub CLI
    echo Выполните: gh auth login
    pause
    exit /b 1
)
echo ✅ GitHub CLI авторизован
echo.

echo [2/5] Инициализация Git репозитория...
if not exist ".git" (
    git init
    git branch -M main
    echo ✅ Git репозиторий инициализирован
) else (
    echo ✅ Git репозиторий уже существует
)
echo.

echo [3/5] Добавление файлов...
git add .
echo ✅ Файлы добавлены
echo.

echo [4/5] Создание коммита...
git commit -m "Initial commit - готово к деплою на Render" 2>nul
if errorlevel 1 (
    git commit -m "Update: подготовка к деплою" -a 2>nul
)
echo ✅ Коммит создан
echo.

echo [5/5] Создание GitHub репозитория и загрузка кода...
echo Название репозитория: gymgenius-ai
echo.
gh repo create gymgenius-ai --public --source=. --remote=origin --push
if errorlevel 1 (
    echo.
    echo ⚠️  Репозиторий уже существует или ошибка при создании
    echo Попытка отправить код в существующий репозиторий...
    git remote remove origin 2>nul
    gh repo create gymgenius-ai --public --source=. --remote=origin --push
)
echo.

echo ========================================
echo ✅ ГОТОВО!
echo ========================================
echo.
echo 📋 Следующие шаги:
echo.
echo 1. Зайдите на https://render.com
echo 2. Войдите через GitHub
echo 3. Создайте новый Web Service
echo 4. Выберите репозиторий: Георгий/gymgenius-ai (или ваш GitHub username)
echo 5. Укажите Root Directory: fitness-ai-app/backend
echo 6. Добавьте переменную OPENAI_API_KEY
echo.
echo 📖 Подробные инструкции: GITHUB_DEPLOY_INSTRUCTIONS.md
echo.
pause

