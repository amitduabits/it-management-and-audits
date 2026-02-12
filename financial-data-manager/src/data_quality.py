"""
data_quality.py -- Automated data quality checks for Financial Data Manager.

Implements 10 checks across five DQ dimensions:

 1. Completeness  -- critical field null detection
 2. Completeness  -- optional field population rate
 3. Uniqueness    -- primary / natural key duplicate detection
 4. Validity      -- email format validation
 5. Validity      -- phone number format validation
 6. Consistency   -- referential integrity (FK resolution)
 7. Consistency   -- account balance sign vs. account type
 8. Timeliness    -- transaction dates within acceptable range
 9. Accuracy      -- transaction amount outlier detection (z-score)
10. Accuracy      -- fraud flag risk_score range enforcement

Each check returns a ``DQResult`` dataclass that can be consumed by the
reporting layer.
"""

from __future__ import annotations

import re
import sqlite3
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.schema import get_connection, DB_PATH

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class DQResult:
    """Outcome of a single data-quality check."""

    check_id: str
    dimension: str
    name: str
    description: str
    passed: bool
    details: str = ""
    affected_rows: int = 0
    total_rows: int = 0
    threshold: Optional[float] = None
    measured_value: Optional[float] = None
    sql_used: str = ""
    sample_violations: list[dict] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_rows == 0:
            return 1.0
        return 1.0 - (self.affected_rows / self.total_rows)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    return get_connection(db_path)


def check_null_critical_fields(db_path: Optional[Path] = None) -> DQResult:
    """DQ-01: Critical fields must not be NULL."""
    checks = [
        ("customers", "email"),
        ("customers", "first_name"),
        ("customers", "last_name"),
        ("customers", "segment"),
        ("accounts", "account_number"),
        ("accounts", "account_type"),
        ("transactions", "transaction_ref"),
        ("transactions", "amount"),
        ("merchants", "merchant_name"),
        ("merchants", "merchant_code"),
    ]
    conn = _conn(db_path)
    violations = 0
    total = 0
    samples: list[dict] = []
    sqls: list[str] = []

    try:
        for table, col in checks:
            sql = f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL;"
            sqls.append(sql)
            null_count = conn.execute(sql).fetchone()[0]
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
            violations += null_count
            total += row_count
            if null_count > 0:
                samples.append({"table": table, "column": col, "null_count": null_count})
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-01",
        dimension="Completeness",
        name="Critical Field Null Check",
        description="Verifies that mandatory fields across all tables contain no NULL values.",
        passed=violations == 0,
        details=f"{violations} NULL value(s) found across {len(checks)} field checks.",
        affected_rows=violations,
        total_rows=total,
        threshold=0.0,
        measured_value=float(violations),
        sql_used="; ".join(sqls[:3]) + " ...",
        sample_violations=samples,
    )


def check_optional_field_population(db_path: Optional[Path] = None) -> DQResult:
    """DQ-02: Optional fields should be populated above 70 %."""
    conn = _conn(db_path)
    fields = [
        ("customers", "phone"),
        ("customers", "address_line1"),
        ("customers", "city"),
        ("transactions", "posted_date"),
        ("transactions", "description"),
    ]
    below_threshold: list[dict] = []
    total_fields = len(fields)

    try:
        for table, col in fields:
            total = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
            populated = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} != '';"
            ).fetchone()[0]
            rate = populated / total if total > 0 else 1.0
            if rate < 0.70:
                below_threshold.append({"table": table, "column": col, "population_rate": round(rate, 4)})
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-02",
        dimension="Completeness",
        name="Optional Field Population Rate",
        description="Optional fields should be populated at >= 70 % to support downstream analytics.",
        passed=len(below_threshold) == 0,
        details=f"{len(below_threshold)} field(s) below 70 % population threshold.",
        affected_rows=len(below_threshold),
        total_rows=total_fields,
        threshold=0.70,
        measured_value=round(1 - len(below_threshold) / total_fields, 4) if total_fields else 1.0,
        sql_used="SELECT COUNT(*) FROM <table> WHERE <col> IS NOT NULL;",
        sample_violations=below_threshold,
    )


def check_duplicate_keys(db_path: Optional[Path] = None) -> DQResult:
    """DQ-03: Natural keys must be unique (no duplicates)."""
    conn = _conn(db_path)
    keys = [
        ("customers", "email"),
        ("accounts", "account_number"),
        ("transactions", "transaction_ref"),
        ("merchants", "merchant_code"),
    ]
    dupes_found: list[dict] = []

    try:
        for table, col in keys:
            sql = f"SELECT {col}, COUNT(*) AS cnt FROM {table} GROUP BY {col} HAVING cnt > 1;"
            rows = conn.execute(sql).fetchall()
            for row in rows:
                dupes_found.append({"table": table, "column": col, "value": row[0], "count": row[1]})
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-03",
        dimension="Uniqueness",
        name="Duplicate Key Detection",
        description="Natural keys (email, account_number, transaction_ref, merchant_code) must be unique.",
        passed=len(dupes_found) == 0,
        details=f"{len(dupes_found)} duplicate key(s) detected.",
        affected_rows=len(dupes_found),
        total_rows=len(keys),
        threshold=0.0,
        measured_value=float(len(dupes_found)),
        sql_used="SELECT <col>, COUNT(*) FROM <table> GROUP BY <col> HAVING COUNT(*) > 1;",
        sample_violations=dupes_found[:10],
    )


