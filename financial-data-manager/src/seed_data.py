"""
seed_data.py -- Synthetic data generation for the Financial Data Manager.

Uses Faker to produce realistic-looking financial records:
    - 500  customers
    - 1000 accounts  (1-4 per customer)
    - 200  merchants
    - 5000 transactions
    - ~300 fraud flags (based on heuristic triggers)

The generator is deterministic when given a fixed seed, making test runs
reproducible.
"""

from __future__ import annotations

import hashlib
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from faker import Faker

from src import SEED_LOCALE
from src.schema import get_connection, create_schema, DB_PATH

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

NUM_CUSTOMERS = 500
NUM_ACCOUNTS = 1000
NUM_MERCHANTS = 200
NUM_TRANSACTIONS = 5000
RANDOM_SEED = 20240601

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

fake = Faker(SEED_LOCALE)
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _date_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _generate_account_number() -> str:
    """Generate a realistic 12-digit account number."""
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def _generate_merchant_code() -> str:
    """Generate a merchant category code like MCC-XXXX."""
    return f"MCC-{random.randint(1000, 9999)}"


def _generate_txn_ref() -> str:
    """Generate a unique transaction reference."""
    return f"TXN-{uuid.uuid4().hex[:16].upper()}"


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

SEGMENTS = ["retail", "premium", "private", "corporate"]
SEGMENT_WEIGHTS = [0.55, 0.25, 0.10, 0.10]

ACCOUNT_TYPES = ["checking", "savings", "credit", "investment", "loan"]
CURRENCIES = ["USD", "USD", "USD", "EUR", "GBP"]  # weighted toward USD

MERCHANT_CATEGORIES = [
    "grocery", "restaurant", "gas_station", "online_retail",
    "travel", "healthcare", "utilities", "entertainment",
    "education", "financial_services",
]

TXN_TYPES = ["purchase", "refund", "transfer", "withdrawal", "deposit", "fee", "interest"]
TXN_TYPE_WEIGHTS = [0.45, 0.05, 0.15, 0.10, 0.15, 0.05, 0.05]

CHANNELS = ["online", "pos", "atm", "mobile", "branch", "wire"]
CHANNEL_WEIGHTS = [0.30, 0.25, 0.10, 0.20, 0.10, 0.05]

TXN_STATUSES = ["completed", "pending", "failed", "reversed", "disputed"]
TXN_STATUS_WEIGHTS = [0.82, 0.08, 0.03, 0.04, 0.03]

FLAG_TYPES = [
    "velocity", "amount_anomaly", "geo_anomaly",
    "merchant_risk", "account_takeover", "card_not_present",
    "pattern_deviation", "manual_review",
]


def generate_customers(conn) -> list[int]:
    """Insert *NUM_CUSTOMERS* customer rows, returning their IDs."""
    customer_ids: list[int] = []
    used_emails: set[str] = set()

    for _ in range(NUM_CUSTOMERS):
        first = fake.first_name()
        last = fake.last_name()

        # Ensure email uniqueness
        base_email = f"{first.lower()}.{last.lower()}@{fake.free_email_domain()}"
        email = base_email
        counter = 1
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{counter}@{fake.free_email_domain()}"
            counter += 1
        used_emails.add(email)

        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
        customer_since = fake.date_between(start_date="-10y", end_date="-30d")
        dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
        status = random.choices(
            ["active", "inactive", "suspended", "closed"],
            weights=[0.80, 0.10, 0.05, 0.05],
            k=1,
        )[0]

        cur = conn.execute(
            """
            INSERT INTO customers
                (first_name, last_name, email, phone, address_line1,
                 city, state, postal_code, country, date_of_birth,
                 customer_since, segment, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                first, last, email, fake.phone_number(),
                fake.street_address(), fake.city(), fake.state_abbr(),
                fake.zipcode(), "US", _date_iso(dob),
                _date_iso(customer_since), segment, status,
            ),
        )
        customer_ids.append(cur.lastrowid)

    conn.commit()
    return customer_ids


def generate_merchants(conn) -> list[int]:
    """Insert *NUM_MERCHANTS* merchant rows, returning their IDs."""
    merchant_ids: list[int] = []
    used_codes: set[str] = set()

    for _ in range(NUM_MERCHANTS):
        code = _generate_merchant_code()
        while code in used_codes:
            code = _generate_merchant_code()
        used_codes.add(code)

        category = random.choice(MERCHANT_CATEGORIES)
        reg_date = fake.date_between(start_date="-8y", end_date="-60d")
        status = random.choices(["active", "inactive", "suspended"], weights=[0.85, 0.10, 0.05], k=1)[0]

        cur = conn.execute(
            """
            INSERT INTO merchants
                (merchant_name, merchant_code, category, city, state, country,
                 registration_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fake.company(), code, category, fake.city(),
                fake.state_abbr(), "US", _date_iso(reg_date), status,
            ),
        )
        merchant_ids.append(cur.lastrowid)

    conn.commit()
    return merchant_ids


