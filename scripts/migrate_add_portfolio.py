#!/usr/bin/env python3
"""
Migration script to add portfolio_transactions table to the database.
This script adds support for tracking stock, ETF, and mutual fund transactions.
"""

import sqlite3
import os


def migrate_add_portfolio():
    """Add portfolio_transactions table to the database"""
    
    # Get database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")
    
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Handle relative paths
    if db_path.startswith("./"):
        db_path = os.path.join(os.path.dirname(__file__), db_path[2:])
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='portfolio_transactions'
        """)
        
        if cursor.fetchone():
            print("Table 'portfolio_transactions' already exists. Migration not needed.")
            conn.close()
            return
        
        print("Creating portfolio_transactions table...")
        
        # Create the portfolio_transactions table
        cursor.execute("""
            CREATE TABLE portfolio_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR NOT NULL,
                transaction_type VARCHAR NOT NULL,
                transaction_date DATE NOT NULL,
                quantity REAL NOT NULL,
                price_per_unit REAL NOT NULL,
                total_amount REAL NOT NULL,
                fees REAL DEFAULT 0.0,
                notes VARCHAR,
                asset_type VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Creating indexes...")
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX idx_portfolio_ticker ON portfolio_transactions(ticker)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_portfolio_transaction_date ON portfolio_transactions(transaction_date)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_portfolio_ticker_date ON portfolio_transactions(ticker, transaction_date)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_portfolio_asset_type ON portfolio_transactions(asset_type)
        """)
        
        print("Successfully created portfolio_transactions table with indexes")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during portfolio migration: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


if __name__ == "__main__":
    migrate_add_portfolio()

