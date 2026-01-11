from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from backend.database import get_db
from backend.models import PortfolioTransaction as PortfolioTransactionModel
from backend.schemas import (
    PortfolioTransaction, 
    PortfolioTransactionCreate, 
    PortfolioTransactionUpdate,
    PortfolioTransactionBatchCreate,
    TickerHolding,
    PortfolioSummary
)
import requests

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_current_stock_price(ticker: str) -> Optional[float]:
    """
    Get current stock price using yfinance (Yahoo Finance).
    Free, no API key required.
    """
    try:
        import yfinance as yf
        
        # Get ticker data
        stock = yf.Ticker(ticker)
        
        # Try to get current price from various sources
        # Method 1: Try fast_info (fastest)
        try:
            price = stock.fast_info.get('lastPrice')
            if price and price > 0:
                return float(price)
        except:
            pass
        
        # Method 2: Try info dictionary
        try:
            info = stock.info
            # Try current price
            if 'currentPrice' in info and info['currentPrice']:
                return float(info['currentPrice'])
            # Try regular market price
            if 'regularMarketPrice' in info and info['regularMarketPrice']:
                return float(info['regularMarketPrice'])
        except:
            pass
        
        # Method 3: Get latest from history
        try:
            hist = stock.history(period='1d')
            if not hist.empty and 'Close' in hist.columns:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        
        return None
        
    except ImportError:
        print("yfinance not installed. Install with: pip install yfinance")
        return None
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None


def get_stock_splits(ticker: str, since_date: Optional[date] = None) -> Dict[str, float]:
    """
    Get historical stock splits for a ticker.
    Returns a dictionary of {date_string: split_ratio}
    
    Split ratio interpretation:
    - 2.0 means 2-for-1 split (you get 2 shares for each 1 you had)
    - 0.5 means 1-for-2 reverse split (you get 1 share for each 2 you had)
    """
    try:
        import yfinance as yf
        import pandas as pd
        
        stock = yf.Ticker(ticker)
        
        # Get all historical splits
        splits = stock.splits
        
        if splits is None or splits.empty:
            return {}
        
        # Filter by date if provided
        if since_date:
            # Convert since_date to pandas Timestamp with timezone awareness
            since_timestamp = pd.Timestamp(since_date)
            
            # Make the comparison timezone-aware if the index is timezone-aware
            if splits.index.tz is not None:
                since_timestamp = since_timestamp.tz_localize(splits.index.tz)
            
            splits = splits[splits.index >= since_timestamp]
        
        # Convert to dictionary with date strings
        split_dict = {}
        for split_date, split_ratio in splits.items():
            # Convert to naive datetime and then to string
            if hasattr(split_date, 'tz_localize'):
                split_date = split_date.tz_localize(None)
            date_str = split_date.strftime('%Y-%m-%d')
            split_dict[date_str] = float(split_ratio)
        
        return split_dict
        
    except ImportError:
        print("yfinance not installed. Install with: pip install yfinance")
        return {}
    except Exception as e:
        print(f"Error fetching splits for {ticker}: {e}")
        return {}


def get_split_adjustment_ratio(
    transaction_date: date,
    splits: Dict[str, float]
) -> float:
    """
    Calculate the cumulative split adjustment ratio for a transaction date.
    Returns the ratio by which to multiply quantities (and divide prices).
    
    Example: If there was a 2-for-1 split after the transaction, returns 2.0
    """
    if not splits:
        return 1.0
    
    cumulative_split_ratio = 1.0
    
    # Apply all splits that happened AFTER this transaction
    for split_date_str, split_ratio in splits.items():
        try:
            split_date = datetime.strptime(split_date_str, '%Y-%m-%d').date()
            
            # If split happened after this transaction, apply it
            if split_date > transaction_date:
                cumulative_split_ratio *= split_ratio
        except:
            continue
    
    return cumulative_split_ratio


