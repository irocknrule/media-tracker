from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from backend.database import get_db
from backend.models import (
    AssetAllocationTarget as AssetAllocationTargetModel,
    TickerCategory as TickerCategoryModel,
    PortfolioTransaction as PortfolioTransactionModel
)
from backend.schemas import (
    AssetAllocationTarget,
    AssetAllocationTargetCreate,
    AssetAllocationTargetUpdate,
    TickerCategory,
    TickerCategoryCreate,
    TickerCategoryUpdate,
    AllocationCategorySummary,
    AssetAllocationSummary
)
from backend.routers.portfolio import calculate_ticker_holdings, get_current_stock_price

router = APIRouter(prefix="/portfolio/allocation", tags=["portfolio", "allocation"])


def auto_categorize_ticker(ticker: str) -> str:
    """
    Automatically categorize a ticker using yfinance metadata.
    Returns: "US Stocks", "International Stocks", "Bonds", or "Cash"
    """
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) < 5:
            # Not enough data, try to infer from ticker
            return infer_category_from_ticker(ticker)
        
        quote_type = info.get('quoteType', '').upper()
        long_name = info.get('longName', '').lower()
        short_name = info.get('shortName', '').lower()
        category = info.get('category', '').lower()
        country = info.get('country', '').upper()
        
        # Check if it's a money market / cash fund
        if any(keyword in long_name for keyword in ['money market', 'cash', 'treasury money']):
            return "Cash"
        if any(keyword in short_name for keyword in ['money market', 'cash']):
            return "Cash"
        
        # Check if it's a bond fund
        if any(keyword in long_name for keyword in ['bond', 'fixed income', 'treasury', 'corporate debt']):
            return "Bonds"
        if any(keyword in short_name for keyword in ['bond', 'fixed income']):
            return "Bonds"
        if 'bond' in category:
            return "Bonds"
        
        # Check if it's an international fund/stock
        # Common keywords for international funds
        international_keywords = [
            'international', 'foreign', 'ex-us', 'ex-u.s.', 'ex us',
            'global ex', 'world ex', 'eafe', 'emerging', 'developed markets',
            'europe', 'asia', 'pacific', 'latin america', 'all world ex'
        ]
        
        if any(keyword in long_name for keyword in international_keywords):
            return "International Stocks"
        if any(keyword in short_name for keyword in international_keywords):
            return "International Stocks"
        
        # Check country for individual stocks
        if quote_type == 'EQUITY' and country and country != 'UNITED STATES' and country != 'US':
            return "International Stocks"
        
        # Check if it's explicitly a US-focused fund
        us_keywords = [
            'u.s.', 'us ', 's&p', 'dow jones', 'nasdaq', 'russell',
            'total stock market', 'american', 'united states'
        ]
        
        if any(keyword in long_name for keyword in us_keywords):
            return "US Stocks"
        
        # For ETFs and mutual funds without clear indicators, check for "total" or "world"
        if quote_type in ['ETF', 'MUTUALFUND']:
            # "Total World" or "All World" usually means international + US
            # We'll classify these as US Stocks by default, but this should be reviewed
            if 'total world' in long_name or 'all world' in long_name:
                # Could be split, but defaulting to US for now
                return "US Stocks"
        
        # Default: if it's a US-listed equity and no international indicators, assume US
        if quote_type in ['EQUITY', 'ETF', 'MUTUALFUND']:
            if country == 'UNITED STATES' or country == 'US' or not country:
                return "US Stocks"
        
        # Last resort: try to infer from ticker
        return infer_category_from_ticker(ticker)
        
    except Exception as e:
        print(f"Error auto-categorizing {ticker}: {e}")
        # Fallback to ticker-based inference
        return infer_category_from_ticker(ticker)


