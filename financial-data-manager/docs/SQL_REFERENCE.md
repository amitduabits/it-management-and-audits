# SQL Reference

A reference guide to the SQL techniques used throughout the Financial Data Manager analytical query library. All examples are drawn from `queries/analytics.sql` and are compatible with SQLite 3.35+.

---

## 1. Aggregate Functions

Standard aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`) form the backbone of most analytical queries.

### Pattern

```sql
SELECT
    category,
    COUNT(*)          AS record_count,
    SUM(amount)       AS total,
    ROUND(AVG(amount), 2) AS average,
    MIN(amount)       AS smallest,
    MAX(amount)       AS largest
FROM transactions
GROUP BY category;
```

### Usage in the Library

- **Query 1** -- `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` on transaction amounts per customer.
- **Query 5** -- balance distribution across account types.
- **Query 7** -- channel usage volume and percentage.

### Notes

- Always wrap monetary aggregates in `ROUND(..., 2)` to avoid floating-point display artefacts.
- Use `COUNT(DISTINCT col)` when counting unique entities within a group (e.g., unique accounts per month).

---

## 2. GROUP BY with HAVING

`HAVING` filters groups *after* aggregation, which is essential for anomaly detection.

### Pattern

```sql
SELECT
    account_id,
    DATE(transaction_date) AS day,
    COUNT(*)               AS daily_count
FROM transactions
GROUP BY account_id, DATE(transaction_date)
HAVING daily_count > 10;
```

### Usage in the Library

- **Query 8** -- velocity analysis: accounts exceeding 10 transactions per day.
- **Query 16** -- dormant account detection via `HAVING days_inactive > 180`.
- **Query 19** -- merchants with a non-zero fraud flag rate.

---

## 3. Multi-Table JOINs

Denormalisation for analytical output often requires joining three or four tables.

### Pattern

```sql
SELECT
    c.first_name || ' ' || c.last_name AS name,
    a.account_number,
    t.amount,
    m.merchant_name
FROM customers c
JOIN accounts a     ON a.customer_id  = c.customer_id
JOIN transactions t ON t.account_id   = a.account_id
LEFT JOIN merchants m ON m.merchant_id = t.merchant_id;
```

### Usage in the Library

- **Query 4** -- fraud flags joined to transactions, merchants, and customers.
- **Query 15** -- large-transaction audit trail with four-table join.
- **Query 18** -- cross-channel analysis joining customers, accounts, and transactions.

### Best Practices

- Use `LEFT JOIN` when the child side is nullable (e.g., `merchant_id` can be NULL).
- Alias every table for readability.
- Place the most restrictive `WHERE` clause filter first to help the query planner.

---

## 4. Window Functions

Window functions compute values across a set of rows related to the current row, without collapsing the result set.

### `SUM() OVER` -- Running Total

```sql
SELECT
    transaction_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY transaction_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM transactions;
```

### `LAG()` -- Previous Row Access

```sql
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_revenue
FROM monthly_revenue;
```

### `AVG() OVER` -- Moving Average

```sql
SELECT
    txn_date,
    daily_amount,
    AVG(daily_amount) OVER (
        ORDER BY txn_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM daily_summary;
```

### Usage in the Library

- **Query 12** -- running total per account using `SUM() OVER`.
- **Query 13** -- month-over-month growth using `LAG()`.
- **Query 17** -- 7-day moving average using `AVG() OVER`.

### Frame Specifications

| Frame | Meaning |
|-------|---------|
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | All rows from the start of the partition to the current row |
| `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` | The current row and the 6 preceding rows (7-row window) |
| `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING` | Three-row sliding window centred on the current row |

---

## 5. Common Table Expressions (CTEs)

CTEs (`WITH ... AS`) break complex queries into named, readable steps.

### Pattern

```sql
WITH monthly AS (
    SELECT strftime('%Y-%m', transaction_date) AS month, SUM(amount) AS revenue
    FROM transactions
    GROUP BY month
),
with_lag AS (
    SELECT month, revenue, LAG(revenue) OVER (ORDER BY month) AS prev
    FROM monthly
)
SELECT month, revenue, prev,
       ROUND((revenue - prev) / prev * 100, 2) AS growth_pct
FROM with_lag;
```

### Usage in the Library

- **Query 13** -- two-stage CTE for month-over-month growth.
- **Query 17** -- daily summary CTE feeding a window function.
- **Query 20** -- separate `expected` and `posted` CTEs for reconciliation.

### When to Use CTEs vs Subqueries

| Use CTEs when ... | Use subqueries when ... |
|-------------------|------------------------|
| The intermediate result is referenced more than once | The intermediate result is used exactly once |
| Readability benefits from named stages | The query is simple enough to inline |
| Debugging requires isolating a stage | Performance benchmarks show subquery is faster |

---

## 6. Correlated Subqueries

A subquery that references a column from the outer query, evaluated once per outer row.

### Pattern

```sql
SELECT
    t.transaction_id,
    t.amount,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM fraud_flags f WHERE f.transaction_id = t.transaction_id
        ) THEN 'FLAGGED'
        ELSE 'CLEAN'
    END AS fraud_status
