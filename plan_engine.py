from typing import Dict, List

from schemas import UserProfile, PlanExercise, PlanResponse
from openai_client import generate_equipment_guidance
from database import DatabaseManager

# Временное отключение GPT (должно совпадать с main.py)
DISABLE_GPT = False


GOAL_TO_REP_SCHEME = {
    "fat_loss": {"reps": "12-15", "sets": "3-4", "rest": "45-75s"},
    "muscle_gain": {"reps": "8-12", "sets": "3-4", "rest": "60-90s"},
    "strength": {"reps": "4-6", "sets": "4-5", "rest": "120-180s"},
    "endurance": {"reps": "15-20", "sets": "2-4", "rest": "30-60s"},
    "rehab": {"reps": "10-15", "sets": "2-3", "rest": "60-90s"},
}


def _apply_health_modifiers(safety: List[str], health_flags: List[str] | None, equipment: str) -> List[str]:
    flags = health_flags or []
    notes = list(safety)
    if "knee_pain" in flags:
        notes.append("При проблемах с коленями уменьшайте амплитуду и избегайте боли.")
    if "lower_back_pain" in flags:
        notes.append("Держите нейтральную спину, избегайте гиперпрогиба, снизьте нагрузку.")
    if "shoulder_pain" in flags:
        notes.append("Избегайте чрезмерной ротации плеча, работайте в комфортной амплитуде.")
    return notes


async def generate_plan(equipment: str, user: UserProfile, locale: str = "ru") -> PlanResponse:
    # 1) Query AI guidance to get canonical exercises and safety baselines
    if DISABLE_GPT:
        # Моковые данные для guidance
        guidance = {
            "equipment": equipment,
            "exercises": [
                {
                    "name": "Базовое упражнение 1",
                    "sets": "3-4",
                    "reps": "10-12",
                    "muscles": "Основные группы мышц",
                    "instructions": "Выполняйте упражнение с правильной техникой",
                    "steps": ["Шаг 1: Подготовка", "Шаг 2: Выполнение", "Шаг 3: Завершение"]
                },
                {
                    "name": "Базовое упражнение 2",
                    "sets": "3-4",
                    "reps": "10-12",
                    "muscles": "Вторичные группы мышц",
                    "instructions": "Контролируйте движение",
                    "steps": ["Шаг 1: Подготовка", "Шаг 2: Выполнение"]
                }
            ],
            "safety": ["Разминка обязательна", "Следите за техникой"],
            "description": "Базовый план тренировок"
        }
    else:
        guidance = await generate_equipment_guidance(equipment, locale=locale)

    # 2) Choose rep scheme by goal
    scheme = GOAL_TO_REP_SCHEME.get(user.goal, GOAL_TO_REP_SCHEME["muscle_gain"])
    sets_str = scheme["sets"]
    reps_str = scheme["reps"]
    rest = scheme["rest"]

    # 3) Map AI exercises to plan items
    plan_items: List[PlanExercise] = []
    for ex in guidance.get("exercises", [])[:4]:
        # Safe parsing of muscles
        muscles = ex.get("muscles")
        if isinstance(muscles, str):
            muscles_list = [m.strip() for m in muscles.split(",") if m.strip()]
        elif isinstance(muscles, list):
            muscles_list = muscles
        else:
            muscles_list = None
        
        # Safe parsing of steps
        steps = ex.get("steps", [])
        instructions = None
        if steps:
            if isinstance(steps, list):
                instructions = " ".join(str(s) for s in steps if s)
            elif isinstance(steps, str):
                instructions = steps
        
        plan_items.append(
            PlanExercise(
                name=ex.get("name", "Exercise"),
                sets=f"{sets_str}",
                reps=reps_str,
                rest=rest,
                muscles=muscles_list,
                video_url=ex.get("video_url"),
                instructions=instructions,
            )
        )

    # 4) Safety and technique notes
    safety = _apply_health_modifiers(guidance.get("safety", []), user.health_flags, equipment)
    tips = []
    if guidance.get("description"):
        tips.append(guidance["description"])

    # 5) Return structured plan
    return PlanResponse(
        equipment=equipment,
        goal=user.goal,
        level=user.level,
        recommendation=plan_items,
        safety_notes=safety,
        technique_tips=tips,
    )



