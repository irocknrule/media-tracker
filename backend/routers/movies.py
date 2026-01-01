from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from backend.database import get_db
from backend.models import Movie as MovieModel
from backend.schemas import Movie, MovieCreate, MovieUpdate

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=List[Movie])
def get_movies(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all movies with optional filtering"""
    query = db.query(MovieModel)
    if year:
        query = query.filter(MovieModel.watched_date >= date(year, 1, 1)).filter(
            MovieModel.watched_date <= date(year, 12, 31)
        )
    movies = query.order_by(MovieModel.watched_date.desc()).offset(skip).limit(limit).all()
    return movies


@router.get("/{movie_id}", response_model=Movie)
def get_movie(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific movie by ID"""
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=Movie, status_code=status.HTTP_201_CREATED)
def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db)
):
    """Create a new movie entry"""
    db_movie = MovieModel(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.put("/{movie_id}", response_model=Movie)
def update_movie(
    movie_id: int,
    movie_update: MovieUpdate,
    db: Session = Depends(get_db)
):
    """Update a movie entry"""
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    update_data = movie_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)
    
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Delete a movie entry"""
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    db.delete(db_movie)
    db.commit()
    return None

