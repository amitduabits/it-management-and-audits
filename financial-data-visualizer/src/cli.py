"""
cli.py
======

Command-line interface for the Financial Data Visualizer.
Built on Click with three commands: analyze, chart, and dashboard.
"""

import os
import sys
import json
import logging

import click
import pandas as pd

from src.data_loader import DataLoader
from src.statistics import FinancialStatistics
from src.dashboard import DashboardBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cli")


# ======================================================================
# CLI Group
# ======================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="Financial Data Visualizer")
def cli():
    """Financial Data Visualizer -- Analyze, chart, and dashboard your data."""
    pass


# ======================================================================
# analyze command
# ======================================================================

@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--date-col", default="date", help="Name of the date column.")
@click.option("--value-col", default="amount", help="Name of the primary value column.")
@click.option("--output", "-o", default=None, help="Save JSON report to file.")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output.")
def analyze(filepath, date_col, value_col, output, verbose):
    """
    Run statistical analysis on a financial dataset.

    FILEPATH is the path to a CSV file.

    Examples:

        python -m src.cli analyze data/transactions.csv

        python -m src.cli analyze data/market_data.csv --value-col close -o report.json
    """
    click.echo(f"\nLoading: {filepath}")
    loader = DataLoader()

    try:
        df = loader.load_csv(filepath, date_col=date_col)
    except Exception as exc:
        click.echo(f"Error loading file: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Rows: {len(df):,}  |  Columns: {list(df.columns)}\n")

    stats = FinancialStatistics(df, date_col=date_col, value_col=value_col)

    # Summary
    summary = stats.summary()
    click.echo("=" * 60)
    click.echo("STATISTICAL SUMMARY")
    click.echo("=" * 60)
    click.echo(f"  Count:     {summary['count']:,}")
    click.echo(f"  Mean:      ${summary['mean']:,.2f}")
    click.echo(f"  Median:    ${summary['median']:,.2f}")
    click.echo(f"  Std Dev:   ${summary['std']:,.2f}")
    click.echo(f"  Min:       ${summary['min']:,.2f}")
    click.echo(f"  Max:       ${summary['max']:,.2f}")
    click.echo(f"  Variance:  ${summary['variance']:,.2f}")
    click.echo(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")

    # Percentiles
    click.echo("\n  Percentiles:")
    for label, val in summary["percentiles"].items():
        click.echo(f"    {label}: ${val:,.2f}")

    # Moving averages (latest values)
    if verbose:
        click.echo("\n" + "=" * 60)
        click.echo("MOVING AVERAGES (Latest Values)")
        click.echo("=" * 60)
        ma_df = stats.moving_averages_multi()
        latest = ma_df.iloc[-1]
        for col, val in latest.items():
            click.echo(f"  {col}: ${val:,.2f}")

        # Outliers
        outliers = stats.detect_outliers_iqr()
        click.echo(f"\n  IQR Outliers Detected: {len(outliers)}")

        # Category breakdown if applicable
        if "category" in df.columns:
            click.echo("\n" + "=" * 60)
            click.echo("CATEGORY BREAKDOWN")
            click.echo("=" * 60)
            breakdown = stats.category_breakdown()
            for cat, val in breakdown.items():
                click.echo(f"  {cat:20s} ${val:>12,.2f}")

    # YoY growth
    try:
        yoy = stats.yoy_growth()
        valid_yoy = yoy["yoy_growth_pct"].dropna()
        if not valid_yoy.empty:
            click.echo("\n  YoY Growth (latest): {:.1f}%".format(valid_yoy.iloc[-1]))
    except Exception:
        pass

    # Save report
    if output:
        report = {
            "file": filepath,
            "summary": summary,
        }
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        click.echo(f"\nReport saved to: {output}")

    click.echo()


# ======================================================================
# chart command
# ======================================================================

@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--type", "chart_type",
    type=click.Choice(["line", "bar", "pie", "heatmap", "scatter", "candlestick"]),
    default="line",
    help="Chart type to generate.",
)
@click.option("--output", "-o", default=None, help="Output file path (e.g. chart.png).")
@click.option("--title", "-t", default=None, help="Custom chart title.")
@click.option("--date-col", default="date", help="Date column name.")
@click.option("--value-col", default="amount", help="Value column name.")
def chart(filepath, chart_type, output, title, date_col, value_col):
    """
    Generate a chart from a financial dataset.

    FILEPATH is the path to a CSV file.

    Examples:

        python -m src.cli chart data/transactions.csv --type bar -o monthly.png

        python -m src.cli chart data/market_data.csv --type candlestick
    """
    import matplotlib
    matplotlib.use("Agg")

    click.echo(f"\nLoading: {filepath}")
    loader = DataLoader()

    try:
        df = loader.load_csv(filepath, date_col=date_col)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Generating {chart_type} chart...")

    if output is None:
        output = f"output/{chart_type}_chart.png"

    try:
        if chart_type == "line":
            from src.charts.line_charts import LineChartGenerator
            gen = LineChartGenerator()
            if "close" in df.columns:
                gen.plot_stock_price(
                    df, date_col=date_col, price_col="close",
                    title=title or "Stock Price with Moving Averages",
                    output=output,
                )
            else:
                gen.plot_trend(
                    df, x=date_col, y=value_col,
                    title=title or "Value Trend Over Time",
                    output=output,
                )

        elif chart_type == "bar":
            from src.charts.bar_charts import BarChartGenerator
            gen = BarChartGenerator()
            gen.plot_monthly_comparison(
                df, date_col=date_col, value_col=value_col,
                title=title or "Monthly Financial Summary",
                output=output,
            )

        elif chart_type == "pie":
            from src.charts.pie_charts import PieChartGenerator
            gen = PieChartGenerator()
            if "category" in df.columns:
                gen.plot_expense_distribution(
                    df, category_col="category", value_col=value_col,
                    title=title or "Expense Distribution",
                    output=output,
                )
            else:
                click.echo("Pie chart requires a 'category' column.", err=True)
                sys.exit(1)

        elif chart_type == "heatmap":
            from src.charts.heatmaps import HeatmapGenerator
            gen = HeatmapGenerator()
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if len(numeric_cols) >= 2:
                gen.plot_correlation(
                    df, columns=numeric_cols,
                    title=title or "Correlation Heatmap",
                    output=output,
                )
            else:
                gen.plot_volume_heatmap(
                    df, date_col=date_col, value_col=value_col,
                    title=title or "Transaction Volume Heatmap",
                    output=output,
                )

        elif chart_type == "scatter":
            from src.charts.scatter_plots import ScatterPlotGenerator
            gen = ScatterPlotGenerator()
            gen.plot_outlier_detection(
                df, x_col=date_col, y_col=value_col,
                title=title or "Outlier Detection",
                output=output,
            )

        elif chart_type == "candlestick":
            from src.charts.candlestick import CandlestickGenerator
            gen = CandlestickGenerator()
            required = {"open", "high", "low", "close"}
            if required.issubset(set(df.columns)):
                gen.plot_candlestick(
                    df, date_col=date_col,
                    title=title or "OHLC Candlestick Chart",
                    output=output,
                )
            else:
                click.echo(
                    f"Candlestick requires columns: {required}. "
                    f"Found: {set(df.columns)}",
                    err=True,
                )
                sys.exit(1)

        click.echo(f"Chart saved to: {output}\n")

    except Exception as exc:
        click.echo(f"Chart generation failed: {exc}", err=True)
        sys.exit(1)


