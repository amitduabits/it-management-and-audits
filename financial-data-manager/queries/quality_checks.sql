-- ============================================================================
-- Financial Data Manager -- Data Quality Check Library
-- 10 production-grade queries covering null detection, duplicates, referential
-- integrity, date validation, outliers, format checks, completeness,
-- consistency, timeliness, and uniqueness.
-- ============================================================================


-- 1. Null Detection -- Check for NULLs in Required Fields Across All Tables
SELECT
    'customers'   AS table_name,
    'customer_id' AS column_name,
    COUNT(*)      AS null_count
FROM customers WHERE customer_id IS NULL
UNION ALL
SELECT 'customers', 'first_name',  COUNT(*) FROM customers WHERE first_name IS NULL
UNION ALL
SELECT 'customers', 'last_name',   COUNT(*) FROM customers WHERE last_name IS NULL
UNION ALL
SELECT 'customers', 'email',       COUNT(*) FROM customers WHERE email IS NULL
UNION ALL
SELECT 'customers', 'phone',       COUNT(*) FROM customers WHERE phone IS NULL
UNION ALL
SELECT 'customers', 'pan_number',  COUNT(*) FROM customers WHERE pan_number IS NULL
UNION ALL
SELECT 'customers', 'aadhar_hash', COUNT(*) FROM customers WHERE aadhar_hash IS NULL
UNION ALL
SELECT 'customers', 'city',        COUNT(*) FROM customers WHERE city IS NULL
UNION ALL
SELECT 'customers', 'segment',     COUNT(*) FROM customers WHERE segment IS NULL
UNION ALL
SELECT 'accounts',  'account_id',     COUNT(*) FROM accounts WHERE account_id IS NULL
UNION ALL
SELECT 'accounts',  'customer_id',    COUNT(*) FROM accounts WHERE customer_id IS NULL
UNION ALL
SELECT 'accounts',  'account_number', COUNT(*) FROM accounts WHERE account_number IS NULL
UNION ALL
SELECT 'accounts',  'account_type',   COUNT(*) FROM accounts WHERE account_type IS NULL
UNION ALL
SELECT 'accounts',  'balance',        COUNT(*) FROM accounts WHERE balance IS NULL
UNION ALL
SELECT 'accounts',  'status',         COUNT(*) FROM accounts WHERE status IS NULL
UNION ALL
SELECT 'accounts',  'opened_date',    COUNT(*) FROM accounts WHERE opened_date IS NULL
UNION ALL
SELECT 'transactions', 'transaction_id',   COUNT(*) FROM transactions WHERE transaction_id IS NULL
UNION ALL
SELECT 'transactions', 'account_id',       COUNT(*) FROM transactions WHERE account_id IS NULL
UNION ALL
SELECT 'transactions', 'amount',           COUNT(*) FROM transactions WHERE amount IS NULL
UNION ALL
SELECT 'transactions', 'transaction_date', COUNT(*) FROM transactions WHERE transaction_date IS NULL
UNION ALL
SELECT 'transactions', 'transaction_type', COUNT(*) FROM transactions WHERE transaction_type IS NULL
UNION ALL
SELECT 'transactions', 'status',           COUNT(*) FROM transactions WHERE status IS NULL
UNION ALL
SELECT 'merchants', 'merchant_id',   COUNT(*) FROM merchants WHERE merchant_id IS NULL
UNION ALL
SELECT 'merchants', 'merchant_name', COUNT(*) FROM merchants WHERE merchant_name IS NULL
UNION ALL
SELECT 'merchants', 'category',      COUNT(*) FROM merchants WHERE category IS NULL
UNION ALL
SELECT 'fraud_flags', 'flag_id',        COUNT(*) FROM fraud_flags WHERE flag_id IS NULL
UNION ALL
SELECT 'fraud_flags', 'transaction_id', COUNT(*) FROM fraud_flags WHERE transaction_id IS NULL
UNION ALL
SELECT 'fraud_flags', 'flag_type',      COUNT(*) FROM fraud_flags WHERE flag_type IS NULL
UNION ALL
SELECT 'fraud_flags', 'risk_score',     COUNT(*) FROM fraud_flags WHERE risk_score IS NULL
ORDER BY null_count DESC;


