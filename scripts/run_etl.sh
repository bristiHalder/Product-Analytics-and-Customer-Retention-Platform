#!/usr/bin/env bash
# End-to-end local bootstrap: sample data → ETL → ready for the dashboard.
set -euo pipefail

echo "==> Generating synthetic sample data (skip if you have the Kaggle CSV)"
python -m scripts.generate_sample_data --users 5000 --days 120

echo "==> Running ETL pipeline"
python -m src.etl.pipeline

echo "==> Done. Launch the dashboard with:  streamlit run app/streamlit_app.py"
