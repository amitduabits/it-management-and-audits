"""
BI Dashboard Builder - Chart Generator

Generates interactive Plotly charts based on data types and dashboard
configuration. Supports line, bar, pie, scatter, heatmap, area, stacked bar,
histogram, box, and treemap chart types.
"""

import json
from typing import Optional

import pandas as pd
import numpy as np
import plotly
import plotly.express as px
import plotly.graph_objects as go

from app.data_processor import DataProcessor


class ChartGenerator:
    """Generate Plotly charts from DataFrames based on configuration."""

    # Professional color palettes
    COLOR_SCHEMES = {
        "blue": ["#1e3a5f", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe"],
        "green": ["#064e3b", "#047857", "#059669", "#10b981", "#34d399", "#6ee7b7", "#a7f3d0"],
        "purple": ["#3b0764", "#6b21a8", "#7c3aed", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"],
        "red": ["#7f1d1d", "#b91c1c", "#dc2626", "#ef4444", "#f87171", "#fca5a5", "#fecaca"],
        "orange": ["#7c2d12", "#c2410c", "#ea580c", "#f97316", "#fb923c", "#fdba74", "#fed7aa"],
        "viridis": ["#440154", "#482777", "#3f4a8a", "#31678e", "#26838f", "#1f9d8a", "#6cce5a"],
        "corporate": ["#1a365d", "#2b6cb0", "#4299e1", "#63b3ed", "#90cdf4", "#bee3f8", "#ebf8ff"],
        "warm": ["#9b2c2c", "#c53030", "#e53e3e", "#fc8181", "#feb2b2", "#fed7d7", "#fff5f5"],
        "cool": ["#2a4365", "#2b6cb0", "#3182ce", "#4299e1", "#63b3ed", "#90cdf4", "#bee3f8"],
        "default": px.colors.qualitative.Set2,
    }

    CHART_LAYOUT_DEFAULTS = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, system-ui, sans-serif", "size": 12, "color": "#374151"},
        "margin": {"l": 50, "r": 30, "t": 50, "b": 50},
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.25,
            "xanchor": "center",
            "x": 0.5,
        },
        "hoverlabel": {
            "bgcolor": "white",
            "font_size": 13,
            "font_family": "Inter, system-ui, sans-serif",
        },
    }

    def __init__(self):
        self.processor = DataProcessor()

    # -----------------------------------------------------------------------
    # Public Interface
    # -----------------------------------------------------------------------

    def generate_all(self, df: pd.DataFrame, chart_configs: list[dict]) -> list[dict]:
        """Generate all charts defined in the configuration."""
        charts = []
        for i, cfg in enumerate(chart_configs):
            try:
                chart = self.generate_single(df, cfg)
                chart["index"] = i
                charts.append(chart)
            except Exception as exc:
                charts.append({
                    "index": i,
                    "error": str(exc),
                    "title": cfg.get("title", f"Chart {i + 1}"),
                    "html": f'<div class="chart-error">Error generating chart: {exc}</div>',
                })
        return charts

    def generate_single(self, df: pd.DataFrame, cfg: dict) -> dict:
        """Generate a single chart from configuration."""
        chart_type = cfg.get("type", "bar").lower()

        type_map = {
            "line": self._line_chart,
            "bar": self._bar_chart,
            "pie": self._pie_chart,
            "donut": self._donut_chart,
            "scatter": self._scatter_chart,
            "area": self._area_chart,
            "heatmap": self._heatmap_chart,
            "stacked_bar": self._stacked_bar_chart,
            "histogram": self._histogram_chart,
            "box": self._box_chart,
            "treemap": self._treemap_chart,
            "waterfall": self._waterfall_chart,
            "funnel": self._funnel_chart,
        }

        generator = type_map.get(chart_type, self._bar_chart)
        fig = generator(df, cfg)

        # Apply standard layout
        layout_updates = {**self.CHART_LAYOUT_DEFAULTS}
        layout_updates["title"] = {
            "text": cfg.get("title", ""),
            "font": {"size": 16, "color": "#1f2937", "family": "Inter, system-ui, sans-serif"},
            "x": 0.5,
            "xanchor": "center",
        }

        if cfg.get("height"):
            layout_updates["height"] = cfg["height"]
        else:
            layout_updates["height"] = 400

        fig.update_layout(**layout_updates)

        # Apply grid styling for non-pie charts
        if chart_type not in ("pie", "donut", "treemap", "funnel"):
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(229, 231, 235, 0.8)",
                zeroline=False,
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(229, 231, 235, 0.8)",
                zeroline=False,
            )

        # Convert to HTML and JSON
        html = plotly.io.to_html(fig, full_html=False, include_plotlyjs=False, config={
            "responsive": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "displaylogo": False,
        })

        chart_json = json.loads(plotly.io.to_json(fig))

        return {
            "title": cfg.get("title", ""),
            "type": chart_type,
            "html": html,
            "json": chart_json,
        }

    # -----------------------------------------------------------------------
    # Chart Generators
    # -----------------------------------------------------------------------

    def _get_colors(self, cfg: dict, n: int = 7) -> list[str]:
        """Get color palette from config."""
        scheme = cfg.get("color_scheme", "default")
        return self.COLOR_SCHEMES.get(scheme, self.COLOR_SCHEMES["default"])[:n]

    def _line_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a line chart (time series)."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")
        agg = cfg.get("agg", "sum")
        color = cfg.get("color")

        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            plot_df = df[[x_col, y_col]].dropna()

            if pd.api.types.is_datetime64_any_dtype(plot_df[x_col]):
                plot_df = plot_df.set_index(x_col).resample("M").agg(agg).reset_index()

            if color and color in df.columns:
                full_df = df[[x_col, y_col, color]].dropna()
                fig = px.line(
                    full_df.groupby([x_col, color])[y_col].agg(agg).reset_index(),
                    x=x_col, y=y_col, color=color,
                    color_discrete_sequence=self._get_colors(cfg, 10),
                )
            else:
                fig = go.Figure()
                colors = self._get_colors(cfg)
                fig.add_trace(go.Scatter(
                    x=plot_df[x_col],
                    y=plot_df[y_col],
                    mode="lines+markers",
                    line={"width": 2.5, "color": colors[1] if len(colors) > 1 else colors[0]},
                    marker={"size": 5},
                    fill="tonexty" if cfg.get("fill") else None,
                    fillcolor=f"rgba(37, 99, 235, 0.1)" if cfg.get("fill") else None,
                ))

            fig.update_layout(
                xaxis_title=x_col.replace("_", " ").title(),
                yaxis_title=y_col.replace("_", " ").title(),
            )
            return fig

        return go.Figure()

    def _bar_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a bar chart."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")
        agg = cfg.get("agg", "sum")
        orientation = cfg.get("orientation", "v")

        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
            grouped = grouped.sort_values(y_col, ascending=False).head(cfg.get("top_n", 20))

            colors = self._get_colors(cfg, len(grouped))

            fig = go.Figure()
            if orientation == "h":
                fig.add_trace(go.Bar(
                    y=grouped[x_col], x=grouped[y_col],
                    orientation="h",
                    marker_color=colors[1] if len(colors) > 1 else colors[0],
                    marker_line={"width": 0},
                ))
            else:
                fig.add_trace(go.Bar(
                    x=grouped[x_col], y=grouped[y_col],
                    marker_color=[colors[i % len(colors)] for i in range(len(grouped))],
                    marker_line={"width": 0},
                ))

            fig.update_layout(
                xaxis_title=x_col.replace("_", " ").title(),
                yaxis_title=y_col.replace("_", " ").title(),
            )
            return fig

        return go.Figure()

    def _pie_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a pie chart."""
        labels_col = cfg.get("labels")
        values_col = cfg.get("values")
        agg = cfg.get("agg", "sum")

        if labels_col and values_col and labels_col in df.columns and values_col in df.columns:
            grouped = df.groupby(labels_col)[values_col].agg(agg).reset_index()
            grouped = grouped.sort_values(values_col, ascending=False).head(10)

            colors = self._get_colors(cfg, len(grouped))

            fig = go.Figure(data=[go.Pie(
                labels=grouped[labels_col],
                values=grouped[values_col],
                hole=0,
                marker={"colors": colors, "line": {"color": "white", "width": 2}},
                textposition="auto",
                textinfo="label+percent",
                textfont={"size": 12},
            )])
            return fig

        return go.Figure()

    def _donut_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a donut chart (pie with hole)."""
        fig = self._pie_chart(df, cfg)
        fig.update_traces(hole=0.5)
        return fig

    def _scatter_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a scatter plot."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")
        color_col = cfg.get("color")
        size_col = cfg.get("size")

        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            plot_df = df[[c for c in [x_col, y_col, color_col, size_col] if c and c in df.columns]].dropna()

            fig = px.scatter(
                plot_df,
                x=x_col, y=y_col,
                color=color_col if color_col and color_col in plot_df.columns else None,
                size=size_col if size_col and size_col in plot_df.columns else None,
                color_discrete_sequence=self._get_colors(cfg, 10),
                opacity=0.7,
            )
            fig.update_traces(marker={"line": {"width": 1, "color": "white"}})
            fig.update_layout(
                xaxis_title=x_col.replace("_", " ").title(),
                yaxis_title=y_col.replace("_", " ").title(),
            )
            return fig

        return go.Figure()

    def _area_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate an area chart."""
        cfg_copy = {**cfg, "fill": True}
        return self._line_chart(df, cfg_copy)

    def _heatmap_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a heatmap."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")
        values_col = cfg.get("values")
        agg = cfg.get("agg", "sum")

        if all(c in df.columns for c in [x_col, y_col, values_col] if c):
            pivot = pd.pivot_table(
                df, index=y_col, columns=x_col, values=values_col,
                aggfunc=agg, fill_value=0,
            )

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=[str(c) for c in pivot.columns],
                y=[str(i) for i in pivot.index],
                colorscale="Blues",
                hoverongaps=False,
            ))
            fig.update_layout(
                xaxis_title=x_col.replace("_", " ").title(),
                yaxis_title=y_col.replace("_", " ").title(),
            )
            return fig

        return go.Figure()

    def _stacked_bar_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a stacked bar chart."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")
        stack_by = cfg.get("stack_by")
        agg = cfg.get("agg", "sum")

        if all(c in df.columns for c in [x_col, y_col, stack_by] if c):
            grouped = df.groupby([x_col, stack_by])[y_col].agg(agg).reset_index()

            fig = px.bar(
                grouped, x=x_col, y=y_col, color=stack_by,
                barmode="stack",
                color_discrete_sequence=self._get_colors(cfg, 10),
            )
            fig.update_layout(
                xaxis_title=x_col.replace("_", " ").title(),
                yaxis_title=y_col.replace("_", " ").title(),
            )
            return fig

        return go.Figure()

    def _histogram_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a histogram."""
        x_col = cfg.get("x")
        nbins = cfg.get("bins", 30)

        if x_col and x_col in df.columns:
            colors = self._get_colors(cfg)
            fig = go.Figure(data=[go.Histogram(
                x=df[x_col].dropna(),
                nbinsx=nbins,
                marker_color=colors[1] if len(colors) > 1 else colors[0],
                marker_line={"width": 1, "color": "white"},
            )])
            fig.update_layout(xaxis_title=x_col.replace("_", " ").title(), yaxis_title="Count")
            return fig

        return go.Figure()

    def _box_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a box plot."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")

        if y_col and y_col in df.columns:
            if x_col and x_col in df.columns:
                fig = px.box(
                    df, x=x_col, y=y_col,
                    color_discrete_sequence=self._get_colors(cfg, 10),
                )
            else:
                fig = px.box(
                    df, y=y_col,
                    color_discrete_sequence=self._get_colors(cfg, 10),
                )
            return fig

        return go.Figure()

    def _treemap_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a treemap chart."""
        path_cols = cfg.get("path", [])
        values_col = cfg.get("values")
        agg = cfg.get("agg", "sum")

        if path_cols and values_col and values_col in df.columns:
            valid_paths = [c for c in path_cols if c in df.columns]
            if valid_paths:
                grouped = df.groupby(valid_paths)[values_col].agg(agg).reset_index()
                fig = px.treemap(
                    grouped,
                    path=valid_paths,
                    values=values_col,
                    color=values_col,
                    color_continuous_scale="Blues",
                )
                return fig

        return go.Figure()

    def _waterfall_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a waterfall chart."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")

        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            plot_df = df[[x_col, y_col]].dropna().head(20)

            fig = go.Figure(go.Waterfall(
                x=plot_df[x_col],
                y=plot_df[y_col],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#10b981"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": "#3b82f6"}},
            ))
            fig.update_layout(
                xaxis_title=x_col.replace("_", " ").title(),
                yaxis_title=y_col.replace("_", " ").title(),
            )
            return fig

        return go.Figure()

    def _funnel_chart(self, df: pd.DataFrame, cfg: dict) -> go.Figure:
        """Generate a funnel chart."""
        x_col = cfg.get("x")
        y_col = cfg.get("y")

        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            grouped = df.groupby(x_col)[y_col].sum().reset_index()
            grouped = grouped.sort_values(y_col, ascending=False)

            fig = go.Figure(go.Funnel(
                y=grouped[x_col],
                x=grouped[y_col],
                marker={"color": self._get_colors(cfg, len(grouped))},
            ))
            return fig

        return go.Figure()
