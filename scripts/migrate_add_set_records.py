#!/usr/bin/env python3
"""
Migration script to add set_records table to the database.
This script adds support for tracking individual sets with their own rep counts.
"""

import sqlite3
import os


def migrate_add_set_records():
    """Add set_records table to the database"""
    
    # Get database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")
    
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Handle relative paths - resolve relative to current working directory
    # In Docker, working directory is /app, so ./data/media_tracker.db -> /app/data/media_tracker.db
    # For local runs, this will also work if run from project root
    if db_path.startswith("./"):
        db_path = os.path.join(os.getcwd(), db_path[2:])
    elif not os.path.isabs(db_path):
        # If it's a relative path without ./, resolve from current working directory
        db_path = os.path.join(os.getcwd(), db_path)
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='set_records'
        """)
        
        if cursor.fetchone():
            print("Table 'set_records' already exists. Migration not needed.")
            conn.close()
            return
        
        print("Creating set_records table...")
        
        # Create the set_records table
        cursor.execute("""
            CREATE TABLE set_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_record_id INTEGER NOT NULL,
                set_number INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                weight REAL NOT NULL,
                weight_unit VARCHAR DEFAULT 'lbs',
                notes VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exercise_record_id) REFERENCES exercise_records(id) ON DELETE CASCADE
            )
        """)
        
        print("Creating indexes...")
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX idx_set_records_exercise_record_id ON set_records(exercise_record_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_set_records_exercise_set ON set_records(exercise_record_id, set_number)
        """)
        
        print("Successfully created set_records table with indexes")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during set_records migration: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


if __name__ == "__main__":
    migrate_add_set_records()
