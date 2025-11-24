# 🚀 Быстрый старт деплоя

## Backend

### 1. Render (Рекомендуется - бесплатный)

1. Зайдите на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите GitHub репозиторий
4. Укажите:
   - **Root Directory**: `fitness-ai-app/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Добавьте переменную окружения: `OPENAI_API_KEY`
6. Деплой готов!

### 2. Railway

1. Зайдите на [railway.app](https://railway.app)
2. Создайте новый проект из GitHub
3. Railway автоматически определит настройки из `railway.json`
4. Добавьте переменную окружения: `OPENAI_API_KEY`
5. Деплой готов!

### 3. Docker

```bash
cd fitness-ai-app/backend
docker build -t gymgenius-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key gymgenius-backend
```

## Frontend

### 1. Обновите BACKEND_URL

В файле `mobile/app.config.js` укажите URL вашего задеплоенного бэкенда:

```javascript
const apiUrl = 'https://your-backend-url.com';
```

### 2. Соберите приложение

```bash
cd fitness-ai-app/mobile
npm install
npm start
```

### 3. Для мобильных приложений

Используйте Expo EAS Build:

```bash
npm install -g eas-cli
eas login
eas build:configure
eas build --platform android
eas build --platform ios
```

## 📝 Подробные инструкции

См. файл `DEPLOY.md` для детальных инструкций по всем платформам.

