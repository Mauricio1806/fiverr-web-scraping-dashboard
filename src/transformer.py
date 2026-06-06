import os
import sys
import re
import argparse
import pandas as pd
import numpy as np

# Add current directory to path to support running both directly and as module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import get_logger, ensure_directories_exist

logger = get_logger("Transformer")

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5
}

def clean_price(price_str: str) -> float:
    """
    Cleans a price string like '£51.77' or 'Â£51.77' and returns it as a float.
    """
    if pd.isna(price_str):
        return 0.0
    # Extract only digits and decimal point
    cleaned = re.sub(r"[^\d.]", "", str(price_str))
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not convert price '{price_str}' to float. Returning 0.0")
        return 0.0

def clean_rating(rating_str: str) -> int:
    """
    Converts rating text (e.g., 'Three', 'Four') to numeric value (1 to 5).
    """
    if pd.isna(rating_str):
        return 0
    cleaned = str(rating_str).strip().lower()
    return RATING_MAP.get(cleaned, 0)

def extract_quantity(availability_str: str) -> int:
    """
    Extracts the stock quantity from a string like 'In stock (22 available)'.
    If it's just 'In stock', returns 1. If it's 'Out of stock' or 'Unavailable', returns 0.
    """
    if pd.isna(availability_str):
        return 0
    text = str(availability_str).strip().lower()
    
    # Try to find digits in parentheses, e.g., "In stock (22 available)"
    match = re.search(r"\((\d+)\s+available\)", text)
    if match:
        return int(match.group(1))
        
    if "in stock" in text:
        return 1
    return 0

def transform_data(raw_csv_path: str) -> pd.DataFrame:
    """
    Loads raw scraped CSV, cleans features, deduplicates, and creates summary columns.
    """
    logger.info(f"Loading raw data from: {raw_csv_path}")
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw data file not found at: {raw_csv_path}")
        
    df = pd.read_csv(raw_csv_path)
    if df.empty:
        logger.warning("Loaded CSV is empty. Nothing to transform.")
        return df
        
    logger.info(f"Raw record count: {len(df)}")
    
    # 1. Clean prices
    df["price_numeric"] = df["price"].apply(clean_price)
    
    # 2. Clean ratings
    df["rating_numeric"] = df["rating"].apply(clean_rating)
    
    # 3. Clean availability and extract stock quantity
    # We prioritize 'detail_availability' from the detail page if present, otherwise 'availability'
    availability_col = "detail_availability" if "detail_availability" in df.columns else "availability"
    df["stock_quantity"] = df[availability_col].apply(extract_quantity)
    df["in_stock"] = df["stock_quantity"] > 0
    
    # 4. Remove duplicates based on SKU (which is unique)
    # If SKU isn't present, fall back to title + price
    if "sku" in df.columns and not df["sku"].isin(["Unknown", ""]).all():
        initial_len = len(df)
        df = df.drop_duplicates(subset=["sku"], keep="first")
        logger.info(f"Deduplicated by SKU. Removed {initial_len - len(df)} duplicate rows.")
    else:
        initial_len = len(df)
        df = df.drop_duplicates(subset=["title", "price_numeric"], keep="first")
        logger.info(f"Deduplicated by Title/Price. Removed {initial_len - len(df)} duplicate rows.")

    # 5. Create useful summary/enrichment columns
    # Price Tier: Budget, Moderate, Premium
    df["price_tier"] = pd.cut(
        df["price_numeric"],
        bins=[-0.01, 20.0, 40.0, np.inf],
        labels=["Budget", "Moderate", "Premium"]
    )
    
    # Value Score: rating_numeric / price_numeric (deal index)
    # Add a small epsilon to price to prevent division by zero
    df["value_score"] = round(df["rating_numeric"] / (df["price_numeric"] + 0.01) * 10, 2)
    
    # Clean up columns and order them nicely
    cols_to_keep = [
        "sku", "title", "category", "price_numeric", "rating_numeric", 
        "stock_quantity", "in_stock", "price_tier", "value_score", "product_url"
    ]
    # Filter only columns that actually exist in the dataframe
    final_cols = [c for c in cols_to_keep if c in df.columns]
    df_transformed = df[final_cols].copy()
    
    # Rename for professional presentation
    rename_map = {
        "price_numeric": "price",
        "rating_numeric": "rating"
    }
    df_transformed.rename(columns=rename_map, inplace=True)
    
    logger.info(f"Transformation complete. Transformed record count: {len(df_transformed)}")
    return df_transformed

def main():
    parser = argparse.ArgumentParser(description="Data Transformer for Book Scraper")
    parser.add_argument("--input", type=str, default="data/raw/books_raw.csv", help="Path to raw CSV input file")
    parser.add_argument("--out-csv", type=str, default="data/processed/books_clean.csv", help="Path to save cleaned CSV")
    parser.add_argument("--out-xlsx", type=str, default="data/processed/books_clean.xlsx", help="Path to save cleaned Excel")
    
    args = parser.parse_args()
    
    ensure_directories_exist()
    
    # Resolve absolute paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_path = os.path.join(base_dir, args.input)
    csv_path = os.path.join(base_dir, args.out_csv)
    xlsx_path = os.path.join(base_dir, args.out_xlsx)
    
    try:
        df_clean = transform_data(input_path)
        if not df_clean.empty:
            # Save to CSV
            df_clean.to_csv(csv_path, index=False, encoding="utf-8")
            logger.info(f"Saved cleaned CSV to: {csv_path}")
            
            # Save to Excel
            df_clean.to_excel(xlsx_path, index=False, engine="openpyxl")
            logger.info(f"Saved cleaned Excel to: {xlsx_path}")
        else:
            logger.error("Transformation generated empty dataset. Saving skipped.")
    except Exception as e:
        logger.error(f"Error running transformation pipeline: {e}")

if __name__ == "__main__":
    main()
