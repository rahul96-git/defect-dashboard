# Defect Metrics Dashboard

A modular Streamlit dashboard for tracking monthly resolved defects from ALM exports with configurable dimensions, data quality tracking, and extensible mapping rules.

## 📁 Project Structure

```
defect_dashboard/
├── app.py                              # Main Streamlit application
├── mapping_config.py                   # All configurable mapping rules
├── data_loader.py                      # Data loading, validation, enrichment
├── charts.py                           # Chart generation functions
├── create_cluster_mapping_template.py  # Helper to generate cluster_mapping.xlsx
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
├── Defect_Metrics_ALM_2026.xlsx        # ALM export (to be provided)
└── cluster_mapping.xlsx                # Cluster mapping file (generate from template)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
py -3.14 -m pip install -r requirements.txt
```

### 2. Create Cluster Mapping Template

```bash
py -3.14 create_cluster_mapping_template.py
```

This generates `cluster_mapping.xlsx` with example mappings. Edit this file to add your project-specific cluster mappings.

### 3. Prepare ALM Export

Place your `Defect_Metrics_ALM_2026.xlsx` file in this directory. The file must have a sheet named `QueryResults` with these columns:

- Project
- Work Item ID
- Work Item
- URL
- Resolution
- Resolved Date
- Resolved Year
- Resolved Month
- Creation Date
- Creator
- Status
- Priority
- Severity
- Planned For
- Filed Against
- Injection Phase (Custom)
- Detection Phase (Custom)
- Owner

### 4. Run the Dashboard

```bash
py -3.14 -m streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📊 Dashboard Features

### KPI Metrics
- Total resolved defects (filtered)
- Category split percentages
- Month-over-month delta

### Charts & Visualizations
1. **Resolved by OEM/Product** – Monthly stacked bar chart
2. **Cluster Trend** – Monthly line chart per cluster
3. **Cluster Heatmap** – Cluster × Month matrix
4. **Category Breakdown** – 100% stacked bar by category
5. **Priority vs Severity** – Bubble chart
6. **Data Table** – Filtered defects with CSV export

### Data Quality Panel
Shows visibility into mapping gaps:
- Unmapped OEM count
- Unmapped Product count
- Unmapped Cluster count
- Unclassified Category count
- Cluster coverage percentage

### Filters
Multi-select filters (all default to all values):
- OEM
- Product
- Cluster
- Category
- Date range (Resolved Month)

## ⚙️ Configuration

### `mapping_config.py`

All mapping rules are externalized here and heavily commented. Edit these to customize classification logic:

#### OEM Mapping
Map `Project` column to OEM categories using substring matching:
```python
map_oem("Audi Q5 Project")      # → "Audi"
map_oem("VW Golf Platform")     # → "VW"
map_oem("Porsche 911 SW")      # → "Porsche"
map_oem("Unknown Project")      # → "Unmapped"
```

#### Category Mapping
Map `Detection Phase (Custom)` to defect categories:
- **Customer Reported** – Field issues, customer validation
- **RBT Raised** – Test/verification activities
- **Non-RBT** – Static analysis, code reviews
- **Unclassified** – Unmapped or blank phases

Edit `DETECTION_PHASE_TO_CATEGORY` dict to customize.

#### Product Mapping
Map first segment of `Filed Against` path to product:
- IPB, RBU, BWA, ESP, iBooster, etc.
- Edit `FILED_AGAINST_TO_PRODUCT` dict

Any unmapped values are written to `needs_mapping.csv` for later review.

#### Cluster Mapping
Loaded from `cluster_mapping.xlsx` (sheet: "Mapped Cluster"):
- Left-joins on full `Filed Against` path (exact match)
- Valid values: DSW, NET, VAF, CNT, Infra
- Unmapped values written to `needs_cluster_mapping.csv` (sorted by count)
- Includes data quality metric: % of defects with mapped cluster

#### Resolution Filtering
Only rows with `Status == "Closed"` and `Resolution NOT IN ["Duplicate", "Invalid"]` are counted as valid resolved defects.

Edit `EXCLUDED_RESOLUTIONS` constant to change.

## 📁 Cluster Mapping File

The `cluster_mapping.xlsx` file is a lookup table that maps detailed `Filed Against` paths to cluster categories.

**Sheet:** "Mapped Cluster"
**Columns:**
- `Filed Against` – Full path (e.g., "IPB/IPB_SW/IPB_ASW/IPB_ABS")
- `Cluster` – Category (DSW, NET, VAF, CNT, Infra)

**Generate template:**
```bash
py -3.14 create_cluster_mapping_template.py
```

Then edit to add your mappings. When data loads:
- Matched rows get their cluster value
- Unmatched rows get "Unmapped"
- All distinct unmatched `Filed Against` values written to `needs_cluster_mapping.csv`

## 📊 Data Quality Outputs

The app generates CSV files in the same directory as the ALM export:

### `needs_mapping.csv`
Unmapped `Filed Against` first segments (Product gaps). Columns:
- `Value` – First path segment
- `Count` – Number of defects

### `needs_cluster_mapping.csv`
Unmapped full `Filed Against` paths (Cluster gaps). Columns:
- `Value` – Full Filed Against path
- `Count` – Number of defects (sorted descending, highest impact first)

Use these files to identify and prioritize mapping extensions.

## 🔄 Data Loading & Caching

- Data is cached with 1-hour TTL (configurable in `data_loader.py`)
- Use the **Refresh Data** button to clear cache immediately
- Cache also clears when browser session expires

## 🛠️ Usage Workflow

1. **First run:**
   - Generate cluster_mapping.xlsx template
   - Customize it with your project mappings
   - Place ALM export in the directory
   - Load data

2. **Ongoing:**
   - ALM export is periodically refreshed
   - Re-upload or re-point to the file
   - Click "Load Data" to refresh
   - Dashboard automatically picks up new/changed defects

3. **Mapping gaps:**
   - Review `needs_mapping.csv` and `needs_cluster_mapping.csv`
   - Add missing values to `mapping_config.py` or `cluster_mapping.xlsx`
   - Click "Clear Cache" and "Load Data" to see changes

## 📝 Notes

- Rows with missing `Resolved Year` or `Resolved Month` are excluded from date filtering
- Rows are counted toward "resolved defect" metrics only if they pass the Status/Resolution filter
- "Unmapped" values (OEM, Product, Cluster) are never silently dropped; they appear in filters and charts
- All configuration is **non-programmatic** – edit dicts/CSVs, not code logic

## 🐛 Troubleshooting

**Data not loading:**
- Check that ALM file has a "QueryResults" sheet
- Verify all required columns are present (error message lists missing ones)
- Check file path or upload status

**Charts showing "No data available":**
- Adjust filters to include more rows
- Check date range

**Unmapped values everywhere:**
- Review `needs_mapping.csv` and `needs_cluster_mapping.csv`
- Add mappings to `mapping_config.py` or `cluster_mapping.xlsx`
- Clear cache and reload data

## 📦 Dependencies

- **streamlit** – Web app framework
- **pandas** – Data manipulation
- **plotly** – Interactive charting
- **openpyxl** – Excel file handling

## 📄 License

Internal use only.
