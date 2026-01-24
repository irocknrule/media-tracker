#!/usr/bin/env python3
"""
Script to find and remove duplicate exercises in the database.
Merges hyphenated duplicates (e.g., "dumbbell-bench-press") with proper format (e.g., "Dumbbell Bench Press").
Uses only Python standard library (sqlite3).
"""

import sqlite3
import re
import os
from pathlib import Path
from collections import defaultdict


def normalize_name(name: str) -> str:
    """Normalize exercise name for comparison (lowercase, remove hyphens/spaces)"""
    return re.sub(r'[-\s]+', '', name.lower())


def format_proper_name(name: str) -> str:
    """Convert hyphenated name to proper format (Title Case with spaces)"""
    # If name already has spaces mixed with hyphens, replace hyphens with spaces first
    # Then split by spaces and capitalize each word
    name = name.replace('-', ' ')
    words = name.split()
    
    # Capitalize first letter of each word, keep rest lowercase
    formatted_words = []
    for word in words:
        if word:
            # Handle special cases like "RDL" should stay uppercase
            if word.upper() in ['RDL', 'DB', 'BB']:
                formatted_words.append(word.upper())
            else:
                formatted_words.append(word.capitalize())
    return ' '.join(formatted_words)


def find_database_path():
    """Find the database file"""
    # Check common locations
    paths = [
        "data/media_tracker.db",
        "media_tracker.db",
        os.path.join(os.path.dirname(__file__), "..", "data", "media_tracker.db"),
        os.path.join(os.path.dirname(__file__), "..", "media_tracker.db"),
    ]
    
    for path in paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            return full_path
    
    raise FileNotFoundError("Could not find media_tracker.db database file")


def find_duplicates(cursor):
    """Find duplicate exercises based on normalized names"""
    cursor.execute("SELECT id, name, primary_muscle, image_url, notes, created_at FROM exercises")
    exercises = cursor.fetchall()
    
    # Group by normalized name
    groups = defaultdict(list)
    for exercise in exercises:
        normalized = normalize_name(exercise[1])  # exercise[1] is name
        groups[normalized].append(exercise)
    
    # Find groups with duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    
    return duplicates


def choose_keep_exercise(exercises):
    """Choose which exercise to keep from a list of duplicates"""
    # Priority:
    # 1. Exercise with proper format (Title Case, no hyphens)
    # 2. Exercise with more records (exercise_records)
    # 3. Exercise with better metadata (primary_muscle, image_url, etc.)
    # 4. Exercise with earlier created_at (original)
    
    def score(exercise):
        # exercise is a tuple: (id, name, primary_muscle, image_url, notes, created_at)
        name = exercise[1]
        score = 0
        
        # Prefer proper format (Title Case, no hyphens)
        if '-' not in name and name[0].isupper():
            score += 1000
        
        # Prefer exercises with metadata
        if exercise[2]:  # primary_muscle
            score += 100
        if exercise[3]:  # image_url
            score += 50
        if exercise[4]:  # notes
            score += 25
        
        return score
    
    # Sort by score (descending), then by created_at (ascending)
    sorted_exercises = sorted(exercises, key=lambda e: (-score(e), e[5] or ''))
    return sorted_exercises[0]


