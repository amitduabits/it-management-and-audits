# Schema Guide

Complete reference for the Financial Data Manager relational schema. The database is implemented in SQLite with full foreign-key enforcement, CHECK constraints, and performance indexes.

## Design Principles

1. **Third Normal Form (3NF)** -- every non-key column depends on the key, the whole key, and nothing but the key.
2. **Referential integrity** -- all relationships are enforced via `FOREIGN KEY` clauses with explicit `ON DELETE` actions.
3. **Audit columns** -- every table carries `created_at` and (where applicable) `updated_at` timestamps defaulting to `datetime('now')`.
4. **Domain constraints** -- status fields and enumerated types use `CHECK` constraints to reject invalid values at the database layer.
5. **Indexing strategy** -- indexes exist on all FK columns, natural keys, and common filter predicates (status, date, segment).

---

## Table: `customers`

The root entity representing an individual or corporate client.

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| `customer_id` | INTEGER | No | AUTOINCREMENT | PRIMARY KEY | Surrogate key |
| `first_name` | TEXT | No | -- | NOT NULL | Legal first name |
| `last_name` | TEXT | No | -- | NOT NULL | Legal last name |
| `email` | TEXT | No | -- | NOT NULL, UNIQUE | Primary contact email |
| `phone` | TEXT | Yes | NULL | -- | Phone number (free-format) |
| `address_line1` | TEXT | Yes | NULL | -- | Street address |
| `city` | TEXT | Yes | NULL | -- | City |
| `state` | TEXT | Yes | NULL | -- | State / province abbreviation |
| `postal_code` | TEXT | Yes | NULL | -- | ZIP / postal code |
| `country` | TEXT | No | `'US'` | NOT NULL | ISO 3166-1 alpha-2 country code |
| `date_of_birth` | TEXT | Yes | NULL | -- | ISO 8601 date (YYYY-MM-DD) |
| `customer_since` | TEXT | No | -- | NOT NULL | Date the customer relationship began |
| `segment` | TEXT | No | -- | CHECK IN (retail, premium, private, corporate) | Business segmentation tier |
| `status` | TEXT | No | `'active'` | CHECK IN (active, inactive, suspended, closed) | Account lifecycle status |
| `created_at` | TEXT | No | `datetime('now')` | NOT NULL | Row creation timestamp |
| `updated_at` | TEXT | No | `datetime('now')` | NOT NULL | Last modification timestamp |

### Indexes on `customers`

- `idx_customers_email` -- accelerates login and duplicate-detection lookups.
- `idx_customers_segment` -- used by segmentation analytics.
- `idx_customers_status` -- filters for active-customer queries.

---

## Table: `accounts`

A financial account owned by a customer. One customer may own multiple accounts of different types.

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| `account_id` | INTEGER | No | AUTOINCREMENT | PRIMARY KEY | Surrogate key |
| `customer_id` | INTEGER | No | -- | FK -> customers.customer_id ON DELETE CASCADE | Owning customer |
| `account_number` | TEXT | No | -- | NOT NULL, UNIQUE | 12-digit human-readable account identifier |
| `account_type` | TEXT | No | -- | CHECK IN (checking, savings, credit, investment, loan) | Product type |
| `currency` | TEXT | No | `'USD'` | NOT NULL | ISO 4217 currency code |
| `balance` | REAL | No | `0.0` | NOT NULL | Current ledger balance |
| `credit_limit` | REAL | Yes | NULL | -- | Applicable to credit accounts only |
| `opened_date` | TEXT | No | -- | NOT NULL | Date the account was opened |
| `closed_date` | TEXT | Yes | NULL | -- | Date the account was closed (NULL if open) |
| `status` | TEXT | No | `'active'` | CHECK IN (active, dormant, closed, frozen) | Current status |
| `created_at` | TEXT | No | `datetime('now')` | NOT NULL | Row creation timestamp |
| `updated_at` | TEXT | No | `datetime('now')` | NOT NULL | Last modification timestamp |

### Indexes on `accounts`

- `idx_accounts_customer` -- join acceleration for customer-account lookups.
- `idx_accounts_status` -- filters for active-account reports.
- `idx_accounts_type` -- groups by product type.

### Cascade behaviour

Deleting a customer row cascades to delete all associated accounts.

---

## Table: `transactions`

