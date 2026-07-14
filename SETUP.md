# Defect Dashboard Setup Guide

This guide walks through setting up and deploying the Defect Metrics Dashboard.

## ✅ Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Your ALM export file: `Defect_Metrics_ALM_2026.xlsx`

## 📦 Step 1: Install Dependencies

Navigate to the dashboard directory and install Python packages:

```bash
cd defect_dashboard
pip install -r requirements.txt
```

**What gets installed:**
- `streamlit` – Web framework
- `pandas` – Data processing
- `plotly` – Interactive charts
- `openpyxl` – Excel file I/O

## 📋 Step 2: Create Cluster Mapping Template

Generate the empty cluster mapping file:

```bash
python create_cluster_mapping_template.py
```

This creates `cluster_mapping.xlsx` with example mappings in a sheet called "Mapped Cluster".

**Output:**
```
✅ Created cluster mapping template: cluster_mapping.xlsx
   Rows: 6
```

## ✏️ Step 3: Customize Cluster Mapping

Open `cluster_mapping.xlsx` in Excel and:

1. Keep the "Mapped Cluster" sheet (do not rename)
2. Keep columns: "Filed Against", "Cluster"
3. Edit the example rows to match your project structure
4. Add more rows as needed

**Example mappings:**
| Filed Against | Cluster |
|---|---|
| IPB/IPB_SW/IPB_ASW/IPB_ABS | CNT |
| IPB/IPB_SW/IPB_BSW/IPB_DCOM | DSW |
| RBU/RBU_SW/RBU_Core | DSW |
| BWA/BWA_APP/BWA_Diag | NET |

Save and close the file.

## 📊 Step 4: Prepare ALM Export

Place your ALM export file (`Defect_Metrics_ALM_2026.xlsx`) in the dashboard directory alongside `cluster_mapping.xlsx`.

**File structure should now be:**
```
defect_dashboard/
├── app.py
├── mapping_config.py
├── data_loader.py
├── charts.py
├── requirements.txt
├── README.md
├── cluster_mapping.xlsx        ← Created
└── Defect_Metrics_ALM_2026.xlsx    ← Place here
```

## 🚀 Step 5: Launch the Dashboard

```bash
streamlit run app.py
```

Streamlit will start a local web server:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open your browser to `http://localhost:8501`

## 🔧 Step 6: Configure Mapping Rules (Optional)

The dashboard auto-maps dimensions using rules in `mapping_config.py`. You can customize these:

### OEM Mapping
Edit the `map_oem()` function to adjust Project → OEM logic:
```python
def map_oem(project: str) -> str:
    if "AUDI" in project.upper():
        return "Audi"
    # ... etc
```

### Category Mapping
Edit `DETECTION_PHASE_TO_CATEGORY` dict:
```python
DETECTION_PHASE_TO_CATEGORY = {
    "Customer Validation": "Customer Reported",
    "Unit Test": "RBT Raised",
    # ... add more mappings
}
```

### Product Mapping
Edit `FILED_AGAINST_TO_PRODUCT` dict:
```python
FILED_AGAINST_TO_PRODUCT = {
    "IPB": "IPB",
    "RBU": "RBU",
    # ... add your products
}
```

### Excluded Resolutions
Edit the list of resolutions to exclude:
```python
EXCLUDED_RESOLUTIONS = ["Duplicate", "Invalid"]
```

## 📥 Step 7: Load Data into Dashboard

1. In the dashboard sidebar, under "📁 Data Source":
   - Click **"Upload ALM Export"** and select your `Defect_Metrics_ALM_2026.xlsx`, OR
   - Check **"Use file path instead"** and paste the full path
   - (Optional) Upload `cluster_mapping.xlsx` if not in the same directory

2. Click **"📥 Load Data"**

3. Wait for success message:
   ```
   ✅ Loaded 1,234 valid resolved defects
   ```

## 📊 Step 8: Explore the Dashboard

The dashboard appears with:

- **KPI Row** – Total resolved, month-over-month delta, category splits
- **Data Quality Panel** – Shows any unmapped values and coverage %
- **Tabs:**
  - 📊 Overview – OEM/Product trend
  - 🏢 OEM/Product – Detailed breakdowns
  - 🎯 Cluster – Cluster trends and heatmap
  - 📂 Categories – Category split analysis
  - 📋 Data Table – Full filtered data + CSV export

### 🔍 Filters

Use the sidebar to refine data:
- **OEM** – Select OEM(s)
- **Product** – Select Product(s)
- **Cluster** – Select Cluster(s)
- **Category** – Select Category(ies)
- **Date Range** – Select Resolved Month range

All defaults include all values so nothing silently disappears.

## 📁 Data Quality Files

After loading data, check for mapping gaps in these files:

- **`needs_mapping.csv`** – Unmapped Product first-segments. Add to `FILED_AGAINST_TO_PRODUCT` dict.
- **`needs_cluster_mapping.csv`** – Unmapped full paths. Add to `cluster_mapping.xlsx`.

Both files are sorted by count (highest impact first).

## 🔄 Ongoing Updates

When your ALM export is refreshed:

1. Replace `Defect_Metrics_ALM_2026.xlsx` with the fresh export
2. Click **"🔄 Clear Cache"** in the dashboard
3. Click **"📥 Load Data"** again
4. Dashboard automatically reflects new/changed defects

## 🛠️ Troubleshooting

### "Missing required columns in 'QueryResults'"
- ALM export file is missing columns
- Error message lists which columns
- Ensure the export has all required columns

### "Cluster mapping file not found"
- `cluster_mapping.xlsx` is not in the same directory as ALM file
- Or the sheet is named incorrectly (must be "Mapped Cluster")
- Dashboard will still work; all defects will have Cluster = "Unmapped"

### Charts showing "No data available"
- Adjust filters to include more rows
- Check the date range is not too restrictive

### Dashboard won't load at all
- Check Python version: `python --version` (should be 3.8+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check for error messages in terminal

## 📝 Notes

- Dashboard runs locally on your machine; no internet required (after dependencies installed)
- Data is cached for 1 hour; use "Clear Cache" to force refresh
- All mapping rules are in `mapping_config.py` – no hardcoding in charts/app code
- Unmapped values are never silently dropped; they appear as "Unmapped" or "Unclassified" categories

## 🎯 Next Steps

1. Run through the dashboard and verify data looks correct
2. Review `needs_mapping.csv` and extend product mappings as needed
3. Review `needs_cluster_mapping.csv` and extend cluster mappings as needed
4. Share with team and gather feedback
5. Iterate on mapping rules as needed

## ❓ Questions

Refer to:
- `README.md` – Overview and feature summary
- `mapping_config.py` – Inline comments on each mapping function
- `data_loader.py` – Data enrichment logic
- `charts.py` – Chart function signatures and behavior
- `app.py` – Streamlit layout and filter logic
