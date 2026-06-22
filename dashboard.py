import streamlit as st
import pandas as pd
import psycopg2
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="E-Commerce Sales Data Warehouse Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

# Load database configuration
@st.cache_resource
def load_db_config():
    with open("config/db_config.json", "r") as f:
        return json.load(f)

DB_CONFIG = load_db_config()

# Helper function to query the database
def run_query(query, params=None):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return pd.DataFrame()

# Title and Description
st.title("🛍️ E-Commerce Sales Data Warehouse Dashboard")
st.markdown("An interactive overview of sales performance, category trends, and customer spending habits.")

st.markdown("---")

# 1. Fetch Basic Data for Filtering
@st.cache_data(ttl=60)
def get_categories():
    return run_query("SELECT category_name FROM category_dimension;")["category_name"].tolist()

@st.cache_data(ttl=60)
def get_date_bounds():
    df = run_query("SELECT MIN(cart_date) as min_date, MAX(cart_date) as max_date FROM cart_dimension;")
    if not df.empty and df["min_date"].iloc[0] is not None:
        return pd.to_datetime(df["min_date"].iloc[0]), pd.to_datetime(df["max_date"].iloc[0])
    return datetime(2020, 1, 1), datetime.now()

categories_list = get_categories()
min_date, max_date = get_date_bounds()

# Sidebar Filters
st.sidebar.header("📊 Filter Operations")

selected_categories = st.sidebar.multiselect(
    "Select Product Categories",
    options=categories_list,
    default=categories_list
)

start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date()
)

top_n_products = st.sidebar.slider("Number of Top Products to show", min_value=5, max_value=20, value=5)

# Convert dates to string for query
start_date_str = start_date.strftime("%Y-%m-%d") + " 00:00:00"
end_date_str = end_date.strftime("%Y-%m-%d") + " 23:59:59"

# Base SQL Filters
category_filter = "AND c.category_name IN %s" if selected_categories else "AND FALSE"
category_params = (tuple(selected_categories),) if selected_categories else ((),)

# 2. Key Performance Indicators (KPIs)
kpi_query = f"""
    SELECT 
        SUM(f.product_total_price) as total_revenue,
        COUNT(DISTINCT f.cart_id) as total_orders,
        COUNT(DISTINCT f.user_id) as total_customers,
        AVG(f.product_total_price) as avg_item_price
    FROM sales_fact_table f
    JOIN category_dimension c ON f.category_id = c.category_id
    JOIN cart_dimension cd ON f.cart_id = cd.cart_id
    WHERE cd.cart_date BETWEEN %s AND %s
    {category_filter}
"""

kpi_params = (start_date_str, end_date_str, tuple(selected_categories)) if selected_categories else (start_date_str, end_date_str)
kpi_df = run_query(kpi_query, kpi_params)

# Display Metrics
col1, col2, col3, col4 = st.columns(4)

if not kpi_df.empty:
    total_rev = kpi_df["total_revenue"].iloc[0] or 0.0
    total_ord = kpi_df["total_orders"].iloc[0] or 0
    total_cust = kpi_df["total_customers"].iloc[0] or 0
    avg_price = kpi_df["avg_item_price"].iloc[0] or 0.0
    
    # Calculate AOV (Average Order Value)
    aov = total_rev / total_ord if total_ord > 0 else 0.0

    col1.metric("💰 Total Revenue", f"${total_rev:,.2f}")
    col2.metric("📦 Total Orders", f"{total_ord:,}")
    col3.metric("👥 Total Customers", f"{total_cust:,}")
    col4.metric("📈 Average Order Value (AOV)", f"${aov:,.2f}")
else:
    col1.metric("💰 Total Revenue", "$0.00")
    col2.metric("📦 Total Orders", "0")
    col3.metric("👥 Total Customers", "0")
    col4.metric("📈 Average Order Value (AOV)", "$0.00")

st.markdown("---")

