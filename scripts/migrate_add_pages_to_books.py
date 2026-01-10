"""
Migration script to add 'pages' column to the books table.
This is a simple schema change - adding an optional integer column.
"""
import sqlite3

def migrate_books_add_pages():
    conn = sqlite3.connect('media_tracker.db')
    cursor = conn.cursor()
    
    print("Starting migration: Adding 'pages' column to books table...")
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(books)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'pages' in columns:
            print("Column 'pages' already exists in books table. Migration not needed.")
            return
        
        # Add the pages column
        print("Adding 'pages' column to books table...")
        cursor.execute("""
            ALTER TABLE books 
            ADD COLUMN pages INTEGER
        """)
        
        print("Migration completed successfully!")
        print("The 'pages' column has been added to the books table.")
        print("Existing books will have NULL for pages - you can update them as needed.")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_books_add_pages()

