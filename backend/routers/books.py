from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, nullslast, or_
from typing import List, Optional
from datetime import date
from backend.database import get_db
from backend.models import Book as BookModel
from backend.schemas import Book, BookCreate, BookUpdate

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=List[Book])
def get_books(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all books with optional filtering"""
    query = db.query(BookModel)
    if year:
        # Check if it's the current year
        current_year = date.today().year
        
        if year == current_year:
            # For current year: include books finished this year OR currently reading
            query = query.filter(
                or_(
                    # Books finished this year
                    (BookModel.finished_date >= date(year, 1, 1)) & 
                    (BookModel.finished_date <= date(year, 12, 31)),
                    # Books currently being read (regardless of finished date)
                    BookModel.status == "currently_reading"
                )
            )
        else:
            # For past years: only include books finished in that year
            query = query.filter(BookModel.finished_date.isnot(None)).filter(
                BookModel.finished_date >= date(year, 1, 1),
                BookModel.finished_date <= date(year, 12, 31)
            )
    # Order by finished_date desc (NULLs last), then by created_at desc as fallback
    books = query.order_by(
        nullslast(desc(BookModel.finished_date)),
        desc(BookModel.created_at)
    ).offset(skip).limit(limit).all()
    return books


@router.get("/{book_id}", response_model=Book)
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific book by ID"""
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(
    book: BookCreate,
    db: Session = Depends(get_db)
):
    """Create a new book entry"""
    db_book = BookModel(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@router.put("/{book_id}", response_model=Book)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db)
):
    """Update a book entry"""
    db_book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    update_data = book_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Delete a book entry"""
    db_book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(db_book)
    db.commit()
    return None

