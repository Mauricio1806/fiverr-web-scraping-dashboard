import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set layout configurations
st.set_page_config(
    page_title="E-Commerce Product Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom typography and modern clean UI styles (Vanilla CSS)
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* Reset main layout font */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #f8fafc;
    }
    
    /* Clean layout headers */
    .dashboard-header {
        background-color: #ffffff;
        padding: 1.75rem 2rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        border: 1px solid #f1f5f9;
        margin-bottom: 2rem;
    }
    .dashboard-header h1 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        letter-spacing: -0.025em;
        margin: 0 0 0.25rem 0 !important;
    }
    .dashboard-header p {
        color: #475569 !important;
        font-size: 1.05rem;
        margin: 0 !important;
        font-weight: 400;
    }

    /* KPI Cards layout */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.25rem;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        border: 1px solid #f1f5f9;
        position: relative;
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    .kpi-icon {
        position: absolute;
        right: 1.25rem;
        top: 1.25rem;
        font-size: 1.5rem;
        color: #cbd5e1;
    }
    .kpi-indicator {
        font-size: 0.7rem;
        color: #10b981;
        font-weight: 500;
        margin-top: 0.5rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 4px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        background-color: transparent;
        border-radius: 6px;
        color: #64748b;
        font-weight: 600;
        font-size: 0.9rem;
        border: none;
        padding: 0 1rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
    }
    
    /* Styled labels */
    .chart-container-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
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
    Loads catalog data from SQLite database with a fallback to the CSV file.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM books", conn)
        conn.close()
        return df
    except Exception:
        if os.path.exists(CSV_PATH):
            try:
                return pd.read_csv(CSV_PATH)
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

def run_pipeline(max_books: int, delay: float) -> bool:
    """
    Executes the backend pipeline: Scrape, Clean/Transform, Load to SQLite.
    """
    from src.scraper import scrape_books
    from src.transformer import transform_data
    from src.database import load_data_to_db
    
    status_box = st.status("🔄 Refreshing Data Source", expanded=True)
    
    try:
        status_box.write("🛰️ Requesting catalog pages from books.toscrape.com...")
        df_raw = scrape_books(max_books=max_books, delay_seconds=delay)
        
        if df_raw.empty:
            status_box.update(label="❌ Refresh Failed", state="error")
            return False
            
        from src.utils import ensure_directories_exist
        ensure_directories_exist()
        df_raw.to_csv(RAW_CSV_PATH, index=False, encoding="utf-8")
        
        status_box.write("⚙️ Standardizing data fields and applying schemas...")
        df_clean = transform_data(RAW_CSV_PATH)
        
        if df_clean.empty:
            status_box.update(label="❌ Refresh Failed", state="error")
            return False
            
        df_clean.to_csv(CSV_PATH, index=False, encoding="utf-8")
        df_clean.to_excel(CSV_PATH.replace(".csv", ".xlsx"), index=False, engine="openpyxl")
        
        status_box.write("💾 Writing data to SQLite relational storage...")
        load_data_to_db(CSV_PATH, DB_PATH)
        
        status_box.update(label="✓ Data Source Refreshed Successfully", state="complete", expanded=False)
        return True
    except Exception as e:
        status_box.update(label="❌ Refresh Failed", state="error")
        st.error(f"Error running pipeline: {e}")
        return False

# =============================================================================
# SIDEBAR FILTERS & CONTROLS
# =============================================================================
st.sidebar.markdown("""
<div style="padding: 10px 0;">
    <h3 style="margin: 0; color: #ffffff;">📊 Catalog Controls</h3>
</div>
""", unsafe_allow_html=True)

df_data = get_data_from_sqlite()

# Apply filters if data is available
if not df_data.empty:
    # Availability Filter
    availability_options = ["All", "In Stock", "Out of Stock"]
    selected_availability = st.sidebar.selectbox("Availability", availability_options, index=0)
    
    # Rating Filter
    available_ratings = sorted([int(r) for r in df_data["rating"].dropna().unique()])
    selected_ratings = st.sidebar.multiselect("Ratings (Stars)", available_ratings, default=available_ratings)
    
    # Price Slider safety boundaries
    min_price_val = float(df_data["price"].min())
    max_price_val = float(df_data["price"].max())
    if min_price_val == max_price_val:
        min_price_val = max(0.0, min_price_val - 5.0)
        max_price_val += 5.0
        
    price_range = st.sidebar.slider(
        "Price Range (£)",
        min_value=min_price_val,
        max_value=max_price_val,
        value=(min_price_val, max_price_val),
        format="£%.2f"
    )
    
    # Search Query
    search_query = st.sidebar.text_input("Search Title / SKU", "").strip()
    
    # Filter operations
    filtered_df = df_data.copy()
    
    # Apply Availability filter
    if selected_availability == "In Stock":
        filtered_df = filtered_df[filtered_df["in_stock"] == 1]
    elif selected_availability == "Out of Stock":
        filtered_df = filtered_df[filtered_df["in_stock"] == 0]
        
    # Apply Rating filter
    if selected_ratings:
        filtered_df = filtered_df[filtered_df["rating"].isin(selected_ratings)]
    else:
        filtered_df = pd.DataFrame()
        
    # Apply Price filter
    if not filtered_df.empty:
        filtered_df = filtered_df[(filtered_df["price"] >= price_range[0]) & (filtered_df["price"] <= price_range[1])]
        
    # Apply Search query
    if not filtered_df.empty and search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False, na=False) |
            filtered_df["sku"].str.contains(search_query, case=False, na=False)
        ]
