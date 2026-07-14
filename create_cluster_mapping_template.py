"""
Helper script to generate cluster_mapping.xlsx template.

Run this script to create a fresh cluster_mapping.xlsx file with headers
and example mappings. This file is used to map detailed "Filed Against" paths
to cluster categories (DSW, NET, VAF, CNT, Infra).

Usage:
    py -3.14 create_cluster_mapping_template.py
"""

import pandas as pd
import os


def create_cluster_mapping_template(output_path: str = "cluster_mapping.xlsx"):
    """
    Create a template cluster_mapping.xlsx file with example mappings.
    
    Args:
        output_path (str): Output file path (default: cluster_mapping.xlsx)
    """
    
    # Example mappings (customize these based on your project structure)
    example_mappings = [
        {"Filed Against": "IPB/IPB_SW/IPB_ASW/IPB_ABS", "Cluster": "CNT"},
        {"Filed Against": "IPB/IPB_SW/IPB_BSW/IPB_DCOM", "Cluster": "DSW"},
        {"Filed Against": "RBU/RBU_SW/RBU_Core", "Cluster": "DSW"},
        {"Filed Against": "BWA/BWA_APP/BWA_Diag", "Cluster": "NET"},
        {"Filed Against": "ESP/ESP_FW/ESP_Sensor", "Cluster": "VAF"},
        {"Filed Against": "iBooster/iBooster_HW/iBooster_Control", "Cluster": "CNT"},
    ]
    
    df = pd.DataFrame(example_mappings)
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            sheet_name="Mapped Cluster",
            index=False,
            engine="openpyxl"
        )
        
        # Adjust column widths
        worksheet = writer.sheets["Mapped Cluster"]
        worksheet.column_dimensions["A"].width = 40
        worksheet.column_dimensions["B"].width = 15
    
    print(f"✅ Created cluster mapping template: {output_path}")
    print(f"   Rows: {len(df)}")
    print(f"\nEdit this file to add more mappings or adjust existing ones.")
    print(f"Columns: 'Filed Against' (full path), 'Cluster' (DSW|NET|VAF|CNT|Infra)")


if __name__ == "__main__":
    create_cluster_mapping_template()
