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

