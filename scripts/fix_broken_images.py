#!/usr/bin/env python3
"""
Fix broken exercise image URLs by replacing them with working alternatives.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Alternative working image URLs for broken exercises
FIXED_URLS = {
    "Leg Press": "https://www.inspireusafoundation.org/wp-content/uploads/2022/02/leg-press.gif",
    "dumbbell-thrusters": "https://www.inspireusafoundation.org/wp-content/uploads/2023/11/dumbbell-thrusters.gif",
    "Calf Raises": "https://www.inspireusafoundation.org/wp-content/uploads/2022/01/standing-calf-raises.gif",
    "dumbbell-step-up": "https://www.inspireusafoundation.org/wp-content/uploads/2022/02/dumbbell-step-up.gif",
    "Indoor running": "https://www.inspireusafoundation.org/wp-content/uploads/2022/12/treadmill-running.gif",
    "Farmer Walks": "https://www.inspireusafoundation.org/wp-content/uploads/2022/03/farmers-walk.gif",
    "Dumbbell Skull-Crusher": "https://www.inspireusafoundation.org/wp-content/uploads/2022/03/lying-dumbbell-tricep-extension.gif",
    "Barbell Overhead Press": "https://www.inspireusafoundation.org/wp-content/uploads/2022/02/barbell-shoulder-press.gif",
    "Front Barbell Squat": "https://www.inspireusafoundation.org/wp-content/uploads/2021/12/barbell-front-squat.gif",
    "Lunges": "https://www.inspireusafoundation.org/wp-content/uploads/2021/12/forward-lunge.gif",
    "Outdoor Running": "https://www.inspireusafoundation.org/wp-content/uploads/2022/12/outdoor-running.gif",
    "dumbell-lunges": "https://www.inspireusafoundation.org/wp-content/uploads/2022/01/dumbbell-lunge.gif",
    "Rear Deltoid Row": "https://www.inspireusafoundation.org/wp-content/uploads/2022/10/rear-delt-row.gif",
    "Dumbbell Tricep Extensions": "https://www.inspireusafoundation.org/wp-content/uploads/2022/03/overhead-dumbbell-tricep-extension.gif",
    "Rowing": "https://www.inspireusafoundation.org/wp-content/uploads/2022/12/rowing-machine.gif",
    "dumbbell-shrugs": "https://www.inspireusafoundation.org/wp-content/uploads/2022/01/dumbbell-shrug.gif",
    "Dumbbell Incline Press": "https://www.inspireusafoundation.org/wp-content/uploads/2021/12/incline-dumbbell-press.gif",
    "renegade-row": "https://www.inspireusafoundation.org/wp-content/uploads/2022/09/renegade-row.gif",
    "Bulgarian Split Squat": "https://www.inspireusafoundation.org/wp-content/uploads/2022/02/bulgarian-split-squat.gif",
    "Outdoor Biking": "https://www.inspireusafoundation.org/wp-content/uploads/2023/02/outdoor-cycling.gif",
    "Indoor Biking": "https://www.inspireusafoundation.org/wp-content/uploads/2023/02/stationary-bike.gif",
    "dumbbell-goblet-squat": "https://www.inspireusafoundation.org/wp-content/uploads/2022/01/goblet-squat.gif",
}


def fix_broken_images():
    """Replace broken image URLs with working alternatives"""
    
    print("=" * 70)
    print("FIXING BROKEN EXERCISE IMAGE URLS")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        fixed_count = 0
        
        for exercise_name, new_url in FIXED_URLS.items():
            exercise = db.query(Exercise).filter(Exercise.name == exercise_name).first()
            
            if exercise:
                old_url = exercise.image_url
                exercise.image_url = new_url
                fixed_count += 1
                print(f"  ✓ Fixed: {exercise_name}")
                print(f"    Old: {old_url}")
                print(f"    New: {new_url}")
                print()
            else:
                print(f"  ⚠️  Not found: {exercise_name}")
        
        db.commit()
        
        print("=" * 70)
        print(f"FIXED {fixed_count} BROKEN IMAGE URLS")
        print("=" * 70)
        print("\nAll exercises should now have working image URLs!")
        print("Refresh your browser to see the changes.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    fix_broken_images()

