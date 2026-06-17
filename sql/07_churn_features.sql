-- ============================================================================
-- 07_churn_features.sql  —  Feature table powering the churn ML models
-- Churn definition: no activity for 30+ days as of the latest event date.
-- ============================================================================

CREATE OR REPLACE VIEW vw_churn_features AS
WITH bounds AS (
    SELECT MAX(event_time) AS analysis_date FROM fact_events
),
per_user AS (
    SELECT
        e.user_id,
        COUNT(*)                                              AS total_events,
        COUNT(*) FILTER (WHERE event_type = 'view')           AS n_views,
        COUNT(*) FILTER (WHERE event_type = 'cart')           AS n_cart,
        COUNT(*) FILTER (WHERE event_type = 'purchase')       AS n_purchase,
        COUNT(DISTINCT user_session)                          AS n_sessions,
        COUNT(DISTINCT product_id)                            AS n_products,
        COUNT(DISTINCT brand)                                 AS n_brands,
        COUNT(DISTINCT category)                              AS n_categories,
        SUM(price) FILTER (WHERE event_type = 'purchase')     AS clv,
        AVG(price) FILTER (WHERE event_type = 'purchase')     AS aov,
        MIN(event_time)                                       AS first_seen,
        MAX(event_time)                                       AS last_seen
    FROM fact_events e
    GROUP BY e.user_id
)
SELECT
    p.user_id,
    p.total_events,
    p.n_views,
    p.n_cart,
    p.n_purchase,
    p.n_sessions,
    p.n_products,
    p.n_brands,
    p.n_categories,
    COALESCE(p.clv, 0)                                          AS customer_lifetime_value,
    COALESCE(p.aov, 0)                                          AS average_order_value,
    EXTRACT(EPOCH FROM (b.analysis_date - p.last_seen)) / 86400 AS days_since_last_seen,
    EXTRACT(EPOCH FROM (p.last_seen - p.first_seen)) / 86400    AS lifespan_days,
    p.n_cart::NUMERIC  / NULLIF(p.n_views, 0)                   AS view_to_cart_rate,
    p.n_purchase::NUMERIC / NULLIF(p.n_cart, 0)                 AS cart_to_purchase_rate,
    CASE WHEN EXTRACT(EPOCH FROM (b.analysis_date - p.last_seen)) / 86400 > 30
         THEN 1 ELSE 0 END                                      AS is_churned
FROM per_user p
CROSS JOIN bounds b;

-- Churn rate by acquisition cohort ------------------------------------------
SELECT
    DATE_TRUNC('month', um.first_seen) AS cohort_month,
    COUNT(*)                            AS users,
    AVG(cf.is_churned)::NUMERIC(6, 4)   AS churn_rate
FROM vw_churn_features cf
JOIN (SELECT user_id, MIN(event_time) AS first_seen FROM fact_events GROUP BY user_id) um
  USING (user_id)
GROUP BY 1
ORDER BY 1;
