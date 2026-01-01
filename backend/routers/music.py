from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from backend.database import get_db
from backend.models import Music as MusicModel
from backend.schemas import Music, MusicCreate, MusicUpdate

router = APIRouter(prefix="/music", tags=["music"])


@router.get("/", response_model=List[Music])
def get_music(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all music entries with optional filtering"""
    query = db.query(MusicModel)
    if year:
        query = query.filter(MusicModel.listened_date >= date(year, 1, 1)).filter(
            MusicModel.listened_date <= date(year, 12, 31)
        )
    music = query.order_by(MusicModel.listened_date.desc()).offset(skip).limit(limit).all()
    return music


@router.get("/{music_id}", response_model=Music)
def get_music_entry(
    music_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific music entry by ID"""
    music = db.query(MusicModel).filter(MusicModel.id == music_id).first()
    if not music:
        raise HTTPException(status_code=404, detail="Music entry not found")
    return music


@router.post("/", response_model=Music, status_code=status.HTTP_201_CREATED)
def create_music(
    music: MusicCreate,
    db: Session = Depends(get_db)
):
    """Create a new music entry"""
    db_music = MusicModel(**music.dict())
    db.add(db_music)
    db.commit()
    db.refresh(db_music)
    return db_music


@router.put("/{music_id}", response_model=Music)
def update_music(
    music_id: int,
    music_update: MusicUpdate,
    db: Session = Depends(get_db)
):
    """Update a music entry"""
    db_music = db.query(MusicModel).filter(MusicModel.id == music_id).first()
    if not db_music:
        raise HTTPException(status_code=404, detail="Music entry not found")
    
    update_data = music_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_music, field, value)
    
    db.commit()
    db.refresh(db_music)
    return db_music


@router.delete("/{music_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_music(
    music_id: int,
    db: Session = Depends(get_db)
):
    """Delete a music entry"""
    db_music = db.query(MusicModel).filter(MusicModel.id == music_id).first()
    if not db_music:
        raise HTTPException(status_code=404, detail="Music entry not found")
    
    db.delete(db_music)
    db.commit()
    return None

