"""
BI Dashboard Builder - KPI Calculator

Calculates Key Performance Indicators including totals, averages, growth rates,
period-over-period comparisons, percentiles, variance, and custom formulas.
"""

from typing import Optional
import pandas as pd
import numpy as np


class KPICalculator:
    """Calculate business KPIs from DataFrame data."""

    # -----------------------------------------------------------------------
    # Public Interface
    # -----------------------------------------------------------------------

    def calculate_all(self, df: pd.DataFrame, kpi_configs: list[dict]) -> list[dict]:
        """Calculate all KPIs from a list of configurations."""
        results = []
        for cfg in kpi_configs:
            try:
                result = self.calculate_single(df, cfg)
                results.append(result)
            except Exception as exc:
                results.append({
                    "label": cfg.get("label", "Unknown"),
                    "value": "N/A",
                    "formatted": "N/A",
                    "error": str(exc),
                    "icon": "alert-circle",
                    "trend": "neutral",
                })
        return results

    def calculate_single(self, df: pd.DataFrame, cfg: dict) -> dict:
        """Calculate a single KPI."""
        column = cfg.get("column")
        function = cfg.get("function", "sum")
        label = cfg.get("label", column or "KPI")
        fmt = cfg.get("format", "number")
        compare_periods = cfg.get("compare_periods", True)
        date_column = cfg.get("date_column")

        if column and column not in df.columns:
            return {
                "label": label, "value": 0, "formatted": "N/A",
                "error": f"Column '{column}' not found",
                "icon": "alert-circle", "trend": "neutral",
            }

        # Calculate primary value
        value = self._compute(df, column, function)

        # Calculate comparison (previous period)
        change_pct = None
        change_value = None
        trend = "neutral"
        if compare_periods and column:
            date_col = date_column or self._find_date_column(df)
            if date_col:
                prev_value = self._compute_previous_period(df, date_col, column, function)
                if prev_value is not None and prev_value != 0:
                    change_pct = round(((value - prev_value) / abs(prev_value)) * 100, 1)
                    change_value = round(value - prev_value, 2)
                    trend = "up" if change_pct > 0 else "down" if change_pct < 0 else "neutral"

        # Format the value
        formatted = self._format_value(value, fmt)
        icon = self._get_icon(function, trend)

        return {
            "label": label,
            "value": round(value, 2) if isinstance(value, float) else value,
            "formatted": formatted,
            "change_pct": change_pct,
            "change_value": change_value,
            "trend": trend,
            "icon": icon,
            "format": fmt,
            "function": function,
        }

    # -----------------------------------------------------------------------
    # Computation Functions
    # -----------------------------------------------------------------------

    def _compute(self, df: pd.DataFrame, column: Optional[str], function: str) -> float:
        """Compute a single aggregation function."""
        if function == "count":
            return len(df)

        if function == "unique_count" and column:
            return df[column].nunique()

        if column is None or column not in df.columns:
            return 0

        series = pd.to_numeric(df[column], errors="coerce").dropna()

        func_map = {
            "sum": lambda s: s.sum(),
            "mean": lambda s: s.mean(),
            "avg": lambda s: s.mean(),
            "average": lambda s: s.mean(),
            "median": lambda s: s.median(),
            "min": lambda s: s.min(),
            "max": lambda s: s.max(),
            "std": lambda s: s.std(),
            "var": lambda s: s.var(),
            "range": lambda s: s.max() - s.min(),
            "p25": lambda s: s.quantile(0.25),
            "p75": lambda s: s.quantile(0.75),
            "p90": lambda s: s.quantile(0.90),
            "p95": lambda s: s.quantile(0.95),
            "p99": lambda s: s.quantile(0.99),
            "iqr": lambda s: s.quantile(0.75) - s.quantile(0.25),
            "cv": lambda s: (s.std() / s.mean() * 100) if s.mean() != 0 else 0,
        }

        compute_fn = func_map.get(function, func_map["sum"])

        if len(series) == 0:
            return 0

        result = compute_fn(series)
        return float(result) if not pd.isna(result) else 0

    def _compute_previous_period(
        self, df: pd.DataFrame, date_col: str, value_col: str, function: str
    ) -> Optional[float]:
        """Compute the same function for the previous comparable period."""
        if date_col not in df.columns:
            return None

        dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
        if len(dates) == 0:
            return None

        max_date = dates.max()
        min_date = dates.min()
        total_span = (max_date - min_date).days

        if total_span == 0:
            return None

        # Split at midpoint for comparison
        midpoint = min_date + pd.Timedelta(days=total_span // 2)

        df_temp = df.copy()
        df_temp["_parsed_date"] = pd.to_datetime(df_temp[date_col], errors="coerce")
        previous_df = df_temp[df_temp["_parsed_date"] <= midpoint]

        if len(previous_df) == 0:
            return None

        return self._compute(previous_df, value_col, function)

    # -----------------------------------------------------------------------
    # Advanced KPI Calculations
    # -----------------------------------------------------------------------

    def growth_rate(
        self, df: pd.DataFrame, date_col: str, value_col: str, periods: int = 1
    ) -> dict:
        """Calculate period-over-period growth rate."""
        if date_col not in df.columns or value_col not in df.columns:
            return {"growth_rate": 0, "current": 0, "previous": 0}

        temp = df[[date_col, value_col]].dropna()
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
        temp = temp.dropna().sort_values(date_col)

        monthly = temp.set_index(date_col).resample("M")[value_col].sum()

        if len(monthly) < periods + 1:
            return {"growth_rate": 0, "current": 0, "previous": 0}

        current = monthly.iloc[-1]
        previous = monthly.iloc[-(periods + 1)]

        rate = ((current - previous) / abs(previous) * 100) if previous != 0 else 0

        return {
            "growth_rate": round(rate, 2),
            "current": round(float(current), 2),
            "previous": round(float(previous), 2),
        }

    def moving_average(
        self, df: pd.DataFrame, date_col: str, value_col: str, window: int = 3
    ) -> pd.DataFrame:
        """Calculate moving average over specified window."""
        if date_col not in df.columns or value_col not in df.columns:
            return pd.DataFrame()

        temp = df[[date_col, value_col]].dropna()
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
        temp = temp.dropna().sort_values(date_col)

        monthly = temp.set_index(date_col).resample("M")[value_col].sum().reset_index()
        monthly["moving_avg"] = monthly[value_col].rolling(window=window, min_periods=1).mean()

        return monthly

    def year_over_year(
        self, df: pd.DataFrame, date_col: str, value_col: str
    ) -> dict:
        """Calculate year-over-year comparison."""
        if date_col not in df.columns or value_col not in df.columns:
            return {}

        temp = df[[date_col, value_col]].dropna()
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
        temp = temp.dropna()
        temp["year"] = temp[date_col].dt.year

        yearly = temp.groupby("year")[value_col].sum().reset_index()
        yearly = yearly.sort_values("year")

        result = {}
        for i in range(len(yearly)):
            year = int(yearly.iloc[i]["year"])
            value = float(yearly.iloc[i][value_col])
            yoy_change = None
            if i > 0:
                prev = float(yearly.iloc[i - 1][value_col])
                yoy_change = round(((value - prev) / abs(prev)) * 100, 2) if prev != 0 else 0

            result[year] = {
                "value": round(value, 2),
                "yoy_change": yoy_change,
            }

        return result

    def top_performers(
        self,
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        n: int = 5,
        ascending: bool = False,
    ) -> list[dict]:
        """Get top (or bottom) performers by a metric."""
        if group_col not in df.columns or value_col not in df.columns:
            return []

        grouped = df.groupby(group_col)[value_col].sum().reset_index()
        grouped = grouped.sort_values(value_col, ascending=ascending).head(n)

        total = grouped[value_col].sum()
        result = []
        for _, row in grouped.iterrows():
            val = float(row[value_col])
            result.append({
                "name": str(row[group_col]),
                "value": round(val, 2),
                "share_pct": round((val / total) * 100, 1) if total != 0 else 0,
            })

        return result

    def variance_analysis(
        self,
        df: pd.DataFrame,
        actual_col: str,
        budget_col: Optional[str] = None,
        group_col: Optional[str] = None,
    ) -> dict:
        """Calculate variance between actual and budget/target values."""
        if actual_col not in df.columns:
            return {"error": f"Column '{actual_col}' not found"}

        actual_total = df[actual_col].sum()

        if budget_col and budget_col in df.columns:
            budget_total = df[budget_col].sum()
        else:
            # Use mean as proxy budget
            budget_total = df[actual_col].mean() * len(df)

        variance = actual_total - budget_total
        variance_pct = (variance / abs(budget_total) * 100) if budget_total != 0 else 0

        result = {
            "actual": round(float(actual_total), 2),
            "budget": round(float(budget_total), 2),
            "variance": round(float(variance), 2),
            "variance_pct": round(float(variance_pct), 2),
            "favorable": variance >= 0,
        }

        if group_col and group_col in df.columns:
            breakdown = []
            for name, group in df.groupby(group_col):
                g_actual = group[actual_col].sum()
                g_budget = group[budget_col].sum() if budget_col and budget_col in group.columns else group[actual_col].mean() * len(group)
                g_variance = g_actual - g_budget
                breakdown.append({
                    "group": str(name),
                    "actual": round(float(g_actual), 2),
                    "budget": round(float(g_budget), 2),
                    "variance": round(float(g_variance), 2),
                })
            result["breakdown"] = breakdown

        return result

    def percentile_ranking(
        self, df: pd.DataFrame, column: str, group_col: Optional[str] = None
    ) -> dict:
        """Calculate percentile rankings for values."""
        if column not in df.columns:
            return {}

        series = pd.to_numeric(df[column], errors="coerce").dropna()

        result = {
            "p10": round(float(series.quantile(0.10)), 2),
            "p25": round(float(series.quantile(0.25)), 2),
            "p50": round(float(series.quantile(0.50)), 2),
            "p75": round(float(series.quantile(0.75)), 2),
            "p90": round(float(series.quantile(0.90)), 2),
            "p95": round(float(series.quantile(0.95)), 2),
            "iqr": round(float(series.quantile(0.75) - series.quantile(0.25)), 2),
        }

        return result

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the first date-type column in the DataFrame."""
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return col
        # Heuristic: look for columns with date-like names
        for col in df.columns:
            if any(kw in col.lower() for kw in ["date", "time", "month", "year", "period"]):
                try:
                    pd.to_datetime(df[col].head(5), errors="raise")
                    return col
                except Exception:
                    pass
        return None

    def _format_value(self, value: float, fmt: str) -> str:
        """Format a numeric value for display."""
        if pd.isna(value):
            return "N/A"

        if fmt == "currency":
            if abs(value) >= 1_000_000_000:
                return f"${value / 1_000_000_000:,.1f}B"
            elif abs(value) >= 1_000_000:
                return f"${value / 1_000_000:,.1f}M"
            elif abs(value) >= 1_000:
                return f"${value / 1_000:,.1f}K"
            else:
                return f"${value:,.2f}"

        elif fmt == "percent":
            return f"{value:.1f}%"

        elif fmt == "decimal":
            return f"{value:,.2f}"

        elif fmt == "integer":
            return f"{int(value):,}"

        elif fmt == "compact":
            if abs(value) >= 1_000_000_000:
                return f"{value / 1_000_000_000:.1f}B"
            elif abs(value) >= 1_000_000:
                return f"{value / 1_000_000:.1f}M"
            elif abs(value) >= 1_000:
                return f"{value / 1_000:.1f}K"
            else:
                return f"{value:.0f}"

        else:
            if abs(value) >= 1_000_000:
                return f"{value / 1_000_000:,.1f}M"
            elif abs(value) >= 1_000:
                return f"{value:,.0f}"
            elif isinstance(value, float) and value != int(value):
                return f"{value:,.2f}"
            else:
                return f"{int(value):,}"

    def _get_icon(self, function: str, trend: str) -> str:
        """Return an icon name for the KPI."""
        icon_map = {
            "sum": "bar-chart-2",
            "mean": "trending-up",
            "avg": "trending-up",
            "average": "trending-up",
            "count": "hash",
            "unique_count": "layers",
            "max": "arrow-up-circle",
            "min": "arrow-down-circle",
            "median": "minus-circle",
            "std": "activity",
            "growth": "trending-up",
        }
        return icon_map.get(function, "bar-chart-2")
