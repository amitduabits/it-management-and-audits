"""bar_charts.py
=============

Bar chart generation module for financial data visualization.
Provides the BarChartGenerator class with methods for plotting
monthly comparison bar charts using matplotlib.
"""

import logging
import os
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

__author__ = "Dr Amit Dua"

logger = logging.getLogger(__name__)


class BarChartGenerator:
    """Generator for bar-based financial charts.

    Produces grouped and single-series bar charts suitable for
    monthly comparison of financial metrics. All output is rendered
    as PNG files.
    """

    STYLE: str = "seaborn-v0_8-whitegrid"
    DPI: int = 150
    FIGSIZE: tuple[int, int] = (14, 7)

    # Colour palette for monthly bars (12 months max)
    MONTH_COLORS: list[str] = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf", "#aec7e8", "#ffbb78",
    ]

    def __init__(self) -> None:
        """Initialise the BarChartGenerator with default styling."""
        logger.info("BarChartGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot_monthly_comparison(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        title: str,
        output: str,
    ) -> str:
        """Plot a monthly comparison bar chart.

        The method aggregates *value_col* by calendar month derived from
        *date_col*, then renders a vertical bar chart comparing monthly
        totals.

        Parameters
        ----------
        df : pd.DataFrame
            Source data containing date and value columns.
        date_col : str
            Name of the datetime column used for grouping.
        value_col : str
            Name of the numeric column to aggregate.
        title : str
            Chart title rendered at the top of the figure.
        output : str
            File path (PNG) where the chart will be saved.

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating monthly comparison chart: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE)

        # ---- data preparation ----
        working_df: pd.DataFrame = df.copy()
        working_df[date_col] = pd.to_datetime(working_df[date_col])
        working_df["_year"] = working_df[date_col].dt.year
        working_df["_month"] = working_df[date_col].dt.month
        working_df["_month_label"] = working_df[date_col].dt.strftime("%b %Y")

        monthly: pd.DataFrame = (
            working_df.groupby(["_year", "_month", "_month_label"], sort=True)[value_col]
            .sum()
            .reset_index()
        )

        labels: list[str] = monthly["_month_label"].tolist()
        values: np.ndarray = monthly[value_col].values
        x_positions: np.ndarray = np.arange(len(labels))

        # Assign colours by calendar month
        bar_colors: list[str] = [
            self.MONTH_COLORS[int(m) - 1] for m in monthly["_month"]
        ]

        bars = ax.bar(
            x_positions,
            values,
            width=0.65,
            color=bar_colors,
            edgecolor="white",
            linewidth=0.8,
            alpha=0.88,
        )

        # ---- value labels on top of each bar ----
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + max(values) * 0.01,
                f"{val:,.0f}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

        # ---- average reference line ----
        avg_value: float = float(np.mean(values))
        ax.axhline(
            avg_value,
            linestyle="--",
            linewidth=1.2,
            color="#d62728",
            alpha=0.7,
            label=f"Average: {avg_value:,.0f}",
        )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Month", fontsize=11)
        ax.set_ylabel(value_col, fontsize=11)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(axis="y", alpha=0.3)

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Monthly comparison chart saved to %s", output)
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
