"""
ML inference module for equipment recognition
For MVP, uses smart mock based on filename and database
In production, load TensorFlow Lite model here
"""
import random
import os
from database import DatabaseManager

# Extended equipment classes from database
EQUIPMENT_CLASSES = [
    'Dumbbell', 'Barbell', 'Bench', 'Cable Machine', 'Smith Machine',
    'Kettlebell', 'Resistance Bands', 'Leg Press Machine', 'Lat Pulldown Machine',
    'Leg Extension Machine', 'Leg Curl Machine', 'Chest Press Machine',
    'Shoulder Press Machine', 'Rowing Machine', 'Hack Squat Machine',
    'Pec Deck Machine', 'Preacher Curl Bench', 'Pull-Up Bar', 'Dip Station',
    'Abdominal Crunch Machine'
]

def predict_equipment(image_path: str) -> dict:
    """
    Predict equipment type from image using smart heuristics
    
    Args:
        image_path: Path to the image file
        
    Returns:
        dict with 'equipment' and 'confidence' keys
    """
    # Try to get equipment from database first
    dbm = DatabaseManager()
    all_equipment = dbm.get_equipment()
    
    if all_equipment and len(all_equipment) > 0:
        # Use database equipment list
        equipment_names = [eq['name'] for eq in all_equipment]
    else:
        equipment_names = EQUIPMENT_CLASSES
    
    # Smart prediction based on filename (if contains keywords)
    filename_lower = os.path.basename(image_path).lower()
    
    # Keyword matching for better predictions
    equipment_keywords = {
        'dumbbell': ['dumbbell', 'dumb', 'гантел'],
        'barbell': ['barbell', 'bar', 'штанга'],
        'bench': ['bench', 'скамья', 'скамейка'],
        'cable machine': ['cable', 'трос', 'блок'],
        'smith machine': ['smith', 'смит'],
        'kettlebell': ['kettlebell', 'kettle', 'гиря'],
        'leg press machine': ['leg press', 'жим ногами'],
        'lat pulldown machine': ['pulldown', 'тяга верхнего блока'],
        'leg extension machine': ['extension', 'разгибание'],
        'leg curl machine': ['curl', 'сгибание'],
        'chest press machine': ['chest press', 'жим от груди'],
        'shoulder press machine': ['shoulder press', 'жим над головой'],
        'rowing machine': ['row', 'гребля'],
        'hack squat machine': ['hack', 'гакк'],
        'pec deck machine': ['pec deck', 'бабочка'],
        'pull-up bar': ['pull', 'pullup', 'турник'],
        'dip station': ['dip', 'брусья'],
    }
    
    # Try to match by filename
    predicted_equipment = None
    confidence = 0.85
    
    for eq_name, keywords in equipment_keywords.items():
        if any(keyword in filename_lower for keyword in keywords):
            # Check if equipment exists in database
            if eq_name in equipment_names or any(eq_name.lower() in name.lower() for name in equipment_names):
                predicted_equipment = eq_name
                confidence = 0.92
                break
    
    # If no match, use most common equipment from database
    if not predicted_equipment:
        if all_equipment:
            # Use equipment with most exercises
            equipment_with_exercises = []
            for eq in all_equipment[:10]:  # Top 10 most common
                exercises = dbm.get_exercises(equipment_id=eq['id'])
                equipment_with_exercises.append((eq['name'], len(exercises)))
            
            if equipment_with_exercises:
                equipment_with_exercises.sort(key=lambda x: x[1], reverse=True)
                predicted_equipment = equipment_with_exercises[0][0]
                confidence = 0.88
            else:
                predicted_equipment = all_equipment[0]['name']
                confidence = 0.85
        else:
            # Fallback to random from common classes
            predicted_equipment = random.choice(['Dumbbell', 'Barbell', 'Bench', 'Cable Machine', 'Leg Press Machine'])
            confidence = 0.80
    
    return {
        "equipment": predicted_equipment,
        "confidence": confidence
    }

def load_model():
    """Load TensorFlow Lite model (for future implementation)"""
    # import tensorflow as tf
    # interpreter = tf.lite.Interpreter(model_path="ml-model/equipment_model.tflite")
    # interpreter.allocate_tensors()
    # return interpreter
    pass


