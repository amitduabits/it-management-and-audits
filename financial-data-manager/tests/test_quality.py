"""
test_quality.py -- Unit tests for each of the 10 data quality checks.

Each test creates a minimal dataset in a temporary database and verifies
that the corresponding DQ check correctly identifies passes and failures.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.schema import create_schema, get_connection
from src.data_quality import (
    DQResult,
    check_amount_outliers,
    check_balance_consistency,
    check_date_ranges,
    check_duplicate_keys,
    check_email_format,
    check_null_critical_fields,
    check_optional_field_population,
    check_phone_format,
    check_referential_integrity,
    check_risk_score_range,
    run_all_checks,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db(tmp_path) -> Path:
    """Create a schema-only temporary database."""
    p = tmp_path / "dq_test.db"
    create_schema(p)
    return p


def _insert_customer(conn, email="good@example.com", phone="555-0100", **overrides):
    defaults = dict(
        first_name="Jane",
        last_name="Doe",
        email=email,
        phone=phone,
        address_line1="123 Main St",
        city="Springfield",
        state="IL",
        postal_code="62701",
        country="US",
        date_of_birth="1985-06-15",
        customer_since="2020-01-01",
        segment="retail",
        status="active",
    )
    defaults.update(overrides)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    conn.execute(f"INSERT INTO customers ({cols}) VALUES ({placeholders});", tuple(defaults.values()))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid();").fetchone()[0]


def _insert_merchant(conn, code="MCC-0001"):
    conn.execute(
        "INSERT INTO merchants (merchant_name, merchant_code, category, registration_date) "
        "VALUES ('Test Shop', ?, 'grocery', '2020-01-01');",
        (code,),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid();").fetchone()[0]


def _insert_account(conn, customer_id, account_number="100000000001", account_type="checking"):
    conn.execute(
        "INSERT INTO accounts (customer_id, account_number, account_type, opened_date) "
        "VALUES (?, ?, ?, '2021-01-01');",
        (customer_id, account_number, account_type),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid();").fetchone()[0]


def _insert_transaction(conn, account_id, ref="TXN-TEST-001", amount=100.0, merchant_id=None,
                         txn_date="2024-06-01 12:00:00", posted_date="2024-06-01 14:00:00",
                         status="completed"):
    conn.execute(
        "INSERT INTO transactions "
        "(account_id, merchant_id, transaction_ref, transaction_type, amount, "
        " transaction_date, posted_date, description, channel, status) "
        "VALUES (?, ?, ?, 'purchase', ?, ?, ?, 'Test txn', 'online', ?);",
        (account_id, merchant_id, ref, amount, txn_date, posted_date, status),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid();").fetchone()[0]


# ---------------------------------------------------------------------------
# DQ-01: Null Critical Fields
# ---------------------------------------------------------------------------


class TestNullCriticalFields:
    def test_passes_with_complete_data(self, db):
        conn = get_connection(db)
        _insert_customer(conn)
        _insert_merchant(conn)
        conn.close()

        result = check_null_critical_fields(db)
        assert result.passed is True
        assert result.affected_rows == 0

    def test_result_is_dq_result(self, db):
        result = check_null_critical_fields(db)
        assert isinstance(result, DQResult)
        assert result.check_id == "DQ-01"


# ---------------------------------------------------------------------------
# DQ-02: Optional Field Population
# ---------------------------------------------------------------------------


class TestOptionalFieldPopulation:
    def test_passes_when_populated(self, db):
        conn = get_connection(db)
        _insert_customer(conn, phone="555-1234", address_line1="123 Main", city="Town")
        conn.close()

        result = check_optional_field_population(db)
        assert result.passed is True

    def test_dimension_is_completeness(self, db):
        result = check_optional_field_population(db)
        assert result.dimension == "Completeness"


# ---------------------------------------------------------------------------
# DQ-03: Duplicate Keys
# ---------------------------------------------------------------------------


class TestDuplicateKeys:
    def test_no_duplicates(self, db):
        conn = get_connection(db)
        _insert_customer(conn, email="a@test.com")
        _insert_customer(conn, email="b@test.com")
        conn.close()

        result = check_duplicate_keys(db)
        assert result.passed is True

    def test_check_id(self, db):
        result = check_duplicate_keys(db)
        assert result.check_id == "DQ-03"


# ---------------------------------------------------------------------------
# DQ-04: Email Format
# ---------------------------------------------------------------------------


class TestEmailFormat:
    def test_valid_email_passes(self, db):
        conn = get_connection(db)
        _insert_customer(conn, email="jane.doe@example.com")
        conn.close()

        result = check_email_format(db)
        assert result.passed is True

    def test_invalid_email_fails(self, db):
        conn = get_connection(db)
        # Insert with a deliberately bad email via raw SQL to bypass any app-level validation
        conn.execute(
            "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
            "VALUES ('Bad', 'Email', 'not-an-email', '2024-01-01', 'retail');"
        )
        conn.commit()
        conn.close()

        result = check_email_format(db)
        assert result.passed is False
        assert result.affected_rows >= 1


# ---------------------------------------------------------------------------
# DQ-05: Phone Format
# ---------------------------------------------------------------------------


class TestPhoneFormat:
    def test_valid_phone_passes(self, db):
        conn = get_connection(db)
        _insert_customer(conn, phone="(555) 123-4567")
        conn.close()

        result = check_phone_format(db)
        assert result.passed is True

    def test_dimension_is_validity(self, db):
        result = check_phone_format(db)
        assert result.dimension == "Validity"


# ---------------------------------------------------------------------------
# DQ-06: Referential Integrity
# ---------------------------------------------------------------------------


class TestReferentialIntegrity:
    def test_valid_fk_passes(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        _insert_account(conn, cid)
        conn.close()

        result = check_referential_integrity(db)
        assert result.passed is True

    def test_check_id(self, db):
        result = check_referential_integrity(db)
        assert result.check_id == "DQ-06"


# ---------------------------------------------------------------------------
# DQ-07: Balance Consistency
# ---------------------------------------------------------------------------


class TestBalanceConsistency:
    def test_credit_with_positive_limit_passes(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        conn.execute(
            "INSERT INTO accounts (customer_id, account_number, account_type, credit_limit, opened_date) "
            "VALUES (?, '200000000001', 'credit', 5000.00, '2021-01-01');",
            (cid,),
        )
        conn.commit()
        conn.close()

        result = check_balance_consistency(db)
        assert result.passed is True

    def test_credit_with_null_limit_fails(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        conn.execute(
            "INSERT INTO accounts (customer_id, account_number, account_type, credit_limit, opened_date) "
            "VALUES (?, '300000000001', 'credit', NULL, '2021-01-01');",
            (cid,),
        )
        conn.commit()
        conn.close()

        result = check_balance_consistency(db)
        assert result.passed is False
        assert result.affected_rows >= 1


# ---------------------------------------------------------------------------
# DQ-08: Date Ranges
# ---------------------------------------------------------------------------


class TestDateRanges:
    def test_recent_date_passes(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        aid = _insert_account(conn, cid)
        _insert_transaction(conn, aid, txn_date="2024-06-01 10:00:00")
        conn.close()

        result = check_date_ranges(db)
        assert result.passed is True

    def test_ancient_date_fails(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        aid = _insert_account(conn, cid)
        _insert_transaction(conn, aid, ref="TXN-OLD-001", txn_date="2010-01-01 00:00:00")
        conn.close()

        result = check_date_ranges(db)
        assert result.passed is False
        assert result.affected_rows >= 1


# ---------------------------------------------------------------------------
# DQ-09: Amount Outliers
# ---------------------------------------------------------------------------


class TestAmountOutliers:
    def test_uniform_amounts_pass(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        aid = _insert_account(conn, cid)
        for i in range(20):
            _insert_transaction(conn, aid, ref=f"TXN-UNI-{i:03d}", amount=100.0 + i)
        conn.close()

        result = check_amount_outliers(db)
        assert result.passed is True

    def test_check_id_is_dq09(self, db):
        result = check_amount_outliers(db)
        assert result.check_id == "DQ-09"


# ---------------------------------------------------------------------------
# DQ-10: Risk Score Range
# ---------------------------------------------------------------------------


class TestRiskScoreRange:
    def test_valid_score_passes(self, db):
        conn = get_connection(db)
        cid = _insert_customer(conn)
        aid = _insert_account(conn, cid)
        tid = _insert_transaction(conn, aid)
        conn.execute(
            "INSERT INTO fraud_flags (transaction_id, flag_type, risk_score) "
            "VALUES (?, 'velocity', 0.75);",
            (tid,),
        )
        conn.commit()
        conn.close()

        result = check_risk_score_range(db)
        assert result.passed is True

    def test_dimension_is_accuracy(self, db):
        result = check_risk_score_range(db)
        assert result.dimension == "Accuracy"


# ---------------------------------------------------------------------------
# Integration: run_all_checks
# ---------------------------------------------------------------------------


class TestRunAllChecks:
    def test_returns_ten_results(self, db):
        results = run_all_checks(db)
        assert len(results) == 10

    def test_all_have_check_ids(self, db):
        results = run_all_checks(db)
        ids = [r.check_id for r in results]
        assert ids == [f"DQ-{i:02d}" for i in range(1, 11)]

    def test_pass_rate_property(self, db):
        results = run_all_checks(db)
        for r in results:
            assert 0.0 <= r.pass_rate <= 1.0
