from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from backend.database import get_db
from backend.models import TVShow as TVShowModel, User
from backend.schemas import TVShow, TVShowCreate, TVShowUpdate
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/tv-shows", tags=["tv-shows"])


@router.get("/", response_model=List[TVShow])
def get_tv_shows(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all TV shows with optional filtering"""
    query = db.query(TVShowModel)
    if year:
        query = query.filter(TVShowModel.watched_date >= date(year, 1, 1)).filter(
            TVShowModel.watched_date <= date(year, 12, 31)
        )
    tv_shows = query.order_by(TVShowModel.watched_date.desc()).offset(skip).limit(limit).all()
    return tv_shows


@router.get("/{tv_show_id}", response_model=TVShow)
def get_tv_show(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific TV show by ID"""
    tv_show = db.query(TVShowModel).filter(TVShowModel.id == tv_show_id).first()
    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    return tv_show


@router.post("/", response_model=TVShow, status_code=status.HTTP_201_CREATED)
def create_tv_show(
    tv_show: TVShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new TV show entry"""
    db_tv_show = TVShowModel(**tv_show.dict())
    db.add(db_tv_show)
    db.commit()
    db.refresh(db_tv_show)
    return db_tv_show


@router.put("/{tv_show_id}", response_model=TVShow)
def update_tv_show(
    tv_show_id: int,
    tv_show_update: TVShowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a TV show entry"""
    db_tv_show = db.query(TVShowModel).filter(TVShowModel.id == tv_show_id).first()
    if not db_tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    
    update_data = tv_show_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tv_show, field, value)
    
    db.commit()
    db.refresh(db_tv_show)
    return db_tv_show


@router.delete("/{tv_show_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tv_show(
    tv_show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a TV show entry"""
    db_tv_show = db.query(TVShowModel).filter(TVShowModel.id == tv_show_id).first()
    if not db_tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    
    db.delete(db_tv_show)
    db.commit()
    return None

