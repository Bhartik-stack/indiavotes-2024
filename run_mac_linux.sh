#!/usr/bin/env bash
# IndiaVotes 2024 - one-click start for macOS / Linux
# Installs the packages, prepares the database, and opens the dashboard.
set -e

echo "Installing required Python packages..."
pip install -r requirements.txt

echo "Preparing the data and database..."
python load_data.py
python build_db.py

echo "Starting the dashboard (your browser will open)..."
python3 -m streamlit run app.py