def calculate_ticker_holdings(transactions: List[PortfolioTransactionModel], apply_splits: bool = True) -> dict:
    """
    Calculate current holdings for a ticker based on all transactions.
    Optionally applies stock split adjustments.
    """
    if not transactions:
        return {
            "total_quantity": 0,
            "total_invested": 0,
            "average_cost": 0
        }
    
    # Get split data if needed
    splits = {}
    if apply_splits and transactions:
        ticker = transactions[0].ticker
        earliest_date = min(txn.transaction_date for txn in transactions)
        splits = get_stock_splits(ticker, since_date=earliest_date)
    
    total_quantity = 0.0
    total_cost = 0.0
    
    for txn in transactions:
        # Get split adjustment ratio for this transaction
        split_ratio = 1.0
        if apply_splits and splits:
            split_ratio = get_split_adjustment_ratio(txn.transaction_date, splits)
        
        # Apply split adjustments
        adjusted_quantity = txn.quantity * split_ratio
        adjusted_price = txn.price_per_unit / split_ratio if split_ratio != 1.0 else txn.price_per_unit
        # Total amount stays the same (quantity * price remains constant)
        adjusted_total = txn.total_amount
        
        if txn.transaction_type.upper() == "BUY":
            total_quantity += adjusted_quantity
            total_cost += adjusted_total + txn.fees
        elif txn.transaction_type.upper() == "SELL":
            # Calculate average cost per unit before the sale
            avg_cost_per_unit = total_cost / total_quantity if total_quantity > 0 else 0
            # Reduce quantity and proportional cost
            total_quantity -= adjusted_quantity
            total_cost -= (adjusted_quantity * avg_cost_per_unit)
    
    if total_quantity <= 0:
        return {
            "total_quantity": 0,
            "total_invested": 0,
            "average_cost": 0,
            "splits_applied": len(splits) if splits else 0
        }
    
    return {
        "total_quantity": total_quantity,
        "total_invested": total_cost,
        "average_cost": total_cost / total_quantity,
        "splits_applied": len(splits) if splits else 0
    }


def parse_schwab_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse Schwab brokerage transaction JSON format into standard format.
    
    Schwab format:
    {
        "FromDate": "MM/DD/YYYY",
        "ToDate": "MM/DD/YYYY",
        "BrokerageTransactions": [
            {
                "Date": "MM/DD/YYYY",
                "Action": "Buy" or "Sell",
                "Symbol": "TICKER",
                "Description": "...",
                "Quantity": "14",
                "Price": "$33.3799",
                "Fees & Comm": "$0.00" or "",
                "Amount": "-$467.32"
            }
        ]
    }
    """
    transactions = []
    
    if "BrokerageTransactions" not in data:
        raise ValueError("Not a valid Schwab transaction format: missing 'BrokerageTransactions' key")
    
    for txn in data["BrokerageTransactions"]:
        try:
            # Parse date from MM/DD/YYYY to YYYY-MM-DD
            date_str = txn.get("Date", "")
            if date_str:
                parsed_date = datetime.strptime(date_str, "%m/%d/%Y")
                transaction_date = parsed_date.strftime("%Y-%m-%d")
            else:
                raise ValueError("Missing date in transaction")
            
            # Parse action (Buy/Sell)
            action = txn.get("Action", "").upper()
            if action not in ["BUY", "SELL"]:
                # Try to handle variations
                if "BUY" in action:
                    action = "BUY"
                elif "SELL" in action:
                    action = "SELL"
                else:
                    raise ValueError(f"Unknown action: {txn.get('Action')}")
            
            # Get ticker
            ticker = txn.get("Symbol", "").strip().upper()
            if not ticker:
                raise ValueError("Missing ticker symbol")
            
            # Parse quantity
            quantity_str = txn.get("Quantity", "0").replace(",", "")
            quantity = float(quantity_str)
            
            # Parse price (remove $ and ,)
            price_str = txn.get("Price", "$0").replace("$", "").replace(",", "")
            price_per_unit = float(price_str)
            
            # Parse fees (remove $ and ,)
            fees_str = txn.get("Fees & Comm", "$0").replace("$", "").replace(",", "").strip()
            fees = float(fees_str) if fees_str else 0.0
            
            # Parse total amount (remove $ and ,, handle negative)
            amount_str = txn.get("Amount", "$0").replace("$", "").replace(",", "")
            total_amount = abs(float(amount_str))  # Use absolute value
            
            # Determine asset type from description
            description = txn.get("Description", "").upper()
            if "ETF" in description:
                asset_type = "ETF"
            elif "MUTUAL FUND" in description or "FUND" in description:
                asset_type = "MUTUAL_FUND"
            else:
                asset_type = "STOCK"
            
            # Build transaction
            parsed_txn = {
                "ticker": ticker,
                "transaction_type": action,
                "transaction_date": transaction_date,
                "quantity": quantity,
                "price_per_unit": price_per_unit,
                "total_amount": total_amount,
                "fees": fees,
                "notes": txn.get("Description", ""),
                "asset_type": asset_type
            }
            
            transactions.append(parsed_txn)
            
        except Exception as e:
            # Skip invalid transactions but log the error
            print(f"Error parsing transaction: {e}, Transaction: {txn}")
            continue
    
    return transactions


def parse_standard_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse standard transaction format.
    
    Standard format:
    {
        "transactions": [
            {
                "ticker": "AAPL",
                "transaction_type": "BUY",
                "transaction_date": "2024-01-15",
                "quantity": 10.0,
                "price_per_unit": 185.50,
                "total_amount": 1855.00,
                "fees": 0.0,
                "notes": "...",
                "asset_type": "STOCK"
            }
        ]
    }
    """
    if "transactions" not in data:
        raise ValueError("Not a valid standard format: missing 'transactions' key")
    
    return data["transactions"]


