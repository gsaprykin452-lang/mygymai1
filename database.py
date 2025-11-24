import sqlite3
import os
from typing import List, Dict, Optional, Tuple
import json

class DatabaseManager:
    """Менеджер базы данных для GymGenius AI"""
    
    def __init__(self, db_path: str = "gymgenius.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
        return conn
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Создание таблицы Equipment
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    image TEXT,
                    description TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание таблицы Exercises
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    muscles TEXT NOT NULL,
                    difficulty TEXT NOT NULL CHECK (difficulty IN ('Beginner', 'Intermediate', 'Advanced')),
                    video_url TEXT,
                    instructions TEXT,
                    sets_recommended TEXT,
                    reps_recommended TEXT,
                    rest_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE
                )
            ''')
            
            # Создание таблицы Workouts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    exercises TEXT NOT NULL,  -- JSON строка с массивом exercise_id
                    duration_minutes INTEGER,
                    difficulty TEXT CHECK (difficulty IN ('Beginner', 'Intermediate', 'Advanced')),
                    target_muscles TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание индексов для оптимизации
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_name ON equipment (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exercises_equipment ON exercises (equipment_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exercises_muscles ON exercises (muscles)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises (difficulty)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workouts_difficulty ON workouts (difficulty)')
            
            # Пользователи (профиль)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    age INTEGER,
                    sex TEXT,
                    height_cm REAL,
                    weight_kg REAL,
                    level TEXT,
                    goal TEXT,
                    health_flags TEXT, -- JSON array
                    recent_muscles TEXT, -- JSON array
                    workouts_per_week INTEGER, -- Количество тренировок в неделю
                    goal_timeline TEXT, -- За какое время хочет достичь цели (например: "3 месяца", "6 месяцев")
                    diet_type TEXT, -- Тип диеты (например: "Обычная", "Кето", "Веганская", "Палео")
                    supplements TEXT, -- JSON array - какие БАДы принимает
                    workout_experience TEXT, -- Опыт тренировок (например: "Новичок", "1-2 года", "3+ года")
                    workout_type TEXT, -- Тип тренировок (JSON array: "Силовые", "Кардио", "Функциональные" и т.д.)
                    available_equipment TEXT, -- Доступное оборудование (JSON array)
                    workout_duration TEXT, -- Продолжительность тренировки (например: "30 минут", "60 минут")
                    preferred_time TEXT, -- Предпочтительное время тренировок (например: "Утро", "День", "Вечер")
                    injuries_limitations TEXT, -- Травмы и ограничения (текст)
                    activity_level TEXT, -- Уровень активности в повседневной жизни
                    intensity_preference TEXT, -- Предпочтения по интенсивности
                    favorite_muscle_groups TEXT, -- Любимые группы мышц (JSON array)
                    onboarding_completed INTEGER DEFAULT 0, -- Флаг прохождения опроса (0/1)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Миграция: добавляем новые колонки если их нет
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN workouts_per_week INTEGER')
            except sqlite3.OperationalError:
                pass  # Колонка уже существует
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN goal_timeline TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN diet_type TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN supplements TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN onboarding_completed INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN workout_experience TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN workout_type TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN available_equipment TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN workout_duration TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN preferred_time TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN injuries_limitations TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN activity_level TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN intensity_preference TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN favorite_muscle_groups TEXT')
            except sqlite3.OperationalError:
                pass
            
            # Новые поля onboarding
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN gender TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN unit_system TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN birth_date TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN desired_weight REAL')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN weight_gain_rate REAL')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN obstacles TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN tried_other_apps TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN referral_source TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN working_with_trainer TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN calorie_transfer TEXT')
            except sqlite3.OperationalError:
                pass
            
            # Google OAuth fields
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN google_id TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN google_email TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN google_name TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN google_picture TEXT')
            except sqlite3.OperationalError:
                pass
            
            # Subscription fields
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN subscription_active INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN subscription_start_date TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN subscription_end_date TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN subscription_price REAL DEFAULT 9.99')
            except sqlite3.OperationalError:
                pass
            
            # Добавляем поля для имени и фото профиля
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN name TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN profile_photo_uri TEXT')
            except sqlite3.OperationalError:
                pass

            # История тренировок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    equipment TEXT,
                    exercise_name TEXT,
                    sets TEXT,
                    reps TEXT,
                    notes TEXT
                )
            ''')
            
            # Пользовательские планы тренировок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_workout_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    plan_text TEXT NOT NULL, -- Полный текст плана от ИИ
                    plan_data TEXT, -- JSON структура плана (упражнения по дням)
                    week_schedule TEXT, -- JSON расписание на неделю
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Рекомендуемые тренажеры для пользователя (игровая механика)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommended_equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    equipment_name TEXT NOT NULL,
                    status TEXT DEFAULT 'recommended', -- 'recommended', 'found', 'added'
                    found_at TIMESTAMP,
                    added_to_plan INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Трекинг тренировок (детальная информация)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    workout_date DATE NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_minutes INTEGER,
                    exercises_completed TEXT, -- JSON массив выполненных упражнений
                    heart_rate_avg INTEGER,
                    heart_rate_max INTEGER,
                    calories_burned INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()

    # ==================== USER PROFILE ====================

    def get_user_profile(self) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = 1')
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                # Десериализуем JSON массивы
                import json as _json
                for key in ["health_flags", "recent_muscles", "supplements", "workout_type", "available_equipment", "favorite_muscle_groups", "obstacles"]:
                    if isinstance(profile.get(key), str):
                        try:
                            profile[key] = _json.loads(profile[key]) if profile.get(key) else []
                        except:
                            profile[key] = []
                
                # Конвертируем subscription_active в boolean
                if "subscription_active" in profile:
                    profile["subscription_active"] = bool(profile["subscription_active"])
                
                return profile
            return None

    def upsert_user_profile(self, profile: Dict) -> Dict:
        data = profile.copy()
        
        # Serialize arrays and handle None values properly
        for key in ("health_flags", "recent_muscles", "supplements", "workout_type", "available_equipment", "favorite_muscle_groups", "obstacles"):
            value = data.get(key)
            if isinstance(value, list):
                data[key] = json.dumps(value) if value else json.dumps([])
            elif value is None:
                data[key] = json.dumps([])
            elif isinstance(value, str):
                # Already a string, keep it
                pass
        
        # Ensure required fields have defaults - don't allow None for required fields
        if 'level' not in data or not data['level'] or data['level'] is None:
            data['level'] = 'beginner'
        if 'goal' not in data or not data['goal'] or data['goal'] is None:
            data['goal'] = 'fat_loss'
        
        # Prepare all fields - convert None to appropriate defaults
        age = data.get('age') if data.get('age') is not None else None
        sex = data.get('sex') if data.get('sex') is not None else None
        height_cm = data.get('height_cm') if data.get('height_cm') is not None else None
        weight_kg = data.get('weight_kg') if data.get('weight_kg') is not None else None
        level = data.get('level', 'beginner')
        goal = data.get('goal', 'fat_loss')
        health_flags = data.get('health_flags', json.dumps([]))
        recent_muscles = data.get('recent_muscles', json.dumps([]))
        workouts_per_week = data.get('workouts_per_week') if data.get('workouts_per_week') is not None else None
        goal_timeline = data.get('goal_timeline') if data.get('goal_timeline') is not None else None
        diet_type = data.get('diet_type') if data.get('diet_type') is not None else None
        supplements = data.get('supplements', json.dumps([]))
        workout_experience = data.get('workout_experience') if data.get('workout_experience') is not None else None
        workout_type = data.get('workout_type', json.dumps([]))
        available_equipment = data.get('available_equipment', json.dumps([]))
        workout_duration = data.get('workout_duration') if data.get('workout_duration') is not None else None
        preferred_time = data.get('preferred_time') if data.get('preferred_time') is not None else None
        injuries_limitations = data.get('injuries_limitations') if data.get('injuries_limitations') is not None else None
        activity_level = data.get('activity_level') if data.get('activity_level') is not None else None
        intensity_preference = data.get('intensity_preference') if data.get('intensity_preference') is not None else None
        favorite_muscle_groups = data.get('favorite_muscle_groups', json.dumps([]))
        onboarding_completed = data.get('onboarding_completed', 0)
        if isinstance(onboarding_completed, bool):
            onboarding_completed = 1 if onboarding_completed else 0
        
        # Новые поля onboarding
        gender = data.get('gender') if data.get('gender') is not None else None
        unit_system = data.get('unitSystem') or data.get('unit_system') if data.get('unitSystem') is not None or data.get('unit_system') is not None else None
        birth_date = data.get('birthDate') or data.get('birth_date') if data.get('birthDate') is not None or data.get('birth_date') is not None else None
        desired_weight = data.get('desiredWeight') or data.get('desired_weight') if data.get('desiredWeight') is not None or data.get('desired_weight') is not None else None
        weight_gain_rate = data.get('weightGainRate') or data.get('weight_gain_rate') if data.get('weightGainRate') is not None or data.get('weight_gain_rate') is not None else None
        obstacles = data.get('obstacles', json.dumps([]))
        tried_other_apps = data.get('triedOtherApps') or data.get('tried_other_apps') if data.get('triedOtherApps') is not None or data.get('tried_other_apps') is not None else None
        referral_source = data.get('referralSource') or data.get('referral_source') if data.get('referralSource') is not None or data.get('referral_source') is not None else None
        working_with_trainer = data.get('workingWithTrainer') or data.get('working_with_trainer') if data.get('workingWithTrainer') is not None or data.get('working_with_trainer') is not None else None
        calorie_transfer = data.get('calorieTransfer') or data.get('calorie_transfer') if data.get('calorieTransfer') is not None or data.get('calorie_transfer') is not None else None
        
        # Subscription fields
        subscription_active = data.get('subscription_active', 0)
        if isinstance(subscription_active, bool):
            subscription_active = 1 if subscription_active else 0
        subscription_start_date = data.get('subscription_start_date') if data.get('subscription_start_date') is not None else None
        subscription_end_date = data.get('subscription_end_date') if data.get('subscription_end_date') is not None else None
        subscription_price = data.get('subscription_price', 9.99)
        
        # Name and profile photo fields
        name = data.get('name') if data.get('name') is not None else None
        profile_photo_uri = data.get('profile_photo_uri') if data.get('profile_photo_uri') is not None else None
        
        # Конвертация роста и веса в зависимости от системы единиц
        if unit_system == 'imperial' and data.get('height'):
            # Конвертация из футов в см (пример: "5'10" -> 177.8 см)
            height_str = str(data.get('height', ''))
            if "'" in height_str:
                parts = height_str.split("'")
                feet = float(parts[0]) if parts[0] else 0
                inches = float(parts[1].replace('"', '')) if len(parts) > 1 else 0
                height_cm = (feet * 30.48) + (inches * 2.54)
            else:
                height_cm = float(height_str) * 2.54 if height_str else None
        elif unit_system == 'metric' and data.get('height'):
            height_cm = float(data.get('height')) if data.get('height') else None
        else:
            height_cm = data.get('height_cm') if data.get('height_cm') is not None else None
        
        if unit_system == 'imperial' and data.get('weight'):
            # Конвертация из фунтов в кг
            weight_kg = float(data.get('weight')) * 0.453592 if data.get('weight') else None
        elif unit_system == 'metric' and data.get('weight'):
            weight_kg = float(data.get('weight')) if data.get('weight') else None
        else:
            weight_kg = data.get('weight_kg') if data.get('weight_kg') is not None else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if profile exists
            cursor.execute('SELECT COUNT(*) as c FROM users WHERE id = 1')
            exists = cursor.fetchone()['c'] > 0
            
            if exists:
                # Update all fields including new ones
                cursor.execute('''
                    UPDATE users 
                    SET age = ?, sex = ?, height_cm = ?, weight_kg = ?, 
                        level = ?, goal = ?, health_flags = ?, recent_muscles = ?,
                        workouts_per_week = ?, goal_timeline = ?, diet_type = ?,
                        supplements = ?, workout_experience = ?, workout_type = ?,
                        available_equipment = ?, workout_duration = ?, preferred_time = ?,
                        injuries_limitations = ?, activity_level = ?, intensity_preference = ?,
                        favorite_muscle_groups = ?, onboarding_completed = ?,
                        gender = ?, unit_system = ?, birth_date = ?, desired_weight = ?,
                        weight_gain_rate = ?, obstacles = ?, tried_other_apps = ?,
                        referral_source = ?, working_with_trainer = ?, calorie_transfer = ?,
                        subscription_active = ?, subscription_start_date = ?, subscription_end_date = ?,
                        subscription_price = ?, name = ?, profile_photo_uri = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (age, sex, height_cm, weight_kg, level, goal, health_flags, recent_muscles,
                      workouts_per_week, goal_timeline, diet_type, supplements, workout_experience,
                      workout_type, available_equipment, workout_duration, preferred_time,
                      injuries_limitations, activity_level, intensity_preference, favorite_muscle_groups,
                      onboarding_completed, gender, unit_system, birth_date, desired_weight,
                      weight_gain_rate, obstacles, tried_other_apps, referral_source,
                      working_with_trainer, calorie_transfer, subscription_active, subscription_start_date,
                      subscription_end_date, subscription_price, name, profile_photo_uri))
            else:
                # Insert new profile
                cursor.execute('''
                    INSERT INTO users (id, age, sex, height_cm, weight_kg, level, goal, health_flags, recent_muscles,
                                     workouts_per_week, goal_timeline, diet_type, supplements, workout_experience,
                                     workout_type, available_equipment, workout_duration, preferred_time,
                                     injuries_limitations, activity_level, intensity_preference, favorite_muscle_groups,
                                     onboarding_completed, gender, unit_system, birth_date, desired_weight,
                                     weight_gain_rate, obstacles, tried_other_apps, referral_source,
                                     working_with_trainer, calorie_transfer, subscription_active, subscription_start_date,
                                     subscription_end_date, subscription_price, name, profile_photo_uri)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (age, sex, height_cm, weight_kg, level, goal, health_flags, recent_muscles,
                      workouts_per_week, goal_timeline, diet_type, supplements, workout_experience,
                      workout_type, available_equipment, workout_duration, preferred_time,
                      injuries_limitations, activity_level, intensity_preference, favorite_muscle_groups,
                      onboarding_completed, gender, unit_system, birth_date, desired_weight,
                      weight_gain_rate, obstacles, tried_other_apps, referral_source,
                      working_with_trainer, calorie_transfer, subscription_active, subscription_start_date,
                      subscription_end_date, subscription_price, name, profile_photo_uri))
            
            conn.commit()
        
        # Return updated profile
        return self.get_user_profile()
    
    def update_google_user(self, google_id: str, google_email: str, google_name: str = None, google_picture: str = None) -> Dict:
        """Обновить или создать пользователя с Google OAuth данными"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if profile exists
            cursor.execute('SELECT COUNT(*) as c FROM users WHERE id = 1')
            exists = cursor.fetchone()['c'] > 0
            
            if exists:
                # Update Google OAuth fields
                cursor.execute('''
                    UPDATE users 
                    SET google_id = ?, google_email = ?, google_name = ?, google_picture = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (google_id, google_email, google_name, google_picture))
            else:
                # Insert new profile with Google OAuth data
                cursor.execute('''
                    INSERT INTO users (id, google_id, google_email, google_name, google_picture, level, goal)
                    VALUES (1, ?, ?, ?, ?, 'beginner', 'fat_loss')
                ''', (google_id, google_email, google_name, google_picture))
            
            conn.commit()
        
        # Return updated profile
        return self.get_user_profile()

    # ==================== WORKOUT HISTORY ====================

    def log_workout(self, entry: Dict) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Если передан timestamp, используем его, иначе CURRENT_TIMESTAMP
            timestamp = entry.get('timestamp')
            if timestamp:
                cursor.execute('''
                    INSERT INTO workout_history (equipment, exercise_name, sets, reps, notes, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    entry.get('equipment'), entry.get('exercise_name'), entry.get('sets'),
                    entry.get('reps'), entry.get('notes'), timestamp
                ))
            else:
                cursor.execute('''
                    INSERT INTO workout_history (equipment, exercise_name, sets, reps, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    entry.get('equipment'), entry.get('exercise_name'), entry.get('sets'),
                    entry.get('reps'), entry.get('notes')
                ))
            conn.commit()
            return cursor.lastrowid

    def recent_workouts(self, limit: int = 20) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workout_history ORDER BY timestamp DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== EQUIPMENT METHODS ====================
    
    def add_equipment(self, name: str, image: str = None, description: str = None, category: str = None) -> int:
        """Добавить новое оборудование"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO equipment (name, image, description, category)
                VALUES (?, ?, ?, ?)
            ''', (name, image, description, category))
            conn.commit()
            return cursor.lastrowid
    
    def get_equipment(self, equipment_id: int = None) -> Optional[Dict]:
        """Получить оборудование по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if equipment_id:
                cursor.execute('SELECT * FROM equipment WHERE id = ?', (equipment_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                cursor.execute('SELECT * FROM equipment ORDER BY name')
                return [dict(row) for row in cursor.fetchall()]
    
    def get_equipment_by_name(self, name: str) -> Optional[Dict]:
        """Получить оборудование по имени"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM equipment WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_equipment(self, equipment_id: int, **kwargs) -> bool:
        """Обновить оборудование"""
        allowed_fields = ['name', 'image', 'description', 'category']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(equipment_id)
        query = f"UPDATE equipment SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_equipment(self, equipment_id: int) -> bool:
        """Удалить оборудование"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM equipment WHERE id = ?', (equipment_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== EXERCISES METHODS ====================
    
    def add_exercise(self, equipment_id: int, name: str, muscles: str, difficulty: str, 
                    video_url: str = None, instructions: str = None, sets_recommended: str = None,
                    reps_recommended: str = None, rest_time: str = None) -> int:
        """Добавить новое упражнение"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exercises (equipment_id, name, muscles, difficulty, video_url, 
                                    instructions, sets_recommended, reps_recommended, rest_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (equipment_id, name, muscles, difficulty, video_url, instructions, 
                  sets_recommended, reps_recommended, rest_time))
            conn.commit()
            return cursor.lastrowid
    
    def get_exercises(self, equipment_id: int = None, difficulty: str = None, muscles: str = None) -> List[Dict]:
        """Получить упражнения с фильтрацией"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT e.*, eq.name as equipment_name 
                FROM exercises e 
                JOIN equipment eq ON e.equipment_id = eq.id
                WHERE 1=1
            '''
            params = []
            
            if equipment_id:
                query += ' AND e.equipment_id = ?'
                params.append(equipment_id)
            
            if difficulty:
                query += ' AND e.difficulty = ?'
                params.append(difficulty)
            
            if muscles:
                query += ' AND e.muscles LIKE ?'
                params.append(f'%{muscles}%')
            
            query += ' ORDER BY e.name'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_exercise(self, exercise_id: int) -> Optional[Dict]:
        """Получить упражнение по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, eq.name as equipment_name 
                FROM exercises e 
                JOIN equipment eq ON e.equipment_id = eq.id
                WHERE e.id = ?
            ''', (exercise_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_exercise(self, exercise_id: int, **kwargs) -> bool:
        """Обновить упражнение"""
        allowed_fields = ['name', 'muscles', 'difficulty', 'video_url', 'instructions', 
                         'sets_recommended', 'reps_recommended', 'rest_time']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(exercise_id)
        query = f"UPDATE exercises SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_exercise(self, exercise_id: int) -> bool:
        """Удалить упражнение"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== WORKOUTS METHODS ====================
    
    def add_workout(self, name: str, exercises: List[int], duration_minutes: int = None,
                   difficulty: str = None, target_muscles: str = None, description: str = None) -> int:
        """Добавить новую тренировку"""
        exercises_json = json.dumps(exercises)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO workouts (name, exercises, duration_minutes, difficulty, target_muscles, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, exercises_json, duration_minutes, difficulty, target_muscles, description))
            conn.commit()
            return cursor.lastrowid
    
    def get_workouts(self, difficulty: str = None, target_muscles: str = None) -> List[Dict]:
        """Получить тренировки с фильтрацией"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM workouts WHERE 1=1'
            params = []
            
            if difficulty:
                query += ' AND difficulty = ?'
                params.append(difficulty)
            
            if target_muscles:
                query += ' AND target_muscles LIKE ?'
                params.append(f'%{target_muscles}%')
            
            query += ' ORDER BY name'
            
            cursor.execute(query, params)
            workouts = []
            for row in cursor.fetchall():
                workout = dict(row)
                workout['exercises'] = json.loads(workout['exercises'])
                workouts.append(workout)
            return workouts
    
    def get_workout(self, workout_id: int) -> Optional[Dict]:
        """Получить тренировку по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workouts WHERE id = ?', (workout_id,))
            row = cursor.fetchone()
            if row:
                workout = dict(row)
                workout['exercises'] = json.loads(workout['exercises'])
                return workout
            return None
    
    def get_workout_with_exercises(self, workout_id: int) -> Optional[Dict]:
        """Получить тренировку с полной информацией об упражнениях"""
        workout = self.get_workout(workout_id)
        if not workout:
            return None
        
        exercise_ids = workout['exercises']
        exercises = []
        for exercise_id in exercise_ids:
            exercise = self.get_exercise(exercise_id)
            if exercise:
                exercises.append(exercise)
        
        workout['exercise_details'] = exercises
        return workout
    
    def update_workout(self, workout_id: int, **kwargs) -> bool:
        """Обновить тренировку"""
        allowed_fields = ['name', 'exercises', 'duration_minutes', 'difficulty', 'target_muscles', 'description']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field == 'exercises' and isinstance(value, list):
                    value = json.dumps(value)
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(workout_id)
        query = f"UPDATE workouts SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_workout(self, workout_id: int) -> bool:
        """Удалить тренировку"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workouts WHERE id = ?', (workout_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== UTILITY METHODS ====================
    
    def search_equipment(self, query: str) -> List[Dict]:
        """Поиск оборудования по названию"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM equipment 
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name
            ''', (f'%{query}%', f'%{query}%'))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_equipment_stats(self) -> Dict:
        """Получить статистику по оборудованию"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Общее количество оборудования
            cursor.execute('SELECT COUNT(*) as total FROM equipment')
            total_equipment = cursor.fetchone()['total']
            
            # Количество упражнений по оборудованию
            cursor.execute('''
                SELECT eq.name, COUNT(e.id) as exercise_count
                FROM equipment eq
                LEFT JOIN exercises e ON eq.id = e.equipment_id
                GROUP BY eq.id, eq.name
                ORDER BY exercise_count DESC
            ''')
            equipment_stats = [dict(row) for row in cursor.fetchall()]
            
            # Общее количество упражнений
            cursor.execute('SELECT COUNT(*) as total FROM exercises')
            total_exercises = cursor.fetchone()['total']
            
            # Общее количество тренировок
            cursor.execute('SELECT COUNT(*) as total FROM workouts')
            total_workouts = cursor.fetchone()['total']
            
            return {
                'total_equipment': total_equipment,
                'total_exercises': total_exercises,
                'total_workouts': total_workouts,
                'equipment_stats': equipment_stats
            }
    
    def populate_sample_data(self):
        """Заполнить базу данных примерными данными с подробными описаниями"""
        # Расширенный список оборудования с подробными описаниями
        equipment_data = [
            {
                'name': 'Dumbbell',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Гантели - универсальные свободные веса для изолированных и комплексных упражнений. Идеальны для тренировки рук, плеч, груди и спины.',
                'category': 'Free Weights',
                'target_muscles': 'Biceps, Triceps, Shoulders, Chest, Back, Legs',
                'exercises': 'Bicep Curls, Tricep Extensions, Shoulder Press, Chest Press, Rows, Lunges'
            },
            {
                'name': 'Barbell',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Штанга - длинный гриф для базовых комплексных упражнений. Позволяет работать с большими весами и развивать общую силу.',
                'category': 'Free Weights',
                'target_muscles': 'Full Body, Back, Legs, Chest, Shoulders, Core',
                'exercises': 'Deadlift, Squat, Bench Press, Overhead Press, Barbell Rows, Romanian Deadlift'
            },
            {
                'name': 'Bench',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Скамья для жима - регулируемая скамья для упражнений на верхнюю часть тела. Поддерживает спину и обеспечивает стабильность при жимовых движениях.',
                'category': 'Equipment',
                'target_muscles': 'Chest, Shoulders, Triceps, Back',
                'exercises': 'Bench Press, Incline Press, Decline Press, Dumbbell Flyes, Shoulder Press'
            },
            {
                'name': 'Cable Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер с тросами - многофункциональная система с регулируемыми блоками. Обеспечивает постоянное напряжение мышц на протяжении всего движения.',
                'category': 'Machines',
                'target_muscles': 'All Muscle Groups - Chest, Back, Shoulders, Arms, Legs',
                'exercises': 'Cable Flyes, Cable Rows, Cable Curls, Tricep Pushdowns, Cable Crossovers, Lat Pulldowns'
            },
            {
                'name': 'Smith Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер Смита - штанга с направляющими для безопасных базовых упражнений. Идеален для тренировок в одиночку благодаря фиксаторам безопасности.',
                'category': 'Machines',
                'target_muscles': 'Full Body, Legs, Chest, Shoulders, Back',
                'exercises': 'Smith Squat, Smith Bench Press, Smith Shoulder Press, Smith Lunges, Smith Rows'
            },
            {
                'name': 'Kettlebell',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Гиря - чугунный вес для функциональных тренировок. Развивает силу, выносливость и координацию через баллистические движения.',
                'category': 'Free Weights',
                'target_muscles': 'Full Body, Core, Shoulders, Legs, Grip Strength',
                'exercises': 'Kettlebell Swing, Turkish Get-Up, Goblet Squat, Kettlebell Press, Snatch, Clean'
            },
            {
                'name': 'Resistance Bands',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Эспандеры - эластичные ленты для тренировок с сопротивлением. Портативные, универсальные и безопасные для суставов.',
                'category': 'Accessories',
                'target_muscles': 'All Muscle Groups - особенно эффективны для активации мышц',
                'exercises': 'Band Pull-Aparts, Band Rows, Band Chest Press, Band Squats, Band Curls, Band Tricep Extensions'
            },
            {
                'name': 'Leg Press Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для жима ногами - безопасная альтернатива приседаниям со штангой. Позволяет работать с большими весами без нагрузки на позвоночник.',
                'category': 'Machines',
                'target_muscles': 'Quadriceps, Glutes, Hamstrings, Calves',
                'exercises': 'Leg Press, Single Leg Press, Calf Raises, Narrow Stance Press, Wide Stance Press'
            },
            {
                'name': 'Lat Pulldown Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для тяги верхнего блока - развивает широчайшие мышцы спины. Отличная альтернатива подтягиваниям для начинающих.',
                'category': 'Machines',
                'target_muscles': 'Latissimus Dorsi, Rhomboids, Biceps, Rear Deltoids',
                'exercises': 'Lat Pulldown, Wide Grip Pulldown, Close Grip Pulldown, Reverse Grip Pulldown, Behind Neck Pulldown'
            },
            {
                'name': 'Leg Extension Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для разгибания ног - изолирует квадрицепсы. Идеален для детальной проработки передней поверхности бедра.',
                'category': 'Machines',
                'target_muscles': 'Quadriceps',
                'exercises': 'Leg Extension, Single Leg Extension, Partial Reps, Drop Sets'
            },
            {
                'name': 'Leg Curl Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для сгибания ног - изолирует заднюю поверхность бедра. Важен для баланса развития мышц ног.',
                'category': 'Machines',
                'target_muscles': 'Hamstrings, Glutes',
                'exercises': 'Leg Curl, Lying Leg Curl, Standing Leg Curl, Single Leg Curl'
            },
            {
                'name': 'Chest Press Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для жима от груди - безопасная альтернатива жиму лежа. Подходит для новичков и реабилитации.',
                'category': 'Machines',
                'target_muscles': 'Chest, Anterior Deltoids, Triceps',
                'exercises': 'Chest Press, Incline Chest Press, Decline Chest Press, Single Arm Press'
            },
            {
                'name': 'Shoulder Press Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для жима над головой - развивает дельтовидные мышцы и трицепсы. Стабильная платформа для безопасного жима.',
                'category': 'Machines',
                'target_muscles': 'Shoulders (Anterior, Medial Deltoids), Triceps, Upper Chest',
                'exercises': 'Shoulder Press, Seated Shoulder Press, Single Arm Press, Partial Reps'
            },
            {
                'name': 'Rowing Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для гребли - развивает мышцы спины и задние дельты. Отличное упражнение для осанки и силы спины.',
                'category': 'Machines',
                'target_muscles': 'Latissimus Dorsi, Rhomboids, Rear Deltoids, Biceps, Core',
                'exercises': 'Seated Row, Wide Grip Row, Close Grip Row, Single Arm Row, Reverse Grip Row'
            },
            {
                'name': 'Hack Squat Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер Гаккеншмидта - наклонная платформа для приседаний. Безопасная альтернатива приседаниям со штангой с акцентом на квадрицепсы.',
                'category': 'Machines',
                'target_muscles': 'Quadriceps, Glutes, Hamstrings, Calves',
                'exercises': 'Hack Squat, Narrow Stance Hack Squat, Wide Stance Hack Squat, Calf Raises'
            },
            {
                'name': 'Pec Deck Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер "Бабочка" - изолирует грудные мышцы через сведение рук. Отлично дополняет базовые жимовые упражнения.',
                'category': 'Machines',
                'target_muscles': 'Pectoralis Major, Anterior Deltoids',
                'exercises': 'Pec Deck Fly, Reverse Pec Deck (Rear Delts), Single Arm Fly'
            },
            {
                'name': 'Preacher Curl Bench',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Скамья Скотта - изолирует бицепсы, исключая читинг. Идеальна для детальной проработки бицепсов.',
                'category': 'Equipment',
                'target_muscles': 'Biceps, Brachialis',
                'exercises': 'Preacher Curl, Barbell Preacher Curl, Dumbbell Preacher Curl, Hammer Curl'
            },
            {
                'name': 'Pull-Up Bar',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Турник - базовое упражнение для развития спины и силы хвата. Одно из лучших упражнений для верхней части тела.',
                'category': 'Equipment',
                'target_muscles': 'Latissimus Dorsi, Biceps, Rhomboids, Rear Deltoids, Core',
                'exercises': 'Pull-Ups, Chin-Ups, Wide Grip Pull-Ups, Close Grip Pull-Ups, L-Sit Pull-Ups'
            },
            {
                'name': 'Dip Station',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Брусья - эффективное упражнение для трицепсов, груди и плеч. Отличное базовое упражнение с собственным весом.',
                'category': 'Equipment',
                'target_muscles': 'Triceps, Chest, Anterior Deltoids, Core',
                'exercises': 'Dips, Chest Dips, Weighted Dips, Assisted Dips, L-Sit Dips'
            },
            {
                'name': 'Abdominal Crunch Machine',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
                'description': 'Тренажер для пресса - изолирует мышцы живота с дополнительным отягощением. Эффективен для развития силы кора.',
                'category': 'Machines',
                'target_muscles': 'Rectus Abdominis, Obliques, Core',
                'exercises': 'Crunches, Weighted Crunches, Twisting Crunches, Decline Crunches'
            },
        ]
        
        equipment_ids = {}
        for eq in equipment_data:
            equipment_id = self.add_equipment(eq['name'], eq['image'], eq['description'], eq['category'])
            equipment_ids[eq['name']] = equipment_id
        
        # Расширенный список упражнений для каждого тренажера
        exercises_data = [
            # Dumbbell exercises
            ('Dumbbell', 'Bicep Curls', 'Biceps', 'Beginner', None, 
             'Стойте прямо, ноги на ширине плеч. Держите гантели по бокам, ладони вперед. Сгибайте локти, поднимая гантели к плечам. Медленно опускайте.', '3x10-12', '10-12', '60-90 seconds'),
            ('Dumbbell', 'Shoulder Press', 'Shoulders, Triceps', 'Intermediate', None,
             'Сядьте или встаньте прямо. Поднимите гантели до уровня плеч. Выжмите вверх над головой, полностью выпрямляя руки. Медленно опустите.', '3x8-10', '8-10', '90-120 seconds'),
            ('Dumbbell', 'Tricep Extensions', 'Triceps', 'Beginner', None,
             'Поднимите гантель над головой обеими руками. Медленно согните локти, опуская гантель за голову. Выжмите обратно вверх.', '3x10-12', '10-12', '60-90 seconds'),
            ('Dumbbell', 'Chest Press', 'Chest, Shoulders, Triceps', 'Intermediate', None,
             'Лягте на скамью. Держите гантели на уровне груди. Выжмите вверх до полного выпрямления рук. Медленно опустите.', '3x8-10', '8-10', '90-120 seconds'),
            ('Dumbbell', 'Dumbbell Rows', 'Back, Biceps', 'Intermediate', None,
             'Наклонитесь вперед, опираясь на скамью. Тяните гантели к поясу, сводя лопатки. Медленно опустите.', '3x8-10', '8-10', '90-120 seconds'),
            ('Dumbbell', 'Lunges', 'Quadriceps, Glutes, Hamstrings', 'Intermediate', None,
             'Сделайте шаг вперед, опуская заднее колено к полу. Оттолкнитесь передней ногой, возвращаясь в исходное положение.', '3x10-12', '10-12', '60-90 seconds'),
            
            # Barbell exercises
            ('Barbell', 'Deadlift', 'Back, Glutes, Hamstrings, Core', 'Advanced', None,
             'Стойте над штангой, ноги на ширине плеч. Наклонитесь, держа спину прямой. Поднимите штангу, разгибая бедра и колени. Опустите контролируемо.', '3x5', '5', '3-5 minutes'),
            ('Barbell', 'Squat', 'Quadriceps, Glutes, Core', 'Intermediate', None,
             'Поместите штангу на верх трапеций. Ноги на ширине плеч. Опуститесь, сгибая колени, до параллели бедер с полом. Поднимитесь, выпрямляя ноги.', '3x8-10', '8-10', '2-3 minutes'),
            ('Barbell', 'Bench Press', 'Chest, Shoulders, Triceps', 'Intermediate', None,
             'Лягте на скамью. Снимите штангу со стоек. Опустите к груди контролируемо. Выжмите вверх до полного выпрямления.', '3x6-8', '6-8', '2-3 minutes'),
            ('Barbell', 'Overhead Press', 'Shoulders, Triceps, Core', 'Intermediate', None,
             'Стойте прямо, штанга на уровне плеч. Выжмите вверх над головой. Медленно опустите к плечам.', '3x6-8', '6-8', '2-3 minutes'),
            ('Barbell', 'Barbell Rows', 'Back, Biceps, Rear Delts', 'Intermediate', None,
             'Наклонитесь вперед, держа штангу. Тяните к поясу, сводя лопатки. Медленно опустите.', '3x8-10', '8-10', '90-120 seconds'),
            
            # Bench exercises
            ('Bench', 'Incline Dumbbell Press', 'Upper Chest, Shoulders', 'Intermediate', None,
             'Установите скамью под углом 30-45°. Лягте, держите гантели на уровне груди. Выжмите вверх и вперед.', '3x8-10', '8-10', '90-120 seconds'),
            ('Bench', 'Decline Bench Press', 'Lower Chest, Triceps', 'Intermediate', None,
             'Установите скамью под отрицательным углом. Выполняйте жим лежа, акцентируя нижнюю часть груди.', '3x8-10', '8-10', '90-120 seconds'),
            ('Bench', 'Dumbbell Flyes', 'Chest', 'Intermediate', None,
             'Лягте на скамью, гантели над грудью. Разведите руки в стороны по дуге. Сведите обратно.', '3x10-12', '10-12', '60-90 seconds'),
            
            # Cable Machine exercises
            ('Cable Machine', 'Cable Flyes', 'Chest', 'Intermediate', None,
             'Установите тросы на уровне плеч. Возьмите рукоятки, сделайте шаг вперед. Сведите руки перед собой по дуге.', '3x10-12', '10-12', '60-90 seconds'),
            ('Cable Machine', 'Cable Rows', 'Back, Biceps', 'Intermediate', None,
             'Сядьте, ноги зафиксированы. Тяните рукоятку к поясу, сводя лопатки. Медленно верните.', '3x10-12', '10-12', '60-90 seconds'),
            ('Cable Machine', 'Cable Curls', 'Biceps', 'Beginner', None,
             'Стойте перед тросом. Возьмите рукоятку снизу. Сгибайте локти, подтягивая к плечам.', '3x10-12', '10-12', '60-90 seconds'),
            ('Cable Machine', 'Tricep Pushdowns', 'Triceps', 'Beginner', None,
             'Стойте перед тросом. Возьмите рукоятку сверху. Разгибайте локти, опуская рукоятку вниз.', '3x10-12', '10-12', '60-90 seconds'),
            ('Cable Machine', 'Lat Pulldowns', 'Latissimus Dorsi, Biceps', 'Intermediate', None,
             'Сядьте, зафиксируйте ноги. Тяните рукоятку к груди широким хватом. Медленно верните.', '3x8-10', '8-10', '90-120 seconds'),
            
            # Smith Machine exercises
            ('Smith Machine', 'Smith Squat', 'Quadriceps, Glutes', 'Intermediate', None,
             'Поместите штангу на плечи. Ноги на ширине плеч. Опуститесь в присед. Поднимитесь.', '3x8-10', '8-10', '2-3 minutes'),
            ('Smith Machine', 'Smith Bench Press', 'Chest, Shoulders, Triceps', 'Intermediate', None,
             'Лягте на скамью под тренажером. Снимите штангу. Выполняйте жим лежа с направляющими.', '3x6-8', '6-8', '2-3 minutes'),
            
            # Kettlebell exercises
            ('Kettlebell', 'Kettlebell Swing', 'Full Body, Core, Glutes', 'Intermediate', None,
             'Стойте, гиря между ног. Наклонитесь, возьмите гирю. Взрывным движением поднимите до уровня груди.', '3x15-20', '15-20', '60-90 seconds'),
            ('Kettlebell', 'Goblet Squat', 'Quadriceps, Glutes, Core', 'Beginner', None,
             'Держите гирю у груди. Опуститесь в присед, колени не выходят за носки. Поднимитесь.', '3x10-12', '10-12', '60-90 seconds'),
            ('Kettlebell', 'Turkish Get-Up', 'Full Body, Core, Stability', 'Advanced', None,
             'Лягте, держите гирю над собой. Поднимитесь через серию движений, сохраняя гирю над головой.', '2x3-5', '3-5', '2-3 minutes'),
            
            # Resistance Bands exercises
            ('Resistance Bands', 'Band Pull-Aparts', 'Rear Delts, Rhomboids', 'Beginner', None,
             'Держите ленту перед собой на ширине плеч. Разведите руки в стороны, сводя лопатки.', '3x15-20', '15-20', '30-60 seconds'),
            ('Resistance Bands', 'Band Rows', 'Back, Biceps', 'Beginner', None,
             'Закрепите ленту. Тяните к поясу, сводя лопатки. Медленно верните.', '3x12-15', '12-15', '60-90 seconds'),
            
            # Leg Press Machine exercises
            ('Leg Press Machine', 'Leg Press', 'Quadriceps, Glutes, Hamstrings', 'Beginner', None,
             'Сядьте в тренажер, ноги на платформе на ширине плеч. Опустите платформу, сгибая колени. Выжмите обратно.', '3x10-12', '10-12', '90-120 seconds'),
            ('Leg Press Machine', 'Single Leg Press', 'Quadriceps, Glutes', 'Intermediate', None,
             'Выполняйте жим одной ногой для большей изоляции и баланса.', '3x8-10', '8-10', '90-120 seconds'),
            ('Leg Press Machine', 'Calf Raises', 'Calves', 'Beginner', None,
             'Поставьте носки на край платформы. Поднимитесь на носки. Медленно опустите.', '3x15-20', '15-20', '60-90 seconds'),
            
            # Lat Pulldown Machine exercises
            ('Lat Pulldown Machine', 'Lat Pulldown', 'Latissimus Dorsi, Biceps', 'Beginner', None,
             'Сядьте, зафиксируйте ноги. Широким хватом тяните рукоятку к груди. Медленно верните.', '3x8-10', '8-10', '90-120 seconds'),
            ('Lat Pulldown Machine', 'Close Grip Pulldown', 'Latissimus Dorsi, Biceps', 'Intermediate', None,
             'Узким хватом тяните рукоятку к груди, акцентируя бицепсы.', '3x8-10', '8-10', '90-120 seconds'),
            
            # Leg Extension Machine exercises
            ('Leg Extension Machine', 'Leg Extension', 'Quadriceps', 'Beginner', None,
             'Сядьте, зафиксируйте ноги под валиками. Разгибайте колени, поднимая вес. Медленно опустите.', '3x10-12', '10-12', '60-90 seconds'),
            ('Leg Extension Machine', 'Single Leg Extension', 'Quadriceps', 'Intermediate', None,
             'Выполняйте разгибание одной ногой для большей изоляции.', '3x8-10', '8-10', '60-90 seconds'),
            
            # Leg Curl Machine exercises
            ('Leg Curl Machine', 'Leg Curl', 'Hamstrings', 'Beginner', None,
             'Лягте лицом вниз, зафиксируйте ноги под валиками. Сгибайте колени, поднимая вес. Медленно опустите.', '3x10-12', '10-12', '60-90 seconds'),
            ('Leg Curl Machine', 'Standing Leg Curl', 'Hamstrings', 'Intermediate', None,
             'Стойте, зафиксируйте одну ногу. Сгибайте колено, поднимая вес.', '3x10-12', '10-12', '60-90 seconds'),
            
            # Chest Press Machine exercises
            ('Chest Press Machine', 'Chest Press', 'Chest, Shoulders, Triceps', 'Beginner', None,
             'Сядьте, спина прижата к спинке. Выжмите рукоятки вперед. Медленно верните.', '3x8-10', '8-10', '90-120 seconds'),
            
            # Shoulder Press Machine exercises
            ('Shoulder Press Machine', 'Shoulder Press', 'Shoulders, Triceps', 'Beginner', None,
             'Сядьте, спина прижата. Выжмите рукоятки вверх над головой. Медленно опустите.', '3x8-10', '8-10', '90-120 seconds'),
            
            # Rowing Machine exercises
            ('Rowing Machine', 'Seated Row', 'Back, Biceps, Rear Delts', 'Intermediate', None,
             'Сядьте, ноги зафиксированы. Тяните рукоятку к поясу, сводя лопатки. Медленно верните.', '3x10-12', '10-12', '90-120 seconds'),
            ('Rowing Machine', 'Wide Grip Row', 'Latissimus Dorsi, Rhomboids', 'Intermediate', None,
             'Широким хватом тяните к груди, акцентируя широчайшие.', '3x8-10', '8-10', '90-120 seconds'),
            
            # Hack Squat Machine exercises
            ('Hack Squat Machine', 'Hack Squat', 'Quadriceps, Glutes', 'Intermediate', None,
             'Встаньте в тренажер, плечи под подушками. Опуститесь в присед. Выжмите обратно.', '3x8-10', '8-10', '2-3 minutes'),
            
            # Pec Deck Machine exercises
            ('Pec Deck Machine', 'Pec Deck Fly', 'Chest, Anterior Deltoids', 'Intermediate', None,
             'Сядьте, локти на подушках. Сведите руки перед собой. Медленно разведите.', '3x10-12', '10-12', '60-90 seconds'),
            
            # Preacher Curl Bench exercises
            ('Preacher Curl Bench', 'Preacher Curl', 'Biceps', 'Beginner', None,
             'Сядьте, рука на скамье. Сгибайте локоть, поднимая вес. Медленно опустите.', '3x10-12', '10-12', '60-90 seconds'),
            
            # Pull-Up Bar exercises
            ('Pull-Up Bar', 'Pull-Ups', 'Latissimus Dorsi, Biceps', 'Intermediate', None,
             'Повисните на турнике широким хватом. Подтянитесь до касания перекладины подбородком. Медленно опуститесь.', '3x5-10', '5-10', '2-3 minutes'),
            ('Pull-Up Bar', 'Chin-Ups', 'Biceps, Latissimus Dorsi', 'Beginner', None,
             'Узким обратным хватом подтягивайтесь к перекладине.', '3x5-10', '5-10', '2-3 minutes'),
            
            # Dip Station exercises
            ('Dip Station', 'Dips', 'Triceps, Chest, Shoulders', 'Intermediate', None,
             'Поднимитесь на брусьях. Опуститесь, сгибая локти. Выжмите обратно вверх.', '3x8-12', '8-12', '90-120 seconds'),
            ('Dip Station', 'Chest Dips', 'Chest, Anterior Deltoids', 'Intermediate', None,
             'Наклонитесь вперед при выполнении отжиманий, акцентируя грудь.', '3x8-12', '8-12', '90-120 seconds'),
            
            # Abdominal Crunch Machine exercises
            ('Abdominal Crunch Machine', 'Weighted Crunches', 'Rectus Abdominis', 'Beginner', None,
             'Сядьте, зафиксируйте ноги. Выполняйте скручивания с дополнительным весом.', '3x12-15', '12-15', '60-90 seconds'),
        ]
        
        for equipment_name, name, muscles, difficulty, video_url, instructions, sets, reps, rest_time in exercises_data:
            if equipment_name in equipment_ids:
                equipment_id = equipment_ids[equipment_name]
                self.add_exercise(equipment_id, name, muscles, difficulty, video_url, instructions, sets, reps, rest_time)
        
        # Добавляем тренировки
        workout_data = [
            ('Upper Body Strength', [1, 2, 3, 4], 45, 'Intermediate', 'Chest, Shoulders, Arms', 'Complete upper body workout focusing on strength'),
            ('Full Body Beginner', [1, 3, 6], 30, 'Beginner', 'Full Body', 'Beginner-friendly full body workout'),
            ('Advanced Powerlifting', [5, 6, 7], 60, 'Advanced', 'Full Body', 'Heavy compound movements for strength'),
        ]
        
        for name, exercise_ids, duration, difficulty, target_muscles, description in workout_data:
            self.add_workout(name, exercise_ids, duration, difficulty, target_muscles, description)
    
    # ==================== USER WORKOUT PLANS ====================
    
    def save_user_workout_plan(self, user_id: int, plan_text: str, plan_data: str = None, week_schedule: str = None) -> int:
        """Сохранить или обновить план тренировок пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Проверяем, есть ли уже план
            cursor.execute('SELECT id FROM user_workout_plans WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем существующий план
                cursor.execute('''
                    UPDATE user_workout_plans 
                    SET plan_text = ?, plan_data = ?, week_schedule = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (plan_text, plan_data, week_schedule, user_id))
                conn.commit()
                return existing['id']
            else:
                # Создаем новый план
                cursor.execute('''
                    INSERT INTO user_workout_plans (user_id, plan_text, plan_data, week_schedule)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, plan_text, plan_data, week_schedule))
                conn.commit()
                return cursor.lastrowid
    
    def get_user_workout_plan(self, user_id: int = 1) -> Optional[Dict]:
        """Получить план тренировок пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_workout_plans WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1', (user_id,))
            row = cursor.fetchone()
            if row:
                plan = dict(row)
                # Парсим JSON поля если они есть
                if plan.get('plan_data'):
                    try:
                        plan['plan_data'] = json.loads(plan['plan_data'])
                    except:
                        pass
                if plan.get('week_schedule'):
                    try:
                        plan['week_schedule'] = json.loads(plan['week_schedule'])
                    except:
                        pass
                return plan
            return None
    
    # ==================== RECOMMENDED EQUIPMENT (GAME MECHANICS) ====================
    
    def add_recommended_equipment(self, user_id: int, equipment_name: str) -> int:
        """Добавить рекомендуемое оборудование для пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Проверяем, не добавлено ли уже
            cursor.execute('SELECT id FROM recommended_equipment WHERE user_id = ? AND equipment_name = ?', 
                          (user_id, equipment_name))
            existing = cursor.fetchone()
            if existing:
                return existing['id']
            
            cursor.execute('''
                INSERT INTO recommended_equipment (user_id, equipment_name, status)
                VALUES (?, ?, 'recommended')
            ''', (user_id, equipment_name))
            conn.commit()
            return cursor.lastrowid
    
    def mark_equipment_found(self, user_id: int, equipment_name: str) -> bool:
        """Отметить оборудование как найденное"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE recommended_equipment 
                SET status = 'found', found_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND equipment_name = ?
            ''', (user_id, equipment_name))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_equipment_to_plan(self, user_id: int, equipment_name: str) -> bool:
        """Добавить оборудование в план тренировок"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE recommended_equipment 
                SET status = 'added', added_to_plan = 1
                WHERE user_id = ? AND equipment_name = ?
            ''', (user_id, equipment_name))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_recommended_equipment(self, user_id: int = 1) -> List[Dict]:
        """Получить список рекомендуемого оборудования"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM recommended_equipment 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== WORKOUT TRACKING ====================
    
    def start_workout_tracking(self, user_id: int, workout_date: str) -> int:
        """Начать трекинг тренировки"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO workout_tracking (user_id, workout_date, start_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, workout_date))
            conn.commit()
            return cursor.lastrowid
    
    def update_workout_tracking(self, tracking_id: int, **kwargs) -> bool:
        """Обновить данные трекинга тренировки"""
        allowed_fields = ['end_time', 'duration_minutes', 'exercises_completed', 
                         'heart_rate_avg', 'heart_rate_max', 'calories_burned', 'notes']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field == 'exercises_completed' and isinstance(value, (list, dict)):
                    value = json.dumps(value)
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(tracking_id)
        query = f"UPDATE workout_tracking SET {', '.join(updates)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def get_workout_tracking(self, user_id: int, workout_date: str = None) -> List[Dict]:
        """Получить данные трекинга тренировок"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if workout_date:
                cursor.execute('''
                    SELECT * FROM workout_tracking 
                    WHERE user_id = ? AND workout_date = ?
                    ORDER BY start_time DESC
                ''', (user_id, workout_date))
            else:
                cursor.execute('''
                    SELECT * FROM workout_tracking 
                    WHERE user_id = ?
                    ORDER BY workout_date DESC, start_time DESC
                    LIMIT 50
                ''', (user_id,))
            
            results = []
            for row in cursor.fetchall():
                tracking = dict(row)
                if tracking.get('exercises_completed'):
                    try:
                        tracking['exercises_completed'] = json.loads(tracking['exercises_completed'])
                    except:
                        pass
                results.append(tracking)
            return results
    
    def close(self):
        """Закрыть соединение с базой данных"""
        pass  # SQLite автоматически закрывает соединения


# Пример использования
if __name__ == "__main__":
    # Создание экземпляра базы данных
    db = DatabaseManager()
    
    # Заполнение примерными данными
    db.populate_sample_data()
    
    # Получение статистики
    stats = db.get_equipment_stats()
    print("Database Statistics:")
    print(f"Total Equipment: {stats['total_equipment']}")
    print(f"Total Exercises: {stats['total_exercises']}")
    print(f"Total Workouts: {stats['total_workouts']}")
    
    # Получение всех упражнений для гантелей
    dumbbell_exercises = db.get_exercises(equipment_id=1)
    print(f"\nDumbbell Exercises: {len(dumbbell_exercises)}")
    
    # Получение тренировки с деталями упражнений
    workout = db.get_workout_with_exercises(1)
    if workout:
        print(f"\nWorkout: {workout['name']}")
        print(f"Exercises: {len(workout['exercise_details'])}")

# =============== Compatibility functions for main.py ===============

# Global database manager instance
_db_manager = None

def init_db():
    """Initialize database - compatibility function"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_db():
    """Get database manager instance - compatibility function"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager