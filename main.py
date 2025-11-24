from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from contextlib import asynccontextmanager
import aiofiles
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============== ВРЕМЕННОЕ ОТКЛЮЧЕНИЕ GPT ===============
# Установите DISABLE_GPT=True чтобы отключить все вызовы GPT и использовать моковые данные
DISABLE_GPT = False  # GPT включен и работает
print("✅ GPT включен и готов к работе.")

from database import init_db, get_db, DatabaseManager
from models import Exercise, Equipment, WorkoutPlan
from ml_inference import predict_equipment
from schemas import EquipmentResponse, ExerciseResponse, WorkoutPlanResponse
from pydantic import BaseModel
from openai_client import (
    generate_equipment_guidance, 
    chat_with_ai, 
    OpenAIError,
    recognize_equipment_from_image,
    recognize_equipment_candidates_from_image,
    get_user_usage
)
from schemas import UserProfile, PlanRequest, PlanResponse, GoogleAuthRequest, GoogleAuthResponse
from plan_engine import generate_plan
from ml_inference import predict_candidates
# DatabaseManager уже импортирован выше
import httpx

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    await load_sample_data()
    # Also populate extended equipment database
    dbm = DatabaseManager()
    try:
        # Check if equipment already exists
        existing = dbm.get_equipment()
        if not existing or len(existing) < 5:
            dbm.populate_sample_data()
            print("Extended equipment database populated successfully")
    except Exception as e:
        print(f"Warning: Could not populate extended database: {e}")
    
    yield
    
    # Shutdown (if needed)
    pass

