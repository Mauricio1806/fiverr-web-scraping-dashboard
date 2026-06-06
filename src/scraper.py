import os
import sys
import argparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd

# Add current directory to path to support running both directly and as module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import get_logger, SafeScraperSession, ensure_directories_exist

logger = get_logger("Scraper")

BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"

def parse_book_detail(session: SafeScraperSession, detail_url: str) -> dict:
    """
    Visits the book detail page to extract category, SKU, and detailed availability.
    """
    logger.info(f"Scraping detail page: {detail_url}")
    response = session.get(detail_url)
    if not response:
        logger.warning(f"Could not load detail page for: {detail_url}")
        return {"category": "Unknown", "sku": "Unknown", "detail_availability": "Unknown"}

    soup = BeautifulSoup(response.content, "html.parser")
    
    # 1. Extract Category from breadcrumbs
    category = "Unknown"
    breadcrumb = soup.find("ul", class_="breadcrumb")
    if breadcrumb:
        lis = breadcrumb.find_all("li")
        if len(lis) >= 3:
            # The category is usually the 3rd item (Home > Books > [Category] > [Book Title])
            category = lis[2].get_text(strip=True)

    # 2. Extract SKU (UPC) and detailed availability from the product info table
    sku = "Unknown"
    detail_availability = "Unknown"
    info_table = soup.find("table", class_="table-striped")
    if info_table:
        for row in info_table.find_all("tr"):
            header = row.find("th")
            value = row.find("td")
            if header and value:
                header_text = header.get_text(strip=True).lower()
                value_text = value.get_text(strip=True)
                if "upc" in header_text:
                    sku = value_text
                elif "availability" in header_text:
                    detail_availability = value_text

    return {
        "category": category,
        "sku": sku,
        "detail_availability": detail_availability
    }

def scrape_books(max_books: int = 50, delay_seconds: float = 1.0) -> pd.DataFrame:
    """
    Main scraping function. Navigates the catalogue pages, extracts books data,
    and returns a pandas DataFrame.
    """
    logger.info(f"Starting scraper. Limit: {max_books} books. Delay: {delay_seconds}s.")
    session = SafeScraperSession(delay_seconds=delay_seconds)
    
    books_data = []
    current_url = START_URL
    books_scraped = 0
    
    while current_url and books_scraped < max_books:
        logger.info(f"Scraping list page: {current_url}")
        response = session.get(current_url)
        if not response:
            logger.error(f"Failed to fetch list page: {current_url}. Stopping scraper.")
            break
            
        soup = BeautifulSoup(response.content, "html.parser")
        product_pods = soup.find_all("article", class_="product_pod")
        
        if not product_pods:
            logger.warning(f"No products found on page: {current_url}")
            break
            
        for pod in product_pods:
            if books_scraped >= max_books:
                break
                
            try:
                # Extract Title & Product URL with defensive checks
                title_el = pod.find("h3")
                title = "Unknown Title"
                relative_product_url = ""
                if title_el:
                    title_a = title_el.find("a")
                    if title_a:
                        title = title_a.get("title") or title_a.get_text(strip=True) or "Unknown Title"
                        relative_product_url = title_a.get("href") or ""
                
                product_url = urljoin(current_url, relative_product_url) if relative_product_url else ""
                
                # Extract Price with defensive check
                price_el = pod.find("p", class_="price_color")
                price = price_el.get_text(strip=True) if price_el else "£0.00"
                
                # Extract Availability status with defensive check
                availability_el = pod.find("p", class_="instock")
                availability = availability_el.get_text(strip=True) if availability_el else "In stock"
                
                # Extract Rating with defensive check
                rating_el = pod.find("p", class_="star-rating")
                rating_classes = rating_el.get("class") if rating_el else []
                rating = "Unknown"
                for cls in rating_classes:
                    if cls != "star-rating":
                        rating = cls
                        break
                
                # Visit details page to get SKU, Category, and detailed availability
                details = {"category": "Unknown", "sku": "Unknown", "detail_availability": "Unknown"}
                if product_url:
                    details = parse_book_detail(session, product_url)
                
                book_info = {
                    "title": title,
                    "price": price,
                    "availability": availability,
                    "rating": rating,
                    "product_url": product_url,
                    "category": details.get("category", "Unknown"),
                    "sku": details.get("sku", "Unknown"),
                    "detail_availability": details.get("detail_availability", "Unknown")
                }
                
                books_data.append(book_info)
                books_scraped += 1
                logger.info(f"Successfully scraped book [{books_scraped}]: '{title}'")
                
            except Exception as e:
                logger.error(f"Error parsing product pod: {e}")
                continue
        
        # Check for next page
        next_button = soup.find("li", class_="next")
        if next_button:
            next_href = next_button.find("a").get("href")
            current_url = urljoin(current_url, next_href)
        else:
            logger.info("No next page found. Scraping completed.")
            current_url = None
            
    df = pd.DataFrame(books_data)
    return df

def main():
    parser = argparse.ArgumentParser(description="Web Scraper for books.toscrape.com")
    parser.add_argument("--max-books", type=int, default=50, help="Maximum number of books to scrape")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between requests")
    parser.add_argument("--output", type=str, default="data/raw/books_raw.csv", help="Path to save raw CSV data")
    
    args = parser.parse_args()
    
    ensure_directories_exist()
    
    # Resolve absolute path for output
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_path = os.path.join(base_dir, args.output)
    
    # Run scraper
    df = scrape_books(max_books=args.max_books, delay_seconds=args.delay)
    
    if not df.empty:
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"Successfully scraped {len(df)} books and saved raw data to {output_path}")
    else:
        logger.error("Scraper ran but did not extract any data.")

if __name__ == "__main__":
    main()
