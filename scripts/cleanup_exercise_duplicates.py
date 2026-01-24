#!/usr/bin/env python3
"""
Script to find and remove duplicate exercises in the database.
Merges hyphenated duplicates (e.g., "dumbbell-bench-press") with proper format (e.g., "Dumbbell Bench Press").
"""

import sys
import re
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise, ExerciseRecord, WorkoutExercise

# Database setup - use same logic as backend/database.py
# Check for database in data/ directory first (Docker), then root
db_path = "sqlite:///./data/media_tracker.db" if os.path.exists("data/media_tracker.db") else "sqlite:///./media_tracker.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", db_path)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def normalize_name(name: str) -> str:
    """Normalize exercise name for comparison (lowercase, remove hyphens/spaces)"""
    return re.sub(r'[-\s]+', '', name.lower())


def format_proper_name(name: str) -> str:
    """Convert hyphenated name to proper format (Title Case with spaces)"""
    # Split by hyphens and capitalize each word
    words = name.split('-')
    return ' '.join(word.capitalize() for word in words)


def find_duplicates(db):
    """Find duplicate exercises based on normalized names"""
    exercises = db.query(Exercise).all()
    
    # Group by normalized name
    groups = defaultdict(list)
    for exercise in exercises:
        normalized = normalize_name(exercise.name)
        groups[normalized].append(exercise)
    
    # Find groups with duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    
    return duplicates


def choose_keep_exercise(exercises):
    """Choose which exercise to keep from a list of duplicates"""
    # Priority:
    # 1. Exercise with proper format (Title Case, no hyphens)
    # 2. Exercise with more records (exercise_records)
    # 3. Exercise with more workout associations
    # 4. Exercise with better metadata (primary_muscle, image_url, etc.)
    # 5. Exercise with earlier created_at (original)
    
    def score(exercise):
        score = 0
        
        # Prefer proper format (Title Case, no hyphens)
        if '-' not in exercise.name and exercise.name[0].isupper():
            score += 1000
        
        # Prefer exercises with metadata
        if exercise.primary_muscle:
            score += 100
        if exercise.image_url:
            score += 50
        if exercise.notes:
            score += 25
        
        return score
    
    # Sort by score (descending), then by created_at (ascending)
    sorted_exercises = sorted(exercises, key=lambda e: (-score(e), e.created_at))
    return sorted_exercises[0]


def merge_exercises(db, keep_exercise: Exercise, remove_exercise: Exercise):
    """Merge remove_exercise into keep_exercise"""
    print(f"  Merging '{remove_exercise.name}' -> '{keep_exercise.name}'")
    
    # Update exercise_records
    records_updated = db.query(ExerciseRecord).filter(
        ExerciseRecord.exercise_id == remove_exercise.id
    ).update({
        'exercise_id': keep_exercise.id,
        'exercise_name': keep_exercise.name
    })
    
    # Update workout_exercises
    workouts_updated = db.query(WorkoutExercise).filter(
        WorkoutExercise.exercise_id == remove_exercise.id
    ).update({
        'exercise_id': keep_exercise.id
    })
    
    # Merge metadata if keep_exercise is missing it
    updated = False
    if not keep_exercise.primary_muscle and remove_exercise.primary_muscle:
        keep_exercise.primary_muscle = remove_exercise.primary_muscle
        updated = True
    if not keep_exercise.secondary_muscles and remove_exercise.secondary_muscles:
        keep_exercise.secondary_muscles = remove_exercise.secondary_muscles
        updated = True
    if not keep_exercise.image_url and remove_exercise.image_url:
        keep_exercise.image_url = remove_exercise.image_url
        updated = True
    if not keep_exercise.notes and remove_exercise.notes:
        keep_exercise.notes = remove_exercise.notes
        updated = True
    
    if updated:
        db.add(keep_exercise)
    
    # Delete the duplicate exercise
    db.delete(remove_exercise)
    
    print(f"    - Updated {records_updated} exercise records")
    print(f"    - Updated {workouts_updated} workout associations")
    
    return records_updated, workouts_updated


def rename_hyphenated_exercises(db):
    """Rename hyphenated exercises to proper format if no duplicates exist"""
    exercises = db.query(Exercise).all()
    renamed = []
    
    for exercise in exercises:
        if '-' in exercise.name:
            # Check if there's already a proper format version
            proper_name = format_proper_name(exercise.name)
            existing = db.query(Exercise).filter(
                Exercise.name == proper_name
            ).first()
            
            if not existing:
                # No duplicate, safe to rename
                old_name = exercise.name
                exercise.name = proper_name
                db.add(exercise)
                
                # Update exercise_records with new name
                db.query(ExerciseRecord).filter(
                    ExerciseRecord.exercise_id == exercise.id
                ).update({
                    'exercise_name': proper_name
                })
                
                renamed.append((old_name, proper_name))
                print(f"  Renamed '{old_name}' -> '{proper_name}'")
    
    return renamed


def main():
    """Main function to clean up exercise duplicates"""
    print("=" * 70)
    print("CLEANING UP EXERCISE DUPLICATES")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Find and merge duplicates
        print("\nStep 1: Finding duplicate exercises...")
        duplicates = find_duplicates(db)
        
        if not duplicates:
            print("  No duplicates found!")
        else:
            print(f"  Found {len(duplicates)} groups of duplicates")
            
            total_records_updated = 0
            total_workouts_updated = 0
            total_removed = 0
            
            for normalized_name, exercises in duplicates.items():
                print(f"\n  Processing group: {normalized_name}")
                print(f"    Exercises: {[e.name for e in exercises]}")
                
                keep_exercise = choose_keep_exercise(exercises)
                print(f"    Keeping: '{keep_exercise.name}'")
                
                for exercise in exercises:
                    if exercise.id != keep_exercise.id:
                        records, workouts = merge_exercises(db, keep_exercise, exercise)
                        total_records_updated += records
                        total_workouts_updated += workouts
                        total_removed += 1
            
            db.commit()
            
            print("\n" + "=" * 70)
            print("DUPLICATE MERGE SUMMARY")
            print("=" * 70)
            print(f"  - Duplicate groups processed: {len(duplicates)}")
            print(f"  - Exercises removed: {total_removed}")
            print(f"  - Exercise records updated: {total_records_updated}")
            print(f"  - Workout associations updated: {total_workouts_updated}")
        
        # Step 2: Rename remaining hyphenated exercises
        print("\n" + "=" * 70)
        print("Step 2: Renaming hyphenated exercises to proper format...")
        print("=" * 70)
        
        renamed = rename_hyphenated_exercises(db)
        
        if renamed:
            db.commit()
            print(f"\n  Renamed {len(renamed)} exercises")
        else:
            print("  No hyphenated exercises to rename (or duplicates exist)")
        
        print("\n" + "=" * 70)
        print("CLEANUP COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
