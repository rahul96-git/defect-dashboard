"""
Data Loader Module for Defect Dashboard

Loads ALM export data from Excel, applies all mappings and enrichments from
mapping_config.py, validates required columns, and generates CSV files for
any unmapped values that need configuration.
"""

import os
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
import streamlit as st

import mapping_config as cfg

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_required_columns(df: pd.DataFrame, required_cols: list, sheet_name: str):
    """
    Check that a dataframe contains all required columns.
    
    Args:
        df (pd.DataFrame): The dataframe to validate
        required_cols (list): List of required column names
        sheet_name (str): Name of the sheet (for error messaging)
        
    Raises:
        ValueError: If any required columns are missing
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        actual = sorted(df.columns.tolist())
        raise ValueError(
            f"Missing required columns in '{sheet_name}': {missing}\n"
            f"Actual columns: {actual}"
        )


def load_alm_export(filepath: str) -> pd.DataFrame:
    """
    Load ALM export from Excel QueryResults sheet.
    
    Args:
        filepath (str): Path to Defect_Metrics_ALM_2026.xlsx
        
    Returns:
        pd.DataFrame: Raw ALM data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ALM export file not found: {filepath}")
    
    logger.info(f"Loading ALM export from {filepath}")
    
    try:
        df = pd.read_excel(filepath, sheet_name="QueryResults")
    except Exception as e:
        raise ValueError(f"Failed to read QueryResults sheet from {filepath}: {e}")
    
    logger.info(f"Loaded {len(df)} rows from ALM export")
    validate_required_columns(df, cfg.REQUIRED_ALM_COLUMNS, "QueryResults")
    
    return df


