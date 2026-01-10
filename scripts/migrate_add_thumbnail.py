#!/usr/bin/env python3
"""
Migration script to add thumbnail_url column to tv_shows table
Run this script to update your existing database schema.
"""
import sqlite3
import os

DB_PATH = "media_tracker.db"

def migrate():
    """Add thumbnail_url column to tv_shows table"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists by trying to query it
        cursor.execute("SELECT thumbnail_url FROM tv_shows LIMIT 1")
        print("Column thumbnail_url already exists. Migration not needed.")
    except sqlite3.OperationalError:
        # Column doesn't exist, add it
        try:
            cursor.execute("ALTER TABLE tv_shows ADD COLUMN thumbnail_url TEXT")
            conn.commit()
            print("✓ Successfully added thumbnail_url column to tv_shows table")
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

