# Data Quality Framework

This document defines the data quality (DQ) framework implemented by the Financial Data Manager. It covers the five DQ dimensions assessed, the 10 automated checks, scoring methodology, and operational guidelines.

---

## 1. DQ Dimensions

The framework evaluates data across five industry-standard dimensions, aligned with the DAMA-DMBOK body of knowledge.

| Dimension | Definition | Business Impact |
|-----------|-----------|-----------------|
| **Completeness** | The degree to which required data values are present and non-null. | Missing fields prevent downstream joins, break reports, and cause silent analytical errors. |
| **Uniqueness** | The degree to which records and key values are free of unwanted duplication. | Duplicate keys inflate counts, corrupt aggregations, and can cause insert failures in downstream systems. |
| **Validity** | The degree to which data values conform to defined formats, patterns, and domain rules. | Invalid emails prevent customer communication; malformed codes cause lookup failures in external systems. |
| **Consistency** | The degree to which related data values are logically coherent across tables and within records. | Orphaned foreign keys indicate data-load failures; inconsistent balances signal reconciliation issues. |
| **Timeliness** | The degree to which data values represent the appropriate time period and are available when needed. | Stale or future-dated transactions distort trend analysis and may indicate clock-skew or replay attacks. |
| **Accuracy** | The degree to which data values correctly represent the real-world entities they describe. | Outlier amounts may indicate data-entry errors, currency-conversion bugs, or fraudulent activity. |

---

## 2. Check Registry

### DQ-01: Critical Field Null Check

- **Dimension:** Completeness
- **Scope:** 10 fields across customers, accounts, transactions, merchants
- **Rule:** `COUNT(*) WHERE field IS NULL` must equal zero for every critical field.
- **Threshold:** 0 (zero tolerance)
- **Remediation:** Investigate upstream ETL or application-layer validation gaps.

### DQ-02: Optional Field Population Rate

- **Dimension:** Completeness
- **Scope:** 5 optional fields (phone, address, city, posted_date, description)
- **Rule:** Population rate (non-null / total) must be >= 70%.
- **Threshold:** 70%
- **Remediation:** Review data collection forms and API contracts for missing optional field handling.

### DQ-03: Duplicate Key Detection

- **Dimension:** Uniqueness
- **Scope:** Natural keys -- email, account_number, transaction_ref, merchant_code
- **Rule:** `GROUP BY key HAVING COUNT(*) > 1` must return zero rows.
- **Threshold:** 0 (zero tolerance)
- **Remediation:** Apply deduplication logic; investigate race conditions in concurrent inserts.

### DQ-04: Email Format Validation

- **Dimension:** Validity
- **Scope:** customers.email
- **Rule:** Must match regex `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`.
- **Threshold:** 0 invalid records
- **Remediation:** Enforce format validation at the application layer before insert.

### DQ-05: Phone Number Format Validation

- **Dimension:** Validity
- **Scope:** customers.phone (non-null rows only)
- **Rule:** Must match regex `^[\d\s\-\+\(\)\.x]+$` (digits, spaces, dashes, parens, plus, extensions).
- **Threshold:** 0 invalid records
- **Remediation:** Standardise phone input via a formatting library (e.g., `phonenumbers`).

### DQ-06: Referential Integrity Check

- **Dimension:** Consistency
- **Scope:** 4 FK relationships (accounts->customers, transactions->accounts, transactions->merchants, fraud_flags->transactions)
- **Rule:** `LEFT JOIN parent WHERE parent.pk IS NULL AND child.fk IS NOT NULL` must return 0.
- **Threshold:** 0 orphan rows
- **Remediation:** Verify load order in ETL pipelines; enable FK constraints at the database level.

### DQ-07: Account Balance Consistency

- **Dimension:** Consistency
- **Scope:** accounts where account_type = 'credit'
- **Rule:** Credit accounts must have a non-null, non-negative `credit_limit`.
- **Threshold:** 0 violations
- **Remediation:** Add application-layer validation requiring credit_limit on credit account creation.

### DQ-08: Transaction Date Range Validation

