# Data Format Specification

This document defines the required CSV column structures for each dataset type supported by the Financial Data Visualizer. Adhering to these specifications ensures that data loading, validation, statistical analysis, and chart generation work correctly.

---

## General Rules

1. **File encoding:** UTF-8 (with or without BOM).
2. **Delimiter:** Comma (`,`). No tab or semicolon support.
3. **Header row:** Required. Column names are case-insensitive and will be normalized to lowercase with underscores.
4. **Date format:** ISO 8601 (`YYYY-MM-DD`) is recommended. Other formats may work with the `date_format` parameter.
5. **Numeric values:** Use period (`.`) as the decimal separator. No thousands separators or currency symbols in numeric columns.
6. **Missing values:** Empty cells or `NaN` are accepted. Fully-empty rows are dropped during loading.

---

## 1. transactions.csv

Transaction-level financial records for personal or business expense tracking.

| Column | Type | Required | Description |
|---|---|---|---|
| `date` | string (YYYY-MM-DD) | Yes | Date the transaction occurred |
| `amount` | float | Yes | Transaction amount. Positive values = income/credit. Negative values = expense/debit |
| `category` | string | Yes | Expense or income category (e.g., "Groceries", "Salary", "Rent") |
| `merchant` | string | Yes | Vendor, employer, or source name |
| `type` | string | Yes | Either "credit" or "debit" |

### Example

```csv
date,amount,category,merchant,type
2025-01-15,-45.23,Groceries,Trader Joe's,debit
2025-01-15,4250.00,Salary,Employer Direct Deposit,credit
2025-01-16,-89.99,Shopping,Amazon,debit
```

### Notes

- The `amount` column should be negative for debits and positive for credits. This convention allows natural summing.
- `category` values should be consistent across the dataset (avoid "groceries" vs. "Groceries" vs. "GROCERIES").
- The `type` column is used for filtering. It should match the sign of `amount` (positive = credit, negative = debit).

### Recommended Categories

**Debit categories:** Groceries, Dining, Transportation, Utilities, Healthcare, Shopping, Entertainment, Insurance, Rent, Subscriptions

**Credit categories:** Salary, Freelance, Investment, Refund

---

## 2. market_data.csv

Daily OHLCV (Open-High-Low-Close-Volume) data for a single security or index. This is the standard format used by most financial data providers.

| Column | Type | Required | Description |
|---|---|---|---|
| `date` | string (YYYY-MM-DD) | Yes | Trading date |
| `open` | float | Yes | Opening price for the trading day |
| `high` | float | Yes | Highest price reached during the day |
| `low` | float | Yes | Lowest price reached during the day |
| `close` | float | Yes | Closing price for the trading day |
| `volume` | integer | Yes | Total number of shares/units traded |

### Example

```csv
date,open,high,low,close,volume
2025-01-02,150.00,152.34,149.12,151.28,4523100
2025-01-03,151.28,153.67,150.45,152.91,3891200
2025-01-06,152.91,154.18,151.73,153.42,5214300
```

### Validation Rules

- `high >= open` and `high >= close` (high must be the maximum)
- `low <= open` and `low <= close` (low must be the minimum)
- `volume >= 0`
- Dates should be business days only (no weekends or market holidays)
- Data should be sorted chronologically (ascending)

### Data Sources

Compatible with CSV exports from:
- Yahoo Finance
- Alpha Vantage
- IEX Cloud
- Polygon.io
- Quandl / Nasdaq Data Link

---

## 3. revenue_expenses.csv

Monthly profit-and-loss statement with revenue and itemized expense categories. Designed for 3-year (36-month) analysis but works with any number of months.

| Column | Type | Required | Description |
|---|---|---|---|
| `date` | string (YYYY-MM-DD) | Yes | First day of the month (e.g., "2023-01-01") |
| `revenue` | float | Yes | Total monthly revenue |
| `cogs` | float | Yes | Cost of goods sold |
| `operating_expenses` | float | Yes | General operating expenses |
| `marketing` | float | Yes | Marketing and advertising spend |
| `salaries` | float | Yes | Employee compensation and benefits |
| `rent` | float | Yes | Rent and facilities costs |
| `utilities` | float | Yes | Utility costs (electric, water, internet) |
| `net_income` | float | Yes | Bottom-line profit/loss for the month |

### Example

```csv
date,revenue,cogs,operating_expenses,marketing,salaries,rent,utilities,net_income
2023-01-01,798542.31,303046.08,143737.62,71868.81,179280.00,45225.00,14520.00,40864.80
2023-02-01,826318.45,314001.01,148737.32,82631.85,180610.00,44887.50,11418.00,44032.77
```

### Validation Rules

- `net_income` should approximately equal `revenue - (cogs + operating_expenses + marketing + salaries + rent + utilities)`
- All monetary values should be positive except `net_income` (which may be negative for loss months)
- Dates should be the first of each month
- Data should be sorted chronologically

### Adding Custom Columns

You can add additional expense columns (e.g., `r_and_d`, `depreciation`, `taxes`). They will automatically be included in:
- Correlation analysis
- Multi-line charts
- Dashboard visualizations

---

## Custom Datasets

The `DataLoader` class can load any CSV file. For custom datasets:

1. Include a `date` column for time-series analysis.
2. Include at least one numeric column for statistical calculations.
3. Use the `schema=None` parameter to skip automatic validation.
4. Specify `date_col` and `value_col` in the CLI commands.

```python
from src.data_loader import DataLoader

loader = DataLoader()
df = loader.load_csv("my_custom_data.csv", schema=None, date_col="timestamp")
```

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---|---|---|
| "Missing required columns" error | Column names do not match expected schema | Check spelling, case, and whitespace in CSV headers |
| Dates not parsing | Non-ISO date format | Pass `date_format="%m/%d/%Y"` (or your format) to DataLoader |
| "Cannot coerce column" warning | Non-numeric data in a numeric column | Remove currency symbols, commas, or text from numeric columns |
| Empty chart output | All values are NaN after loading | Check for encoding issues or mismatched delimiters |
