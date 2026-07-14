"""
Mapping Configuration Module for Defect Dashboard

This module contains all the configurable mapping rules for deriving dimensions from
raw ALM export data. All rules are externally editable (not hardcoded in logic code),
so you can update classification rules here without touching the app or data loader.

Categories:
  - OEM (from Project column)
  - Category (from Detection Phase)
  - Product (from Filed Against, first path segment)
  - Cluster (loaded from external mapping file)
  - Resolved_Month (from Resolved Year + Resolved Month)
"""

# ============================================================================
# OEM MAPPING
# ============================================================================
# Derive OEM from the Project column using case-insensitive substring matching.
# Order matters: Audi is checked first, then VAG/VW together, then Porsche.
# Any Project not matching any rule maps to "Unmapped" and is flagged in data quality.

def map_oem(project: str) -> str:
    """
    Classify a project name into an OEM category.
    
    Args:
        project (str): The Project column value from ALM export
        
    Returns:
        str: One of "Audi", "VW", "Porsche", or "Unmapped"
    """
    if not project or not isinstance(project, str):
        return "Unmapped"
    
    project_upper = project.upper()
    
    if "AUDI" in project_upper:
        return "Audi"
    elif "VAG" in project_upper or "VW" in project_upper:
        return "VW"
    elif "PORSCHE" in project_upper:
        return "Porsche"
    else:
        return "Unmapped"


# ============================================================================
# CATEGORY MAPPING (from Detection Phase Custom)
# ============================================================================
# Each detection phase value (from "Detection Phase (Custom)" column) is classified
# into one of: "Customer Reported", "RBT Raised", "Non-RBT", or "Unclassified".
# 
# This is implemented as an explicit mapping dict so you can adjust the rules
# by editing the dictionary keys directly, without touching the logic.

DETECTION_PHASE_TO_CATEGORY = {
    # Customer Reported phases
    "Customer Validation": "Customer Reported",
    "PF Defect from CUS-Prj": "Customer Reported",
    "Field": "Customer Reported",
    "Pre-0 Km": "Customer Reported",
    
    # RBT Raised phases (testing/verification activities)
    "Qualification Test": "RBT Raised",
    "Component Test": "RBT Raised",
    "Integration Test": "RBT Raised",
    "Unit Test": "RBT Raised",
    "Hardware Verification": "RBT Raised",
    "Mechanical Verification": "RBT Raised",
    
    # Non-RBT phases (static analysis, review, compliance)
    "Static Code Analysis": "Non-RBT",
    "Manual Code Review": "Non-RBT",
    "Review": "Non-RBT",
    "Process Compliance Check": "Non-RBT",
}


def map_detection_phase_to_category(detection_phase: str) -> str:
    """
    Classify a detection phase into a defect category.
    
    Uses exact dictionary lookup first, then falls back to substring matching
    for flexibility with slight variations in naming.
    
    Args:
        detection_phase (str): The Detection Phase (Custom) column value
        
    Returns:
        str: One of "Customer Reported", "RBT Raised", "Non-RBT", or "Unclassified"
    """
    if not detection_phase or not isinstance(detection_phase, str):
        return "Unclassified"
    
    # Try exact match first
    if detection_phase in DETECTION_PHASE_TO_CATEGORY:
        return DETECTION_PHASE_TO_CATEGORY[detection_phase]
    
    # Fall back to substring matching for partial matches
    detection_phase_lower = detection_phase.lower()
    
    # Check RBT keywords
    rbt_keywords = ["qualification test", "component test", "integration test", 
                    "unit test", "hardware verification", "mechanical verification"]
    for keyword in rbt_keywords:
        if keyword in detection_phase_lower:
            return "RBT Raised"
    
    # Check Non-RBT keywords
    non_rbt_keywords = ["static code analysis", "manual code review", "review", 
                        "process compliance"]
    for keyword in non_rbt_keywords:
        if keyword in detection_phase_lower:
            return "Non-RBT"
    
    # Check Customer Reported keywords
    customer_keywords = ["customer", "field", "pre-0"]
    for keyword in customer_keywords:
        if keyword in detection_phase_lower:
            return "Customer Reported"
    
    return "Unclassified"


# ============================================================================
# PRODUCT MAPPING
# ============================================================================
# Derive Product from the first path segment of "Filed Against" (split on "/", take index 0),
# then look it up in the FILED_AGAINST_TO_PRODUCT dict.
# 
# Any unmapped value is logged to "needs_mapping.csv" for later configuration.

FILED_AGAINST_TO_PRODUCT = {
    # IPB product variants
    "IPB": "IPB",
    "IPB_PJM": "IPB",
    
    # RBU product variants
    "RBU": "RBU",
    
    # BWA product variants
    "BWA": "BWA",
    
    # iBooster product variants
    "iBooster Gen2": "iBooster",
    "iBooster": "iBooster",
    
    # ESP product variants (VW-specific naming)
    "ESP10": "ESP",
    "ESP": "ESP",
    
    # Shared/Common components (not forced into a single product)
    # "Any Product": "Shared/Common",  # Example placeholder
}


