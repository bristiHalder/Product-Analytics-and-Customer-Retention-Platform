# Product Analytics & Customer Retention Platform

An end-to-end analytics platform that transforms raw eCommerce clickstream data into retention insights, funnel diagnostics, churn predictions, and experiment evaluations. Designed to support the decisions product and growth teams make daily - where to invest, what to ship, and which customers to protect.

Built on real-world behavioral event data, the platform covers the full analytics workflow: data ingestion, cleaning, feature engineering, SQL analysis, statistical testing, machine learning, and interactive reporting.

---

## Business Problem

Product and growth teams face three recurring challenges when working with behavioral event data:

1. **Funnel abandonment is invisible.** Companies track conversion rates but rarely quantify the revenue lost at each stage of the customer journey, making it difficult to prioritize where to invest.

2. **Retention and churn are measured reactively.** Most teams detect churn after users have already left. Connecting behavioral signals to churn risk - and translating that risk into revenue at stake - enables proactive intervention.

3. **Experiments lack business context.** A/B tests are often evaluated on statistical significance alone, without estimating the projected revenue impact of shipping or not shipping a change.

This platform addresses each gap with a structured analytics layer that combines SQL transformations, statistical methods, predictive modeling, and a decision-oriented reporting interface.

---

## Business Outcomes

| Outcome | Why It Matters |
|---------|---------------|
| Quantify revenue opportunity from funnel improvements | Translates drop-off percentages into estimated dollar impact, enabling prioritized investment |
| Estimate revenue at risk from customer churn | Connects each at-risk user to their lifetime value, making retention spend justifiable |
| Identify and protect high-value customer segments | A small cohort often drives disproportionate revenue - losing them is expensive |
| Evaluate experiments with projected business impact | Moves ship/no-ship decisions beyond p-values to estimated annual revenue effect |
| Connect user behaviors to retention outcomes | Identifies which actions predict long-term engagement, informing product roadmap priorities |
| Surface the highest-leverage growth opportunity | Synthesizes funnel, retention, and monetization signals into a single recommended focus area |

---

## Key Capabilities

| Capability | Business Question | What It Delivers |
|-----------|------------------|-----------------|
| **Funnel Analysis** | Where are we losing revenue? | Identifies where customers abandon the purchase journey and estimates the revenue opportunity from reducing drop-off |
| **Cohort Retention** | Are users returning? | Tracks Day-1 through Day-90 retention across acquisition cohorts and benchmarks against thresholds |
| **Customer Segmentation** | Which customers drive business value? | Groups users by behavioral value and quantifies each segment's revenue contribution and churn exposure |
| **Feature Adoption** | Which behaviors create retention? | Measures which user actions correlate most strongly with retention and revenue |
| **Churn Prediction** | Who is likely to leave and what is at risk? | Identifies at-risk users, estimates revenue at risk, and surfaces the top behavioral churn drivers |
| **A/B Testing** | Should we ship this change? | Evaluates experiments with statistical rigor and translates observed lift into projected business impact |
| **Root Cause Analysis** | Why did the metric move? | Detects anomalies in revenue and retention, ranks probable causes, and recommends actions |
| **Decision Support** | What should we do next? | Answers questions using a structured format: Observation → Evidence → Recommendation → Expected Impact |

---

## Project Highlights

- End-to-end analytics platform built on clickstream event data (view, cart, purchase).
- ETL pipeline with data cleaning, validation, and behavioral feature engineering.
- SQL analytics layer covering funnel conversion, cohort retention, segmentation, and revenue analysis.
- Churn prediction using Logistic Regression, Random Forest, and XGBoost with business-impact framing.
- Statistical experimentation framework with two-proportion z-tests, confidence intervals, and power analysis.
- Business Health Summary with explainable labels (Strong / Stable / Weak) instead of arbitrary scores.
- Interactive analytics application with 9 pages, each answering one executive question.
- Dockerized deployment with PostgreSQL and GitHub Actions CI/CD.

---

## Dataset

**[eCommerce Behavior Data from Multi Category Store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store)** (Kaggle)

| Column | Description |
|--------|-------------|
| `event_time` | UTC timestamp |
| `event_type` | `view`, `cart`, `remove_from_cart`, `purchase` |
| `product_id` | Product identifier |
| `category_id` / `category_code` | Category identifier and hierarchical code |
| `brand` | Brand name |
| `price` | Item price |
| `user_id` | User identifier |
| `user_session` | Session identifier |

