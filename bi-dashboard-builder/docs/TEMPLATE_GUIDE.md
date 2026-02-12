# Dashboard Template Guide

This guide explains how to create, customize, and manage dashboard templates
for the BI Dashboard Builder. Templates are JSON configuration files that
define the layout, KPI cards, chart types, and filter options for a dashboard.

---

## Table of Contents

1. [Template Structure](#template-structure)
2. [KPI Configuration](#kpi-configuration)
3. [Chart Configuration](#chart-configuration)
4. [Filter Configuration](#filter-configuration)
5. [Layout Options](#layout-options)
6. [Color Schemes](#color-schemes)
7. [Creating a Custom Template](#creating-a-custom-template)
8. [Template Examples](#template-examples)
9. [Best Practices](#best-practices)

---

## Template Structure

Every template is a JSON file stored in the `templates/` directory. The builder
automatically discovers and lists all `.json` files in that folder.

```json
{
    "title": "My Dashboard",
    "description": "A brief description of the dashboard purpose.",
    "version": "1.0.0",
    "refresh_interval": 300,
    "kpis": [ ... ],
    "charts": [ ... ],
    "filters": { ... },
    "layout": { ... }
}
```

### Top-Level Fields

| Field              | Type   | Required | Description                                     |
|--------------------|--------|----------|-------------------------------------------------|
| `title`            | string | Yes      | Dashboard heading displayed at the top           |
| `description`      | string | No       | Short description shown below the title          |
| `version`          | string | No       | Template version for tracking changes            |
| `refresh_interval` | int    | No       | Auto-refresh interval in seconds (0 = disabled)  |
| `kpis`             | array  | Yes      | List of KPI card configurations                  |
| `charts`           | array  | Yes      | List of chart configurations                     |
| `filters`          | object | No       | Filter bar configuration                         |
| `layout`           | object | No       | Grid layout settings                             |

---

## KPI Configuration

Each KPI is an object in the `kpis` array:

```json
{
    "label": "Total Revenue",
    "column": "amount",
    "function": "sum",
    "format": "currency",
    "compare_periods": true,
    "date_column": "date",
    "icon": "dollar-sign"
}
```

### KPI Fields

| Field             | Type    | Required | Description                                       |
|-------------------|---------|----------|---------------------------------------------------|
| `label`           | string  | Yes      | Display name for the KPI card                      |
| `column`          | string  | Yes*     | Data column to compute (*not needed for `count`)   |
| `function`        | string  | Yes      | Aggregation function (see list below)              |
| `format`          | string  | No       | Display format: `currency`, `percent`, `decimal`, `integer`, `compact` |
| `compare_periods` | boolean | No       | Enable period-over-period comparison (default: true) |
| `date_column`     | string  | No       | Override auto-detected date column                 |
| `icon`            | string  | No       | Icon name for the card                             |

### Available Functions

| Function       | Description                            |
|----------------|----------------------------------------|
| `sum`          | Sum of all values                      |
| `mean` / `avg` | Arithmetic mean                        |
| `median`       | 50th percentile                        |
| `count`        | Total row count                        |
| `unique_count` | Count of distinct values               |
| `min`          | Minimum value                          |
| `max`          | Maximum value                          |
| `std`          | Standard deviation                     |
| `var`          | Variance                               |
| `range`        | Max minus min                          |
| `p25`          | 25th percentile                        |
| `p75`          | 75th percentile                        |
| `p90`          | 90th percentile                        |
| `p95`          | 95th percentile                        |
| `p99`          | 99th percentile                        |
| `iqr`          | Interquartile range (p75 - p25)        |
| `cv`           | Coefficient of variation (%)           |

---

## Chart Configuration

Each chart is an object in the `charts` array. The required fields depend
on the chart type.

### Common Fields

| Field          | Type   | Required | Description                           |
|----------------|--------|----------|---------------------------------------|
| `type`         | string | Yes      | Chart type (see list below)           |
| `title`        | string | Yes      | Chart title                           |
| `height`       | int    | No       | Chart height in pixels (default: 400) |
| `color_scheme` | string | No       | Color palette name                    |

### Chart Types and Their Fields

#### Line Chart
```json
{
    "type": "line",
    "title": "Revenue Over Time",
    "x": "date",
    "y": "amount",
    "agg": "sum",
    "color": "category",
    "fill": true
}
```

#### Bar Chart
```json
{
    "type": "bar",
    "title": "Sales by Region",
    "x": "region",
    "y": "amount",
    "agg": "sum",
    "top_n": 10,
    "orientation": "v"
}
```

#### Pie / Donut Chart
```json
{
    "type": "pie",
    "title": "Category Distribution",
    "labels": "category",
    "values": "amount",
    "agg": "sum"
}
```

#### Scatter Plot
```json
{
    "type": "scatter",
    "title": "Amount vs Quantity",
    "x": "amount",
    "y": "quantity",
    "color": "category",
    "size": "quantity"
}
```

#### Stacked Bar
```json
{
    "type": "stacked_bar",
    "title": "Sales by Region and Category",
    "x": "region",
    "y": "amount",
    "stack_by": "category",
    "agg": "sum"
}
```

#### Heatmap
```json
{
    "type": "heatmap",
    "title": "Sales Heatmap",
    "x": "month",
    "y": "category",
    "values": "amount",
    "agg": "sum"
}
```

#### Other Types

- **`area`** - Area chart (line with fill)
- **`histogram`** - Distribution histogram (`x`, `bins`)
- **`box`** - Box plot (`x`, `y`)
- **`treemap`** - Treemap chart (`path`, `values`)
- **`waterfall`** - Waterfall chart (`x`, `y`)
- **`funnel`** - Funnel chart (`x`, `y`)

---

## Filter Configuration

Filters enable interactive dashboard refinement. They are defined in
the `filters` object:

```json
{
    "filters": {
        "region": {
            "type": "select",
            "label": "Region"
        },
        "date": {
            "type": "date_range",
            "label": "Date Range"
        }
    }
}
```

| Field   | Type   | Description                               |
|---------|--------|-------------------------------------------|
| `type`  | string | `select` for dropdowns, `date_range` for date pickers |
| `label` | string | Display label for the filter control      |

---

## Layout Options

```json
{
    "layout": {
        "kpi_columns": 4,
        "chart_columns": 2
    }
}
```

| Field           | Type | Default | Description                          |
|-----------------|------|---------|--------------------------------------|
| `kpi_columns`   | int  | auto    | Number of KPI cards per row          |
| `chart_columns` | int  | 2       | Number of chart columns              |

---

## Color Schemes

Available named color schemes:

| Name        | Description                                |
|-------------|--------------------------------------------|
| `blue`      | Professional blue gradient                 |
| `green`     | Nature-inspired greens                     |
| `purple`    | Rich purple tones                          |
| `red`       | Warm reds                                  |
| `orange`    | Vibrant oranges                            |
| `viridis`   | Scientific viridis palette                 |
| `corporate` | Business-focused blue-gray                 |
| `warm`      | Red-to-orange warm spectrum                |
| `cool`      | Blue-to-cyan cool spectrum                 |
| `default`   | Plotly's Set2 qualitative palette          |

---

## Creating a Custom Template

1. Create a new `.json` file in the `templates/` directory.
2. Define the required fields (`title`, `kpis`, `charts`).
3. Map column names to your expected data schema.
4. Restart the application or refresh the upload page.

### Step-by-Step Example

```json
{
    "title": "E-Commerce Analytics",
    "description": "Track online store performance metrics",
    "kpis": [
        {
            "label": "Gross Revenue",
            "column": "order_total",
            "function": "sum",
            "format": "currency"
        },
        {
            "label": "Orders",
            "column": "order_id",
            "function": "unique_count",
            "format": "integer"
        }
    ],
    "charts": [
        {
            "type": "line",
            "title": "Daily Revenue",
            "x": "order_date",
            "y": "order_total",
            "agg": "sum",
            "color_scheme": "corporate"
        },
        {
            "type": "pie",
            "title": "Revenue by Channel",
            "labels": "channel",
            "values": "order_total",
            "agg": "sum"
        }
    ]
}
```

---

## Best Practices

1. **Keep KPIs under 8.** More than 8 KPI cards reduce readability.
2. **Use meaningful labels.** Avoid technical column names in display labels.
3. **Match chart types to data.** Use line charts for time series, bar charts
   for categorical comparisons, and pie charts for proportional breakdowns.
4. **Limit pie chart slices to 10.** More slices make pie charts unreadable.
5. **Use `top_n` for bar charts.** Limit bars to the most significant categories.
6. **Set `compare_periods: true`** for KPIs where trend context is valuable.
7. **Version your templates.** Increment the version field when making changes.
8. **Test with sample data first.** Validate that column names in the template
   match your data before deploying to production.
