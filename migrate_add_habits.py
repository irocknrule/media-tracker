"""
Migration script to add habit tracking tables.
Creates the habit_logs table for storing daily habit entries.
"""
import sqlite3
import os

def migrate_add_habits():
    db_path = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration: Adding habit tracking tables...")
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='habit_logs'
        """)
        
        if cursor.fetchone():
            print("Table 'habit_logs' already exists. Migration not needed.")
            return
        
        # Create the habit_logs table
        print("Creating 'habit_logs' table...")
        cursor.execute("""
            CREATE TABLE habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                habit_type VARCHAR NOT NULL,
                metric_name VARCHAR NOT NULL,
                value REAL NOT NULL,
                unit VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better query performance
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_habit_logs_date ON habit_logs(date)
        """)
        cursor.execute("""
            CREATE INDEX idx_habit_logs_habit_type ON habit_logs(habit_type)
        """)
        cursor.execute("""
            CREATE INDEX idx_habit_logs_date_habit_type ON habit_logs(date, habit_type)
        """)
        
        print("Migration completed successfully!")
        print("The 'habit_logs' table has been created with indexes.")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_habits()

