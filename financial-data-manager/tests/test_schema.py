"""
test_schema.py -- Tests for schema creation, constraints, and indexes.

Uses a temporary in-memory or temp-file database so that the production
database is never touched.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.schema import (
    create_schema,
    drop_all,
    get_connection,
    get_row_counts,
    get_table_names,
    table_exists,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path) -> Path:
    """Return a path to a temporary SQLite database file."""
    return tmp_path / "test.db"


@pytest.fixture()
def seeded_db(tmp_db) -> Path:
    """Create the schema and return the path."""
    create_schema(tmp_db)
    return tmp_db


# ---------------------------------------------------------------------------
# Schema creation tests
# ---------------------------------------------------------------------------


class TestSchemaCreation:
    """Verify that create_schema produces the expected tables and indexes."""

    def test_creates_all_tables(self, seeded_db):
        tables = get_table_names(seeded_db)
        expected = ["accounts", "customers", "fraud_flags", "merchants", "transactions"]
        assert tables == expected

    def test_table_exists_helper(self, seeded_db):
        assert table_exists("customers", seeded_db) is True
        assert table_exists("nonexistent_table", seeded_db) is False

    def test_idempotent_creation(self, seeded_db):
        """Running create_schema twice should not raise."""
        create_schema(seeded_db)
        tables = get_table_names(seeded_db)
        assert len(tables) == 5

    def test_empty_row_counts(self, seeded_db):
        counts = get_row_counts(seeded_db)
        assert all(v == 0 for v in counts.values())

    def test_foreign_keys_enabled(self, seeded_db):
        conn = get_connection(seeded_db)
        try:
            result = conn.execute("PRAGMA foreign_keys;").fetchone()
            assert result[0] == 1
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Constraint tests
# ---------------------------------------------------------------------------


class TestConstraints:
    """Verify CHECK, UNIQUE, and FK constraints."""

    def test_customer_segment_check(self, seeded_db):
        conn = get_connection(seeded_db)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                    "VALUES ('Test', 'User', 'test@example.com', '2024-01-01', 'invalid_segment');"
                )
        finally:
            conn.close()

    def test_customer_email_unique(self, seeded_db):
        conn = get_connection(seeded_db)
        try:
            conn.execute(
                "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                "VALUES ('A', 'B', 'dup@example.com', '2024-01-01', 'retail');"
            )
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                    "VALUES ('C', 'D', 'dup@example.com', '2024-01-01', 'premium');"
                )
        finally:
            conn.close()

    def test_account_type_check(self, seeded_db):
        conn = get_connection(seeded_db)
        try:
            # Insert a valid customer first
            conn.execute(
                "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                "VALUES ('FK', 'Test', 'fk@example.com', '2024-01-01', 'retail');"
            )
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO accounts (customer_id, account_number, account_type, opened_date) "
                    "VALUES (1, '123456789012', 'invalid_type', '2024-01-01');"
                )
        finally:
            conn.close()

    def test_transaction_status_check(self, seeded_db):
        conn = get_connection(seeded_db)
        try:
            # Set up parent rows
            conn.execute(
                "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                "VALUES ('X', 'Y', 'xy@example.com', '2024-01-01', 'retail');"
            )
            conn.execute(
                "INSERT INTO accounts (customer_id, account_number, account_type, opened_date) "
                "VALUES (1, '111111111111', 'checking', '2024-01-01');"
            )
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO transactions "
                    "(account_id, transaction_ref, transaction_type, amount, transaction_date, channel, status) "
                    "VALUES (1, 'REF-001', 'purchase', 100.0, '2024-06-01', 'online', 'bad_status');"
                )
        finally:
            conn.close()

    def test_fk_cascade_delete(self, seeded_db):
        """Deleting a customer cascades to their accounts."""
        conn = get_connection(seeded_db)
        try:
            conn.execute(
                "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                "VALUES ('Del', 'Test', 'del@example.com', '2024-01-01', 'retail');"
            )
            cid = conn.execute("SELECT last_insert_rowid();").fetchone()[0]
            conn.execute(
                f"INSERT INTO accounts (customer_id, account_number, account_type, opened_date) "
                f"VALUES ({cid}, '999999999999', 'savings', '2024-01-01');"
            )
            conn.commit()

            # Verify account exists
            count = conn.execute(
                f"SELECT COUNT(*) FROM accounts WHERE customer_id = {cid};"
            ).fetchone()[0]
            assert count == 1

            # Delete customer
            conn.execute(f"DELETE FROM customers WHERE customer_id = {cid};")
            conn.commit()

            # Account should be cascade-deleted
            count = conn.execute(
                f"SELECT COUNT(*) FROM accounts WHERE customer_id = {cid};"
            ).fetchone()[0]
            assert count == 0
        finally:
            conn.close()

    def test_fraud_flag_risk_score_check(self, seeded_db):
        """risk_score must be between 0.0 and 1.0."""
        conn = get_connection(seeded_db)
        try:
            # Build parent chain
            conn.execute(
                "INSERT INTO customers (first_name, last_name, email, customer_since, segment) "
                "VALUES ('RS', 'Test', 'rs@example.com', '2024-01-01', 'retail');"
            )
            conn.execute(
                "INSERT INTO accounts (customer_id, account_number, account_type, opened_date) "
                "VALUES (1, '222222222222', 'checking', '2024-01-01');"
            )
            conn.execute(
                "INSERT INTO transactions "
                "(account_id, transaction_ref, transaction_type, amount, transaction_date, channel) "
                "VALUES (1, 'REF-RS-01', 'purchase', 50.0, '2024-06-01', 'online');"
            )
            conn.commit()

            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO fraud_flags (transaction_id, flag_type, risk_score) "
                    "VALUES (1, 'velocity', 1.5);"
                )
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Drop / reset tests
# ---------------------------------------------------------------------------


class TestDropAll:
    """Verify that drop_all removes every table."""

    def test_drop_all_empties_schema(self, seeded_db):
        drop_all(seeded_db)
        tables = get_table_names(seeded_db)
        assert tables == []

    def test_recreate_after_drop(self, seeded_db):
        drop_all(seeded_db)
        create_schema(seeded_db)
        tables = get_table_names(seeded_db)
        assert len(tables) == 5


# ---------------------------------------------------------------------------
# Index tests
# ---------------------------------------------------------------------------


class TestIndexes:
    """Verify critical indexes exist."""

    def _get_index_names(self, db_path: Path) -> list[str]:
        conn = get_connection(db_path)
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name;"
            )
            return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

    def test_indexes_created(self, seeded_db):
        indexes = self._get_index_names(seeded_db)
        assert len(indexes) >= 15  # we define 17 indexes

    def test_key_indexes_present(self, seeded_db):
        indexes = self._get_index_names(seeded_db)
        expected_substrings = [
            "idx_accounts_customer",
            "idx_transactions_account",
            "idx_transactions_merchant",
            "idx_transactions_date",
            "idx_fraud_flags_txn",
            "idx_customers_segment",
        ]
        for substr in expected_substrings:
            assert any(substr in idx for idx in indexes), f"Missing index containing '{substr}'"
