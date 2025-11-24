# Инструкция по настройке Google OAuth

## Шаг 1: Создание OAuth 2.0 Client ID в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите **Google+ API**:
   - Перейдите в "APIs & Services" > "Library"
   - Найдите "Google+ API" и включите его
4. Создайте OAuth 2.0 Client ID:
   - Перейдите в "APIs & Services" > "Credentials"
   - Нажмите "Create Credentials" > "OAuth client ID"
   - Выберите тип приложения: **"Web application"** (важно для Expo!)
   - Назовите клиента (например, "GymGenius AI")
   - Добавьте Authorized redirect URIs:
     ```
     https://auth.expo.io/@your-username/your-app-slug
     ```
     Или для локальной разработки:
     ```
     exp://127.0.0.1:19000
     ```
   - Нажмите "Create"
5. Скопируйте **Client ID** (не Client Secret!)

## Шаг 2: Настройка в приложении

### Вариант 1: Через переменную окружения (рекомендуется)

В Git Bash выполните:

```bash
export GOOGLE_CLIENT_ID="ваш-client-id-здесь"
```

Затем перезапустите Expo:

```bash
cd "C:/Users/Георгий/Desktop/GymGenius AI/fitness-ai-app/mobile"
npx expo start --clear
```

### Вариант 2: Через app.config.js

Откройте `fitness-ai-app/mobile/app.config.js` и замените:

```javascript
googleClientId: process.env.GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID',
```

На:

```javascript
googleClientId: 'ваш-client-id-здесь',
```

## Шаг 3: Проверка Redirect URI

Убедитесь, что Redirect URI в Google Cloud Console совпадает с тем, что использует Expo.

Для проверки:
1. Запустите приложение
2. Нажмите кнопку "Войти через Google"
3. В консоли будет выведен `redirectUri` - скопируйте его
4. Добавьте этот URI в Google Cloud Console в разделе "Authorized redirect URIs"

## Важные моменты

1. **Тип приложения**: Используйте "Web application", а не "Mobile app"
2. **Redirect URI**: Должен точно совпадать с тем, что генерирует Expo
3. **Client ID**: Используйте Client ID, а не Client Secret
4. **Ошибка 400**: Обычно означает неправильный Client ID или Redirect URI

## Отладка

Если возникают ошибки:

1. Проверьте консоль браузера/Expo для детальных логов
2. Проверьте логи backend сервера
3. Убедитесь, что Client ID правильный
4. Убедитесь, что Redirect URI добавлен в Google Cloud Console

## Альтернативный способ (для тестирования)

Если настройка через Google Cloud Console вызывает проблемы, можно временно использовать тестовый режим:

1. В Google Cloud Console создайте OAuth consent screen
2. Добавьте тестовых пользователей (если приложение не опубликовано)
3. Используйте Client ID для тестирования