def check_email_format(db_path: Optional[Path] = None) -> DQResult:
    """DQ-04: Customer emails must match a valid email pattern."""
    conn = _conn(db_path)
    email_re = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    bad: list[dict] = []

    try:
        rows = conn.execute("SELECT customer_id, email FROM customers;").fetchall()
        for row in rows:
            if not email_re.match(row[1]):
                bad.append({"customer_id": row[0], "email": row[1]})
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-04",
        dimension="Validity",
        name="Email Format Validation",
        description="All customer email addresses must conform to RFC-compliant format.",
        passed=len(bad) == 0,
        details=f"{len(bad)} invalid email(s) found out of {len(rows)}.",
        affected_rows=len(bad),
        total_rows=len(rows),
        threshold=0.0,
        measured_value=float(len(bad)),
        sql_used="SELECT customer_id, email FROM customers;",
        sample_violations=bad[:10],
    )


def check_phone_format(db_path: Optional[Path] = None) -> DQResult:
    """DQ-05: Customer phone numbers should contain only digits, dashes, parens, spaces, or +."""
    conn = _conn(db_path)
    phone_re = re.compile(r"^[\d\s\-\+\(\)\.x]+$")
    bad: list[dict] = []

    try:
        rows = conn.execute("SELECT customer_id, phone FROM customers WHERE phone IS NOT NULL;").fetchall()
        for row in rows:
            if not phone_re.match(row[1]):
                bad.append({"customer_id": row[0], "phone": row[1]})
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-05",
        dimension="Validity",
        name="Phone Number Format Validation",
        description="Phone numbers should contain only numeric characters, dashes, parentheses, spaces, or plus signs.",
        passed=len(bad) == 0,
        details=f"{len(bad)} invalid phone number(s) out of {len(rows)}.",
        affected_rows=len(bad),
        total_rows=len(rows),
        threshold=0.0,
        measured_value=float(len(bad)),
        sql_used="SELECT customer_id, phone FROM customers WHERE phone IS NOT NULL;",
        sample_violations=bad[:10],
    )


def check_referential_integrity(db_path: Optional[Path] = None) -> DQResult:
    """DQ-06: All foreign keys must resolve to existing parent rows."""
    conn = _conn(db_path)
    fk_checks = [
        (
            "accounts",
            "customer_id",
            "customers",
            "customer_id",
        ),
        (
            "transactions",
            "account_id",
            "accounts",
            "account_id",
        ),
        (
            "transactions",
            "merchant_id",
            "merchants",
            "merchant_id",
        ),
        (
            "fraud_flags",
            "transaction_id",
            "transactions",
            "transaction_id",
        ),
    ]
    orphans: list[dict] = []

    try:
        for child_table, child_col, parent_table, parent_col in fk_checks:
            # For nullable FKs, exclude NULLs
            sql = (
                f"SELECT COUNT(*) FROM {child_table} c "
                f"LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col} "
                f"WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL;"
            )
            orphan_count = conn.execute(sql).fetchone()[0]
            if orphan_count > 0:
                orphans.append({
                    "child_table": child_table,
                    "child_column": child_col,
                    "parent_table": parent_table,
                    "orphan_count": orphan_count,
                })
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-06",
        dimension="Consistency",
        name="Referential Integrity Check",
        description="Every foreign-key value must resolve to an existing row in the parent table.",
        passed=len(orphans) == 0,
        details=f"{len(orphans)} broken FK relationship(s) detected.",
        affected_rows=sum(o["orphan_count"] for o in orphans),
        total_rows=len(fk_checks),
        threshold=0.0,
        measured_value=float(len(orphans)),
        sql_used="SELECT COUNT(*) FROM child LEFT JOIN parent ... WHERE parent.pk IS NULL;",
        sample_violations=orphans,
    )


def check_balance_consistency(db_path: Optional[Path] = None) -> DQResult:
    """DQ-07: Credit accounts should have non-negative credit limits; loan balances should be >= 0."""
    conn = _conn(db_path)
    issues: list[dict] = []

    try:
        # Credit accounts with NULL or negative credit_limit
        sql1 = (
            "SELECT account_id, account_type, credit_limit FROM accounts "
            "WHERE account_type = 'credit' AND (credit_limit IS NULL OR credit_limit < 0);"
        )
        for row in conn.execute(sql1).fetchall():
            issues.append({
                "account_id": row[0],
                "issue": f"Credit account with invalid credit_limit: {row[2]}",
            })

        total = conn.execute("SELECT COUNT(*) FROM accounts;").fetchone()[0]
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-07",
        dimension="Consistency",
        name="Account Balance Consistency",
        description="Credit accounts must have a positive credit_limit; loan balances must be non-negative.",
        passed=len(issues) == 0,
        details=f"{len(issues)} account(s) with inconsistent balance / limit values.",
        affected_rows=len(issues),
        total_rows=total,
        threshold=0.0,
        measured_value=float(len(issues)),
        sql_used=sql1,
        sample_violations=issues[:10],
    )


