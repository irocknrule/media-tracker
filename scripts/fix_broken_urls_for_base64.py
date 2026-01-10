#!/usr/bin/env python3
"""
Fix broken exercise image URLs with working alternatives before converting to base64.
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

# Working image URLs (verified to be accessible)
WORKING_URLS = {
    "Leg Press": "https://www.gymvisual.com/img/p/2/6/8/9/7/26897.gif",
    "dumbbell-thrusters": "https://www.gymvisual.com/img/p/2/4/6/5/7/24657.gif",
    "Calf Raises": "https://www.gymvisual.com/img/p/1/5/4/3/5/15435.gif",
    "dumbbell-step-up": "https://www.gymvisual.com/img/p/1/0/3/4/3/10343.gif",
    "Indoor running": "https://www.gymvisual.com/img/p/1/0/2/5/6/10256.gif",
    "Farmer Walks": "https://www.gymvisual.com/img/p/3/8/0/1/38001.gif",
    "Dumbbell Skull-Crusher": "https://www.gymvisual.com/img/p/7/7/1/0/7710.gif",
    "Barbell Overhead Press": "https://www.gymvisual.com/img/p/1/9/4/8/3/19483.gif",
    "Front Barbell Squat": "https://www.gymvisual.com/img/p/1/1/4/3/8/11438.gif",
    "Lunges": "https://www.gymvisual.com/img/p/1/0/4/6/1/10461.gif",
    "Outdoor Running": "https://www.gymvisual.com/img/p/3/7/8/8/3/37883.gif",
    "dumbell-lunges": "https://www.gymvisual.com/img/p/1/0/4/6/1/10461.gif",
    "Rear Deltoid Row": "https://www.gymvisual.com/img/p/1/9/8/8/7/19887.gif",
    "Dumbbell Tricep Extensions": "https://www.gymvisual.com/img/p/7/7/1/7/7717.gif",
    "Rowing": "https://www.gymvisual.com/img/p/2/9/1/0/2/29102.gif",
    "dumbbell-shrugs": "https://www.gymvisual.com/img/p/5/0/4/1/5041.gif",
    "Dumbbell Incline Press": "https://www.gymvisual.com/img/p/4/1/4/8/4148.gif",
    "renegade-row": "https://www.gymvisual.com/img/p/1/8/0/3/2/18032.gif",
    "Bulgarian Split Squat": "https://www.gymvisual.com/img/p/2/3/8/5/2/23852.gif",
    "Outdoor Biking": "https://www.gymvisual.com/img/p/3/7/8/8/1/37881.gif",
    "Indoor Biking": "https://www.gymvisual.com/img/p/2/9/1/0/1/29101.gif",
    "dumbbell-goblet-squat": "https://www.gymvisual.com/img/p/1/8/4/0/3/18403.gif",
}


def fix_broken_urls():
    """Replace broken image URLs with working alternatives"""
    
    print("=" * 70)
    print("FIXING BROKEN EXERCISE IMAGE URLS")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        fixed_count = 0
        
        for exercise_name, new_url in WORKING_URLS.items():
            exercise = db.query(Exercise).filter(Exercise.name == exercise_name).first()
            
            if exercise:
                old_url = exercise.image_url
                exercise.image_url = new_url
                fixed_count += 1
                print(f"  ✓ Fixed: {exercise_name}")
                print(f"    New URL: {new_url}")
            else:
                print(f"  ⚠️  Not found: {exercise_name}")
        
        db.commit()
        
        print("\n" + "=" * 70)
        print(f"FIXED {fixed_count} BROKEN IMAGE URLS")
        print("=" * 70)
        print("\nNow run convert_exercise_images_to_base64.py to convert them!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    fix_broken_urls()

