# 🚀 Быстрый старт GymGenius AI

## Установка зависимостей

### Все зависимости сразу:
```bash
npm run install:all
```

### Или по отдельности:

**Backend (Python):**
```bash
npm run install:backend
# или
cd backend
pip install -r requirements.txt
```

**Mobile (Node.js):**
```bash
npm run install:mobile
# или
cd mobile
npm install
```

## Запуск приложения

### Вариант 1: Через npm скрипты (из корня проекта)

**Терминал 1 - Backend:**
```bash
npm run start:backend
```

**Терминал 2 - Mobile:**
```bash
npm run start:mobile
```

### Вариант 2: Вручную

**Терминал 1 - Backend:**
```bash
cd backend
python main.py
```

**Терминал 2 - Mobile:**
```bash
cd mobile
npm start
```

## Доступные команды

- `npm run start:backend` - Запустить бэкенд сервер
- `npm run start:mobile` - Запустить мобильное приложение
- `npm run install:backend` - Установить Python зависимости
- `npm run install:mobile` - Установить Node.js зависимости
- `npm run install:all` - Установить все зависимости

## Примечание

⚠️ **Важно:** Backend и Mobile должны работать одновременно!

Backend будет доступен на: `http://localhost:8000`
Mobile приложение откроется в Expo Go после сканирования QR кода.