def map_filed_against_to_product(filed_against: str) -> tuple:
    """
    Extract the product from Filed Against path and map to product category.
    
    Splits "Filed Against" on "/" and takes the first segment as the lookup key.
    
    Args:
        filed_against (str): The Filed Against column value (may be a path like "IPB/IPB_SW/...")
        
    Returns:
        tuple: (product_category, lookup_key) where lookup_key is the first path segment
               product_category is one of the mapped products or "Unmapped"
    """
    if not filed_against or not isinstance(filed_against, str):
        return "Unmapped", None
    
    # Extract first path segment
    lookup_key = filed_against.split("/")[0].strip()
    
    if lookup_key in FILED_AGAINST_TO_PRODUCT:
        return FILED_AGAINST_TO_PRODUCT[lookup_key], lookup_key
    else:
        return "Unmapped", lookup_key


# ============================================================================
# RESOLUTION FILTERING
# ============================================================================
# Define which resolution values should be EXCLUDED from "resolved defects" counts.
# 
# Only rows with Status == "Closed" AND Resolution NOT IN EXCLUDED_RESOLUTIONS
# are counted as genuine resolved defects. Duplicates and Invalid items are excluded.

EXCLUDED_RESOLUTIONS = ["Duplicate", "Invalid"]


def is_valid_resolved_defect(status: str, resolution: str) -> bool:
    """
    Determine if a row represents a genuine resolved defect.
    
    A defect is considered genuinely resolved if:
      - Status is "Closed"
      - Resolution is NOT in the excluded list (Duplicate, Invalid)
    
    Args:
        status (str): The Status column value
        resolution (str): The Resolution column value
        
    Returns:
        bool: True if the defect should be counted as resolved, False otherwise
    """
    if not status or not isinstance(status, str):
        return False
    
    if status.strip().lower() != "closed":
        return False
    
    if not resolution or not isinstance(resolution, str):
        # No resolution value: not a valid closed defect
        return False
    
    if resolution.strip() in EXCLUDED_RESOLUTIONS:
        return False
    
    return True


# ============================================================================
# RESOLVED MONTH FORMATTING
# ============================================================================
# Combine Resolved Year and Resolved Month into a YYYY-MM string.

def build_resolved_month(resolved_year, resolved_month) -> str:
    """
    Create a YYYY-MM string from separate year and month columns.
    
    Args:
        resolved_year: Integer or string year (e.g., 2026)
        resolved_month: Integer or string month (e.g., 1, "01", "January")
        
    Returns:
        str: YYYY-MM format string, or empty string if either input is missing/invalid
    """
    if not resolved_year or not resolved_month:
        return ""
    
    try:
        year_int = int(resolved_year)
        month_int = int(resolved_month)
        
        # Validate month is in valid range
        if month_int < 1 or month_int > 12:
            return ""
        
        return f"{year_int:04d}-{month_int:02d}"
    except (ValueError, TypeError):
        return ""


# ============================================================================
# VALID CLUSTER VALUES
# ============================================================================
# These are the only valid cluster categories. Loaded from cluster_mapping.xlsx,
# they are displayed in filters even if currently empty in the data.

VALID_CLUSTERS = ["DSW", "NET", "VAF", "CNT", "Infra", "Unmapped"]


# ============================================================================
# REQUIRED COLUMNS IN ALM EXPORT
# ============================================================================
# These columns are expected in the "QueryResults" sheet of the ALM export.
# If any are missing, the data loader will raise an error.

REQUIRED_ALM_COLUMNS = [
    "Project",
    "Work Item ID",
    "Work Item",
    "URL",
    "Resolution",
    "Resolved Date",
    "Resolved Year",
    "Resolved Month",
    "Creation Date",
    "Creator",
    "Status",
    "Priority",
    "Severity",
    "Planned For",
    "Filed Against",
    "Injection Phase (Custom)",
    "Detection Phase (Custom)",
    "Owner",
]

# ============================================================================
# CLUSTER MAPPING REQUIREMENTS
# ============================================================================
# cluster_mapping.xlsx must have these columns on the "Mapped Cluster" sheet.

REQUIRED_CLUSTER_COLUMNS = ["Filed Against", "Cluster"]

# ============================================================================
# OUTPUT FILES FOR DATA QUALITY / MAPPING GAPS
# ============================================================================

NEEDS_MAPPING_FILE = "needs_mapping.csv"  # Unmapped Product values
NEEDS_CLUSTER_MAPPING_FILE = "needs_cluster_mapping.csv"  # Unmapped Filed Against values