def merge_exercises(conn, keep_exercise, remove_exercise):
    """Merge remove_exercise into keep_exercise"""
    keep_id = keep_exercise[0]
    keep_name = keep_exercise[1]
    remove_id = remove_exercise[0]
    remove_name = remove_exercise[1]
    
    print(f"  Merging '{remove_name}' -> '{keep_name}'")
    
    cursor = conn.cursor()
    
    # Count records to update
    cursor.execute("SELECT COUNT(*) FROM exercise_records WHERE exercise_id = ?", (remove_id,))
    records_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM workout_exercises WHERE exercise_id = ?", (remove_id,))
    workouts_count = cursor.fetchone()[0]
    
    # Update exercise_records
    cursor.execute("""
        UPDATE exercise_records 
        SET exercise_id = ?, exercise_name = ?
        WHERE exercise_id = ?
    """, (keep_id, keep_name, remove_id))
    
    # Update workout_exercises
    cursor.execute("""
        UPDATE workout_exercises 
        SET exercise_id = ?
        WHERE exercise_id = ?
    """, (keep_id, remove_id))
    
    # Merge metadata if keep_exercise is missing it
    # exercise tuple: (id, name, primary_muscle, image_url, notes, created_at)
    updates = []
    if not keep_exercise[2] and remove_exercise[2]:  # primary_muscle
        updates.append(("primary_muscle", remove_exercise[2]))
    if not keep_exercise[3] and remove_exercise[3]:  # image_url
        updates.append(("image_url", remove_exercise[3]))
    if not keep_exercise[4] and remove_exercise[4]:  # notes
        updates.append(("notes", remove_exercise[4]))
    if not keep_exercise[2] and remove_exercise[2]:  # secondary_muscles (if exists)
        # Note: secondary_muscles not in our query, skip for now
        pass
    
    for field, value in updates:
        cursor.execute(f"UPDATE exercises SET {field} = ? WHERE id = ?", (value, keep_id))
    
    # Delete the duplicate exercise
    cursor.execute("DELETE FROM exercises WHERE id = ?", (remove_id,))
    
    conn.commit()
    
    print(f"    - Updated {records_count} exercise records")
    print(f"    - Updated {workouts_count} workout associations")
    
    return records_count, workouts_count


def rename_hyphenated_exercises(conn):
    """Rename hyphenated exercises to proper format if no duplicates exist"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM exercises WHERE name LIKE '%-%'")
    exercises = cursor.fetchall()
    
    renamed = []
    
    for exercise_id, name in exercises:
        proper_name = format_proper_name(name)
        
        # Normalize both names for comparison
        normalized_old = normalize_name(name)
        normalized_new = normalize_name(proper_name)
        
        # Check if there's already a proper format version (by normalized name)
        cursor.execute("""
            SELECT id, name FROM exercises 
            WHERE id != ? 
            AND LOWER(REPLACE(REPLACE(name, '-', ''), ' ', '')) = ?
        """, (exercise_id, normalized_new))
        existing = cursor.fetchone()
        
        if existing:
            # Duplicate found - merge instead of rename
            print(f"  Found duplicate: '{name}' matches '{existing[1]}' - will merge in step 1")
            continue
        
        if proper_name != name:
            # No duplicate, safe to rename
            cursor.execute("UPDATE exercises SET name = ? WHERE id = ?", (proper_name, exercise_id))
            
            # Update exercise_records with new name
            cursor.execute("""
                UPDATE exercise_records 
                SET exercise_name = ?
                WHERE exercise_id = ?
            """, (proper_name, exercise_id))
            
            renamed.append((name, proper_name))
            print(f"  Renamed '{name}' -> '{proper_name}'")
    
    conn.commit()
    return renamed


def main():
    """Main function to clean up exercise duplicates"""
    print("=" * 70)
    print("CLEANING UP EXERCISE DUPLICATES")
    print("=" * 70)
    
    db_path = find_database_path()
    print(f"\nUsing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    try:
        # Step 1: Find and merge duplicates
        print("\nStep 1: Finding duplicate exercises...")
        cursor = conn.cursor()
        duplicates = find_duplicates(cursor)
        
        if not duplicates:
            print("  No duplicates found!")
        else:
            print(f"  Found {len(duplicates)} groups of duplicates")
            
            total_records_updated = 0
            total_workouts_updated = 0
            total_removed = 0
            
            for normalized_name, exercises in duplicates.items():
                print(f"\n  Processing group: {normalized_name}")
                print(f"    Exercises: {[e[1] for e in exercises]}")
                
                keep_exercise = choose_keep_exercise(exercises)
                print(f"    Keeping: '{keep_exercise[1]}'")
                
                for exercise in exercises:
                    if exercise[0] != keep_exercise[0]:  # Different ID
                        records, workouts = merge_exercises(conn, keep_exercise, exercise)
                        total_records_updated += records
                        total_workouts_updated += workouts
                        total_removed += 1
            
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
        
        renamed = rename_hyphenated_exercises(conn)
        
        if renamed:
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
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
