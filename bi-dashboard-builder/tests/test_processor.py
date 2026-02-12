"""
Tests for the DataProcessor module.

Covers file loading, column type detection, aggregation,
auto-configuration, and filter option generation.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

# Adjust path so tests can import the app package
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.data_processor import DataProcessor


@pytest.fixture
def processor():
    """Create a DataProcessor instance."""
    return DataProcessor()


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100, freq="D"),
        "product": np.random.choice(["Widget A", "Widget B", "Widget C", "Widget D"], 100),
        "region": np.random.choice(["North", "South", "East", "West"], 100),
        "amount": np.random.uniform(10.0, 500.0, 100).round(2),
        "quantity": np.random.randint(1, 50, 100),
        "category": np.random.choice(["Electronics", "Furniture", "Accessories"], 100),
    })


@pytest.fixture
def csv_file(sample_df):
    """Write sample_df to a temporary CSV and return the path."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    sample_df.to_csv(path, index=False)
    yield path
    os.close(fd)
    os.unlink(path)


# -----------------------------------------------------------------------
# File Loading Tests
# -----------------------------------------------------------------------

class TestFileLoading:
    """Tests for loading files from disk."""

    def test_load_csv(self, processor, csv_file):
        """CSV files should load into a DataFrame."""
        df = processor.load_file(csv_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert "amount" in df.columns

    def test_load_nonexistent_file(self, processor):
        """Loading a non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            processor.load_file("/tmp/does_not_exist_12345.csv")

    def test_load_unsupported_format(self, processor):
        """Loading an unsupported format should raise ValueError."""
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            with pytest.raises(ValueError, match="Unsupported"):
                processor.load_file(path)
        finally:
            os.unlink(path)

    def test_column_names_cleaned(self, processor):
        """Column names should be lowercased and spaces replaced with underscores."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        df = pd.DataFrame({"Product Name": ["A"], "Sale Amount": [100]})
        df.to_csv(path, index=False)
        os.close(fd)
        try:
            loaded = processor.load_file(path)
            assert "product_name" in loaded.columns
            assert "sale_amount" in loaded.columns
        finally:
            os.unlink(path)


# -----------------------------------------------------------------------
# Column Type Detection Tests
# -----------------------------------------------------------------------

class TestColumnTypeDetection:
    """Tests for automatic column type classification."""

    def test_detect_numeric(self, processor, sample_df):
        """Numeric columns should be detected correctly."""
        types = processor.detect_column_types(sample_df)
        assert types["amount"] == "numeric"
        assert types["quantity"] == "numeric"

    def test_detect_categorical(self, processor, sample_df):
        """Low-cardinality string columns should be detected as categorical."""
        types = processor.detect_column_types(sample_df)
        assert types["product"] == "categorical"
        assert types["region"] == "categorical"
        assert types["category"] == "categorical"

    def test_detect_date(self, processor, sample_df):
        """Datetime columns should be detected as date."""
        types = processor.detect_column_types(sample_df)
        assert types["date"] == "date"

    def test_high_cardinality_text(self, processor):
        """High cardinality string columns should be classified as text."""
        df = pd.DataFrame({
            "description": [f"Item description number {i}" for i in range(200)]
        })
        types = processor.detect_column_types(df)
        assert types["description"] == "text"


# -----------------------------------------------------------------------
# Summary Tests
# -----------------------------------------------------------------------

class TestGetSummary:
    """Tests for the dataset summary generation."""

    def test_summary_basic_fields(self, processor, sample_df):
        """Summary should include row count, columns, and type info."""
        summary = processor.get_summary(sample_df)
        assert summary["rows"] == 100
        assert summary["columns"] == 6
        assert len(summary["column_names"]) == 6
        assert "numeric_columns" in summary
        assert "categorical_columns" in summary
        assert "date_columns" in summary

    def test_summary_numeric_stats(self, processor, sample_df):
        """Summary should include descriptive stats for numeric columns."""
        summary = processor.get_summary(sample_df)
        assert "numeric_stats" in summary
        assert "amount" in summary["numeric_stats"]
        stats = summary["numeric_stats"]["amount"]
        assert "mean" in stats
        assert "min" in stats
        assert "max" in stats

    def test_summary_categorical_values(self, processor, sample_df):
        """Summary should include top values for categorical columns."""
        summary = processor.get_summary(sample_df)
        assert "categorical_values" in summary
        assert "region" in summary["categorical_values"]

    def test_summary_missing_values(self, processor):
        """Summary should report missing value counts."""
        df = pd.DataFrame({
            "a": [1, 2, None, 4, None],
            "b": ["x", "y", "z", None, "w"],
        })
        summary = processor.get_summary(df)
        assert summary["missing_values"]["a"] == 2
        assert summary["missing_values"]["b"] == 1


# -----------------------------------------------------------------------
# Aggregation Engine Tests
# -----------------------------------------------------------------------

class TestAggregation:
    """Tests for the aggregation engine."""

    def test_aggregate_sum(self, processor, sample_df):
        """Aggregate by sum should return correct groups."""
        result = processor.aggregate(sample_df, "region", "amount", "sum")
        assert len(result) > 0
        assert "amount_sum" in result.columns

    def test_aggregate_mean(self, processor, sample_df):
        """Aggregate by mean should compute averages."""
        result = processor.aggregate(sample_df, "category", "amount", "mean")
        assert "amount_mean" in result.columns

    def test_aggregate_count(self, processor, sample_df):
        """Aggregate by count should tally records."""
        result = processor.aggregate(sample_df, "product", "amount", "count")
        assert "amount_count" in result.columns
        assert result["amount_count"].sum() == 100

    def test_aggregate_top_n(self, processor, sample_df):
        """top_n parameter should limit results."""
        result = processor.aggregate(sample_df, "product", "amount", "sum", top_n=2)
        assert len(result) <= 2

    def test_aggregate_multiple_group_cols(self, processor, sample_df):
        """Aggregation should work with multiple group-by columns."""
        result = processor.aggregate(sample_df, ["region", "category"], "amount", "sum")
        assert len(result) > 0

    def test_aggregate_invalid_column(self, processor, sample_df):
        """Aggregation with invalid column should return empty DataFrame."""
        result = processor.aggregate(sample_df, "nonexistent", "amount", "sum")
        assert len(result) == 0

    def test_time_series_aggregate(self, processor, sample_df):
        """Time series aggregation should resample by period."""
        result = processor.time_series_aggregate(sample_df, "date", "amount", freq="M")
        assert len(result) > 0

    def test_pivot_data(self, processor, sample_df):
        """Pivot table should create cross-tabulations."""
        result = processor.pivot_data(sample_df, "region", "category", "amount")
        assert len(result) > 0


# -----------------------------------------------------------------------
# Filter Options Tests
# -----------------------------------------------------------------------

class TestFilterOptions:
    """Tests for filter option generation."""

    def test_categorical_filters(self, processor, sample_df):
        """Categorical columns should produce select filters."""
        filters = processor.get_filter_options(sample_df)
        assert "region" in filters
        assert filters["region"]["type"] == "select"
        assert len(filters["region"]["values"]) > 0

    def test_date_filters(self, processor, sample_df):
        """Date columns should produce date_range filters."""
        filters = processor.get_filter_options(sample_df)
        assert "date" in filters
        assert filters["date"]["type"] == "date_range"
        assert "min" in filters["date"]
        assert "max" in filters["date"]


# -----------------------------------------------------------------------
# Auto-Configuration Tests
# -----------------------------------------------------------------------

class TestAutoConfiguration:
    """Tests for automatic dashboard configuration."""

    def test_auto_configure_returns_dict(self, processor, sample_df):
        """Auto-configure should return a valid config dict."""
        config = processor.auto_configure(sample_df)
        assert isinstance(config, dict)
        assert "title" in config
        assert "kpis" in config
        assert "charts" in config

    def test_auto_configure_generates_kpis(self, processor, sample_df):
        """Auto-configure should generate at least one KPI."""
        config = processor.auto_configure(sample_df)
        assert len(config["kpis"]) > 0

    def test_auto_configure_generates_charts(self, processor, sample_df):
        """Auto-configure should generate at least one chart."""
        config = processor.auto_configure(sample_df)
        assert len(config["charts"]) > 0

    def test_auto_configure_kpi_max_limit(self, processor, sample_df):
        """Auto-configure should limit KPIs to 8."""
        config = processor.auto_configure(sample_df)
        assert len(config["kpis"]) <= 8

    def test_auto_configure_includes_line_chart(self, processor, sample_df):
        """When date columns exist, a line chart should be generated."""
        config = processor.auto_configure(sample_df)
        chart_types = [c["type"] for c in config["charts"]]
        assert "line" in chart_types

    def test_auto_configure_includes_bar_chart(self, processor, sample_df):
        """When categorical columns exist, a bar chart should be generated."""
        config = processor.auto_configure(sample_df)
        chart_types = [c["type"] for c in config["charts"]]
        assert "bar" in chart_types


# -----------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_dataframe(self, processor):
        """Empty DataFrames should not crash."""
        df = pd.DataFrame()
        summary = processor.get_summary(df)
        assert summary["rows"] == 0
        assert summary["columns"] == 0

    def test_single_row(self, processor):
        """Single-row DataFrames should work correctly."""
        df = pd.DataFrame({"a": [1], "b": ["x"]})
        summary = processor.get_summary(df)
        assert summary["rows"] == 1

    def test_all_null_column(self, processor):
        """Columns with all null values should be handled."""
        df = pd.DataFrame({"a": [None, None, None], "b": [1, 2, 3]})
        types = processor.detect_column_types(df)
        assert "a" in types
        assert "b" in types