def load_cluster_mapping(filepath: str) -> pd.DataFrame:
    """
    Load cluster mapping from external file.
    
    Args:
        filepath (str): Path to cluster_mapping.xlsx
        
    Returns:
        pd.DataFrame: Cluster mapping with columns [Filed Against, Cluster]
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(filepath):
        logger.warning(f"Cluster mapping file not found: {filepath}")
        logger.warning("Cluster column will be 'Unmapped' for all rows")
        return pd.DataFrame(columns=cfg.REQUIRED_CLUSTER_COLUMNS)
    
    logger.info(f"Loading cluster mapping from {filepath}")
    
    try:
        df = pd.read_excel(filepath, sheet_name="Mapped Cluster")
    except Exception as e:
        logger.warning(f"Failed to read cluster mapping: {e}")
        return pd.DataFrame(columns=cfg.REQUIRED_CLUSTER_COLUMNS)
    
    validate_required_columns(df, cfg.REQUIRED_CLUSTER_COLUMNS, "Mapped Cluster")
    
    logger.info(f"Loaded {len(df)} cluster mappings")
    return df


def write_unmapped_values_csv(values_dict: dict, filename: str, output_dir: str):
    """
    Write unmapped values to a CSV for review and configuration.
    
    values_dict should be {unmapped_value: count, ...}
    Sorted by count descending (highest impact first).
    
    Args:
        values_dict (dict): {unmapped_value: count}
        filename (str): Output filename
        output_dir (str): Directory to write to (created if missing)
    """
    if not values_dict:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Sort by count descending
    sorted_items = sorted(values_dict.items(), key=lambda x: x[1], reverse=True)
    
    df = pd.DataFrame(sorted_items, columns=["Value", "Count"])
    filepath = os.path.join(output_dir, filename)
    
    df.to_csv(filepath, index=False)
    logger.info(f"Wrote {len(df)} unmapped values to {filepath}")


def enrich_dataframe(df: pd.DataFrame, cluster_mapping: pd.DataFrame, output_dir: str = ".") -> tuple:
    """
    Apply all mappings and enrichments from mapping_config.
    
    Adds columns: OEM, Category, Product, Cluster, Resolved_Month, Is_Valid_Resolved
    Also tracks unmapped values and writes CSV files.
    
    Args:
        df (pd.DataFrame): Raw ALM export dataframe
        cluster_mapping (pd.DataFrame): Cluster mapping dataframe
        output_dir (str): Directory to write unmapped CSVs to
        
    Returns:
        tuple: (enriched_df, data_quality_metrics)
    """
    df = df.copy()
    
    # =========================================================================
    # OEM Mapping
    # =========================================================================
    df["OEM"] = df["Project"].apply(cfg.map_oem)
    unmapped_oem = df[df["OEM"] == "Unmapped"].shape[0]
    
    # =========================================================================
    # Category Mapping (from Detection Phase)
    # =========================================================================
    df["Category"] = df["Detection Phase (Custom)"].apply(
        cfg.map_detection_phase_to_category
    )
    unclassified_category = df[df["Category"] == "Unclassified"].shape[0]
    
    # =========================================================================
    # Product Mapping (from Filed Against)
    # =========================================================================
    df[["Product", "FiledAgainst_FirstSegment"]] = df["Filed Against"].apply(
        lambda x: pd.Series(cfg.map_filed_against_to_product(x))
    )
    unmapped_product = df[df["Product"] == "Unmapped"].shape[0]
    
    # Collect unmapped product values for CSV
    unmapped_product_vals = (
        df[df["Product"] == "Unmapped"]
        .groupby("FiledAgainst_FirstSegment")
        .size()
        .to_dict()
    )
    write_unmapped_values_csv(
        unmapped_product_vals,
        cfg.NEEDS_MAPPING_FILE,
        output_dir
    )
    
    # Drop temporary column
    df.drop(columns=["FiledAgainst_FirstSegment"], inplace=True)
    
    # =========================================================================
    # Cluster Mapping (from external file via join)
    # =========================================================================
    if not cluster_mapping.empty:
        # Left join on Filed Against (exact match, full path)
        df = df.merge(
            cluster_mapping,
            on="Filed Against",
            how="left"
        )
        # Fill unmatched with "Unmapped"
        df["Cluster"] = df["Cluster"].fillna("Unmapped")
    else:
        df["Cluster"] = "Unmapped"
    
    unmapped_cluster = df[df["Cluster"] == "Unmapped"].shape[0]
    
    # Collect unmapped cluster values (distinct Filed Against values with counts)
    unmapped_cluster_vals = (
        df[df["Cluster"] == "Unmapped"]
        .groupby("Filed Against")
        .size()
        .to_dict()
    )
    write_unmapped_values_csv(
        unmapped_cluster_vals,
        cfg.NEEDS_CLUSTER_MAPPING_FILE,
        output_dir
    )
    
    # =========================================================================
    # Resolved Month (combine Resolved Year + Resolved Month)
    # =========================================================================
    df["Resolved_Month"] = df.apply(
        lambda row: cfg.build_resolved_month(
            row["Resolved Year"],
            row["Resolved Month"]
        ),
        axis=1
    )
    
    # =========================================================================
    # Valid Resolved Defect Filter
    # =========================================================================
    df["Is_Valid_Resolved"] = df.apply(
        lambda row: cfg.is_valid_resolved_defect(
            row["Status"],
            row["Resolution"]
        ),
        axis=1
    )
    
    excluded_resolutions_count = df[
        (df["Status"].str.lower() == "closed") & 
        (df["Resolution"].isin(cfg.EXCLUDED_RESOLUTIONS))
    ].shape[0]
    
    # =========================================================================
    # Data Quality Metrics
    # =========================================================================
    total_rows = len(df)
    valid_resolved = df["Is_Valid_Resolved"].sum()
    
    data_quality = {
        "total_rows": total_rows,
        "valid_resolved_defects": int(valid_resolved),
        "excluded_resolutions": int(excluded_resolutions_count),
        "unmapped_oem": int(unmapped_oem),
        "unmapped_product": int(unmapped_product),
        "unmapped_cluster": int(unmapped_cluster),
        "unclassified_category": int(unclassified_category),
        "cluster_coverage_pct": round(100 * (total_rows - unmapped_cluster) / total_rows, 2) if total_rows > 0 else 0,
    }
    
    logger.info(f"Data quality metrics: {data_quality}")
    
    return df, data_quality


@st.cache_data(ttl=3600)
def load_data(alm_filepath: str, cluster_mapping_filepath: str = None) -> tuple:
    """
    Main data loading function. Caches with 1-hour TTL.
    
    Loads ALM export and cluster mapping, applies all enrichments,
    and returns enriched dataframe + data quality metrics.
    
    Args:
        alm_filepath (str): Path to Defect_Metrics_ALM_2026.xlsx
        cluster_mapping_filepath (str): Path to cluster_mapping.xlsx (optional)
        
    Returns:
        tuple: (enriched_df, data_quality_metrics)
        
    Raises:
        FileNotFoundError: If ALM export file not found
        ValueError: If required columns are missing
    """
    # Load ALM export
    alm_df = load_alm_export(alm_filepath)
    
    # Load cluster mapping (optional)
    if cluster_mapping_filepath is None:
        cluster_mapping_filepath = alm_filepath.replace(
            "Defect_Metrics_ALM_2026.xlsx",
            "cluster_mapping.xlsx"
        )
    
    cluster_df = load_cluster_mapping(cluster_mapping_filepath)
    
    # Get output directory (same as ALM file directory)
    output_dir = os.path.dirname(alm_filepath)
    
    # Enrich
    enriched_df, metrics = enrich_dataframe(alm_df, cluster_df, output_dir)
    
    logger.info(f"Data loading complete. {metrics['valid_resolved_defects']} valid resolved defects")
    
    return enriched_df, metrics


def clear_cache():
    """Clear the streamlit cache for data loading."""
    st.cache_data.clear()
