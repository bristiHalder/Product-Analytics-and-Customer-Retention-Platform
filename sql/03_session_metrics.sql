-- ============================================================================
-- 03_session_metrics.sql  —  Session-level engagement & cart abandonment
-- ============================================================================

CREATE OR REPLACE VIEW vw_session_metrics AS
SELECT
    user_session,
    MIN(user_id)                                                AS user_id,
    MIN(event_time)                                             AS session_start,
    MAX(event_time)                                             AS session_end,
    EXTRACT(EPOCH FROM (MAX(event_time) - MIN(event_time)))     AS session_duration_proxy,
    COUNT(*)                                                    AS n_events,
    COUNT(*) FILTER (WHERE event_type = 'view')                 AS n_views,
    COUNT(*) FILTER (WHERE event_type = 'cart')                 AS n_cart,
    COUNT(*) FILTER (WHERE event_type = 'purchase')             AS n_purchase,
    SUM(price) FILTER (WHERE event_type = 'purchase')           AS revenue,
    CASE
        WHEN COUNT(*) FILTER (WHERE event_type = 'cart') > 0
         AND COUNT(*) FILTER (WHERE event_type = 'purchase') = 0
        THEN 1 ELSE 0
    END                                                         AS cart_abandonment,
    CASE WHEN COUNT(*) FILTER (WHERE event_type = 'purchase') > 0
         THEN 1 ELSE 0 END                                      AS converted
FROM fact_events
GROUP BY user_session;

-- Overall cart-abandonment rate ---------------------------------------------
SELECT
    AVG(cart_abandonment)::NUMERIC(6, 4) AS cart_abandonment_rate,
    AVG(converted)::NUMERIC(6, 4)        AS session_conversion_rate,
    AVG(session_duration_proxy)          AS avg_session_seconds
FROM vw_session_metrics;
