"""candlestick.py
=============

Candlestick chart generation module for financial data visualization.
Provides the CandlestickGenerator class with methods for plotting
OHLC candlestick charts using plotly.
"""

import logging
import os
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

__author__ = "Dr Amit Dua"

logger = logging.getLogger(__name__)


class CandlestickGenerator:
    """Generator for OHLC candlestick financial charts.

    Produces interactive candlestick charts rendered to static PNG
    images via plotly. The input DataFrame must contain Open, High,
    Low, and Close columns alongside the date column.
    """

    DEFAULT_WIDTH: int = 1200
    DEFAULT_HEIGHT: int = 700

    # Expected OHLC column names (case-insensitive lookup performed)
    _OHLC_FIELDS: list[str] = ["Open", "High", "Low", "Close"]

    def __init__(self) -> None:
        """Initialise the CandlestickGenerator."""
        logger.info("CandlestickGenerator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot_candlestick(
        self,
        df: pd.DataFrame,
        date_col: str,
        title: str,
        output: str,
    ) -> str:
        """Plot an OHLC candlestick chart.

        The DataFrame is expected to contain columns for Open, High,
        Low, and Close values (case-insensitive matching is applied).
        A volume subplot is added when a ``Volume`` column is present.

        Parameters
        ----------
        df : pd.DataFrame
            Source data with date, open, high, low, close (and
            optionally volume) columns.
        date_col : str
            Name of the datetime column.
        title : str
            Chart title.
        output : str
            Destination file path (PNG).

        Returns
        -------
        str
            Absolute path of the saved chart image.
        """
        logger.info("Generating candlestick chart: %s", title)
        self._ensure_output_dir(output)

        working: pd.DataFrame = df.copy()
        working[date_col] = pd.to_datetime(working[date_col])

        # ---- resolve OHLC column names (case-insensitive) ----
        col_map: dict[str, str] = self._resolve_ohlc_columns(working)

        dates: pd.Series = working[date_col]
        open_vals: pd.Series = working[col_map["Open"]].astype(float)
        high_vals: pd.Series = working[col_map["High"]].astype(float)
        low_vals: pd.Series = working[col_map["Low"]].astype(float)
        close_vals: pd.Series = working[col_map["Close"]].astype(float)

        # ---- determine if volume data is available ----
        volume_col: Optional[str] = self._find_column(working, "Volume")
        has_volume: bool = volume_col is not None

        # ---- build figure ----
        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=open_vals,
                high=high_vals,
                low=low_vals,
                close=close_vals,
                increasing_line_color="#26a69a",
                increasing_fillcolor="#26a69a",
                decreasing_line_color="#ef5350",
                decreasing_fillcolor="#ef5350",
                name="OHLC",
            )
        )

        if has_volume:
            # Add volume as a bar trace on a secondary y-axis
            volume_data: pd.Series = working[volume_col].astype(float)

            # Colour volume bars by direction
            colors: list[str] = [
                "#26a69a" if c >= o else "#ef5350"
                for o, c in zip(open_vals, close_vals)
            ]

            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=volume_data,
                    marker_color=colors,
                    opacity=0.35,
                    name="Volume",
                    yaxis="y2",
                )
            )

            fig.update_layout(
                yaxis2=dict(
                    title="Volume",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    range=[0, float(volume_data.max()) * 3],
                ),
            )

        # ---- layout ----
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis=dict(
                title="Date",
                rangeslider=dict(visible=False),
                type="date",
            ),
            yaxis=dict(title="Price"),
            template="plotly_white",
            width=self.DEFAULT_WIDTH,
            height=self.DEFAULT_HEIGHT,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        # ---- export to PNG ----
        fig.write_image(output, scale=2)

        logger.info("Candlestick chart saved to %s", output)
        return os.path.abspath(output)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_ohlc_columns(cls, df: pd.DataFrame) -> dict[str, str]:
        """Map canonical OHLC names to actual DataFrame column names.

        Raises ``KeyError`` when a required column cannot be found.
        """
        mapping: dict[str, str] = {}
        for field in cls._OHLC_FIELDS:
            found: Optional[str] = cls._find_column(df, field)
            if found is None:
                raise KeyError(
                    f"Required column '{field}' not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )
            mapping[field] = found
        return mapping

    @staticmethod
    def _find_column(df: pd.DataFrame, name: str) -> Optional[str]:
        """Return the actual column name matching *name* (case-insensitive)."""
        lower_map: dict[str, str] = {c.lower(): c for c in df.columns}
        return lower_map.get(name.lower())

    @staticmethod
    def _ensure_output_dir(path: str) -> None:
        """Create the parent directory for *path* if it does not exist."""
        directory: str = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
