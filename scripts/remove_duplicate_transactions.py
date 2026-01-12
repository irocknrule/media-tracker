#!/usr/bin/env python3
"""
Script to remove duplicate portfolio transactions from the database.
For each group of duplicates, keeps the transaction with the lowest ID (oldest).
"""

import sqlite3
import os
import sys


def remove_duplicate_transactions(skip_confirmation=False):
    """Remove duplicate transactions, keeping the oldest one (lowest ID) from each group"""
    
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
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='portfolio_transactions'
        """)
        
        if not cursor.fetchone():
            print("Table 'portfolio_transactions' does not exist.")
            conn.close()
            return
        
        # Find all duplicate groups
        print("\nFinding duplicate transaction groups...")
        cursor.execute("""
            SELECT ticker, transaction_type, transaction_date, quantity, 
                   price_per_unit, total_amount, fees, asset_type, COUNT(*) as count
            FROM portfolio_transactions
            GROUP BY ticker, transaction_type, transaction_date, quantity, 
                     price_per_unit, total_amount, fees, asset_type
            HAVING COUNT(*) > 1
        """)
        
        duplicate_groups = cursor.fetchall()
        
        if not duplicate_groups:
            print("No duplicate transactions found!")
            conn.close()
            return
        
        print(f"\nFound {len(duplicate_groups)} duplicate transaction groups:")
        total_duplicates_to_remove = 0
        
        for dup in duplicate_groups:
            count = dup[8]
            duplicates_in_group = count - 1  # Keep one, remove the rest
            total_duplicates_to_remove += duplicates_in_group
            print(f"  - {dup[0]} {dup[1]} on {dup[2]}: {count} occurrences (will remove {duplicates_in_group})")
        
        print(f"\nTotal duplicate transactions to remove: {total_duplicates_to_remove}")
        
        # Ask for confirmation (unless skipped)
        if not skip_confirmation:
            response = input("\nProceed with removing duplicates? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled.")
                conn.close()
                return
        else:
            print("\nProceeding automatically (--yes flag provided)...")
        
        print("\nRemoving duplicates...")
        
        # For each duplicate group, keep the one with the lowest ID and delete the rest
        removed_count = 0
        
        for dup in duplicate_groups:
            ticker, transaction_type, transaction_date, quantity, price_per_unit, total_amount, fees, asset_type, count = dup
            
            # Get all IDs for this duplicate group, ordered by ID
            cursor.execute("""
                SELECT id FROM portfolio_transactions
                WHERE ticker = ? AND transaction_type = ? AND transaction_date = ?
                  AND quantity = ? AND price_per_unit = ? AND total_amount = ?
                  AND fees = ? AND asset_type = ?
                ORDER BY id ASC
            """, (ticker, transaction_type, transaction_date, quantity, price_per_unit, total_amount, fees, asset_type))
            
            ids = [row[0] for row in cursor.fetchall()]
            
            # Keep the first one (lowest ID), delete the rest
            ids_to_delete = ids[1:]  # All except the first
            
            if ids_to_delete:
                # Delete duplicates
                placeholders = ','.join(['?'] * len(ids_to_delete))
                cursor.execute(f"""
                    DELETE FROM portfolio_transactions
                    WHERE id IN ({placeholders})
                """, ids_to_delete)
                
                removed_count += len(ids_to_delete)
                print(f"  ✓ Removed {len(ids_to_delete)} duplicate(s) for {ticker} {transaction_type} on {transaction_date}")
        
        conn.commit()
        print(f"\n✓ Successfully removed {removed_count} duplicate transaction(s)")
        print("You can now run the migration to add the unique constraint.")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


if __name__ == "__main__":
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    remove_duplicate_transactions(skip_confirmation=skip_confirmation)
