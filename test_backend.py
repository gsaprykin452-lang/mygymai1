#!/usr/bin/env python3
"""
Простой скрипт для проверки работоспособности бэкенда
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Проверка импортов...")
    from database import DatabaseManager, init_db
    print("✓ database импортирован")
    
    from models import Exercise, Equipment, WorkoutPlan
    print("✓ models импортирован")
    
    from schemas import UserProfile, PlanRequest, PlanResponse
    print("✓ schemas импортирован")
    
    from openai_client import generate_equipment_guidance
    print("✓ openai_client импортирован")
    
    from plan_engine import generate_plan
    print("✓ plan_engine импортирован")
    
    from ml_inference import predict_equipment
    print("✓ ml_inference импортирован")
    
    print("\nПроверка базы данных...")
    db = init_db()
    print("✓ База данных инициализирована")
    
    profile = db.get_user_profile()
    print(f"✓ Профиль пользователя: {'найден' if profile else 'не найден (это нормально для первого запуска)'}")
    
    equipment = db.get_equipment()
    print(f"✓ Оборудование в базе: {len(equipment)} записей")
    
    exercises = db.get_exercises()
    print(f"✓ Упражнения в базе: {len(exercises)} записей")
    
    print("\n✓ Все проверки пройдены успешно!")
    print("\nБэкенд готов к запуску. Используйте команду:")
    print("  python main.py")
    print("или")
    print("  uvicorn main:app --host 0.0.0.0 --port 8000")
    
except ImportError as e:
    print(f"✗ Ошибка импорта: {e}")
    print("\nУбедитесь, что все зависимости установлены:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



