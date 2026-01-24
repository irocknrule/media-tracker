#!/usr/bin/env python3
"""
Script to merge exercises that are duplicates but differ by word order.
"""

import sqlite3
import re
import os
from collections import defaultdict


def normalize_name(name: str) -> str:
    """Normalize exercise name for comparison - sort words alphabetically"""
    # Remove hyphens, convert to lowercase, split into words, sort, and rejoin
    words = re.sub(r'[-\s]+', ' ', name.lower()).split()
    return ''.join(sorted(words))


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
    """Main function to merge word-order duplicates"""
    print("=" * 70)
    print("MERGING WORD-ORDER DUPLICATES")
    print("=" * 70)
    
    db_path = find_database_path()
    print(f"\nUsing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all exercises
        cursor.execute("SELECT id, name, primary_muscle, image_url, notes, created_at FROM exercises")
        exercises = cursor.fetchall()
        
        # Group by normalized name (sorted words)
        groups = defaultdict(list)
        for exercise in exercises:
            normalized = normalize_name(exercise[1])
            groups[normalized].append(exercise)
        
        # Find groups with duplicates
        duplicates = {k: v for k, v in groups.items() if len(v) > 1}
        
        if not duplicates:
            print("\nNo word-order duplicates found!")
        else:
            print(f"\nFound {len(duplicates)} groups of word-order duplicates")
            
            total_removed = 0
            total_records_updated = 0
            total_workouts_updated = 0
            
            for normalized_name, exercise_list in duplicates.items():
                print(f"\n  Processing: {[e[1] for e in exercise_list]}")
                
                # Choose which to keep - prefer proper format, then most records/workouts
                def score(ex):
                    s = 0
                    name = ex[1]
                    # Prefer names that start with the main equipment/type
                    if name.startswith(('Barbell', 'Dumbbell', 'Cable', 'Machine')):
                        s += 500
                    if '-' not in name and name[0].isupper():
                        s += 1000
                    if ex[2]:  # primary_muscle
                        s += 100
                    if ex[3]:  # image_url
                        s += 50
                    if ex[4]:  # notes
                        s += 25
                    return s
                
                # Get record/workout counts for each
                scored_exercises = []
                for ex in exercise_list:
                    cursor.execute("SELECT COUNT(*) FROM exercise_records WHERE exercise_id = ?", (ex[0],))
                    records = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM workout_exercises WHERE exercise_id = ?", (ex[0],))
                    workouts = cursor.fetchone()[0]
                    scored_exercises.append((ex, records, workouts, score(ex)))
                
                # Sort by score, then by records, then by workouts
                sorted_exercises = sorted(scored_exercises, 
                                        key=lambda x: (-x[3], -x[1], -x[2]))
                keep_exercise, keep_records, keep_workouts, keep_score = sorted_exercises[0]
                keep_id = keep_exercise[0]
                keep_name = keep_exercise[1]
                
                print(f"    Keeping: '{keep_name}' (id: {keep_id}, {keep_records} records, {keep_workouts} workouts)")
                
                for ex, records, workouts, score_val in sorted_exercises[1:]:
                    remove_id = ex[0]
                    remove_name = ex[1]
                    
                    print(f"    Removing: '{remove_name}' (id: {remove_id}, {records} records, {workouts} workouts)")
                    
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
                    if not keep_exercise[2] and ex[2]:  # primary_muscle
                        cursor.execute("UPDATE exercises SET primary_muscle = ? WHERE id = ?", 
                                     (ex[2], keep_id))
                    if not keep_exercise[3] and ex[3]:  # image_url
                        cursor.execute("UPDATE exercises SET image_url = ? WHERE id = ?", 
                                     (ex[3], keep_id))
                    if not keep_exercise[4] and ex[4]:  # notes
                        cursor.execute("UPDATE exercises SET notes = ? WHERE id = ?", 
                                     (ex[4], keep_id))
                    
                    # Delete duplicate
                    cursor.execute("DELETE FROM exercises WHERE id = ?", (remove_id,))
                    
                    total_removed += 1
                    total_records_updated += records
                    total_workouts_updated += workouts
                    
                    print(f"      - Updated {records} records, {workouts} workouts")
            
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
