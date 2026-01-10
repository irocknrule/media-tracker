#!/usr/bin/env python3
"""
Script to update exercises with pre-vetted image URLs from ExerciseDB.
These URLs are publicly available and don't require API calls.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

# Database setup
DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Pre-vetted exercise image URLs from ExerciseDB
# These are direct links to GIFs that are publicly available
EXERCISE_IMAGES = {
    # Chest
    "Bench Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif",
    "Barbell Bench Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif",
    "Dumbbell Incline Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Incline-Press.gif",
    
    # Back
    "Barbell Squat": "https://fitnessprogramer.com/wp-content/uploads/2021/02/BARBELL-SQUAT.gif",
    "Lat Pulldown": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Lat-Pulldown.gif",
    "single-arm-dumbbell-row": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Row.gif",
    
    # Shoulders
    "Dumbbell Shoulder Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Shoulder-Press.gif",
    "Barbell Overhead Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Military-Press.gif",
    "Arnold Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Arnold-Press.gif",
    "Side Lateral Raise": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif",
    "Dumbbell Lateral Raises": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif",
    "dumbbell-shrugs": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Shrug.gif",
    "Rear Deltoid Row": "https://fitnessprogramer.com/wp-content/uploads/2022/02/Barbell-rear-delt-row.gif",
    
    # Arms
    "Bicep Curl": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Curl.gif",
    "dumbbell-bicep-curls": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Curl.gif",
    "Hammer Curls": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Hammer-Curl.gif",
    "dumbell-hammer-curls": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Hammer-Curl.gif",
    "Dumbbell Tricep Extensions": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lying-Triceps-Extension.gif",
    "Dumbbell Skull-Crusher": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lying-Triceps-Extension.gif",
    
    # Legs
    "Leg Press": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Press.gif",
    "Front Barbell Squat": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Front-Squat.gif",
    "Bulgarian Split Squat": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Bulgarian-Split-Squat.gif",
    "Lunges": "https://fitnessprogramer.com/wp-content/uploads/2021/02/dumbbell-lunges.gif",
    "dumbell-lunges": "https://fitnessprogramer.com/wp-content/uploads/2021/02/dumbbell-lunges.gif",
    "Calf Raises": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Calf-Raises.gif",
    "dumbbell-calf-raises": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Calf-Raise.gif",
    "dumbbell-goblet-squat": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Goblet-Squat.gif",
    "dumbbell-step-up": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Step-up.gif",
    
    # Core / Full Body
    "Farmer Walks": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Farmers-Walk.gif",
    "renegade-row": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Plank-Row.gif",
    "dumbbell-thrusters": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Thruster.gif",
    
    # Cardio
    "Indoor running": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Treadmill-Running.gif",
    "Outdoor Running": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Running.gif",
    "Indoor Biking": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Stationary-Bike.gif",
    "Outdoor Biking": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Cycling.gif",
    "Rowing": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Rowing-Machine.gif",
    
    # Rear delts / reverse fly
    "dumbbell-reverse-flyes": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Reverse-Fly.gif",
}


def update_exercises_with_images():
    """Update exercises with pre-vetted image URLs"""
    
    print("=" * 70)
    print("UPDATING EXERCISES WITH CURATED IMAGE URLS")
    print("=" * 70)
    print(f"\nImages available: {len(EXERCISE_IMAGES)}")
    
    db = SessionLocal()
    
    try:
        updated_count = 0
        not_found_count = 0
        already_has_image = 0
        
        # Get all exercises
        exercises = db.query(Exercise).all()
        
        print(f"\nProcessing {len(exercises)} exercises...")
        print()
        
        for exercise in exercises:
            # Skip if already has image
            if exercise.image_url:
                already_has_image += 1
                print(f"  ⏭️  {exercise.name}: Already has image")
                continue
            
            # Check if we have an image URL for this exercise
            if exercise.name in EXERCISE_IMAGES:
                exercise.image_url = EXERCISE_IMAGES[exercise.name]
                updated_count += 1
                print(f"  ✓ {exercise.name}: Added image")
            else:
                not_found_count += 1
                print(f"  ⚠️  {exercise.name}: No image available")
        
        # Commit changes
        db.commit()
        
        print("\n" + "=" * 70)
        print("UPDATE COMPLETE")
        print("=" * 70)
        print(f"\nResults:")
        print(f"  - Already had images: {already_has_image}")
        print(f"  - Successfully updated: {updated_count}")
        print(f"  - No image available: {not_found_count}")
        print(f"  - Total with images now: {already_has_image + updated_count}")
        
        if not_found_count > 0:
            print(f"\n💡 Tip: You can manually add images for the remaining {not_found_count} exercises")
            print("   using the frontend (Workout Tracker → Exercises → Edit button)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    update_exercises_with_images()

