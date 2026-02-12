-- ============================================================================
-- Financial Data Manager -- Analytical Query Library
-- 20 production-grade queries covering revenue, fraud, merchant, and
-- reconciliation analytics.
-- ============================================================================


-- 1. Top 20 Customers by Lifetime Transaction Volume
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.segment,
    COUNT(t.transaction_id)            AS txn_count,
    ROUND(SUM(t.amount), 2)            AS total_amount,
    ROUND(AVG(t.amount), 2)            AS avg_txn_amount,
    MIN(t.transaction_date)            AS first_txn,
    MAX(t.transaction_date)            AS last_txn
FROM customers c
JOIN accounts a  ON a.customer_id = c.customer_id
JOIN transactions t ON t.account_id = a.account_id
WHERE t.status = 'completed'
GROUP BY c.customer_id
ORDER BY total_amount DESC
LIMIT 20;


-- 2. Monthly Revenue Trend (last 24 months)
SELECT
    strftime('%Y-%m', t.transaction_date) AS month,
    COUNT(*)                              AS txn_count,
    ROUND(SUM(t.amount), 2)              AS total_revenue,
    ROUND(AVG(t.amount), 2)              AS avg_amount,
    COUNT(DISTINCT t.account_id)          AS unique_accounts
FROM transactions t
WHERE t.transaction_type = 'purchase'
  AND t.status = 'completed'
GROUP BY month
ORDER BY month;


-- 3. Merchant Category Breakdown
SELECT
    m.category,
    COUNT(DISTINCT m.merchant_id)       AS merchant_count,
    COUNT(t.transaction_id)             AS txn_count,
    ROUND(SUM(t.amount), 2)            AS total_volume,
    ROUND(AVG(t.amount), 2)            AS avg_txn,
    ROUND(SUM(t.amount) * 100.0 / (SELECT SUM(amount) FROM transactions WHERE status = 'completed'), 2)
                                        AS pct_of_total
FROM merchants m
JOIN transactions t ON t.merchant_id = m.merchant_id
WHERE t.status = 'completed'
GROUP BY m.category
ORDER BY total_volume DESC;


-- 4. High-Risk Fraud Flags with Transaction Details
SELECT
    f.flag_id,
    f.flag_type,
    f.risk_score,
    t.transaction_ref,
    t.amount,
    t.transaction_date,
    t.channel,
    m.merchant_name,
    m.category                          AS merchant_category,
    f.resolution,
    f.analyst_notes
FROM fraud_flags f
JOIN transactions t ON t.transaction_id = f.transaction_id
LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
WHERE f.risk_score >= 0.80
ORDER BY f.risk_score DESC, t.amount DESC
LIMIT 50;


-- 5. Account Balance Distribution by Type
SELECT
    a.account_type,
    COUNT(*)                            AS account_count,
    ROUND(MIN(a.balance), 2)           AS min_balance,
    ROUND(AVG(a.balance), 2)           AS avg_balance,
    ROUND(MAX(a.balance), 2)           AS max_balance,
    ROUND(SUM(a.balance), 2)           AS total_balance
FROM accounts a
WHERE a.status = 'active'
GROUP BY a.account_type
ORDER BY total_balance DESC;


-- 6. Customer Segment Revenue Contribution
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id)      AS customer_count,
    COUNT(t.transaction_id)            AS txn_count,
    ROUND(SUM(t.amount), 2)           AS total_revenue,
    ROUND(AVG(t.amount), 2)           AS avg_txn,
    ROUND(SUM(t.amount) / COUNT(DISTINCT c.customer_id), 2)
                                       AS revenue_per_customer
FROM customers c
JOIN accounts a  ON a.customer_id = c.customer_id
JOIN transactions t ON t.account_id = a.account_id
WHERE t.status = 'completed'
GROUP BY c.segment
ORDER BY total_revenue DESC;


-- 7. Channel Usage Analysis
SELECT
    t.channel,
    COUNT(*)                           AS txn_count,
    ROUND(SUM(t.amount), 2)          AS total_amount,
    ROUND(AVG(t.amount), 2)          AS avg_amount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 2)
                                      AS pct_of_transactions
FROM transactions t
GROUP BY t.channel
ORDER BY txn_count DESC;


-- 8. Fraud Detection -- Velocity Analysis (accounts with > 10 txns in a single day)
SELECT
    a.account_id,
    a.account_number,
    DATE(t.transaction_date)           AS txn_date,
    COUNT(*)                           AS daily_txn_count,
    ROUND(SUM(t.amount), 2)          AS daily_total
