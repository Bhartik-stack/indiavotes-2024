@echo off
REM IndiaVotes 2024 - one-click start for Windows
REM Installs the packages, prepares the database, and opens the dashboard.

echo Installing required Python packages...
pip install -r requirements.txt

echo Preparing the data and database...
python load_data.py
python build_db.py

echo Starting the dashboard (your browser will open)...
python -m streamlit run app.py
pause
