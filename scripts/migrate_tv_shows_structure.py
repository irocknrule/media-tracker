"""
Migration script to convert old TV show structure to new structure
with separate show and season tables.
"""
import sqlite3
from datetime import datetime

def migrate_tv_shows():
    conn = sqlite3.connect('media_tracker.db')
    cursor = conn.cursor()
    
    print("Starting TV show structure migration...")
    
    try:
        # Create new tables
        print("Creating new tables...")
        
        # Create new tv_shows table (for show-level data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tv_shows_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER,
                genres TEXT,
                overall_rating REAL,
                show_thumbnail_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on title
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tv_shows_new_title ON tv_shows_new(title)
        """)
        
        # Create tv_show_seasons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tv_show_seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                show_id INTEGER NOT NULL,
                season_number INTEGER NOT NULL,
                watched_date DATE NOT NULL,
                rating REAL,
                notes TEXT,
                season_thumbnail_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (show_id) REFERENCES tv_shows_new(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tv_show_seasons_show_id ON tv_show_seasons(show_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tv_show_seasons_watched_date ON tv_show_seasons(watched_date)
        """)
        
        print("New tables created successfully.")
        
        # Migrate data from old structure
        print("Migrating data from old structure...")
        
        # Get all old TV show entries
        cursor.execute("SELECT * FROM tv_shows")
        old_entries = cursor.fetchall()
        
        print(f"Found {len(old_entries)} old TV show entries to migrate.")
        
        # Group by title to create shows
        shows_dict = {}
        
        for entry in old_entries:
            old_id, title, season, episode, watched_date, rating, notes, created_at, thumbnail_url = entry
            
            if title not in shows_dict:
                # Create new show entry
                cursor.execute("""
                    INSERT INTO tv_shows_new (title, show_thumbnail_url, created_at)
                    VALUES (?, ?, ?)
                """, (title, thumbnail_url, created_at))
                
                show_id = cursor.lastrowid
                shows_dict[title] = show_id
                print(f"  Created show: {title} (ID: {show_id})")
            else:
                show_id = shows_dict[title]
            
            # Create season entry
            cursor.execute("""
                INSERT INTO tv_show_seasons (show_id, season_number, watched_date, rating, notes, season_thumbnail_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (show_id, season or 1, watched_date, rating, notes, thumbnail_url, created_at))
            
            print(f"    Added Season {season or 1} to {title}")
        
        print("Data migration completed.")
        
        # Rename tables
        print("Renaming tables...")
        cursor.execute("ALTER TABLE tv_shows RENAME TO tv_shows_old")
        cursor.execute("ALTER TABLE tv_shows_new RENAME TO tv_shows")
        
        print("Tables renamed successfully.")
        print("\nMigration completed successfully!")
        print("The old tv_shows table has been renamed to tv_shows_old for backup.")
        print("You can drop it manually after verifying the migration.")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_tv_shows()