# 3. Main Visualization Area
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🛍️ Top Products by Revenue")
    top_products_query = f"""
        SELECT 
            p.product_name,
            c.category_name,
            SUM(f.product_total_price) as revenue
        FROM sales_fact_table f
        JOIN product_dimension p ON f.product_id = p.product_id
        JOIN category_dimension c ON f.category_id = c.category_id
        JOIN cart_dimension cd ON f.cart_id = cd.cart_id
        WHERE cd.cart_date BETWEEN %s AND %s
        {category_filter}
        GROUP BY p.product_name, c.category_name
        ORDER BY revenue DESC
        LIMIT %s
    """
    prod_params = (start_date_str, end_date_str, tuple(selected_categories), top_n_products) if selected_categories else (start_date_str, end_date_str, top_n_products)
    products_df = run_query(top_products_query, prod_params)
    
    if not products_df.empty:
        # Wrap product names for better formatting on axis
        products_df["short_name"] = products_df["product_name"].apply(lambda x: x[:30] + "..." if len(x) > 30 else x)
        fig_prod = px.bar(
            products_df,
            x="revenue",
            y="short_name",
            color="category_name",
            orientation="h",
            title=f"Top {top_n_products} Products Contribution",
            labels={"revenue": "Revenue ($)", "short_name": "Product"},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_prod.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_dark")
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("No product sales data matches the filters.")

with col_right:
    st.subheader("📊 Revenue by Product Category")
    category_revenue_query = f"""
        SELECT 
            c.category_name,
            SUM(f.product_total_price) as revenue
        FROM sales_fact_table f
        JOIN category_dimension c ON f.category_id = c.category_id
        JOIN cart_dimension cd ON f.cart_id = cd.cart_id
        WHERE cd.cart_date BETWEEN %s AND %s
        {category_filter}
        GROUP BY c.category_name
        ORDER BY revenue DESC
    """
    cat_df = run_query(category_revenue_query, kpi_params)
    
    if not cat_df.empty:
        fig_cat = px.pie(
            cat_df,
            values="revenue",
            names="category_name",
            title="Revenue Distribution by Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_cat.update_layout(template="plotly_dark")
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("No category sales data matches the filters.")

st.markdown("---")

# 4. Timeline / Sales Trends and Top Customers
col_trend, col_cust = st.columns([2, 1])

with col_trend:
    st.subheader("📈 Sales Trend Over Time")
    trend_query = f"""
        SELECT 
            DATE(cd.cart_date) as date,
            SUM(f.product_total_price) as daily_revenue,
            COUNT(DISTINCT f.cart_id) as daily_orders
        FROM sales_fact_table f
        JOIN category_dimension c ON f.category_id = c.category_id
        JOIN cart_dimension cd ON f.cart_id = cd.cart_id
        WHERE cd.cart_date BETWEEN %s AND %s
        {category_filter}
        GROUP BY DATE(cd.cart_date)
        ORDER BY date
    """
    trend_df = run_query(trend_query, kpi_params)
    
    if not trend_df.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["daily_revenue"],
            mode='lines+markers',
            name='Daily Revenue ($)',
            line=dict(color='#3b82f6', width=3)
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["daily_orders"],
            mode='lines+markers',
            name='Daily Orders',
            yaxis='y2',
            line=dict(color='#10b981', width=3, dash='dash')
        ))
        
        # Dual axis setup
        fig_trend.update_layout(
            title="Daily Sales Revenue and Order Volumes",
            xaxis_title="Date",
            yaxis=dict(title="Revenue ($)", title_font_color="#3b82f6", tickfont=dict(color="#3b82f6")),
            yaxis2=dict(title="Orders count", title_font_color="#10b981", tickfont=dict(color="#10b981"), anchor="x", overlaying="y", side="right"),
            template="plotly_dark",
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No trend data matches the filters.")

with col_cust:
    st.subheader("💎 Top Spending Customers")
    customers_query = f"""
        SELECT 
            CONCAT(u.first_name, ' ', u.last_name) as customer_name,
            u.email,
            SUM(f.product_total_price) as total_spent
        FROM sales_fact_table f
        JOIN user_dimension u ON f.user_id = u.user_id
        JOIN category_dimension c ON f.category_id = c.category_id
        JOIN cart_dimension cd ON f.cart_id = cd.cart_id
        WHERE cd.cart_date BETWEEN %s AND %s
        {category_filter}
        GROUP BY u.user_id, u.first_name, u.last_name, u.email
        ORDER BY total_spent DESC
        LIMIT 5
    """
    cust_df = run_query(customers_query, kpi_params)
    
    if not cust_df.empty:
        # Title case the names
        cust_df["customer_name"] = cust_df["customer_name"].str.title()
        
        fig_cust = px.bar(
            cust_df,
            x="total_spent",
            y="customer_name",
            orientation="h",
            text="total_spent",
            labels={"total_spent": "Total Spent ($)", "customer_name": "Customer"},
            color_discrete_sequence=["#f59e0b"]
        )
        fig_cust.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
        fig_cust.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis=dict(showticklabels=False),
            template="plotly_dark"
        )
        st.plotly_chart(fig_cust, use_container_width=True)
    else:
        st.info("No customer data matches the filters.")

st.markdown("---")

# 5. Raw Data Preview
st.subheader("📋 Explore Data Warehouse Tables")
table_selection = st.selectbox(
    "Choose Table to View",
    options=["sales_fact_table", "product_dimension", "category_dimension", "user_dimension", "cart_dimension"]
)

if table_selection:
    limit_rows = st.number_input("Rows to display", min_value=5, max_value=100, value=10)
    raw_df = run_query(f"SELECT * FROM {table_selection} LIMIT %s", (int(limit_rows),))
    st.dataframe(raw_df, use_container_width=True)
