#!/usr/bin/env python3
"""
Script to fetch exercise images from ExerciseDB (RapidAPI) and update the database.
This uses a free API that provides exercise images and GIFs.

Usage:
1. Get a free API key from https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb
2. Set environment variable: export RAPIDAPI_KEY=your_key_here
3. Run: python scripts/fetch_exercise_images.py
"""

import os
import sys
from pathlib import Path
import requests
from time import sleep

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

# Database setup
DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# Exercise name mapping (your database name -> API search term)
EXERCISE_NAME_MAP = {
    "Deadlift": "deadlift",
    "Barbell Squat": "barbell squat",
    "Bench Press": "barbell bench press",
    "Barbell Bench Press": "barbell bench press",
    "Romanian Deadlift": "romanian deadlift",
    "Bent-over Barbell Row": "barbell row",
    "barbell-bent-over-row": "barbell row",
    "Dumbbell Shoulder Press": "dumbbell shoulder press",
    "Dumbbell Lateral Raises": "dumbbell lateral raise",
    "Dumbbell Incline Press": "dumbbell incline press",
    "Dumbbell Rear Delt Fly": "dumbbell rear delt fly",
    "dumbbell-rear-delt-fly": "dumbbell rear delt fly",
    "Dumbbell Tricep Extensions": "dumbbell tricep extension",
    "dumbbell-bicep-curls": "dumbbell curl",
    "Bicep Curl": "dumbbell curl",
    "Hammer Curls": "hammer curl",
    "dumbell-hammer-curls": "hammer curl",
    "Bulgarian Split Squat": "bulgarian split squat",
    "Lunges": "dumbbell lunge",
    "dumbell-lunges": "dumbbell lunge",
    "Calf Raises": "calf raise",
    "dumbbell-calf-raises": "dumbbell calf raise",
    "Lat Pulldown": "lat pulldown",
    "Leg Press": "leg press",
    "Arnold Press": "arnold press",
    "Front Barbell Squat": "front squat",
    "Barbell Overhead Press": "barbell overhead press",
    "Side Lateral Raise": "dumbbell lateral raise",
    "Rear Deltoid Row": "rear delt row",
    "single-arm-dumbbell-row": "dumbbell row",
    "dumbbell-goblet-squat": "goblet squat",
    "dumbbell-reverse-flyes": "dumbbell reverse fly",
    "Dumbbell Skull-Crusher": "dumbbell skull crusher",
    "dumbbell-shrugs": "dumbbell shrug",
    "renegade-row": "renegade row",
    "dumbbell-step-up": "step up",
    "Single-leg deadlift": "single leg deadlift",
    "single-leg-rdl": "single leg rdl",
    "Farmer Walks": "farmer walk",
    "dumbbell-thrusters": "dumbbell thruster",
}


def fetch_from_exercisedb(api_key: str, exercise_name: str):
    """Fetch exercise data from ExerciseDB API"""
    
    # Map exercise name to search term
    search_term = EXERCISE_NAME_MAP.get(exercise_name, exercise_name.lower())
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
    }
    
    try:
        # First, try searching by name
        url = "https://exercisedb.p.rapidapi.com/exercises/name/" + search_term.replace(" ", "%20")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Return the first matching exercise
                return data[0].get('gifUrl')
        
        # If name search fails, try getting all exercises and searching manually
        # (This is a fallback - only use for exercises that don't match)
        print(f"    Trying alternative search method...")
        url = "https://exercisedb.p.rapidapi.com/exercises"
        params = {"limit": "1000"}
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            all_exercises = response.json()
            
            # Search for matching exercise name
            for exercise in all_exercises:
                ex_name = exercise.get('name', '').lower()
                if search_term.lower() in ex_name or ex_name in search_term.lower():
                    return exercise.get('gifUrl')
        
        return None
    
    except Exception as e:
        print(f"    Error fetching from API: {e}")
        return None


