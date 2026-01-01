from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


# Authentication schemas
class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Movie schemas
class MovieBase(BaseModel):
    title: str
    year: Optional[int] = None
    watched_date: date
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    watched_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class Movie(MovieBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# TV Show schemas
class TVShowSeasonBase(BaseModel):
    season_number: int
    watched_date: date
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    season_thumbnail_url: Optional[str] = None


class TVShowSeasonCreate(TVShowSeasonBase):
    show_id: int


class TVShowSeasonUpdate(BaseModel):
    season_number: Optional[int] = None
    watched_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    season_thumbnail_url: Optional[str] = None


class TVShowSeason(TVShowSeasonBase):
    id: int
    show_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TVShowBase(BaseModel):
    title: str
    year: Optional[int] = None
    genres: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=0, le=10)
    show_thumbnail_url: Optional[str] = None


class TVShowCreate(TVShowBase):
    pass


class TVShowUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    genres: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=0, le=10)
    show_thumbnail_url: Optional[str] = None


class TVShow(TVShowBase):
    id: int
    created_at: datetime
    seasons: List['TVShowSeason'] = []
    
    class Config:
        from_attributes = True


# Legacy schemas for backward compatibility
class TVShowLegacyBase(BaseModel):
    title: str
    season: Optional[int] = None
    watched_date: date
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class TVShowLegacyCreate(TVShowLegacyBase):
    pass


# Book schemas
class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    finished_date: date
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None
    pages: Optional[int] = Field(None, ge=1)  # Number of pages (must be positive if provided)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    finished_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None
    pages: Optional[int] = Field(None, ge=1)


class Book(BookBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Music schemas
class MusicBase(BaseModel):
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    listened_date: date
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class MusicCreate(MusicBase):
    pass


class MusicUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    listened_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class Music(MusicBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Analytics schemas
class YearSummary(BaseModel):
    year: int
    movies_count: int
    tv_shows_count: int
    books_count: int
    music_count: int
    avg_movie_rating: Optional[float] = None
    avg_tv_rating: Optional[float] = None
    avg_book_rating: Optional[float] = None
    avg_music_rating: Optional[float] = None
    total_pages_read: Optional[int] = None  # Total pages from all books
    avg_pages_per_book: Optional[float] = None  # Average pages per book


class YearComparison(BaseModel):
    year1: YearSummary
    year2: YearSummary
    movies_change: float
    tv_shows_change: float
    books_change: float
    music_change: float