A synthetic data generator (`scripts/generate_sample_data.py`) produces the identical schema with realistic behavioral archetypes, so the platform runs end-to-end without downloading the full dataset (~5 GB/month).

---

## Architecture

```
product-analytics-platform/
├── app/                        # Streamlit application (9 pages)
│   ├── streamlit_app.py
│   ├── components/             # Design system + shared helpers
│   │   ├── theme.py            # CSS, Plotly theme, reusable UI components
│   │   └── ui.py               # Data loading, filters, business impact estimators
│   └── pages/                  # Executive Overview → Decision Support
├── src/
│   ├── config.py               # Environment-driven settings
│   ├── db.py                   # SQLAlchemy engine + Parquet fallback
│   ├── etl/                    # load → clean → transform → pipeline
│   ├── analytics/              # metrics, funnel, cohort, segmentation,
│   │                           #   feature_adoption, ab_testing, root_cause
│   ├── ml/                     # churn_model (LogReg / RF / XGBoost)
│   └── ai/                     # decision support (rule-based + optional LLM)
├── sql/                        # 01_schema → 07_churn_features
├── scripts/                    # Data generator + run_etl.sh
├── tests/                      # pytest smoke + unit tests
├── docs/                       # Architecture & ER diagrams
├── Dockerfile · docker-compose.yml
├── .github/workflows/ci.yml
└── requirements.txt
```

See [docs/architecture.md](docs/architecture.md) and [docs/er_diagram.md](docs/er_diagram.md) for detailed diagrams.

---

## Data Pipeline

### Cleaning (`src/etl/clean.py`)

- Parses timestamps to UTC; drops rows missing user, product, event type, or timestamp.
- Fills categorical nulls (`brand`, `category_code`, `user_session`) with explicit sentinels.
- Coerces `price` to non-negative floats.
- Splits `category_code` into `category` and `subcategory`.
- Restricts to the canonical event vocabulary and deduplicates events.
- Outputs a data-quality report (rows dropped, percentage dropped, nulls filled).

### Feature Engineering (`src/etl/transform.py`)

Raw events are mapped to the product funnel (**View → Cart → Purchase → Repeat Purchase**) and enriched with derived metrics:

`days_since_last_purchase` · `purchase_frequency` · `customer_lifetime_value` · `average_order_value` · `session_duration_proxy` · `cart_abandonment` · `view_to_cart_rate` · `cart_to_purchase_rate` · `is_churned` · `cohort_month`

---

## SQL Analytics

Warehouse-native SQL in `sql/`:

| File | Purpose |
|------|---------|
| `01_schema.sql` | Star-schema DDL with indexes |
| `02_user_metrics.sql` | DAU / WAU / MAU, ARPU, per-user CLV |
| `03_session_metrics.sql` | Session engagement and cart abandonment rates |
| `04_product_metrics.sql` | Product, brand, and category performance |
| `05_funnel.sql` | View → Cart → Purchase → Repeat conversion rates |
| `06_cohort.sql` | Monthly acquisition cohorts with D1 / D7 / D30 / D90 retention |
| `07_churn_features.sql` | Churn feature engineering and churn-by-cohort analysis |

---

## Statistical Methods

- **Two-proportion z-test** and **confidence intervals** for A/B experiment evaluation.
- **Power analysis and sample-size planning** to determine required experiment duration before launch.
- **Correlation analysis** to rank behavioral drivers of retention, revenue, and churn.
- **Cohort retention matrices** with Day-N retention benchmarking against industry thresholds.

Libraries: `scipy`, `statsmodels` (`NormalIndPower`).

---

## Machine Learning

### Churn Prediction (`src/ml/churn_model.py`)

**Business context:** Churn (30+ days of inactivity) is the primary risk to recurring revenue. The platform identifies which users are likely to churn, how much revenue is at stake, and which behavioral patterns drive disengagement.

**Approach:** Three models trained and compared on ROC-AUC:

| Model | Details |
|-------|---------|
| Logistic Regression | Scaled features, class-balanced, interpretable coefficients |
| Random Forest | 200 trees, max depth 8, class-balanced |
| XGBoost | 300 estimators, learning rate 0.05, scale-aware weighting |

**Outputs:**
- Per-user churn probability scores for targeted outreach
- Ranked feature importance to identify top churn drivers
- ROC curves with AUC comparison and confusion matrix
- Best model auto-selected by AUC

**Business application:** Predictions are surfaced as revenue at risk - each at-risk user is connected to their CLV - and the top churn drivers are translated into specific retention recommendations.