def detect_and_parse_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Auto-detect JSON format and parse accordingly.
    Supports:
    1. Schwab brokerage format
    2. Standard format
    """
    # Try Schwab format first
    if "BrokerageTransactions" in data:
        return parse_schwab_json(data)
    
    # Try standard format
    elif "transactions" in data:
        return parse_standard_json(data)
    
    else:
        raise ValueError(
            "Unknown JSON format. Supported formats: "
            "1) Schwab (with 'BrokerageTransactions'), "
            "2) Standard (with 'transactions')"
        )


@router.get("/transactions", response_model=List[PortfolioTransaction])
def get_transactions(
    skip: int = 0,
    limit: int = 1000,
    ticker: Optional[str] = None,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all portfolio transactions with optional filtering"""
    query = db.query(PortfolioTransactionModel)
    
    if ticker:
        query = query.filter(PortfolioTransactionModel.ticker == ticker.upper())
    
    if asset_type:
        query = query.filter(PortfolioTransactionModel.asset_type == asset_type.upper())
    
    transactions = query.order_by(
        PortfolioTransactionModel.transaction_date.desc()
    ).offset(skip).limit(limit).all()
    
    return transactions


@router.get("/transactions/{transaction_id}", response_model=PortfolioTransaction)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific transaction by ID"""
    transaction = db.query(PortfolioTransactionModel).filter(
        PortfolioTransactionModel.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.post("/transactions", response_model=PortfolioTransaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: PortfolioTransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a new portfolio transaction"""
    # Normalize ticker and transaction type to uppercase
    transaction_data = transaction.dict()
    transaction_data['ticker'] = transaction_data['ticker'].upper()
    transaction_data['transaction_type'] = transaction_data['transaction_type'].upper()
    transaction_data['asset_type'] = transaction_data['asset_type'].upper()
    
    # Validate transaction type
    if transaction_data['transaction_type'] not in ["BUY", "SELL"]:
        raise HTTPException(
            status_code=400, 
            detail="Transaction type must be 'BUY' or 'SELL'"
        )
    
    # Validate asset type
    if transaction_data['asset_type'] not in ["STOCK", "ETF", "MUTUAL_FUND"]:
        raise HTTPException(
            status_code=400,
            detail="Asset type must be 'STOCK', 'ETF', or 'MUTUAL_FUND'"
        )
    
    db_transaction = PortfolioTransactionModel(**transaction_data)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


@router.post("/transactions/batch", response_model=List[PortfolioTransaction], status_code=status.HTTP_201_CREATED)
def create_transactions_batch(
    batch: PortfolioTransactionBatchCreate,
    db: Session = Depends(get_db)
):
    """Batch upload multiple transactions from JSON (standard format)"""
    created_transactions = []
    
    for transaction in batch.transactions:
        # Normalize data
        transaction_data = transaction.dict()
        transaction_data['ticker'] = transaction_data['ticker'].upper()
        transaction_data['transaction_type'] = transaction_data['transaction_type'].upper()
        transaction_data['asset_type'] = transaction_data['asset_type'].upper()
        
        # Validate transaction type
        if transaction_data['transaction_type'] not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transaction type for {transaction_data['ticker']}: must be 'BUY' or 'SELL'"
            )
        
        # Validate asset type
        if transaction_data['asset_type'] not in ["STOCK", "ETF", "MUTUAL_FUND"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid asset type for {transaction_data['ticker']}: must be 'STOCK', 'ETF', or 'MUTUAL_FUND'"
            )
        
        db_transaction = PortfolioTransactionModel(**transaction_data)
        db.add(db_transaction)
        created_transactions.append(db_transaction)
    
    db.commit()
    
    # Refresh all created transactions
    for txn in created_transactions:
        db.refresh(txn)
    
    return created_transactions