-- 2. Duplicate Records -- Check for Duplicates in Unique Columns
SELECT
    'customers - email'              AS check_description,
    email                            AS duplicate_value,
    COUNT(*)                         AS occurrence_count
FROM customers
GROUP BY email
HAVING occurrence_count > 1
UNION ALL
SELECT
    'customers - pan_number',
    pan_number,
    COUNT(*)
FROM customers
GROUP BY pan_number
HAVING COUNT(*) > 1
UNION ALL
SELECT
    'customers - aadhar_hash',
    aadhar_hash,
    COUNT(*)
FROM customers
GROUP BY aadhar_hash
HAVING COUNT(*) > 1
UNION ALL
SELECT
    'accounts - account_number',
    account_number,
    COUNT(*)
FROM accounts
GROUP BY account_number
HAVING COUNT(*) > 1
UNION ALL
SELECT
    'transactions - transaction_ref',
    transaction_ref,
    COUNT(*)
FROM transactions
GROUP BY transaction_ref
HAVING COUNT(*) > 1
UNION ALL
SELECT
    'merchants - gst_number',
    gst_number,
    COUNT(*)
FROM merchants
WHERE gst_number IS NOT NULL
GROUP BY gst_number
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;


-- 3. Referential Integrity -- Verify All Foreign Key References Are Valid
SELECT
    'accounts -> customers'          AS fk_relationship,
    a.account_id                     AS orphan_record_id,
    a.customer_id                    AS invalid_fk_value
FROM accounts a
LEFT JOIN customers c ON c.customer_id = a.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT
    'transactions -> accounts',
    t.transaction_id,
    t.account_id
FROM transactions t
LEFT JOIN accounts a ON a.account_id = t.account_id
WHERE a.account_id IS NULL
UNION ALL
SELECT
    'transactions -> merchants',
    t.transaction_id,
    t.merchant_id
FROM transactions t
LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
WHERE t.merchant_id IS NOT NULL
  AND m.merchant_id IS NULL
UNION ALL
SELECT
    'fraud_flags -> transactions',
    f.flag_id,
    f.transaction_id
FROM fraud_flags f
LEFT JOIN transactions t ON t.transaction_id = f.transaction_id
WHERE t.transaction_id IS NULL
ORDER BY fk_relationship;


-- 4. Date Range Validation -- Ensure Dates Are Within Valid Boundaries
SELECT
    'accounts - opened_date in future'  AS validation_rule,
    COUNT(*)                            AS violation_count
FROM accounts
WHERE DATE(opened_date) > DATE('now')
UNION ALL
SELECT
    'accounts - opened_date before 2000',
    COUNT(*)
FROM accounts
WHERE DATE(opened_date) < DATE('2000-01-01')
UNION ALL
SELECT
    'transactions - transaction_date in future',
    COUNT(*)
FROM transactions
WHERE DATE(transaction_date) > DATE('now')
UNION ALL
SELECT
    'transactions - transaction_date before 2000',
    COUNT(*)
FROM transactions
WHERE DATE(transaction_date) < DATE('2000-01-01')
UNION ALL
SELECT
    'transactions - posted_date before transaction_date',
    COUNT(*)
FROM transactions
WHERE posted_date IS NOT NULL
  AND DATE(posted_date) < DATE(transaction_date)
UNION ALL
SELECT
    'transactions - posting lag exceeds 30 days',
    COUNT(*)
FROM transactions
WHERE posted_date IS NOT NULL
  AND JULIANDAY(posted_date) - JULIANDAY(transaction_date) > 30
ORDER BY violation_count DESC;


-- 5. Amount Outliers -- Flag Transactions More Than 3 Standard Deviations from Mean
WITH stats AS (
    SELECT
        AVG(amount)  AS mean_amount,
        AVG(amount * amount) - AVG(amount) * AVG(amount) AS variance
    FROM transactions
    WHERE status = 'completed'
),
thresholds AS (
    SELECT
        mean_amount,
        mean_amount - 3 * SQRT(variance) AS lower_bound,
        mean_amount + 3 * SQRT(variance) AS upper_bound,
        SQRT(variance)                   AS std_dev
    FROM stats
)
SELECT
    t.transaction_id,
    t.transaction_ref,
    t.amount,
    ROUND(th.mean_amount, 2)            AS mean_amount,
    ROUND(th.std_dev, 2)                AS std_dev,
    ROUND((t.amount - th.mean_amount) / th.std_dev, 2)
                                        AS z_score,
    a.account_number,
    c.first_name || ' ' || c.last_name  AS customer_name,
    t.transaction_date,
    t.channel
