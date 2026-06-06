import os
import time
import logging
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a configured logger.
    Logs to both console and a local file within the project directory.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Ensure log directory exists
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "pipeline.log")
        
        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
    return logger


class SafeScraperSession:
    """
    A wrapper around requests.Session to perform scraping operations safely and politely.
    Includes automated retry logic, custom User-Agents, and a rate-limiting delay between requests.
    """
    def __init__(self, delay_seconds: float = 1.0, retries: int = 3, backoff_factor: float = 0.5):
        self.logger = get_logger("SafeScraperSession")
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        
        # Set up retry policy
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Standard professional user-agent
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
        
        self.last_request_time = 0.0

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Performs a GET request with auto rate-limiting/delay and error handling.
        """
        # Apply rate limiting delay
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            self.logger.debug(f"Rate limiting active: sleeping for {sleep_time:.2f}s before accessing {url}")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
        try:
            self.logger.info(f"Fetching: {url}")
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error requesting URL {url}: {e}")
            return None


def ensure_directories_exist():
    """
    Helper function to make sure raw, processed, and database data directories exist.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dirs = [
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "data", "database"),
        os.path.join(base_dir, "assets"),
    ]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"Created directory: {d}")