- **Dimension:** Timeliness
- **Scope:** transactions.transaction_date
- **Rule:** Date must fall within the last 3 years and must not be in the future.
- **Threshold:** 0 out-of-range records
- **Remediation:** Check system clocks, timezone conversions, and backfill scripts.

### DQ-09: Amount Outlier Detection

- **Dimension:** Accuracy
- **Scope:** transactions.amount
- **Rule:** No transaction amount should exceed 4 standard deviations from the mean.
- **Threshold:** 4 sigma
- **Remediation:** Flag for manual review; check for currency mismatch or decimal-point errors.

### DQ-10: Risk Score Range Enforcement

- **Dimension:** Accuracy
- **Scope:** fraud_flags.risk_score
- **Rule:** Value must be between 0.0 and 1.0 inclusive.
- **Threshold:** 0 out-of-range values
- **Remediation:** Validate score normalisation in the fraud scoring engine.

---

## 3. Scoring Methodology

### Per-Check Pass Rate

```
pass_rate = 1 - (affected_rows / total_rows)
```

A check is marked **PASS** when `affected_rows == 0` (or the measured value is within threshold).

### Overall Score

```
overall_pass_rate = passed_checks / total_checks * 100
```

### Severity Classification

| Pass Rate | Severity | Action |
|-----------|----------|--------|
| 100% | None | No action required |
| >= 95% | Low | Monitor; address in next sprint |
| >= 80% | Medium | Investigate root cause within 48 hours |
| < 80% | High | Escalate immediately; block downstream pipelines |

---

## 4. Execution Model

### On-Demand

```bash
python -m src.cli check-quality
```

Results are printed to the terminal in a formatted table with colour-coded PASS/FAIL indicators.

### Report Generation

```bash
python -m src.cli report
```

Produces both `reports/dq_report.md` and `reports/dq_report.html`. The HTML report includes a dark-themed dashboard with summary cards and detail panels.

### Integration with CI/CD

DQ checks can be executed as part of a CI pipeline. Example GitHub Actions step:

```yaml
- name: Run DQ checks
  run: |
    python -m src.cli init-db
    python -m src.cli seed
    python -m src.cli check-quality
```

To fail the pipeline on any DQ violation, wrap the CLI in a script that checks the exit code or parse the JSON output.

---

## 5. Extending the Framework

### Adding a New Check

1. Define a function in `src/data_quality.py` following the signature:
   ```python
   def check_my_new_rule(db_path: Optional[Path] = None) -> DQResult:
       ...
   ```

2. Return a `DQResult` with all required fields populated.

3. Append the function to the `ALL_CHECKS` list.

4. Add a corresponding test in `tests/test_quality.py`.

5. Document the check in this file under the Check Registry section.

### DQResult Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `check_id` | str | Yes | Unique identifier (e.g., DQ-11) |
| `dimension` | str | Yes | One of the five DQ dimensions |
| `name` | str | Yes | Human-readable check name |
| `description` | str | Yes | What the check validates |
| `passed` | bool | Yes | Whether the check passed |
| `details` | str | No | Explanation of the result |
| `affected_rows` | int | No | Number of rows that violated the rule |
| `total_rows` | int | No | Total rows evaluated |
| `threshold` | float | No | The threshold used for comparison |
| `measured_value` | float | No | The actual measured metric |
| `sql_used` | str | No | SQL statement(s) executed |
| `sample_violations` | list[dict] | No | Up to 10 example violations |

---

## 6. Operational Runbook

### Daily Operations

1. Run `check-quality` after each data load.
2. Review any FAIL results and classify severity.
3. Generate a report for the data governance team.

### Incident Response

1. Identify the failed check and its dimension.
2. Query the `sample_violations` for concrete examples.
3. Trace the data lineage back to the source system.
4. Apply a fix (data patch, ETL correction, or validation rule).
5. Re-run the affected check to confirm resolution.
6. Document the incident in the analyst notes or change log.

### Monthly Review

1. Aggregate pass rates over the month to identify trends.
2. Compare dimension-level scores against targets.
3. Propose new checks based on incidents observed.
4. Retire or adjust checks that consistently pass with no violations.
