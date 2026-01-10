from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Boolean
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
    watched_date = Column(Date, nullable=False, index=True)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to seasons
    seasons = relationship("TVShowSeason", back_populates="show", cascade="all, delete-orphan")


class TVShowSeason(Base):
    __tablename__ = "tv_show_seasons"
    
    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("tv_shows.id"), nullable=False, index=True)
    season_number = Column(Integer, nullable=False)
    watched_date = Column(Date, nullable=False, index=True)
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
    finished_date = Column(Date, nullable=False, index=True)
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
    listened_date = Column(Date, nullable=False, index=True)
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