def generate_accounts(conn, customer_ids: list[int]) -> list[int]:
    """Insert *NUM_ACCOUNTS* accounts spread across existing customers."""
    account_ids: list[int] = []
    used_numbers: set[str] = set()

    # Guarantee every customer gets at least one account
    assigned = list(customer_ids)
    random.shuffle(assigned)

    # Fill remaining slots with random repeats
    while len(assigned) < NUM_ACCOUNTS:
        assigned.append(random.choice(customer_ids))
    assigned = assigned[:NUM_ACCOUNTS]
    random.shuffle(assigned)

    for cid in assigned:
        acct_num = _generate_account_number()
        while acct_num in used_numbers:
            acct_num = _generate_account_number()
        used_numbers.add(acct_num)

        acct_type = random.choice(ACCOUNT_TYPES)
        currency = random.choice(CURRENCIES)
        balance = round(random.uniform(-5000, 250000), 2)
        credit_limit = round(random.uniform(1000, 50000), 2) if acct_type == "credit" else None
        opened = fake.date_between(start_date="-8y", end_date="-30d")
        status = random.choices(["active", "dormant", "closed", "frozen"], weights=[0.78, 0.10, 0.08, 0.04], k=1)[0]
        closed_date = _date_iso(fake.date_between(start_date=opened, end_date="today")) if status == "closed" else None

        cur = conn.execute(
            """
            INSERT INTO accounts
                (customer_id, account_number, account_type, currency, balance,
                 credit_limit, opened_date, closed_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid, acct_num, acct_type, currency, balance,
                credit_limit, _date_iso(opened), closed_date, status,
            ),
        )
        account_ids.append(cur.lastrowid)

    conn.commit()
    return account_ids


def generate_transactions(conn, account_ids: list[int], merchant_ids: list[int]) -> list[int]:
    """Insert *NUM_TRANSACTIONS* transactions across accounts and merchants."""
    txn_ids: list[int] = []
    used_refs: set[str] = set()

    for _ in range(NUM_TRANSACTIONS):
        ref = _generate_txn_ref()
        while ref in used_refs:
            ref = _generate_txn_ref()
        used_refs.add(ref)

        aid = random.choice(account_ids)
        mid = random.choice(merchant_ids) if random.random() > 0.05 else None  # 5 % have no merchant
        txn_type = random.choices(TXN_TYPES, weights=TXN_TYPE_WEIGHTS, k=1)[0]
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
        status = random.choices(TXN_STATUSES, weights=TXN_STATUS_WEIGHTS, k=1)[0]

        # Realistic amount distribution -- most are small, some are large
        if random.random() < 0.92:
            amount = round(random.uniform(1.50, 500.00), 2)
        else:
            amount = round(random.uniform(500.00, 15000.00), 2)

        txn_date = fake.date_time_between(start_date="-2y", end_date="now")
        posted_date = txn_date + timedelta(hours=random.randint(0, 72)) if status == "completed" else None

        description_templates = [
            f"Payment to {fake.company()}",
            f"Purchase at {fake.company()}",
            f"Transfer ref {fake.bothify('??###')}",
            f"ATM withdrawal {fake.city()}",
            f"Direct deposit from {fake.company()}",
            f"Service fee",
            f"Interest accrual",
            f"Refund from {fake.company()}",
        ]
        description = random.choice(description_templates)

        cur = conn.execute(
            """
            INSERT INTO transactions
                (account_id, merchant_id, transaction_ref, transaction_type,
                 amount, currency, transaction_date, posted_date,
                 description, channel, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                aid, mid, ref, txn_type,
                amount, "USD", _iso(txn_date),
                _iso(posted_date) if posted_date else None,
                description, channel, status,
            ),
        )
        txn_ids.append(cur.lastrowid)

    conn.commit()
    return txn_ids


