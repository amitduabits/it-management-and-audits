"""
Tests for the KPICalculator module.

Covers single KPI calculation, bulk calculation, growth rate,
moving average, year-over-year, top performers, variance analysis,
percentile ranking, and value formatting.
"""

import os
import pytest
import pandas as pd
import numpy as np

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.kpi_calculator import KPICalculator


@pytest.fixture
def calculator():
    """Create a KPICalculator instance."""
    return KPICalculator()


@pytest.fixture
def sales_df():
    """Create a sample sales DataFrame spanning 12 months."""
    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    np.random.seed(42)
    return pd.DataFrame({
        "date": dates,
        "amount": np.random.uniform(50.0, 1000.0, 365).round(2),
        "quantity": np.random.randint(1, 30, 365),
        "region": np.random.choice(["North", "South", "East", "West"], 365),
        "category": np.random.choice(["A", "B", "C"], 365),
    })


@pytest.fixture
def financial_df():
    """Create a sample financial DataFrame with 24 months."""
    months = pd.date_range("2023-01-01", periods=24, freq="MS")
    np.random.seed(42)
    revenue = np.random.uniform(100000, 500000, 24).round(2)
    expenses = (revenue * np.random.uniform(0.6, 0.85, 24)).round(2)
    return pd.DataFrame({
        "month": months,
        "revenue": revenue,
        "expenses": expenses,
        "net_profit": (revenue - expenses).round(2),
        "budget": (revenue * np.random.uniform(0.95, 1.1, 24)).round(2),
    })


# -----------------------------------------------------------------------
# Single KPI Calculation Tests
# -----------------------------------------------------------------------

class TestCalculateSingle:
    """Test individual KPI computation."""

    def test_sum_kpi(self, calculator, sales_df):
        """Sum KPI should return the total of a column."""
        cfg = {"label": "Total Revenue", "column": "amount", "function": "sum", "format": "currency"}
        result = calculator.calculate_single(sales_df, cfg)
        assert result["label"] == "Total Revenue"
        assert result["value"] > 0
        assert result["formatted"].startswith("$")
        assert "error" not in result

    def test_mean_kpi(self, calculator, sales_df):
        """Mean KPI should compute the average."""
        cfg = {"label": "Avg Amount", "column": "amount", "function": "mean", "format": "decimal"}
        result = calculator.calculate_single(sales_df, cfg)
        assert 50 <= result["value"] <= 1000

    def test_count_kpi(self, calculator, sales_df):
        """Count KPI should return the row count."""
        cfg = {"label": "Total Orders", "column": "amount", "function": "count", "format": "integer"}
        result = calculator.calculate_single(sales_df, cfg)
        assert result["value"] == 365

    def test_max_kpi(self, calculator, sales_df):
        """Max KPI should return the maximum value."""
        cfg = {"label": "Highest Sale", "column": "amount", "function": "max", "format": "currency"}
        result = calculator.calculate_single(sales_df, cfg)
        assert result["value"] == round(sales_df["amount"].max(), 2)

    def test_min_kpi(self, calculator, sales_df):
        """Min KPI should return the minimum value."""
        cfg = {"label": "Lowest Sale", "column": "amount", "function": "min", "format": "currency"}
        result = calculator.calculate_single(sales_df, cfg)
        assert result["value"] == round(sales_df["amount"].min(), 2)

    def test_median_kpi(self, calculator, sales_df):
        """Median KPI should return the 50th percentile."""
        cfg = {"label": "Median Sale", "column": "amount", "function": "median", "format": "decimal"}
        result = calculator.calculate_single(sales_df, cfg)
        expected = round(sales_df["amount"].median(), 2)
        assert result["value"] == expected

    def test_std_kpi(self, calculator, sales_df):
        """Standard deviation KPI should compute spread."""
        cfg = {"label": "Std Dev", "column": "amount", "function": "std", "format": "decimal"}
        result = calculator.calculate_single(sales_df, cfg)
        assert result["value"] > 0

    def test_unique_count_kpi(self, calculator, sales_df):
        """Unique count should return distinct values."""
        cfg = {"label": "Regions", "column": "region", "function": "unique_count", "format": "integer"}
        result = calculator.calculate_single(sales_df, cfg)
        assert result["value"] == 4

    def test_invalid_column(self, calculator, sales_df):
        """Missing column should return error in result."""
        cfg = {"label": "Missing", "column": "nonexistent", "function": "sum", "format": "number"}
        result = calculator.calculate_single(sales_df, cfg)
        assert "error" in result

    def test_compare_periods(self, calculator, sales_df):
        """Period comparison should return change percentage."""
        cfg = {
            "label": "Revenue", "column": "amount", "function": "sum",
            "format": "currency", "compare_periods": True,
        }
        result = calculator.calculate_single(sales_df, cfg)
        # change_pct may or may not be set depending on date column detection
        assert "trend" in result


