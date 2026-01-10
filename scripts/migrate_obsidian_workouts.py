#!/usr/bin/env python3
"""
Migration script to import workout data from Obsidian markdown files
into the media tracker database.

This script parses:
- Exercises from obsidian/_database/exercises/
- Workouts from obsidian/_database/workouts/
- Workout Records from obsidian/_database/workout-records/
- Exercise Records from obsidian/_database/exercise-records/
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
import yaml

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import (
    Base,
    Exercise,
    Workout,
    WorkoutExercise,
    WorkoutRecord,
    ExerciseRecord
)


# Database setup
DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown file"""
    frontmatter = {}
    
    if content.startswith('---'):
        try:
            # Extract frontmatter between --- markers
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                frontmatter = yaml.safe_load(frontmatter_text) or {}
        except Exception as e:
            print(f"Warning: Failed to parse frontmatter: {e}")
    
    return frontmatter


def extract_inline_field(content: str, field_name: str) -> str:
    """Extract inline field value (e.g., 'exercises::' or 'Sets::')"""
    pattern = rf'{field_name}::\s*(.+?)(?:\n|$)'
    match = re.search(pattern, content, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_exercise_links(text: str) -> list:
    """Parse exercise links from markdown (e.g., [[exercise-name]])"""
    if not text:
        return []
    
    # Match [[exercise-name]] or [[path/to/exercise-name]]
    pattern = r'\[\[(?:.*?/)?([^\]|]+?)(?:\|[^\]]+)?\]\]'
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches]


def parse_date_from_filename(filename: str) -> datetime:
    """Parse date from workout record filename (e.g., 'workout-2024-07-13-09.01.md')"""
    # Pattern: name-YYYY-MM-DD-HH.MM.md
    pattern = r'(\d{4})-(\d{2})-(\d{2})-(\d{2})\.(\d{2})'
    match = re.search(pattern, filename)
    
    if match:
        year, month, day, hour, minute = match.groups()
        return datetime(int(year), int(month), int(day), int(hour), int(minute))
    
    return None


def import_exercises(db, obsidian_path: Path):
    """Import exercises from Obsidian markdown files"""
    exercises_path = obsidian_path / "_database" / "exercises"
    
    if not exercises_path.exists():
        print(f"Exercises path not found: {exercises_path}")
        return {}
    
    print(f"\nImporting exercises from {exercises_path}...")
    
    exercise_map = {}  # Map exercise name to database ID
    created_count = 0
    
    for exercise_file in exercises_path.glob("*.md"):
        try:
            content = exercise_file.read_text(encoding='utf-8')
            frontmatter = parse_frontmatter(content)
            
            # Get exercise name (use title from frontmatter or filename)
            name = frontmatter.get('name') or frontmatter.get('title') or exercise_file.stem
            
            # Get muscle groups
            primary_muscle = frontmatter.get('primary-muscle', '')
            secondary_muscles = frontmatter.get('secondary-muscles', [])
            if isinstance(secondary_muscles, list):
                secondary_muscles = ', '.join(secondary_muscles)
            
            # Extract notes from content (everything after frontmatter and title)
            notes_match = re.search(r'## Notes\s*\n(.+?)(?:\n##|$)', content, re.DOTALL)
            notes = notes_match.group(1).strip() if notes_match else None
            
            # Check if exercise already exists
            existing = db.query(Exercise).filter(Exercise.name == name).first()
            
            if existing:
                exercise_map[name] = existing.id
                print(f"  ✓ Exercise already exists: {name}")
            else:
                # Create new exercise
                exercise = Exercise(
                    name=name,
                    primary_muscle=primary_muscle if primary_muscle else None,
                    secondary_muscles=secondary_muscles if secondary_muscles else None,
                    notes=notes
                )
                db.add(exercise)
                db.flush()
                
                exercise_map[name] = exercise.id
                created_count += 1
                print(f"  ✓ Imported: {name} (muscle: {primary_muscle})")
        
        except Exception as e:
            print(f"  ✗ Error importing {exercise_file.name}: {e}")
    
    db.commit()
    print(f"\n✓ Imported {created_count} new exercises (total: {len(exercise_map)})")
    
    return exercise_map


