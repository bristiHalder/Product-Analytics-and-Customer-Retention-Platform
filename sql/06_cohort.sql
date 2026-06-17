-- ============================================================================
-- 06_cohort.sql  —  Monthly acquisition cohorts & retention matrix
-- ============================================================================

-- Each user's first activity month (acquisition cohort)
WITH first_activity AS (
    SELECT user_id,
           DATE_TRUNC('month', MIN(event_time)) AS cohort_month
    FROM fact_events
    GROUP BY user_id
),
-- Distinct active months per user
user_months AS (
    SELECT DISTINCT user_id,
           DATE_TRUNC('month', event_time) AS active_month
    FROM fact_events
),
joined AS (
    SELECT
        f.cohort_month,
        um.active_month,
        -- months since acquisition
        (EXTRACT(YEAR  FROM um.active_month) - EXTRACT(YEAR  FROM f.cohort_month)) * 12
      + (EXTRACT(MONTH FROM um.active_month) - EXTRACT(MONTH FROM f.cohort_month)) AS month_number,
        um.user_id
    FROM user_months um
    JOIN first_activity f USING (user_id)
)
SELECT
    cohort_month,
    month_number,
    COUNT(DISTINCT user_id) AS active_users
FROM joined
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number;

-- Day-N retention (D1 / D7 / D30 / D90) -------------------------------------
WITH signup AS (
    SELECT user_id, MIN(event_date) AS signup_date
    FROM fact_events
    GROUP BY user_id
),
activity AS (
    SELECT DISTINCT user_id, event_date FROM fact_events
)
SELECT
    COUNT(DISTINCT s.user_id)                                                          AS cohort_size,
    ROUND(100.0 * COUNT(DISTINCT a.user_id) FILTER (
        WHERE a.event_date = s.signup_date + 1)  / NULLIF(COUNT(DISTINCT s.user_id),0), 2) AS d1_retention,
    ROUND(100.0 * COUNT(DISTINCT a.user_id) FILTER (
        WHERE a.event_date = s.signup_date + 7)  / NULLIF(COUNT(DISTINCT s.user_id),0), 2) AS d7_retention,
    ROUND(100.0 * COUNT(DISTINCT a.user_id) FILTER (
        WHERE a.event_date = s.signup_date + 30) / NULLIF(COUNT(DISTINCT s.user_id),0), 2) AS d30_retention,
    ROUND(100.0 * COUNT(DISTINCT a.user_id) FILTER (
        WHERE a.event_date = s.signup_date + 90) / NULLIF(COUNT(DISTINCT s.user_id),0), 2) AS d90_retention
FROM signup s
LEFT JOIN activity a USING (user_id);
