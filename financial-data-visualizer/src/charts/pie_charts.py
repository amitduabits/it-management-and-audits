"""pie_charts.py
=============

Pie chart generation module for financial data visualization.
Provides the PieChartGenerator class with methods for plotting
expense distribution breakdowns using matplotlib.
"""

import logging
import os
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__author__ = "Dr Amit Dua"

logger = logging.getLogger(__name__)


class PieChartGenerator:
    """Generator for pie-based financial charts.

    Produces clear, labelled pie (and donut) charts suitable for
    expense category breakdowns. All output is rendered as PNG files.
    """

    STYLE: str = "seaborn-v0_8-whitegrid"
    DPI: int = 150
    FIGSIZE: tuple[int, int] = (10, 8)

    # Professional colour palette for category slices
    PALETTE: list[str] = [
        "#2196F3", "#FF9800", "#4CAF50", "#F44336",
        "#9C27B0", "#00BCD4", "#FFEB3B", "#795548",
        "#607D8B", "#E91E63", "#3F51B5", "#8BC34A",
        "#FF5722", "#009688", "#CDDC39", "#673AB7",
    ]

    def __init__(self) -> None:
        """Initialise the PieChartGenerator with default styling."""
        logger.info("PieChartGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot_expense_distribution(
        self,
        df: pd.DataFrame,
        category_col: str,
        value_col: str,
        title: str,
        output: str,
    ) -> str:
        """Plot an expense distribution pie chart.

        Values are aggregated by *category_col* and rendered as
        proportional slices. Small slices (< 2 %) are grouped into an
        "Other" category for readability.

        Parameters
        ----------
        df : pd.DataFrame
            Source data containing category and value columns.
        category_col : str
            Column whose unique values define the slices.
        value_col : str
            Numeric column to sum per category.
        title : str
            Chart title.
        output : str
            Destination file path (PNG).

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating expense distribution chart: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE)

        # ---- data preparation ----
        agg: pd.DataFrame = (
            df.groupby(category_col, sort=False)[value_col]
            .sum()
            .reset_index()
            .sort_values(value_col, ascending=False)
        )

        total: float = float(agg[value_col].sum())

        # Group tiny slices into "Other"
        threshold: float = 0.02 * total
        main_mask: pd.Series = agg[value_col] >= threshold
        main: pd.DataFrame = agg[main_mask].copy()
        other_total: float = float(agg[~main_mask][value_col].sum())

        if other_total > 0:
            other_row = pd.DataFrame(
                {category_col: ["Other"], value_col: [other_total]}
            )
            main = pd.concat([main, other_row], ignore_index=True)

        labels: list[str] = main[category_col].tolist()
        sizes: list[float] = main[value_col].tolist()
        colors: list[str] = self.PALETTE[: len(labels)]

        # Explode the largest slice slightly
        explode: list[float] = [0.05 if i == 0 else 0.0 for i in range(len(labels))]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct=lambda pct: f"{pct:.1f}%\n({pct * total / 100:,.0f})",
            startangle=140,
            pctdistance=0.75,
            wedgeprops=dict(edgecolor="white", linewidth=1.5),
        )

        # Style the percentage labels
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_fontweight("bold")
        for text in texts:
            text.set_fontsize(9)

        # Draw a circle in the centre to create a donut appearance
        centre_circle = plt.Circle((0, 0), 0.50, fc="white")
        ax.add_artist(centre_circle)

        # Centre annotation showing total
        ax.text(
            0, 0,
            f"Total\n{total:,.0f}",
            ha="center", va="center",
            fontsize=12, fontweight="bold",
            color="#333333",
        )

        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
        ax.axis("equal")  # ensure circular shape

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Expense distribution chart saved to %s", output)
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
