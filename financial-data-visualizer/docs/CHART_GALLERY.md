# Chart Gallery

A reference guide to every visualization type available in the Financial Data Visualizer. Each section describes the chart, its ideal use case, the data it requires, and key configuration options.

---

## 1. Revenue Trend Line Chart

**Module:** `src.charts.line_charts.LineChartGenerator.plot_trend`

**Description:**
A single time-series line with optional area fill beneath the curve. Displays values over time with a clean, professional aesthetic.

**When to Use:**
- Tracking revenue, profit, or any single metric over time
- Identifying long-term growth or decline patterns
- Detecting seasonal cycles in financial data

**Required Data:**
- A date column (datetime)
- A numeric value column

**Key Options:**
- `fill=True` -- Shade the area under the curve for visual weight
- `color` -- Custom hex color for the line
- `ylabel` -- Axis label for the value dimension

---

## 2. Stock Price with Moving Averages

**Module:** `src.charts.line_charts.LineChartGenerator.plot_stock_price`

**Description:**
Closing price plotted as a solid line with dashed moving average overlays (default: 7, 30, and 90-day). Moving averages help smooth noise and reveal trends.

**When to Use:**
- Technical analysis of equity or fund performance
- Identifying crossover signals between short and long MAs
- Visualizing price momentum and trend direction

**Required Data:**
- `date` column
- `close` column (closing price)

**Key Options:**
- `windows` -- List of MA window sizes, e.g. `[7, 30, 90]`
- Customizable colors for each MA line

---

## 3. Multi-Line Comparison

**Module:** `src.charts.line_charts.LineChartGenerator.plot_multi_line`

**Description:**
Multiple numeric columns plotted as separate colored lines on the same time axis. Useful for comparing related metrics.

**When to Use:**
- Comparing revenue vs. expenses over time
- Overlaying multiple cost centers or business units
- Tracking multiple KPIs on a single chart

**Required Data:**
- A date column
- Two or more numeric columns

---

## 4. Monthly Comparison Bar Chart

**Module:** `src.charts.bar_charts.BarChartGenerator.plot_monthly_comparison`

**Description:**
Vertical bars showing monthly totals, colored green for positive and red for negative values. Each bar is labeled with its dollar amount.

**When to Use:**
- Period-over-period financial comparison
- Identifying months of net loss vs. net gain
- Budget tracking and variance analysis

**Required Data:**
- `date` column
- Numeric value column (e.g., `amount`, `net_income`)

---

## 5. Category Breakdown Bar Chart

**Module:** `src.charts.bar_charts.BarChartGenerator.plot_category_breakdown`

**Description:**
Horizontal bars showing aggregated values per category, sorted from smallest to largest. Uses a blue gradient palette for visual hierarchy.

**When to Use:**
- Identifying the largest expense categories
- Comparing spending across departments or cost centers
- Budget allocation review

**Required Data:**
- A categorical column (e.g., `category`, `department`)
- A numeric value column

---

## 6. Top-N Analysis Bar Chart

**Module:** `src.charts.bar_charts.BarChartGenerator.plot_top_n`

**Description:**
Vertical bars ranking the top N items (merchants, products, clients) by aggregated value. Uses a viridis gradient for visual distinction.

**When to Use:**
- Identifying key revenue drivers
- Finding the biggest expense sinks
- Vendor or client concentration analysis

**Key Options:**
- `n` -- Number of top items to display (default: 10)
- `agg` -- Aggregation function: `sum`, `mean`, or `count`
- `label_col` -- Column to group by

---

## 7. Stacked Monthly Bar Chart

**Module:** `src.charts.bar_charts.BarChartGenerator.plot_stacked_monthly`

**Description:**
Stacked vertical bars showing how monthly totals break down by category. Each color represents a different category.

**When to Use:**
- Understanding composition of monthly spending
- Tracking category proportions over time
- Identifying which categories drive overall trends

---

## 8. Expense Distribution Pie/Donut Chart

**Module:** `src.charts.pie_charts.PieChartGenerator.plot_expense_distribution`

**Description:**
A donut (or traditional pie) chart showing the proportional breakdown of expenses by category. Small categories are automatically grouped into "Other."

**When to Use:**
- Quick overview of where money is being spent
- Budget allocation presentations
- Executive-level financial summaries

**Key Options:**
- `min_pct` -- Minimum slice percentage before grouping into "Other"
- `donut=True` -- Render as a donut with center total

---

## 9. Revenue by Segment Pie Chart

**Module:** `src.charts.pie_charts.PieChartGenerator.plot_revenue_segments`