else:
    filtered_df = pd.DataFrame()

# Pipeline execution panel
st.sidebar.markdown("---")
st.sidebar.subheader("Automation Panel")
max_books_slider = st.sidebar.slider("Extraction Limit", min_value=10, max_value=200, value=50, step=10)
delay_slider = st.sidebar.slider("Request Spacing (s)", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

if st.sidebar.button("🔄 Trigger Data Refresh", use_container_width=True):
    if run_pipeline(max_books_slider, delay_slider):
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 0.75rem; color: #64748b; text-align: center; line-height: 1.4;">
    <strong>Completed Client Case Study</strong><br>
    Built with Python, SQLite, & Streamlit.
</div>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER SECTION
# =============================================================================
st.markdown("""
<div class="dashboard-header">
    <h1>E-Commerce Web Scraping & Analytics Dashboard</h1>
    <p>A completed data engineering and business intelligence solution analyzing structured catalog data.</p>
</div>
""", unsafe_allow_html=True)

if df_data.empty:
    st.warning("⚠️ Relational SQLite database is currently unpopulated.")
    st.info("To initialize the pipeline and load client data, use the sidebar 'Automation Panel' to run a scrape.")
    if st.button("Initialize Pipeline & Fetch Demo Data (50 Products)", type="primary"):
        with st.spinner("Executing pipeline..."):
            if run_pipeline(50, 1.0):
                st.rerun()
else:
    # -------------------------------------------------------------------------
    # KPI METRICS
    # -------------------------------------------------------------------------
    total_products = len(df_data)
    avg_price = df_data["price"].mean()
    products_in_stock = int(df_data["in_stock"].sum())
    avg_rating = df_data["rating"].mean()
    
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <span class="kpi-icon">📦</span>
            <div class="kpi-title">Total Products</div>
            <div class="kpi-value">{total_products}</div>
            <div class="kpi-indicator">✓ Active Listings</div>
        </div>
        <div class="kpi-card">
            <span class="kpi-icon">💷</span>
            <div class="kpi-title">Average Price</div>
            <div class="kpi-value">£{avg_price:.2f}</div>
            <div class="kpi-indicator">Market Weighted</div>
        </div>
        <div class="kpi-card">
            <span class="kpi-icon">🟢</span>
            <div class="kpi-title">Products In Stock</div>
            <div class="kpi-value">{products_in_stock}</div>
            <div class="kpi-indicator">Available Inventory</div>
        </div>
        <div class="kpi-card">
            <span class="kpi-icon">★</span>
            <div class="kpi-title">Average Rating</div>
            <div class="kpi-value">★ {avg_rating:.1f}</div>
            <div class="kpi-indicator">Customer Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TABS STRUCTURE
    # -------------------------------------------------------------------------
    tab_overview, tab_pricing, tab_ratings, tab_explorer = st.tabs([
        "📊 Overview Insights",
        "💷 Pricing Analytics",
        "⭐ Rating Distributions",
        "🔍 Data Explorer"
    ])
    
    # -------------------------------------------------------------------------
    # TAB 1: OVERVIEW INSIGHTS
    # -------------------------------------------------------------------------
    with tab_overview:
        if not filtered_df.empty:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown('<div class="chart-container-title">Inventory Status Distribution</div>', unsafe_allow_html=True)
                # Group by stock status
                stock_status = filtered_df["in_stock"].map({1: "In Stock", 0: "Out of Stock"}).value_counts().reset_index()
                stock_status.columns = ["Status", "Count"]
                
                fig_stock = px.pie(
                    stock_status,
                    values="Count",
                    names="Status",
                    color="Status",
                    color_discrete_map={"In Stock": "#10b981", "Out of Stock": "#ef4444"},
                    hole=0.45
                )
                fig_stock.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_stock, use_container_width=True)
                
            with col_chart2:
                st.markdown('<div class="chart-container-title">Top 10 Most Expensive Products</div>', unsafe_allow_html=True)
                expensive_products = filtered_df.sort_values(by="price", ascending=False).head(10)
                
                fig_exp = px.bar(
                    expensive_products,
                    y="title",
                    x="price",
                    orientation="h",
                    labels={"title": "Product Title", "price": "Price (£)"},
                    color="price",
                    color_continuous_scale=px.colors.sequential.Teal
                )
                fig_exp.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    yaxis=dict(autorange="reversed", title=""),
                    xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Price (£)"),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_exp, use_container_width=True)
                
            # Product Volume by Category Chart
            st.markdown('<div class="chart-container-title">Catalog Volume by Category</div>', unsafe_allow_html=True)
            cat_counts = filtered_df["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            cat_counts = cat_counts.sort_values(by="Count", ascending=True)
            
            fig_cat = px.bar(
                cat_counts,
                y="Category",
                x="Count",
                orientation="h",
                color="Count",
                color_continuous_scale=px.colors.sequential.Blues
            )
            fig_cat.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Products Count"),
                yaxis=dict(title=""),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        else:
            st.info("No items match the current filters. Update criteria in the sidebar.")

    # -------------------------------------------------------------------------
    # TAB 2: PRICING ANALYTICS
    # -------------------------------------------------------------------------
    with tab_pricing:
        if not filtered_df.empty:
            st.markdown('<div class="chart-container-title">Pricing Spreads & Density Distribution</div>', unsafe_allow_html=True)
            fig_density = px.histogram(
                filtered_df,
                x="price",
                nbins=12,
                labels={"price": "Price (£)", "count": "Products Count"},
                color_discrete_sequence=["#3b82f6"],
                marginal="box"
            )
            fig_density.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Price (£)"),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Frequency Density")
            )
            st.plotly_chart(fig_density, use_container_width=True)
            
            # Value Index Analysis Scatter
            st.markdown('<div class="chart-container-title">Product Rating vs Price Value Scatter</div>', unsafe_allow_html=True)
            fig_val = px.scatter(
                filtered_df,
                x="price",
                y="value_score",
                size="stock_quantity",
                color="rating",
                hover_name="title",
                labels={"price": "Price (£)", "value_score": "Value Score (Stars/£)"},
                color_continuous_scale=px.colors.sequential.Plasma
            )
            fig_val.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Price (£)"),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Value Index")
            )
            st.plotly_chart(fig_val, use_container_width=True)
        else:
            st.info("No items match the current filters.")

    # -------------------------------------------------------------------------
    # TAB 3: RATINGS DISTRIBUTIONS
    # -------------------------------------------------------------------------
    with tab_ratings:
        if not filtered_df.empty:
            st.markdown('<div class="chart-container-title">Customer Ratings Count</div>', unsafe_allow_html=True)
            counts_ratings = filtered_df["rating"].value_counts().reset_index()
            counts_ratings.columns = ["Rating", "Count"]
            counts_ratings = counts_ratings.sort_values(by="Rating")
            
            fig_ratings_bar = px.bar(
                counts_ratings,
                x="Rating",
                y="Count",
                labels={"Rating": "Stars", "Count": "Products Count"},
                color="Rating",
                color_continuous_scale=px.colors.sequential.YlOrRd
            )
            fig_ratings_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False, title="Ratings (Stars)"),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Total Products"),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_ratings_bar, use_container_width=True)
        else:
            st.info("No items match the current filters.")

    # -------------------------------------------------------------------------
    # TAB 4: DATA EXPLORER
    # -------------------------------------------------------------------------
    with tab_explorer:
        st.markdown('<div class="chart-container-title">Cleaned Catalog Data Table</div>', unsafe_allow_html=True)
        st.write(f"Displaying **{len(filtered_df)}** filtered records.")
        
        if not filtered_df.empty:
            st.dataframe(
                filtered_df[[
                    "sku", "title", "category", "price", "rating", 
                    "stock_quantity", "in_stock", "price_tier", "value_score"
                ]],
                column_config={
                    "sku": st.column_config.TextColumn("SKU (UPC)", width="medium"),
                    "title": st.column_config.TextColumn("Product Title", width="large"),
                    "category": st.column_config.TextColumn("Category", width="medium"),
                    "price": st.column_config.NumberColumn("Price (£)", format="£%.2f", width="small"),
                    "rating": st.column_config.NumberColumn("Rating (Stars)", width="small"),
                    "stock_quantity": st.column_config.NumberColumn("Stock", width="small"),
                    "in_stock": st.column_config.CheckboxColumn("Available", width="small"),
                    "price_tier": st.column_config.TextColumn("Price Tier", width="small"),
                    "value_score": st.column_config.NumberColumn("Value Index", format="%.2f", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Downloads options
            download_col1, download_col2, _ = st.columns([1.2, 1.2, 2])
            
            # Export CSV
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            with download_col1:
                st.download_button(
                    label="📥 Download Dataset (CSV)",
                    data=csv_data,
                    file_name=f"ecommerce_catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
                    label="📥 Download Dataset (Excel)",
                    data=excel_data,
                    file_name=f"ecommerce_catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.warning("No records match the active criteria.")