FROM transactions t
CROSS JOIN thresholds th
JOIN accounts a  ON a.account_id = t.account_id
JOIN customers c ON c.customer_id = a.customer_id
WHERE t.status = 'completed'
  AND (t.amount > th.upper_bound OR t.amount < th.lower_bound)
ORDER BY ABS(t.amount - th.mean_amount) DESC;


-- 6. Format Validation -- Check PAN, GST, and Email Formats
SELECT
    'customers - invalid PAN format'     AS validation_rule,
    customer_id                          AS record_id,
    pan_number                           AS invalid_value
FROM customers
WHERE pan_number IS NOT NULL
  AND pan_number NOT GLOB '[A-Z][A-Z][A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9][A-Z]'
UNION ALL
SELECT
    'customers - invalid email format',
    customer_id,
    email
FROM customers
WHERE email IS NOT NULL
  AND email NOT LIKE '%_@_%.__%'
UNION ALL
SELECT
    'merchants - invalid GST format',
    merchant_id,
    gst_number
FROM merchants
WHERE gst_number IS NOT NULL
  AND LENGTH(gst_number) != 15
ORDER BY validation_rule;


-- 7. Completeness -- Measure Overall Data Completeness Percentage per Table
SELECT
    'customers'                         AS table_name,
    COUNT(*)                            AS total_rows,
    ROUND(100.0 - (
        (SUM(CASE WHEN first_name IS NULL  THEN 1 ELSE 0 END) +
         SUM(CASE WHEN last_name IS NULL   THEN 1 ELSE 0 END) +
         SUM(CASE WHEN email IS NULL       THEN 1 ELSE 0 END) +
         SUM(CASE WHEN phone IS NULL       THEN 1 ELSE 0 END) +
         SUM(CASE WHEN pan_number IS NULL  THEN 1 ELSE 0 END) +
         SUM(CASE WHEN aadhar_hash IS NULL THEN 1 ELSE 0 END) +
         SUM(CASE WHEN city IS NULL        THEN 1 ELSE 0 END) +
         SUM(CASE WHEN segment IS NULL     THEN 1 ELSE 0 END))
        * 100.0 / (COUNT(*) * 8)
    ), 2)                               AS completeness_pct
FROM customers
UNION ALL
SELECT
    'accounts',
    COUNT(*),
    ROUND(100.0 - (
        (SUM(CASE WHEN customer_id IS NULL    THEN 1 ELSE 0 END) +
         SUM(CASE WHEN account_number IS NULL THEN 1 ELSE 0 END) +
         SUM(CASE WHEN account_type IS NULL   THEN 1 ELSE 0 END) +
         SUM(CASE WHEN balance IS NULL        THEN 1 ELSE 0 END) +
         SUM(CASE WHEN status IS NULL         THEN 1 ELSE 0 END) +
         SUM(CASE WHEN opened_date IS NULL    THEN 1 ELSE 0 END))
        * 100.0 / (COUNT(*) * 6)
    ), 2)
FROM accounts
UNION ALL
SELECT
    'transactions',
    COUNT(*),
    ROUND(100.0 - (
        (SUM(CASE WHEN account_id IS NULL        THEN 1 ELSE 0 END) +
         SUM(CASE WHEN merchant_id IS NULL       THEN 1 ELSE 0 END) +
         SUM(CASE WHEN transaction_ref IS NULL   THEN 1 ELSE 0 END) +
         SUM(CASE WHEN amount IS NULL            THEN 1 ELSE 0 END) +
         SUM(CASE WHEN transaction_date IS NULL  THEN 1 ELSE 0 END) +
         SUM(CASE WHEN posted_date IS NULL       THEN 1 ELSE 0 END) +
         SUM(CASE WHEN transaction_type IS NULL  THEN 1 ELSE 0 END) +
         SUM(CASE WHEN channel IS NULL           THEN 1 ELSE 0 END) +
         SUM(CASE WHEN status IS NULL            THEN 1 ELSE 0 END))
        * 100.0 / (COUNT(*) * 9)
    ), 2)