# ======================================================================
# dashboard command
# ======================================================================

@cli.command()
@click.argument("data_dir", type=click.Path(exists=True))
@click.option("--output", "-o", default="dashboard.html", help="Output HTML file path.")
@click.option("--title", "-t", default="Financial Data Dashboard",
              help="Dashboard title.")
@click.option("--theme", default="plotly_white",
              type=click.Choice(["plotly_white", "plotly_dark", "plotly", "ggplot2"]),
              help="Plotly visual theme.")
def dashboard(data_dir, output, title, theme):
    """
    Generate an interactive HTML dashboard from a data directory.

    DATA_DIR should contain transactions.csv, market_data.csv,
    and/or revenue_expenses.csv.

    Examples:

        python -m src.cli dashboard data/ -o reports/dashboard.html

        python -m src.cli dashboard data/ --theme plotly_dark
    """
    click.echo(f"\nBuilding dashboard from: {data_dir}")
    click.echo(f"Theme: {theme}")

    try:
        builder = DashboardBuilder(
            data_dir=data_dir,
            title=title,
            theme=theme,
        )
        result_path = builder.build(output)
        click.echo(f"Dashboard generated: {result_path}\n")
    except Exception as exc:
        click.echo(f"Dashboard build failed: {exc}", err=True)
        sys.exit(1)


# ======================================================================
# Entry point
# ======================================================================

if __name__ == "__main__":
    cli()
