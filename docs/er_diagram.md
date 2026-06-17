# Entity-Relationship Diagram

The warehouse uses a star schema centred on `fact_events`, with derived metric
tables materialised by the ETL.

```mermaid
erDiagram
    FACT_EVENTS {
        timestamp event_time
        varchar   event_type
        bigint    product_id FK
        bigint    category_id
        varchar   category_code
        varchar   category
        varchar   subcategory
        varchar   brand
        numeric   price
        bigint    user_id FK
        varchar   user_session FK
        date      event_date
        varchar   event_month
    }

    USER_METRICS {
        bigint  user_id PK
        timestamp first_seen
        timestamp last_seen
        int     n_orders
        numeric customer_lifetime_value
        numeric average_order_value
        numeric purchase_frequency
        numeric days_since_last_purchase
        int     is_repeat_purchaser
        int     is_churned
        varchar cohort_month
        varchar preferred_brand
        varchar preferred_category
    }

    SESSION_METRICS {
        varchar user_session PK
        bigint  user_id FK
        timestamp session_start
        timestamp session_end
        numeric session_duration_proxy
        int     cart_abandonment
        int     converted
        numeric revenue
    }

    PRODUCT_METRICS {
        bigint  product_id PK
        varchar category
        varchar brand
        numeric avg_price
        int     n_views
        int     n_purchase
        numeric revenue
        numeric view_to_purchase_rate
    }

    DAILY_ACTIVITY {
        date    activity_date PK
        int     active_users
        int     sessions
        int     events
        int     purchases
        numeric revenue
    }

    USER_METRICS    ||--o{ FACT_EVENTS : "generates"
    SESSION_METRICS ||--o{ FACT_EVENTS : "groups"
    PRODUCT_METRICS ||--o{ FACT_EVENTS : "aggregates"
    USER_METRICS    ||--o{ SESSION_METRICS : "owns"
```

## Grain

| Table | Grain | Key |
|-------|-------|-----|
| `fact_events` | one row per event | composite |
| `user_metrics` | one row per user | `user_id` |
| `session_metrics` | one row per session | `user_session` |
| `product_metrics` | one row per product | `product_id` |
| `daily_activity` | one row per day | `activity_date` |
