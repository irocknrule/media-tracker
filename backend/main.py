from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from backend.routers import auth, movies, tv_shows, books, music, analytics, search, habits, portfolio, allocation, workouts, fire, internet_usage
from backend.database import get_db, engine
from backend.models import Base
from backend.schemas import BookYearStat
import warnings
import logging

# Suppress bcrypt/passlib warnings
logging.getLogger('passlib').setLevel(logging.ERROR)
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')
warnings.filterwarnings('ignore', message='.*bcrypt.*')

app = FastAPI(
    title="Personal Media Tracker API",
    description="A secure local media tracking application API",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(tv_shows.router)
app.include_router(books.router)
app.include_router(music.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(habits.router)
app.include_router(portfolio.router)
app.include_router(allocation.router)
app.include_router(workouts.router)
app.include_router(fire.router)
app.include_router(internet_usage.router)


@app.get("/books-stats/summary", response_model=List[BookYearStat])
def books_stats_summary(db: Session = Depends(get_db)):
    """Books stats by year (unambiguous path to avoid shadowing by /books/{id})."""
    return books.get_books_stats_summary(db)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Personal Media Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

