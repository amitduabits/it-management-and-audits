"""
test_statistics.py
==================

Unit tests for src.statistics.FinancialStatistics.
Covers moving averages, YoY growth, variance, percentiles,
correlation matrices, and outlier detection.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.statistics import FinancialStatistics


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_transactions():
    """Create a synthetic transactions DataFrame for testing."""
    np.random.seed(0)
    n = 500
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    amounts = np.random.normal(loc=-75, scale=150, size=n)
    categories = np.random.choice(
        ["Groceries", "Dining", "Shopping", "Utilities", "Entertainment"],
        size=n,
    )
    return pd.DataFrame({
        "date": dates[:n],
        "amount": amounts,
        "category": categories,
        "merchant": ["Merchant_" + str(i % 20) for i in range(n)],
        "type": np.where(amounts >= 0, "credit", "debit"),
    })


@pytest.fixture
def sample_market_data():
    """Create synthetic market data with known price series."""
    np.random.seed(42)
    n = 252
    dates = pd.bdate_range("2025-01-01", periods=n)
    prices = 150 + np.cumsum(np.random.normal(0.1, 2, size=n))

    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": prices + np.abs(np.random.normal(1, 0.5, n)),
        "low": prices - np.abs(np.random.normal(1, 0.5, n)),
        "close": prices + np.random.normal(0, 1, n),
        "volume": np.random.randint(2_000_000, 8_000_000, n),
    })
    return df


@pytest.fixture
def sample_revenue():
    """Create a simple monthly revenue/expense DataFrame."""
    months = pd.date_range("2023-01-01", periods=36, freq="MS")
    np.random.seed(7)
    revenue = 850_000 * (1.015 ** np.arange(36)) + np.random.normal(0, 20_000, 36)
    cogs = revenue * np.random.uniform(0.35, 0.45, 36)
    return pd.DataFrame({
        "date": months,
        "revenue": revenue,
        "cogs": cogs,
        "operating_expenses": revenue * 0.18,
        "net_income": revenue - cogs - revenue * 0.18,
    })


@pytest.fixture
def stats_txn(sample_transactions):
    return FinancialStatistics(sample_transactions, date_col="date", value_col="amount")


@pytest.fixture
def stats_market(sample_market_data):
    return FinancialStatistics(sample_market_data, date_col="date", value_col="close")


@pytest.fixture
def stats_revenue(sample_revenue):
    return FinancialStatistics(sample_revenue, date_col="date", value_col="revenue")


# ------------------------------------------------------------------
# Moving Averages
# ------------------------------------------------------------------

class TestMovingAverages:

    def test_moving_average_returns_series(self, stats_txn):
        ma = stats_txn.moving_average(window=7)
        assert isinstance(ma, pd.Series)
        assert len(ma) == len(stats_txn.df)

    def test_moving_average_window_30(self, stats_txn):
        ma = stats_txn.moving_average(window=30)
        # First 29 values should still have results due to min_periods=1
        assert not ma.isna().all()

    def test_moving_averages_multi_default_windows(self, stats_txn):
        result = stats_txn.moving_averages_multi()
        assert isinstance(result, pd.DataFrame)
        assert "MA_7" in result.columns
        assert "MA_30" in result.columns
        assert "MA_90" in result.columns

    def test_moving_averages_multi_custom_windows(self, stats_txn):
        result = stats_txn.moving_averages_multi(windows=[5, 10, 20])
        assert "MA_5" in result.columns
        assert "MA_10" in result.columns
        assert "MA_20" in result.columns

    def test_exponential_moving_average(self, stats_market):
        ema = stats_market.exponential_moving_average(span=20)
        assert isinstance(ema, pd.Series)
        assert len(ema) == len(stats_market.df)
        # EMA should not have NaN values (no min_periods needed)
        assert not ema.isna().any()

    def test_moving_average_smoothing(self, stats_txn):
        """MA values should be smoother (lower std) than raw values."""
        raw_std = stats_txn.df["amount"].std()
        ma = stats_txn.moving_average(window=30)
        ma_std = ma.dropna().std()
        assert ma_std < raw_std


# ------------------------------------------------------------------
# Year-over-Year Growth
# ------------------------------------------------------------------

class TestYoYGrowth:

    def test_yoy_growth_returns_dataframe(self, stats_revenue):
        result = stats_revenue.yoy_growth(col="revenue", freq="M")
        assert isinstance(result, pd.DataFrame)
        assert "period_total" in result.columns
        assert "yoy_growth_pct" in result.columns

    def test_yoy_growth_first_year_is_nan(self, stats_revenue):
        result = stats_revenue.yoy_growth(col="revenue", freq="M")
        # First 12 months should have NaN growth (no prior year)
        assert result["yoy_growth_pct"].iloc[:12].isna().all()

    def test_yoy_growth_has_values_after_first_year(self, stats_revenue):
        result = stats_revenue.yoy_growth(col="revenue", freq="M")
        valid = result["yoy_growth_pct"].dropna()
        assert len(valid) > 0

    def test_yoy_growth_positive_for_growing_revenue(self, stats_revenue):
        result = stats_revenue.yoy_growth(col="revenue", freq="M")
        valid = result["yoy_growth_pct"].dropna()
        # Most months should show positive growth given 1.5% monthly growth
        assert (valid > 0).sum() > len(valid) * 0.5


# ------------------------------------------------------------------
# Variance and Volatility
# ------------------------------------------------------------------

class TestVariance:

    def test_variance_returns_float(self, stats_txn):
        var = stats_txn.variance()
        assert isinstance(var, float)
        assert var >= 0

    def test_std_deviation_returns_float(self, stats_txn):
        std = stats_txn.std_deviation()
        assert isinstance(std, float)
        assert std >= 0

    def test_variance_matches_std_squared(self, stats_txn):
        """Population variance should approximately equal std^2."""
        var = stats_txn.variance()
        std = stats_txn.std_deviation()
        # Note: variance uses ddof=0, std uses ddof=1, so not exact match
        n = len(stats_txn.df)
        expected_var = std ** 2 * (n - 1) / n
        assert abs(var - expected_var) < 1.0

    def test_rolling_volatility(self, stats_market):
        vol = stats_market.rolling_volatility(window=30)
        assert isinstance(vol, pd.Series)
        # Values should be annualized (typically 10-50% range)
        valid = vol.dropna()
        assert len(valid) > 0


# ------------------------------------------------------------------
# Percentiles
# ------------------------------------------------------------------

class TestPercentiles:

    def test_percentiles_returns_dict(self, stats_txn):
        result = stats_txn.percentiles()
        assert isinstance(result, dict)
        assert "P50" in result  # median

    def test_percentiles_default_keys(self, stats_txn):
        result = stats_txn.percentiles()
        expected_keys = {"P5", "P10", "P25", "P50", "P75", "P90", "P95"}
        assert expected_keys == set(result.keys())

    def test_percentiles_custom_quantiles(self, stats_txn):
        result = stats_txn.percentiles(quantiles=[0.1, 0.5, 0.9])
        assert len(result) == 3
        assert "P10" in result
        assert "P50" in result
        assert "P90" in result

    def test_percentiles_ordered(self, stats_txn):
        result = stats_txn.percentiles()
        assert result["P5"] <= result["P25"] <= result["P50"]
        assert result["P50"] <= result["P75"] <= result["P95"]

    def test_p50_matches_median(self, stats_txn):
        result = stats_txn.percentiles()
        median = stats_txn.df["amount"].median()
        assert abs(result["P50"] - median) < 0.01


# ------------------------------------------------------------------
# Correlation Matrix
# ------------------------------------------------------------------

class TestCorrelationMatrix:

    def test_correlation_matrix_shape(self, stats_revenue):
        corr = stats_revenue.correlation_matrix()
        assert isinstance(corr, pd.DataFrame)
        n_numeric = len(stats_revenue.df.select_dtypes(include=[np.number]).columns)
        assert corr.shape == (n_numeric, n_numeric)

    def test_correlation_diagonal_is_one(self, stats_revenue):
        corr = stats_revenue.correlation_matrix()
        for col in corr.columns:
            assert abs(corr.loc[col, col] - 1.0) < 1e-10

    def test_correlation_symmetric(self, stats_revenue):
        corr = stats_revenue.correlation_matrix()
        assert np.allclose(corr.values, corr.values.T, atol=1e-10)

    def test_correlation_bounds(self, stats_revenue):
        corr = stats_revenue.correlation_matrix()
        assert (corr >= -1.0).all().all()
        assert (corr <= 1.0).all().all()

    def test_correlation_selected_columns(self, stats_revenue):
        cols = ["revenue", "cogs"]
        corr = stats_revenue.correlation_matrix(columns=cols)
        assert corr.shape == (2, 2)

    def test_correlation_method_spearman(self, stats_revenue):
        corr = stats_revenue.correlation_matrix(method="spearman")
        assert isinstance(corr, pd.DataFrame)


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

class TestSummary:

    def test_summary_returns_dict(self, stats_txn):
        result = stats_txn.summary()
        assert isinstance(result, dict)

    def test_summary_keys(self, stats_txn):
        result = stats_txn.summary()
        expected = {"count", "mean", "median", "std", "min", "max",
                    "variance", "percentiles", "date_range"}
        assert expected.issubset(set(result.keys()))

    def test_summary_count_matches(self, stats_txn):
        result = stats_txn.summary()
        assert result["count"] == len(stats_txn.df)

    def test_summary_min_max_bounds(self, stats_txn):
        result = stats_txn.summary()
        assert result["min"] <= result["mean"] <= result["max"]


# ------------------------------------------------------------------
# Outlier Detection
# ------------------------------------------------------------------

class TestOutlierDetection:

    def test_iqr_outliers_returns_dataframe(self, stats_txn):
        outliers = stats_txn.detect_outliers_iqr()
        assert isinstance(outliers, pd.DataFrame)
        assert "outlier_direction" in outliers.columns

    def test_iqr_outliers_are_extreme(self, stats_txn):
        outliers = stats_txn.detect_outliers_iqr()
        if not outliers.empty:
            q1 = stats_txn.df["amount"].quantile(0.25)
            q3 = stats_txn.df["amount"].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            assert ((outliers["amount"] < lower) | (outliers["amount"] > upper)).all()

    def test_zscore_outliers_returns_dataframe(self, stats_txn):
        outliers = stats_txn.detect_outliers_zscore()
        assert isinstance(outliers, pd.DataFrame)
        assert "z_score" in outliers.columns

    def test_zscore_outliers_exceed_threshold(self, stats_txn):
        threshold = 3.0
        outliers = stats_txn.detect_outliers_zscore(threshold=threshold)
        if not outliers.empty:
            assert (outliers["z_score"].abs() > threshold).all()

    def test_stricter_threshold_fewer_outliers(self, stats_txn):
        mild = stats_txn.detect_outliers_iqr(factor=1.5)
        strict = stats_txn.detect_outliers_iqr(factor=3.0)
        assert len(strict) <= len(mild)


# ------------------------------------------------------------------
# Aggregation
# ------------------------------------------------------------------

class TestAggregation:

    def test_monthly_totals(self, stats_txn):
        monthly = stats_txn.monthly_totals()
        assert isinstance(monthly, pd.Series)
        assert len(monthly) > 0

    def test_daily_totals(self, stats_txn):
        daily = stats_txn.daily_totals()
        assert isinstance(daily, pd.Series)

    def test_category_breakdown(self, stats_txn):
        breakdown = stats_txn.category_breakdown()
        assert isinstance(breakdown, pd.Series)
        assert len(breakdown) == 5  # 5 categories in fixture


# ------------------------------------------------------------------
# Error Handling
# ------------------------------------------------------------------

class TestErrorHandling:

    def test_missing_column_raises_keyerror(self, stats_txn):
        with pytest.raises(KeyError):
            stats_txn.moving_average(col="nonexistent_column")

    def test_missing_value_col_raises_keyerror(self, sample_transactions):
        stats = FinancialStatistics(
            sample_transactions, date_col="date", value_col="missing"
        )
        with pytest.raises(KeyError):
            stats.summary()
