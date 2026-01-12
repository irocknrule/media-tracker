from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    year = Column(Integer)
    watched_date = Column(Date, nullable=True, index=True)
    status = Column(String, default="watched", index=True)  # "currently_watching", "want_to_watch", "watched", "dropped"
    rating = Column(Float)
    notes = Column(String)
    thumbnail_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class TVShow(Base):
    __tablename__ = "tv_shows"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    year = Column(Integer)  # Overall show year
    genres = Column(String)  # Comma-separated genres
    overall_rating = Column(Float)  # Overall show rating
    show_thumbnail_url = Column(String)  # Overall show poster
    status = Column(String, default="watched", index=True)  # "currently_watching", "want_to_watch", "watched", "dropped"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to seasons
    seasons = relationship("TVShowSeason", back_populates="show", cascade="all, delete-orphan")


class TVShowSeason(Base):
    __tablename__ = "tv_show_seasons"
    
    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("tv_shows.id"), nullable=False, index=True)
    season_number = Column(Integer, nullable=False)
    watched_date = Column(Date, nullable=True, index=True)  # Nullable to support in-progress status
    rating = Column(Float)
    notes = Column(String)
    season_thumbnail_url = Column(String)  # Individual season poster
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to show
    show = relationship("TVShow", back_populates="seasons")


class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, index=True)
    finished_date = Column(Date, nullable=True, index=True)
    status = Column(String, default="finished", index=True)  # "currently_reading", "want_to_read", "finished", "dropped"
    rating = Column(Float)
    notes = Column(String)
    thumbnail_url = Column(String)
    pages = Column(Integer)  # Number of pages
    created_at = Column(DateTime, default=datetime.utcnow)


class Music(Base):
    __tablename__ = "music"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    artist = Column(String, index=True)
    album = Column(String)
    listened_date = Column(Date, nullable=True, index=True)
    status = Column(String, default="listened", index=True)  # "currently_listening", "want_to_listen", "listened", "dropped"
    rating = Column(Float)
    notes = Column(String)
    thumbnail_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class HabitLog(Base):
    __tablename__ = "habit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    habit_type = Column(String, nullable=False, index=True)  # e.g., "exercise_workout", "mindfulness_meditation"
    metric_name = Column(String, nullable=False)  # e.g., "minutes", "distance", "elevation"
    value = Column(Float, nullable=False)  # The numeric value
    unit = Column(String, nullable=False)  # e.g., "min", "mi", "ft"
    created_at = Column(DateTime, default=datetime.utcnow)


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"
    __table_args__ = (
        UniqueConstraint(
            'ticker', 'transaction_type', 'transaction_date', 'quantity', 
            'price_per_unit', 'total_amount', 'fees', 'asset_type',
            name='uq_portfolio_transaction'
        ),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)  # Stock ticker symbol (e.g., "AAPL", "VTI")
    transaction_type = Column(String, nullable=False)  # "BUY" or "SELL"
    transaction_date = Column(Date, nullable=False, index=True)
    quantity = Column(Float, nullable=False)  # Number of shares/units
    price_per_unit = Column(Float, nullable=False)  # Price per share at transaction
    total_amount = Column(Float, nullable=False)  # Total transaction amount
    fees = Column(Float, default=0.0)  # Transaction fees
    notes = Column(String)  # Optional notes
    asset_type = Column(String, nullable=False)  # "STOCK", "ETF", or "MUTUAL_FUND"
    created_at = Column(DateTime, default=datetime.utcnow)


class AssetAllocationTarget(Base):
    __tablename__ = "asset_allocation_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, unique=True, index=True)  # "US Stocks", "International Stocks", "Bonds", "Cash"
    target_percentage = Column(Float, nullable=False)  # Target allocation percentage (0-100)
    threshold_percentage = Column(Float, nullable=False, default=5.0)  # Acceptable deviation threshold
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TickerCategory(Base):
    __tablename__ = "ticker_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, unique=True, index=True)  # Stock ticker symbol
    category = Column(String, nullable=False, index=True)  # "US Stocks", "International Stocks", "Bonds", "Cash"
    is_auto_categorized = Column(Boolean, default=True)  # Whether this was auto-detected or manually set
    notes = Column(String)  # Optional notes about the categorization
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Workout Tracking Models

class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    primary_muscle = Column(String, index=True)  # e.g., "Glutes", "Chest", "Upper Back"
    secondary_muscles = Column(String)  # JSON or comma-separated list
    notes = Column(String)  # Form cues, instructions, etc.
    image_url = Column(String)  # URL or path to exercise image/GIF
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exercise_records = relationship("ExerciseRecord", back_populates="exercise")
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan")


class Workout(Base):
    __tablename__ = "workouts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exercises = relationship("WorkoutExercise", back_populates="workout", cascade="all, delete-orphan")
    workout_records = relationship("WorkoutRecord", back_populates="workout")


class WorkoutExercise(Base):
    """Junction table to maintain exercise order in workouts"""
    __tablename__ = "workout_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)  # To maintain exercise order
    notes = Column(String)  # Specific notes for this exercise in this workout
    
    # Relationships
    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")


class WorkoutRecord(Base):
    __tablename__ = "workout_records"
    
    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=True, index=True)  # Nullable for ad-hoc workouts
    workout_name = Column(String, index=True)  # Store name for reference (even if ad-hoc)
    workout_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer)  # Optional workout duration
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workout = relationship("Workout", back_populates="workout_records")
    exercise_records = relationship("ExerciseRecord", back_populates="workout_record", cascade="all, delete-orphan")


class ExerciseRecord(Base):
    __tablename__ = "exercise_records"
    
    id = Column(Integer, primary_key=True, index=True)
    workout_record_id = Column(Integer, ForeignKey("workout_records.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)
    exercise_name = Column(String, index=True)  # Store name for reference
    
    # Performance metrics
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    weight_unit = Column(String, default="lbs")  # "lbs" or "kg"
    
    # For cardio exercises
    time_seconds = Column(Integer)  # Duration in seconds
    distance = Column(Float)  # Distance covered
    distance_unit = Column(String)  # "mi", "km", "m"
    
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workout_record = relationship("WorkoutRecord", back_populates="exercise_records")
    exercise = relationship("Exercise", back_populates="exercise_records")

