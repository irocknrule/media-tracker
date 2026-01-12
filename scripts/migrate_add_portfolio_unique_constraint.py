#!/usr/bin/env python3
"""
Migration script to add unique constraint to portfolio_transactions table.
This prevents duplicate transactions at the database level.

The unique constraint ensures that transactions with identical:
- ticker
- transaction_type
- transaction_date
- quantity
- price_per_unit
- total_amount
- fees
- asset_type
cannot be inserted.
"""

import sqlite3
import os


def migrate_add_portfolio_unique_constraint():
    """Add unique constraint to portfolio_transactions table"""
    
    # Get database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./media_tracker.db")
    
    # Extract path from SQLAlchemy URL if needed
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Handle relative paths - go up one level from scripts/ to project root
    if db_path.startswith("./"):
        script_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(script_dir)
        db_path = os.path.join(project_root, db_path[2:])
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='portfolio_transactions'
        """)
        
        if not cursor.fetchone():
            print("Table 'portfolio_transactions' does not exist. Please run migrate_add_portfolio.py first.")
            conn.close()
            return
        
        # Check if unique index already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='uq_portfolio_transaction'
        """)
        
        if cursor.fetchone():
            print("Unique constraint 'uq_portfolio_transaction' already exists. Migration not needed.")
            conn.close()
            return
        
        # Check for existing duplicates before adding constraint
        print("\nChecking for existing duplicate transactions...")
        cursor.execute("""
            SELECT ticker, transaction_type, transaction_date, quantity, 
                   price_per_unit, total_amount, fees, asset_type, COUNT(*) as count
            FROM portfolio_transactions
            GROUP BY ticker, transaction_type, transaction_date, quantity, 
                     price_per_unit, total_amount, fees, asset_type
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"\n⚠️  WARNING: Found {len(duplicates)} duplicate transaction groups!")
            print("The unique constraint cannot be added until duplicates are removed.")
            print("\nDuplicate groups:")
            for dup in duplicates:
                print(f"  - {dup[0]} {dup[1]} on {dup[2]}: {dup[8]} occurrences")
            print("\nPlease remove duplicates manually or use the application's duplicate detection.")
            conn.close()
            return
        
        print("No duplicates found. Proceeding with adding unique constraint...")
        
        # Create unique index (SQLite uses unique indexes to enforce uniqueness)
        print("\nCreating unique index...")
        cursor.execute("""
            CREATE UNIQUE INDEX uq_portfolio_transaction 
            ON portfolio_transactions(
                ticker, 
                transaction_type, 
                transaction_date, 
                quantity, 
                price_per_unit, 
                total_amount, 
                fees, 
                asset_type
            )
        """)
        
        conn.commit()
        print("✓ Successfully created unique constraint 'uq_portfolio_transaction'")
        
        conn.close()
        print("\nMigration completed successfully!")
        
    except sqlite3.OperationalError as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"\n✗ Error: Cannot create unique constraint due to existing duplicates.")
            print("Please remove duplicate transactions first.")
        else:
            print(f"\n✗ Error during migration: {e}")
            import traceback
            traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


if __name__ == "__main__":
    migrate_add_portfolio_unique_constraint()
