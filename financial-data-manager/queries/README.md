# Analytical Query Library

This directory contains 20 pre-built SQL queries that cover the most common analytical use cases for financial transaction data. Each query is designed to run against the Financial Data Manager schema and returns actionable insights.

## Query Index

| # | Query | Business Context |
|---|-------|------------------|
| 1 | Top 20 Customers by Lifetime Volume | Identifies the highest-value customers by total completed transaction amount. Used by relationship managers to prioritise outreach and retention programmes. |
| 2 | Monthly Revenue Trend | Tracks revenue on a month-by-month basis for the most recent 24 months. Feeds executive dashboards and budget forecasting models. |
| 3 | Merchant Category Breakdown | Shows how transaction volume distributes across merchant categories (grocery, travel, etc.). Supports interchange-fee optimisation and partnership decisions. |
| 4 | High-Risk Fraud Flags | Surfaces fraud flags with a risk score at or above 0.80, joined with full transaction and merchant context. Consumed by the fraud operations desk for immediate triage. |
| 5 | Account Balance Distribution | Aggregates active account balances by account type, exposing the range (min / avg / max) and total deposits under management. |
| 6 | Customer Segment Revenue | Compares revenue contribution across customer segments (retail, premium, private, corporate). Validates segmentation strategy and product-market fit. |
| 7 | Channel Usage Analysis | Ranks transaction channels (online, POS, ATM, mobile, branch, wire) by volume and amount. Informs digital transformation investment priorities. |
| 8 | Velocity Analysis | Detects accounts with more than 10 transactions in a single calendar day -- a common indicator of automated or fraudulent activity. |
| 9 | Reconciliation -- Missing Posted Date | Lists completed transactions that have not yet received a posted date, indicating settlement delays that need investigation. |
| 10 | Top 10 Merchants by Revenue | Ranks merchants by revenue generated. Supports co-brand card programme evaluations and merchant incentive tiers. |
| 11 | Accounts Opened vs Closed by Quarter | Tracks the net account growth by quarter. Useful for churn analysis and customer acquisition funnel monitoring. |
| 12 | Running Total per Account | Uses a window function to compute a running cumulative sum of transaction amounts per account, ordered by date. Commonly used in statement generation. |
| 13 | Month-over-Month Growth Rate | A CTE-based query that computes percentage growth in purchase revenue between consecutive months. Powers trend analysis in BI tools. |
| 14 | Fraud Flag Resolution Summary | Breaks down fraud flags by type and resolution status, providing the fraud operations team with a workload dashboard. |
| 15 | Large Transaction Audit Trail | Extracts transactions above 5,000 USD with full customer, merchant, and fraud-status context. Feeds regulatory audit reports (e.g. SAR filings). |
| 16 | Dormant Account Detection | Identifies active accounts with no transactions in the last 180 days. Triggers outreach campaigns or regulatory dormancy procedures. |
| 17 | Daily Summary with 7-Day Moving Average | Computes daily transaction counts and amounts alongside a 7-day trailing moving average. Smooths volatility for operational dashboards. |
| 18 | Cross-Channel Comparison by Segment | Breaks down channel usage within each customer segment. Reveals whether premium customers favour mobile over branch, for instance. |
| 19 | Merchant Risk Scoring | Ranks merchants by fraud-flag rate (flags per transaction). Used by the merchant risk team to enforce compliance thresholds. |
| 20 | End-of-Day Reconciliation | Compares expected completed amounts to actually posted amounts per date, computing variance. Core to the daily settlement reconciliation workflow. |

## How to Run

Execute all queries at once:

```bash
python -m src.cli run-file queries/analytics.sql
```

Execute a subset (first 5 queries):

```bash
python -m src.cli run-file queries/analytics.sql --limit 5
```

Run an individual query interactively:

```bash
python -m src.cli query "SELECT segment, COUNT(*) FROM customers GROUP BY segment;"
```

## SQL Techniques Used

The queries in this library demonstrate several intermediate-to-advanced SQL patterns:

- **Window functions** -- `SUM() OVER`, `LAG() OVER`, `AVG() OVER` with `ROWS BETWEEN` frame specs (queries 12, 13, 17).
- **Common Table Expressions (CTEs)** -- `WITH ... AS` for readability and multi-step aggregation (queries 13, 17, 20).
- **Correlated subqueries** -- `EXISTS` used inside `CASE` for per-row classification (query 15).
- **Percentage-of-total calculations** -- Scalar subquery in the SELECT list to compute share metrics (queries 3, 7).
- **`HAVING` clause filtering** -- Post-aggregation filters for anomaly detection (queries 8, 16, 19).
- **`JULIANDAY` date arithmetic** -- SQLite-native date difference calculations (queries 9, 16).
- **`COALESCE` / `NULLIF`** -- Safe null handling to prevent division-by-zero and default substitutions (queries 19, 20).
- **Multi-table JOINs** -- Up to four-table joins to denormalise analytical result sets (queries 4, 15, 18).

## Notes

- All queries are tested against the seeded dataset (500 customers, 1,000 accounts, 5,000 transactions, 200 merchants).
- Results are formatted via the `rich` library when executed through the CLI.
- Queries intentionally avoid database-specific extensions beyond SQLite's built-in functions to keep the codebase portable.