FROM transactions t;
```

### Usage in the Library

- **Query 15** -- classifies each large transaction as FLAGGED or CLEAN.

### Performance Note

Correlated subqueries execute per outer row. For large datasets, consider rewriting as a `LEFT JOIN` with a `CASE` on NULL.

---

## 7. Scalar Subqueries (Percentage of Total)

A scalar subquery in the `SELECT` list returns a single value used for ratio calculations.

### Pattern

```sql
SELECT
    channel,
    COUNT(*) AS cnt,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) AS pct
FROM transactions
GROUP BY channel;
```

### Usage in the Library

- **Query 3** -- merchant category share of total volume.
- **Query 7** -- channel percentage of all transactions.

---

## 8. CASE Expressions

Conditional logic inside SQL for classification, pivoting, or conditional aggregation.

### Pattern

```sql
SELECT
    flag_type,
    SUM(CASE WHEN resolution = 'confirmed_fraud' THEN 1 ELSE 0 END) AS confirmed,
    SUM(CASE WHEN resolution = 'false_positive'  THEN 1 ELSE 0 END) AS false_pos
FROM fraud_flags
GROUP BY flag_type;
```

### Usage in the Library

- **Query 11** -- opened vs closed accounts per quarter.
- **Query 14** -- fraud resolution breakdown by type.
- **Query 15** -- FLAGGED / CLEAN classification.

---

## 9. Date Arithmetic in SQLite

SQLite lacks native DATE types. Dates are stored as TEXT in ISO 8601 format and manipulated with built-in functions.

### Key Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `strftime('%Y-%m', col)` | Extract year-month | `2024-06` |
| `DATE(col)` | Extract date portion | `2024-06-15` |
| `JULIANDAY(a) - JULIANDAY(b)` | Day difference as float | `45.5` |
| `datetime('now')` | Current UTC timestamp | `2024-06-15 14:30:00` |

### Usage in the Library

- **Query 2** -- monthly grouping via `strftime`.
- **Query 9** -- days-since-transaction via `JULIANDAY`.
- **Query 16** -- days-inactive calculation.
- **Query 17** -- daily grouping via `DATE()`.

---

## 10. NULL Handling

### Key Functions

| Function | Purpose |
|----------|---------|
| `COALESCE(a, b)` | Return `a` if non-NULL, else `b` |
| `NULLIF(a, b)` | Return NULL if `a = b` (prevents division by zero) |
| `IFNULL(a, b)` | SQLite alias for `COALESCE` with two arguments |

### Usage in the Library

- **Query 19** -- `NULLIF(COUNT(...), 0)` prevents divide-by-zero in flag rate calculation.
- **Query 20** -- `COALESCE(posted_count, 0)` handles dates with no posted transactions.

---

## SQLite Version Requirements

All queries in this library require **SQLite 3.25+** for window function support. The recommended minimum is **SQLite 3.35+** which ships with Python 3.10+.

Check your version:

```bash
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```
