"""
Chart Module for Defect Dashboard

Contains functions to generate all dashboard charts using Plotly.
Each function is parameterized by dataframe and filtering criteria.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


def build_kpi_metrics(df_filtered: pd.DataFrame) -> dict:
    """
    Calculate KPI metrics for the filtered dataset.
    
    Args:
        df_filtered (pd.DataFrame): Filtered defects dataframe
        
    Returns:
        dict: KPI values including total, month-over-month delta, category split
    """
    # Filter to valid resolved defects only
    valid_df = df_filtered[df_filtered["Is_Valid_Resolved"]].copy()
    
    total_resolved = len(valid_df)
    
    if total_resolved == 0:
        return {
            "total_resolved": 0,
            "mom_delta": 0,
            "mom_delta_pct": 0,
            "customer_pct": 0,
            "rbt_pct": 0,
            "non_rbt_pct": 0,
            "unclassified_pct": 0,
        }
    
    # Category split
    category_counts = valid_df["Category"].value_counts()
    total = category_counts.sum()
    
    kpi = {
        "total_resolved": total_resolved,
        "customer_pct": round(100 * category_counts.get("Customer Reported", 0) / total, 1) if total > 0 else 0,
        "rbt_pct": round(100 * category_counts.get("RBT Raised", 0) / total, 1) if total > 0 else 0,
        "non_rbt_pct": round(100 * category_counts.get("Non-RBT", 0) / total, 1) if total > 0 else 0,
        "unclassified_pct": round(100 * category_counts.get("Unclassified", 0) / total, 1) if total > 0 else 0,
    }
    
    # Month-over-month delta
    if valid_df["Resolved_Month"].notna().any():
        monthly = valid_df[valid_df["Resolved_Month"].notna()].groupby("Resolved_Month").size()
        if len(monthly) >= 2:
            current_month = monthly.iloc[-1]
            previous_month = monthly.iloc[-2]
            delta = current_month - previous_month
            delta_pct = round(100 * delta / previous_month, 1) if previous_month > 0 else 0
            kpi["mom_delta"] = delta
            kpi["mom_delta_pct"] = delta_pct
        else:
            kpi["mom_delta"] = 0
            kpi["mom_delta_pct"] = 0
    else:
        kpi["mom_delta"] = 0
        kpi["mom_delta_pct"] = 0
    
    return kpi


def chart_resolved_by_oem_product(df_filtered: pd.DataFrame) -> go.Figure:
    """
    Create a stacked monthly bar chart: OEM as primary group, Product as sub-group.
    
    Args:
        df_filtered (pd.DataFrame): Filtered defects dataframe
        
    Returns:
        go.Figure: Plotly figure
    """
    valid_df = df_filtered[df_filtered["Is_Valid_Resolved"]].copy()
    
    # Remove rows without Resolved_Month
    valid_df = valid_df[valid_df["Resolved_Month"].notna()]
    
    if len(valid_df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Group by Month and OEM/Product, count
    grouped = valid_df.groupby(["Resolved_Month", "OEM", "Product"]).size().reset_index(name="Count")
    grouped = grouped.sort_values("Resolved_Month")
    
    fig = px.bar(
        grouped,
        x="Resolved_Month",
        y="Count",
        color="OEM",
        hover_data={"Product": True},
        barmode="stack",
        title="Resolved Defects by OEM and Product (Monthly)",
        labels={"Resolved_Month": "Month", "Count": "Defects"},
    )
    
    fig.update_layout(
        hovermode="x unified",
        height=400,
        showlegend=True,
        legend_title="OEM"
    )
    
    return fig


def chart_resolved_by_cluster(df_filtered: pd.DataFrame) -> go.Figure:
    """
    Create a monthly line chart showing trend per cluster.
    
    Args:
        df_filtered (pd.DataFrame): Filtered defects dataframe
        
    Returns:
        go.Figure: Plotly figure
    """
    valid_df = df_filtered[df_filtered["Is_Valid_Resolved"]].copy()
    valid_df = valid_df[valid_df["Resolved_Month"].notna()]
    
    if len(valid_df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Group by Month and Cluster
    grouped = valid_df.groupby(["Resolved_Month", "Cluster"]).size().reset_index(name="Count")
    grouped = grouped.sort_values("Resolved_Month")
    
    fig = px.line(
        grouped,
        x="Resolved_Month",
        y="Count",
        color="Cluster",
        markers=True,
        title="Resolved Defects Trend by Cluster",
        labels={"Resolved_Month": "Month", "Count": "Defects"},
    )
    
    fig.update_layout(
        hovermode="x unified",
        height=400,
        showlegend=True,
    )
    
    return fig


def chart_cluster_heatmap(df_filtered: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap: Cluster x Month showing defect counts.
    
    Args:
        df_filtered (pd.DataFrame): Filtered defects dataframe
        
    Returns:
        go.Figure: Plotly figure
    """
    valid_df = df_filtered[df_filtered["Is_Valid_Resolved"]].copy()
    valid_df = valid_df[valid_df["Resolved_Month"].notna()]
    
    if len(valid_df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Pivot: rows = Cluster, cols = Month, values = Count
    pivot = valid_df.groupby(["Cluster", "Resolved_Month"]).size().unstack(fill_value=0)
    
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            text=pivot.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Cluster: %{y}<br>Month: %{x}<br>Defects: %{z}<extra></extra>"
        )
    )
    
    fig.update_layout(
        title="Resolved Defects Heatmap: Cluster x Month",
        xaxis_title="Month",
        yaxis_title="Cluster",
        height=300,
    )
    
    return fig