FROM transactions t
JOIN accounts a ON a.account_id = t.account_id
GROUP BY a.account_id, DATE(t.transaction_date)
HAVING daily_txn_count > 10
ORDER BY daily_txn_count DESC;


-- 9. Reconciliation -- Transactions Without Posted Date
SELECT
    t.transaction_id,
    t.transaction_ref,
    t.transaction_type,
    t.amount,
    t.transaction_date,
    t.status,
    t.channel,
    JULIANDAY('now') - JULIANDAY(t.transaction_date) AS days_since_txn
FROM transactions t
WHERE t.posted_date IS NULL
  AND t.status = 'completed'
ORDER BY t.transaction_date;


-- 10. Top 10 Merchants by Revenue
SELECT
    m.merchant_id,
    m.merchant_name,
    m.category,
    m.city || ', ' || m.state          AS location,
    COUNT(t.transaction_id)            AS txn_count,
    ROUND(SUM(t.amount), 2)           AS total_revenue,
    ROUND(AVG(t.amount), 2)           AS avg_txn
FROM merchants m
JOIN transactions t ON t.merchant_id = m.merchant_id
WHERE t.status = 'completed'
GROUP BY m.merchant_id
ORDER BY total_revenue DESC
LIMIT 10;


-- 11. Customer Retention -- Accounts Opened vs Closed by Quarter
SELECT
    strftime('%Y-Q', a.opened_date) || CAST((CAST(strftime('%m', a.opened_date) AS INTEGER) + 2) / 3 AS TEXT) AS quarter,
    SUM(CASE WHEN a.status != 'closed' THEN 1 ELSE 0 END) AS opened,
    SUM(CASE WHEN a.status = 'closed'  THEN 1 ELSE 0 END) AS closed,
    COUNT(*)                                                AS total
FROM accounts a
GROUP BY strftime('%Y', a.opened_date), ((CAST(strftime('%m', a.opened_date) AS INTEGER) + 2) / 3)
ORDER BY strftime('%Y', a.opened_date), ((CAST(strftime('%m', a.opened_date) AS INTEGER) + 2) / 3);


-- 12. Window Function -- Running Total of Transactions per Account
SELECT
    t.account_id,
    t.transaction_id,
    t.transaction_date,
    t.amount,
    SUM(t.amount) OVER (
        PARTITION BY t.account_id
        ORDER BY t.transaction_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM transactions t
WHERE t.status = 'completed'
ORDER BY t.account_id, t.transaction_date
LIMIT 100;


-- 13. CTE -- Month-over-Month Growth Rate
WITH monthly AS (
    SELECT
        strftime('%Y-%m', transaction_date) AS month,
        SUM(amount) AS revenue
    FROM transactions
    WHERE status = 'completed' AND transaction_type = 'purchase'
    GROUP BY month
),
with_lag AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS prev_revenue
    FROM monthly
)
SELECT
    month,
    ROUND(revenue, 2)                                        AS revenue,
    ROUND(prev_revenue, 2)                                   AS prev_revenue,
    CASE
        WHEN prev_revenue IS NOT NULL AND prev_revenue > 0
        THEN ROUND((revenue - prev_revenue) / prev_revenue * 100, 2)
        ELSE NULL
    END                                                      AS growth_pct
FROM with_lag
ORDER BY month;


-- 14. Fraud Flag Resolution Summary
SELECT
    f.flag_type,
    COUNT(*)                                                 AS total_flags,
    SUM(CASE WHEN f.resolution = 'confirmed_fraud'  THEN 1 ELSE 0 END) AS confirmed,
    SUM(CASE WHEN f.resolution = 'false_positive'   THEN 1 ELSE 0 END) AS false_positive,
    SUM(CASE WHEN f.resolution = 'under_review'     THEN 1 ELSE 0 END) AS under_review,
    SUM(CASE WHEN f.resolution IS NULL              THEN 1 ELSE 0 END) AS unresolved,
    ROUND(AVG(f.risk_score), 4)                              AS avg_risk_score
FROM fraud_flags f
GROUP BY f.flag_type
ORDER BY total_flags DESC;


-- 15. Large Transaction Audit Trail (amounts above 5000)
SELECT
    t.transaction_id,
    t.transaction_ref,
    t.amount,
    t.transaction_date,
    t.channel,
    t.status,
    a.account_number,
    c.first_name || ' ' || c.last_name AS customer_name,
    m.merchant_name,
    CASE
        WHEN EXISTS (SELECT 1 FROM fraud_flags ff WHERE ff.transaction_id = t.transaction_id)
        THEN 'FLAGGED'
        ELSE 'CLEAN'
    END AS fraud_status
