"""line_charts.py
=============

Line chart generation module for financial data visualization.
Provides the LineChartGenerator class with methods for plotting
time-series trends and stock price movements using matplotlib.
"""

import logging
import os
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

__author__ = "Dr Amit Dua"

logger = logging.getLogger(__name__)


class LineChartGenerator:
    """Generator for line-based financial charts.

    Produces publication-quality line charts suitable for trend analysis
    and stock price visualization. All output is rendered as PNG files.
    """

    STYLE: str = "seaborn-v0_8-whitegrid"
    DPI: int = 150
    FIGSIZE: tuple[int, int] = (12, 6)

    def __init__(self) -> None:
        """Initialise the LineChartGenerator with default styling."""
        logger.info("LineChartGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot_trend(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str,
        output: str,
    ) -> str:
        """Plot a generic trend line from *x* vs *y* columns.

        Parameters
        ----------
        df : pd.DataFrame
            Source data containing at least the *x* and *y* columns.
        x : str
            Column name for the horizontal axis.
        y : str
            Column name for the vertical axis.
        title : str
            Chart title rendered at the top of the figure.
        output : str
            File path (PNG) where the chart will be saved.

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating trend chart: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE)

        x_data: pd.Series = df[x]
        y_data: pd.Series = df[y]

        ax.plot(
            x_data,
            y_data,
            linewidth=2,
            color="#1f77b4",
            marker="o",
            markersize=4,
            alpha=0.85,
            label=y,
        )

        # Rolling mean overlay when enough data points exist
        if len(y_data) >= 7:
            rolling_mean: pd.Series = y_data.rolling(window=7, min_periods=1).mean()
            ax.plot(
                x_data,
                rolling_mean,
                linewidth=1.5,
                linestyle="--",
                color="#ff7f0e",
                alpha=0.7,
                label=f"{y} (7-period MA)",
            )

        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel(x, fontsize=11)
        ax.set_ylabel(y, fontsize=11)
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Trend chart saved to %s", output)
        return os.path.abspath(output)

    def plot_stock_price(
        self,
        df: pd.DataFrame,
        date_col: str,
        price_col: str,
        title: str,
        output: str,
    ) -> str:
        """Plot a stock-price time-series with date formatting.

        Parameters
        ----------
        df : pd.DataFrame
            Source data with a date column and a price column.
        date_col : str
            Name of the datetime column.
        price_col : str
            Name of the price column.
        title : str
            Chart title.
        output : str
            Destination file path (PNG).

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating stock price chart: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE)

        dates: pd.Series = pd.to_datetime(df[date_col])
        prices: pd.Series = df[price_col].astype(float)

        ax.plot(dates, prices, linewidth=1.8, color="#2ca02c", label=price_col)

        # Shade the area under the price curve
        ax.fill_between(dates, prices, alpha=0.15, color="#2ca02c")

        # Highlight min / max prices
        idx_min: int = int(prices.idxmin())
        idx_max: int = int(prices.idxmax())
        ax.annotate(
            f"Min: {prices[idx_min]:.2f}",
            xy=(dates[idx_min], prices[idx_min]),
            xytext=(10, -25),
            textcoords="offset points",
            fontsize=8,
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red",
        )
        ax.annotate(
            f"Max: {prices[idx_max]:.2f}",
            xy=(dates[idx_max], prices[idx_max]),
            xytext=(10, 15),
            textcoords="offset points",
            fontsize=8,
            arrowprops=dict(arrowstyle="->", color="green"),
            color="green",
        )

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)

        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel(price_col, fontsize=11)
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Stock price chart saved to %s", output)
        return os.path.abspath(output)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_output_dir(path: str) -> None:
        """Create the parent directory for *path* if it does not exist."""
        directory: str = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