def import_workouts(db, obsidian_path: Path, exercise_map: dict):
    """Import workout templates from Obsidian markdown files"""
    workouts_path = obsidian_path / "_database" / "workouts"
    
    if not workouts_path.exists():
        print(f"Workouts path not found: {workouts_path}")
        return {}
    
    print(f"\nImporting workouts from {workouts_path}...")
    
    workout_map = {}  # Map workout name to database ID
    created_count = 0
    
    for workout_file in workouts_path.glob("*.md"):
        try:
            content = workout_file.read_text(encoding='utf-8')
            frontmatter = parse_frontmatter(content)
            
            # Get workout name
            name = frontmatter.get('name') or workout_file.stem
            
            # Get exercises list
            exercises_text = extract_inline_field(content, 'exercises')
            exercise_names = parse_exercise_links(exercises_text) if exercises_text else []
            
            # Check if workout already exists
            existing = db.query(Workout).filter(Workout.name == name).first()
            
            if existing:
                workout_map[name] = existing.id
                print(f"  ✓ Workout already exists: {name}")
            else:
                # Create new workout
                workout = Workout(
                    name=name,
                    description=None
                )
                db.add(workout)
                db.flush()
                
                # Add exercises to workout
                for idx, exercise_name in enumerate(exercise_names):
                    if exercise_name in exercise_map:
                        workout_exercise = WorkoutExercise(
                            workout_id=workout.id,
                            exercise_id=exercise_map[exercise_name],
                            order_index=idx
                        )
                        db.add(workout_exercise)
                    else:
                        print(f"    ⚠ Warning: Exercise '{exercise_name}' not found in exercise map")
                
                workout_map[name] = workout.id
                created_count += 1
                print(f"  ✓ Imported: {name} ({len(exercise_names)} exercises)")
        
        except Exception as e:
            print(f"  ✗ Error importing {workout_file.name}: {e}")
    
    db.commit()
    print(f"\n✓ Imported {created_count} new workouts (total: {len(workout_map)})")
    
    return workout_map