---

## Dashboard

Every page answers one business question. The focus is on decisions and business impact, not visualizations.

| Page | Question It Answers | Action It Enables |
|------|--------------------|--------------------|
| **Executive Overview** | What should leadership focus on? | Surfaces a Business Health Summary (Growth / Retention / Revenue / Risk) and the highest-leverage opportunity with estimated revenue impact |
| **Funnel Analysis** | Where are we losing revenue? | Identifies where customers abandon the journey and estimates the revenue recoverable from reducing drop-off |
| **Cohort Analysis** | Are users returning? | Assesses retention health across acquisition cohorts with benchmark comparisons to flag weak habit loops |
| **User Segmentation** | Which customers drive business value? | Quantifies revenue concentration by segment and highlights at-risk high-value customers needing retention investment |
| **Feature Adoption** | Which behaviors create retention and revenue? | Identifies the highest-value user action and its correlation to long-term engagement and monetization |
| **Churn Prediction** | Who is likely to leave and what is at risk? | Surfaces users at risk, revenue at risk, top churn drivers, and recommended retention actions |
| **A/B Testing Lab** | Should we ship this change? | Delivers a Ship / Don't Ship / Need More Data recommendation with confidence level and projected annual impact |
| **Root Cause Analysis** | Why did the metric move? | Detects anomalies and presents ranked probable causes with estimated impact and recommended actions |
| **Decision Support** | What should we do next? | Returns structured answers: Observation → Evidence → Recommendation → Expected Impact |

Sidebar filters: date range, category, brand, minimum user revenue.

---

## Results & Insights

Findings from the platform (using synthetic data with realistic behavioral archetypes):

- **Revenue opportunity identified:** The largest funnel drop-off stage was quantified in dollar terms - estimating the revenue recoverable from a 10% reduction in abandonment at the weakest transition.
- **Retention gap surfaced:** Cohort analysis revealed weak Day-30 retention, indicating that users engage initially but fail to form a habit loop - a signal to invest in onboarding and lifecycle messaging.
- **High-value customers isolated:** A small customer segment drives a disproportionate share of total revenue, making retention of this group the highest-ROI investment.
- **Churn drivers identified:** Behavioral patterns most strongly associated with churn (low session frequency, no repeat purchase) were ranked, enabling targeted retention strategies instead of blanket campaigns.
- **Experiment decisions contextualized:** The A/B testing framework produces Ship / Don't Ship / Need More Data recommendations with projected annual revenue impact, not just statistical outputs.
- **At-risk revenue quantified:** Churn prediction connects each at-risk user to their lifetime value, prioritizing win-back outreach by business impact rather than probability alone.

---

## Deployment

| Method | Details |
|--------|---------|
| **Docker** | Application image on port `8501` |
| **docker-compose** | PostgreSQL + application provisioned together |
| **GitHub Actions** | CI pipeline: lint → ETL → tests → Docker build |
| **Cloud** | Deployable to Cloud Run, ECS, Render, Fly.io, or Streamlit Community Cloud |

### Quickstart

```bash
# Local (offline, no database required)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m scripts.generate_sample_data --users 5000 --days 120
python -m src.etl.pipeline
streamlit run app/streamlit_app.py
```

```bash
# Docker Compose (with PostgreSQL)
cp .env.example .env
docker compose up --build
docker compose exec app python -m scripts.generate_sample_data
docker compose exec app python -m src.etl.pipeline
# → http://localhost:8501
```

To use the Kaggle dataset, download a monthly CSV to `data/raw/ecommerce_events.csv` and run the ETL:

```bash
python -m src.etl.pipeline --nrows 2000000
```

---

## Tech Stack

`Python` · `PostgreSQL` · `Pandas` · `NumPy` · `SciPy` · `Statsmodels` · `scikit-learn` · `XGBoost` · `Streamlit` · `Plotly` · `SQLAlchemy` · `Docker` · `GitHub Actions`

---

## Skills Demonstrated

- Product Analytics
- Funnel Analysis
- Cohort Analysis
- Customer Segmentation
- Churn Prediction
- A/B Testing & Experimentation
- Statistical Inference
- SQL Analytics
- Data Engineering (ETL)
- Machine Learning
- Dashboard Development
- Docker & CI/CD

---

## Testing

```bash
pytest -q
```

GitHub Actions (`.github/workflows/ci.yml`) runs linting, generates sample data, executes the ETL in offline mode, runs the test suite, and builds the Docker image on every push and pull request.
