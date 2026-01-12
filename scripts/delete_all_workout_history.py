#!/usr/bin/env python3
"""
Script to delete all workout history from the database.
This removes all WorkoutRecord and ExerciseRecord entries.
"""

import sqlite3
import os
import sys


def delete_all_workout_history(skip_confirmation=False):
    """Delete all workout records and exercise records from the database"""
    
    # Get database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")
    
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Handle relative paths - go up one level from scripts/ to project root
    if db_path.startswith("./"):
        script_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(script_dir)
        db_path = os.path.join(project_root, db_path[2:])
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='workout_records'
        """)
        
        if not cursor.fetchone():
            print("Table 'workout_records' does not exist.")
            conn.close()
            return
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM exercise_records")
        exercise_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM workout_records")
        workout_count = cursor.fetchone()[0]
        
        print(f"\nFound {workout_count} workout record(s) and {exercise_count} exercise record(s)")
        
        if workout_count == 0 and exercise_count == 0:
            print("No workout history to delete.")
            conn.close()
            return
        
        # Confirm deletion
        if not skip_confirmation:
            response = input(f"\nAre you sure you want to delete ALL workout history? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Deletion cancelled.")
                conn.close()
                return
        
        # Delete exercise records first (though cascade should handle this)
        print("\nDeleting exercise records...")
        cursor.execute("DELETE FROM exercise_records")
        exercise_deleted = cursor.rowcount
        
        # Delete workout records
        print("Deleting workout records...")
        cursor.execute("DELETE FROM workout_records")
        workout_deleted = cursor.rowcount
        
        conn.commit()
        print(f"\n✅ Successfully deleted {workout_deleted} workout record(s) and {exercise_deleted} exercise record(s)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error deleting workout history: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        sys.exit(1)


if __name__ == "__main__":
    # Allow skipping confirmation with --yes flag
    skip_confirmation = "--yes" in sys.argv or "-y" in sys.argv
    delete_all_workout_history(skip_confirmation=skip_confirmation)
