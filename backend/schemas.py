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
    watched_date: Optional[date] = None
    status: Optional[str] = "watched"  # "currently_watching", "want_to_watch", "watched", "dropped"
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    watched_date: Optional[date] = None
    status: Optional[str] = None
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
    watched_date: Optional[date] = None  # Nullable to support in-progress status
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
    status: Optional[str] = "watched"  # "currently_watching", "want_to_watch", "watched", "dropped"


class TVShowCreate(TVShowBase):
    pass


class TVShowUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    genres: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=0, le=10)
    show_thumbnail_url: Optional[str] = None
    status: Optional[str] = None


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
    watched_date: Optional[date] = None
    status: Optional[str] = "watched"  # "currently_watching", "want_to_watch", "watched", "dropped"
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None


class TVShowLegacyCreate(TVShowLegacyBase):
    pass


# Book schemas
class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    finished_date: Optional[date] = None
    status: Optional[str] = "finished"  # "currently_reading", "want_to_read", "finished", "dropped"
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
    status: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    thumbnail_url: Optional[str] = None
    pages: Optional[int] = Field(None, ge=1)


class Book(BookBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookYearStat(BaseModel):
    """Stats per year (by finished_date) for books."""
    year: int
    book_count: int
    total_pages: int


# Music schemas
class MusicBase(BaseModel):
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    listened_date: Optional[date] = None
    status: Optional[str] = "listened"  # "currently_listening", "want_to_listen", "listened", "dropped"
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
    status: Optional[str] = None
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


class PortfolioUploadResponse(BaseModel):
    """Response for transaction upload with created vs duplicate counts"""
    transactions: List[PortfolioTransaction]
    created_count: int
    duplicates_count: int


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


class YearlyInvestmentTicker(BaseModel):
    """Per-ticker breakdown within a yearly investment"""
    ticker: str
    asset_type: str
    total_amount: float
    fees: float
    transaction_count: int
    cost_basis_remaining: Optional[float] = None  # Cost basis from this year still held (FIFO + splits)
    current_value: Optional[float] = None  # Current value of those shares
    gain_loss: Optional[float] = None  # current_value - cost_basis_remaining


class YearlyInvestment(BaseModel):
    """Total cost basis invested into the brokerage account for a given year"""
    year: int
    total_invested: float
    total_fees: float
    transaction_count: int
    tickers: List[YearlyInvestmentTicker] = []
    cost_basis_remaining: Optional[float] = None  # Cost basis from this year still held
    current_value_remaining: Optional[float] = None  # Current value of those shares
    gain_loss: Optional[float] = None  # current_value_remaining - cost_basis_remaining
    gain_loss_percentage: Optional[float] = None  # (gain_loss / cost_basis_remaining) * 100 when > 0


# Performance / Top Performers schemas
class TickerPerformance(BaseModel):
    ticker: str
    asset_type: str
    quantity: float
    current_price: Optional[float] = None
    period_start_price: Optional[float] = None
    period_return_pct: Optional[float] = None
    period_dollar_change: Optional[float] = None
    total_invested: float
    current_value: Optional[float] = None
    all_time_return_pct: Optional[float] = None
    all_time_dollar_change: Optional[float] = None


class PerformanceSummary(BaseModel):
    timeframe: str
    tickers: List[TickerPerformance]
    portfolio_period_return_pct: Optional[float] = None
    portfolio_period_dollar_change: Optional[float] = None
    portfolio_total_invested: float
    portfolio_current_value: Optional[float] = None


# Asset Allocation schemas
class AssetAllocationTargetBase(BaseModel):
    """Base schema for asset allocation target"""
    category: str
    target_percentage: float = Field(..., ge=0, le=100)
    threshold_percentage: float = Field(default=5.0, ge=0, le=100)


class AssetAllocationTargetCreate(AssetAllocationTargetBase):
    """Schema for creating asset allocation target"""
    pass


class AssetAllocationTargetUpdate(BaseModel):
    """Schema for updating asset allocation target"""
    target_percentage: Optional[float] = Field(None, ge=0, le=100)
    threshold_percentage: Optional[float] = Field(None, ge=0, le=100)


class AssetAllocationTarget(AssetAllocationTargetBase):
    """Schema for asset allocation target response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TickerCategoryBase(BaseModel):
    """Base schema for ticker category"""
    ticker: str
    category: str
    is_auto_categorized: bool = True
    notes: Optional[str] = None


class TickerCategoryCreate(TickerCategoryBase):
    """Schema for creating ticker category"""
    pass


class TickerCategoryUpdate(BaseModel):
    """Schema for updating ticker category"""
    category: Optional[str] = None
    is_auto_categorized: Optional[bool] = None
    notes: Optional[str] = None


class TickerCategory(TickerCategoryBase):
    """Schema for ticker category response"""
    id: int
    created_at: datetime
    updated_at: datetime
    ticker_name: Optional[str] = None  # Full name of the ticker
    
    class Config:
        from_attributes = True


class AllocationCategorySummary(BaseModel):
    """Summary for a single allocation category"""
    category: str
    target_percentage: float
    actual_percentage: float
    difference: float
    threshold: float
    current_value: float
    needs_rebalancing: bool


class AssetAllocationSummary(BaseModel):
    """Complete asset allocation summary"""
    total_portfolio_value: float
    categories: List[AllocationCategorySummary]
    last_updated: Optional[datetime] = None


# FIRE Journey Tracker schemas

class InvestmentAccountBase(BaseModel):
    name: str
    account_type: str  # "401K", "IRA", "ROTH_IRA", "HSA", "BROKERAGE", "STOCK_PLAN", "OTHER"
    owner: str
    institution: Optional[str] = None
    last_four: Optional[str] = None
    is_active: bool = True


class InvestmentAccountCreate(InvestmentAccountBase):
    balance: Optional[float] = None
    snapshot_date: Optional[date] = None


class InvestmentAccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    owner: Optional[str] = None
    institution: Optional[str] = None
    last_four: Optional[str] = None
    is_active: Optional[bool] = None


class InvestmentAccount(InvestmentAccountBase):
    id: int
    created_at: datetime
    updated_at: datetime
    latest_balance: Optional[float] = None
    latest_snapshot_date: Optional[date] = None
    
    class Config:
        from_attributes = True


class AccountSnapshotBase(BaseModel):
    snapshot_date: date
    balance: float
    contributions_since_last: Optional[float] = 0.0
    notes: Optional[str] = None


class AccountSnapshotCreate(AccountSnapshotBase):
    account_id: int


class AccountSnapshotUpdate(BaseModel):
    balance: Optional[float] = None
    contributions_since_last: Optional[float] = None
    notes: Optional[str] = None


class AccountSnapshot(AccountSnapshotBase):
    id: int
    account_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BulkSnapshotEntry(BaseModel):
    account_id: int
    balance: float
    contributions_since_last: Optional[float] = 0.0


class BulkSnapshotCreate(BaseModel):
    snapshot_date: date
    entries: List[BulkSnapshotEntry]


class BulkAccountImport(BaseModel):
    text: str
    snapshot_date: Optional[date] = None


class BulkAccountImportResult(BaseModel):
    accounts_created: int
    accounts_updated: int
    snapshots_created: int
    accounts: List[InvestmentAccount]


class OwnerSummary(BaseModel):
    owner: str
    total_value: float
    account_count: int


class AccountTypeSummary(BaseModel):
    account_type: str
    total_value: float
    account_count: int


class FireDashboard(BaseModel):
    total_portfolio_value: float
    by_owner: List[OwnerSummary]
    by_account_type: List[AccountTypeSummary]
    total_investment_income: Optional[float] = None
    month_over_month_change: Optional[float] = None
    month_over_month_change_pct: Optional[float] = None


class IncomeHistoryEntry(BaseModel):
    period_start: date
    period_end: date
    starting_balance: float
    ending_balance: float
    contributions: float
    investment_income: float
    growth_rate_pct: float


class IncomeHistory(BaseModel):
    entries: List[IncomeHistoryEntry]
    total_investment_income: float
    total_contributions: float


class PortfolioAggregateSnapshotBase(BaseModel):
    snapshot_date: date
    total_value: float
    contributions_since_last: Optional[float] = 0.0
    notes: Optional[str] = None


class PortfolioAggregateSnapshotCreate(PortfolioAggregateSnapshotBase):
    pass


class PortfolioAggregateSnapshotUpdate(BaseModel):
    total_value: Optional[float] = None
    contributions_since_last: Optional[float] = None
    notes: Optional[str] = None


class PortfolioAggregateSnapshot(PortfolioAggregateSnapshotBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Workout Tracking schemas

class ExerciseBase(BaseModel):
    """Base schema for exercise"""
    name: str
    primary_muscle: Optional[str] = None
    secondary_muscles: Optional[str] = None  # JSON or comma-separated
    notes: Optional[str] = None
    image_url: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise"""
    pass


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise"""
    name: Optional[str] = None
    primary_muscle: Optional[str] = None
    secondary_muscles: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


class Exercise(ExerciseBase):
    """Schema for exercise response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkoutExerciseBase(BaseModel):
    """Base schema for workout-exercise relationship"""
    exercise_id: int
    order_index: int
    notes: Optional[str] = None


class WorkoutExerciseCreate(WorkoutExerciseBase):
    """Schema for adding exercise to workout"""
    pass


class WorkoutExerciseDetail(BaseModel):
    """Detailed workout-exercise with exercise info"""
    id: int
    exercise_id: int
    exercise_name: str
    primary_muscle: Optional[str] = None
    order_index: int
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class WorkoutBase(BaseModel):
    """Base schema for workout"""
    name: str
    description: Optional[str] = None


class WorkoutCreate(BaseModel):
    """Schema for creating a workout with exercises"""
    name: str
    description: Optional[str] = None
    exercise_ids: List[int] = []  # List of exercise IDs in order


class WorkoutUpdate(BaseModel):
    """Schema for updating a workout"""
    name: Optional[str] = None
    description: Optional[str] = None
    exercise_ids: Optional[List[int]] = None  # Update exercise list


class Workout(WorkoutBase):
    """Schema for workout response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkoutWithExercises(Workout):
    """Workout response with exercise details"""
    exercises: List[WorkoutExerciseDetail] = []
    
    class Config:
        from_attributes = True


class SetRecordBase(BaseModel):
    """Base schema for individual set record"""
    set_number: int
    reps: int
    weight: float
    weight_unit: Optional[str] = "lbs"
    notes: Optional[str] = None


class SetRecordCreate(SetRecordBase):
    """Schema for creating a set record"""
    pass


class SetRecord(SetRecordBase):
    """Schema for set record response"""
    id: int
    exercise_record_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExerciseRecordBase(BaseModel):
    """Base schema for exercise record"""
    exercise_id: int
    sets: Optional[int] = None  # Kept for backward compatibility
    reps: Optional[int] = None  # Kept for backward compatibility
    weight: Optional[float] = None  # Kept for backward compatibility
    weight_unit: Optional[str] = "lbs"
    time_seconds: Optional[int] = None
    distance: Optional[float] = None
    distance_unit: Optional[str] = None
    notes: Optional[str] = None
    set_records: Optional[List[SetRecordCreate]] = None  # Individual sets with reps and weight


class ExerciseRecordCreate(ExerciseRecordBase):
    """Schema for creating an exercise record"""
    pass


class ExerciseRecord(ExerciseRecordBase):
    """Schema for exercise record response"""
    id: int
    workout_record_id: int
    exercise_name: str
    created_at: datetime
    set_records: Optional[List[SetRecord]] = []  # Individual sets
    
    class Config:
        from_attributes = True


class WorkoutRecordBase(BaseModel):
    """Base schema for workout record"""
    workout_id: Optional[int] = None  # Nullable for ad-hoc workouts
    workout_name: str
    workout_date: datetime
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class WorkoutRecordCreate(BaseModel):
    """Schema for creating a workout record with exercises"""
    workout_id: Optional[int] = None
    workout_name: str
    workout_date: datetime
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    exercises: List[ExerciseRecordCreate] = []


class WorkoutRecordUpdate(BaseModel):
    """Schema for updating a workout record"""
    workout_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class WorkoutRecord(WorkoutRecordBase):
    """Schema for workout record response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkoutRecordWithExercises(WorkoutRecord):
    """Workout record with exercise details"""
    exercises: List[ExerciseRecord] = []
    
    class Config:
        from_attributes = True


class ExerciseProgressEntry(BaseModel):
    """Single entry for exercise progress tracking"""
    date: datetime
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    volume: Optional[float] = None  # sets * reps * weight
    one_rep_max: Optional[float] = None  # Estimated 1RM


class ExerciseProgress(BaseModel):
    """Progress tracking for an exercise"""
    exercise_id: int
    exercise_name: str
    history: List[ExerciseProgressEntry] = []
    personal_record_weight: Optional[float] = None
    personal_record_volume: Optional[float] = None
    personal_record_reps: Optional[int] = None


class WorkoutAnalytics(BaseModel):
    """Analytics summary for workouts"""
    total_workouts: int
    total_exercises_logged: int
    unique_exercises: int
    total_volume: float  # Sum of all sets * reps * weight
    most_frequent_exercises: List[dict]  # List of {exercise_name, count}
    workout_frequency_by_month: List[dict]  # {month, count}
    muscle_group_distribution: dict  # {muscle_group: count}


# Home internet usage (monthly)

class HomeInternetUsageMonthBase(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    total_gb: float = Field(..., gt=0)
    download_gb: Optional[float] = Field(None, ge=0)
    upload_gb: Optional[float] = Field(None, ge=0)
    source: str = "manual"
    notes: Optional[str] = None


class HomeInternetUsageMonthUpsert(HomeInternetUsageMonthBase):
    """Create or replace the record for this calendar month."""

    pass


class HomeInternetUsageMonthUpdate(BaseModel):
    total_gb: Optional[float] = Field(None, gt=0)
    download_gb: Optional[float] = Field(None, ge=0)
    upload_gb: Optional[float] = Field(None, ge=0)
    source: Optional[str] = None
    notes: Optional[str] = None


class HomeInternetUsageMonth(HomeInternetUsageMonthBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EeroScreenshotParseResult(BaseModel):
    ocr_text_preview: str
    suggested_year: Optional[int] = None
    suggested_month: Optional[int] = None
    suggested_total_gb: Optional[float] = None
    total_parse_hint: Optional[str] = None
    parse_note: Optional[str] = None
    ocr_available: bool = True

