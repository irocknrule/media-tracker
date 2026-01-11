from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import date
from backend.database import get_db
from backend.models import TVShow as TVShowModel, TVShowSeason as TVShowSeasonModel
from backend.schemas import (
    TVShow, TVShowCreate, TVShowUpdate,
    TVShowSeason, TVShowSeasonCreate, TVShowSeasonUpdate,
    TVShowLegacyCreate
)

router = APIRouter(prefix="/tv-shows", tags=["tv-shows"])


# Show-level endpoints
@router.get("/", response_model=List[TVShow])
def get_tv_shows(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all TV shows with their seasons"""
    query = db.query(TVShowModel)
    
    if year:
        # Check if it's the current year
        current_year = date.today().year
        
        if year == current_year:
            # For current year: include shows with seasons watched this year OR currently watching
            query = query.join(TVShowSeasonModel).filter(
                or_(
                    # Shows with seasons watched this year
                    (TVShowSeasonModel.watched_date >= date(year, 1, 1)) & 
                    (TVShowSeasonModel.watched_date <= date(year, 12, 31)),
                    # Shows currently being watched (regardless of watched date)
                    TVShowModel.status == "currently_watching"
                )
            ).distinct()
        else:
            # For past years: only include shows with seasons watched in that year
            query = query.join(TVShowSeasonModel).filter(
                TVShowSeasonModel.watched_date.isnot(None),
                TVShowSeasonModel.watched_date >= date(year, 1, 1),
                TVShowSeasonModel.watched_date <= date(year, 12, 31)
            ).distinct()
    
    tv_shows = query.offset(skip).limit(limit).all()
    return tv_shows


@router.get("/{show_id}", response_model=TVShow)
def get_tv_show(
    show_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific TV show by ID with all its seasons"""
    tv_show = db.query(TVShowModel).filter(TVShowModel.id == show_id).first()
    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    return tv_show


@router.post("/", response_model=TVShow, status_code=status.HTTP_201_CREATED)
def create_tv_show(
    tv_show: TVShowCreate,
    db: Session = Depends(get_db)
):
    """Create a new TV show (without seasons)"""
    db_tv_show = TVShowModel(**tv_show.dict())
    db.add(db_tv_show)
    db.commit()
    db.refresh(db_tv_show)
    return db_tv_show


@router.put("/{show_id}", response_model=TVShow)
def update_tv_show(
    show_id: int,
    tv_show_update: TVShowUpdate,
    db: Session = Depends(get_db)
):
    """Update a TV show's metadata"""
    db_tv_show = db.query(TVShowModel).filter(TVShowModel.id == show_id).first()
    if not db_tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    
    update_data = tv_show_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tv_show, field, value)
    
    db.commit()
    db.refresh(db_tv_show)
    return db_tv_show


@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tv_show(
    show_id: int,
    db: Session = Depends(get_db)
):
    """Delete a TV show and all its seasons"""
    db_tv_show = db.query(TVShowModel).filter(TVShowModel.id == show_id).first()
    if not db_tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    
    db.delete(db_tv_show)
    db.commit()
    return None


# Season-level endpoints
@router.get("/{show_id}/seasons", response_model=List[TVShowSeason])
def get_show_seasons(
    show_id: int,
    db: Session = Depends(get_db)
):
    """Get all seasons for a specific TV show"""
    # Check if show exists
    tv_show = db.query(TVShowModel).filter(TVShowModel.id == show_id).first()
    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    
    seasons = db.query(TVShowSeasonModel).filter(
        TVShowSeasonModel.show_id == show_id
    ).order_by(TVShowSeasonModel.season_number).all()
    
    return seasons


@router.get("/seasons/{season_id}", response_model=TVShowSeason)
def get_season(
    season_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific season by ID"""
    season = db.query(TVShowSeasonModel).filter(TVShowSeasonModel.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return season


@router.post("/seasons", response_model=TVShowSeason, status_code=status.HTTP_201_CREATED)
def create_season(
    season: TVShowSeasonCreate,
    db: Session = Depends(get_db)
):
    """Create a new season for a TV show"""
    # Check if show exists
    tv_show = db.query(TVShowModel).filter(TVShowModel.id == season.show_id).first()
    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")
    
    db_season = TVShowSeasonModel(**season.dict())
    db.add(db_season)
    db.commit()
    db.refresh(db_season)
    return db_season


@router.put("/seasons/{season_id}", response_model=TVShowSeason)
def update_season(
    season_id: int,
    season_update: TVShowSeasonUpdate,
    db: Session = Depends(get_db)
):
    """Update a season's metadata"""
    db_season = db.query(TVShowSeasonModel).filter(TVShowSeasonModel.id == season_id).first()
    if not db_season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    update_data = season_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_season, field, value)
    
    db.commit()
    db.refresh(db_season)
    return db_season


@router.delete("/seasons/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_season(
    season_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific season"""
    db_season = db.query(TVShowSeasonModel).filter(TVShowSeasonModel.id == season_id).first()
    if not db_season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    db.delete(db_season)
    db.commit()
    return None


# Legacy endpoint for backward compatibility
@router.post("/legacy", response_model=TVShow, status_code=status.HTTP_201_CREATED)
def create_tv_show_legacy(
    tv_show: TVShowLegacyCreate,
    db: Session = Depends(get_db)
):
    """
    Legacy endpoint: Create or update a TV show with season in one call.
    This maintains backward compatibility with the old structure.
    """
    # Check if show already exists
    existing_show = db.query(TVShowModel).filter(TVShowModel.title == tv_show.title).first()
    
    if existing_show:
        show_id = existing_show.id
        # Update thumbnail if provided
        if tv_show.thumbnail_url:
            existing_show.show_thumbnail_url = tv_show.thumbnail_url
        # Update status if provided
        if tv_show.status:
            existing_show.status = tv_show.status
        db.commit()
    else:
        # Create new show
        new_show = TVShowModel(
            title=tv_show.title,
            show_thumbnail_url=tv_show.thumbnail_url,
            status=tv_show.status or "watched"
        )
        db.add(new_show)
        db.commit()
        db.refresh(new_show)
        show_id = new_show.id
    
    # Create season
    new_season = TVShowSeasonModel(
        show_id=show_id,
        season_number=tv_show.season or 1,
        watched_date=tv_show.watched_date,
        rating=tv_show.rating,
        notes=tv_show.notes,
        season_thumbnail_url=tv_show.thumbnail_url
    )
    db.add(new_season)
    db.commit()
    
    # Return the updated show with all seasons
    db_show = db.query(TVShowModel).filter(TVShowModel.id == show_id).first()
    return db_show
