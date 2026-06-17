-- ============================================================================
-- 04_product_metrics.sql  —  Product & catalog performance
-- ============================================================================

CREATE OR REPLACE VIEW vw_product_metrics AS
SELECT
    product_id,
    MAX(category)                                         AS category,
    MAX(brand)                                            AS brand,
    AVG(price)                                            AS avg_price,
    COUNT(*) FILTER (WHERE event_type = 'view')          AS n_views,
    COUNT(*) FILTER (WHERE event_type = 'cart')          AS n_cart,
    COUNT(*) FILTER (WHERE event_type = 'purchase')      AS n_purchase,
    COUNT(DISTINCT user_id)                              AS n_unique_users,
    SUM(price) FILTER (WHERE event_type = 'purchase')    AS revenue,
    COUNT(*) FILTER (WHERE event_type = 'purchase')::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE event_type = 'view'), 0) AS view_to_purchase_rate
FROM fact_events
GROUP BY product_id;

-- Top revenue brands --------------------------------------------------------
SELECT brand,
       SUM(price) FILTER (WHERE event_type = 'purchase') AS revenue,
       COUNT(*)  FILTER (WHERE event_type = 'purchase')  AS orders
FROM fact_events
GROUP BY brand
ORDER BY revenue DESC NULLS LAST
LIMIT 20;

-- Top revenue categories ----------------------------------------------------
SELECT category,
       SUM(price) FILTER (WHERE event_type = 'purchase') AS revenue,
       COUNT(DISTINCT user_id)                           AS buyers
FROM fact_events
GROUP BY category
ORDER BY revenue DESC NULLS LAST;
