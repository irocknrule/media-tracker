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
    """Migration: Add thumbnail_url column to tv_shows table"""
    db = SessionLocal()
    try:
        # Check if column already exists
        if "sqlite" in SQLALCHEMY_DATABASE_URL:
            # SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
            # So we'll try to add it and catch the error if it exists
            try:
                db.execute(text("ALTER TABLE tv_shows ADD COLUMN thumbnail_url VARCHAR"))
                db.commit()
                print("Successfully added thumbnail_url column to tv_shows table")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("Column thumbnail_url already exists, skipping migration")
                else:
                    raise
        else:
            # For other databases (PostgreSQL, MySQL, etc.)
            db.execute(text("ALTER TABLE tv_shows ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR"))
            db.commit()
            print("Successfully added thumbnail_url column to tv_shows table")
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    migrate_add_thumbnail_url()