FROM transactions
UNION ALL
SELECT
    'merchants',
    COUNT(*),
    ROUND(100.0 - (
        (SUM(CASE WHEN merchant_name IS NULL THEN 1 ELSE 0 END) +
         SUM(CASE WHEN category IS NULL      THEN 1 ELSE 0 END) +
         SUM(CASE WHEN city IS NULL          THEN 1 ELSE 0 END) +
         SUM(CASE WHEN state IS NULL         THEN 1 ELSE 0 END) +
         SUM(CASE WHEN gst_number IS NULL    THEN 1 ELSE 0 END))
        * 100.0 / (COUNT(*) * 5)
    ), 2)
FROM merchants
UNION ALL
SELECT
    'fraud_flags',
    COUNT(*),
    ROUND(100.0 - (
        (SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) +
         SUM(CASE WHEN flag_type IS NULL      THEN 1 ELSE 0 END) +
         SUM(CASE WHEN risk_score IS NULL     THEN 1 ELSE 0 END) +
         SUM(CASE WHEN resolution IS NULL     THEN 1 ELSE 0 END) +
         SUM(CASE WHEN analyst_notes IS NULL  THEN 1 ELSE 0 END))
        * 100.0 / (COUNT(*) * 5)
    ), 2)
FROM fraud_flags
ORDER BY completeness_pct ASC;


-- 8. Consistency -- Validate Enum / Domain Values Are Consistent
SELECT
    'accounts - invalid account_type'    AS consistency_rule,
    account_type                         AS invalid_value,
    COUNT(*)                             AS occurrence_count
FROM accounts
WHERE account_type NOT IN ('savings', 'current', 'salary', 'fixed_deposit', 'recurring_deposit')
GROUP BY account_type
UNION ALL
SELECT
    'accounts - invalid status',
    status,
    COUNT(*)
FROM accounts
WHERE status NOT IN ('active', 'inactive', 'closed', 'frozen', 'dormant')
GROUP BY status
UNION ALL
SELECT
    'transactions - invalid transaction_type',
    transaction_type,
    COUNT(*)
FROM transactions
WHERE transaction_type NOT IN ('purchase', 'refund', 'transfer', 'withdrawal', 'deposit', 'payment')
GROUP BY transaction_type
UNION ALL
SELECT
    'transactions - invalid channel',
    channel,
    COUNT(*)
FROM transactions
WHERE channel NOT IN ('online', 'mobile', 'branch', 'atm', 'pos', 'upi')
GROUP BY channel
UNION ALL
SELECT
    'transactions - invalid status',
    status,
    COUNT(*)
FROM transactions
WHERE status NOT IN ('completed', 'pending', 'failed', 'reversed', 'cancelled')
GROUP BY status
UNION ALL
SELECT
    'customers - invalid segment',
    segment,
    COUNT(*)
FROM customers
WHERE segment NOT IN ('retail', 'premium', 'corporate', 'nri', 'sme')
GROUP BY segment
UNION ALL
SELECT
    'fraud_flags - invalid flag_type',
    flag_type,
    COUNT(*)
FROM fraud_flags
WHERE flag_type NOT IN ('velocity', 'amount', 'geographic', 'pattern', 'identity', 'device')
GROUP BY flag_type
UNION ALL
SELECT
    'fraud_flags - invalid resolution',
    resolution,
    COUNT(*)
FROM fraud_flags
WHERE resolution IS NOT NULL
  AND resolution NOT IN ('confirmed_fraud', 'false_positive', 'under_review', 'escalated', 'dismissed')
GROUP BY resolution
ORDER BY occurrence_count DESC;


-- 9. Timeliness -- Check Data Is Current and Recently Updated
SELECT
    'transactions - latest record age'   AS timeliness_check,
    MAX(transaction_date)                AS latest_record,
    CAST(JULIANDAY('now') - JULIANDAY(MAX(transaction_date)) AS INTEGER)
                                         AS days_since_latest,
    CASE
        WHEN JULIANDAY('now') - JULIANDAY(MAX(transaction_date)) <= 1
        THEN 'CURRENT'
        WHEN JULIANDAY('now') - JULIANDAY(MAX(transaction_date)) <= 7
        THEN 'RECENT'
        WHEN JULIANDAY('now') - JULIANDAY(MAX(transaction_date)) <= 30
        THEN 'STALE'
        ELSE 'OUTDATED'
    END                                  AS freshness_status