**Description:**
Shows revenue share across business segments, product lines, or geographic regions. Can accept either a dictionary or a DataFrame.

**When to Use:**
- Portfolio composition analysis
- Revenue diversification assessment
- Investor presentations

---

## 10. Correlation Heatmap

**Module:** `src.charts.heatmaps.HeatmapGenerator.plot_correlation`

**Description:**
A color-coded matrix showing Pearson (or Spearman/Kendall) correlations between all numeric columns. Uses a diverging red-blue color scale centered at zero. Optionally masks the upper triangle for cleaner display.

**When to Use:**
- Identifying relationships between financial metrics
- Feature selection for predictive models
- Understanding co-movement between revenue lines

**Key Options:**
- `method` -- `pearson`, `spearman`, or `kendall`
- `mask_upper` -- Hide redundant upper triangle
- `annot` -- Show correlation values in each cell

---

## 11. Transaction Volume Heatmap

**Module:** `src.charts.heatmaps.HeatmapGenerator.plot_volume_heatmap`

**Description:**
A grid heatmap with hours of the day on the y-axis and days of the week on the x-axis. Cell values represent transaction count or total amount.

**When to Use:**
- Discovering operational patterns (peak transaction hours)
- Capacity planning for payment processing
- Fraud detection (unusual activity patterns)

**Key Options:**
- `agg` -- `count` for transaction frequency, `sum` for dollar volume

---

## 12. Risk vs. Return Scatter Plot

**Module:** `src.charts.scatter_plots.ScatterPlotGenerator.plot_risk_return`

**Description:**
Each point represents an asset, plotted by its volatility (x-axis) vs. expected return (y-axis). Points are colored by their return/risk ratio. Optionally includes an approximate efficient frontier curve.

**When to Use:**
- Portfolio optimization discussions
- Comparing risk-adjusted performance across assets
- Investment committee presentations

**Key Options:**
- `show_frontier` -- Approximate efficient frontier curve
- Assets passed as a dictionary of `{name: (risk, return)}` tuples

---

## 13. Outlier Detection Scatter Plot

**Module:** `src.charts.scatter_plots.ScatterPlotGenerator.plot_outlier_detection`

**Description:**
Scatter plot of individual data points with statistical outliers highlighted in red diamonds. Boundary lines show the IQR or Z-score thresholds.

**When to Use:**
- Fraud detection in transaction data
- Data quality auditing
- Identifying unusual financial activity

**Key Options:**
- `method` -- `iqr` or `zscore`
- `factor` -- IQR multiplier or Z-score threshold

---

## 14. OHLC Candlestick Chart

**Module:** `src.charts.candlestick.CandlestickGenerator.plot_candlestick`

**Description:**
Traditional candlestick chart with green (bullish) and red (bearish) candle bodies, high-low wicks, an optional volume subplot, and moving average overlays.

**When to Use:**
- Daily market analysis and trading decisions
- Earnings report presentations
- Technical analysis with price patterns

**Required Data:**
- `date`, `open`, `high`, `low`, `close` columns
- Optional: `volume` column

**Key Options:**
- `show_volume` -- Include volume bar subplot
- `show_ma` -- Overlay moving averages
- `ma_windows` -- Moving average periods (default: [20, 50])
- `last_n` -- Show only the most recent N trading days

---

## 15. Interactive HTML Dashboard

**Module:** `src.dashboard.DashboardBuilder`

**Description:**
A self-contained HTML file combining multiple Plotly interactive charts into a single scrollable report. Includes monthly transaction bars, category pie, OHLC candlestick, revenue/expense lines, correlation heatmap, and outlier scatter.

**When to Use:**
- Generating stakeholder-facing reports
- Periodic financial review meetings
- Self-service analytics that non-technical users can open in a browser

**Key Options:**
- `theme` -- Plotly templates: `plotly_white`, `plotly_dark`, `ggplot2`
- `title` -- Custom dashboard header

---

## Choosing the Right Chart

| Question | Recommended Chart |
|---|---|
| How does a metric change over time? | Line chart (trend or stock price) |
| How do months compare to each other? | Monthly comparison bar chart |
| What are the biggest categories? | Category breakdown or top-N bar chart |
| What proportion of total does each part represent? | Pie/donut chart |
| Are my financial variables correlated? | Correlation heatmap |
| When are transactions most frequent? | Volume heatmap (hour x day) |
| Which points are statistical anomalies? | Outlier detection scatter plot |
| How does risk compare to return? | Risk vs. return scatter |
| What is the full OHLC picture? | Candlestick chart |
| How do I combine everything? | HTML dashboard |
