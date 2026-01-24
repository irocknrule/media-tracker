"""
Migration script to make date columns nullable in books, movies, and music tables.
SQLite doesn't support ALTER COLUMN to change NOT NULL constraints, so we need to recreate the tables.
"""
import sqlite3
import json
from datetime import datetime

def migrate_make_dates_nullable():
    conn = sqlite3.connect('media_tracker.db')
    cursor = conn.cursor()
    
    print("Starting migration: Making date columns nullable...")
    
    try:
        # Books table
        print("\n1. Updating books table...")
        cursor.execute("PRAGMA table_info(books)")
        columns = cursor.fetchall()
        
        # Check if finished_date is already nullable
        finished_date_nullable = any(col[1] == 'finished_date' and col[3] == 0 for col in columns)
        
        if not finished_date_nullable:
            print("  Recreating books table to make finished_date nullable...")
            
            # Get all existing data
            cursor.execute("SELECT * FROM books")
            books_data = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Create new table with nullable finished_date
            cursor.execute("""
                CREATE TABLE books_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR NOT NULL,
                    author VARCHAR,
                    finished_date DATE,
                    rating FLOAT,
                    notes VARCHAR,
                    created_at DATETIME,
                    thumbnail_url VARCHAR,
                    pages INTEGER,
                    status TEXT DEFAULT 'finished'
                )
            """)
            
            # Copy data to new table (handling NULL dates)
            for book in books_data:
                book_dict = dict(zip(column_names, book))
                # finished_date can be NULL now
                cursor.execute("""
                    INSERT INTO books_new (id, title, author, finished_date, rating, notes, created_at, thumbnail_url, pages, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    book_dict.get('id'),
                    book_dict.get('title'),
                    book_dict.get('author'),
                    book_dict.get('finished_date'),
                    book_dict.get('rating'),
                    book_dict.get('notes'),
                    book_dict.get('created_at'),
                    book_dict.get('thumbnail_url'),
                    book_dict.get('pages'),
                    book_dict.get('status', 'finished')
                ))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE books")
            cursor.execute("ALTER TABLE books_new RENAME TO books")
            
            # Recreate indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_finished_date ON books(finished_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_status ON books(status)")
            
            print("  Books table updated successfully!")
        else:
            print("  finished_date is already nullable in books table")
        
        # Movies table
        print("\n2. Updating movies table...")
        cursor.execute("PRAGMA table_info(movies)")
        columns = cursor.fetchall()
        
        watched_date_nullable = any(col[1] == 'watched_date' and col[3] == 0 for col in columns)
        
        if not watched_date_nullable:
            print("  Recreating movies table to make watched_date nullable...")
            
            cursor.execute("SELECT * FROM movies")
            movies_data = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            cursor.execute("""
                CREATE TABLE movies_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR NOT NULL,
                    year INTEGER,
                    watched_date DATE,
                    status TEXT DEFAULT 'watched',
                    rating FLOAT,
                    notes VARCHAR,
                    thumbnail_url VARCHAR,
                    created_at DATETIME
                )
            """)
            
            for movie in movies_data:
                movie_dict = dict(zip(column_names, movie))
                cursor.execute("""
                    INSERT INTO movies_new (id, title, year, watched_date, status, rating, notes, thumbnail_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    movie_dict.get('id'),
                    movie_dict.get('title'),
                    movie_dict.get('year'),
                    movie_dict.get('watched_date'),
                    movie_dict.get('status', 'watched'),
                    movie_dict.get('rating'),
                    movie_dict.get('notes'),
                    movie_dict.get('thumbnail_url'),
                    movie_dict.get('created_at')
                ))
            
            cursor.execute("DROP TABLE movies")
            cursor.execute("ALTER TABLE movies_new RENAME TO movies")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_watched_date ON movies(watched_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_status ON movies(status)")
            
            print("  Movies table updated successfully!")
        else:
            print("  watched_date is already nullable in movies table")
        
        # Music table
        print("\n3. Updating music table...")
        cursor.execute("PRAGMA table_info(music)")
        columns = cursor.fetchall()
        
        listened_date_nullable = any(col[1] == 'listened_date' and col[3] == 0 for col in columns)
        
        if not listened_date_nullable:
            print("  Recreating music table to make listened_date nullable...")
            
            cursor.execute("SELECT * FROM music")
            music_data = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            cursor.execute("""
                CREATE TABLE music_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR NOT NULL,
                    artist VARCHAR,
                    album VARCHAR,
                    listened_date DATE,
                    status TEXT DEFAULT 'listened',
                    rating FLOAT,
                    notes VARCHAR,
                    thumbnail_url VARCHAR,
                    created_at DATETIME
                )
            """)
            
            for music in music_data:
                music_dict = dict(zip(column_names, music))
                cursor.execute("""
                    INSERT INTO music_new (id, title, artist, album, listened_date, status, rating, notes, thumbnail_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    music_dict.get('id'),
                    music_dict.get('title'),
                    music_dict.get('artist'),
                    music_dict.get('album'),
                    music_dict.get('listened_date'),
                    music_dict.get('status', 'listened'),
                    music_dict.get('rating'),
                    music_dict.get('notes'),
                    music_dict.get('thumbnail_url'),
                    music_dict.get('created_at')
                ))
            
            cursor.execute("DROP TABLE music")
            cursor.execute("ALTER TABLE music_new RENAME TO music")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_music_listened_date ON music(listened_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_music_status ON music(status)")
            
            print("  Music table updated successfully!")
        else:
            print("  listened_date is already nullable in music table")
        
        print("\nMigration completed successfully!")
        print("Date columns are now properly nullable and can accept NULL values.")
        
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
    migrate_make_dates_nullable()