def generate_fraud_flags(conn, txn_ids: list[int]) -> int:
    """
    Generate fraud flags for a subset of transactions.

    Selection criteria (heuristic):
      - ~6 % of all transactions receive at least one flag.
      - High-amount transactions are more likely to be flagged.
    """
    flagged_count = 0
    candidates = random.sample(txn_ids, k=min(int(len(txn_ids) * 0.06), len(txn_ids)))

    for tid in candidates:
        flag_type = random.choice(FLAG_TYPES)
        risk_score = round(random.uniform(0.30, 1.00), 4)
        resolution = random.choices(
            ["confirmed_fraud", "false_positive", "under_review", None],
            weights=[0.15, 0.40, 0.30, 0.15],
            k=1,
        )[0]

        flagged_at = fake.date_time_between(start_date="-2y", end_date="now")
        resolved_at = (
            _iso(flagged_at + timedelta(days=random.randint(1, 30)))
            if resolution in ("confirmed_fraud", "false_positive")
            else None
        )

        descriptions = [
            "Unusual transaction velocity detected within 1-hour window",
            "Amount exceeds 3-sigma threshold for this account profile",
            "Transaction originated from geographic region inconsistent with account history",
            "Merchant flagged in industry risk database",
            "Multiple failed authentication attempts preceding transaction",
            "Card-not-present transaction above risk threshold",
            "Spending pattern deviates significantly from 90-day baseline",
            "Flagged for manual review by rule engine",
        ]

        analyst_notes_pool = [
            "Contacted customer -- confirmed legitimate purchase.",
            "Cross-referenced with known fraud ring identifiers.",
            "Escalated to senior analyst for further investigation.",
            "Customer dispute filed; chargeback initiated.",
            "Reviewed transaction chain; no anomalies beyond initial trigger.",
            None,
        ]

        conn.execute(
            """
            INSERT INTO fraud_flags
                (transaction_id, flag_type, risk_score, description,
                 resolution, flagged_at, resolved_at, analyst_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tid, flag_type, risk_score,
                random.choice(descriptions),
                resolution, _iso(flagged_at), resolved_at,
                random.choice(analyst_notes_pool),
            ),
        )
        flagged_count += 1

    conn.commit()
    return flagged_count


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def seed_all(db_path: Optional[Path] = None, verbose: bool = True) -> dict[str, int]:
    """
    Run the full seed pipeline.

    Returns a dict with counts per entity.
    """
    path = db_path or DB_PATH
    create_schema(path)
    conn = get_connection(path)

    try:
        if verbose:
            print("[seed] Generating customers ...")
        cust_ids = generate_customers(conn)

        if verbose:
            print("[seed] Generating merchants ...")
        merch_ids = generate_merchants(conn)

        if verbose:
            print("[seed] Generating accounts ...")
        acct_ids = generate_accounts(conn, cust_ids)

        if verbose:
            print("[seed] Generating transactions ...")
        txn_ids = generate_transactions(conn, acct_ids, merch_ids)

        if verbose:
            print("[seed] Generating fraud flags ...")
        flag_count = generate_fraud_flags(conn, txn_ids)

        counts = {
            "customers": len(cust_ids),
            "merchants": len(merch_ids),
            "accounts": len(acct_ids),
            "transactions": len(txn_ids),
            "fraud_flags": flag_count,
        }

        if verbose:
            print(f"[seed] Done -- {counts}")

        return counts
    finally:
        conn.close()