@router.post("/transactions/upload", response_model=List[PortfolioTransaction], status_code=status.HTTP_201_CREATED)
def upload_transactions_flexible(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Flexible batch upload that auto-detects format.
    Supports:
    1. Schwab brokerage format (BrokerageTransactions)
    2. Standard format (transactions)
    """
    try:
        # Auto-detect and parse JSON format
        parsed_transactions = detect_and_parse_json(data)
        
        if not parsed_transactions:
            raise HTTPException(
                status_code=400,
                detail="No valid transactions found in the uploaded data"
            )
        
        created_transactions = []
        
        for transaction_data in parsed_transactions:
            # Normalize data
            transaction_data['ticker'] = transaction_data['ticker'].upper()
            transaction_data['transaction_type'] = transaction_data['transaction_type'].upper()
            transaction_data['asset_type'] = transaction_data['asset_type'].upper()
            
            # Convert transaction_date string to date object if it's a string
            if isinstance(transaction_data.get('transaction_date'), str):
                from datetime import datetime as dt
                transaction_data['transaction_date'] = dt.strptime(
                    transaction_data['transaction_date'], 
                    "%Y-%m-%d"
                ).date()
            
            # Validate transaction type
            if transaction_data['transaction_type'] not in ["BUY", "SELL"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transaction type for {transaction_data['ticker']}: must be 'BUY' or 'SELL'"
                )
            
            # Validate asset type
            if transaction_data['asset_type'] not in ["STOCK", "ETF", "MUTUAL_FUND"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid asset type for {transaction_data['ticker']}: must be 'STOCK', 'ETF', or 'MUTUAL_FUND'"
                )
            
            db_transaction = PortfolioTransactionModel(**transaction_data)
            db.add(db_transaction)
            created_transactions.append(db_transaction)
        
        db.commit()
        
        # Refresh all created transactions
        for txn in created_transactions:
            db.refresh(txn)
        
        return created_transactions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing transactions: {str(e)}")


@router.put("/transactions/{transaction_id}", response_model=PortfolioTransaction)
def update_transaction(
    transaction_id: int,
    transaction_update: PortfolioTransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update a portfolio transaction"""
    db_transaction = db.query(PortfolioTransactionModel).filter(
        PortfolioTransactionModel.id == transaction_id
    ).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction_update.dict(exclude_unset=True)
    
    # Normalize if present
    if 'ticker' in update_data:
        update_data['ticker'] = update_data['ticker'].upper()
    if 'transaction_type' in update_data:
        update_data['transaction_type'] = update_data['transaction_type'].upper()
        if update_data['transaction_type'] not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=400,
                detail="Transaction type must be 'BUY' or 'SELL'"
            )
    if 'asset_type' in update_data:
        update_data['asset_type'] = update_data['asset_type'].upper()
        if update_data['asset_type'] not in ["STOCK", "ETF", "MUTUAL_FUND"]:
            raise HTTPException(
                status_code=400,
                detail="Asset type must be 'STOCK', 'ETF', or 'MUTUAL_FUND'"
            )
    
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Delete a portfolio transaction"""
    db_transaction = db.query(PortfolioTransactionModel).filter(
        PortfolioTransactionModel.id == transaction_id
    ).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(db_transaction)
    db.commit()
    
    return None


@router.delete("/transactions", status_code=status.HTTP_200_OK)
def delete_all_transactions(
    db: Session = Depends(get_db)
):
    """Delete all portfolio transactions"""
    deleted_count = db.query(PortfolioTransactionModel).delete()
    db.commit()
    
    return {"message": f"Successfully deleted {deleted_count} transaction(s)", "deleted_count": deleted_count}


@router.get("/holdings", response_model=List[TickerHolding])
def get_holdings(
    db: Session = Depends(get_db)
):
    """Get current holdings for all tickers"""
    # Get all unique tickers
    tickers = db.query(PortfolioTransactionModel.ticker).distinct().all()
    tickers = [t[0] for t in tickers]
    
    holdings = []
    
    for ticker in tickers:
        # Get all transactions for this ticker
        transactions = db.query(PortfolioTransactionModel).filter(
            PortfolioTransactionModel.ticker == ticker
        ).order_by(PortfolioTransactionModel.transaction_date).all()
        
        if not transactions:
            continue
        
        # Calculate holdings
        holding_data = calculate_ticker_holdings(transactions)
        
        if holding_data['total_quantity'] <= 0:
            continue  # Skip if no current holdings
        
        # Get current price (placeholder for now)
        current_price = get_current_stock_price(ticker)
        
        holding = TickerHolding(
            ticker=ticker,
            asset_type=transactions[0].asset_type,
            total_quantity=holding_data['total_quantity'],
            average_cost=holding_data['average_cost'],
            total_invested=holding_data['total_invested'],
            current_price=current_price,
            current_value=current_price * holding_data['total_quantity'] if current_price else None,
            profit_loss=(current_price * holding_data['total_quantity'] - holding_data['total_invested']) if current_price else None,
            profit_loss_percentage=((current_price * holding_data['total_quantity'] - holding_data['total_invested']) / holding_data['total_invested'] * 100) if current_price and holding_data['total_invested'] > 0 else None
        )
        
        holdings.append(holding)
    
    return holdings


@router.get("/holdings/{ticker}", response_model=TickerHolding)
def get_ticker_holding(
    ticker: str,
    db: Session = Depends(get_db)
):
    """Get current holding information for a specific ticker"""
    ticker = ticker.upper()
    
    # Get all transactions for this ticker
    transactions = db.query(PortfolioTransactionModel).filter(
        PortfolioTransactionModel.ticker == ticker
    ).order_by(PortfolioTransactionModel.transaction_date).all()
    
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this ticker")
    
    # Calculate holdings
    holding_data = calculate_ticker_holdings(transactions)
    
    if holding_data['total_quantity'] <= 0:
        raise HTTPException(status_code=404, detail="No current holdings for this ticker")
    
    # Get current price (placeholder for now)
    current_price = get_current_stock_price(ticker)
    
    holding = TickerHolding(
        ticker=ticker,
        asset_type=transactions[0].asset_type,
        total_quantity=holding_data['total_quantity'],
        average_cost=holding_data['average_cost'],
        total_invested=holding_data['total_invested'],
        current_price=current_price,
        current_value=current_price * holding_data['total_quantity'] if current_price else None,
        profit_loss=(current_price * holding_data['total_quantity'] - holding_data['total_invested']) if current_price else None,
        profit_loss_percentage=((current_price * holding_data['total_quantity'] - holding_data['total_invested']) / holding_data['total_invested'] * 100) if current_price and holding_data['total_invested'] > 0 else None
    )
    
    return holding


@router.get("/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
    db: Session = Depends(get_db)
):
    """Get overall portfolio summary"""
    holdings = get_holdings(db)
    
    total_invested = sum(h.total_invested for h in holdings)
    current_value = sum(h.current_value for h in holdings if h.current_value is not None)
    
    # Only calculate if we have current values for all holdings
    has_all_prices = all(h.current_price is not None for h in holdings)
    
    summary = PortfolioSummary(
        total_invested=total_invested,
        current_value=current_value if has_all_prices and holdings else None,
        total_profit_loss=(current_value - total_invested) if has_all_prices and holdings else None,
        total_profit_loss_percentage=((current_value - total_invested) / total_invested * 100) if has_all_prices and holdings and total_invested > 0 else None,
        holdings=holdings
    )
    
    return summary


@router.get("/tickers", response_model=List[str])
def get_all_tickers(
    db: Session = Depends(get_db)
):
    """Get list of all unique tickers in the portfolio"""
    tickers = db.query(PortfolioTransactionModel.ticker).distinct().order_by(
        PortfolioTransactionModel.ticker
    ).all()
    
    return [t[0] for t in tickers]


@router.get("/splits/{ticker}")
def get_ticker_splits(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Get stock split history for a ticker.
    Returns splits that occurred after the earliest transaction.
    """
    ticker = ticker.upper()
    
    # Get earliest transaction date for this ticker
    earliest_txn = db.query(PortfolioTransactionModel).filter(
        PortfolioTransactionModel.ticker == ticker
    ).order_by(PortfolioTransactionModel.transaction_date).first()
    
    if not earliest_txn:
        raise HTTPException(status_code=404, detail="No transactions found for this ticker")
    
    # Get splits since earliest transaction
    splits = get_stock_splits(ticker, since_date=earliest_txn.transaction_date)
    
    return {
        "ticker": ticker,
        "earliest_transaction_date": str(earliest_txn.transaction_date),
        "splits": splits,
        "total_splits": len(splits)
    }

