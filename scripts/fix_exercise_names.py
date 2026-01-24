#!/usr/bin/env python3
"""
Script to fix exercise name capitalization and merge remaining duplicates.
"""

import sqlite3
import re
import os
from collections import defaultdict


def normalize_name(name: str) -> str:
    """Normalize exercise name for comparison (lowercase, remove hyphens/spaces)"""
    return re.sub(r'[-\s]+', '', name.lower())


def fix_capitalization(name: str) -> str:
    """Fix capitalization to proper Title Case"""
    # Split by spaces
    words = name.split()
    fixed_words = []
    
    for word in words:
        if word:
            # Handle special cases like "RDL" should stay uppercase
            if word.upper() in ['RDL', 'DB', 'BB']:
                fixed_words.append(word.upper())
            else:
                # Capitalize first letter, lowercase the rest
                fixed_words.append(word.capitalize())
    
    return ' '.join(fixed_words)


def find_database_path():
    """Find the database file"""
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


def main():
    """Main function to fix exercise names"""
    print("=" * 70)
    print("FIXING EXERCISE NAMES")
    print("=" * 70)
    
    db_path = find_database_path()
    print(f"\nUsing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Step 1: Find and fix capitalization issues
        print("\nStep 1: Fixing capitalization...")
        cursor.execute("SELECT id, name FROM exercises")
        exercises = cursor.fetchall()
        
        fixed = []
        for exercise_id, name in exercises:
            fixed_name = fix_capitalization(name)
            if fixed_name != name:
                cursor.execute("UPDATE exercises SET name = ? WHERE id = ?", (fixed_name, exercise_id))
                cursor.execute("UPDATE exercise_records SET exercise_name = ? WHERE exercise_id = ?", 
                             (fixed_name, exercise_id))
                fixed.append((name, fixed_name))
                print(f"  Fixed: '{name}' -> '{fixed_name}'")
        
        conn.commit()
        print(f"\n  Fixed {len(fixed)} exercise names")
        
        # Step 2: Find and merge duplicates
        print("\nStep 2: Finding and merging duplicates...")
        cursor.execute("SELECT id, name, primary_muscle, image_url, notes, created_at FROM exercises")
        exercises = cursor.fetchall()
        
        # Group by normalized name
        groups = defaultdict(list)
        for exercise in exercises:
            normalized = normalize_name(exercise[1])
            groups[normalized].append(exercise)
        
        duplicates = {k: v for k, v in groups.items() if len(v) > 1}
        
        if not duplicates:
            print("  No duplicates found!")
        else:
            print(f"  Found {len(duplicates)} groups of duplicates")
            
            total_removed = 0
            total_records_updated = 0
            total_workouts_updated = 0
            
            for normalized_name, exercise_list in duplicates.items():
                print(f"\n  Processing: {[e[1] for e in exercise_list]}")
                
                # Choose which to keep - prefer proper format, then most metadata
                def score(ex):
                    s = 0
                    name = ex[1]
                    if '-' not in name and name[0].isupper():
                        s += 1000
                    if ex[2]:  # primary_muscle
                        s += 100
                    if ex[3]:  # image_url
                        s += 50
                    if ex[4]:  # notes
                        s += 25
                    return s
                
                sorted_exercises = sorted(exercise_list, key=lambda e: (-score(e), e[5] or ''))
                keep_exercise = sorted_exercises[0]
                keep_id = keep_exercise[0]
                keep_name = keep_exercise[1]
                
                print(f"    Keeping: '{keep_name}' (id: {keep_id})")
                
                for exercise in sorted_exercises[1:]:
                    remove_id = exercise[0]
                    remove_name = exercise[1]
                    
                    print(f"    Removing: '{remove_name}' (id: {remove_id})")
                    
                    # Count records
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
                    
                    # Merge metadata
                    if not keep_exercise[2] and exercise[2]:  # primary_muscle
                        cursor.execute("UPDATE exercises SET primary_muscle = ? WHERE id = ?", 
                                     (exercise[2], keep_id))
                    if not keep_exercise[3] and exercise[3]:  # image_url
                        cursor.execute("UPDATE exercises SET image_url = ? WHERE id = ?", 
                                     (exercise[3], keep_id))
                    if not keep_exercise[4] and exercise[4]:  # notes
                        cursor.execute("UPDATE exercises SET notes = ? WHERE id = ?", 
                                     (exercise[4], keep_id))
                    
                    # Delete duplicate
                    cursor.execute("DELETE FROM exercises WHERE id = ?", (remove_id,))
                    
                    total_removed += 1
                    total_records_updated += records_count
                    total_workouts_updated += workouts_count
                    
                    print(f"      - Updated {records_count} records, {workouts_count} workouts")
            
            conn.commit()
            
            print("\n" + "=" * 70)
            print("MERGE SUMMARY")
            print("=" * 70)
            print(f"  - Duplicate groups: {len(duplicates)}")
            print(f"  - Exercises removed: {total_removed}")
            print(f"  - Exercise records updated: {total_records_updated}")
            print(f"  - Workout associations updated: {total_workouts_updated}")
        
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
