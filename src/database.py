import os
import sys
import sqlite3
import argparse
import pandas as pd

# Add current directory to path to support running both directly and as module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import get_logger, ensure_directories_exist

logger = get_logger("Database")

DEFAULT_DB_PATH = "data/database/books.db"
DEFAULT_CSV_PATH = "data/processed/books_clean.csv"

def init_database(db_path: str):
    """
    Initializes the SQLite database schema if not already initialized.
    Creates the 'books' table.
    """
    logger.info(f"Initializing database at: {db_path}")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create books table with appropriate data types and constraints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            sku TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            price REAL,
            rating INTEGER,
            stock_quantity INTEGER,
            in_stock INTEGER,
            price_tier TEXT,
            value_score REAL,
            product_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def load_data_to_db(csv_path: str, db_path: str):
    """
    Loads data from the cleaned CSV file into the SQLite database table.
    Overwrites the existing records.
    """
    logger.info(f"Loading cleaned data from {csv_path} to DB {db_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Cleaned CSV file not found: {csv_path}")
        
    df = pd.read_csv(csv_path)
    if df.empty:
        logger.warning("No records to load from CSV.")
        return
        
    init_database(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We will use transaction to insert rows or replace
    # Convert dataframe to tuples for sqlite execution
    insert_query = """
        INSERT OR REPLACE INTO books (
            sku, title, category, price, rating, stock_quantity, in_stock, price_tier, value_score, product_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    records = []
    for _, row in df.iterrows():
        # Ensure proper Python standard types for sqlite
        records.append((
            str(row.get("sku", "Unknown")),
            str(row.get("title", "")),
            str(row.get("category", "Unknown")),
            float(row.get("price", 0.0)),
            int(row.get("rating", 0)),
            int(row.get("stock_quantity", 0)),
            1 if row.get("in_stock") is True or str(row.get("in_stock")).lower() == "true" or row.get("in_stock") == 1 else 0,
            str(row.get("price_tier", "Unknown")),
            float(row.get("value_score", 0.0)),
            str(row.get("product_url", ""))
        ))
        
    try:
        cursor.executemany(insert_query, records)
        conn.commit()
        logger.info(f"Successfully loaded {len(records)} records into the 'books' table.")
        
        # Verify load
        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        logger.info(f"Verification: 'books' table now contains {count} total records.")
        
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Database error loading records: {e}")
        raise e
    finally:
        conn.close()

def query_db_summary(db_path: str):
    """
    Runs a simple analytical query to show database loading was successful and log statistics.
    """
    logger.info(f"Running database check on: {db_path}")
    if not os.path.exists(db_path):
        logger.error("Database file does not exist.")
        return
        
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("""
            SELECT 
                category, 
                COUNT(*) as book_count, 
                ROUND(AVG(price), 2) as avg_price,
                ROUND(AVG(rating), 2) as avg_rating
            FROM books
            GROUP BY category
            ORDER BY book_count DESC
            LIMIT 5
        """, conn)
        logger.info("\nTop 5 Categories in Database by Volume:\n" + df.to_string(index=False))
    except sqlite3.Error as e:
        logger.error(f"Failed to query database summary: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Database Loader for Book Scraper")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV_PATH, help="Path to cleaned CSV dataset")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Path to target SQLite DB file")
    
    args = parser.parse_args()
    
    ensure_directories_exist()
    
    # Resolve absolute paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    csv_path = os.path.join(base_dir, args.csv)
    db_path = os.path.join(base_dir, args.db)
    
    try:
        load_data_to_db(csv_path, db_path)
        query_db_summary(db_path)
    except Exception as e:
        logger.error(f"Failed to execute database pipeline step: {e}")

if __name__ == "__main__":
    main()