def infer_category_from_ticker(ticker: str) -> str:
    """
    Infer category from ticker symbol patterns.
    This is a fallback when API data is unavailable.
    """
    ticker = ticker.upper()
    
    # Common international ETFs
    international_tickers = {
        'VXUS', 'IXUS', 'VEA', 'IEFA', 'VWO', 'IEMG', 'EFA', 'ACWX',
        'VYMI', 'VXUS', 'SCHF', 'SPDW', 'FNDF', 'DFAI', 'DFAE', 'AVDV'
    }
    
    # Common US ETFs
    us_tickers = {
        'VTI', 'VOO', 'SPY', 'QQQ', 'IVV', 'VUG', 'VTV', 'SCHB',
        'ITOT', 'IWM', 'VB', 'VO', 'SPTM', 'DFUS', 'AVUS', 'DFAS'
    }
    
    # Common bond ETFs
    bond_tickers = {
        'BND', 'AGG', 'BNDX', 'VGIT', 'VGLT', 'TLT', 'SHY', 'IEF',
        'LQD', 'HYG', 'VCIT', 'VCSH', 'SCHZ', 'SCHR', 'SCHO'
    }
    
    # Money market / cash
    cash_tickers = {
        'SGOV', 'TFLO', 'USFR', 'VMFXX', 'SPAXX', 'VUSXX'
    }
    
    if ticker in international_tickers:
        return "International Stocks"
    elif ticker in us_tickers:
        return "US Stocks"
    elif ticker in bond_tickers:
        return "Bonds"
    elif ticker in cash_tickers:
        return "Cash"
    else:
        # Default to US Stocks for unknown tickers
        return "US Stocks"


def get_ticker_name(ticker: str) -> Optional[str]:
    """
    Get the full name of a ticker using yfinance.
    Returns the shortName or longName if available.
    """
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) < 5:
            return None
        
        # Try to get a readable name
        name = info.get('shortName') or info.get('longName') or info.get('symbol')
        return name
    except Exception as e:
        print(f"Error fetching name for {ticker}: {e}")
        return None


def get_or_create_ticker_category(ticker: str, db: Session) -> TickerCategoryModel:
    """
    Get existing ticker category or create one with auto-categorization.
    """
    # Check if it already exists
    existing = db.query(TickerCategoryModel).filter(
        TickerCategoryModel.ticker == ticker.upper()
    ).first()
    
    if existing:
        return existing
    
    # Auto-categorize
    category = auto_categorize_ticker(ticker)
    
    # Create new entry
    new_category = TickerCategoryModel(
        ticker=ticker.upper(),
        category=category,
        is_auto_categorized=True,
        notes=f"Auto-categorized on {datetime.utcnow().strftime('%Y-%m-%d')}"
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category


# Allocation Targets Endpoints
@router.get("/targets", response_model=List[AssetAllocationTarget])
def get_allocation_targets(db: Session = Depends(get_db)):
    """Get all asset allocation targets"""
    targets = db.query(AssetAllocationTargetModel).all()
    return targets


@router.put("/targets/{category}", response_model=AssetAllocationTarget)
def update_allocation_target(
    category: str,
    target_update: AssetAllocationTargetUpdate,
    db: Session = Depends(get_db)
):
    """Update an asset allocation target"""
    target = db.query(AssetAllocationTargetModel).filter(
        AssetAllocationTargetModel.category == category
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail=f"Target for category '{category}' not found")
    
    update_data = target_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(target, field, value)
    
    target.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(target)
    
    return target


@router.post("/targets", response_model=AssetAllocationTarget, status_code=status.HTTP_201_CREATED)
def create_allocation_target(
    target_create: AssetAllocationTargetCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset allocation target"""
    # Check if category already exists
    existing = db.query(AssetAllocationTargetModel).filter(
        AssetAllocationTargetModel.category == target_create.category
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Target for category '{target_create.category}' already exists"
        )
    
    new_target = AssetAllocationTargetModel(**target_create.dict())
    db.add(new_target)
    db.commit()
    db.refresh(new_target)
    
    return new_target


# Ticker Category Endpoints
@router.get("/ticker-categories", response_model=List[TickerCategory])
def get_ticker_categories(db: Session = Depends(get_db)):
    """Get all ticker category mappings with ticker names"""
    categories = db.query(TickerCategoryModel).all()
    
    # Enhance with ticker names
    result = []
    for cat in categories:
        cat_dict = {
            "id": cat.id,
            "ticker": cat.ticker,
            "category": cat.category,
            "is_auto_categorized": cat.is_auto_categorized,
            "notes": cat.notes,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
            "ticker_name": get_ticker_name(cat.ticker)
        }
        result.append(cat_dict)
    
    return result


@router.get("/ticker-categories/{ticker}", response_model=TickerCategory)
def get_ticker_category(ticker: str, db: Session = Depends(get_db)):
    """Get or auto-create category for a specific ticker"""
    ticker = ticker.upper()
    category = get_or_create_ticker_category(ticker, db)
    return category


@router.put("/ticker-categories/{ticker}", response_model=TickerCategory)
def update_ticker_category(
    ticker: str,
    category_update: TickerCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update ticker category (manual override)"""
    ticker = ticker.upper()
    
    ticker_category = db.query(TickerCategoryModel).filter(
        TickerCategoryModel.ticker == ticker
    ).first()
    
    if not ticker_category:
        # Create it if it doesn't exist
        ticker_category = TickerCategoryModel(ticker=ticker)
        db.add(ticker_category)
    
    update_data = category_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(ticker_category, field, value)
    
    # If category was updated, mark as manual
    if 'category' in update_data:
        ticker_category.is_auto_categorized = False
    
    ticker_category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticker_category)
    
    return ticker_category


@router.post("/ticker-categories/recategorize/{ticker}", response_model=TickerCategory)
def recategorize_ticker(ticker: str, db: Session = Depends(get_db)):
    """Force re-categorization of a ticker using auto-detection"""
    ticker = ticker.upper()
    
    # Get new category
    new_category = auto_categorize_ticker(ticker)
    
    ticker_category = db.query(TickerCategoryModel).filter(
        TickerCategoryModel.ticker == ticker
    ).first()
    
    if not ticker_category:
        ticker_category = TickerCategoryModel(ticker=ticker)
        db.add(ticker_category)
    
    ticker_category.category = new_category
    ticker_category.is_auto_categorized = True
    ticker_category.notes = f"Re-categorized on {datetime.utcnow().strftime('%Y-%m-%d')}"
    ticker_category.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticker_category)
    
    return ticker_category


