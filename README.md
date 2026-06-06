# Automated E-Commerce ETL Pipeline & Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458.svg?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)

This repository showcases an end-to-end data engineering and business intelligence (BI) solution. It automates the extraction, cleaning, structured storage, and visualization of catalog data from a public e-commerce bookstore demonstration site ([books.toscrape.com](https://books.toscrape.com/)).

The project is structured modularly following software engineering best practices, dividing responsibilities into **Extract** (Scraper), **Transform** (Data Engineering), **Load** (SQLite Database), and **Visualize** (Streamlit Dashboard).

---

## 💼 Business Value & Core Benefits

In retail and e-commerce, tracking catalog offerings and pricing is vital. Doing this manually is time-consuming, expensive, and prone to errors. This project automates the entire process:

- **Saving Time:** What once required hours of manual browsing and copy-pasting is completed in seconds by a single automation pipeline.
- **Reducing Manual Work:** Eliminates human labor in data entry, allowing team members to focus on pricing strategy and market analysis rather than data gathering.
- **Standardized Quality:** Automated filters clean messy HTML text, standardizing numerical types and mapping rating scales into clean structured schemas.
- **Actionable Visual Reporting:** Consolidates databases into a single, intuitive interface, providing stakeholders with real-time stats and immediate file downloads.

---

## ⚙️ Core Pipeline Capabilities

### 1. Web Scraping & Data Extraction
- **Polite Crawling:** Implements rate-limiting delays and requests retry logic to respect target servers and prevent IP blocks.
- **Detail-Level Extraction:** Extracts catalog grids and follows detail links to gather product-level specifications (category breadcrumbs, SKU/UPC, and stock quantities).
- **Fail-Safe Parsing:** Features defensive element lookups to ensure the scraper defaults gracefully if layouts change or fields go missing.

### 2. Data Cleaning & Engineering
- **Price Parsing:** Automatically strips currency characters, normalizes encoding issues, and converts numbers to floats.
- **Rating Mapping:** Translates words (e.g., "Three") into numeric integers (e.g., 3).
- **Deduplication:** Uses e-commerce SKUs to ensure duplicate items are removed.
- **Summary Metrics:** Calculates a *Deal Value Index* (Rating/Price) and segregates listings into budget, moderate, and premium price tiers.

### 3. SQLite Relational Database
- **Relational Schema:** Loads clean data into an SQLite table defined with appropriate column constraints and data types.
- **Database Loader:** Uses SQL transactions (`INSERT OR REPLACE` rules) to keep records fresh on rerun.

### 4. Interactive BI Dashboard
- **Executive Metrics:** Metric cards showing catalog volumes, price averages, average ratings, and in-stock counts.
- **Visual Analytics:** Interactive Plotly charts mapping price spreads, star ratings, and top-volume categories.
- **Custom Filters:** Multi-layer filtering based on search keywords, categories, ratings, and price boundaries.

### 5. Multi-Format Data Export
- **CSV & Excel:** Allows downloading filtered tables in Excel (`.xlsx`) and CSV formats for immediate use in other corporate tools.

---

## 💼 Freelance & Client Use Cases

This project demonstrates a production-ready framework that can be adapted for diverse freelance business needs:

### Competitor Price Monitoring
- **Adaptation:** Schedule the pipeline to run daily or weekly. Monitor changes in competitor pricing over time and flag discounts.

### Catalog & Inventory Extraction
- **Adaptation:** Extract products from supplier websites and format them into platform-specific imports (e.g., Shopify, WooCommerce, or Amazon bulk import templates).

### Business Directory Scraping
- **Adaptation:** Crawl public directory sites (e.g., real estate indexes, local directories) to extract company names, phone numbers, addresses, and email lists for sales outreach.

### Reporting Automation
- **Adaptation:** Replace manually updated tracking spreadsheets with an automated script that extracts data from APIs or internal tools, loads it into SQL, and updates a shared dashboard.

---

## 📁 Project Structure

```text
fiverr-web-scraping-dashboard/
│
├── app.py                       # Streamlit BI application & interactive pipeline controller
├── requirements.txt             # Project library dependencies
├── .gitignore                   # Excludes virtual environments and data folders from Git
├── README.md                    # Project documentation
│
├── data/
│   ├── raw/                     # Raw CSV extracts direct from scraper
│   ├── processed/               # Cleaned CSV & Excel catalog exports
│   └── database/                # SQLite relational database storage (books.db)
│
├── src/
│   ├── __init__.py              # Python package marker
│   ├── scraper.py               # Extraction engine (requests / BeautifulSoup)
│   ├── transformer.py           # Clean & normalization engine (pandas)
│   ├── database.py              # Schema definition & SQL loading engine (sqlite3)
│   └── utils.py                 # Logging setups & rate-limiting connection adapter
│
└── assets/
    └── portfolio_description.md # Prepared copy-paste text for portfolio/gig usage
```

---

## 🚀 Installation & Setup

Ensure Python 3.8+ is installed on your system.

### 1. Set Up Virtual Environment
Using a virtual environment keeps project dependencies isolated and prevents system-level package conflicts.

**On Windows (Command Prompt or PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Pipeline

You can run pipeline stages via command line interfaces, or execute the entire process directly from the Web UI!

### Option A: Command Line Interface (CLI)

Run scripts sequentially from the root directory to populate raw files, clean data, and load the database:

1. **Run Scraper:**
   ```bash
   python src/scraper.py --max-books 50 --delay 1.0
   ```
   *Downloads book listings and details, saving them to `data/raw/books_raw.csv`.*

2. **Run Transformer:**
   ```bash
   python src/transformer.py
   ```
   *Cleans and writes outputs to `data/processed/books_clean.csv` and `data/processed/books_clean.xlsx`.*

3. **Run Database Loader:**
   ```bash
   python src/database.py
   ```
   *Populates the SQLite database file at `data/database/books.db`.*

---

### Option B: Web UI Execution (Interactive)

1. Start the Streamlit server (see below).
2. Use the **ETL Control Panel** sidebar.
3. Configure the extraction count and click **🚀 Run ETL Pipeline**.
4. The application will fetch data, run data transformations, load SQLite, and refresh the dashboard in real-time.

---

## 📊 Launching the Dashboard

Run the development server:
```bash
streamlit run app.py
```
Your default browser will open to:
`http://localhost:8501`