FROM transactions t
JOIN accounts a  ON a.account_id = t.account_id
JOIN customers c ON c.customer_id = a.customer_id
LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
WHERE t.amount > 5000
ORDER BY t.amount DESC;


-- 16. Dormant Account Detection (no transactions in last 180 days)
SELECT
    a.account_id,
    a.account_number,
    a.account_type,
    a.balance,
    a.status,
    c.first_name || ' ' || c.last_name AS customer_name,
    MAX(t.transaction_date) AS last_txn_date,
    CAST(JULIANDAY('now') - JULIANDAY(MAX(t.transaction_date)) AS INTEGER) AS days_inactive
FROM accounts a
JOIN customers c ON c.customer_id = a.customer_id
LEFT JOIN transactions t ON t.account_id = a.account_id
WHERE a.status = 'active'
GROUP BY a.account_id
HAVING days_inactive > 180 OR last_txn_date IS NULL
ORDER BY days_inactive DESC;


-- 17. Daily Transaction Summary with 7-Day Moving Average
WITH daily AS (
    SELECT
        DATE(transaction_date) AS txn_date,
        COUNT(*)               AS daily_count,
        SUM(amount)            AS daily_amount
    FROM transactions
    WHERE status = 'completed'
    GROUP BY DATE(transaction_date)
)
SELECT
    txn_date,
    daily_count,
    ROUND(daily_amount, 2)   AS daily_amount,
    ROUND(AVG(daily_amount) OVER (
        ORDER BY txn_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2)                    AS moving_avg_7d
FROM daily
ORDER BY txn_date;


-- 18. Cross-Channel Transaction Comparison
SELECT
    c.segment,
    t.channel,
    COUNT(*)                 AS txn_count,
    ROUND(SUM(t.amount), 2) AS total_amount,
    ROUND(AVG(t.amount), 2) AS avg_amount
FROM customers c
JOIN accounts a  ON a.customer_id = c.customer_id
JOIN transactions t ON t.account_id = a.account_id
WHERE t.status = 'completed'
GROUP BY c.segment, t.channel
ORDER BY c.segment, total_amount DESC;


-- 19. Merchant Risk Scoring -- Merchants with Highest Fraud Flag Rates
SELECT
    m.merchant_id,
    m.merchant_name,
    m.category,
    COUNT(DISTINCT t.transaction_id)    AS total_txns,
    COUNT(DISTINCT f.flag_id)           AS fraud_flags,
    ROUND(COUNT(DISTINCT f.flag_id) * 100.0 / NULLIF(COUNT(DISTINCT t.transaction_id), 0), 2)
                                        AS flag_rate_pct,
    ROUND(AVG(f.risk_score), 4)        AS avg_risk_score
FROM merchants m
JOIN transactions t ON t.merchant_id = m.merchant_id
LEFT JOIN fraud_flags f ON f.transaction_id = t.transaction_id
GROUP BY m.merchant_id
HAVING fraud_flags > 0
ORDER BY flag_rate_pct DESC
LIMIT 20;


-- 20. End-of-Day Reconciliation -- Expected vs Actual Posted Amounts
WITH expected AS (
    SELECT
        DATE(transaction_date) AS txn_date,
        SUM(amount)            AS expected_amount,
        COUNT(*)               AS expected_count
    FROM transactions
    WHERE status = 'completed'
    GROUP BY DATE(transaction_date)
),
posted AS (
    SELECT
        DATE(posted_date)      AS post_date,
        SUM(amount)            AS posted_amount,
        COUNT(*)               AS posted_count
    FROM transactions
    WHERE posted_date IS NOT NULL
    GROUP BY DATE(posted_date)
)
SELECT
    e.txn_date,
    e.expected_count,
    COALESCE(p.posted_count, 0)                              AS posted_count,
    e.expected_count - COALESCE(p.posted_count, 0)           AS unposted_count,
    ROUND(e.expected_amount, 2)                              AS expected_amount,
    ROUND(COALESCE(p.posted_amount, 0), 2)                   AS posted_amount,
    ROUND(e.expected_amount - COALESCE(p.posted_amount, 0), 2) AS variance
FROM expected e
LEFT JOIN posted p ON p.post_date = e.txn_date
ORDER BY e.txn_date;
