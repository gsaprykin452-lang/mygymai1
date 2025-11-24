# 🚀 Руководство по деплою GymGenius AI

## 📋 Содержание

1. [Подготовка к деплою](#подготовка-к-деплою)
2. [Деплой Backend](#деплой-backend)
   - [Render](#render)
   - [Railway](#railway)
   - [Heroku](#heroku)
   - [Docker](#docker)
   - [VPS/Сервер](#vpsсервер)
3. [Деплой Frontend](#деплой-frontend)
   - [Expo EAS Build](#expo-eas-build)
   - [Web версия](#web-версия)
4. [Переменные окружения](#переменные-окружения)
5. [Проверка после деплоя](#проверка-после-деплоя)

---

## 🔧 Подготовка к деплою

### 1. Убедитесь, что все зависимости установлены

**Backend:**
```bash
cd fitness-ai-app/backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd fitness-ai-app/mobile
npm install
```

### 2. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cd fitness-ai-app/backend
cp .env.example .env
```

Отредактируйте `.env` и укажите:
- `OPENAI_API_KEY` - ваш API ключ OpenAI
- `PORT` - порт сервера (по умолчанию 8000)
- Другие переменные при необходимости

### 3. Проверьте работоспособность локально

```bash
# Backend
cd fitness-ai-app/backend
python main.py

# Frontend (в другом терминале)
cd fitness-ai-app/mobile
npm start
```

---

## 🌐 Деплой Backend

### Render

1. **Создайте аккаунт на [Render.com](https://render.com)**

2. **Создайте новый Web Service:**
   - Подключите ваш Git репозиторий
   - Выберите ветку (обычно `main` или `master`)
   - Укажите:
     - **Name**: `gymgenius-backend`
     - **Root Directory**: `fitness-ai-app/backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Настройте переменные окружения:**
   - Перейдите в **Environment** секцию
   - Добавьте:
     - `OPENAI_API_KEY` = ваш API ключ
     - `PORT` = `8000` (или оставьте пустым, Render установит автоматически)
     - `ENVIRONMENT` = `production`

4. **Деплой:**
   - Нажмите **Create Web Service**
   - Render автоматически задеплоит приложение
   - После деплоя вы получите URL вида: `https://gymgenius-backend.onrender.com`

### Railway

1. **Создайте аккаунт на [Railway.app](https://railway.app)**

2. **Создайте новый проект:**
   - Нажмите **New Project**
   - Выберите **Deploy from GitHub repo**
   - Выберите ваш репозиторий

3. **Настройте сервис:**
   - Railway автоматически определит Python проект
   - Убедитесь, что **Root Directory** = `fitness-ai-app/backend`
   - Railway использует `railway.json` для конфигурации

4. **Настройте переменные окружения:**
   - Перейдите в **Variables** секцию
   - Добавьте:
     - `OPENAI_API_KEY` = ваш API ключ
     - `PORT` = Railway установит автоматически
     - `ENVIRONMENT` = `production`

5. **Деплой:**
   - Railway автоматически задеплоит приложение
   - После деплоя вы получите URL вида: `https://gymgenius-backend.up.railway.app`

### Heroku

1. **Установите Heroku CLI:**
   ```bash
   # Windows
   # Скачайте с https://devcenter.heroku.com/articles/heroku-cli
   
   # Mac
   brew tap heroku/brew && brew install heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Войдите в Heroku:**
   ```bash
   heroku login
   ```

3. **Создайте приложение:**
   ```bash
   cd fitness-ai-app/backend
   heroku create gymgenius-backend
   ```

4. **Настройте переменные окружения:**
   ```bash
   heroku config:set OPENAI_API_KEY=your_api_key_here
   heroku config:set ENVIRONMENT=production
   ```

5. **Деплой:**
   ```bash
   git push heroku main
   ```

### Docker

1. **Соберите Docker образ:**
   ```bash
   cd fitness-ai-app/backend
   docker build -t gymgenius-backend .
   ```

2. **Запустите контейнер:**
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e OPENAI_API_KEY=your_api_key_here \
     -e ENVIRONMENT=production \
     --name gymgenius-backend \
     gymgenius-backend
   ```

3. **Для деплоя на Docker Hub:**
   ```bash
   # Войдите в Docker Hub
   docker login
   
   # Тег образа
   docker tag gymgenius-backend yourusername/gymgenius-backend:latest
   
   # Загрузите образ
   docker push yourusername/gymgenius-backend:latest
   ```

### VPS/Сервер

1. **Подключитесь к серверу:**
   ```bash
   ssh user@your-server-ip
   ```

2. **Установите зависимости:**
   ```bash
   # Обновите систему
   sudo apt update && sudo apt upgrade -y
   
   # Установите Python 3.11
   sudo apt install python3.11 python3.11-venv python3-pip -y
   
   # Установите Nginx (опционально, для reverse proxy)
   sudo apt install nginx -y
   ```

3. **Клонируйте репозиторий:**
   ```bash
   git clone your-repo-url
   cd fitness-ai-app/backend
   ```

4. **Создайте виртуальное окружение:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Настройте переменные окружения:**
   ```bash
   cp .env.example .env
   nano .env  # Отредактируйте файл
   ```

6. **Запустите через systemd (рекомендуется):**
   ```bash
   # Создайте файл сервиса
   sudo nano /etc/systemd/system/gymgenius-backend.service
   ```

   Содержимое файла:
   ```ini
   [Unit]
   Description=GymGenius AI Backend
   After=network.target

   [Service]
   User=your-user
   WorkingDirectory=/path/to/fitness-ai-app/backend
   Environment="PATH=/path/to/fitness-ai-app/backend/venv/bin"
   ExecStart=/path/to/fitness-ai-app/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Активируйте сервис:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable gymgenius-backend
   sudo systemctl start gymgenius-backend
   ```

7. **Настройте Nginx (опционально):**
   ```bash
   sudo nano /etc/nginx/sites-available/gymgenius-backend
   ```

   Содержимое:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Активируйте конфигурацию:
   ```bash
   sudo ln -s /etc/nginx/sites-available/gymgenius-backend /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## 📱 Деплой Frontend

### Expo EAS Build

1. **Установите EAS CLI:**
   ```bash
   npm install -g eas-cli
   ```

2. **Войдите в Expo:**
   ```bash
   eas login
   ```

3. **Настройте проект:**
   ```bash
   cd fitness-ai-app/mobile
   eas build:configure
   ```

4. **Обновите `app.config.js`:**
   ```javascript
   const apiUrl = process.env.BACKEND_URL || 'https://your-backend-url.com';
   ```

5. **Создайте билд:**
   ```bash
   # Android
   eas build --platform android
   
   # iOS
   eas build --platform ios
   
   # Оба
   eas build --platform all
   ```

6. **После билда:**
   - Android: APK/AAB будет доступен для скачивания
   - iOS: Билд будет отправлен в App Store Connect

### Web версия

1. **Соберите веб-версию:**
   ```bash
   cd fitness-ai-app/mobile
   npm install
   npx expo export:web
   ```

2. **Деплой на Vercel:**
   ```bash
   # Установите Vercel CLI
   npm install -g vercel
   
   # Деплой
   cd web-build
   vercel
   ```

3. **Деплой на Netlify:**
   ```bash
   # Установите Netlify CLI
   npm install -g netlify-cli
   
   # Деплой
   cd web-build
   netlify deploy --prod
   ```

---

## 🔐 Переменные окружения

### Backend

| Переменная | Описание | Обязательная | По умолчанию |
|------------|----------|--------------|--------------|
| `OPENAI_API_KEY` | API ключ OpenAI | ✅ Да | - |
| `PORT` | Порт сервера | ❌ Нет | `8000` |
| `HOST` | Хост сервера | ❌ Нет | `0.0.0.0` |
| `ENVIRONMENT` | Окружение (production/development) | ❌ Нет | `development` |
| `DATABASE_URL` | URL базы данных | ❌ Нет | `sqlite:///./gymgenius.db` |
| `CORS_ORIGINS` | Разрешенные источники для CORS | ❌ Нет | `*` |

### Frontend

| Переменная | Описание | Обязательная | По умолчанию |
|------------|----------|--------------|--------------|
| `BACKEND_URL` | URL бэкенд сервера | ✅ Да | `http://localhost:8000` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | ❌ Нет | - |

---

## ✅ Проверка после деплоя

### Backend

1. **Проверьте health check:**
   ```bash
   curl https://your-backend-url.com/
   ```
   
   Должен вернуть:
   ```json
   {"message": "GymGenius AI API", "status": "running"}
   ```

2. **Проверьте API эндпоинты:**
   ```bash
   # Получить список упражнений
   curl https://your-backend-url.com/exercises
   
   # Получить профиль пользователя
   curl https://your-backend-url.com/user/profile?user_id=1
   ```

3. **Проверьте логи:**
   - Render: Dashboard → Logs
   - Railway: Deployments → View Logs
   - Heroku: `heroku logs --tail`
   - Docker: `docker logs gymgenius-backend`

### Frontend

1. **Обновите `BACKEND_URL` в `app.config.js`:**
   ```javascript
   const apiUrl = 'https://your-backend-url.com';
   ```

2. **Пересоберите приложение:**
   ```bash
   cd fitness-ai-app/mobile
   npm start
   ```

3. **Проверьте подключение к API:**
   - Откройте приложение
   - Попробуйте выполнить любую операцию, требующую API
   - Проверьте консоль на ошибки

---

## 🐛 Решение проблем

### Backend не запускается

1. **Проверьте логи:**
   ```bash
   # Render/Railway: через Dashboard
   # Heroku:
   heroku logs --tail
   
   # Docker:
   docker logs gymgenius-backend
   ```

2. **Проверьте переменные окружения:**
   - Убедитесь, что `OPENAI_API_KEY` установлен
   - Проверьте формат переменных

3. **Проверьте порт:**
   - Убедитесь, что порт доступен
   - Проверьте файрвол

### Frontend не подключается к Backend

1. **Проверьте CORS:**
   - Убедитесь, что `CORS_ORIGINS` включает ваш домен
   - Или используйте `*` для разработки

2. **Проверьте URL:**
   - Убедитесь, что `BACKEND_URL` правильный
   - Проверьте, что URL доступен из браузера

3. **Проверьте SSL:**
   - Если Backend на HTTPS, Frontend должен использовать HTTPS
   - Проверьте сертификаты

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи приложения
2. Проверьте документацию платформы деплоя
3. Убедитесь, что все переменные окружения установлены
4. Проверьте версии зависимостей

---

**Удачи с деплоем! 🚀**

