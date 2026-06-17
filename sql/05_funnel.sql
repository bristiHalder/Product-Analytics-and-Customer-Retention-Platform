-- ============================================================================
-- 05_funnel.sql  —  Product funnel: view → cart → purchase → repeat purchase
-- ============================================================================

WITH user_funnel AS (
    SELECT
        user_id,
        MAX((event_type = 'view')::int)     AS reached_view,
        MAX((event_type = 'cart')::int)     AS reached_cart,
        (COUNT(*) FILTER (WHERE event_type = 'purchase') >= 1)::int AS reached_purchase,
        (COUNT(*) FILTER (WHERE event_type = 'purchase') >= 2)::int AS reached_repeat
    FROM fact_events
    GROUP BY user_id
)
SELECT
    SUM(reached_view)      AS users_view,
    SUM(reached_cart)      AS users_cart,
    SUM(reached_purchase)  AS users_purchase,
    SUM(reached_repeat)    AS users_repeat,
    -- stage-to-stage conversion
    ROUND(100.0 * SUM(reached_cart)     / NULLIF(SUM(reached_view), 0), 2)     AS view_to_cart_pct,
    ROUND(100.0 * SUM(reached_purchase) / NULLIF(SUM(reached_cart), 0), 2)     AS cart_to_purchase_pct,
    ROUND(100.0 * SUM(reached_repeat)   / NULLIF(SUM(reached_purchase), 0), 2) AS purchase_to_repeat_pct,
    -- overall conversion from top of funnel
    ROUND(100.0 * SUM(reached_purchase) / NULLIF(SUM(reached_view), 0), 2)     AS overall_conversion_pct
FROM user_funnel;
