"""
BI Dashboard Builder - Data Processor

Handles CSV/XLSX/JSON file loading, column type detection, data cleaning,
aggregation engine, and automatic dashboard configuration based on data shape.
"""

import os
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np


class DataProcessor:
    """Core data processing engine for the BI Dashboard Builder."""

    # Column-type classification thresholds
    CATEGORY_UNIQUE_RATIO = 0.05   # If unique/total < 5%, treat as categorical
    CATEGORY_MAX_UNIQUE = 50       # Max unique values to still consider categorical
    DATE_FORMATS = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S",
        "%Y/%m/%d", "%d-%m-%Y", "%B %Y", "%b %Y",
        "%Y-%m", "%Y",
    ]

    # -----------------------------------------------------------------------
    # File Loading
    # -----------------------------------------------------------------------

    def load_file(self, file_path: str) -> pd.DataFrame:
        """Load a data file into a pandas DataFrame."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            df = self._load_csv(file_path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        df = self._clean_dataframe(df)
        return df

    def _load_csv(self, path: str) -> pd.DataFrame:
        """Load CSV with automatic delimiter and encoding detection."""
        for encoding in ("utf-8", "latin-1", "cp1252"):
            for sep in (",", ";", "\t", "|"):
                try:
                    df = pd.read_csv(path, encoding=encoding, sep=sep)
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
        # Fallback
        return pd.read_csv(path)

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean column names, strip whitespace, parse dates."""
        # Normalize column names
        df.columns = [
            str(c).strip().lower().replace(" ", "_").replace("-", "_")
            for c in df.columns
        ]

        # Strip string whitespace
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()

        # Try to parse date columns
        for col in df.columns:
            if df[col].dtype == object:
                parsed = self._try_parse_date(df[col])
                if parsed is not None:
                    df[col] = parsed

        return df

    def _try_parse_date(self, series: pd.Series) -> Optional[pd.Series]:
        """Attempt to parse a string series as datetime."""
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return None

        for fmt in self.DATE_FORMATS:
            try:
                parsed = pd.to_datetime(sample, format=fmt)
                if parsed.notna().sum() >= len(sample) * 0.8:
                    return pd.to_datetime(series, format=fmt, errors="coerce")
            except (ValueError, TypeError):
                continue

        # Generic parse attempt
        try:
            result = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
            if result.notna().sum() >= len(series) * 0.5:
                return result
        except Exception:
            pass

        return None

    # -----------------------------------------------------------------------
    # Column Type Detection
    # -----------------------------------------------------------------------

    def detect_column_types(self, df: pd.DataFrame) -> dict:
        """Classify each column as numeric, categorical, date, or text."""
        types = {}
        for col in df.columns:
            types[col] = self._classify_column(df[col], len(df))
        return types

    def _classify_column(self, series: pd.Series, total_rows: int) -> str:
        """Classify a single column."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return "date"

        if pd.api.types.is_numeric_dtype(series):
            n_unique = series.nunique()
            if n_unique <= 10 and n_unique / max(total_rows, 1) < self.CATEGORY_UNIQUE_RATIO:
                return "categorical"
            return "numeric"

        if series.dtype == object:
            n_unique = series.nunique()
            if n_unique <= self.CATEGORY_MAX_UNIQUE:
                return "categorical"
            return "text"

        return "text"

    # -----------------------------------------------------------------------
    # Summary & Metadata
    # -----------------------------------------------------------------------

    def get_summary(self, df: pd.DataFrame) -> dict:
        """Generate a comprehensive summary of the dataset."""
        col_types = self.detect_column_types(df)
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        cat_cols = [c for c, t in col_types.items() if t == "categorical"]
        date_cols = [c for c, t in col_types.items() if t == "date"]

        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "column_types": col_types,
            "numeric_columns": numeric_cols,
            "categorical_columns": cat_cols,
            "date_columns": date_cols,
            "missing_values": df.isnull().sum().to_dict(),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1_048_576, 2),
        }

        # Numeric stats
        if numeric_cols:
            desc = df[numeric_cols].describe().to_dict()
            summary["numeric_stats"] = {
                col: {k: round(v, 2) if isinstance(v, float) else v for k, v in stats.items()}
                for col, stats in desc.items()
            }

        # Categorical value counts (top 10)
        summary["categorical_values"] = {}
        for col in cat_cols:
            vc = df[col].value_counts().head(10)
            summary["categorical_values"][col] = vc.to_dict()

        # Date range
        for col in date_cols:
            valid = df[col].dropna()
            if len(valid) > 0:
                summary[f"date_range_{col}"] = {
                    "min": str(valid.min()),
                    "max": str(valid.max()),
                }

        return summary

    # -----------------------------------------------------------------------
    # Aggregation Engine
    # -----------------------------------------------------------------------

    def aggregate(
        self,
        df: pd.DataFrame,
        group_by: str | list[str],
        agg_column: str,
        agg_func: str = "sum",
        sort: bool = True,
        top_n: Optional[int] = None,
    ) -> pd.DataFrame:
        """Aggregate data by grouping column(s) with a specified function."""
        if isinstance(group_by, str):
            group_by = [group_by]

        valid_cols = [c for c in group_by if c in df.columns]
        if not valid_cols or agg_column not in df.columns:
            return pd.DataFrame()

        func_map = {
            "sum": "sum",
            "mean": "mean",
            "avg": "mean",
            "average": "mean",
            "count": "count",
            "min": "min",
            "max": "max",
            "median": "median",
            "std": "std",
        }
        pandas_func = func_map.get(agg_func.lower(), "sum")

        grouped = df.groupby(valid_cols, dropna=False)[agg_column].agg(pandas_func).reset_index()
        grouped.columns = valid_cols + [f"{agg_column}_{pandas_func}"]

        if sort:
            grouped = grouped.sort_values(
                grouped.columns[-1], ascending=False
            ).reset_index(drop=True)

        if top_n:
            grouped = grouped.head(top_n)

        return grouped

    def time_series_aggregate(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        freq: str = "M",
        agg_func: str = "sum",
    ) -> pd.DataFrame:
        """Aggregate data by time period."""
        if date_col not in df.columns or value_col not in df.columns:
            return pd.DataFrame()

        temp = df[[date_col, value_col]].dropna()
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
        temp = temp.dropna()

        temp = temp.set_index(date_col)
        resampled = temp.resample(freq).agg(agg_func).reset_index()
        return resampled

    def pivot_data(
        self,
        df: pd.DataFrame,
        index_col: str,
        columns_col: str,
        values_col: str,
        agg_func: str = "sum",
    ) -> pd.DataFrame:
        """Create a pivot table from the data."""
        if not all(c in df.columns for c in [index_col, columns_col, values_col]):
            return pd.DataFrame()

        pivot = pd.pivot_table(
            df,
            index=index_col,
            columns=columns_col,
            values=values_col,
            aggfunc=agg_func,
            fill_value=0,
        )
        return pivot.reset_index()

    # -----------------------------------------------------------------------
    # Filter Options
    # -----------------------------------------------------------------------

    def get_filter_options(self, df: pd.DataFrame) -> dict:
        """Get available filter values for categorical and date columns."""
        col_types = self.detect_column_types(df)
        filters = {}

        for col, ctype in col_types.items():
            if ctype == "categorical":
                unique_vals = sorted(df[col].dropna().unique().tolist())
                if len(unique_vals) <= 100:
                    filters[col] = {
                        "type": "select",
                        "values": unique_vals,
                        "label": col.replace("_", " ").title(),
                    }
            elif ctype == "date":
                valid = df[col].dropna()
                if len(valid) > 0:
                    filters[col] = {
                        "type": "date_range",
                        "min": str(valid.min().date()) if hasattr(valid.min(), "date") else str(valid.min()),
                        "max": str(valid.max().date()) if hasattr(valid.max(), "date") else str(valid.max()),
                        "label": col.replace("_", " ").title(),
                    }

        return filters

    # -----------------------------------------------------------------------
    # Auto-Configuration
    # -----------------------------------------------------------------------

    def auto_configure(self, df: pd.DataFrame) -> dict:
        """Automatically build a dashboard configuration from data shape."""
        col_types = self.detect_column_types(df)
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        cat_cols = [c for c, t in col_types.items() if t == "categorical"]
        date_cols = [c for c, t in col_types.items() if t == "date"]

        config = {
            "title": "Auto-Generated Dashboard",
            "description": f"Dashboard built from {len(df)} records across {len(df.columns)} columns",
            "kpis": [],
            "charts": [],
        }

        # KPIs for each numeric column
        for col in numeric_cols[:6]:
            config["kpis"].append({
                "label": col.replace("_", " ").title(),
                "column": col,
                "function": "sum",
                "format": "currency" if any(kw in col for kw in ["amount", "revenue", "price", "cost", "profit", "salary"]) else "number",
            })
            config["kpis"].append({
                "label": f"Avg {col.replace('_', ' ').title()}",
                "column": col,
                "function": "mean",
                "format": "decimal",
            })

        # Limit to 8 KPI cards
        config["kpis"] = config["kpis"][:8]

        # Time series chart if date column exists
        if date_cols and numeric_cols:
            config["charts"].append({
                "type": "line",
                "title": f"{numeric_cols[0].replace('_', ' ').title()} Over Time",
                "x": date_cols[0],
                "y": numeric_cols[0],
                "agg": "sum",
                "color_scheme": "blue",
            })

        # Bar chart for categorical breakdowns
        if cat_cols and numeric_cols:
            config["charts"].append({
                "type": "bar",
                "title": f"{numeric_cols[0].replace('_', ' ').title()} by {cat_cols[0].replace('_', ' ').title()}",
                "x": cat_cols[0],
                "y": numeric_cols[0],
                "agg": "sum",
                "color_scheme": "viridis",
            })

        # Pie chart for first categorical
        if cat_cols and numeric_cols:
            config["charts"].append({
                "type": "pie",
                "title": f"{cat_cols[0].replace('_', ' ').title()} Distribution",
                "labels": cat_cols[0],
                "values": numeric_cols[0],
                "agg": "sum",
            })

        # Scatter if 2+ numeric columns
        if len(numeric_cols) >= 2:
            config["charts"].append({
                "type": "scatter",
                "title": f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()}",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "color": cat_cols[0] if cat_cols else None,
            })

        # Stacked bar if 2 categorical + numeric
        if len(cat_cols) >= 2 and numeric_cols:
            config["charts"].append({
                "type": "stacked_bar",
                "title": f"{numeric_cols[0].replace('_', ' ').title()} by {cat_cols[0].replace('_', ' ').title()} and {cat_cols[1].replace('_', ' ').title()}",
                "x": cat_cols[0],
                "y": numeric_cols[0],
                "stack_by": cat_cols[1],
                "agg": "sum",
            })

        # Heatmap if date + categorical + numeric
        if date_cols and cat_cols and numeric_cols:
            config["charts"].append({
                "type": "heatmap",
                "title": f"{numeric_cols[0].replace('_', ' ').title()} Heatmap",
                "x": date_cols[0],
                "y": cat_cols[0],
                "values": numeric_cols[0],
                "agg": "sum",
            })

        return config