def predict_candidates(image_path: str, top_k: int = 3) -> list[dict]:
    """
    Return top-k smart predictions based on database and heuristics
    Uses diverse selection to avoid always returning the same equipment
    """
    from database import DatabaseManager
    import random
    
    dbm = DatabaseManager()
    all_equipment = dbm.get_equipment()
    
    if all_equipment and len(all_equipment) > 0:
        # Try to match by filename first
        filename_lower = os.path.basename(image_path).lower()
        
        # Keyword matching for better predictions
        equipment_keywords = {
            'Dumbbell': ['dumbbell', 'dumb', 'гантел'],
            'Barbell': ['barbell', 'bar', 'штанга'],
            'Bench': ['bench', 'скамья', 'скамейка'],
            'Cable Machine': ['cable', 'трос', 'блок'],
            'Smith Machine': ['smith', 'смит'],
            'Kettlebell': ['kettlebell', 'kettle', 'гиря'],
            'Leg Press Machine': ['leg press', 'жим ногами'],
            'Lat Pulldown Machine': ['pulldown', 'тяга верхнего блока'],
            'Leg Extension Machine': ['extension', 'разгибание'],
            'Leg Curl Machine': ['curl', 'сгибание'],
            'Chest Press Machine': ['chest press', 'жим от груди'],
            'Shoulder Press Machine': ['shoulder press', 'жим над головой'],
            'Rowing Machine': ['row', 'гребля'],
            'Hack Squat Machine': ['hack', 'гакк'],
            'Pec Deck Machine': ['pec deck', 'бабочка'],
            'Pull-Up Bar': ['pull', 'pullup', 'турник'],
            'Dip Station': ['dip', 'брусья'],
        }
        
        # Find matching equipment by keywords
        matched_equipment = []
        for eq in all_equipment:
            eq_name = eq['name']
            keywords = equipment_keywords.get(eq_name, [])
            if any(keyword in filename_lower for keyword in keywords):
                matched_equipment.append(eq_name)
        
        # If we found matches, use them as candidates
        if matched_equipment:
            candidates = []
            main_conf = 0.75
            candidates.append({"equipment": matched_equipment[0], "confidence": round(main_conf, 2)})
            
            # Add other matched equipment or diverse selection
            remaining = matched_equipment[1:top_k] if len(matched_equipment) > 1 else []
            
            # If not enough matches, add diverse equipment from database
            if len(remaining) < top_k - 1:
                # Get equipment from different categories
                equipment_names = [eq['name'] for eq in all_equipment]
                # Remove already selected
                available = [name for name in equipment_names if name not in matched_equipment]
                # Shuffle for diversity
                random.shuffle(available)
                remaining.extend(available[:top_k - 1 - len(remaining)])
            
            # Add remaining candidates with decreasing confidence
            for i, eq_name in enumerate(remaining[:top_k - 1]):
                conf = round(0.20 - (i * 0.05), 2)
                if conf > 0.05:
                    candidates.append({"equipment": eq_name, "confidence": conf})
            
            return candidates[:top_k]
        
        # No filename match - use diverse selection
        # Mix popular equipment with random selection for diversity
        equipment_names = [eq['name'] for eq in all_equipment]
        
        # Get equipment with exercises (popular)
        equipment_with_exercises = []
        for eq in all_equipment:
            exercises = dbm.get_exercises(equipment_id=eq['id'])
            if len(exercises) > 0:
                equipment_with_exercises.append(eq['name'])
        
        # Create diverse candidate list
        candidates = []
        
        # First candidate: random from popular equipment or random from all
        if equipment_with_exercises:
            main_equipment = random.choice(equipment_with_exercises)
        else:
            main_equipment = random.choice(equipment_names)
        candidates.append({"equipment": main_equipment, "confidence": round(0.70, 2)})
        
        # Remaining candidates: diverse selection
        remaining_equipment = [name for name in equipment_names if name != main_equipment]
        random.shuffle(remaining_equipment)
        
        # Mix popular and random for diversity
        for i in range(min(top_k - 1, len(remaining_equipment))):
            if i < len(equipment_with_exercises) and equipment_with_exercises[i] in remaining_equipment:
                eq_name = equipment_with_exercises[i]
            else:
                eq_name = remaining_equipment[i] if i < len(remaining_equipment) else remaining_equipment[0]
            
            conf = round(0.20 - (i * 0.04), 2)
            if conf > 0.05:
                candidates.append({"equipment": eq_name, "confidence": conf})
        
        return candidates[:top_k]
    else:
        # Fallback to diverse common equipment
        common_equipment = ['Dumbbell', 'Barbell', 'Bench', 'Cable Machine', 'Leg Press Machine', 
                           'Kettlebell', 'Smith Machine', 'Lat Pulldown Machine']
        random.shuffle(common_equipment)
        candidates = [
            {"equipment": common_equipment[0], "confidence": 0.70},
            {"equipment": common_equipment[1], "confidence": 0.20},
            {"equipment": common_equipment[2], "confidence": 0.10},
        ]
        return candidates[:top_k]

