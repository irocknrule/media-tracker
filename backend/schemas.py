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


# Habit schemas
class HabitLogBase(BaseModel):
    date: date
    habit_type: str
    metric_name: str
    value: float
    unit: str


class HabitLogCreate(HabitLogBase):
    pass


class HabitLog(HabitLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class HabitLogEntry(BaseModel):
    """Individual habit log entry without date (date comes from batch)"""
    habit_type: str
    metric_name: str
    value: float
    unit: str


class HabitLogBatchCreate(BaseModel):
    """Batch create multiple habit logs for a single date"""
    date: date
    logs: List[HabitLogEntry]


class HabitLogResponse(BaseModel):
    """Response format for habit logs grouped by date"""
    date: date
    habits: dict  # Dictionary mapping habit_type to list of metrics


class HabitCalendarEntry(BaseModel):
    """Entry for calendar view showing which habits were done on a date"""
    date: date
    habit_types: List[str]  # List of habit types completed on this date


# Portfolio schemas
class PortfolioTransactionBase(BaseModel):
    ticker: str
    transaction_type: str  # "BUY" or "SELL"
    transaction_date: date
    quantity: float
    price_per_unit: float
    total_amount: float
    fees: Optional[float] = 0.0
    notes: Optional[str] = None
    asset_type: str  # "STOCK", "ETF", or "MUTUAL_FUND"


class PortfolioTransactionCreate(PortfolioTransactionBase):
    pass


class PortfolioTransactionUpdate(BaseModel):
    ticker: Optional[str] = None
    transaction_type: Optional[str] = None
    transaction_date: Optional[date] = None
    quantity: Optional[float] = None
    price_per_unit: Optional[float] = None
    total_amount: Optional[float] = None
    fees: Optional[float] = None
    notes: Optional[str] = None
    asset_type: Optional[str] = None


class PortfolioTransaction(PortfolioTransactionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioTransactionBatchCreate(BaseModel):
    """Batch upload multiple transactions from JSON"""
    transactions: List[PortfolioTransactionCreate]


class TickerHolding(BaseModel):
    """Current holding information for a ticker"""
    ticker: str
    asset_type: str
    total_quantity: float
    average_cost: float
    total_invested: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Overall portfolio summary"""
    total_invested: float
    current_value: Optional[float] = None
    total_profit_loss: Optional[float] = None
    total_profit_loss_percentage: Optional[float] = None
    holdings: List[TickerHolding]
    last_updated: Optional[datetime] = None

