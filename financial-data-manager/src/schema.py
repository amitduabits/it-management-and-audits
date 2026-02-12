"""
schema.py -- DDL definitions and database initialisation for Financial Data Manager.

Tables
------
- customers       Core customer profiles with segmentation.
- accounts        Financial accounts linked to customers.
- transactions    Individual monetary events against accounts and merchants.
- merchants       Payee / vendor registry.
- fraud_flags     Risk annotations attached to transactions.

All tables enforce foreign-key constraints and carry audit timestamps.
Indexes are created on every foreign-key column, natural keys, and
common filter predicates (status, date ranges).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from src import DB_PATH, ensure_dirs

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------

CUSTOMERS_DDL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT,
    address_line1   TEXT,
    city            TEXT,
    state           TEXT,
    postal_code     TEXT,
    country         TEXT NOT NULL DEFAULT 'US',
    date_of_birth   TEXT,
    customer_since  TEXT NOT NULL,
    segment         TEXT NOT NULL CHECK (segment IN ('retail', 'premium', 'private', 'corporate')),
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'closed')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

ACCOUNTS_DDL = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    account_number  TEXT NOT NULL UNIQUE,
    account_type    TEXT NOT NULL CHECK (account_type IN ('checking', 'savings', 'credit', 'investment', 'loan')),
    currency        TEXT NOT NULL DEFAULT 'USD',
    balance         REAL NOT NULL DEFAULT 0.0,
    credit_limit    REAL,
    opened_date     TEXT NOT NULL,
    closed_date     TEXT,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'dormant', 'closed', 'frozen')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE
);
"""

TRANSACTIONS_DDL = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id       INTEGER NOT NULL,
    merchant_id      INTEGER,
    transaction_ref  TEXT NOT NULL UNIQUE,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'refund', 'transfer', 'withdrawal', 'deposit', 'fee', 'interest')),
    amount           REAL NOT NULL,
    currency         TEXT NOT NULL DEFAULT 'USD',
    transaction_date TEXT NOT NULL,
    posted_date      TEXT,
    description      TEXT,
    channel          TEXT NOT NULL CHECK (channel IN ('online', 'pos', 'atm', 'mobile', 'branch', 'wire')),
    status           TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'pending', 'failed', 'reversed', 'disputed')),
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (account_id)  REFERENCES accounts  (account_id)  ON DELETE CASCADE,
    FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id) ON DELETE SET NULL
);
"""

MERCHANTS_DDL = """
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_name     TEXT NOT NULL,
    merchant_code     TEXT NOT NULL UNIQUE,
    category          TEXT NOT NULL CHECK (category IN (
        'grocery', 'restaurant', 'gas_station', 'online_retail',
        'travel', 'healthcare', 'utilities', 'entertainment',
        'education', 'financial_services'
    )),
    city              TEXT,
    state             TEXT,
    country           TEXT NOT NULL DEFAULT 'US',
    registration_date TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

FRAUD_FLAGS_DDL = """
CREATE TABLE IF NOT EXISTS fraud_flags (
    flag_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  INTEGER NOT NULL,
    flag_type       TEXT NOT NULL CHECK (flag_type IN (
        'velocity', 'amount_anomaly', 'geo_anomaly',
        'merchant_risk', 'account_takeover', 'card_not_present',
        'pattern_deviation', 'manual_review'
    )),
    risk_score      REAL NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    description     TEXT,
    resolution      TEXT CHECK (resolution IN ('confirmed_fraud', 'false_positive', 'under_review', NULL)),
    flagged_at      TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at     TEXT,
    analyst_notes   TEXT,
    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE
);
"""

# ---------------------------------------------------------------------------
# Index definitions
# ---------------------------------------------------------------------------

INDEXES_DDL = [
    "CREATE INDEX IF NOT EXISTS idx_accounts_customer       ON accounts       (customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_accounts_status          ON accounts       (status);",
    "CREATE INDEX IF NOT EXISTS idx_accounts_type            ON accounts       (account_type);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_account     ON transactions   (account_id);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_merchant    ON transactions   (merchant_id);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_date        ON transactions   (transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_status      ON transactions   (status);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_type        ON transactions   (transaction_type);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_channel     ON transactions   (channel);",
    "CREATE INDEX IF NOT EXISTS idx_merchants_category       ON merchants      (category);",
    "CREATE INDEX IF NOT EXISTS idx_merchants_status         ON merchants      (status);",
    "CREATE INDEX IF NOT EXISTS idx_fraud_flags_txn          ON fraud_flags    (transaction_id);",
    "CREATE INDEX IF NOT EXISTS idx_fraud_flags_type         ON fraud_flags    (flag_type);",
    "CREATE INDEX IF NOT EXISTS idx_fraud_flags_score        ON fraud_flags    (risk_score);",
    "CREATE INDEX IF NOT EXISTS idx_customers_segment        ON customers      (segment);",
    "CREATE INDEX IF NOT EXISTS idx_customers_status         ON customers      (status);",
    "CREATE INDEX IF NOT EXISTS idx_customers_email          ON customers      (email);",
]

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

ALL_DDL = [CUSTOMERS_DDL, MERCHANTS_DDL, ACCOUNTS_DDL, TRANSACTIONS_DDL, FRAUD_FLAGS_DDL]


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Return a connection with foreign-key enforcement enabled."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(db_path: Optional[Path] = None) -> None:
    """
    Execute all DDL statements and create indexes.

    Parameters
    ----------
    db_path : Path, optional
        Override for the default database path.
    """
    ensure_dirs()
    conn = get_connection(db_path)
    try:
        for ddl in ALL_DDL:
            conn.execute(ddl)
        for idx in INDEXES_DDL:
            conn.execute(idx)
        conn.commit()
    finally:
        conn.close()


def drop_all(db_path: Optional[Path] = None) -> None:
    """Drop every managed table (useful for testing)."""
    conn = get_connection(db_path)
    try:
        for table in ("fraud_flags", "transactions", "accounts", "merchants", "customers"):
            conn.execute(f"DROP TABLE IF EXISTS {table};")
        conn.commit()
    finally:
        conn.close()


def table_exists(table_name: str, db_path: Optional[Path] = None) -> bool:
    """Return True if *table_name* exists in the database."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        return cur.fetchone()[0] == 1
    finally:
        conn.close()


def get_table_names(db_path: Optional[Path] = None) -> list[str]:
    """Return a sorted list of user-defined table names."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_row_counts(db_path: Optional[Path] = None) -> dict[str, int]:
    """Return a mapping of table name to row count."""
    conn = get_connection(db_path)
    try:
        counts: dict[str, int] = {}
        for table in get_table_names(db_path):
            cur = conn.execute(f"SELECT COUNT(*) FROM {table};")
            counts[table] = cur.fetchone()[0]
        return counts
    finally:
        conn.close()
