"""
data_loader.py
==============

Robust financial data ingestion module. Loads CSV and JSON files into
pandas DataFrames with comprehensive validation, type coercion, and
error reporting. Supports transaction records, market OHLCV data, and
revenue/expense datasets.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Union

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Expected schemas for each dataset type
# ---------------------------------------------------------------------------

SCHEMAS: Dict[str, Dict[str, str]] = {
    "transactions": {
        "date": "datetime64[ns]",
        "amount": "float64",
        "category": "object",
        "merchant": "object",
        "type": "object",
    },
    "market_data": {
        "date": "datetime64[ns]",
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "int64",
    },
    "revenue_expenses": {
        "date": "datetime64[ns]",
        "revenue": "float64",
        "cogs": "float64",
        "operating_expenses": "float64",
        "marketing": "float64",
        "salaries": "float64",
        "rent": "float64",
        "utilities": "float64",
        "net_income": "float64",
    },
}


class DataValidationError(Exception):
    """Raised when loaded data fails schema or integrity checks."""
    pass


class DataLoader:
    """
    Load, validate, and pre-process financial datasets.

    Parameters
    ----------
    date_format : str, optional
        Expected date format string for parsing (default: ISO 8601).
    strict : bool
        If True, raise on any validation warning; if False, log warnings
        and attempt best-effort coercion.
    """

    def __init__(self, date_format: Optional[str] = None, strict: bool = False):
        self.date_format = date_format
        self.strict = strict
        self._loaded: Dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_csv(
        self,
        filepath: Union[str, Path],
        schema: Optional[str] = None,
        date_col: str = "date",
        encoding: str = "utf-8",
    ) -> pd.DataFrame:
        """
        Load a CSV file into a DataFrame with optional schema validation.

        Parameters
        ----------
        filepath : str or Path
            Path to the CSV file.
        schema : str, optional
            One of 'transactions', 'market_data', 'revenue_expenses'.
            If provided, validates and coerces columns to the expected types.
        date_col : str
            Name of the date column to parse.
        encoding : str
            File encoding (default utf-8).

        Returns
        -------
        pd.DataFrame
            Cleaned and validated DataFrame sorted by date.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        DataValidationError
            If required columns are missing or data cannot be coerced.
        """
        filepath = Path(filepath)
        self._assert_file_exists(filepath)
        logger.info("Loading CSV: %s", filepath)

        try:
            df = pd.read_csv(filepath, encoding=encoding)
        except pd.errors.ParserError as exc:
            raise DataValidationError(f"CSV parsing failed: {exc}") from exc

        df = self._normalize_columns(df)
        df = self._parse_dates(df, date_col)

        if schema:
            df = self._validate_schema(df, schema)

        df = self._clean(df, date_col)
        self._loaded[filepath.stem] = df
        logger.info("Loaded %d rows from %s", len(df), filepath.name)
        return df

    def load_json(
        self,
        filepath: Union[str, Path],
        schema: Optional[str] = None,
        date_col: str = "date",
    ) -> pd.DataFrame:
        """
        Load a JSON file (records-oriented or columnar) into a DataFrame.

        Parameters
        ----------
        filepath : str or Path
            Path to the JSON file.
        schema : str, optional
            Schema name for validation.
        date_col : str
            Date column name.

        Returns
        -------
        pd.DataFrame
        """
        filepath = Path(filepath)
        self._assert_file_exists(filepath)
        logger.info("Loading JSON: %s", filepath)

        with open(filepath, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

        if isinstance(raw, list):
            df = pd.DataFrame(raw)
        elif isinstance(raw, dict):
            df = pd.DataFrame(raw)
        else:
            raise DataValidationError("JSON root must be an array or object.")

        df = self._normalize_columns(df)
        df = self._parse_dates(df, date_col)

        if schema:
            df = self._validate_schema(df, schema)

        df = self._clean(df, date_col)
        self._loaded[filepath.stem] = df
        logger.info("Loaded %d rows from %s", len(df), filepath.name)
        return df

    def load_directory(self, dirpath: Union[str, Path]) -> Dict[str, pd.DataFrame]:
        """
        Load all recognized CSV files from a directory.

        Looks for transactions.csv, market_data.csv, and revenue_expenses.csv.
        Returns a dict mapping dataset name to DataFrame.
        """
        dirpath = Path(dirpath)
        if not dirpath.is_dir():
            raise FileNotFoundError(f"Directory not found: {dirpath}")

        results: Dict[str, pd.DataFrame] = {}
        known_files = {
            "transactions.csv": "transactions",
            "market_data.csv": "market_data",
            "revenue_expenses.csv": "revenue_expenses",
        }

        for filename, schema_name in known_files.items():
            fpath = dirpath / filename
            if fpath.exists():
                results[schema_name] = self.load_csv(fpath, schema=schema_name)
            else:
                logger.warning("Expected file not found: %s", fpath)

        return results

    def get_summary(self, df: pd.DataFrame) -> Dict:
        """Return a quick statistical summary of a numeric DataFrame."""
        numeric = df.select_dtypes(include=[np.number])
        return {
            "rows": len(df),
            "columns": list(df.columns),
            "numeric_columns": list(numeric.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "describe": numeric.describe().to_dict(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_file_exists(filepath: Path) -> None:
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        if not filepath.is_file():
            raise FileNotFoundError(f"Path is not a file: {filepath}")

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Lowercase and strip whitespace from column names."""
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df

    def _parse_dates(self, df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Attempt to parse the date column into datetime."""
        if date_col not in df.columns:
            logger.warning("Date column '%s' not found; skipping parse.", date_col)
            return df
        try:
            if self.date_format:
                df[date_col] = pd.to_datetime(df[date_col], format=self.date_format)
            else:
                df[date_col] = pd.to_datetime(df[date_col], infer_datetime_format=True)
        except (ValueError, TypeError) as exc:
            msg = f"Failed to parse dates in column '{date_col}': {exc}"
            if self.strict:
                raise DataValidationError(msg) from exc
            logger.warning(msg)
        return df

    def _validate_schema(self, df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
        """Validate that required columns exist and coerce types."""
        if schema_name not in SCHEMAS:
            raise DataValidationError(f"Unknown schema: {schema_name}")

        expected = SCHEMAS[schema_name]
        missing = [col for col in expected if col not in df.columns]
        if missing:
            msg = f"Missing required columns for '{schema_name}': {missing}"
            if self.strict:
                raise DataValidationError(msg)
            logger.warning(msg)

        for col, dtype in expected.items():
            if col not in df.columns:
                continue
            if dtype == "datetime64[ns]":
                continue  # already handled by _parse_dates
            try:
                df[col] = df[col].astype(dtype)
            except (ValueError, TypeError) as exc:
                msg = f"Cannot coerce column '{col}' to {dtype}: {exc}"
                if self.strict:
                    raise DataValidationError(msg) from exc
                logger.warning(msg)

        return df

    @staticmethod
    def _clean(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Drop fully-empty rows and sort by date if available."""
        df = df.dropna(how="all")
        if date_col in df.columns:
            df = df.sort_values(date_col).reset_index(drop=True)
        return df