def update_exercise_images_from_api():
    """Update exercise images using ExerciseDB API"""
    
    # Check for API key
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        print("=" * 70)
        print("ERROR: RAPIDAPI_KEY environment variable not set")
        print("=" * 70)
        print("\nTo use this script:")
        print("1. Get a free API key from: https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb")
        print("2. Set the environment variable: export RAPIDAPI_KEY=your_key_here")
        print("3. Run this script again")
        print("\nNote: Free tier allows 10 requests/month")
        return
    
    print("=" * 70)
    print("UPDATING EXERCISE IMAGES FROM EXERCISEDB API")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Get all exercises without images
        exercises = db.query(Exercise).filter(
            (Exercise.image_url == None) | (Exercise.image_url == '')
        ).all()
        
        print(f"\nFound {len(exercises)} exercises without images")
        print("\nFetching images from ExerciseDB API...")
        
        updated_count = 0
        failed_count = 0
        
        for exercise in exercises:
            print(f"\n  Processing: {exercise.name}")
            
            # Fetch image URL from API
            image_url = fetch_from_exercisedb(api_key, exercise.name)
            
            if image_url:
                exercise.image_url = image_url
                updated_count += 1
                print(f"    ✓ Found: {image_url}")
            else:
                failed_count += 1
                print(f"    ✗ No image found")
            
            # Rate limiting - be nice to the API
            sleep(0.5)
        
        # Commit changes
        db.commit()
        
        print("\n" + "=" * 70)
        print("UPDATE COMPLETE")
        print("=" * 70)
        print(f"\nResults:")
        print(f"  - Successfully updated: {updated_count}")
        print(f"  - Failed to find: {failed_count}")
        print(f"  - Total processed: {len(exercises)}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
    
    finally:
        db.close()


def use_local_obsidian_gifs():
    """Map local Obsidian GIFs to exercises"""
    
    print("=" * 70)
    print("MAPPING LOCAL OBSIDIAN GIFS TO EXERCISES")
    print("=" * 70)
    
    # Mapping of exercise names to local GIF files
    local_mappings = {
        "Deadlift": "_assets/deadlift-2.gif",
        "deadlift": "_assets/deadlift-2.gif",
        "Romanian Deadlift": "_assets/Romanian-Deadlift.gif",
        "romanian-deadlifts": "_assets/Romanian-Deadlift.gif",
        "Bent-over Barbell Row": "_assets/bai-tap-bent-over-barbell-row.gif",
        "barbell-bent-over-row": "_assets/bai-tap-bent-over-barbell-row.gif",
        "Dumbbell Rear Delt Fly": "_assets/dumbbell-rear-delt-fly.webp",
        "dumbbell-rear-delt-fly": "_assets/dumbbell-rear-delt-fly.webp",
        "Single-leg deadlift": "_assets/opposite_arm_leg_dumbbell_straight_leg_deadlift.gif",
        "single-leg-rdl": "_assets/opposite_arm_leg_dumbbell_straight_leg_deadlift.gif",
    }
    
    db = SessionLocal()
    
    try:
        updated_count = 0
        
        for exercise_name, gif_path in local_mappings.items():
            exercise = db.query(Exercise).filter(Exercise.name == exercise_name).first()
            
            if exercise:
                exercise.image_url = f"/obsidian/{gif_path}"
                updated_count += 1
                print(f"  ✓ Mapped: {exercise_name} -> {gif_path}")
        
        db.commit()
        
        print(f"\n✓ Successfully mapped {updated_count} local GIFs")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
    
    finally:
        db.close()


def main():
    """Main function"""
    print("\nExercise Image Updater")
    print("=" * 70)
    print("\nOptions:")
    print("1. Use local Obsidian GIFs (for exercises that have them)")
    print("2. Fetch from ExerciseDB API (requires free API key)")
    print("3. Both (recommended)")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    if choice == "1":
        use_local_obsidian_gifs()
    elif choice == "2":
        update_exercise_images_from_api()
    elif choice == "3":
        use_local_obsidian_gifs()
        print("\n")
        update_exercise_images_from_api()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()

