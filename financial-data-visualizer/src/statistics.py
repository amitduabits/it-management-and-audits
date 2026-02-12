"""
statistics.py
=============

Financial statistics engine. Computes moving averages, year-over-year
growth rates, variance metrics, percentile distributions, and full
correlation matrices from pandas DataFrames.
"""

import logging
from typing import Optional, List, Dict, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FinancialStatistics:
    """
    Compute descriptive and time-series statistics on a financial DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Source data.
    date_col : str
        Name of the datetime column.
    value_col : str
        Primary numeric column for single-series calculations.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
        value_col: str = "amount",
    ):
        self.df = df.copy()
        self.date_col = date_col
        self.value_col = value_col

        # Ensure date column is datetime
        if date_col in self.df.columns:
            self.df[date_col] = pd.to_datetime(self.df[date_col])
            self.df = self.df.sort_values(date_col).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Moving Averages
    # ------------------------------------------------------------------

    def moving_average(
        self,
        window: int = 30,
        col: Optional[str] = None,
        min_periods: int = 1,
    ) -> pd.Series:
        """
        Simple moving average over a rolling window.

        Parameters
        ----------
        window : int
            Number of periods (default 30).
        col : str, optional
            Column to average; defaults to value_col.
        min_periods : int
            Minimum observations required for a valid result.

        Returns
        -------
        pd.Series
            Moving average values aligned with the original index.
        """
        col = col or self.value_col
        self._assert_column(col)
        return self.df[col].rolling(window=window, min_periods=min_periods).mean()

    def moving_averages_multi(
        self,
        windows: List[int] = None,
        col: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Compute multiple moving averages (default: 7, 30, 90-day).

        Returns a DataFrame with one column per window size, e.g. 'MA_7'.
        """
        if windows is None:
            windows = [7, 30, 90]
        col = col or self.value_col
        self._assert_column(col)

        result = pd.DataFrame(index=self.df.index)
        for w in windows:
            result[f"MA_{w}"] = self.df[col].rolling(window=w, min_periods=1).mean()
        return result

    def exponential_moving_average(
        self,
        span: int = 30,
        col: Optional[str] = None,
    ) -> pd.Series:
        """Exponential moving average with the given span."""
        col = col or self.value_col
        self._assert_column(col)
        return self.df[col].ewm(span=span, adjust=False).mean()

    # ------------------------------------------------------------------
    # Year-over-Year Growth
    # ------------------------------------------------------------------

    def yoy_growth(
        self,
        col: Optional[str] = None,
        freq: str = "M",
    ) -> pd.DataFrame:
        """
        Year-over-year growth rate.

        Resamples data to the given frequency, then computes the percentage
        change compared to the same period in the prior year.

        Parameters
        ----------
        col : str, optional
            Column to measure (defaults to value_col).
        freq : str
            Resample frequency -- 'M' for monthly, 'Q' for quarterly.

        Returns
        -------
        pd.DataFrame
            Columns: 'period_total', 'yoy_growth_pct'.
        """
        col = col or self.value_col
        self._assert_column(col)

        ts = self.df.set_index(self.date_col)[col].resample(freq).sum()
        growth = ts.pct_change(periods=12 if freq == "M" else 4) * 100

        result = pd.DataFrame({"period_total": ts, "yoy_growth_pct": growth})
        return result

    # ------------------------------------------------------------------
    # Variance and Volatility
    # ------------------------------------------------------------------

    def variance(self, col: Optional[str] = None) -> float:
        """Population variance of the specified column."""
        col = col or self.value_col
        self._assert_column(col)
        return float(self.df[col].var(ddof=0))

    def std_deviation(self, col: Optional[str] = None) -> float:
        """Sample standard deviation."""
        col = col or self.value_col
        self._assert_column(col)
        return float(self.df[col].std(ddof=1))

    def rolling_volatility(
        self,
        window: int = 30,
        col: Optional[str] = None,
    ) -> pd.Series:
        """
        Annualized rolling volatility (standard deviation * sqrt(252)).
        Useful for daily market data.
        """
        col = col or self.value_col
        self._assert_column(col)
        returns = self.df[col].pct_change().dropna()
        rolling_std = returns.rolling(window=window, min_periods=window).std()
        return rolling_std * np.sqrt(252)

    # ------------------------------------------------------------------
    # Percentiles
    # ------------------------------------------------------------------

    def percentiles(
        self,
        col: Optional[str] = None,
        quantiles: Optional[List[float]] = None,
    ) -> Dict[str, float]:
        """
        Compute percentile values for a numeric column.

        Parameters
        ----------
        col : str, optional
        quantiles : list of float
            Percentile thresholds between 0 and 1. Default: common set.

        Returns
        -------
        dict
            Mapping of percentile label to value.
        """
        col = col or self.value_col
        self._assert_column(col)
        if quantiles is None:
            quantiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]

        series = self.df[col].dropna()
        return {
            f"P{int(q * 100)}": float(series.quantile(q))
            for q in quantiles
        }

    # ------------------------------------------------------------------
    # Correlation Matrix
    # ------------------------------------------------------------------

    def correlation_matrix(
        self,
        columns: Optional[List[str]] = None,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """
        Compute a correlation matrix for the selected numeric columns.

        Parameters
        ----------
        columns : list of str, optional
            Columns to include. If None, all numeric columns are used.
        method : str
            Correlation method: 'pearson', 'kendall', or 'spearman'.

        Returns
        -------
        pd.DataFrame
            Symmetric correlation matrix.
        """
        if columns:
            subset = self.df[columns]
        else:
            subset = self.df.select_dtypes(include=[np.number])

        if subset.empty:
            logger.warning("No numeric columns found for correlation.")
            return pd.DataFrame()

        return subset.corr(method=method)

    # ------------------------------------------------------------------
    # Aggregate Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict:
        """
        Return a comprehensive statistical summary.

        Includes count, mean, median, std, min, max, percentiles,
        and moving average snapshots.
        """
        col = self.value_col
        self._assert_column(col)
        series = self.df[col].dropna()

        return {
            "count": int(series.count()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "variance": self.variance(col),
            "percentiles": self.percentiles(col),
            "date_range": {
                "start": str(self.df[self.date_col].min()) if self.date_col in self.df.columns else None,
                "end": str(self.df[self.date_col].max()) if self.date_col in self.df.columns else None,
            },
        }

    # ------------------------------------------------------------------
    # Monthly and Daily Aggregation
    # ------------------------------------------------------------------

    def monthly_totals(self, col: Optional[str] = None) -> pd.Series:
        """Resample to monthly totals."""
        col = col or self.value_col
        self._assert_column(col)
        return self.df.set_index(self.date_col)[col].resample("M").sum()

    def daily_totals(self, col: Optional[str] = None) -> pd.Series:
        """Resample to daily totals."""
        col = col or self.value_col
        self._assert_column(col)
        return self.df.set_index(self.date_col)[col].resample("D").sum()

    def category_breakdown(
        self,
        category_col: str = "category",
        value_col: Optional[str] = None,
        agg: str = "sum",
    ) -> pd.Series:
        """Aggregate by category."""
        value_col = value_col or self.value_col
        self._assert_column(category_col)
        self._assert_column(value_col)
        return self.df.groupby(category_col)[value_col].agg(agg).sort_values(ascending=False)

    # ------------------------------------------------------------------
    # Outlier Detection
    # ------------------------------------------------------------------

    def detect_outliers_iqr(
        self,
        col: Optional[str] = None,
        factor: float = 1.5,
    ) -> pd.DataFrame:
        """
        Detect outliers using the IQR method.

        Returns a DataFrame containing only the outlier rows.
        """
        col = col or self.value_col
        self._assert_column(col)

        q1 = self.df[col].quantile(0.25)
        q3 = self.df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        mask = (self.df[col] < lower) | (self.df[col] > upper)
        outliers = self.df[mask].copy()
        outliers["outlier_direction"] = np.where(
            outliers[col] < lower, "below", "above"
        )
        return outliers

    def detect_outliers_zscore(
        self,
        col: Optional[str] = None,
        threshold: float = 3.0,
    ) -> pd.DataFrame:
        """
        Detect outliers using the Z-score method.

        Returns rows where the absolute Z-score exceeds the threshold.
        """
        col = col or self.value_col
        self._assert_column(col)

        series = self.df[col]
        z_scores = (series - series.mean()) / series.std()
        mask = z_scores.abs() > threshold

        outliers = self.df[mask].copy()
        outliers["z_score"] = z_scores[mask]
        return outliers

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_column(self, col: str) -> None:
        if col not in self.df.columns:
            raise KeyError(
                f"Column '{col}' not found. Available: {list(self.df.columns)}"
            )