# Main Allocation Summary Endpoint
@router.get("/summary", response_model=AssetAllocationSummary)
def get_allocation_summary(db: Session = Depends(get_db)):
    """Get complete asset allocation summary with target vs actual comparison"""
    
    # Get all targets
    targets = db.query(AssetAllocationTargetModel).all()
    
    if not targets:
        raise HTTPException(
            status_code=404,
            detail="No allocation targets found. Please set up targets first."
        )
    
    # Get all unique tickers with holdings
    tickers = db.query(PortfolioTransactionModel.ticker).distinct().all()
    tickers = [t[0] for t in tickers]
    
    # Calculate current holdings value by category
    category_values: Dict[str, float] = {
        "US Stocks": 0.0,
        "International Stocks": 0.0,
        "Bonds": 0.0,
        "Cash": 0.0
    }
    
    total_portfolio_value = 0.0
    
    for ticker in tickers:
        # Get transactions for ticker
        transactions = db.query(PortfolioTransactionModel).filter(
            PortfolioTransactionModel.ticker == ticker
        ).order_by(PortfolioTransactionModel.transaction_date).all()
        
        if not transactions:
            continue
        
        # Calculate holdings
        holding_data = calculate_ticker_holdings(transactions)
        
        if holding_data['total_quantity'] <= 0:
            continue
        
        # Get current price
        current_price = get_current_stock_price(ticker)
        
        if current_price is None:
            continue
        
        current_value = current_price * holding_data['total_quantity']
        total_portfolio_value += current_value
        
        # Get or create ticker category
        ticker_category = get_or_create_ticker_category(ticker, db)
        
        # Add to category total
        if ticker_category.category in category_values:
            category_values[ticker_category.category] += current_value
    
    # Build summary for each category
    category_summaries = []
    
    for target in targets:
        category = target.category
        current_value = category_values.get(category, 0.0)
        
        # Calculate percentages
        actual_percentage = (current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0
        difference = actual_percentage - target.target_percentage
        needs_rebalancing = abs(difference) > target.threshold_percentage
        
        summary = AllocationCategorySummary(
            category=category,
            target_percentage=target.target_percentage,
            actual_percentage=round(actual_percentage, 2),
            difference=round(difference, 2),
            threshold=target.threshold_percentage,
            current_value=round(current_value, 2),
            needs_rebalancing=needs_rebalancing
        )
        
        category_summaries.append(summary)
    
    return AssetAllocationSummary(
        total_portfolio_value=round(total_portfolio_value, 2),
        categories=category_summaries,
        last_updated=datetime.utcnow()
    )

