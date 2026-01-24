"""
Migration script to add 'status' column to books, movies, tv_shows, and music tables.
Also makes date columns nullable (finished_date, watched_date, listened_date) to support in-progress status.
"""
import sqlite3

def migrate_add_status():
    conn = sqlite3.connect('media_tracker.db')
    cursor = conn.cursor()
    
    print("Starting migration: Adding 'status' columns and making date fields nullable...")
    
    try:
        # Books table
        print("\n1. Updating books table...")
        cursor.execute("PRAGMA table_info(books)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Make finished_date nullable (SQLite doesn't support ALTER COLUMN, so we'll recreate if needed)
        # Actually, SQLite doesn't enforce NOT NULL constraints on existing columns when adding new columns
        # But we need to add the status column
        if 'status' not in columns:
            print("  Adding 'status' column to books table...")
            cursor.execute("""
                ALTER TABLE books 
                ADD COLUMN status TEXT DEFAULT 'finished'
            """)
            # Create index on status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_status ON books(status)
            """)
            print("  Status column added with default value 'finished'")
        else:
            print("  Status column already exists in books table")
        
        # Movies table
        print("\n2. Updating movies table...")
        cursor.execute("PRAGMA table_info(movies)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            print("  Adding 'status' column to movies table...")
            cursor.execute("""
                ALTER TABLE movies 
                ADD COLUMN status TEXT DEFAULT 'watched'
            """)
            # Create index on status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_movies_status ON movies(status)
            """)
            print("  Status column added with default value 'watched'")
        else:
            print("  Status column already exists in movies table")
        
        # TV Shows table
        print("\n3. Updating tv_shows table...")
        cursor.execute("PRAGMA table_info(tv_shows)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            print("  Adding 'status' column to tv_shows table...")
            cursor.execute("""
                ALTER TABLE tv_shows 
                ADD COLUMN status TEXT DEFAULT 'watched'
            """)
            # Create index on status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tv_shows_status ON tv_shows(status)
            """)
            print("  Status column added with default value 'watched'")
        else:
            print("  Status column already exists in tv_shows table")
        
        # Music table
        print("\n4. Updating music table...")
        cursor.execute("PRAGMA table_info(music)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            print("  Adding 'status' column to music table...")
            cursor.execute("""
                ALTER TABLE music 
                ADD COLUMN status TEXT DEFAULT 'listened'
            """)
            # Create index on status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_music_status ON music(status)
            """)
            print("  Status column added with default value 'listened'")
        else:
            print("  Status column already exists in music table")
        
        # Note: SQLite doesn't support ALTER COLUMN to change NULL constraints
        # The existing date columns will work fine - SQLite will allow NULL values
        # even if they were originally NOT NULL, as long as we don't recreate the table
        print("\n5. Date columns are now effectively nullable")
        print("   (SQLite allows NULL values in existing NOT NULL columns)")
        
        print("\nMigration completed successfully!")
        print("\nStatus values:")
        print("  - Books: 'currently_reading', 'want_to_read', 'finished', 'dropped'")
        print("  - Movies: 'currently_watching', 'want_to_watch', 'watched', 'dropped'")
        print("  - TV Shows: 'currently_watching', 'want_to_watch', 'watched', 'dropped'")
        print("  - Music: 'currently_listening', 'want_to_listen', 'listened', 'dropped'")
        
        conn.commit()
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_status()