def chart_category_breakdown(
    df_filtered: pd.DataFrame,
    group_by: str = None
) -> go.Figure:
    """
    Create a 100% stacked bar chart of categories by month.
    Optionally group by OEM or Cluster for secondary dimension.
    
    Args:
        df_filtered (pd.DataFrame): Filtered defects dataframe
        group_by (str): Optional grouping column ("OEM" or "Cluster")
        
    Returns:
        go.Figure: Plotly figure
    """
    valid_df = df_filtered[df_filtered["Is_Valid_Resolved"]].copy()
    valid_df = valid_df[valid_df["Resolved_Month"].notna()]
    
    if len(valid_df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    if group_by and group_by in valid_df.columns:
        # Group by Month + group_by + Category
        grouped = valid_df.groupby(["Resolved_Month", group_by, "Category"]).size().reset_index(name="Count")
        
        fig = px.bar(
            grouped,
            x="Resolved_Month",
            y="Count",
            color="Category",
            facet_col=group_by,
            barmode="stack",
            title=f"Category Breakdown by Month (Grouped by {group_by})",
            labels={"Resolved_Month": "Month", "Count": "Defects"},
        )
        fig.update_layout(height=500)
    else:
        # Simple: Month + Category
        grouped = valid_df.groupby(["Resolved_Month", "Category"]).size().reset_index(name="Count")
        grouped = grouped.sort_values("Resolved_Month")
        
        fig = px.bar(
            grouped,
            x="Resolved_Month",
            y="Count",
            color="Category",
            barmode="stack",
            title="Category Breakdown by Month",
            labels={"Resolved_Month": "Month", "Count": "Defects"},
        )
        fig.update_layout(height=400)
    
    fig.update_layout(
        hovermode="x unified",
        showlegend=True,
    )
    
    return fig


def chart_priority_severity_grid(df_filtered: pd.DataFrame) -> go.Figure:
    """
    Create a scatter/bubble chart of Priority vs Severity.
    
    Args:
        df_filtered (pd.DataFrame): Filtered defects dataframe
        
    Returns:
        go.Figure: Plotly figure
    """
    valid_df = df_filtered[df_filtered["Is_Valid_Resolved"]].copy()
    
    # Count by Priority + Severity
    grouped = valid_df.groupby(["Priority", "Severity"]).size().reset_index(name="Count")
    
    if len(grouped) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    fig = px.scatter(
        grouped,
        x="Priority",
        y="Severity",
        size="Count",
        hover_data={"Count": True},
        title="Resolved Defects: Priority vs Severity",
        labels={"Priority": "Priority", "Severity": "Severity"},
    )
    
    fig.update_layout(
        height=400,
        hovermode="closest",
    )
    
    return fig
