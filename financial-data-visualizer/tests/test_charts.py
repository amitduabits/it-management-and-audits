"""
test_charts.py
==============

Unit tests for chart generation modules. Tests verify that charts
are created without errors and return valid matplotlib Figure objects.
Uses non-interactive Agg backend to avoid display issues in CI.
"""

import os
import tempfile

import pytest
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for testing
import matplotlib.pyplot as plt

from src.charts.line_charts import LineChartGenerator
from src.charts.bar_charts import BarChartGenerator
from src.charts.pie_charts import PieChartGenerator
from src.charts.heatmaps import HeatmapGenerator
from src.charts.scatter_plots import ScatterPlotGenerator
from src.charts.candlestick import CandlestickGenerator


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def transactions_df():
    """Sample transactions DataFrame."""
    np.random.seed(0)
    n = 200
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "date": dates,
        "amount": np.random.normal(-100, 200, n),
        "category": np.random.choice(
            ["Groceries", "Dining", "Shopping", "Utilities", "Entertainment"],
            size=n,
        ),
        "merchant": ["Merchant_" + str(i % 10) for i in range(n)],
        "type": np.random.choice(["credit", "debit"], size=n),
    })


@pytest.fixture
def market_df():
    """Sample market data DataFrame."""
    np.random.seed(42)
    n = 100
    dates = pd.bdate_range("2025-01-01", periods=n)
    prices = 150 + np.cumsum(np.random.normal(0.1, 2, size=n))
    return pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": prices + np.abs(np.random.normal(1, 0.5, n)),
        "low": prices - np.abs(np.random.normal(1, 0.5, n)),
        "close": prices + np.random.normal(0, 0.5, n),
        "volume": np.random.randint(2_000_000, 8_000_000, n),
    })