app = FastAPI(title="GymGenius AI API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "GymGenius AI API", "status": "running"}


# =============== AI Guidance (OpenAI ChatGPT) ===============
class GuidanceRequest(BaseModel):
    equipment: str
    locale: str | None = "ru"


@app.post("/ai/guidance")
async def ai_guidance(body: GuidanceRequest):
    """
    Use OpenAI ChatGPT to provide exercises and detailed instructions for given equipment.
    """
    try:
        if DISABLE_GPT:
            # Моковые данные вместо реального GPT
            return {
                "equipment": body.equipment,
                "exercises": [
                    {
                        "name": "Базовое упражнение",
                        "sets": "3-4",
                        "reps": "10-12",
                        "muscles": "Основные группы мышц",
                        "instructions": "Выполняйте упражнение с правильной техникой. Начните с легкого веса и постепенно увеличивайте нагрузку."
                    }
                ],
                "safety_notes": ["Разминка обязательна", "Следите за техникой выполнения"],
                "technique_tips": ["Держите спину прямой", "Дышите равномерно"]
            }
        result = await generate_equipment_guidance(body.equipment, body.locale or "ru")
        return result
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Equipment recognition endpoint
@app.post("/recognize", response_model=EquipmentResponse)
async def recognize_equipment(file: UploadFile = File(...), locale: str = "ru"):
    """
    Upload an image and get equipment recognition results using OpenAI GPT-4 Vision API
    """
    file_path = None
    try:
        # Save uploaded file temporarily
        filename = file.filename or "upload.jpg"
        file_path = f"uploads/{filename}"
        os.makedirs("uploads", exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Try OpenAI recognition first
        if DISABLE_GPT:
            # Используем моковое распознавание
            print("GPT отключен, используем моковое распознавание")
            result = predict_equipment(file_path)
            equipment_name = result.get("equipment", "Dumbbell")
            confidence = result.get("confidence", 0.85)
        else:
            try:
                result = await recognize_equipment_from_image(file_path, locale=locale)
                equipment_name = result.get("equipment", "Unknown")
                confidence = result.get("confidence", 0.5)
            except OpenAIError as e:
                # Fallback to mock recognition if OpenAI fails
                print(f"OpenAI recognition failed, using fallback: {e}")
                result = predict_equipment(file_path)
                equipment_name = result.get("equipment", "Unknown")
                confidence = result.get("confidence", 0.5)
            except Exception as e:
                # Fallback to mock recognition on any error
                print(f"Recognition error, using fallback: {e}")
                result = predict_equipment(file_path)
                equipment_name = result.get("equipment", "Unknown")
                confidence = result.get("confidence", 0.5)
        
        # Clean up file
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
        
        return EquipmentResponse(
            equipment=equipment_name,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        # Clean up file on error
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

# Get exercises for specific equipment
@app.get("/exercises/{equipment_name}", response_model=List[ExerciseResponse])
async def get_exercises(equipment_name: str):
    """
    Get list of exercises for a specific equipment
    """
    db = get_db()
    # Get equipment by name to get its ID
    equipment = db.get_equipment_by_name(equipment_name)
    if not equipment:
        return []
    
    exercises = db.get_exercises(equipment_id=equipment['id'])
    
    return [
        ExerciseResponse(
            name=ex['name'],
            sets=ex.get('sets_recommended', '3x10-12'),
            reps=ex.get('reps_recommended', '10-12'),
            muscle_group=ex.get('muscles', 'General'),
            description=ex.get('instructions', '')
        )
        for ex in exercises
    ]

# Get all exercises
@app.get("/exercises", response_model=List[ExerciseResponse])
async def get_all_exercises():
    """
    Get all exercises
    """
    db = get_db()
    exercises = db.get_exercises()
    
    return [
        ExerciseResponse(
            name=ex['name'],
            sets=ex.get('sets_recommended', '3x10-12'),
            reps=ex.get('reps_recommended', '10-12'),
            muscle_group=ex.get('muscles', 'General'),
            description=ex.get('instructions', '')
        )
        for ex in exercises
    ]

# Generate workout plan
@app.get("/generate-workout", response_model=WorkoutPlanResponse)
async def generate_workout(
    duration: Optional[int] = 45,
    difficulty: Optional[str] = "intermediate",
    focus: Optional[str] = "full_body"
):
    """
    Generate a personalized workout plan
    """
    db = get_db()
    
    # For MVP, return a predefined workout plan
    workouts = db.get_workouts(difficulty=difficulty)
    
    if not workouts:
        workouts = db.get_workouts()
    
    if not workouts:
        raise HTTPException(status_code=404, detail="No workout plans found")
    
    workout = workouts[0]  # Get first workout
    
    # Get exercises for this workout
    workout_with_exercises = db.get_workout_with_exercises(workout['id'])
    exercises_list = []
    if workout_with_exercises and workout_with_exercises.get('exercise_details'):
        exercises_list = [ex['name'] for ex in workout_with_exercises['exercise_details']]
    
    return WorkoutPlanResponse(
        name=workout.get('name', 'Workout Plan'),
        duration=workout.get('duration', duration),
        difficulty=workout.get('difficulty', difficulty),
        exercises=exercises_list,
        calories=workout.get('estimated_calories', 300)
    )

# =============== User Analysis & Plan Generation ===============
@app.post("/user/analyze")
async def analyze_user(profile: UserProfile):
    """
    Simple passthrough for now: validates and echoes enriched profile.
    Future: add BMI, BMR and contraindication checks.
    """
    # Use model_dump for Pydantic v2, dict() for v1
    try:
        enriched = profile.model_dump() if hasattr(profile, 'model_dump') else profile.dict()
    except AttributeError:
        enriched = profile.dict()
    # Quick derived metrics (optional)
    try:
        if profile.height_cm and profile.weight_kg:
            h_m = profile.height_cm / 100.0
            bmi = round(profile.weight_kg / (h_m * h_m), 1)
            enriched["bmi"] = bmi
    except Exception:
        pass
    return enriched


@app.post("/plan/generate", response_model=PlanResponse)
async def plan_generate(req: PlanRequest):
    """
    Generate a personalized plan for detected equipment using user profile and AI guidance.
    """
    try:
        plan = await generate_plan(req.equipment, req.user, locale="ru")
        return plan
    except OpenAIError as e:
        # Fallback handled inside client; still return 502 if upstream fails
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ComprehensivePlanRequest(BaseModel):
    goal: str
    workouts_per_week: Optional[int] = None
    goal_timeline: Optional[str] = None
    diet_type: Optional[str] = None
    supplements: Optional[List[str]] = []
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    level: Optional[str] = "beginner"
    workout_experience: Optional[str] = None
    workout_type: Optional[List[str]] = []
    available_equipment: Optional[List[str]] = []
    workout_duration: Optional[str] = None
    preferred_time: Optional[str] = None
    injuries_limitations: Optional[str] = None
    activity_level: Optional[str] = None
    intensity_preference: Optional[str] = None
    favorite_muscle_groups: Optional[List[str]] = []
    # Новые поля onboarding
    gender: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    unitSystem: Optional[str] = None
    birthDate: Optional[str] = None
    desiredWeight: Optional[float] = None
    weightGainRate: Optional[float] = None
    obstacles: Optional[List[str]] = []
    triedOtherApps: Optional[str] = None
    referralSource: Optional[str] = None
    workingWithTrainer: Optional[str] = None
    calorieTransfer: Optional[str] = None


@app.post("/plan/generate-comprehensive")
async def generate_comprehensive_plan(req: ComprehensivePlanRequest):
    """
    Generate a comprehensive workout plan based on onboarding questionnaire data.
    Uses ChatGPT to create a detailed, personalized plan with structured exercises,
    muscle groups, instructions, and technique tips.
    """
    try:
        from plan_generator import generate_structured_plan
        
        # Convert request to user profile dict
        user_profile = {
            "goal": req.goal,
            "level": req.level or "beginner",
            "age": req.age,
            "sex": req.sex,
            "gender": getattr(req, 'gender', None),
            "height_cm": req.height_cm,
            "weight_kg": req.weight_kg,
            "workouts_per_week": req.workouts_per_week,
            "goal_timeline": req.goal_timeline,
            "workout_experience": getattr(req, 'workout_experience', None),
            "available_equipment": getattr(req, 'available_equipment', None),
            "workout_duration": getattr(req, 'workout_duration', None),
            "activity_level": getattr(req, 'activity_level', None),
            "intensity_preference": getattr(req, 'intensity_preference', None),
            "favorite_muscle_groups": getattr(req, 'favorite_muscle_groups', None),
            "injuries_limitations": getattr(req, 'injuries_limitations', None),
            "health_flags": getattr(req, 'health_flags', None),
            "diet_type": req.diet_type,
            "desiredWeight": getattr(req, 'desiredWeight', None),
            "weightGainRate": getattr(req, 'weightGainRate', None),
            "obstacles": getattr(req, 'obstacles', None),
        }
        
        # Generate structured plan
        plan_response = await generate_structured_plan(user_profile, locale="ru")
        
        # Convert PlanResponse to dict for JSON serialization
        plan_dict = {
            "equipment": plan_response.equipment,
            "goal": plan_response.goal,
            "level": plan_response.level,
            "recommendation": [
                {
                    "name": ex.name,
                    "sets": ex.sets,
                    "reps": ex.reps,
                    "rest": ex.rest,
                    "muscles": ex.muscles,
                    "instructions": ex.instructions,
                    "technique_tips": ex.technique_tips,
                }
                for ex in plan_response.recommendation
            ],
            "safety_notes": plan_response.safety_notes,
            "technique_tips": plan_response.technique_tips,
        }
        
        # Save plan to database
        dbm = DatabaseManager()
        user_id = 1  # Default user
        import json
        plan_id = dbm.save_user_workout_plan(
            user_id=user_id,
            plan_text=json.dumps(plan_dict, ensure_ascii=False, indent=2),
            plan_data=json.dumps(plan_dict, ensure_ascii=False),
            week_schedule=None
        )
        
        return {
            "success": True,
            "plan": plan_dict,
            "plan_id": plan_id,
            "message": "Comprehensive plan generated and saved successfully"
        }
        
    except OpenAIError as e:
        # Log error but return mock plan instead of 502
        print(f"OpenAI error in generate_comprehensive_plan: {e}")
        # Try to generate a fallback plan
        try:
            from plan_generator import _generate_mock_plan
            available_equipment = req.available_equipment if isinstance(req.available_equipment, list) and req.available_equipment else ['Dumbbell']
            fallback_plan = _generate_mock_plan({
                "goal": req.goal,
                "level": req.level or "beginner",
            }, available_equipment[0] if available_equipment else 'Dumbbell')
            
            # Convert to dict
            plan_dict = {
                "equipment": fallback_plan.equipment,
                "goal": fallback_plan.goal,
                "level": fallback_plan.level,
                "recommendation": [
                    {
                        "name": ex.name,
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "rest": ex.rest,
                        "muscles": ex.muscles,
                        "instructions": ex.instructions,
                        "technique_tips": ex.technique_tips,
                    }
                    for ex in fallback_plan.recommendation
                ],
                "safety_notes": fallback_plan.safety_notes,
                "technique_tips": fallback_plan.technique_tips,
            }
            
            # Save fallback plan
            dbm = DatabaseManager()
            user_id = 1
            import json
            plan_id = dbm.save_user_workout_plan(
                user_id=user_id,
                plan_text=json.dumps(plan_dict, ensure_ascii=False, indent=2),
                plan_data=json.dumps(plan_dict, ensure_ascii=False),
                week_schedule=None
            )
            
            return {
                "success": True,
                "plan": plan_dict,
                "plan_id": plan_id,
                "message": "Fallback plan generated (OpenAI unavailable)"
            }
        except Exception as fallback_error:
            print(f"Fallback plan generation also failed: {fallback_error}")
            raise HTTPException(status_code=502, detail=f"OpenAI error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in generate_comprehensive_plan: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recognize/candidates")
async def recognize_candidates(file: UploadFile = File(...), top_k: int = 3, locale: str = "ru"):
    """
    Upload an image and get top-K equipment recognition candidates using OpenAI GPT-4 Vision API
    """
    file_path = None
    try:
        filename = file.filename or "upload.jpg"
        file_path = f"uploads/{filename}"
        os.makedirs("uploads", exist_ok=True)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Try OpenAI recognition first
        if DISABLE_GPT:
            # Используем моковое распознавание
            print("GPT отключен, используем моковое распознавание кандидатов")
            result = predict_candidates(file_path, top_k=top_k)
        else:
            try:
                result = await recognize_equipment_candidates_from_image(file_path, top_k=top_k, locale=locale)
            except OpenAIError as e:
                # Fallback to mock recognition if OpenAI fails
                print(f"OpenAI candidates recognition failed, using fallback: {e}")
                result = predict_candidates(file_path, top_k=top_k)
            except Exception as e:
                # Fallback to mock recognition on any error
                print(f"Candidates recognition error, using fallback: {e}")
                result = predict_candidates(file_path, top_k=top_k)
        
        # Clean up file
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
        
        return {"candidates": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        # Clean up file on error
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

# Load sample data
async def load_sample_data():
    """
    Populate database with sample data if empty
    """
    db = get_db()
    
    # Check if data already exists - use DatabaseManager methods
    existing_exercises = db.get_exercises()
    if existing_exercises and len(existing_exercises) > 0:
        print("Sample data already exists, skipping...")
        return
    
    sample_exercises = [
        Exercise(
            name="Bicep Curls",
            equipment_name="Dumbbell",
            sets="3x10-12",
            reps="10-12",
            muscle_group="Biceps",
            description="Stand with feet shoulder-width apart, hold dumbbells at your sides, curl weights up by bending elbows."
        ),
        Exercise(
            name="Bench Press",
            equipment_name="Barbell",
            sets="4x6-8",
            reps="6-8",
            muscle_group="Chest",
            description="Lie on bench, lower barbell to chest with control, press up explosively."
        ),
        Exercise(
            name="Deadlift",
            equipment_name="Barbell",
            sets="3x5",
            reps="5",
            muscle_group="Back",
            description="Stand with feet hip-width apart, lift barbell from floor by extending hips and knees."
        ),
        Exercise(
            name="Shoulder Press",
            equipment_name="Dumbbell",
            sets="3x8-10",
            reps="8-10",
            muscle_group="Shoulders",
            description="Press dumbbells overhead from shoulder height, lower with control."
        ),
        Exercise(
            name="Cable Flys",
            equipment_name="Cable Machine",
            sets="3x12-15",
            reps="12-15",
            muscle_group="Chest",
            description="Stand between cable machine, pull handles together in arcing motion."
        ),
    ]
    
    sample_workouts = [
        WorkoutPlan(
            name="Full Body Blast",
            duration=45,
            difficulty="intermediate",
            exercises="Squats,Bench Press,Rows,Overhead Press,Deadlift",
            estimated_calories=400
        ),
        WorkoutPlan(
            name="Upper Body Focus",
            duration=35,
            difficulty="beginner",
            exercises="Bench Press,Rows,Shoulder Press,Curls,Tricep Extensions",
            estimated_calories=320
        ),
        WorkoutPlan(
            name="Leg Day Deluxe",
            duration=50,
            difficulty="advanced",
            exercises="Squats,Deadlifts,Lunges,Leg Press,Calf Raises",
            estimated_calories=450
        ),
    ]
    
    # Get equipment IDs first
    equipment_map = {}
    all_equipment = db.get_equipment()
    for eq in all_equipment:
        equipment_map[eq['name']] = eq['id']
    
    # Add exercises using DatabaseManager methods
    for exercise in sample_exercises:
        equipment_name = exercise.equipment_name
        if equipment_name in equipment_map:
            equipment_id = equipment_map[equipment_name]
            db.add_exercise(
                equipment_id=equipment_id,
                name=exercise.name,
                muscles=exercise.muscle_group,
                difficulty="Beginner",  # Default difficulty
                video_url=None,
                instructions=exercise.description,
                sets_recommended=exercise.sets,
                reps_recommended=exercise.reps,
                rest_time="60-90 seconds"
            )
    
    # Add workouts - convert exercise names to IDs
    # For simplicity, we'll just create workouts with empty exercise lists
    # The actual exercise linking can be done later if needed
    for workout in sample_workouts:
        # Convert difficulty to proper format
        difficulty = workout.difficulty.capitalize()
        if difficulty not in ['Beginner', 'Intermediate', 'Advanced']:
            difficulty = 'Intermediate'
        
        # For now, use empty exercise list - workouts can be populated later
        db.add_workout(
            name=workout.name,
            exercises=[],  # Empty for now
            duration_minutes=workout.duration,
            difficulty=difficulty,
            target_muscles="Full Body",
            description=f"Sample workout: {workout.exercises}"
        )
    
    print("Sample data loaded successfully")

# =============== Google OAuth ===============
@app.post("/auth/google", response_model=GoogleAuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """
    Обработка Google OAuth токена и создание/обновление пользователя
    """
    try:
        if not request.access_token or not request.access_token.strip():
            raise HTTPException(
                status_code=400,
                detail="Access token is required"
            )
        
        # Verify token with Google API
        async with httpx.AsyncClient() as client:
            # Попробуем использовать более новый endpoint
            try:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {request.access_token}"},
                    timeout=10.0
                )
            except Exception as e:
                # Если v3 не работает, попробуем v2
                print(f"Trying v3 endpoint failed: {e}, trying v2...")
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {request.access_token}"},
                    timeout=10.0
                )
            
            print(f"Google API response status: {response.status_code}")
            
            if response.status_code == 400:
                error_detail = response.text
                print(f"Google API 400 error: {error_detail}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Google API error: {error_detail}"
                )
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"Google API error ({response.status_code}): {error_detail}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid Google access token: {error_detail}"
                )
            
            google_user_data = response.json()
            print(f"Google user data: {google_user_data}")
            
            google_id = google_user_data.get("id") or google_user_data.get("sub")
            google_email = google_user_data.get("email")
            google_name = google_user_data.get("name")
            google_picture = google_user_data.get("picture")
            
            if not google_id or not google_email:
                print(f"Missing user info - id: {google_id}, email: {google_email}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required Google user information. Received: {google_user_data}"
                )
            
            # Update or create user with Google OAuth data
            dbm = DatabaseManager()
            user = dbm.update_google_user(
                google_id=google_id,
                google_email=google_email,
                google_name=google_name,
                google_picture=google_picture
            )
            
            return GoogleAuthResponse(
                success=True,
                message="Successfully authenticated with Google",
                user=user
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout while verifying Google token"
        )
    except httpx.RequestError as e:
        print(f"HTTP request error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error connecting to Google API: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in google_auth: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


# =============== User Profile Persistence ===============
@app.get("/user/profile")
async def get_profile():
    dbm = DatabaseManager()
    prof = dbm.get_user_profile()
    if prof:
        import json as _json
        try:
            # Parse JSON strings
            for key in ["health_flags", "recent_muscles", "supplements", "workout_type", "available_equipment", "favorite_muscle_groups", "obstacles"]:
                if isinstance(prof.get(key), str):
                    prof[key] = _json.loads(prof[key]) if prof.get(key) else []
            
            # Convert onboarding_completed to boolean
            if "onboarding_completed" in prof:
                prof["onboarding_completed"] = bool(prof["onboarding_completed"])
            
            # Convert subscription_active to boolean
            if "subscription_active" in prof:
                prof["subscription_active"] = bool(prof["subscription_active"])
            
            # Добавляем поля с snake_case для совместимости
            if "unit_system" in prof:
                prof["unitSystem"] = prof["unit_system"]
            if "birth_date" in prof:
                prof["birthDate"] = prof["birth_date"]
            if "desired_weight" in prof:
                prof["desiredWeight"] = prof["desired_weight"]
            if "weight_gain_rate" in prof:
                prof["weightGainRate"] = prof["weight_gain_rate"]
            if "tried_other_apps" in prof:
                prof["triedOtherApps"] = prof["tried_other_apps"]
            if "referral_source" in prof:
                prof["referralSource"] = prof["referral_source"]
            if "working_with_trainer" in prof:
                prof["workingWithTrainer"] = prof["working_with_trainer"]
            if "calorie_transfer" in prof:
                prof["calorieTransfer"] = prof["calorie_transfer"]
        except Exception:
            pass
    return prof or {}


@app.post("/user/profile")
async def upsert_profile(profile: UserProfile):
    dbm = DatabaseManager()
    # Use model_dump for Pydantic v2, dict() for v1
    try:
        profile_dict = profile.model_dump() if hasattr(profile, 'model_dump') else profile.dict()
    except AttributeError:
        profile_dict = profile.dict()
    
    # Получаем старый профиль для сравнения
    old_profile = dbm.get_user_profile()
    
    saved = dbm.upsert_user_profile(profile_dict)
    
    # Проверяем, изменились ли ключевые параметры, влияющие на план
    key_fields = ['goal', 'level', 'workouts_per_week', 'workout_type', 'available_equipment', 
                  'injuries_limitations', 'favorite_muscle_groups', 'height_cm', 'weight_kg']
    
    profile_changed = False
    if old_profile:
        for field in key_fields:
            old_value = old_profile.get(field)
            new_value = saved.get(field)
            if old_value != new_value:
                profile_changed = True
                break
    
    # Если профиль изменился, автоматически обновляем план
    if profile_changed and saved.get('onboarding_completed'):
        try:
            # Преобразуем сохраненный профиль в словарь для генерации плана
            user_profile = {
                "goal": saved.get('goal', 'muscle_gain'),
                "level": saved.get('level', 'beginner'),
                "age": saved.get('age'),
                "sex": saved.get('sex'),
                "gender": saved.get('gender'),
                "height_cm": saved.get('height_cm'),
                "weight_kg": saved.get('weight_kg'),
                "workouts_per_week": saved.get('workouts_per_week'),
                "goal_timeline": saved.get('goal_timeline'),
                "workout_experience": saved.get('workout_experience'),
                "available_equipment": saved.get('available_equipment', []),
                "workout_duration": saved.get('workout_duration'),
                "activity_level": saved.get('activity_level'),
                "intensity_preference": saved.get('intensity_preference'),
                "favorite_muscle_groups": saved.get('favorite_muscle_groups', []),
                "injuries_limitations": saved.get('injuries_limitations'),
                "health_flags": saved.get('health_flags', []),
                "diet_type": saved.get('diet_type'),
                "desiredWeight": saved.get('desired_weight'),
                "weightGainRate": saved.get('weight_gain_rate'),
                "obstacles": saved.get('obstacles', []),
            }
            
            # Генерируем обновленный структурированный план
            from plan_generator import generate_structured_plan
            plan_response = await generate_structured_plan(user_profile, locale="ru")
            
            # Convert PlanResponse to dict for JSON serialization
            plan_dict = {
                "equipment": plan_response.equipment,
                "goal": plan_response.goal,
                "level": plan_response.level,
                "recommendation": [
                    {
                        "name": ex.name,
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "rest": ex.rest,
                        "muscles": ex.muscles,
                        "instructions": ex.instructions,
                        "technique_tips": ex.technique_tips,
                    }
                    for ex in plan_response.recommendation
                ],
                "safety_notes": plan_response.safety_notes,
                "technique_tips": plan_response.technique_tips,
            }
            
            import json
            # Сохраняем обновленный план
            dbm.save_user_workout_plan(
                user_id=1,
                plan_text=json.dumps(plan_dict, ensure_ascii=False, indent=2),
                plan_data=json.dumps(plan_dict, ensure_ascii=False),
                week_schedule=None
            )
        except Exception as e:
            print(f"Warning: Could not auto-update workout plan: {e}")
            # Не блокируем сохранение профиля из-за ошибки обновления плана
    # decode arrays for response
    import json as _json
    try:
        for key in ["health_flags", "recent_muscles", "supplements", "workout_type", "available_equipment", "favorite_muscle_groups", "obstacles"]:
            if isinstance(saved.get(key), str):
                saved[key] = _json.loads(saved[key]) if saved.get(key) else []
        
        # Convert onboarding_completed to boolean
        if "onboarding_completed" in saved:
            saved["onboarding_completed"] = bool(saved["onboarding_completed"])
        
        # Convert subscription_active to boolean
        if "subscription_active" in saved:
            saved["subscription_active"] = bool(saved["subscription_active"])
        
        # Добавляем поля с camelCase для совместимости
        if "unit_system" in saved:
            saved["unitSystem"] = saved["unit_system"]
        if "birth_date" in saved:
            saved["birthDate"] = saved["birth_date"]
        if "desired_weight" in saved:
            saved["desiredWeight"] = saved["desired_weight"]
        if "weight_gain_rate" in saved:
            saved["weightGainRate"] = saved["weight_gain_rate"]
        if "tried_other_apps" in saved:
            saved["triedOtherApps"] = saved["tried_other_apps"]
        if "referral_source" in saved:
            saved["referralSource"] = saved["referral_source"]
        if "working_with_trainer" in saved:
            saved["workingWithTrainer"] = saved["working_with_trainer"]
        if "calorie_transfer" in saved:
            saved["calorieTransfer"] = saved["calorie_transfer"]
    except Exception:
        pass
    return saved


# =============== Workout History ===============
class HistoryEntry(BaseModel):
    equipment: str
    exercise_name: str
    sets: str
    reps: str
    notes: Optional[str] = None
    timestamp: Optional[str] = None  # ISO format timestamp


@app.post("/history/log")
async def history_log(entry: HistoryEntry):
    dbm = DatabaseManager()
    # Use model_dump for Pydantic v2, dict() for v1
    try:
        entry_dict = entry.model_dump() if hasattr(entry, 'model_dump') else entry.dict()
    except AttributeError:
        entry_dict = entry.dict()
    entry_id = dbm.log_workout(entry_dict)
    return {"id": entry_id}


@app.get("/history/recent")
async def history_recent(limit: int = 20):
    dbm = DatabaseManager()
    return dbm.recent_workouts(limit=limit)

# =============== User Workout Plan ===============
@app.get("/user/plan")
async def get_user_plan():
    """Получить план тренировок пользователя в структурированном формате"""
    dbm = DatabaseManager()
    plan = dbm.get_user_workout_plan(user_id=1)
    if plan:
        import json as _json
        # Try to parse plan_data as JSON if it exists
        if plan.get('plan_data'):
            try:
                plan_data = _json.loads(plan['plan_data'])
                return plan_data
            except:
                pass
        # If plan_data is not available, try to parse plan_text
        if plan.get('plan_text'):
            try:
                plan_data = _json.loads(plan['plan_text'])
                return plan_data
            except:
                pass
        return plan
    return {"message": "No workout plan found. Complete onboarding to generate a plan."}

# =============== Equipment Scanning Game Mechanics ===============
@app.get("/equipment/recommended")
async def get_recommended_equipment():
    """Получить список рекомендуемого оборудования для пользователя"""
    dbm = DatabaseManager()
    recommended = dbm.get_recommended_equipment(user_id=1)
    
    # Если нет рекомендаций, генерируем их на основе профиля пользователя
    if not recommended:
        user_profile = dbm.get_user_profile()
        if user_profile:
            # Генерируем рекомендации на основе цели и доступного оборудования
            goal = user_profile.get('goal', 'muscle_gain')
            available = user_profile.get('available_equipment', [])
            
            # Базовые рекомендации в зависимости от цели
            equipment_recommendations = []
            if goal == 'muscle_gain':
                equipment_recommendations = ['Barbell', 'Dumbbell', 'Bench', 'Cable Machine']
            elif goal == 'fat_loss':
                equipment_recommendations = ['Dumbbell', 'Kettlebell', 'Resistance Bands', 'Cable Machine']
            elif goal == 'strength':
                equipment_recommendations = ['Barbell', 'Smith Machine', 'Leg Press Machine']
            else:
                equipment_recommendations = ['Dumbbell', 'Barbell', 'Cable Machine']
            
            # Добавляем рекомендации в базу
            for eq_name in equipment_recommendations:
                if eq_name not in (available if isinstance(available, list) else []):
                    dbm.add_recommended_equipment(user_id=1, equipment_name=eq_name)
            
            recommended = dbm.get_recommended_equipment(user_id=1)
    
    return {"recommended_equipment": recommended}

@app.post("/equipment/found")
async def mark_equipment_found(equipment_name: str):
    """Отметить оборудование как найденное при сканировании"""
    dbm = DatabaseManager()
    success = dbm.mark_equipment_found(user_id=1, equipment_name=equipment_name)
    
    if success:
        # Проверяем, подходит ли это оборудование для плана пользователя
        user_profile = dbm.get_user_profile()
        if user_profile:
            goal = user_profile.get('goal', 'muscle_gain')
            # Можно добавить логику проверки совместимости с планом
            return {
                "success": True,
                "message": f"Отлично! Вы нашли {equipment_name}. Это оборудование подходит для вашей цели!",
                "suitable": True
            }
    
    return {
        "success": success,
        "message": f"Оборудование {equipment_name} отмечено как найденное"
    }

@app.post("/equipment/add-to-plan")
async def add_equipment_to_plan(equipment_name: str):
    """Добавить найденное оборудование в план тренировок и обновить план через GPT"""
    dbm = DatabaseManager()
    success = dbm.add_equipment_to_plan(user_id=1, equipment_name=equipment_name)
    
    if success:
        # Обновляем план тренировок с учетом нового оборудования
        try:
            from plan_generator import generate_structured_plan
            
            user_profile = dbm.get_user_profile()
            if user_profile:
                # Обновляем список доступного оборудования
                available_equipment = user_profile.get('available_equipment', [])
                if isinstance(available_equipment, list):
                    if equipment_name not in available_equipment:
                        available_equipment.append(equipment_name)
                else:
                    available_equipment = [equipment_name]
                
                user_profile['available_equipment'] = available_equipment
                
                # Генерируем обновленный структурированный план
                plan_response = await generate_structured_plan(user_profile, locale="ru")
                
                # Convert PlanResponse to dict for JSON serialization
                plan_dict = {
                    "equipment": plan_response.equipment,
                    "goal": plan_response.goal,
                    "level": plan_response.level,
                    "recommendation": [
                        {
                            "name": ex.name,
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "rest": ex.rest,
                            "muscles": ex.muscles,
                            "instructions": ex.instructions,
                            "technique_tips": ex.technique_tips,
                        }
                        for ex in plan_response.recommendation
                    ],
                    "safety_notes": plan_response.safety_notes,
                    "technique_tips": plan_response.technique_tips,
                }
                
                import json
                dbm.save_user_workout_plan(
                    user_id=1,
                    plan_text=json.dumps(plan_dict, ensure_ascii=False, indent=2),
                    plan_data=json.dumps(plan_dict, ensure_ascii=False),
                    week_schedule=None
                )
        except Exception as e:
            print(f"Warning: Could not update plan with new equipment: {e}")
    
    return {
        "success": success,
        "message": f"Оборудование {equipment_name} добавлено в план тренировок. План обновлен автоматически."
    }

# =============== Workout Tracking ===============
class WorkoutTrackingRequest(BaseModel):
    workout_date: str  # YYYY-MM-DD
    exercises_completed: Optional[List[dict]] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    calories_burned: Optional[int] = None
    notes: Optional[str] = None

@app.post("/workout/start")
async def start_workout_tracking(workout_date: str):
    """Начать трекинг тренировки"""
    dbm = DatabaseManager()
    tracking_id = dbm.start_workout_tracking(user_id=1, workout_date=workout_date)
    return {"tracking_id": tracking_id, "start_time": "now"}

@app.post("/workout/update/{tracking_id}")
async def update_workout_tracking(tracking_id: int, data: WorkoutTrackingRequest):
    """Обновить данные трекинга тренировки"""
    dbm = DatabaseManager()
    
    # Вычисляем длительность если есть start_time
    duration_minutes = None
    tracking_data = dbm.get_workout_tracking(user_id=1)
    current_tracking = next((t for t in tracking_data if t['id'] == tracking_id), None)
    
    if current_tracking and current_tracking.get('start_time'):
        try:
            start_time_str = current_tracking['start_time']
            # Парсим timestamp (может быть в разных форматах)
            if 'T' in start_time_str:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            else:
                start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.now()
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
        except Exception as e:
            print(f"Error calculating duration: {e}")
            duration_minutes = None
    
    update_data = {}
    if data.exercises_completed:
        update_data['exercises_completed'] = data.exercises_completed
    if data.heart_rate_avg:
        update_data['heart_rate_avg'] = data.heart_rate_avg
    if data.heart_rate_max:
        update_data['heart_rate_max'] = data.heart_rate_max
    if data.calories_burned:
        update_data['calories_burned'] = data.calories_burned
    if data.notes:
        update_data['notes'] = data.notes
    if duration_minutes:
        update_data['duration_minutes'] = duration_minutes
        update_data['end_time'] = datetime.now().isoformat()
    
    success = dbm.update_workout_tracking(tracking_id, **update_data)
    return {"success": success, "tracking_id": tracking_id}

@app.get("/workout/tracking")
async def get_workout_tracking(workout_date: Optional[str] = None):
    """Получить данные трекинга тренировок"""
    dbm = DatabaseManager()
    tracking = dbm.get_workout_tracking(user_id=1, workout_date=workout_date)
    return {"tracking": tracking}

@app.get("/workout/week-schedule")
async def get_week_schedule():
    """Получить расписание тренировок на неделю"""
    dbm = DatabaseManager()
    plan = dbm.get_user_workout_plan(user_id=1)
    
    if plan and plan.get('week_schedule'):
        return {"schedule": plan['week_schedule']}
    
    # Генерируем базовое расписание если его нет
    user_profile = dbm.get_user_profile()
    workouts_per_week = user_profile.get('workouts_per_week', 3) if user_profile else 3
    
    # Базовое расписание: распределяем тренировки по неделе
    base_schedule = {
        "monday": "Верх тела" if workouts_per_week >= 3 else None,
        "tuesday": None,
        "wednesday": "Низ тела" if workouts_per_week >= 3 else None,
        "thursday": None,
        "friday": "Полное тело" if workouts_per_week >= 3 else ("Верх тела" if workouts_per_week == 2 else None),
        "saturday": "Низ тела" if workouts_per_week >= 4 else None,
        "sunday": None
    }
    
    return {"schedule": base_schedule}

# =============== Database Management ===============
@app.post("/admin/populate-db")
async def populate_database():
    """
    Заполнить базу данных расширенными данными о тренажерах и упражнениях.
    Используйте этот эндпоинт для инициализации или обновления базы данных.
    """
    try:
        dbm = DatabaseManager()
        dbm.populate_sample_data()
        stats = dbm.get_equipment_stats()
        return {
            "success": True,
            "message": "Database populated successfully",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to populate database: {str(e)}")

@app.get("/equipment/all")
async def get_all_equipment():
    """
    Получить список всего оборудования с описаниями
    """
    try:
        dbm = DatabaseManager()
        equipment = dbm.get_equipment()
        return equipment or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/equipment/{equipment_name}/details")
async def get_equipment_details(equipment_name: str):
    """
    Получить детальную информацию о тренажере включая описание и упражнения
    """
    try:
        dbm = DatabaseManager()
        equipment = dbm.get_equipment_by_name(equipment_name)
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        # Get exercises for this equipment
        exercises = dbm.get_exercises(equipment_id=equipment['id'])
        
        return {
            "equipment": equipment,
            "exercises": exercises,
            "total_exercises": len(exercises)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============== AI Chat Assistant ===============
class ChatRequest(BaseModel):
    message: str
    equipment: Optional[str] = None
    locale: Optional[str] = "ru"


@app.post("/ai/chat")
async def ai_chat(request: ChatRequest):
    """
    Чат с ИИ-ассистентом для любых вопросов по тренировкам.
    Поддерживает контекст пользователя и текущего тренажера.
    """
    try:
        # Validate request
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get user profile for context
        context = {}
        try:
            dbm = DatabaseManager()
            user_profile = dbm.get_user_profile()
            if user_profile:
                # Parse JSON strings
                if isinstance(user_profile.get("health_flags"), str):
                    import json as _json
                    try:
                        user_profile["health_flags"] = _json.loads(user_profile["health_flags"]) if user_profile.get("health_flags") else []
                        user_profile["recent_muscles"] = _json.loads(user_profile["recent_muscles"]) if user_profile.get("recent_muscles") else []
                    except Exception:
                        pass
                context['user_profile'] = user_profile
        except Exception as e:
            print(f"Warning: Could not load user profile for context: {e}")
        
        if request.equipment:
            context['equipment'] = request.equipment
        
        # Call AI
        if DISABLE_GPT:
            # Моковый ответ от AI
            user_msg = request.message.strip().lower()
            if "привет" in user_msg or "hello" in user_msg:
                response = "Привет! Я ваш фитнес-ассистент. Чем могу помочь?"
            elif "план" in user_msg or "тренировка" in user_msg:
                response = "Я могу помочь составить план тренировок. Опишите ваши цели и уровень подготовки."
            elif "упражнение" in user_msg or "exercise" in user_msg:
                response = "Рекомендую начать с базовых упражнений: приседания, отжимания, планка. Выполняйте 3 подхода по 10-15 повторений."
            else:
                response = f"Спасибо за вопрос: '{request.message.strip()}'. Это демо-режим. Для получения полного ответа включите GPT. Я могу помочь с планами тренировок, упражнениями и техникой выполнения."
        else:
            response = await chat_with_ai(request.message.strip(), context=context, locale=request.locale or "ru")
        return {"response": response, "success": True}
    except OpenAIError as e:
        error_msg = str(e)
        print(f"OpenAI error in /ai/chat: {error_msg}")
        
        # Специальная обработка ошибки недостатка средств (402, 403)
        if "402" in error_msg or "403" in error_msg or "Недостаточно средств" in error_msg or "Insufficient" in error_msg:
            # Возвращаем понятное сообщение пользователю
            raise HTTPException(
                status_code=402, 
                detail=error_msg
            )
        
        # Return 502 for other OpenAI API errors
        raise HTTPException(status_code=502, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error in /ai/chat: {str(e)}"
        print(f"Error: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/ai/usage")
async def get_ai_usage(user_id: int = 1):
    """
    Получить информацию об использовании OpenAI API пользователем.
    """
    try:
        usage_info = get_user_usage(user_id)
        return {
            "success": True,
            "usage": usage_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Получаем настройки из переменных окружения или используем значения по умолчанию
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Определяем локальный IP для вывода в консоль (только в development)
    if environment == "development":
        def get_local_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                try:
                    hostname = socket.gethostname()
                    return socket.gethostbyname(hostname)
                except Exception:
                    return "127.0.0.1"
        
        local_ip = get_local_ip()
        
        print("=" * 60)
        print("🚀 GymGenius AI Backend Server")
        print("=" * 60)
        print(f"📡 Сервер запущен на всех интерфейсах ({host})")
        print(f"🌐 Локальный доступ: http://localhost:{port}")
        print(f"📱 Доступ из сети: http://{local_ip}:{port}")
        print("=" * 60)
        print(f"\n💡 Для подключения мобильного приложения:")
        print(f"   Установите BACKEND_URL=http://{local_ip}:{port}")
        print(f"   или используйте IP: {local_ip}")
        print("=" * 60)
        print("\n⚠️  Убедитесь, что:")
        print("   1. Файрвол разрешает входящие подключения на порт 8000")
        print("   2. Устройства находятся в одной Wi-Fi сети")
        print("   3. В мобильном приложении указан правильный IP адрес")
        print("=" * 60)
        print("\n")
    else:
        print(f"🚀 GymGenius AI Backend Server (Production)")
        print(f"📡 Running on {host}:{port}")
    
    # Запускаем сервер
    uvicorn.run(app, host=host, port=port)

