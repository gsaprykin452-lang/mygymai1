from pydantic import BaseModel
from typing import List, Optional, Dict

class EquipmentResponse(BaseModel):
    equipment: str
    confidence: float
    timestamp: str

class ExerciseResponse(BaseModel):
    name: str
    sets: str
    reps: str
    muscle_group: str
    description: str

class WorkoutPlanResponse(BaseModel):
    name: str
    duration: int
    difficulty: str
    exercises: List[str]
    calories: int


# =============== User Analysis & Plan Generation Schemas ===============
class UserProfile(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None  # 'male' | 'female' | 'other'
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    level: str = "beginner"  # beginner | intermediate | advanced
    goal: str = "fat_loss"  # fat_loss | muscle_gain | strength | endurance | rehab
    health_flags: Optional[List[str]] = None  # e.g., ['knee_pain', 'lower_back_pain']
    recent_muscles: Optional[List[str]] = None  # muscle groups trained recently
    workouts_per_week: Optional[int] = None
    goal_timeline: Optional[str] = None
    diet_type: Optional[str] = None
    supplements: Optional[List[str]] = []
    workout_experience: Optional[str] = None
    workout_type: Optional[List[str]] = []
    available_equipment: Optional[List[str]] = []
    workout_duration: Optional[str] = None
    preferred_time: Optional[str] = None
    injuries_limitations: Optional[str] = None
    activity_level: Optional[str] = None
    intensity_preference: Optional[str] = None
    favorite_muscle_groups: Optional[List[str]] = []
    onboarding_completed: Optional[bool] = False
    # Новые поля onboarding
    gender: Optional[str] = None  # 'male' | 'female' | 'other'
    height: Optional[str] = None  # Рост в исходных единицах
    weight: Optional[str] = None  # Вес в исходных единицах
    unitSystem: Optional[str] = None  # 'metric' | 'imperial'
    birthDate: Optional[str] = None  # Дата рождения в формате YYYY-MM-DD
    desiredWeight: Optional[float] = None  # Желаемый вес
    weightGainRate: Optional[float] = None  # Скорость набора веса (кг/неделю)
    obstacles: Optional[List[str]] = []  # Препятствия
    triedOtherApps: Optional[str] = None  # 'yes' | 'no'
    referralSource: Optional[str] = None  # Источник реферала
    workingWithTrainer: Optional[str] = None  # 'yes' | 'no'
    calorieTransfer: Optional[str] = None  # 'yes' | 'no'
    # Subscription fields
    subscription_active: Optional[bool] = False
    subscription_start_date: Optional[str] = None  # Дата начала подписки (YYYY-MM-DD)
    subscription_end_date: Optional[str] = None  # Дата окончания подписки (YYYY-MM-DD)
    subscription_price: Optional[float] = 9.99  # Цена подписки в долларах
    # Profile fields
    name: Optional[str] = None  # Имя пользователя
    profile_photo_uri: Optional[str] = None  # URI фото профиля


class PlanRequest(BaseModel):
    equipment: str
    user: UserProfile


class PlanExercise(BaseModel):
    name: str
    sets: str
    reps: str
    rest: Optional[str] = None
    muscles: Optional[List[str]] = None
    video_url: Optional[str] = None
    instructions: Optional[str] = None
    technique_tips: Optional[List[str]] = None


class PlanResponse(BaseModel):
    equipment: str
    goal: str
    level: str
    recommendation: List[PlanExercise]
    safety_notes: List[str]
    technique_tips: List[str]


# =============== Google OAuth Schemas ===============
class GoogleAuthRequest(BaseModel):
    access_token: str


class GoogleAuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict] = None

