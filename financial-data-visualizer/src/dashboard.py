"""
dashboard.py
============

Interactive HTML dashboard builder using Plotly. Combines multiple
visualizations into a single navigable report with tabs for each
dataset and chart type.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class DashboardBuilder:
    """
    Build a self-contained HTML dashboard from financial datasets.

    Parameters
    ----------
    data_dir : str or Path
        Directory containing CSV datasets (transactions.csv,
        market_data.csv, revenue_expenses.csv).
    title : str
        Dashboard page title.
    theme : str
        Plotly template name ('plotly_dark', 'plotly_white', etc.).
    """

    def __init__(
        self,
        data_dir: str = "data/",
        title: str = "Financial Data Dashboard",
        theme: str = "plotly_white",
    ):
        self.data_dir = Path(data_dir)
        self.title = title
        self.theme = theme
        self._datasets: Dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Data Loading
    # ------------------------------------------------------------------

    def _load_datasets(self) -> None:
        """Load all recognized datasets from the data directory."""
        files = {
            "transactions": "transactions.csv",
            "market": "market_data.csv",
            "pnl": "revenue_expenses.csv",
        }
        for key, filename in files.items():
            path = self.data_dir / filename
            if path.exists():
                df = pd.read_csv(path)
                df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                self._datasets[key] = df
                logger.info("Loaded %s (%d rows)", filename, len(df))
            else:
                logger.warning("Dataset not found: %s", path)

    # ------------------------------------------------------------------
    # Chart Builders
    # ------------------------------------------------------------------

    def _build_transaction_overview(self) -> go.Figure:
        """Monthly transaction totals as a bar chart."""
        df = self._datasets.get("transactions")
        if df is None:
            return go.Figure()

        monthly = df.set_index("date")["amount"].resample("M").sum().reset_index()
        monthly.columns = ["date", "total"]

        colors = ["#10B981" if v >= 0 else "#EF4444" for v in monthly["total"]]

        fig = go.Figure(
            go.Bar(
                x=monthly["date"],
                y=monthly["total"],
                marker_color=colors,
                text=[f"${v:,.0f}" for v in monthly["total"]],
                textposition="outside",
                name="Monthly Net",
            )
        )
        fig.update_layout(
            title=dict(text="Monthly Transaction Summary", font=dict(size=18)),
            xaxis_title="Month",
            yaxis_title="Net Amount ($)",
            template=self.theme,
            height=500,
        )
        return fig

    def _build_category_breakdown(self) -> go.Figure:
        """Pie chart of expense categories."""
        df = self._datasets.get("transactions")
        if df is None:
            return go.Figure()

        expenses = df[df["amount"] < 0].copy()
        expenses["amount"] = expenses["amount"].abs()
        cat_totals = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)

        fig = go.Figure(
            go.Pie(
                labels=cat_totals.index,
                values=cat_totals.values,
                hole=0.45,
                textinfo="label+percent",
                marker=dict(
                    colors=px.colors.qualitative.Set2[: len(cat_totals)],
                    line=dict(color="white", width=2),
                ),
            )
        )
        fig.update_layout(
            title=dict(text="Expense Distribution by Category", font=dict(size=18)),
            template=self.theme,
            height=500,
        )
        return fig

    def _build_stock_price_chart(self) -> go.Figure:
        """Candlestick chart with volume from market data."""
        df = self._datasets.get("market")
        if df is None:
            return go.Figure()

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=("Price", "Volume"),
        )

        fig.add_trace(
            go.Candlestick(
                x=df["date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                increasing_line_color="#10B981",
                decreasing_line_color="#EF4444",
                name="OHLC",
            ),
            row=1, col=1,
        )

        # Moving averages
        for window, color, name in [(20, "#F59E0B", "20-Day MA"), (50, "#8B5CF6", "50-Day MA")]:
            ma = df["close"].rolling(window=window, min_periods=1).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["date"], y=ma,
                    mode="lines",
                    line=dict(color=color, width=1.5, dash="dash"),
                    name=name,
                ),
                row=1, col=1,
            )

        # Volume bars
        colors = [
            "#A7F3D0" if df["close"].iloc[i] >= df["open"].iloc[i] else "#FECACA"
            for i in range(len(df))
        ]
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                marker_color=colors,
                name="Volume",
                showlegend=False,
            ),
            row=2, col=1,
        )

        fig.update_layout(
            title=dict(text="Market Data -- OHLC with Volume", font=dict(size=18)),
            xaxis_rangeslider_visible=False,
            template=self.theme,
            height=700,
        )
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

        return fig

    def _build_revenue_expenses_chart(self) -> go.Figure:
        """Revenue, expenses, and net income over time."""
        df = self._datasets.get("pnl")
        if df is None:
            return go.Figure()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["date"], y=df["revenue"],
            mode="lines+markers",
            name="Revenue",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(size=6),
        ))

        # Total expenses
        expense_cols = [c for c in df.columns if c not in ("date", "revenue", "net_income")]
        if expense_cols:
            total_expenses = df[expense_cols].sum(axis=1)
            fig.add_trace(go.Scatter(
                x=df["date"], y=total_expenses,
                mode="lines+markers",
                name="Total Expenses",
                line=dict(color="#EF4444", width=2),
                marker=dict(size=5),
            ))

        fig.add_trace(go.Bar(
            x=df["date"], y=df["net_income"],
            name="Net Income",
            marker_color=[
                "#10B981" if v >= 0 else "#F87171" for v in df["net_income"]
            ],
            opacity=0.6,
        ))

        fig.update_layout(
            title=dict(text="Revenue, Expenses & Net Income", font=dict(size=18)),
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            template=self.theme,
            height=550,
            barmode="overlay",
        )
        return fig

    def _build_correlation_heatmap(self) -> go.Figure:
        """Correlation heatmap for revenue/expense metrics."""
        df = self._datasets.get("pnl")
        if df is None:
            return go.Figure()

        numeric = df.select_dtypes(include=[np.number])
        corr = numeric.corr()

        labels = [c.replace("_", " ").title() for c in corr.columns]

        fig = go.Figure(
            go.Heatmap(
                z=corr.values,
                x=labels,
                y=labels,
                colorscale="RdBu_r",
                zmin=-1, zmax=1,
                text=np.round(corr.values, 2),
                texttemplate="%{text:.2f}",
                textfont=dict(size=10),
                hovertemplate="x: %{x}<br>y: %{y}<br>r: %{z:.3f}<extra></extra>",
                colorbar=dict(title="Correlation"),
            )
        )
        fig.update_layout(
            title=dict(text="Financial Metrics Correlation", font=dict(size=18)),
            template=self.theme,
            height=600,
            width=700,
        )
        return fig

    def _build_outlier_scatter(self) -> go.Figure:
        """Scatter plot highlighting transaction outliers."""
        df = self._datasets.get("transactions")
        if df is None:
            return go.Figure()

        q1 = df["amount"].quantile(0.25)
        q3 = df["amount"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        df = df.copy()
        df["is_outlier"] = (df["amount"] < lower) | (df["amount"] > upper)

        fig = go.Figure()

        normal = df[~df["is_outlier"]]
        outliers = df[df["is_outlier"]]

        fig.add_trace(go.Scatter(
            x=normal["date"], y=normal["amount"],
            mode="markers",
            name="Normal",
            marker=dict(color="#2563EB", size=5, opacity=0.4),
        ))

        fig.add_trace(go.Scatter(
            x=outliers["date"], y=outliers["amount"],
            mode="markers",
            name=f"Outliers (n={len(outliers)})",
            marker=dict(color="#EF4444", size=10, symbol="diamond", opacity=0.9,
                        line=dict(width=1, color="#991B1B")),
        ))

        fig.add_hline(y=upper, line_dash="dash", line_color="#F59E0B",
                       annotation_text=f"Upper: ${upper:,.0f}")
        fig.add_hline(y=lower, line_dash="dash", line_color="#F59E0B",
                       annotation_text=f"Lower: ${lower:,.0f}")

        fig.update_layout(
            title=dict(text="Transaction Outlier Detection", font=dict(size=18)),
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            template=self.theme,
            height=500,
        )
        return fig

    # ------------------------------------------------------------------
    # Build HTML
    # ------------------------------------------------------------------

    def build(self, output_path: str = "dashboard.html") -> str:
        """
        Generate the complete HTML dashboard.

        Parameters
        ----------
        output_path : str
            File path for the output HTML.

        Returns
        -------
        str
            Absolute path to the generated file.
        """
        self._load_datasets()

        charts = []

        if "transactions" in self._datasets:
            charts.append(("transaction_overview", self._build_transaction_overview()))
            charts.append(("category_breakdown", self._build_category_breakdown()))
            charts.append(("outlier_scatter", self._build_outlier_scatter()))

        if "market" in self._datasets:
            charts.append(("stock_price", self._build_stock_price_chart()))

        if "pnl" in self._datasets:
            charts.append(("revenue_expenses", self._build_revenue_expenses_chart()))
            charts.append(("correlation", self._build_correlation_heatmap()))

        # Build HTML with embedded Plotly
        chart_divs = []
        for chart_id, fig in charts:
            div_html = fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)
            chart_divs.append(f'<div class="chart-container">{div_html}</div>')

        html = self._render_template(chart_divs)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        abs_path = os.path.abspath(output_path)
        logger.info("Dashboard saved to %s", abs_path)
        return abs_path

    # ------------------------------------------------------------------
    # HTML Template
    # ------------------------------------------------------------------

    def _render_template(self, chart_divs: list) -> str:
        """Assemble the full HTML page."""
        charts_html = "\n".join(chart_divs)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         Oxygen, Ubuntu, sans-serif;
            background-color: #F8FAFC;
            color: #1E293B;
            line-height: 1.6;
        }}
        header {{
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            color: white;
            padding: 2rem 3rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        header h1 {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        header p {{
            font-size: 1rem;
            color: #94A3B8;
            margin-top: 0.5rem;
        }}
        .dashboard-meta {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.85rem;
            color: #CBD5E1;
        }}
        .dashboard-meta span {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        main {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        .chart-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1),
                        0 1px 2px rgba(0, 0, 0, 0.06);
            margin-bottom: 2rem;
            padding: 1.5rem;
            transition: box-shadow 0.2s;
        }}
        .chart-container:hover {{
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1),
                        0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: #64748B;
            font-size: 0.85rem;
            border-top: 1px solid #E2E8F0;
            margin-top: 2rem;
        }}
        @media (max-width: 768px) {{
            header {{
                padding: 1.5rem;
            }}
            main {{
                padding: 0 1rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{self.title}</h1>
        <p>Interactive financial analytics and data visualization report</p>
        <div class="dashboard-meta">
            <span>Generated with Financial Data Visualizer v1.0</span>
        </div>
    </header>
    <main>
        {charts_html}
    </main>
    <footer>
        <p>Financial Data Visualizer &mdash; Professional Analytics Dashboard</p>
    </footer>
</body>
</html>"""
