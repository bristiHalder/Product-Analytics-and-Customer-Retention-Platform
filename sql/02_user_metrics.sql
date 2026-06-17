-- ============================================================================
-- 02_user_metrics.sql  —  User-level analytics in pure SQL
-- (mirror of the Python ETL; useful for warehouse-native pipelines & review)
-- ============================================================================

-- Active-user metrics: DAU / WAU / MAU --------------------------------------
CREATE OR REPLACE VIEW vw_active_users AS
SELECT
    event_date,
    COUNT(DISTINCT user_id)                                                AS dau,
    COUNT(DISTINCT user_id) FILTER (
        WHERE event_date > event_date - INTERVAL '7 days')                 AS wau_window,
    COUNT(DISTINCT user_id) FILTER (
        WHERE event_date > event_date - INTERVAL '30 days')                AS mau_window
FROM fact_events
GROUP BY event_date
ORDER BY event_date;

-- Rolling DAU / WAU / MAU on a given as-of date ------------------------------
-- DAU
SELECT COUNT(DISTINCT user_id) AS dau
FROM fact_events
WHERE event_date = (SELECT MAX(event_date) FROM fact_events);

-- WAU (trailing 7 days)
SELECT COUNT(DISTINCT user_id) AS wau
FROM fact_events
WHERE event_date > (SELECT MAX(event_date) FROM fact_events) - INTERVAL '7 days';

-- MAU (trailing 30 days)
SELECT COUNT(DISTINCT user_id) AS mau
FROM fact_events
WHERE event_date > (SELECT MAX(event_date) FROM fact_events) - INTERVAL '30 days';

-- Revenue & ARPU ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_revenue_summary AS
SELECT
    SUM(price) FILTER (WHERE event_type = 'purchase')                       AS total_revenue,
    COUNT(*)  FILTER (WHERE event_type = 'purchase')                        AS total_orders,
    COUNT(DISTINCT user_id)                                                 AS total_users,
    SUM(price) FILTER (WHERE event_type = 'purchase')
        / NULLIF(COUNT(DISTINCT user_id), 0)                               AS arpu
FROM fact_events;

-- Per-user lifetime value & frequency (SQL equivalent of user_metrics) ------
CREATE OR REPLACE VIEW vw_user_value AS
SELECT
    user_id,
    MIN(event_time)                                                        AS first_seen,
    MAX(event_time)                                                        AS last_seen,
    COUNT(*) FILTER (WHERE event_type = 'purchase')                        AS n_orders,
    SUM(price) FILTER (WHERE event_type = 'purchase')                      AS customer_lifetime_value,
    AVG(price) FILTER (WHERE event_type = 'purchase')                      AS average_order_value,
    COUNT(DISTINCT user_session)                                           AS n_sessions,
    CASE WHEN COUNT(*) FILTER (WHERE event_type = 'purchase') >= 2
         THEN 1 ELSE 0 END                                                 AS is_repeat_purchaser
FROM fact_events
GROUP BY user_id;
