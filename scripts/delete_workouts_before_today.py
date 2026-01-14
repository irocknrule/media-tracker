#!/usr/bin/env python3
"""
Script to delete all workout records before today from the database.
This removes WorkoutRecord and ExerciseRecord entries dated before today.
"""

import sqlite3
import os
import sys
from datetime import datetime, date


def delete_workouts_before_today(skip_confirmation=False):
    """Delete all workout records before today"""
    
    # Get database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")
    
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Handle relative paths - go up one level from scripts/ to project root
    if db_path.startswith("./"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        db_path = os.path.join(project_root, db_path[2:])
    
    # Check if Docker database exists (in data/ directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    docker_db_path = os.path.join(project_root, "data", "media_tracker.db")
    
    # Use Docker database if it exists, otherwise use the specified path
    if os.path.exists(docker_db_path):
        db_path = docker_db_path
        print(f"Found Docker database, using: {db_path}")
    elif not os.path.exists(db_path):
        # Try the root location as fallback
        root_db_path = os.path.join(project_root, "media_tracker.db")
        if os.path.exists(root_db_path):
            db_path = root_db_path
            print(f"Found database at root, using: {db_path}")
        else:
            print(f"Warning: Database not found at {db_path} or {docker_db_path}")
    
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
        
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).isoformat()
        
        print(f"\nDeleting workout records before {today.strftime('%Y-%m-%d')}...")
        
        # Count records to be deleted
        cursor.execute("""
            SELECT COUNT(*) FROM workout_records 
            WHERE workout_date < ?
        """, (today_start,))
        workout_count = cursor.fetchone()[0]
        
        if workout_count == 0:
            print("No workout records found before today.")
            conn.close()
            return
        
        # Count exercise records to be deleted (via cascade)
        cursor.execute("""
            SELECT COUNT(*) FROM exercise_records er
            INNER JOIN workout_records wr ON er.workout_record_id = wr.id
            WHERE wr.workout_date < ?
        """, (today_start,))
        exercise_count = cursor.fetchone()[0]
        
        print(f"\nFound {workout_count} workout record(s) and {exercise_count} exercise record(s) before today")
        
        # Confirm deletion
        if not skip_confirmation:
            response = input(f"\nAre you sure you want to delete {workout_count} workout record(s) before today? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Deletion cancelled.")
                conn.close()
                return
        
        # Delete workout records (exercise records will be deleted via cascade)
        print("\nDeleting workout records...")
        cursor.execute("""
            DELETE FROM workout_records 
            WHERE workout_date < ?
        """, (today_start,))
        workout_deleted = cursor.rowcount
        
        conn.commit()
        print(f"\n✅ Successfully deleted {workout_deleted} workout record(s) before today")
        print(f"   (Associated exercise records were automatically deleted via cascade)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error deleting workout records: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        sys.exit(1)


if __name__ == "__main__":
    # Allow skipping confirmation with --yes flag
    skip_confirmation = "--yes" in sys.argv or "-y" in sys.argv
    delete_workouts_before_today(skip_confirmation=skip_confirmation)