@pytest.fixture
def revenue_df():
    """Sample revenue/expense DataFrame."""
    months = pd.date_range("2023-01-01", periods=24, freq="MS")
    np.random.seed(7)
    revenue = 850_000 * (1.015 ** np.arange(24))
    return pd.DataFrame({
        "date": months,
        "revenue": revenue,
        "cogs": revenue * 0.40,
        "operating_expenses": revenue * 0.18,
        "marketing": revenue * 0.10,
        "salaries": 180_000 + 3000 * np.arange(24),
        "net_income": revenue * 0.12,
    })


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for chart output."""
    with tempfile.TemporaryDirectory() as d:
        yield d


# ------------------------------------------------------------------
# Line Charts
# ------------------------------------------------------------------

class TestLineCharts:

    def test_plot_trend_returns_figure(self, transactions_df):
        gen = LineChartGenerator()
        fig = gen.plot_trend(transactions_df, x="date", y="amount")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_trend_with_title(self, transactions_df):
        gen = LineChartGenerator()
        fig = gen.plot_trend(
            transactions_df, x="date", y="amount",
            title="Test Trend Chart",
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_stock_price(self, market_df):
        gen = LineChartGenerator()
        fig = gen.plot_stock_price(market_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_stock_price_custom_windows(self, market_df):
        gen = LineChartGenerator()
        fig = gen.plot_stock_price(market_df, windows=[5, 20])
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_multi_line(self, revenue_df):
        gen = LineChartGenerator()
        fig = gen.plot_multi_line(
            revenue_df,
            value_cols=["revenue", "cogs", "net_income"],
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_trend_saves_file(self, transactions_df, tmp_dir):
        gen = LineChartGenerator()
        path = os.path.join(tmp_dir, "trend.png")
        gen.plot_trend(transactions_df, x="date", y="amount", output=path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


# ------------------------------------------------------------------
# Bar Charts
# ------------------------------------------------------------------

class TestBarCharts:

    def test_monthly_comparison(self, transactions_df):
        gen = BarChartGenerator()
        fig = gen.plot_monthly_comparison(transactions_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_category_breakdown(self, transactions_df):
        gen = BarChartGenerator()
        fig = gen.plot_category_breakdown(transactions_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_top_n_default(self, transactions_df):
        gen = BarChartGenerator()
        fig = gen.plot_top_n(transactions_df, label_col="merchant")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_top_n_custom(self, transactions_df):
        gen = BarChartGenerator()
        fig = gen.plot_top_n(transactions_df, label_col="category", n=3)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_stacked_monthly(self, transactions_df):
        gen = BarChartGenerator()
        fig = gen.plot_stacked_monthly(transactions_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_monthly_comparison_saves_file(self, transactions_df, tmp_dir):
        gen = BarChartGenerator()
        path = os.path.join(tmp_dir, "monthly.png")
        gen.plot_monthly_comparison(transactions_df, output=path)
        assert os.path.exists(path)


# ------------------------------------------------------------------
# Pie Charts
# ------------------------------------------------------------------

class TestPieCharts:

    def test_expense_distribution(self, transactions_df):
        gen = PieChartGenerator()
        fig = gen.plot_expense_distribution(transactions_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_expense_distribution_no_donut(self, transactions_df):
        gen = PieChartGenerator()
        fig = gen.plot_expense_distribution(transactions_df, donut=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_revenue_segments_from_dict(self):
        gen = PieChartGenerator()
        segments = {
            "Enterprise": 5_000_000,
            "SMB": 3_000_000,
            "Consumer": 2_000_000,
        }
        fig = gen.plot_revenue_segments(segments)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_revenue_from_df(self, transactions_df):
        gen = PieChartGenerator()
        fig = gen.plot_revenue_from_df(transactions_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_comparison_pie(self):
        gen = PieChartGenerator()
        d1 = {"A": 100, "B": 200, "C": 300}
        d2 = {"A": 150, "B": 180, "C": 350}
        fig = gen.plot_comparison(d1, d2)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ------------------------------------------------------------------
# Heatmaps
# ------------------------------------------------------------------

class TestHeatmaps:

    def test_correlation_heatmap(self, revenue_df):
        gen = HeatmapGenerator()
        fig = gen.plot_correlation(revenue_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_correlation_no_mask(self, revenue_df):
        gen = HeatmapGenerator()
        fig = gen.plot_correlation(revenue_df, mask_upper=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_volume_heatmap(self, transactions_df):
        gen = HeatmapGenerator()
        fig = gen.plot_volume_heatmap(transactions_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_correlation_saves_file(self, revenue_df, tmp_dir):
        gen = HeatmapGenerator()
        path = os.path.join(tmp_dir, "corr.png")
        gen.plot_correlation(revenue_df, output=path)
        assert os.path.exists(path)


# ------------------------------------------------------------------
# Scatter Plots
# ------------------------------------------------------------------

class TestScatterPlots:

    def test_risk_return(self):
        gen = ScatterPlotGenerator()
        assets = {
            "Stock A": (15.0, 12.0),
            "Stock B": (25.0, 18.0),
            "Stock C": (10.0, 7.0),
            "Bond Fund": (5.0, 4.0),
        }
        fig = gen.plot_risk_return(assets)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_risk_return_no_frontier(self):
        gen = ScatterPlotGenerator()
        assets = {"A": (10.0, 8.0), "B": (20.0, 15.0)}
        fig = gen.plot_risk_return(assets, show_frontier=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_outlier_detection_iqr(self, transactions_df):
        gen = ScatterPlotGenerator()
        fig = gen.plot_outlier_detection(transactions_df, method="iqr")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_outlier_detection_zscore(self, transactions_df):
        gen = ScatterPlotGenerator()
        fig = gen.plot_outlier_detection(transactions_df, method="zscore")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_risk_return_from_df(self, market_df):
        gen = ScatterPlotGenerator()
        fig = gen.plot_risk_return_from_df(market_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_scatter_regression(self, revenue_df):
        gen = ScatterPlotGenerator()
        fig = gen.plot_scatter_regression(
            revenue_df, x_col="revenue", y_col="net_income",
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ------------------------------------------------------------------
# Candlestick Charts
# ------------------------------------------------------------------

class TestCandlestick:

    def test_candlestick_basic(self, market_df):
        gen = CandlestickGenerator()
        fig = gen.plot_candlestick(market_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_candlestick_no_volume(self, market_df):
        gen = CandlestickGenerator()
        fig = gen.plot_candlestick(market_df, show_volume=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_candlestick_no_ma(self, market_df):
        gen = CandlestickGenerator()
        fig = gen.plot_candlestick(market_df, show_ma=False)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_candlestick_last_n(self, market_df):
        gen = CandlestickGenerator()
        fig = gen.plot_candlestick(market_df, last_n=30)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_ohlc_bars(self, market_df):
        gen = CandlestickGenerator()
        fig = gen.plot_ohlc_bars(market_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_candlestick_saves_file(self, market_df, tmp_dir):
        gen = CandlestickGenerator()
        path = os.path.join(tmp_dir, "candle.png")
        gen.plot_candlestick(market_df, output=path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


# ------------------------------------------------------------------
# Integration: Chart from loaded data file
# ------------------------------------------------------------------

class TestChartIntegration:

    def test_all_generators_accept_custom_figsize(self, market_df, transactions_df):
        """Verify that custom figsize is accepted without error."""
        LineChartGenerator(figsize=(10, 5)).plot_trend(
            transactions_df, x="date", y="amount"
        )
        BarChartGenerator(figsize=(10, 5)).plot_monthly_comparison(transactions_df)
        PieChartGenerator(figsize=(8, 8)).plot_expense_distribution(transactions_df)
        HeatmapGenerator(figsize=(10, 8)).plot_volume_heatmap(transactions_df)
        ScatterPlotGenerator(figsize=(10, 8)).plot_outlier_detection(transactions_df)
        CandlestickGenerator(figsize=(12, 8)).plot_candlestick(market_df)
        plt.close("all")

    def test_all_generators_accept_custom_dpi(self, market_df, transactions_df, tmp_dir):
        """Verify custom DPI generates valid output."""
        path = os.path.join(tmp_dir, "high_dpi.png")
        gen = LineChartGenerator(dpi=300)
        gen.plot_trend(transactions_df, x="date", y="amount", output=path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        plt.close("all")
