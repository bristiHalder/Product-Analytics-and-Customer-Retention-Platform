-- ============================================================================
-- 01_schema.sql  —  Star-schema DDL for the Growth Analytics warehouse
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- Raw / fact event table -----------------------------------------------------
DROP TABLE IF EXISTS fact_events CASCADE;
CREATE TABLE fact_events (
    event_time     TIMESTAMP        NOT NULL,
    event_type     VARCHAR(20)      NOT NULL,
    product_id     BIGINT           NOT NULL,
    category_id    BIGINT,
    category_code  VARCHAR(120),
    category       VARCHAR(60),
    subcategory    VARCHAR(60),
    brand          VARCHAR(60),
    price          NUMERIC(12, 2),
    user_id        BIGINT           NOT NULL,
    user_session   VARCHAR(80),
    event_date     DATE,
    event_month    VARCHAR(7)
);

CREATE INDEX IF NOT EXISTS idx_events_user   ON fact_events (user_id);
CREATE INDEX IF NOT EXISTS idx_events_type   ON fact_events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_date   ON fact_events (event_date);
CREATE INDEX IF NOT EXISTS idx_events_brand  ON fact_events (brand);

-- Dimensional / metric tables (populated by the Python ETL) ------------------
DROP TABLE IF EXISTS user_metrics CASCADE;
CREATE TABLE user_metrics (
    user_id                  BIGINT PRIMARY KEY,
    first_seen               TIMESTAMP,
    last_seen                TIMESTAMP,
    total_events             INT,
    n_views                  INT,
    n_cart                   INT,
    n_purchase               INT,
    n_sessions               INT,
    n_products               INT,
    n_brands                 INT,
    n_categories             INT,
    customer_lifetime_value  NUMERIC(14, 2),
    average_order_value      NUMERIC(12, 2),
    n_orders                 INT,
    cohort_month             VARCHAR(7),
    signup_date              DATE,
    lifespan_days            NUMERIC(10, 2),
    days_since_last_purchase NUMERIC(10, 2),
    days_since_last_seen     NUMERIC(10, 2),
    purchase_frequency       NUMERIC(10, 4),
    is_repeat_purchaser      INT,
    reached_view             INT,
    reached_cart             INT,
    reached_purchase         INT,
    reached_repeat           INT,
    is_churned               INT,
    view_to_cart_rate        NUMERIC(10, 4),
    cart_to_purchase_rate    NUMERIC(10, 4),
    avg_session_events       NUMERIC(10, 4),
    preferred_brand          VARCHAR(60),
    preferred_category       VARCHAR(60)
);

DROP TABLE IF EXISTS session_metrics CASCADE;
CREATE TABLE session_metrics (
    user_session           VARCHAR(80) PRIMARY KEY,
    user_id                BIGINT,
    session_start          TIMESTAMP,
    session_end            TIMESTAMP,
    n_events               INT,
    n_views                INT,
    n_cart                 INT,
    n_purchase             INT,
    n_products             INT,
    revenue                NUMERIC(12, 2),
    session_duration_proxy NUMERIC(12, 2),
    cart_abandonment       INT,
    converted              INT,
    session_date           DATE
);

DROP TABLE IF EXISTS product_metrics CASCADE;
CREATE TABLE product_metrics (
    product_id             BIGINT PRIMARY KEY,
    category               VARCHAR(60),
    brand                  VARCHAR(60),
    avg_price              NUMERIC(12, 2),
    n_views                INT,
    n_cart                 INT,
    n_purchase             INT,
    n_unique_users         INT,
    revenue                NUMERIC(14, 2),
    view_to_purchase_rate  NUMERIC(10, 4)
);

DROP TABLE IF EXISTS daily_activity CASCADE;
CREATE TABLE daily_activity (
    activity_date  DATE PRIMARY KEY,
    active_users   INT,
    sessions       INT,
    events         INT,
    purchases      INT,
    revenue        NUMERIC(14, 2)
);
