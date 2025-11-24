# Database models - simple data classes for compatibility
# These are used in load_sample_data function

class Exercise:
    """Exercise model"""
    def __init__(self, name, equipment_name, sets, reps, muscle_group, description):
        self.name = name
        self.equipment_name = equipment_name
        self.sets = sets
        self.reps = reps
        self.muscle_group = muscle_group
        self.description = description

class Equipment:
    """Equipment model - compatibility class"""
    def __init__(self, name=None, image=None, description=None):
        self.name = name
        self.image = image
        self.description = description

class WorkoutPlan:
    """WorkoutPlan model"""
    def __init__(self, name, duration, difficulty, exercises, estimated_calories=None):
        self.name = name
        self.duration = duration
        self.difficulty = difficulty
        self.exercises = exercises
        self.estimated_calories = estimated_calories

__all__ = ['Exercise', 'Equipment', 'WorkoutPlan']

