"""
Financial Data Manager -- core package.

Provides schema management, synthetic data generation, analytical query
execution, data quality checks, and reporting for a financial transaction
data warehouse backed by SQLite.
"""

import os
from pathlib import Path

__version__ = "1.4.0"

# ---------------------------------------------------------------------------
# Resolved paths used throughout the application
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = Path(
    os.environ.get("FDM_DB_PATH", str(PROJECT_ROOT / "data" / "financial.db"))
)

REPORT_DIR = Path(
    os.environ.get("FDM_REPORT_DIR", str(PROJECT_ROOT / "reports"))
)

QUERIES_DIR = PROJECT_ROOT / "queries"

SEED_LOCALE = os.environ.get("FDM_SEED_LOCALE", "en_US")


def ensure_dirs() -> None:
    """Create runtime directories if they do not already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