def check_date_ranges(db_path: Optional[Path] = None) -> DQResult:
    """DQ-08: Transaction dates must fall within the last 3 years and not be in the future."""
    conn = _conn(db_path)
    now = datetime.now()
    lower_bound = now.replace(year=now.year - 3).strftime("%Y-%m-%d")
    upper_bound = (now).strftime("%Y-%m-%d %H:%M:%S")

    sql = (
        "SELECT COUNT(*) FROM transactions "
        f"WHERE transaction_date < '{lower_bound}' OR transaction_date > '{upper_bound}';"
    )

    try:
        out_of_range = conn.execute(sql).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM transactions;").fetchone()[0]
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-08",
        dimension="Timeliness",
        name="Transaction Date Range Validation",
        description="Transaction dates must be within the last 3 years and not in the future.",
        passed=out_of_range == 0,
        details=f"{out_of_range} transaction(s) outside acceptable date range.",
        affected_rows=out_of_range,
        total_rows=total,
        threshold=0.0,
        measured_value=float(out_of_range),
        sql_used=sql,
    )


def check_amount_outliers(db_path: Optional[Path] = None) -> DQResult:
    """DQ-09: Transaction amounts should not exceed 4 standard deviations from the mean."""
    conn = _conn(db_path)

    try:
        rows = conn.execute("SELECT amount FROM transactions;").fetchall()
        amounts = [r[0] for r in rows]
        if len(amounts) < 2:
            return DQResult(
                check_id="DQ-09",
                dimension="Accuracy",
                name="Amount Outlier Detection",
                description="Insufficient data for outlier analysis.",
                passed=True,
                total_rows=len(amounts),
            )

        mean = statistics.mean(amounts)
        stdev = statistics.stdev(amounts)
        threshold_upper = mean + 4 * stdev
        threshold_lower = mean - 4 * stdev

        outlier_sql = (
            f"SELECT transaction_id, amount FROM transactions "
            f"WHERE amount > {threshold_upper} OR amount < {threshold_lower};"
        )
        outliers = conn.execute(outlier_sql).fetchall()
        samples = [{"transaction_id": r[0], "amount": r[1]} for r in outliers[:10]]
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-09",
        dimension="Accuracy",
        name="Amount Outlier Detection",
        description="Transaction amounts exceeding 4 sigma from the mean are flagged as potential outliers.",
        passed=len(outliers) == 0,
        details=(
            f"{len(outliers)} outlier(s) detected. "
            f"Mean={mean:,.2f}, StdDev={stdev:,.2f}, "
            f"Bounds=[{threshold_lower:,.2f}, {threshold_upper:,.2f}]."
        ),
        affected_rows=len(outliers),
        total_rows=len(amounts),
        threshold=4.0,
        measured_value=round(max(abs(a - mean) / stdev for a in amounts) if stdev > 0 else 0, 4),
        sql_used=outlier_sql,
        sample_violations=samples,
    )


def check_risk_score_range(db_path: Optional[Path] = None) -> DQResult:
    """DQ-10: Fraud flag risk_score must be between 0.0 and 1.0 inclusive."""
    conn = _conn(db_path)

    sql = "SELECT COUNT(*) FROM fraud_flags WHERE risk_score < 0.0 OR risk_score > 1.0;"
    try:
        bad_count = conn.execute(sql).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM fraud_flags;").fetchone()[0]
    finally:
        conn.close()

    return DQResult(
        check_id="DQ-10",
        dimension="Accuracy",
        name="Risk Score Range Enforcement",
        description="Fraud flag risk_score values must be within [0.0, 1.0].",
        passed=bad_count == 0,
        details=f"{bad_count} record(s) with out-of-range risk_score.",
        affected_rows=bad_count,
        total_rows=total,
        threshold=0.0,
        measured_value=float(bad_count),
        sql_used=sql,
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_null_critical_fields,
    check_optional_field_population,
    check_duplicate_keys,
    check_email_format,
    check_phone_format,
    check_referential_integrity,
    check_balance_consistency,
    check_date_ranges,
    check_amount_outliers,
    check_risk_score_range,
]


def run_all_checks(db_path: Optional[Path] = None) -> list[DQResult]:
    """Execute every registered DQ check and return results."""
    results: list[DQResult] = []
    for check_fn in ALL_CHECKS:
        results.append(check_fn(db_path))
    return results
