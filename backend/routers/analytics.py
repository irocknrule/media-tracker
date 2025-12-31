from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
from backend.database import get_db
from backend.models import Movie, TVShow, Book, Music, User
from backend.schemas import YearSummary, YearComparison
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/year/{year}", response_model=YearSummary)
def get_year_summary(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for a specific year"""
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    
    # Movies
    movies = db.query(Movie).filter(
        Movie.watched_date >= year_start,
        Movie.watched_date <= year_end
    ).all()
    movies_count = len(movies)
    avg_movie_rating = sum(m.rating for m in movies if m.rating) / len([m for m in movies if m.rating]) if any(m.rating for m in movies) else None
    
    # TV Shows
    tv_shows = db.query(TVShow).filter(
        TVShow.watched_date >= year_start,
        TVShow.watched_date <= year_end
    ).all()
    tv_shows_count = len(tv_shows)
    avg_tv_rating = sum(t.rating for t in tv_shows if t.rating) / len([t for t in tv_shows if t.rating]) if any(t.rating for t in tv_shows) else None
    
    # Books
    books = db.query(Book).filter(
        Book.finished_date >= year_start,
        Book.finished_date <= year_end
    ).all()
    books_count = len(books)
    avg_book_rating = sum(b.rating for b in books if b.rating) / len([b for b in books if b.rating]) if any(b.rating for b in books) else None
    
    # Music
    music = db.query(Music).filter(
        Music.listened_date >= year_start,
        Music.listened_date <= year_end
    ).all()
    music_count = len(music)
    avg_music_rating = sum(m.rating for m in music if m.rating) / len([m for m in music if m.rating]) if any(m.rating for m in music) else None
    
    return YearSummary(
        year=year,
        movies_count=movies_count,
        tv_shows_count=tv_shows_count,
        books_count=books_count,
        music_count=music_count,
        avg_movie_rating=avg_movie_rating,
        avg_tv_rating=avg_tv_rating,
        avg_book_rating=avg_book_rating,
        avg_music_rating=avg_music_rating
    )


@router.get("/compare/{year1}/{year2}", response_model=YearComparison)
def compare_years(
    year1: int,
    year2: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare statistics between two years"""
    summary1 = get_year_summary(year1, db, current_user)
    summary2 = get_year_summary(year2, db, current_user)
    
    def calculate_change(old: int, new: int) -> float:
        if old == 0:
            return 100.0 if new > 0 else 0.0
        return ((new - old) / old) * 100
    
    return YearComparison(
        year1=summary1,
        year2=summary2,
        movies_change=calculate_change(summary1.movies_count, summary2.movies_count),
        tv_shows_change=calculate_change(summary1.tv_shows_count, summary2.tv_shows_count),
        books_change=calculate_change(summary1.books_count, summary2.books_count),
        music_change=calculate_change(summary1.music_count, summary2.music_count)
    )


@router.get("/years")
def get_available_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of years that have data"""
    years = set()
    
    # Get years from movies
    movies = db.query(Movie).all()
    years.update(m.watched_date.year for m in movies)
    
    # Get years from TV shows
    tv_shows = db.query(TVShow).all()
    years.update(t.watched_date.year for t in tv_shows)
    
    # Get years from books
    books = db.query(Book).all()
    years.update(b.finished_date.year for b in books)
    
    # Get years from music
    music = db.query(Music).all()
    years.update(m.listened_date.year for m in music)
    
    return {"years": sorted(list(years), reverse=True)}