FROM transactions
UNION ALL
SELECT
    'transactions - latest posted_date age',
    MAX(posted_date),
    CAST(JULIANDAY('now') - JULIANDAY(MAX(posted_date)) AS INTEGER),
    CASE
        WHEN JULIANDAY('now') - JULIANDAY(MAX(posted_date)) <= 1
        THEN 'CURRENT'
        WHEN JULIANDAY('now') - JULIANDAY(MAX(posted_date)) <= 7
        THEN 'RECENT'
        WHEN JULIANDAY('now') - JULIANDAY(MAX(posted_date)) <= 30
        THEN 'STALE'
        ELSE 'OUTDATED'
    END
FROM transactions
WHERE posted_date IS NOT NULL
UNION ALL
SELECT
    'accounts - latest opened_date age',
    MAX(opened_date),
    CAST(JULIANDAY('now') - JULIANDAY(MAX(opened_date)) AS INTEGER),
    CASE
        WHEN JULIANDAY('now') - JULIANDAY(MAX(opened_date)) <= 7
        THEN 'CURRENT'
        WHEN JULIANDAY('now') - JULIANDAY(MAX(opened_date)) <= 30
        THEN 'RECENT'
        WHEN JULIANDAY('now') - JULIANDAY(MAX(opened_date)) <= 90
        THEN 'STALE'
        ELSE 'OUTDATED'
    END
FROM accounts
UNION ALL
SELECT
    'fraud_flags - unresolved flags count',
    CAST(COUNT(*) AS TEXT),
    COUNT(*),
    CASE
        WHEN COUNT(*) = 0 THEN 'ALL_RESOLVED'
        WHEN COUNT(*) <= 10 THEN 'ACCEPTABLE'
        WHEN COUNT(*) <= 50 THEN 'ATTENTION_NEEDED'
        ELSE 'CRITICAL'
    END
FROM fraud_flags
WHERE resolution IS NULL OR resolution = 'under_review'
ORDER BY days_since_latest DESC;


-- 10. Uniqueness -- Verify Primary Key Uniqueness Across All Tables
SELECT
    'customers - customer_id'            AS uniqueness_check,
    COUNT(*)                             AS total_rows,
    COUNT(DISTINCT customer_id)          AS distinct_values,
    COUNT(*) - COUNT(DISTINCT customer_id)
                                         AS duplicate_count,
    CASE
        WHEN COUNT(*) = COUNT(DISTINCT customer_id) THEN 'PASS'
        ELSE 'FAIL'
    END                                  AS result
FROM customers
UNION ALL
SELECT
    'accounts - account_id',
    COUNT(*),
    COUNT(DISTINCT account_id),
    COUNT(*) - COUNT(DISTINCT account_id),
    CASE WHEN COUNT(*) = COUNT(DISTINCT account_id) THEN 'PASS' ELSE 'FAIL' END
FROM accounts
UNION ALL
SELECT
    'transactions - transaction_id',
    COUNT(*),
    COUNT(DISTINCT transaction_id),
    COUNT(*) - COUNT(DISTINCT transaction_id),
    CASE WHEN COUNT(*) = COUNT(DISTINCT transaction_id) THEN 'PASS' ELSE 'FAIL' END
FROM transactions
UNION ALL
SELECT
    'merchants - merchant_id',
    COUNT(*),
    COUNT(DISTINCT merchant_id),
    COUNT(*) - COUNT(DISTINCT merchant_id),
    CASE WHEN COUNT(*) = COUNT(DISTINCT merchant_id) THEN 'PASS' ELSE 'FAIL' END
FROM merchants
UNION ALL
SELECT
    'fraud_flags - flag_id',
    COUNT(*),
    COUNT(DISTINCT flag_id),
    COUNT(*) - COUNT(DISTINCT flag_id),
    CASE WHEN COUNT(*) = COUNT(DISTINCT flag_id) THEN 'PASS' ELSE 'FAIL' END
FROM fraud_flags
ORDER BY duplicate_count DESC;
