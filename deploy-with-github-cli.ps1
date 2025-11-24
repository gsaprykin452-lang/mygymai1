# Скрипт для деплоя через GitHub CLI
# Запустите: powershell -ExecutionPolicy Bypass -File deploy-with-github-cli.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 ДЕПЛОЙ ЧЕРЕЗ GITHUB CLI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Переходим в директорию проекта
$projectPath = $PSScriptRoot
Set-Location $projectPath

Write-Host "📁 Текущая директория: $projectPath" -ForegroundColor Green
Write-Host ""

# Проверяем авторизацию GitHub
Write-Host "🔐 Проверка авторизации GitHub..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Не авторизован в GitHub CLI" -ForegroundColor Red
    Write-Host "Выполните: gh auth login" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Авторизован в GitHub" -ForegroundColor Green
Write-Host ""

# Проверяем, инициализирован ли git репозиторий
Write-Host "🔍 Проверка Git репозитория..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "📦 Инициализация Git репозитория..." -ForegroundColor Yellow
    git init
    git branch -M main
    Write-Host "✅ Git репозиторий инициализирован" -ForegroundColor Green
} else {
    Write-Host "✅ Git репозиторий уже существует" -ForegroundColor Green
}
Write-Host ""

# Добавляем все файлы
Write-Host "📝 Добавление файлов..." -ForegroundColor Yellow
git add .
Write-Host "✅ Файлы добавлены" -ForegroundColor Green
Write-Host ""

# Проверяем, есть ли коммиты
Write-Host "💾 Проверка коммитов..." -ForegroundColor Yellow
$commitCount = (git rev-list --count HEAD 2>$null)
if ($LASTEXITCODE -ne 0 -or $commitCount -eq 0) {
    Write-Host "📝 Создание первого коммита..." -ForegroundColor Yellow
    git commit -m "Initial commit - готово к деплою на Render"
    Write-Host "✅ Коммит создан" -ForegroundColor Green
} else {
    Write-Host "📝 Создание коммита с изменениями..." -ForegroundColor Yellow
    git commit -m "Update: подготовка к деплою" -a
    Write-Host "✅ Коммит создан" -ForegroundColor Green
}
Write-Host ""

# Проверяем, существует ли remote
Write-Host "🔗 Проверка remote репозитория..." -ForegroundColor Yellow
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Создание GitHub репозитория..." -ForegroundColor Yellow
    Write-Host "Название репозитория: gymgenius-ai" -ForegroundColor Cyan
    Write-Host ""
    
    # Создаем репозиторий через GitHub CLI
    gh repo create gymgenius-ai --public --source=. --remote=origin --push
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Репозиторий создан и код загружен!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 Репозиторий доступен по адресу:" -ForegroundColor Cyan
        $repoUrl = gh repo view --web 2>&1 | Select-String -Pattern "https://github.com"
        $username = gh api user --jq .login 2>$null
        if ($username) {
            Write-Host "   https://github.com/$username/gymgenius-ai" -ForegroundColor Yellow
        } else {
            Write-Host "   https://github.com/YOUR_USERNAME/gymgenius-ai" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Ошибка при создании репозитория" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Remote уже настроен: $remote" -ForegroundColor Green
    Write-Host "📤 Отправка изменений..." -ForegroundColor Yellow
    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Код отправлен в репозиторий" -ForegroundColor Green
    }
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ ГОТОВО!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Зайдите на https://render.com" -ForegroundColor White
Write-Host "2. Создайте новый Web Service" -ForegroundColor White
$username = gh api user --jq .login 2>$null
if ($username) {
    Write-Host "3. Подключите репозиторий: $username/gymgenius-ai" -ForegroundColor White
} else {
    Write-Host "3. Подключите репозиторий: YOUR_USERNAME/gymgenius-ai" -ForegroundColor White
}
Write-Host "4. Укажите Root Directory: fitness-ai-app/backend" -ForegroundColor White
Write-Host "5. Добавьте переменную OPENAI_API_KEY" -ForegroundColor White
Write-Host ""
Write-Host "📖 Подробные инструкции: DEPLOY_NOW.md" -ForegroundColor Cyan
Write-Host ""

# Открываем репозиторий в браузере
$openRepo = Read-Host "Открыть репозиторий в браузере? (y/n)"
if ($openRepo -eq "y" -or $openRepo -eq "Y") {
    gh repo view --web
}

