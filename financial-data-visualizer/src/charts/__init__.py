"""__init__.py
=============

Charts package initialization module. Imports and exports all chart
generator classes for convenient access from the parent package.
"""

from src.charts.line_charts import LineChartGenerator
from src.charts.bar_charts import BarChartGenerator
from src.charts.pie_charts import PieChartGenerator
from src.charts.heatmaps import HeatmapGenerator
from src.charts.scatter_plots import ScatterPlotGenerator
from src.charts.candlestick import CandlestickGenerator

__author__ = "Dr Amit Dua"

__all__ = [
    "LineChartGenerator",
    "BarChartGenerator",
    "PieChartGenerator",
    "HeatmapGenerator",
    "ScatterPlotGenerator",
    "CandlestickGenerator",
]
