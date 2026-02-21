"""scatter_plots.py
=============

Scatter plot generation module for financial data visualization.
Provides the ScatterPlotGenerator class with methods for plotting
outlier detection scatter charts using matplotlib and seaborn.
"""

import logging
import os
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

__author__ = "Dr Amit Dua"

logger = logging.getLogger(__name__)


class ScatterPlotGenerator:
    """Generator for scatter-based financial charts.

    Produces scatter plots with statistical overlays such as
    regression lines and outlier boundaries (IQR-based) for
    anomaly detection. All output is rendered as PNG files.
    """

    STYLE: str = "seaborn-v0_8-whitegrid"
    DPI: int = 150
    FIGSIZE: tuple[int, int] = (12, 8)

    def __init__(self) -> None:
        """Initialise the ScatterPlotGenerator with default styling."""
        logger.info("ScatterPlotGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot_outlier_detection(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        output: str,
    ) -> str:
        """Plot a scatter chart with automatic outlier highlighting.

        Outliers are identified using the Inter-Quartile Range (IQR)
        method on the *y_col* values. Points outside 1.5 x IQR from
        Q1/Q3 are drawn in a contrasting colour and labelled.

        Parameters
        ----------
        df : pd.DataFrame
            Source data.
        x_col : str
            Column for the horizontal axis.
        y_col : str
            Column for the vertical axis (used for outlier detection).
        title : str
            Chart title.
        output : str
            Destination file path (PNG).

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating outlier detection scatter plot: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE)

        x_data: pd.Series = df[x_col].astype(float)
        y_data: pd.Series = df[y_col].astype(float)

        # ---- IQR-based outlier boundaries ----
        q1: float = float(y_data.quantile(0.25))
        q3: float = float(y_data.quantile(0.75))
        iqr: float = q3 - q1
        lower_bound: float = q1 - 1.5 * iqr
        upper_bound: float = q3 + 1.5 * iqr

        is_outlier: pd.Series = (y_data < lower_bound) | (y_data > upper_bound)
        normal_mask: pd.Series = ~is_outlier

        # ---- plot normal points ----
        ax.scatter(
            x_data[normal_mask],
            y_data[normal_mask],
            c="#1f77b4",
            s=50,
            alpha=0.6,
            edgecolors="white",
            linewidths=0.5,
            label="Normal",
            zorder=2,
        )

        # ---- plot outlier points ----
        outlier_count: int = int(is_outlier.sum())
        ax.scatter(
            x_data[is_outlier],
            y_data[is_outlier],
            c="#d62728",
            s=90,
            alpha=0.85,
            edgecolors="black",
            linewidths=1.0,
            marker="X",
            label=f"Outliers ({outlier_count})",
            zorder=3,
        )

        # ---- boundary lines ----
        ax.axhline(
            upper_bound, linestyle="--", linewidth=1.2,
            color="#ff7f0e", alpha=0.7,
            label=f"Upper bound ({upper_bound:,.2f})",
        )
        ax.axhline(
            lower_bound, linestyle="--", linewidth=1.2,
            color="#ff7f0e", alpha=0.7,
            label=f"Lower bound ({lower_bound:,.2f})",
        )

        # ---- regression trend line ----
        if len(x_data) > 2:
            coeffs: np.ndarray = np.polyfit(x_data, y_data, deg=1)
            trend_line: np.ndarray = np.polyval(coeffs, x_data.sort_values())
            ax.plot(
                x_data.sort_values(),
                trend_line,
                linewidth=1.5,
                linestyle="-.",
                color="#2ca02c",
                alpha=0.7,
                label="Trend",
            )

        # ---- text summary box ----
        stats_text: str = (
            f"n = {len(y_data)}\n"
            f"Mean = {y_data.mean():,.2f}\n"
            f"Std = {y_data.std():,.2f}\n"
            f"Outliers = {outlier_count}"
        )
        props = dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.5)
        ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=9, verticalalignment="top",
            bbox=props,
        )

        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel(x_col, fontsize=11)
        ax.set_ylabel(y_col, fontsize=11)
        ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Outlier detection scatter plot saved to %s", output)
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
