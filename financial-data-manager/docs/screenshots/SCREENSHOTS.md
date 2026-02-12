# Screenshots

This directory is reserved for screenshots of the Financial Data Manager CLI output and HTML reports.

## Recommended Screenshots to Capture

### 1. Schema Initialisation

```bash
python -m src.cli init-db
```

Capture the table listing output showing all five tables created successfully.

### 2. Data Seeding

```bash
python -m src.cli seed
```

Capture the seed results table showing row counts for all entities (500 customers, 1000 accounts, 5000 transactions, 200 merchants, ~300 fraud flags).

### 3. Ad-Hoc Query Execution

```bash
python -m src.cli query "SELECT segment, COUNT(*) AS cnt, ROUND(AVG(a.balance), 2) AS avg_bal FROM customers c JOIN accounts a ON a.customer_id = c.customer_id GROUP BY segment ORDER BY cnt DESC"
```

Capture the rich-formatted table showing segment distribution with coloured headers.

### 4. Analytics Query File

```bash
python -m src.cli run-file queries/analytics.sql --limit 3
```

Capture the first three analytical queries executing with rule dividers, SQL preview, and formatted results.

### 5. Data Quality Check Results

```bash
python -m src.cli check-quality
```

Capture the full 10-check results table with PASS/FAIL indicators and the summary line.

### 6. HTML Data Quality Report

```bash
python -m src.cli report
```

Open `reports/dq_report.html` in a browser and capture:
- The summary cards (Total Checks, Passed, Failed, Pass Rate)
- The check summary table
- At least one detailed result panel

### 7. Test Suite Execution

```bash
pytest tests/ -v
```

Capture the full test output showing all passing tests across `test_schema.py` and `test_quality.py`.

## Naming Convention

Save screenshots with descriptive filenames:

```
01_init_db.png
02_seed_output.png
03_query_segment.png
04_analytics_queries.png
05_dq_check_results.png
06_html_report_overview.png
06_html_report_detail.png
07_test_suite.png
```

## Format

- PNG format preferred (lossless)
- Minimum width: 1200px
- Use a dark terminal theme for consistency with the HTML report styling
