"""heatmaps.py
=============

Heatmap generation module for financial data visualization.
Provides the HeatmapGenerator class with methods for plotting
correlation matrices and volume heatmaps using seaborn.
"""

import logging
import os
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

__author__ = "Dr Amit Dua"

logger = logging.getLogger(__name__)


class HeatmapGenerator:
    """Generator for heatmap-based financial visualizations.

    Produces annotated heatmaps for correlation analysis and
    temporal volume patterns using seaborn. All output is rendered
    as PNG files.
    """

    STYLE: str = "seaborn-v0_8-whitegrid"
    DPI: int = 150
    FIGSIZE_CORR: tuple[int, int] = (12, 10)
    FIGSIZE_VOL: tuple[int, int] = (14, 8)

    def __init__(self) -> None:
        """Initialise the HeatmapGenerator with default styling."""
        logger.info("HeatmapGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot_correlation(
        self,
        df: pd.DataFrame,
        columns: List[str],
        title: str,
        output: str,
    ) -> str:
        """Plot a correlation-matrix heatmap for selected columns.

        Parameters
        ----------
        df : pd.DataFrame
            Source data.
        columns : list[str]
            Numeric column names to include in the matrix.
        title : str
            Chart title.
        output : str
            Destination file path (PNG).

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating correlation heatmap: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE_CORR)

        # ---- compute correlation ----
        corr_matrix: pd.DataFrame = df[columns].corr()

        # Generate a mask for the upper triangle (avoid redundancy)
        mask: np.ndarray = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

        # Custom diverging colour map
        cmap = sns.diverging_palette(220, 20, as_cmap=True)

        sns.heatmap(
            corr_matrix,
            mask=mask,
            cmap=cmap,
            vmin=-1.0,
            vmax=1.0,
            center=0,
            annot=True,
            fmt=".2f",
            linewidths=1.0,
            linecolor="white",
            square=True,
            cbar_kws={"shrink": 0.75, "label": "Correlation"},
            ax=ax,
        )

        ax.set_title(title, fontsize=14, fontweight="bold", pad=16)
        ax.set_xticklabels(
            ax.get_xticklabels(), rotation=45, ha="right", fontsize=9
        )
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Correlation heatmap saved to %s", output)
        return os.path.abspath(output)

    def plot_volume_heatmap(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        title: str,
        output: str,
    ) -> str:
        """Plot a calendar-style volume heatmap (month x day-of-week).

        The data is aggregated into a pivot table with months as rows
        and days of the week as columns for temporal pattern discovery.

        Parameters
        ----------
        df : pd.DataFrame
            Source data with a date column and a numeric value column.
        date_col : str
            Name of the datetime column.
        value_col : str
            Name of the numeric column to aggregate.
        title : str
            Chart title.
        output : str
            Destination file path (PNG).

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating volume heatmap: %s", title)
        self._ensure_output_dir(output)

        plt.style.use(self.STYLE)
        fig, ax = plt.subplots(figsize=self.FIGSIZE_VOL)

        # ---- data preparation ----
        working: pd.DataFrame = df.copy()
        working[date_col] = pd.to_datetime(working[date_col])
        working["_month"] = working[date_col].dt.strftime("%Y-%m")
        working["_dow"] = working[date_col].dt.day_name()

        dow_order: list[str] = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]

        pivot: pd.DataFrame = (
            working.groupby(["_month", "_dow"])[value_col]
            .mean()
            .reset_index()
            .pivot(index="_month", columns="_dow", values=value_col)
        )

        # Reorder columns to standard week order (only keep those present)
        ordered_cols: list[str] = [d for d in dow_order if d in pivot.columns]
        pivot = pivot[ordered_cols]

        sns.heatmap(
            pivot,
            cmap="YlOrRd",
            annot=True,
            fmt=".0f",
            linewidths=0.5,
            linecolor="white",
            cbar_kws={"shrink": 0.8, "label": f"Mean {value_col}"},
            ax=ax,
        )

        ax.set_title(title, fontsize=14, fontweight="bold", pad=16)
        ax.set_xlabel("Day of Week", fontsize=11)
        ax.set_ylabel("Month", fontsize=11)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)

        fig.tight_layout()
        fig.savefig(output, dpi=self.DPI, bbox_inches="tight")
        plt.close(fig)

        logger.info("Volume heatmap saved to %s", output)
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
