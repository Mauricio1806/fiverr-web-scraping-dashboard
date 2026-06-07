# Fiverr Portfolio Description: E-Commerce Data Automation & Dashboard

This document represents a completed client-ready case study for web scraping, ETL automation, and business intelligence (BI) dashboard deliverables. 

---

## 📌 Project Overview
A client in the e-commerce space needed to automate competitor analysis and catalog monitoring on a public catalog platform. Doing this manually took hours every week, was prone to errors, and provided no real-time pricing intelligence. 

I developed a **complete, custom Python ETL (Extract, Transform, Load) automation pipeline** and an **interactive analytics dashboard** that reduced manual data entry to zero and provided the client with immediate pricing intelligence.

---

## 🛠️ The Deliverables
I designed and delivered a modular, production-ready system consisting of:
1. **Automated Scraping Engine:** Crawls catalog indexes dynamically, handles pagination, rotates browser User-Agents, and respects target servers using request delay settings.
2. **Detailed Extraction Pipeline:** Crawls inside product listing detail pages to fetch categories, SKUs (UPC), pricing, star ratings, and inventory stock quantities.
3. **Data Cleaning & Normalization Engine (ETL):** Normalizes encoding errors, parses price floats, maps text reviews to numeric levels, deduplicates records based on SKU keys, and calculates price tiers.
4. **Relational Database Integration:** Automates loading into SQLite databases, using upsert rules to keep datasets fresh.
5. **Spreadsheet Exports:** Auto-generates clean CSV and Microsoft Excel datasets for downstream ERP/inventory imports.
6. **BI Dashboard Console:** A Streamlit interface displaying:
   - Modern KPI cards (Total products, Average Price, In-stock volume, Average rating).
   - Dynamic charts mapping pricing density spreads, ratings distribution, and category volumes.
   - Global catalog search table with column configurations and checkbox status indicators.
   - One-click CSV and Excel exports.
   - A sidebar pipeline trigger to refresh database catalogs on-demand.

---

## 📈 Client Business Outcomes
- **100% Automation:** Saved the client hours of manual entry every week by replacing it with a single, automated click.
- **Improved Data Accuracy:** Removed data cleaning errors by implementing automated regular expression formatting.
- **Empowered Decision Making:** Provided instant insights into the client's competitor pricing distributions and product ratings.
- **Easy System Integration:** Delivered clean Excel datasets formatted for import into WooCommerce and Shopify.

---

## 🏷️ Skills Demonstrated
- **Languages:** Python (3.8+)
- **Scraping Frameworks:** BeautifulSoup4, Requests
- **Data Engineering:** Pandas, NumPy
- **Databases:** SQLite3
- **Visualization:** Streamlit, Plotly
- **Office Automation:** Openpyxl
