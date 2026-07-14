"""
Main Streamlit Application: Defect Tracking Dashboard

This dashboard displays monthly resolved defects from ALM exports,
with configurable dimensions (OEM, Product, Cluster, Category) and
data quality tracking for mapping gaps.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

import data_loader
import charts
import mapping_config as cfg

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Defect Metrics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Defect Metrics Dashboard")
st.markdown("Monthly resolved defects tracking from ALM exports")


# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================

st.sidebar.header("📁 Data Source")

# File uploader / path input
alm_file = st.sidebar.file_uploader(
    "Upload ALM Export (Defect_Metrics_ALM_2026.xlsx)",
    type=["xlsx"],
    help="Excel file with 'QueryResults' sheet containing defect data"
)

cluster_file = st.sidebar.file_uploader(
    "Upload Cluster Mapping (Optional)",
    type=["xlsx"],
    help="Excel file with 'Mapped Cluster' sheet containing Filed Against -> Cluster mapping"
)

# Alternatively allow manual file path input
use_file_path = st.sidebar.checkbox("Use file path instead of upload", value=False)
if use_file_path:
    alm_filepath = st.sidebar.text_input(
        "ALM Export file path",
        value="c:\\path\\to\\Defect_Metrics_ALM_2026.xlsx"
    )
    cluster_filepath = st.sidebar.text_input(
        "Cluster mapping file path (optional)",
        value=""
    )
else:
    alm_filepath = None
    cluster_filepath = None


# Load data button and refresh
st.sidebar.markdown("---")
col_load, col_refresh = st.sidebar.columns(2)

with col_load:
    if st.button("📥 Load Data", use_container_width=True):
        # Determine which file to use
        if alm_file is not None:
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(alm_file.getbuffer())
                alm_path = tmp.name
            
            cluster_path = None
            if cluster_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_cluster:
                    tmp_cluster.write(cluster_file.getbuffer())
                    cluster_path = tmp_cluster.name
        elif alm_filepath and os.path.exists(alm_filepath):
            alm_path = alm_filepath
            cluster_path = cluster_filepath if cluster_filepath and os.path.exists(cluster_filepath) else None
        else:
            st.error("No ALM export file provided or file not found")
            alm_path = None
            cluster_path = None
        
        if alm_path:
            try:
                df, metrics = data_loader.load_data(alm_path, cluster_path)
                st.session_state["df"] = df
                st.session_state["metrics"] = metrics
                st.success(f"✅ Loaded {metrics['valid_resolved_defects']} valid resolved defects")
            except Exception as e:
                st.error(f"❌ Error loading data: {e}")

with col_refresh:
    if st.button("🔄 Clear Cache", use_container_width=True):
        data_loader.clear_cache()
        st.session_state.pop("df", None)
        st.session_state.pop("metrics", None)
        st.info("Cache cleared")


# Check if data is loaded
if "df" not in st.session_state:
    st.warning("⚠️ Please load data using the 'Load Data' button in the sidebar")
    st.stop()


df = st.session_state["df"]
metrics = st.session_state["metrics"]


# ============================================================================
# FILTERS
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

# Multi-select filters
oem_options = sorted(df["OEM"].unique().tolist())
selected_oem = st.sidebar.multiselect(
    "OEM",
    options=oem_options,
    default=oem_options,
    help="Select OEM(s) to include in analysis"
)

product_options = sorted(df["Product"].unique().tolist())
selected_product = st.sidebar.multiselect(
    "Product",
    options=product_options,
    default=product_options,
    help="Select Product(s) to include in analysis"
)

cluster_options = sorted(cfg.VALID_CLUSTERS)
selected_cluster = st.sidebar.multiselect(
    "Cluster",
    options=cluster_options,
    default=cluster_options,
    help="Select Cluster(s) to include (even if empty)"
)

category_options = sorted(df["Category"].unique().tolist())
selected_category = st.sidebar.multiselect(
    "Category",
    options=category_options,
    default=category_options,
    help="Select Category(ies) to include in analysis"
)

# Date range filter
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Date Range (Resolved)")

# Get min/max from data
df_valid = df[df["Resolved_Month"].notna()]
if len(df_valid) > 0:
    min_date_str = df_valid["Resolved_Month"].min()
    max_date_str = df_valid["Resolved_Month"].max()
    min_date = pd.to_datetime(min_date_str)
    max_date = pd.to_datetime(max_date_str)
    default_start = max_date - timedelta(days=180)  # Default last 6 months
else:
    min_date = max_date = default_start = pd.Timestamp.now()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(default_start.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

if len(date_range) == 2:
    date_start, date_end = date_range
    date_start_str = date_start.strftime("%Y-%m")
    date_end_str = date_end.strftime("%Y-%m")
else:
    date_start_str = None
    date_end_str = None


# ============================================================================
# APPLY FILTERS
# ============================================================================

df_filtered = df[
    (df["OEM"].isin(selected_oem)) &
    (df["Product"].isin(selected_product)) &
    (df["Cluster"].isin(selected_cluster)) &
    (df["Category"].isin(selected_category))
].copy()

# Apply date range filter
if date_start_str and date_end_str:
    df_filtered = df_filtered[
        (df_filtered["Resolved_Month"].notna()) &
        (df_filtered["Resolved_Month"] >= date_start_str) &
        (df_filtered["Resolved_Month"] <= date_end_str)
    ]

# Filter to valid resolved defects for metrics
df_filtered_valid = df_filtered[df_filtered["Is_Valid_Resolved"]]


# ============================================================================
# KPI ROW
# ============================================================================

st.markdown("---")
st.subheader("📈 Key Metrics")

kpi = charts.build_kpi_metrics(df_filtered)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Total Resolved",
        value=kpi["total_resolved"],
    )

with col2:
    st.metric(
        label="Month-over-Month",
        value=f"{kpi['mom_delta']:+d}",
        delta=f"{kpi['mom_delta_pct']:+.1f}%",
    )

with col3:
    st.metric(
        label="Customer Reported",
        value=f"{kpi['customer_pct']:.1f}%",
    )

with col4:
    st.metric(
        label="RBT Raised",
        value=f"{kpi['rbt_pct']:.1f}%",
    )

with col5:
    st.metric(
        label="Non-RBT",
        value=f"{kpi['non_rbt_pct']:.1f}%",
    )


# ============================================================================
# DATA QUALITY PANEL
# ============================================================================

st.markdown("---")
st.subheader("⚠️ Data Quality")

dq_col1, dq_col2, dq_col3, dq_col4, dq_col5 = st.columns(5)

with dq_col1:
    st.metric(
        label="Unmapped OEM",
        value=metrics["unmapped_oem"],
    )

with dq_col2:
    st.metric(
        label="Unmapped Product",
        value=metrics["unmapped_product"],
    )

with dq_col3:
    st.metric(
        label="Unmapped Cluster",
        value=metrics["unmapped_cluster"],
    )

with dq_col4:
    st.metric(
        label="Unclassified Category",
        value=metrics["unclassified_category"],
    )

with dq_col5:
    st.metric(
        label="Cluster Coverage",
        value=f"{metrics['cluster_coverage_pct']:.1f}%",
        help="% of resolved defects with mapped cluster"
    )

st.info(
    f"ℹ️ Data source: {metrics['total_rows']} total rows, "
    f"{metrics['excluded_resolutions']} excluded (Duplicate/Invalid), "
    f"{metrics['valid_resolved_defects']} valid resolved defects"
)


# ============================================================================
# DASHBOARD TABS
# ============================================================================

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🏢 OEM/Product", "🎯 Cluster", "📂 Categories", "📋 Data Table"]
)


# TAB 1: Overview
with tab1:
    st.subheader("Resolved Defects by OEM and Product")
    fig_oem_product = charts.chart_resolved_by_oem_product(df_filtered)
    st.plotly_chart(fig_oem_product, use_container_width=True)


# TAB 2: OEM/Product
with tab2:
    col_trend, col_heat = st.columns(2)
    
    with col_trend:
        st.subheader("Cluster Trend")
        fig_cluster_trend = charts.chart_resolved_by_cluster(df_filtered)
        st.plotly_chart(fig_cluster_trend, use_container_width=True)
    
    with col_heat:
        st.subheader("Cluster Heatmap")
        fig_heatmap = charts.chart_cluster_heatmap(df_filtered)
        st.plotly_chart(fig_heatmap, use_container_width=True)


# TAB 3: Cluster
with tab3:
    st.subheader("Resolved Defects by Cluster")
    
    # Option to slice by OEM or no grouping
    grouping = st.radio(
        "Group by:",
        options=["None", "OEM", "Product"],
        horizontal=True,
    )
    
    group_col = None if grouping == "None" else grouping
    fig_category = charts.chart_category_breakdown(df_filtered, group_by=group_col)
    st.plotly_chart(fig_category, use_container_width=True)


# TAB 4: Categories
with tab4:
    st.subheader("Priority vs Severity")
    fig_priority_severity = charts.chart_priority_severity_grid(df_filtered)
    st.plotly_chart(fig_priority_severity, use_container_width=True)


# TAB 5: Data Table
with tab5:
    st.subheader("Filtered Defects Data")
    
    # Display filtered data
    display_cols = [
        "Project", "Work Item ID", "Work Item", "Status", "Resolution",
        "Resolved_Month", "Priority", "Severity", "OEM", "Product", "Cluster",
        "Category", "Owner", "Filed Against"
    ]
    
    display_df = df_filtered[[col for col in display_cols if col in df_filtered.columns]].copy()
    
    # Sort by Resolved_Month descending
    if "Resolved_Month" in display_df.columns:
        display_df = display_df.sort_values("Resolved_Month", ascending=False, na_position="last")
    
    st.dataframe(display_df, use_container_width=True, height=500)
    
    # CSV export
    csv_data = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv_data,
        file_name=f"defects_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 0.8em; color: gray;'>
    Defect Metrics Dashboard | Last updated: {0}<br/>
    Configuration editable in: mapping_config.py, cluster_mapping.xlsx
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True,
)
