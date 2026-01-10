#!/usr/bin/env python3
"""
Migration script to add asset allocation tables
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")

Base = declarative_base()


class AssetAllocationTarget(Base):
    __tablename__ = "asset_allocation_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, unique=True, index=True)
    target_percentage = Column(Float, nullable=False)
    threshold_percentage = Column(Float, nullable=False, default=5.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TickerCategory(Base):
    __tablename__ = "ticker_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=False, index=True)
    is_auto_categorized = Column(Boolean, default=True)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def migrate():
    """Run the migration"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    
    print("Creating asset allocation tables...")
    
    # Create the new tables
    AssetAllocationTarget.__table__.create(engine, checkfirst=True)
    TickerCategory.__table__.create(engine, checkfirst=True)
    
    print("✓ Created asset_allocation_targets table")
    print("✓ Created ticker_categories table")
    
    # Add default allocation targets
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if defaults already exist
        existing = session.query(AssetAllocationTarget).first()
        
        if not existing:
            print("\nAdding default allocation targets...")
            default_targets = [
                AssetAllocationTarget(
                    category="US Stocks",
                    target_percentage=70.0,
                    threshold_percentage=5.0
                ),
                AssetAllocationTarget(
                    category="International Stocks",
                    target_percentage=25.0,
                    threshold_percentage=5.0
                ),
                AssetAllocationTarget(
                    category="Bonds",
                    target_percentage=0.0,
                    threshold_percentage=0.0
                ),
                AssetAllocationTarget(
                    category="Cash",
                    target_percentage=5.0,
                    threshold_percentage=1.0
                ),
            ]
            
            for target in default_targets:
                session.add(target)
            
            session.commit()
            print("✓ Added default allocation targets (70% US, 25% International, 0% Bonds, 5% Cash)")
        else:
            print("\nAllocation targets already exist, skipping defaults")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error adding defaults: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate()

