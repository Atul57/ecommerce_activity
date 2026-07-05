"""
E-Commerce Sales Dashboard — Streamlit App
Run with:  streamlit run ecommerce_dashboard_app.py

Expects 'cleaned_ecommerce_sales_data.csv' in the same folder as this script.
If it's not found, you'll get an uploader to pick the file manually.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="🛒",
    layout="wide",
)

CSV_PATH = "cleaned_ecommerce_sales_data.csv"


@st.cache_data
def load_data(path_or_buffer):
    df = pd.read_csv(path_or_buffer)
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    df["Year"] = df["Order_Date"].dt.year
    df["Quarter"] = df["Order_Date"].dt.to_period("Q").astype(str)
    df["Month"] = df["Order_Date"].dt.to_period("M").astype(str)
    return df


# ----------------------------------------------------------------------
# Load data (local file first, fall back to uploader)
# ----------------------------------------------------------------------
try:
    df = load_data(CSV_PATH)
except FileNotFoundError:
    st.warning(f"Couldn't find `{CSV_PATH}` next to this script.")
    uploaded = st.file_uploader("Upload the sales CSV to continue", type="csv")
    if uploaded is None:
        st.stop()
    df = load_data(uploaded)

# ----------------------------------------------------------------------
# Sidebar filters — these drive every KPI, chart, and table below
# ----------------------------------------------------------------------
st.sidebar.header("🔎 Filters")

categories = sorted(df["Category"].unique())
payments = sorted(df["Payment_Method"].unique())
statuses = sorted(df["Status"].unique())
years = sorted(df["Year"].unique())

sel_categories = st.sidebar.multiselect("Category", categories, default=categories)
sel_payments = st.sidebar.multiselect("Payment Method", payments, default=payments)
sel_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)
sel_years = st.sidebar.multiselect("Year", years, default=years)

min_date, max_date = df["Order_Date"].min(), df["Order_Date"].max()
date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if st.sidebar.button("Reset filters"):
    st.rerun()

# Apply filters
mask = (
    df["Category"].isin(sel_categories)
    & df["Payment_Method"].isin(sel_payments)
    & df["Status"].isin(sel_statuses)
    & df["Year"].isin(sel_years)
)
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask &= df["Order_Date"].between(start, end)

fdf = df[mask]

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("🛒 E-Commerce Sales Dashboard")
st.caption("Use the sidebar filters to slice every metric, chart, and table on this page.")

if fdf.empty:
    st.info("No orders match the current filters. Try widening your selection.")
    st.stop()

# ----------------------------------------------------------------------
# KPI cards
# ----------------------------------------------------------------------
total_sales = fdf["Total"].sum()
total_orders = len(fdf)
avg_order_value = total_sales / total_orders if total_orders else 0
units_sold = fdf["Quantity"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Orders", f"{total_orders:,}")
k3.metric("Avg Order Value", f"${avg_order_value:,.2f}")
k4.metric("Units Sold", f"{units_sold:,.0f}")

st.divider()

# ----------------------------------------------------------------------
# Charts row 1: Sales by Category | Sales Share by Payment Method
# ----------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    cat_sales = (
        fdf.groupby("Category", as_index=False)["Total"]
        .sum()
        .sort_values("Total", ascending=False)
    )
    fig = px.bar(
        cat_sales, x="Category", y="Total", title="Sales by Category",
        text_auto=".2s", color="Category",
    )
    fig.update_layout(showlegend=False, yaxis_title="Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    pay_sales = fdf.groupby("Payment_Method", as_index=False)["Total"].sum()
    fig = px.pie(
        pay_sales, names="Payment_Method", values="Total",
        title="Sales Share by Payment Method", hole=0.4,
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# Charts row 2: Order Count by Status | Quarterly Sales Trend
# ----------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    status_counts = fdf["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Orders"]
    fig = px.bar(
        status_counts, x="Status", y="Orders", title="Order Count by Status",
        text_auto=True, color="Status",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    trend = fdf.groupby("Quarter", as_index=False)["Total"].sum().sort_values("Quarter")
    fig = px.line(
        trend, x="Quarter", y="Total", title="Quarterly Sales Trend", markers=True,
    )
    fig.update_layout(yaxis_title="Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# Top products & raw data
# ----------------------------------------------------------------------
st.divider()
c5, c6 = st.columns([1, 2])

with c5:
    top_products = (
        fdf.groupby("Product", as_index=False)["Total"]
        .sum()
        .sort_values("Total", ascending=False)
        .head(10)
    )
    fig = px.bar(
        top_products, x="Total", y="Product", orientation="h",
        title="Top 10 Products by Sales",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Filtered Order Data")
    st.dataframe(
        fdf.sort_values("Order_Date", ascending=False).drop(columns=["Year", "Quarter", "Month"]),
        use_container_width=True,
        height=430,
    )
    csv_bytes = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_sales_data.csv",
        mime="text/csv",
    )