Individual monetary events (purchases, refunds, transfers, etc.) against an account.

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| `transaction_id` | INTEGER | No | AUTOINCREMENT | PRIMARY KEY | Surrogate key |
| `account_id` | INTEGER | No | -- | FK -> accounts.account_id ON DELETE CASCADE | Source account |
| `merchant_id` | INTEGER | Yes | NULL | FK -> merchants.merchant_id ON DELETE SET NULL | Receiving merchant (nullable for internal txns) |
| `transaction_ref` | TEXT | No | -- | NOT NULL, UNIQUE | Human-readable reference (TXN-XXXXXXXX) |
| `transaction_type` | TEXT | No | -- | CHECK IN (purchase, refund, transfer, withdrawal, deposit, fee, interest) | Event type |
| `amount` | REAL | No | -- | NOT NULL | Monetary value (always positive; direction inferred from type) |
| `currency` | TEXT | No | `'USD'` | NOT NULL | ISO 4217 currency code |
| `transaction_date` | TEXT | No | -- | NOT NULL | Datetime the transaction was initiated |
| `posted_date` | TEXT | Yes | NULL | -- | Datetime the transaction was settled |
| `description` | TEXT | Yes | NULL | -- | Human-readable memo |
| `channel` | TEXT | No | -- | CHECK IN (online, pos, atm, mobile, branch, wire) | Origination channel |
| `status` | TEXT | No | `'completed'` | CHECK IN (completed, pending, failed, reversed, disputed) | Settlement status |
| `created_at` | TEXT | No | `datetime('now')` | NOT NULL | Row creation timestamp |

### Indexes on `transactions`

- `idx_transactions_account` -- join acceleration for account statement generation.
- `idx_transactions_merchant` -- merchant revenue rollups.
- `idx_transactions_date` -- time-range filters and partitioning.
- `idx_transactions_status` -- settlement reconciliation queries.
- `idx_transactions_type` -- aggregation by transaction type.
- `idx_transactions_channel` -- channel analytics.

---

## Table: `merchants`

Registry of payees and vendors that receive transaction payments.

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| `merchant_id` | INTEGER | No | AUTOINCREMENT | PRIMARY KEY | Surrogate key |
| `merchant_name` | TEXT | No | -- | NOT NULL | Legal business name |
| `merchant_code` | TEXT | No | -- | NOT NULL, UNIQUE | Merchant category code (MCC-XXXX) |
| `category` | TEXT | No | -- | CHECK IN (grocery, restaurant, gas_station, online_retail, travel, healthcare, utilities, entertainment, education, financial_services) | Industry classification |
| `city` | TEXT | Yes | NULL | -- | City of registration |
| `state` | TEXT | Yes | NULL | -- | State / province |
| `country` | TEXT | No | `'US'` | NOT NULL | Country code |
| `registration_date` | TEXT | No | -- | NOT NULL | Date the merchant was onboarded |
| `status` | TEXT | No | `'active'` | CHECK IN (active, inactive, suspended) | Operational status |
| `created_at` | TEXT | No | `datetime('now')` | NOT NULL | Row creation timestamp |

### Indexes on `merchants`

- `idx_merchants_category` -- category-level aggregation.
- `idx_merchants_status` -- filter for active merchants.

---

## Table: `fraud_flags`

Risk annotations attached to transactions by the fraud detection engine or manual review.

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| `flag_id` | INTEGER | No | AUTOINCREMENT | PRIMARY KEY | Surrogate key |
| `transaction_id` | INTEGER | No | -- | FK -> transactions.transaction_id ON DELETE CASCADE | Flagged transaction |
| `flag_type` | TEXT | No | -- | CHECK IN (velocity, amount_anomaly, geo_anomaly, merchant_risk, account_takeover, card_not_present, pattern_deviation, manual_review) | Detection rule that triggered the flag |
| `risk_score` | REAL | No | -- | CHECK (0.0 <= risk_score <= 1.0) | Normalised risk score |
| `description` | TEXT | Yes | NULL | -- | Human-readable explanation |
| `resolution` | TEXT | Yes | NULL | CHECK IN (confirmed_fraud, false_positive, under_review, NULL) | Outcome of investigation |
| `flagged_at` | TEXT | No | `datetime('now')` | NOT NULL | When the flag was raised |
| `resolved_at` | TEXT | Yes | NULL | -- | When the flag was resolved |
| `analyst_notes` | TEXT | Yes | NULL | -- | Free-text notes from the reviewing analyst |

### Indexes on `fraud_flags`

- `idx_fraud_flags_txn` -- join to transaction table.
- `idx_fraud_flags_type` -- workload distribution by flag type.
- `idx_fraud_flags_score` -- threshold-based triage queries.

---

## Relationship Summary

```
customers  1 ──── * accounts    (customer_id FK, CASCADE)
accounts   1 ──── * transactions (account_id FK, CASCADE)
merchants  1 ──── * transactions (merchant_id FK, SET NULL)
transactions 1 ── * fraud_flags  (transaction_id FK, CASCADE)
```

## Data Volume (Seeded Dataset)

| Table | Rows |
|-------|------|
| customers | 500 |
| accounts | 1,000 |
| transactions | 5,000 |
| merchants | 200 |
| fraud_flags | ~300 |

## Migration Notes

- The schema is created idempotently via `CREATE TABLE IF NOT EXISTS`.
- Calling `create_schema()` multiple times is safe and will not duplicate tables or indexes.
- Use `drop_all()` followed by `create_schema()` for a full reset during development.