def import_workout_records(db, obsidian_path: Path, workout_map: dict, exercise_map: dict):
    """Import workout records and exercise records from Obsidian"""
    workout_records_path = obsidian_path / "_database" / "workout-records"
    exercise_records_path = obsidian_path / "_database" / "exercise-records"
    
    if not workout_records_path.exists():
        print(f"Workout records path not found: {workout_records_path}")
        return
    
    print(f"\nImporting workout records from {workout_records_path}...")
    
    workout_record_map = {}  # Map filename to database ID
    created_workouts = 0
    created_exercises = 0
    
    # First, import all workout records
    for record_file in sorted(workout_records_path.glob("*.md")):
        try:
            content = record_file.read_text(encoding='utf-8')
            frontmatter = parse_frontmatter(content)
            
            # Parse workout date from filename
            workout_date = parse_date_from_filename(record_file.name)
            if not workout_date:
                print(f"  ⚠ Warning: Could not parse date from {record_file.name}")
                continue
            
            # Get workout name
            workout_text = extract_inline_field(content, 'workout')
            workout_names = parse_exercise_links(workout_text) if workout_text else []
            workout_name = workout_names[0] if workout_names else record_file.stem.rsplit('-', 4)[0]
            
            # Get workout ID if it exists
            workout_id = workout_map.get(workout_name)
            
            # Check if this workout record already exists
            existing = db.query(WorkoutRecord).filter(
                WorkoutRecord.workout_date == workout_date,
                WorkoutRecord.workout_name == workout_name
            ).first()
            
            if existing:
                workout_record_map[record_file.stem] = existing.id
                print(f"  ✓ Workout record already exists: {record_file.name}")
            else:
                # Create workout record
                workout_record = WorkoutRecord(
                    workout_id=workout_id,
                    workout_name=workout_name,
                    workout_date=workout_date,
                    notes=None
                )
                db.add(workout_record)
                db.flush()
                
                workout_record_map[record_file.stem] = workout_record.id
                created_workouts += 1
                print(f"  ✓ Imported: {record_file.name}")
        
        except Exception as e:
            print(f"  ✗ Error importing {record_file.name}: {e}")
    
    db.commit()
    print(f"\n✓ Imported {created_workouts} new workout records")
    
    # Now import exercise records
    if not exercise_records_path.exists():
        print(f"Exercise records path not found: {exercise_records_path}")
        return
    
    print(f"\nImporting exercise records from {exercise_records_path}...")
    
    for record_file in sorted(exercise_records_path.glob("*.md")):
        try:
            content = record_file.read_text(encoding='utf-8')
            
            # Get exercise name (first part of filename before date)
            exercise_name = record_file.stem.rsplit('-', 4)[0]
            
            # Get exercise ID
            exercise_id = exercise_map.get(exercise_name)
            if not exercise_id:
                print(f"  ⚠ Warning: Exercise '{exercise_name}' not found for {record_file.name}")
                continue
            
            # Get workout record reference
            workout_ref = extract_inline_field(content, 'Workout')
            workout_record_names = parse_exercise_links(workout_ref) if workout_ref else []
            
            if not workout_record_names:
                print(f"  ⚠ Warning: No workout reference found for {record_file.name}")
                continue
            
            workout_record_name = workout_record_names[0]
            workout_record_id = workout_record_map.get(workout_record_name)
            
            if not workout_record_id:
                print(f"  ⚠ Warning: Workout record '{workout_record_name}' not found")
                continue
            
            # Extract performance data
            sets = extract_inline_field(content, 'Sets')
            reps = extract_inline_field(content, 'Reps')
            weight = extract_inline_field(content, 'Weight')
            time = extract_inline_field(content, 'Time')
            distance = extract_inline_field(content, 'Distance')
            
            # Check if already exists
            existing = db.query(ExerciseRecord).filter(
                ExerciseRecord.workout_record_id == workout_record_id,
                ExerciseRecord.exercise_id == exercise_id
            ).first()
            
            if existing:
                print(f"  ✓ Exercise record already exists: {record_file.name}")
                continue
            
            # Create exercise record
            exercise_record = ExerciseRecord(
                workout_record_id=workout_record_id,
                exercise_id=exercise_id,
                exercise_name=exercise_name,
                sets=int(sets) if sets and sets != '-' else None,
                reps=int(reps) if reps and reps != '-' else None,
                weight=float(weight) if weight and weight != '-' else None,
                weight_unit='lbs',
                time_seconds=int(time) if time and time != '-' else None,
                distance=float(distance) if distance and distance != '-' else None
            )
            db.add(exercise_record)
            created_exercises += 1
        
        except Exception as e:
            print(f"  ✗ Error importing {record_file.name}: {e}")
    
    db.commit()
    print(f"\n✓ Imported {created_exercises} new exercise records")


def main():
    """Main migration function"""
    print("=" * 70)
    print("OBSIDIAN WORKOUT DATA MIGRATION")
    print("=" * 70)
    
    # Get obsidian path
    script_dir = Path(__file__).parent.parent
    obsidian_path = script_dir / "obsidian"
    
    if not obsidian_path.exists():
        print(f"\n✗ Error: Obsidian folder not found at {obsidian_path}")
        print("Please ensure the obsidian folder is in the project root.")
        return
    
    print(f"\nObsidian path: {obsidian_path}")
    print(f"Database: {DATABASE_URL}")
    
    # Create tables if they don't exist
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Import in order: exercises, workouts, then records
        exercise_map = import_exercises(db, obsidian_path)
        workout_map = import_workouts(db, obsidian_path, exercise_map)
        import_workout_records(db, obsidian_path, workout_map, exercise_map)
        
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETE!")
        print("=" * 70)
        
        # Print summary
        total_exercises = db.query(Exercise).count()
        total_workouts = db.query(Workout).count()
        total_workout_records = db.query(WorkoutRecord).count()
        total_exercise_records = db.query(ExerciseRecord).count()
        
        print(f"\nDatabase Summary:")
        print(f"  - Exercises: {total_exercises}")
        print(f"  - Workout Templates: {total_workouts}")
        print(f"  - Workout Records: {total_workout_records}")
        print(f"  - Exercise Records: {total_exercise_records}")
        print("\n✓ All data successfully migrated!")
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