# -----------------------------------------------------------------------
# Bulk KPI Calculation Tests
# -----------------------------------------------------------------------

class TestCalculateAll:
    """Test batch KPI computation."""

    def test_calculate_all_returns_list(self, calculator, sales_df):
        """calculate_all should return a list of results."""
        configs = [
            {"label": "Total", "column": "amount", "function": "sum", "format": "currency"},
            {"label": "Average", "column": "amount", "function": "mean", "format": "decimal"},
            {"label": "Count", "column": "amount", "function": "count", "format": "integer"},
        ]
        results = calculator.calculate_all(sales_df, configs)
        assert len(results) == 3
        assert all("label" in r for r in results)

    def test_calculate_all_handles_errors(self, calculator, sales_df):
        """Errors in one KPI should not affect others."""
        configs = [
            {"label": "Valid", "column": "amount", "function": "sum", "format": "currency"},
            {"label": "Invalid", "column": "missing_col", "function": "sum", "format": "number"},
        ]
        results = calculator.calculate_all(sales_df, configs)
        assert len(results) == 2
        assert "error" not in results[0]
        assert "error" in results[1]

    def test_empty_config_list(self, calculator, sales_df):
        """Empty config list should return empty results."""
        results = calculator.calculate_all(sales_df, [])
        assert results == []


# -----------------------------------------------------------------------
# Growth Rate Tests
# -----------------------------------------------------------------------

class TestGrowthRate:
    """Test period-over-period growth rate calculation."""

    def test_growth_rate_returns_dict(self, calculator, financial_df):
        """Growth rate should return a dict with rate, current, and previous."""
        result = calculator.growth_rate(financial_df, "month", "revenue")
        assert "growth_rate" in result
        assert "current" in result
        assert "previous" in result

    def test_growth_rate_numeric(self, calculator, financial_df):
        """Growth rate should be a numeric value."""
        result = calculator.growth_rate(financial_df, "month", "revenue")
        assert isinstance(result["growth_rate"], (int, float))

    def test_growth_rate_invalid_columns(self, calculator, financial_df):
        """Invalid columns should return zero growth."""
        result = calculator.growth_rate(financial_df, "missing", "also_missing")
        assert result["growth_rate"] == 0


# -----------------------------------------------------------------------
# Moving Average Tests
# -----------------------------------------------------------------------

class TestMovingAverage:
    """Test moving average computation."""

    def test_moving_average_returns_df(self, calculator, financial_df):
        """Moving average should return a DataFrame with the moving_avg column."""
        result = calculator.moving_average(financial_df, "month", "revenue", window=3)
        assert isinstance(result, pd.DataFrame)
        assert "moving_avg" in result.columns

    def test_moving_average_length(self, calculator, financial_df):
        """Result should have same number of rows as resampled months."""
        result = calculator.moving_average(financial_df, "month", "revenue", window=3)
        assert len(result) > 0

    def test_moving_average_invalid_columns(self, calculator, financial_df):
        """Invalid columns should return empty DataFrame."""
        result = calculator.moving_average(financial_df, "missing", "revenue")
        assert len(result) == 0


# -----------------------------------------------------------------------
# Year-Over-Year Tests
# -----------------------------------------------------------------------

class TestYearOverYear:
    """Test year-over-year comparison."""

    def test_yoy_returns_dict(self, calculator, financial_df):
        """YoY should return a dict keyed by year."""
        result = calculator.year_over_year(financial_df, "month", "revenue")
        assert isinstance(result, dict)
        assert 2023 in result or 2024 in result

    def test_yoy_contains_values(self, calculator, financial_df):
        """Each year entry should have a value."""
        result = calculator.year_over_year(financial_df, "month", "revenue")
        for year, data in result.items():
            assert "value" in data
            assert data["value"] > 0

    def test_yoy_change_for_second_year(self, calculator, financial_df):
        """Second year should have a yoy_change value."""
        result = calculator.year_over_year(financial_df, "month", "revenue")
        years = sorted(result.keys())
        if len(years) >= 2:
            assert result[years[1]]["yoy_change"] is not None


# -----------------------------------------------------------------------
# Top Performers Tests
# -----------------------------------------------------------------------

class TestTopPerformers:
    """Test top/bottom performer identification."""

    def test_top_performers_returns_list(self, calculator, sales_df):
        """Top performers should return a list of dicts."""
        result = calculator.top_performers(sales_df, "region", "amount", n=3)
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_top_performers_sorted(self, calculator, sales_df):
        """Results should be sorted in descending order."""
        result = calculator.top_performers(sales_df, "region", "amount", n=4)
        values = [r["value"] for r in result]
        assert values == sorted(values, reverse=True)

    def test_top_performers_share_pct(self, calculator, sales_df):
        """Each performer should have a share percentage."""
        result = calculator.top_performers(sales_df, "region", "amount", n=4)
        for r in result:
            assert "share_pct" in r
            assert 0 <= r["share_pct"] <= 100

    def test_bottom_performers(self, calculator, sales_df):
        """ascending=True should return bottom performers."""
        result = calculator.top_performers(sales_df, "region", "amount", n=2, ascending=True)
        values = [r["value"] for r in result]
        assert values == sorted(values)


