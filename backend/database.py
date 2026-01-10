from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User
from passlib.context import CryptContext
import os
import warnings
import logging

# Suppress bcrypt version warning
logging.getLogger('passlib').setLevel(logging.ERROR)
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')

# Database setup
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db():
    """Initialize database and create default admin user"""
    Base.metadata.create_all(bind=engine)
    
    # Run migrations
    migrate_add_thumbnail_url()
    migrate_add_habits()
    migrate_add_portfolio()
    
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # Create default admin user
            password = "admin123"
            # Ensure password is not longer than 72 bytes for bcrypt
            if len(password.encode('utf-8')) > 72:
                password = password[:72]
            admin_password_hash = pwd_context.hash(password)
            admin_user = User(
                username="admin",
                password_hash=admin_password_hash
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created (username: admin, password: admin123)")
        else:
            print("Database already initialized")
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_add_thumbnail_url():
    """Migration: Add thumbnail_url column to tv_shows, movies, books, and music tables"""
    db = SessionLocal()
    try:
        tables = ["tv_shows", "movies", "books", "music"]
        
        for table in tables:
            if "sqlite" in SQLALCHEMY_DATABASE_URL:
                # SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
                # So we'll try to add it and catch the error if it exists
                try:
                    db.execute(text(f"ALTER TABLE {table} ADD COLUMN thumbnail_url VARCHAR"))
                    db.commit()
                    print(f"Successfully added thumbnail_url column to {table} table")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"Column thumbnail_url already exists in {table}, skipping migration")
                        db.rollback()
                    else:
                        raise
            else:
                # For other databases (PostgreSQL, MySQL, etc.)
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR"))
                db.commit()
                print(f"Successfully added thumbnail_url column to {table} table")
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def migrate_add_habits():
    """Migration: Create habit_logs table"""
    import sqlite3
    
    db_path = SQLALCHEMY_DATABASE_URL
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='habit_logs'
        """)
        
        if cursor.fetchone():
            print("Table 'habit_logs' already exists. Migration not needed.")
            conn.close()
            return
        
        # Create the habit_logs table
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
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_habit_logs_date ON habit_logs(date)
        """)
        cursor.execute("""
            CREATE INDEX idx_habit_logs_habit_type ON habit_logs(habit_type)
        """)
        cursor.execute("""
            CREATE INDEX idx_habit_logs_date_habit_type ON habit_logs(date, habit_type)
        """)
        
        print("Successfully created habit_logs table with indexes")
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error during habit migration: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()


def migrate_add_habits():
    """Migration: Create habit_logs table"""
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from migrate_add_habits import migrate_add_habits as run_migration
    run_migration()


def migrate_add_portfolio():
    """Migration: Create portfolio_transactions table"""
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from migrate_add_portfolio import migrate_add_portfolio as run_migration
    run_migration()


if __name__ == "__main__":
    init_db()
    migrate_add_thumbnail_url()
    migrate_add_habits()
    migrate_add_portfolio()

