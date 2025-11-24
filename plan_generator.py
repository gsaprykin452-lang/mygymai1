"""
Enhanced plan generator that creates structured workout plans with detailed exercises,
muscle groups, instructions, and technique tips using GPT.
"""
import json
import os
from typing import Dict, List, Optional
from schemas import PlanResponse, PlanExercise, UserProfile
from openai_client import OpenAIError

# Get default API key
DEFAULT_OPENAI_API_KEY = "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"

DISABLE_GPT = False  # Should match main.py


async def generate_structured_plan(user_profile: Dict, locale: str = "ru") -> PlanResponse:
    """
    Generate a structured workout plan with detailed exercises, muscle groups,
    instructions, and technique tips based on user profile data.
    
    Returns a PlanResponse with structured exercise data.
    """
    try:
        # Build comprehensive prompt for GPT
        prompt_parts = [
            "Ты — профессиональный фитнес-тренер. Создай персонализированный план тренировок на основе данных пользователя.",
            "",
            "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:",
        ]
        
        # Add all user profile data
        if user_profile.get('goal'):
            prompt_parts.append(f"Цель: {user_profile['goal']}")
        
        if user_profile.get('level'):
            prompt_parts.append(f"Уровень подготовки: {user_profile['level']}")
        
        if user_profile.get('age'):
            prompt_parts.append(f"Возраст: {user_profile['age']} лет")
        
        if user_profile.get('sex') or user_profile.get('gender'):
            sex = user_profile.get('sex') or user_profile.get('gender')
            prompt_parts.append(f"Пол: {sex}")
        
        if user_profile.get('height_cm') and user_profile.get('weight_kg'):
            prompt_parts.append(f"Рост: {user_profile['height_cm']} см, Вес: {user_profile['weight_kg']} кг")
        
        if user_profile.get('workouts_per_week'):
            prompt_parts.append(f"Количество тренировок в неделю: {user_profile['workouts_per_week']}")
        
        if user_profile.get('goal_timeline'):
            prompt_parts.append(f"Срок достижения цели: {user_profile['goal_timeline']}")
        
        if user_profile.get('workout_experience'):
            prompt_parts.append(f"Опыт тренировок: {user_profile['workout_experience']}")
        
        if user_profile.get('available_equipment'):
            equipment = user_profile['available_equipment']
            if isinstance(equipment, list):
                equipment_str = ', '.join(equipment)
            else:
                equipment_str = str(equipment)
            prompt_parts.append(f"Доступное оборудование: {equipment_str}")
        
        if user_profile.get('workout_duration'):
            prompt_parts.append(f"Продолжительность тренировки: {user_profile['workout_duration']}")
        
        if user_profile.get('activity_level'):
            prompt_parts.append(f"Уровень активности: {user_profile['activity_level']}")
        
        if user_profile.get('intensity_preference'):
            prompt_parts.append(f"Предпочтения по интенсивности: {user_profile['intensity_preference']}")
        
        if user_profile.get('favorite_muscle_groups'):
            muscles = user_profile['favorite_muscle_groups']
            if isinstance(muscles, list):
                muscles_str = ', '.join(muscles)
            else:
                muscles_str = str(muscles)
            prompt_parts.append(f"Приоритетные группы мышц: {muscles_str}")
        
        if user_profile.get('injuries_limitations') and user_profile['injuries_limitations'] != 'None':
            prompt_parts.append(f"Травмы и ограничения: {user_profile['injuries_limitations']}")
            prompt_parts.append("ВАЖНО: Учти эти ограничения и предложи безопасные альтернативные упражнения!")
        
        if user_profile.get('health_flags'):
            flags = user_profile['health_flags']
            if isinstance(flags, list) and flags:
                prompt_parts.append(f"Проблемы со здоровьем: {', '.join(flags)}")
        
        if user_profile.get('diet_type'):
            prompt_parts.append(f"Тип диеты: {user_profile['diet_type']}")
        
        if user_profile.get('desiredWeight'):
            prompt_parts.append(f"Желаемый вес: {user_profile['desiredWeight']} кг")
        
        # Determine equipment to use
        available_equipment = user_profile.get('available_equipment', [])
        if isinstance(available_equipment, list) and available_equipment:
            primary_equipment = available_equipment[0]
        else:
            # Default equipment based on goal
            goal = user_profile.get('goal', 'muscle_gain')
            if goal == 'muscle_gain':
                primary_equipment = 'Dumbbell'
            elif goal == 'fat_loss':
                primary_equipment = 'Dumbbell'
            elif goal == 'strength':
                primary_equipment = 'Barbell'
            else:
                primary_equipment = 'Dumbbell'
        
        prompt_parts.extend([
            "",
            "ЗАДАНИЕ:",
            "Создай детальный план тренировок в формате JSON со следующей структурой:",
            "{",
            '  "equipment": "название основного оборудования",',
            '  "recommendation": [',
            '    {',
            '      "name": "название упражнения",',
            '      "sets": "количество подходов (например: 3 или 3-4)",',
            '      "reps": "количество повторений (например: 10-12 или 8-10)",',
            '      "rest": "время отдыха (например: 60s или 60-90s)",',
            '      "muscles": ["группа мышц 1", "группа мышц 2"],',
            '      "instructions": "подробная пошаговая инструкция по выполнению упражнения. Каждый шаг должен быть на новой строке, разделен точкой или переносом строки.",',
            '      "technique_tips": ["совет 1", "совет 2", "совет 3"]',
            '    }',
            '  ],',
            '  "safety_notes": ["предупреждение 1", "предупреждение 2"],',
            '  "technique_tips": ["общий совет 1", "общий совет 2"]',
            "}",
            "",
            "ТРЕБОВАНИЯ:",
            "1. Создай 4-6 упражнений, подходящих для цели и уровня пользователя",
            "2. Для каждого упражнения укажи конкретные группы мышц, которые работают",
            "3. Инструкции должны быть подробными и пошаговыми (каждый шаг с новой строки)",
            "4. Добавь 2-3 совета по технике для каждого упражнения",
            "5. Учти доступное оборудование пользователя",
            "6. Если есть травмы/ограничения, предложи безопасные альтернативы",
            "7. Количество подходов и повторений должно соответствовать цели пользователя",
            "8. Время отдыха должно быть указано для каждого упражнения",
            "",
            "Верни ТОЛЬКО валидный JSON, без дополнительных пояснений."
        ])
        
        prompt = "\n".join(prompt_parts)
        
        if DISABLE_GPT:
            # Mock structured plan
            return _generate_mock_plan(user_profile, primary_equipment)
        
        # Call GPT with JSON response format
        api_key = os.getenv("OPENAI_API_KEY") or DEFAULT_OPENAI_API_KEY
        if not api_key:
            return _generate_mock_plan(user_profile, primary_equipment)
        
        # Используем безопасный вызов OpenAI API с retry логикой
        from openai_client import safe_openai_call
        
        messages = [
            {
                "role": "system",
                "content": "Ты — профессиональный фитнес-тренер. Отвечай ТОЛЬКО валидным JSON без дополнительных пояснений."
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            content = await safe_openai_call(
                messages=messages,
                model="gpt-3.5-turbo",
                max_tokens=3000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            plan_data = json.loads(content)
                
                # Convert to PlanResponse
                exercises = []
                for ex in plan_data.get("recommendation", []):
                    muscles = ex.get("muscles", [])
                    if isinstance(muscles, str):
                        muscles = [m.strip() for m in muscles.split(",") if m.strip()]
                    
                    exercises.append(PlanExercise(
                        name=ex.get("name", "Exercise"),
                        sets=str(ex.get("sets", "3")),
                        reps=str(ex.get("reps", "10-12")),
                        rest=str(ex.get("rest", "60s")),
                        muscles=muscles if isinstance(muscles, list) else None,
                        instructions=ex.get("instructions", ""),
                        technique_tips=ex.get("technique_tips", []) if isinstance(ex.get("technique_tips"), list) else None,
                    ))
                
                return PlanResponse(
                    equipment=plan_data.get("equipment", primary_equipment),
                    goal=user_profile.get("goal", "muscle_gain"),
                    level=user_profile.get("level", "beginner"),
                    recommendation=exercises,
                    safety_notes=plan_data.get("safety_notes", []),
                    technique_tips=plan_data.get("technique_tips", []),
                )
        except OpenAIError:
            raise
            
    except OpenAIError as e:
        error_msg = str(e)
        print(f"OpenAI API error: {error_msg}")
        
        # Специальная обработка ошибки недостаточного баланса (402, 403)
        if "402" in error_msg or "403" in error_msg or "Недостаточно средств" in error_msg or "Insufficient" in error_msg:
            # Возвращаем fallback план вместо ошибки
            print("Insufficient balance detected, generating fallback plan...")
            available_equipment = user_profile.get('available_equipment', [])
            if isinstance(available_equipment, list) and available_equipment:
                primary_equipment = available_equipment[0]
            else:
                primary_equipment = 'Dumbbell'
            return _generate_mock_plan(user_profile, primary_equipment)
        
        # Re-raise OpenAIError for other errors so it can be caught by main.py
        raise
    except json.JSONDecodeError as e:
        print(f"Failed to parse GPT response as JSON: {e}")
        return _generate_mock_plan(user_profile, primary_equipment)
    except Exception as e:
        print(f"Error generating structured plan: {e}")
        import traceback
        traceback.print_exc()
        return _generate_mock_plan(user_profile, primary_equipment)


def _generate_mock_plan(user_profile: Dict, equipment: str) -> PlanResponse:
    """Generate a mock structured plan for testing."""
    goal = user_profile.get("goal", "muscle_gain")
    level = user_profile.get("level", "beginner")
    
    # Determine rep scheme based on goal
    if goal == "fat_loss":
        reps = "12-15"
        sets = "3-4"
        rest = "45-60s"
    elif goal == "strength":
        reps = "4-6"
        sets = "4-5"
        rest = "120-180s"
    elif goal == "endurance":
        reps = "15-20"
        sets = "2-4"
        rest = "30-60s"
    else:  # muscle_gain
        reps = "8-12"
        sets = "3-4"
        rest = "60-90s"
    
    exercises = [
        PlanExercise(
            name="Жим гантелей лежа",
            sets=sets,
            reps=reps,
            rest=rest,
            muscles=["Грудь", "Плечи", "Трицепс"],
            instructions="1. Лягте на скамью, возьмите гантели в руки. 2. Опустите гантели к груди контролируемым движением. 3. Выжмите гантели вверх, выдыхая. 4. Вернитесь в исходное положение.",
            technique_tips=["Держите запястья прямо", "Не отрывайте ноги от пола", "Контролируйте движение вниз"]
        ),
        PlanExercise(
            name="Тяга гантелей в наклоне",
            sets=sets,
            reps=reps,
            rest=rest,
            muscles=["Спина", "Бицепс"],
            instructions="1. Наклонитесь вперед с гантелями в руках. 2. Подтяните гантели к поясу, сводя лопатки. 3. Опустите гантели контролируемо. 4. Повторите движение.",
            technique_tips=["Держите спину прямой", "Не раскачивайтесь", "Фокусируйтесь на работе спины"]
        ),
        PlanExercise(
            name="Приседания с гантелями",
            sets=sets,
            reps=reps,
            rest=rest,
            muscles=["Квадрицепс", "Ягодицы", "Бицепс бедра"],
            instructions="1. Встаньте прямо, держа гантели у плеч. 2. Опуститесь в присед, отводя таз назад. 3. Опуститесь до параллели бедер с полом. 4. Вернитесь в исходное положение, выдыхая.",
            technique_tips=["Держите колени над стопами", "Не округляйте спину", "Вес на пятках"]
        ),
        PlanExercise(
            name="Жим гантелей стоя",
            sets=sets,
            reps=reps,
            rest=rest,
            muscles=["Плечи", "Трицепс"],
            instructions="1. Встаньте прямо, держа гантели на уровне плеч. 2. Выжмите гантели вверх над головой. 3. Опустите гантели контролируемо к плечам. 4. Повторите движение.",
            technique_tips=["Держите корпус напряженным", "Не прогибайтесь в пояснице", "Контролируйте движение"]
        ),
    ]
    
    return PlanResponse(
        equipment=equipment,
        goal=goal,
        level=level,
        recommendation=exercises,
        safety_notes=[
            "Обязательно делайте разминку 5-10 минут перед тренировкой",
            "Останавливайтесь при появлении боли",
            "Следите за правильной техникой выполнения"
        ],
        technique_tips=[
            "Дышите правильно: выдох на усилии, вдох на расслаблении",
            "Начинайте с легкого веса и постепенно увеличивайте нагрузку",
            "Отдыхайте между подходами согласно указанному времени"
        ],
    )