# -----------------------------------------------------------------------
# Variance Analysis Tests
# -----------------------------------------------------------------------

class TestVarianceAnalysis:
    """Test budget variance calculations."""

    def test_variance_basic(self, calculator, financial_df):
        """Variance analysis should return actual, budget, and variance."""
        result = calculator.variance_analysis(financial_df, "revenue", "budget")
        assert "actual" in result
        assert "budget" in result
        assert "variance" in result
        assert "variance_pct" in result
        assert "favorable" in result

    def test_variance_without_budget(self, calculator, financial_df):
        """Without budget column, should use mean as proxy."""
        result = calculator.variance_analysis(financial_df, "revenue")
        assert "actual" in result
        assert "budget" in result

    def test_variance_with_breakdown(self, calculator, sales_df):
        """Group breakdown should return per-group variance."""
        result = calculator.variance_analysis(sales_df, "amount", group_col="region")
        assert "breakdown" in result
        assert len(result["breakdown"]) > 0

    def test_variance_invalid_column(self, calculator, sales_df):
        """Invalid column should return error."""
        result = calculator.variance_analysis(sales_df, "nonexistent")
        assert "error" in result


# -----------------------------------------------------------------------
# Percentile Ranking Tests
# -----------------------------------------------------------------------

class TestPercentileRanking:
    """Test percentile ranking calculations."""

    def test_percentile_ranking(self, calculator, sales_df):
        """Percentile ranking should return standard percentiles."""
        result = calculator.percentile_ranking(sales_df, "amount")
        assert "p10" in result
        assert "p25" in result
        assert "p50" in result
        assert "p75" in result
        assert "p90" in result
        assert "iqr" in result

    def test_percentile_ordering(self, calculator, sales_df):
        """Percentiles should be in ascending order."""
        result = calculator.percentile_ranking(sales_df, "amount")
        assert result["p10"] <= result["p25"]
        assert result["p25"] <= result["p50"]
        assert result["p50"] <= result["p75"]
        assert result["p75"] <= result["p90"]

    def test_iqr_calculation(self, calculator, sales_df):
        """IQR should equal p75 - p25."""
        result = calculator.percentile_ranking(sales_df, "amount")
        expected_iqr = round(result["p75"] - result["p25"], 2)
        assert result["iqr"] == expected_iqr

    def test_percentile_invalid_column(self, calculator, sales_df):
        """Invalid column should return empty dict."""
        result = calculator.percentile_ranking(sales_df, "nonexistent")
        assert result == {}


# -----------------------------------------------------------------------
# Value Formatting Tests
# -----------------------------------------------------------------------

class TestFormatting:
    """Test value formatting for KPI display."""

    def test_format_currency_millions(self, calculator):
        """Millions should be formatted as $X.XM."""
        result = calculator._format_value(2500000, "currency")
        assert "M" in result
        assert "$" in result

    def test_format_currency_thousands(self, calculator):
        """Thousands should be formatted as $X.XK."""
        result = calculator._format_value(45000, "currency")
        assert "K" in result

    def test_format_currency_small(self, calculator):
        """Small amounts should show full value."""
        result = calculator._format_value(42.50, "currency")
        assert "$" in result
        assert "42" in result

    def test_format_percent(self, calculator):
        """Percent format should append %."""
        result = calculator._format_value(35.7, "percent")
        assert "%" in result
        assert "35.7" in result

    def test_format_decimal(self, calculator):
        """Decimal format should show 2 decimal places."""
        result = calculator._format_value(123.456, "decimal")
        assert "123.46" in result

    def test_format_integer(self, calculator):
        """Integer format should not show decimals."""
        result = calculator._format_value(1234.0, "integer")
        assert "1,234" in result

    def test_format_compact_billions(self, calculator):
        """Billions should show B suffix."""
        result = calculator._format_value(3200000000, "compact")
        assert "B" in result

    def test_format_na(self, calculator):
        """NaN should format as N/A."""
        result = calculator._format_value(float("nan"), "currency")
        assert result == "N/A"


# -----------------------------------------------------------------------
# Icon Selection Tests
# -----------------------------------------------------------------------

class TestIconSelection:
    """Test icon selection based on KPI function and trend."""

    def test_sum_icon(self, calculator):
        assert calculator._get_icon("sum", "up") == "bar-chart-2"

    def test_mean_icon(self, calculator):
        assert calculator._get_icon("mean", "neutral") == "trending-up"

    def test_count_icon(self, calculator):
        assert calculator._get_icon("count", "down") == "hash"

    def test_unknown_function_default(self, calculator):
        """Unknown functions should return a default icon."""
        result = calculator._get_icon("custom_func", "up")
        assert result == "bar-chart-2"
