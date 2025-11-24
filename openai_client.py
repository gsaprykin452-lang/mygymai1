import os
from typing import List, Dict, Optional
import httpx
from dotenv import load_dotenv
import base64
from datetime import datetime, timedelta
import asyncio

# Load environment variables from .env file
load_dotenv()

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Default API key (can be overridden by environment variable)
DEFAULT_OPENAI_API_KEY = "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"

# Кэш для результатов запросов к OpenAI API
# Структура: {key: {"data": result, "timestamp": datetime}}
_exercise_cache: Dict[str, Dict] = {}
_cache_ttl_hours = 24  # Время жизни кэша в часах

# Отслеживание использования API пользователями (отключено)
# Структура: {user_key: count}
_user_usage: Dict[str, int] = {}
DAILY_LIMIT = 10  # Лимит запросов в день на пользователя (не используется)


class OpenAIError(Exception):
    pass


async def safe_openai_call(
    messages: List[Dict], 
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    response_format: Optional[Dict] = None,
    max_retries: int = 3
) -> str:
    """
    Безопасный вызов OpenAI API с защитой от бесконечных циклов и retry логикой.
    
    Args:
        messages: Список сообщений для OpenAI API
        model: Модель GPT для использования
        max_tokens: Максимальное количество токенов в ответе
        temperature: Температура для генерации (0.0-1.0)
        response_format: Формат ответа (например, {"type": "json_object"})
        max_retries: Максимальное количество попыток при ошибке
    
    Returns:
        Содержимое ответа от GPT
    
    Raises:
        OpenAIError: Если все попытки не удались или недостаточно средств
    """
    api_key = _get_api_key()
    if not api_key:
        raise OpenAIError("OpenAI API key not found")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    if response_format:
        payload["response_format"] = response_format
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(OPENAI_API_URL, headers=headers, json=payload)
                
                if resp.status_code >= 400:
                    error_text = resp.text
                    print(f"🔴 ПОЛНЫЙ ТЕКСТ ОШИБКИ: {error_text}")
                    print(f"🔴 Статус код: {resp.status_code}")
                    print(f"🔴 Попытка: {attempt}/{max_retries}")
                    
                    try:
                        error_data = resp.json()
                        error_obj = error_data.get("error", {})
                        error_message = error_obj.get("message", error_text)
                        error_code = error_obj.get("code", "")
                        
                        print(f"🔴 Код ошибки: {error_code}")
                        print(f"🔴 Сообщение: {error_message}")
                        
                        # Если ошибка баланса - немедленно прекращаем
                        if (resp.status_code in [402, 403] or 
                            "insufficient" in error_message.lower() or 
                            "quota" in error_message.lower() or
                            "billing" in error_message.lower()):
                            raise OpenAIError(
                                f"Недостаточно средств на счете API ({resp.status_code}). "
                                f"Пополните баланс на https://platform.openai.com/account/billing. "
                                f"Детали: {error_message}"
                            )
                        
                        # Если ошибка не связана с балансом, пробуем повторить
                        if attempt < max_retries:
                            wait_time = 1000 * attempt  # Экспоненциальная задержка: 1s, 2s, 3s...
                            print(f"Retrying in {wait_time}ms...")
                            await asyncio.sleep(wait_time / 1000)
                            continue
                        else:
                            raise OpenAIError(f"OpenAI API error {resp.status_code}: {error_message}")
                    except OpenAIError:
                        raise
                    except Exception as parse_error:
                        print(f"🔴 Ошибка парсинга JSON ответа: {parse_error}")
                        if attempt < max_retries:
                            wait_time = 1000 * attempt
                            await asyncio.sleep(wait_time / 1000)
                            continue
                        raise OpenAIError(f"OpenAI API error {resp.status_code}: {error_text}")
                
                # Успешный ответ
                data = resp.json()
                
                if "choices" not in data or len(data["choices"]) == 0:
                    raise OpenAIError(f"Unexpected OpenAI response format: {data}")
                
                content = data["choices"][0]["message"]["content"]
                if not content:
                    raise OpenAIError("Empty response from OpenAI API")
                
                return content
                
        except httpx.TimeoutException as e:
            last_error = e
            print(f"OpenAI API timeout (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                wait_time = 1000 * attempt
                await asyncio.sleep(wait_time / 1000)
                continue
            raise OpenAIError("Request to OpenAI API timed out. Please try again.")
            
        except httpx.RequestError as e:
            last_error = e
            print(f"OpenAI API network error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                wait_time = 1000 * attempt
                await asyncio.sleep(wait_time / 1000)
                continue
            raise OpenAIError(f"Network error connecting to OpenAI API: {str(e)}")
            
        except OpenAIError:
            raise
            
        except Exception as e:
            last_error = e
            print(f"OpenAI API unexpected error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                wait_time = 1000 * attempt
                await asyncio.sleep(wait_time / 1000)
                continue
    
    # Если все попытки не удались
    if last_error:
        raise OpenAIError(f"Failed to get AI response after {max_retries} attempts: {str(last_error)}")
    else:
        raise OpenAIError(f"Failed to get AI response after {max_retries} attempts")


def _handle_openai_error(resp) -> None:
    """
    Универсальная функция для обработки ошибок OpenAI API.
    Вызывает OpenAIError с понятным сообщением.
    """
    error_text = resp.text[:500] if resp.text else "No error details"
    
    # Логируем полную ошибку для диагностики
    print(f"OpenAI API error {resp.status_code}: {error_text}")
    
    try:
        error_data = resp.json()
        error_obj = error_data.get("error", {})
        error_type = error_obj.get("type", "")
        error_message = error_obj.get("message", error_text)
        
        # Детальное логирование
        print(f"Error type: {error_type}, Message: {error_message}")
        
        # Специальная обработка ошибки 401 (неверный API ключ)
        if resp.status_code == 401:
            raise OpenAIError(
                f"OpenAI API: Неверный API ключ (401). "
                f"Проверьте правильность OPENAI_API_KEY. Детали: {error_message}"
            )
        
        # Специальная обработка ошибки 404 (модель не найдена)
        if resp.status_code == 404 or ("model" in error_message.lower() and 
                                       ("not found" in error_message.lower() or 
                                        "does not exist" in error_message.lower())):
            raise OpenAIError(
                f"OpenAI API: Модель не найдена (404). "
                f"Проверьте название модели. Детали: {error_message}"
            )
        
        # Специальная обработка ошибки 429 (превышен лимит запросов)
        if resp.status_code == 429:
            raise OpenAIError(
                f"OpenAI API: Превышен лимит запросов (429). "
                f"Подождите немного и попробуйте снова. Детали: {error_message}"
            )
        
        # Специальная обработка ошибки недостаточного баланса (402, 403)
        # Проверяем не только статус код, но и текст ошибки
        if (resp.status_code in [402, 403] or 
            "insufficient" in error_message.lower() or 
            "quota" in error_message.lower() or
            "billing" in error_message.lower() or
            "payment" in error_message.lower()):
            raise OpenAIError(
                f"OpenAI API: Недостаточно средств на балансе ({resp.status_code}). "
                f"Пополните баланс на https://platform.openai.com/account/billing. "
                f"Детали: {error_message}"
            )
        
        # Общая ошибка API
        raise OpenAIError(f"OpenAI API error {resp.status_code} ({error_type}): {error_message}")
    except OpenAIError:
        raise
    except:
        # Если не удалось распарсить JSON, используем текст ошибки
        raise OpenAIError(f"OpenAI API error {resp.status_code}: {error_text}")


def _get_api_key() -> str | None:
    """Get OpenAI API key with diagnostics."""
    api_key = os.getenv("OPENAI_API_KEY") or DEFAULT_OPENAI_API_KEY
    
    if not api_key:
        print("❌ API ключ не найден!")
        return None
    
    # Проверяем формат ключа
    if api_key.startswith("sk-proj-"):
        print("✅ Используется новый формат API ключа (sk-proj-)")
    elif api_key.startswith("sk-"):
        print("✅ Используется стандартный формат API ключа (sk-)")
    else:
        print("❌ Неверный формат API ключа")
    
    return api_key


def _get_cache_key(equipment_name: str, locale: str) -> str:
    """Генерирует ключ для кэша на основе названия оборудования и локали."""
    return f"{equipment_name.lower()}_{locale.lower()}"


def _is_cache_valid(cache_entry: Dict) -> bool:
    """Проверяет, действителен ли кэш (не истек ли TTL)."""
    if not cache_entry or "timestamp" not in cache_entry:
        return False
    age = datetime.now() - cache_entry["timestamp"]
    return age < timedelta(hours=_cache_ttl_hours)


def _get_from_cache(key: str) -> Optional[Dict]:
    """Получает данные из кэша, если они действительны."""
    if key in _exercise_cache:
        cache_entry = _exercise_cache[key]
        if _is_cache_valid(cache_entry):
            print(f"Cache hit for key: {key}")
            return cache_entry["data"]
        else:
            # Удаляем устаревший кэш
            del _exercise_cache[key]
            print(f"Cache expired for key: {key}")
    return None


def _save_to_cache(key: str, data: Dict) -> None:
    """Сохраняет данные в кэш с текущей меткой времени."""
    _exercise_cache[key] = {
        "data": data,
        "timestamp": datetime.now()
    }
    print(f"Cache saved for key: {key}")


def _get_user_key(user_id: int) -> str:
    """Генерирует ключ пользователя на основе ID и текущей даты."""
    today = datetime.now().date().isoformat()
    return f"{user_id}_{today}"


def _increment_user_usage(user_id: int) -> None:
    """Увеличивает счетчик использования API для пользователя."""
    user_key = _get_user_key(user_id)
    if user_key not in _user_usage:
        _user_usage[user_key] = 0
    _user_usage[user_key] += 1
    print(f"User {user_id} usage: {_user_usage[user_key]}/{DAILY_LIMIT}")


def can_make_request(user_id: int = 1) -> bool:
    """
    Проверяет, может ли пользователь сделать запрос к OpenAI API.
    
    Args:
        user_id: ID пользователя (по умолчанию 1)
    
    Returns:
        True если пользователь может сделать запрос, False если лимит исчерпан
    """
    user_key = _get_user_key(user_id)
    
    if user_key not in _user_usage:
        _user_usage[user_key] = 0
    
    current_usage = _user_usage[user_key]
    can_make = current_usage < DAILY_LIMIT
    
    if not can_make:
        print(f"User {user_id} has reached daily limit ({DAILY_LIMIT} requests)")
    
    return can_make


def get_user_usage(user_id: int = 1) -> Dict[str, int]:
    """
    Возвращает информацию об использовании API пользователем.
    
    Args:
        user_id: ID пользователя (по умолчанию 1)
    
    Returns:
        Dict с информацией об использовании: {"used": int, "limit": int, "remaining": int}
    """
    user_key = _get_user_key(user_id)
    used = _user_usage.get(user_key, 0)
    
    return {
        "used": used,
        "limit": DAILY_LIMIT,
        "remaining": max(0, DAILY_LIMIT - used)
    }


async def generate_equipment_guidance(equipment_name: str, locale: str = "ru", user_id: int = 1) -> Dict:
    """
    Call OpenAI ChatGPT to generate structured guidance for the given equipment.
    Использует кэширование для избежания повторных запросов.

    Args:
        equipment_name: Название оборудования
        locale: Язык ответа
        user_id: ID пользователя (не используется, оставлен для совместимости)

    Returns a dict with keys: description, exercises (list of {name, muscles, steps}) and safety.
    """
    # Проверяем кэш
    cache_key = _get_cache_key(equipment_name, locale)
    cached_result = _get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    api_key = _get_api_key()

    system_prompt = (
        "Ты — эксперт по тренажёрам и технике упражнений. Отвечай кратко, структурировано,"
        " на языке пользователя. Возвращай только JSON, без пояснений."
    )

    user_prompt = (
        f"Сформируй краткое описание, 4-6 подходящих упражнений и пошаговую инструкцию по технике и безопасности "
        f"для тренажёра: {equipment_name}. Верни JSON с ключами: description (string), exercises (array of objects: "
        f"name, muscles, steps [array of strings]), safety (array of strings)."
    )

    # If no API key, return a deterministic mock for local testing
    if not api_key:
        return {
            "description": f"Краткое описание тренажёра {equipment_name} и его назначение.",
            "exercises": [
                {"name": "Базовое упражнение 1", "muscles": "Грудь, плечи", "steps": [
                    "Настройте высоту/сиденье.", "Примите устойчивое положение.", "Двигайтесь в контролируемом темпе."]},
                {"name": "Базовое упражнение 2", "muscles": "Спина, бицепс", "steps": [
                    "Выберите умеренный вес.", "Сохраняйте нейтральную спину.", "Не раскачивайтесь."]},
            ],
            "safety": [
                "Разминка 5–10 минут перед началом.",
                "Следите за дыханием и амплитудой движения.",
                "Останавливайтесь при боли или дискомфорте."
            ],
        }

    # Используем безопасный вызов OpenAI API с retry логикой
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt if locale != "en" else user_prompt.replace("Отвечай", "Reply")},
    ]
    
    try:
        content = await safe_openai_call(
            messages=messages,
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Парсим JSON ответ
        import json as _json
        try:
            parsed = _json.loads(content)
        except Exception as exc:
            raise OpenAIError(f"Failed to parse OpenAI JSON content: {str(exc)}. Content: {content[:200]}") from exc
        
        # Минимальная нормализация
        parsed.setdefault("description", "")
        parsed.setdefault("exercises", [])
        parsed.setdefault("safety", [])
        
        # Сохраняем в кэш перед возвратом
        _save_to_cache(cache_key, parsed)
        
        return parsed
        
    except OpenAIError:
        raise
    except Exception as e:
        print(f"OpenAI API error: Unexpected error in generate_equipment_guidance: {e}")
        import traceback
        traceback.print_exc()
        raise OpenAIError(f"Failed to get equipment guidance: {str(e)}")


async def chat_with_ai(user_message: str, context: Dict = None, locale: str = "ru", user_id: int = 1) -> str:
    """
    Chat with OpenAI ChatGPT assistant for any training-related questions.
    
    Args:
        user_message: User's question about training
        context: Optional context (user profile, equipment, etc.)
        locale: Language preference
        user_id: ID пользователя (не используется, оставлен для совместимости)
        
    Returns:
        AI response as string
    """
    api_key = _get_api_key()
    
    # Build context-aware system prompt
    system_prompt = (
        "Ты — профессиональный фитнес-тренер и эксперт по тренировкам. "
        "Отвечай на вопросы пользователей о тренировках, питании, технике упражнений, "
        "программах тренировок и здоровье. Будь дружелюбным, профессиональным и полезным. "
        "Всегда подчеркивай важность безопасности и консультации с врачом при необходимости."
    )
    
    # Add context if provided
    user_prompt = user_message
    if context:
        context_str = ""
        if context.get('user_profile'):
            profile = context['user_profile']
            context_str += f"\nПрофиль пользователя: уровень - {profile.get('level', 'не указан')}, "
            context_str += f"цель - {profile.get('goal', 'не указана')}"
        if context.get('equipment'):
            context_str += f"\nТекущий тренажер: {context['equipment']}"
        if context_str:
            user_prompt = context_str + "\n\nВопрос пользователя: " + user_message
    
    # If no API key, return helpful mock response
    if not api_key:
        return (
            f"Привет! Я ваш фитнес-ассистент. По вашему вопросу '{user_message}':\n\n"
            "Для полноценной работы ИИ-ассистента необходимо установить OPENAI_API_KEY. "
            "Без ключа я могу дать общие советы:\n\n"
            "- Всегда начинайте с разминки\n"
            "- Следите за правильной техникой выполнения упражнений\n"
            "- Увеличивайте нагрузку постепенно\n"
            "- Отдыхайте между тренировками\n"
            "- Пейте достаточно воды\n\n"
            "Для получения персонализированных рекомендаций установите API ключ OpenAI."
        )
    
    # Используем безопасный вызов OpenAI API с retry логикой
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        content = await safe_openai_call(
            messages=messages,
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7
        )
        
        return content
        
    except OpenAIError:
        raise
    except Exception as e:
        print(f"OpenAI API error: Unexpected error in chat_with_ai: {e}")
        import traceback
        traceback.print_exc()
        raise OpenAIError(f"Failed to get AI response: {str(e)}")


async def recognize_equipment_from_image(image_path: str, locale: str = "ru") -> Dict:
    """
    Recognize gym equipment from an image using OpenAI GPT-4 Vision API.
    
    Args:
        image_path: Path to the image file
        locale: Language preference
        
    Returns:
        Dict with equipment name and confidence, or list of candidates
    """
    api_key = _get_api_key()
    
    # Read and encode image
    try:
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        raise OpenAIError(f"Failed to read image file: {str(e)}")
    
    # Determine image MIME type
    if image_path.lower().endswith('.png'):
        mime_type = "image/png"
    elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
        mime_type = "image/jpeg"
    else:
        mime_type = "image/jpeg"  # default
    
    # Build prompt based on locale
    if locale == "ru":
        system_prompt = (
            "Ты — эксперт по распознаванию тренажерного оборудования. "
            "Анализируй изображение и определи, какой тренажер на нем изображен. "
            "Отвечай только JSON форматом без дополнительных пояснений."
        )
        user_prompt = (
            "Определи, какой тренажер изображен на этой фотографии. "
            "Верни JSON с ключами: equipment (название тренажера на английском, например: Dumbbell, Barbell, Bench, Cable Machine, Smith Machine, Leg Press Machine, Lat Pulldown Machine, Leg Extension Machine, Leg Curl Machine, Chest Press Machine, Shoulder Press Machine, Rowing Machine, Hack Squat Machine, Pec Deck Machine, Pull-Up Bar, Dip Station, Kettlebell, Resistance Band), "
            "confidence (число от 0 до 1), "
            "description (краткое описание на русском языке, что это за тренажер). "
            "Если тренажер не распознан или это не тренажерное оборудование, верни equipment: 'Unknown', confidence: 0.1"
        )
    elif locale == "en":
        system_prompt = (
            "You are an expert at recognizing gym equipment. "
            "Analyze the image and identify what equipment is shown. "
            "Respond only in JSON format without additional explanations."
        )
        user_prompt = (
            "Identify what gym equipment is shown in this photo. "
            "Return JSON with keys: equipment (equipment name in English, e.g.: Dumbbell, Barbell, Bench, Cable Machine, Smith Machine, Leg Press Machine, Lat Pulldown Machine, Leg Extension Machine, Leg Curl Machine, Chest Press Machine, Shoulder Press Machine, Rowing Machine, Hack Squat Machine, Pec Deck Machine, Pull-Up Bar, Dip Station, Kettlebell, Resistance Band), "
            "confidence (number from 0 to 1), "
            "description (brief description in English of what this equipment is). "
            "If equipment is not recognized or this is not gym equipment, return equipment: 'Unknown', confidence: 0.1"
        )
    else:
        # Default to English
        system_prompt = (
            "You are an expert at recognizing gym equipment. "
            "Analyze the image and identify what equipment is shown. "
            "Respond only in JSON format without additional explanations."
        )
        user_prompt = (
            "Identify what gym equipment is shown in this photo. "
            "Return JSON with keys: equipment (equipment name in English), confidence (number from 0 to 1), description (brief description). "
            "If equipment is not recognized, return equipment: 'Unknown', confidence: 0.1"
        )
    
    # If no API key, return mock response
    if not api_key:
        return {
            "equipment": "Dumbbell",
            "confidence": 0.75,
            "description": "Mock recognition: Dumbbell equipment"
        }
    
    # Используем безопасный вызов OpenAI API с retry логикой для Vision API
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    try:
        content = await safe_openai_call(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        import json as _json
        try:
            parsed = _json.loads(content)
        except Exception as exc:
            raise OpenAIError(f"Failed to parse OpenAI JSON content: {str(exc)}. Content: {content[:200]}") from exc
        
        # Validate and normalize response
        if "equipment" not in parsed:
            raise OpenAIError("Response missing 'equipment' field")
        
        parsed.setdefault("confidence", 0.5)
        parsed.setdefault("description", f"Recognized equipment: {parsed['equipment']}")
        
        # Ensure confidence is a float between 0 and 1
        try:
            parsed["confidence"] = float(parsed["confidence"])
            if parsed["confidence"] < 0:
                parsed["confidence"] = 0.0
            elif parsed["confidence"] > 1:
                parsed["confidence"] = 1.0
        except (ValueError, TypeError):
            parsed["confidence"] = 0.5
        
        return parsed
        
    except OpenAIError:
        raise
    except Exception as e:
        raise OpenAIError(f"Failed to recognize equipment: {str(e)}")


async def recognize_equipment_candidates_from_image(image_path: str, top_k: int = 3, locale: str = "ru") -> List[Dict]:
    """
    Recognize multiple gym equipment candidates from an image using OpenAI GPT-4 Vision API.
    
    Args:
        image_path: Path to the image file
        top_k: Number of candidates to return
        locale: Language preference
        
    Returns:
        List of dicts with equipment name and confidence
    """
    api_key = _get_api_key()
    
    # Read and encode image
    try:
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        raise OpenAIError(f"Failed to read image file: {str(e)}")
    
    # Determine image MIME type
    if image_path.lower().endswith('.png'):
        mime_type = "image/png"
    elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
        mime_type = "image/jpeg"
    else:
        mime_type = "image/jpeg"
    
    # Build prompt for multiple candidates
    if locale == "ru":
        system_prompt = (
            "Ты — эксперт по распознаванию тренажерного оборудования. "
            "Анализируй изображение и определи несколько возможных вариантов тренажеров. "
            "Отвечай только JSON форматом без дополнительных пояснений."
        )
        user_prompt = (
            f"Определи {top_k} наиболее вероятных тренажеров на этой фотографии. "
            "Верни JSON с ключом 'candidates' (массив объектов), каждый объект должен содержать: "
            "equipment (название на английском: Dumbbell, Barbell, Bench, Cable Machine, Smith Machine, Leg Press Machine, Lat Pulldown Machine, Leg Extension Machine, Leg Curl Machine, Chest Press Machine, Shoulder Press Machine, Rowing Machine, Hack Squat Machine, Pec Deck Machine, Pull-Up Bar, Dip Station, Kettlebell, Resistance Band), "
            "confidence (число от 0 до 1). "
            "Отсортируй по убыванию confidence. "
            "Если тренажер не распознан, верни пустой массив или один элемент с equipment: 'Unknown', confidence: 0.1"
        )
    else:
        system_prompt = (
            "You are an expert at recognizing gym equipment. "
            "Analyze the image and identify several possible equipment options. "
            "Respond only in JSON format without additional explanations."
        )
        user_prompt = (
            f"Identify {top_k} most likely gym equipment items in this photo. "
            "Return JSON with key 'candidates' (array of objects), each object should contain: "
            "equipment (name in English), confidence (number from 0 to 1). "
            "Sort by confidence descending. "
            "If equipment is not recognized, return empty array or one element with equipment: 'Unknown', confidence: 0.1"
        )
    
    # If no API key, return mock response
    if not api_key:
        return [
            {"equipment": "Dumbbell", "confidence": 0.75},
            {"equipment": "Barbell", "confidence": 0.20},
            {"equipment": "Bench", "confidence": 0.05},
        ][:top_k]
    
    # Используем безопасный вызов OpenAI API с retry логикой для Vision API
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    try:
        content = await safe_openai_call(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=800,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        import json as _json
        try:
            parsed = _json.loads(content)
        except Exception as exc:
            raise OpenAIError(f"Failed to parse OpenAI JSON content: {str(exc)}. Content: {content[:200]}") from exc
        
        # Extract candidates
        candidates = parsed.get("candidates", [])
        if not isinstance(candidates, list):
            candidates = []
        
        # Validate and normalize each candidate
        normalized_candidates = []
        for candidate in candidates[:top_k]:
            if isinstance(candidate, dict) and "equipment" in candidate:
                conf = candidate.get("confidence", 0.5)
                try:
                    conf = float(conf)
                    if conf < 0:
                        conf = 0.0
                    elif conf > 1:
                        conf = 1.0
                except (ValueError, TypeError):
                    conf = 0.5
                
                normalized_candidates.append({
                    "equipment": candidate["equipment"],
                    "confidence": conf
                })
        
        # If no valid candidates, return mock
        if not normalized_candidates:
            return [
                {"equipment": "Dumbbell", "confidence": 0.75},
                {"equipment": "Barbell", "confidence": 0.20},
                {"equipment": "Bench", "confidence": 0.05},
            ][:top_k]
        
        return normalized_candidates
        
    except OpenAIError:
        raise
    except Exception as e:
        raise OpenAIError(f"Failed to recognize equipment candidates: {str(e)}")


# Простой тест без vision
async def simple_test():
    """Простой тест для проверки работы OpenAI API без vision функций."""
    try:
        response = await chat_with_ai("Привет! Ответь одним словом: 'работает'")
        print(f"✅ Тест пройден: {response}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


# Для запуска теста напрямую
if __name__ == "__main__":
    import asyncio
    asyncio.run(simple_test())

