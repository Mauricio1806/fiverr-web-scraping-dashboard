import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure page metadata and layout
st.set_page_config(
    page_title="E-Commerce Intelligence ETL Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# PREMIUM CUSTOM CSS
# -----------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* Reset typography to clean sans-serif */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #f8fafc;
    }
    
    /* Top main title bar styling */
    .main-title-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        color: #ffffff;
        position: relative;
        overflow: hidden;
    }
    .main-title-container::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
        border-radius: 50%;
    }
    .main-title-container h1 {
        color: #ffffff !important;
        font-size: 2.25rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main-title-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Metrics Card container */
    .metric-card-wrapper {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.25rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.02), 0 0 0 1px rgba(0,0,0,0.04);
        border-left: 5px solid #3b82f6;
        position: relative;
        overflow: hidden;
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .metric-card.card-blue { border-left-color: #3b82f6; }
    .metric-card.card-purple { border-left-color: #8b5cf6; }
    .metric-card.card-gold { border-left-color: #f59e0b; }
    .metric-card.card-emerald { border-left-color: #10b981; }

    .metric-icon {
        position: absolute;
        right: 1.25rem;
        top: 1.25rem;
        font-size: 1.75rem;
        opacity: 0.2;
    }

    .metric-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 0.5rem;
        line-height: 1;
    }

    .metric-desc {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Sidebar styling overrides */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #94a3b8 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Elegant tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre;
        background-color: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0f172a;
        background-color: #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "books.db")
CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "books_clean.csv")
RAW_CSV_PATH = os.path.join(BASE_DIR, "data", "raw", "books_raw.csv")

def get_data_from_sqlite() -> pd.DataFrame:
    """
    Fetches the cleaned data from SQLite database.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM books", conn)
        conn.close()
        return df
    except Exception as e:
        # Fallback to CSV if DB fails
        if os.path.exists(CSV_PATH):
            try:
                return pd.read_csv(CSV_PATH)
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

def run_pipeline(max_books: int, delay: float) -> bool:
    """
    Executes the scraper, transformer, and database loader sequentially.
    Displays progress steps in Streamlit.
    """
    # Import components inline to avoid circular dependencies
    from src.scraper import scrape_books
    from src.transformer import transform_data
    from src.database import load_data_to_db
    
    status_box = st.status("🏗️ ETL Pipeline Status", expanded=True)
    
    try:
        # Step 1: Scrape
        status_box.write("🕵️ Running Scraper: Extracting listings and detail specs from books.toscrape.com...")
        df_raw = scrape_books(max_books=max_books, delay_seconds=delay)
        
        if df_raw.empty:
            status_box.update(label="❌ Pipeline Execution Failed", state="error", expanded=True)
            st.error("Scraping completed but returned 0 results. Check network connectivity.")
            return False
            
        # Ensure directories exist and save raw file
        from src.utils import ensure_directories_exist
        ensure_directories_exist()
        df_raw.to_csv(RAW_CSV_PATH, index=False, encoding="utf-8")
        status_box.write(f"✓ Scraper complete: {len(df_raw)} raw books downloaded.")
        
        # Step 2: Transform
        status_box.write("⚙️ Running Transformer: Processing strings, formatting types, mapping star levels...")
        df_clean = transform_data(RAW_CSV_PATH)
        
        if df_clean.empty:
            status_box.update(label="❌ Pipeline Execution Failed", state="error", expanded=True)
            st.error("Data engineering transformation failed. Dataset is empty.")
            return False
            
        df_clean.to_csv(CSV_PATH, index=False, encoding="utf-8")
        df_clean.to_excel(CSV_PATH.replace(".csv", ".xlsx"), index=False, engine="openpyxl")
        status_box.write("✓ Transformer complete: Normalized data saved as CSV and Excel.")
        
        # Step 3: Database Load
        status_box.write("💾 Running SQLite Loader: Populating books relational database...")
        load_data_to_db(CSV_PATH, DB_PATH)
        
        status_box.update(label="🚀 Pipeline Executed Successfully!", state="complete", expanded=False)
        st.balloons()
        return True
    except Exception as e:
        status_box.update(label="❌ Pipeline Execution Failed", state="error", expanded=True)
        st.error(f"ETL pipeline crashed: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False

# =============================================================================
# SIDEBAR CONTROLS
# =============================================================================
st.sidebar.title("🛠️ ETL Control Panel")
st.sidebar.markdown("Use this panel to automate extraction or filter catalog results.")
st.sidebar.markdown("---")

st.sidebar.subheader("Automate Scraping")
max_books_input = st.sidebar.slider(
    "Max Books to Extract", 
    min_value=10, 
    max_value=200, 
    value=50, 
    step=10, 
    help="Limit book extractions to keep the demo quick and polite."
)
delay_input = st.sidebar.slider(
    "Politeness Delay (sec)", 
    min_value=0.5, 
    max_value=3.0, 
    value=1.0, 
    step=0.1,
    help="Interval spacing between page requests to avoid server blocks."
)

if st.sidebar.button("🚀 Run ETL Pipeline", use_container_width=True):
    success = run_pipeline(max_books_input, delay_input)
    if success:
        st.sidebar.success("Database updated! Reloading...")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Live Filters")

# Load data for filtering
df_data = get_data_from_sqlite()

# Apply filters only if data is loaded
if not df_data.empty:
    # Category Filter
    all_categories = sorted(df_data["category"].dropna().unique())
    selected_categories = st.sidebar.multiselect("Filter by Category", all_categories, default=[])
    
    # Rating Filter
    ratings = sorted([int(r) for r in df_data["rating"].dropna().unique()])
    selected_ratings = st.sidebar.multiselect("Filter by Rating Stars", ratings, default=[])
    
    # Price Filter with slider safety check (min must be < max)
    raw_min_price = float(df_data["price"].min())
    raw_max_price = float(df_data["price"].max())
    if raw_min_price == raw_max_price:
        raw_min_price = max(0.0, raw_min_price - 1.0)
        raw_max_price = raw_max_price + 1.0
        
    price_range = st.sidebar.slider(
        "Filter by Price (£)", 
        min_value=raw_min_price, 
        max_value=raw_max_price, 
        value=(raw_min_price, raw_max_price),
        format="£%.2f"
    )
    
    # Search Title/SKU
    search_query = st.sidebar.text_input("Search Title or SKU", "").strip()

    # Filter operations
    filtered_df = df_data.copy()
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    if selected_ratings:
        filtered_df = filtered_df[filtered_df["rating"].isin(selected_ratings)]
    filtered_df = filtered_df[(filtered_df["price"] >= price_range[0]) & (filtered_df["price"] <= price_range[1])]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False, na=False) |
            filtered_df["sku"].str.contains(search_query, case=False, na=False)
        ]
else:
    filtered_df = pd.DataFrame()

# Fiverr Badge / Portfolio Notice
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background-color: #1e293b; border: 1px solid #334155; padding: 12px; border-radius: 10px; text-align: center;">
    <div style="color: #3b82f6; font-size: 0.95rem; font-weight: 700; margin-bottom: 2px;">💼 FIVERR PORTFOLIO ITEM</div>
    <div style="font-size: 0.75rem; color: #94a3b8;">
        Demonstrating professional data engineering, pipeline logic, database integration, and UI reporting.
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# MAIN DASHBOARD AREA
# =============================================================================

# Sleek visual title header
st.markdown("""
<div class="main-title-container">
    <h1>📚 E-Commerce Scraper & Analytics Dashboard</h1>
    <div class="main-title-subtitle">
        An interactive portfolio showcase analyzing mock pricing, inventories, and categories scraped from 
        <a href="https://books.toscrape.com/" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 600; border-bottom: 1px dashed #60a5fa;">books.toscrape.com</a>.
    </div>
</div>
""", unsafe_allow_html=True)

if df_data.empty:
    st.warning("⚠️ **E-Commerce database is currently unpopulated!**")
    st.info("""
        The SQLite database `data/database/books.db` does not exist or is empty. 
        This is normal on a fresh setup.
        
        **To populate the dashboard:**
        1. Open the **ETL Control Panel** in the left sidebar.
        2. Adjust your scraper parameters.
        3. Click the **🚀 Run ETL Pipeline** button.
        4. The pipeline will automatically fetch the data, clean it, write it to SQLite, and load this dashboard!
    """)
    
    # Prompt user with an inline run option
    if st.button("⚡ Run Initial Demo Scrape (50 Books)", type="primary", use_container_width=True):
        with st.spinner("Executing initial pipeline setup..."):
            if run_pipeline(50, 1.0):
                st.rerun()

else:
    # -------------------------------------------------------------------------
    # KPI CARD METRICS DISPLAY
    # -------------------------------------------------------------------------
    total_books = len(df_data)
    avg_price = df_data["price"].mean()
    avg_rating = df_data["rating"].mean()
    in_stock_pct = (df_data["in_stock"].sum() / total_books) * 100 if total_books > 0 else 0
    
    st.markdown(f"""
    <div class="metric-card-wrapper">
        <div class="metric-card card-blue">
            <span class="metric-icon">📖</span>
            <div class="metric-title">Total Extracted</div>
            <div class="metric-value">{total_books}</div>
            <div class="metric-desc">Clean catalog records in SQLite</div>
        </div>
        <div class="metric-card card-purple">
            <span class="metric-icon">💷</span>
            <div class="metric-title">Average Price</div>
            <div class="metric-value">£{avg_price:.2f}</div>
            <div class="metric-desc">E-commerce price index</div>
        </div>
        <div class="metric-card card-gold">
            <span class="metric-icon">★</span>
            <div class="metric-title">Average rating</div>
            <div class="metric-value">★ {avg_rating:.1f}</div>
            <div class="metric-desc">Out of 5 star rating scale</div>
        </div>
        <div class="metric-card card-emerald">
            <span class="metric-icon">🛒</span>
            <div class="metric-title">In-Stock Rate</div>
            <div class="metric-value">{in_stock_pct:.1f}%</div>
            <div class="metric-desc">Total availability percentage</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB INTERFACE LAYOUT
    # -------------------------------------------------------------------------
    tab_analytics, tab_explorer, tab_insights = st.tabs([
        "📊 Market Analytics", 
        "🔍 Interactive Catalog Explorer", 
        "💡 Business Intelligence Insights"
    ])
    
    # -------------------------------------------------------------------------
    # TAB 1: MARKET ANALYTICS
    # -------------------------------------------------------------------------
    with tab_analytics:
        if not filtered_df.empty:
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown('<div class="section-header">📈 Pricing Distribution & Spreads</div>', unsafe_allow_html=True)
                fig_price = px.histogram(
                    filtered_df, 
                    x="price", 
                    nbins=12, 
                    labels={"price": "Price (£)", "count": "Book Count"},
                    color_discrete_sequence=["#3b82f6"],
                    marginal="box" # Adds a box plot on top of the distribution
                )
                fig_price.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Price (£)"),
                    yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Count"),
                    font=dict(family="Plus Jakarta Sans", size=11)
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
            with chart_col2:
                st.markdown('<div class="section-header">⭐ Customer Review Distribution</div>', unsafe_allow_html=True)
                rating_counts = filtered_df["rating"].value_counts().reset_index()
                rating_counts.columns = ["Rating", "Count"]
                rating_counts = rating_counts.sort_values(by="Rating")
                
                fig_rating = px.bar(
                    rating_counts, 
                    x="Rating", 
                    y="Count",
                    labels={"Rating": "Rating (Stars)", "Count": "Quantity of Books"},
                    color="Rating",
                    color_continuous_scale=["#f59e0b", "#d97706", "#b45309"] # Golden gradients
                )
                fig_rating.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, title="Rating (Stars)"),
                    yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Count"),
                    coloraxis_showscale=False,
                    font=dict(family="Plus Jakarta Sans", size=11)
                )
                st.plotly_chart(fig_rating, use_container_width=True)
                
            # Categories Volume
            st.markdown('<div class="section-header">🏷️ Product Volume by Category</div>', unsafe_allow_html=True)
            cat_df = filtered_df["category"].value_counts().reset_index()
            cat_df.columns = ["Category", "Count"]
            cat_df = cat_df.sort_values(by="Count", ascending=True)
            
            fig_cat = px.bar(
                cat_df,
                y="Category",
                x="Count",
                orientation="h",
                labels={"Category": "Book Category", "Count": "Number of Books"},
                color="Count",
                color_continuous_scale=px.colors.sequential.Teal
            )
            fig_cat.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Product Count"),
                yaxis=dict(title=""),
                coloraxis_showscale=False,
                font=dict(family="Plus Jakarta Sans", size=11)
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No items match the current filters. Expand selections in the sidebar control panel.")

    # -------------------------------------------------------------------------
    # TAB 2: INTERACTIVE CATALOG EXPLORER
    # -------------------------------------------------------------------------
    with tab_explorer:
        st.markdown('<div class="section-header">🔍 Filtered Catalog Table</div>', unsafe_allow_html=True)
        st.write(f"Displaying **{len(filtered_df)}** matching listings of **{len(df_data)}** total.")
        
        if not filtered_df.empty:
            st.dataframe(
                filtered_df[[
                    "sku", "title", "category", "price", "rating", 
                    "stock_quantity", "in_stock", "price_tier", "value_score"
                ]],
                column_config={
                    "sku": st.column_config.TextColumn("SKU (UPC)", width="medium"),
                    "title": st.column_config.TextColumn("Book Title", width="large"),
                    "category": st.column_config.TextColumn("Category", width="medium"),
                    "price": st.column_config.NumberColumn("Price (£)", format="£%.2f", width="small"),
                    "rating": st.column_config.NumberColumn("Rating (Stars)", width="small"),
                    "stock_quantity": st.column_config.NumberColumn("Stock", width="small"),
                    "in_stock": st.column_config.CheckboxColumn("In Stock", width="small"),
                    "price_tier": st.column_config.TextColumn("Price Tier", width="small"),
                    "value_score": st.column_config.NumberColumn("Value Index", format="%.2f", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Downloads Section
            st.markdown("<br>", unsafe_allow_html=True)
            download_col1, download_col2, _ = st.columns([1.2, 1.2, 2])
            
            # Export CSV
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            with download_col1:
                st.download_button(
                    label="📥 Export Filtered View (CSV)",
                    data=csv_data,
                    file_name=f"books_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            # Export Excel
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='E-Commerce Data')
            excel_data = buffer.getvalue()
            with download_col2:
                st.download_button(
                    label="📥 Export Filtered View (Excel)",
                    data=excel_data,
                    file_name=f"books_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.warning("No items match the current filters. Adjust sidebar sliders or multiselect options.")

    # -------------------------------------------------------------------------
    # TAB 3: BUSINESS INTELLIGENCE INSIGHTS
    # -------------------------------------------------------------------------
    with tab_insights:
        st.markdown('<div class="section-header">💡 Product Analytics & Catalog Health</div>', unsafe_allow_html=True)
        
        if not filtered_df.empty:
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                st.subheader("Price Tier Breakdown")
                # Group by price tier
                tier_counts = filtered_df["price_tier"].value_counts().reset_index()
                tier_counts.columns = ["Tier", "Count"]
                
                fig_pie = px.pie(
                    tier_counts,
                    values="Count",
                    names="Tier",
                    color_discrete_sequence=["#3b82f6", "#8b5cf6", "#10b981"],
                    hole=0.4 # Donut layout
                )
                fig_pie.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    font=dict(family="Plus Jakarta Sans", size=11)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with insight_col2:
                st.subheader("Inventory Stock vs Rating Correlation")
                # Scatter correlation
                fig_scatter = px.scatter(
                    filtered_df,
                    x="price",
                    y="value_score",
                    size="stock_quantity",
                    color="rating",
                    hover_name="title",
                    labels={"price": "Price (£)", "value_score": "Deal Value Index (Stars/£)", "rating": "Stars"},
                    color_continuous_scale=px.colors.sequential.Agsunset
                )
                fig_scatter.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Price (£)"),
                    yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Value Index"),
                    font=dict(family="Plus Jakarta Sans", size=11)
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            # Key statistics section
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📊 E-Commerce Summary Metrics")
            
            # Calculate metrics grouped by category
            summary_stats = filtered_df.groupby("category").agg(
                book_count=("sku", "count"),
                avg_price=("price", "mean"),
                avg_rating=("rating", "mean"),
                total_stock=("stock_quantity", "sum")
            ).reset_index()
            
            summary_stats.rename(columns={
                "category": "Category",
                "book_count": "Book Count",
                "avg_price": "Avg Price (£)",
                "avg_rating": "Avg Rating",
                "total_stock": "Total Stock (Units)"
            }, inplace=True)
            
            summary_stats = summary_stats.sort_values(by="Book Count", ascending=False)
            
            st.dataframe(
                summary_stats,
                column_config={
                    "Avg Price (£)": st.column_config.NumberColumn("Avg Price", format="£%.2f"),
                    "Avg Rating": st.column_config.NumberColumn("Avg Rating (Stars)", format="%.1f")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No items match the current filters.")
