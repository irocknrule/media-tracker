"""
Migration script to make watched_date column nullable in tv_show_seasons table.
SQLite doesn't support ALTER COLUMN to change NOT NULL constraints, so we need to recreate the table.
"""
import sqlite3

def migrate_tv_season_dates_nullable():
    conn = sqlite3.connect('media_tracker.db')
    cursor = conn.cursor()
    
    print("Starting migration: Making watched_date nullable in tv_show_seasons table...")
    
    try:
        # Check if watched_date is already nullable
        cursor.execute("PRAGMA table_info(tv_show_seasons)")
        columns = cursor.fetchall()
        
        watched_date_nullable = any(col[1] == 'watched_date' and col[3] == 0 for col in columns)
        
        if not watched_date_nullable:
            print("  Recreating tv_show_seasons table to make watched_date nullable...")
            
            # Get all existing data
            cursor.execute("SELECT * FROM tv_show_seasons")
            seasons_data = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Create new table with nullable watched_date
            cursor.execute("""
                CREATE TABLE tv_show_seasons_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    show_id INTEGER NOT NULL,
                    season_number INTEGER NOT NULL,
                    watched_date DATE,
                    rating FLOAT,
                    notes VARCHAR,
                    season_thumbnail_url VARCHAR,
                    created_at DATETIME,
                    FOREIGN KEY (show_id) REFERENCES tv_shows(id)
                )
            """)
            
            # Copy data to new table
            for season in seasons_data:
                season_dict = dict(zip(column_names, season))
                cursor.execute("""
                    INSERT INTO tv_show_seasons_new (id, show_id, season_number, watched_date, rating, notes, season_thumbnail_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    season_dict.get('id'),
                    season_dict.get('show_id'),
                    season_dict.get('season_number'),
                    season_dict.get('watched_date'),
                    season_dict.get('rating'),
                    season_dict.get('notes'),
                    season_dict.get('season_thumbnail_url'),
                    season_dict.get('created_at')
                ))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE tv_show_seasons")
            cursor.execute("ALTER TABLE tv_show_seasons_new RENAME TO tv_show_seasons")
            
            # Recreate indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tv_show_seasons_show_id ON tv_show_seasons(show_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tv_show_seasons_watched_date ON tv_show_seasons(watched_date)")
            
            print("  tv_show_seasons table updated successfully!")
        else:
            print("  watched_date is already nullable in tv_show_seasons table")
        
        print("\nMigration completed successfully!")
        print("watched_date column is now properly nullable and can accept NULL values.")
        
        conn.commit()
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_tv_season_dates_nullable()


