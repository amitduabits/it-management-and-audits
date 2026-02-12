# KPI Calculations Reference

Complete reference for all Key Performance Indicator calculations available
in the BI Dashboard Builder. This document covers formulas, use cases,
configuration options, and interpretation guidance.

---

## Table of Contents

1. [Overview](#overview)
2. [Basic Aggregations](#basic-aggregations)
3. [Statistical Measures](#statistical-measures)
4. [Percentile Functions](#percentile-functions)
5. [Growth & Trend Analysis](#growth--trend-analysis)
6. [Comparison Metrics](#comparison-metrics)
7. [Formatting Options](#formatting-options)
8. [Period Comparison Logic](#period-comparison-logic)
9. [Advanced KPI Methods](#advanced-kpi-methods)

---

## Overview

The KPI Calculator (`kpi_calculator.py`) processes a pandas DataFrame and
a list of KPI configuration objects. Each configuration specifies:

- **column** - The data column to analyze
- **function** - The aggregation or statistical function to apply
- **format** - How to display the result
- **compare_periods** - Whether to calculate period-over-period change

The calculator returns structured results including the raw value, formatted
display string, trend direction, and change percentage.

---

## Basic Aggregations

### Sum
**Function name:** `sum`

Adds all numeric values in the specified column.

**Formula:** `SUM(column)`

**Use cases:**
- Total revenue, total expenses, total units sold
- Cumulative metrics across all records

**Example config:**
```json
{"label": "Total Revenue", "column": "amount", "function": "sum", "format": "currency"}
```

---

### Count
**Function name:** `count`

Returns the total number of rows in the dataset (ignores the column value).

**Formula:** `COUNT(rows)`

**Use cases:**
- Total number of orders, transactions, or records
- Volume metrics

---

### Unique Count
**Function name:** `unique_count`

Counts distinct values in the specified column.

**Formula:** `COUNT(DISTINCT column)`

**Use cases:**
- Number of unique customers, products, or regions
- Cardinality analysis

---

### Mean / Average
**Function names:** `mean`, `avg`, `average`

Computes the arithmetic average.

**Formula:** `SUM(column) / COUNT(non-null values)`

**Use cases:**
- Average order value, average transaction size
- Per-unit or per-record metrics

---

### Minimum
**Function name:** `min`

Returns the smallest value.

**Formula:** `MIN(column)`

**Use cases:**
- Lowest sale, minimum inventory level
- Threshold identification

---

### Maximum
**Function name:** `max`

Returns the largest value.

**Formula:** `MAX(column)`

**Use cases:**
- Highest sale, peak performance
- Outlier identification

---

## Statistical Measures

### Median
**Function name:** `median`

The middle value when data is sorted. Less sensitive to outliers than the mean.

**Formula:** 50th percentile of sorted values

**Use cases:**
- Typical order value (when distribution is skewed)
- Salary benchmarking

---

### Standard Deviation
**Function name:** `std`

Measures the spread or dispersion of values around the mean.

**Formula:** `SQRT(SUM((x - mean)^2) / (n - 1))`

**Use cases:**
- Revenue volatility, quality control
- Risk assessment

---

### Variance
**Function name:** `var`

The square of the standard deviation. Represents data spread.

**Formula:** `SUM((x - mean)^2) / (n - 1)`

---

### Range
**Function name:** `range`

The difference between the maximum and minimum values.

**Formula:** `MAX(column) - MIN(column)`

**Use cases:**
- Price spread, performance range
- Data quality checks

---

### Coefficient of Variation
**Function name:** `cv`

Relative standard deviation expressed as a percentage. Useful for comparing
variability between datasets with different means.

**Formula:** `(std / mean) * 100`

**Use cases:**
- Comparing consistency across product lines
- Normalizing variability for benchmarking

---

## Percentile Functions

Percentiles divide sorted data into 100 equal parts. They indicate what
percentage of values fall below a given threshold.

| Function | Description                       | Common Use                    |
|----------|-----------------------------------|-------------------------------|
| `p25`    | 25th percentile (Q1)              | Lower quartile boundary       |
| `p75`    | 75th percentile (Q3)              | Upper quartile boundary       |
| `p90`    | 90th percentile                   | High-performance threshold    |
| `p95`    | 95th percentile                   | Near-maximum performance      |
| `p99`    | 99th percentile                   | Outlier boundary              |
| `iqr`    | Interquartile range (Q3 - Q1)     | Core spread of data           |

### Interquartile Range (IQR)

**Formula:** `P75 - P25`

Represents the range of the middle 50% of data. Used to identify outliers:
values below `P25 - 1.5*IQR` or above `P75 + 1.5*IQR` are often considered
outliers.

---

## Growth & Trend Analysis

### Growth Rate
**Method:** `growth_rate(df, date_col, value_col, periods=1)`

Calculates the percentage change between the most recent period and a
previous period.

**Formula:** `((current - previous) / |previous|) * 100`

**Returns:**
```python
{
    "growth_rate": 12.5,      # Percentage change
    "current": 150000.00,     # Current period value
    "previous": 133333.33     # Previous period value
}
```

---

### Moving Average
**Method:** `moving_average(df, date_col, value_col, window=3)`

Smooths time series data by averaging over a rolling window.

**Formula:** `AVG(values in window of N periods)`

**Returns:** DataFrame with original values and `moving_avg` column.

**Use cases:**
- Trend identification (removing noise)
- Seasonal adjustment
- Forecasting baseline

---

### Year-Over-Year Comparison
**Method:** `year_over_year(df, date_col, value_col)`

Compares annual totals and calculates the percentage change.

**Returns:**
```python
{
    2023: {"value": 1200000, "yoy_change": null},
    2024: {"value": 1350000, "yoy_change": 12.5},
    2025: {"value": 1500000, "yoy_change": 11.11}
}
```

---

## Comparison Metrics

### Top Performers
**Method:** `top_performers(df, group_col, value_col, n=5, ascending=False)`

Identifies the highest (or lowest) performing groups by a metric.

**Returns:**
```python
[
    {"name": "North", "value": 450000, "share_pct": 35.2},
    {"name": "East", "value": 320000, "share_pct": 25.0},
    ...
]
```

---

### Variance Analysis
**Method:** `variance_analysis(df, actual_col, budget_col, group_col)`

Compares actual performance against budget or target values.

**Returns:**
```python
{
    "actual": 1500000,
    "budget": 1400000,
    "variance": 100000,
    "variance_pct": 7.14,
    "favorable": true,
    "breakdown": [...]    # Per-group breakdown if group_col provided
}
```

**Interpretation:**
- Positive variance = actual exceeds budget (favorable for revenue)
- Negative variance = actual below budget (unfavorable for revenue)

---

### Percentile Ranking
**Method:** `percentile_ranking(df, column, group_col)`

Returns standard percentile values for a column.

---

## Formatting Options

The `format` field in KPI configuration controls how values are displayed:

| Format     | Example Input | Example Output | Description                     |
|------------|---------------|----------------|---------------------------------|
| `currency` | 2500000       | $2.5M          | Dollar sign, auto-scale K/M/B   |
| `currency` | 45000         | $45.0K         | Thousands with K suffix          |
| `currency` | 42.50         | $42.50         | Small amounts in full            |
| `percent`  | 35.7          | 35.7%          | Appends percent sign             |
| `decimal`  | 123.456       | 123.46         | Two decimal places with commas   |
| `integer`  | 1234          | 1,234          | No decimals, with commas         |
| `compact`  | 3200000000    | 3.2B           | Auto-scale without currency sign |
| `number`   | 1500000       | 1.5M           | Auto-scale (default)             |

### Auto-Scaling Thresholds

| Value Range      | Suffix | Example        |
|------------------|--------|----------------|
| >= 1,000,000,000 | B      | 3.2B           |
| >= 1,000,000     | M      | 1.5M           |
| >= 1,000         | K      | 45.0K          |
| < 1,000          | (none) | 42.50 or 42    |

---

## Period Comparison Logic

When `compare_periods` is enabled, the calculator:

1. Identifies the date column (auto-detected or specified).
2. Determines the total date range of the data.
3. Splits the data at the midpoint.
4. Calculates the KPI for the first half (previous period) and full dataset.
5. Computes percentage change: `((full - previous) / |previous|) * 100`.
6. Sets the trend direction:
   - **up** - positive change
   - **down** - negative change
   - **neutral** - zero or no comparison available

### Trend Colors in UI

| Trend   | Card Accent | Change Text |
|---------|-------------|-------------|
| up      | Green       | Green (+)   |
| down    | Red         | Red (-)     |
| neutral | Blue        | Gray        |

---

## Advanced KPI Methods

### Custom KPI Pipelines

For complex calculations not covered by built-in functions, you can extend
the `KPICalculator` class:

```python
from app.kpi_calculator import KPICalculator

class CustomKPICalculator(KPICalculator):
    def calculate_custom_metric(self, df, config):
        revenue = df["revenue"].sum()
        costs = df["costs"].sum()
        roi = ((revenue - costs) / costs) * 100
        return {
            "label": "ROI",
            "value": round(roi, 2),
            "formatted": f"{roi:.1f}%",
            "trend": "up" if roi > 0 else "down",
        }
```

### Combining Multiple Columns

The variance analysis method demonstrates how to compare two columns:

```python
result = calculator.variance_analysis(
    df,
    actual_col="revenue",
    budget_col="budget_revenue",
    group_col="department"
)
```

This returns both the overall variance and a per-group breakdown, making
it suitable for detailed financial reporting.
