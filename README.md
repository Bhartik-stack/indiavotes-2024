# IndiaVotes 2024

A small data-analytics project that analyses the **2024 Lok Sabha general
election** results using **SQL, Pandas and NumPy**, with a simple
**Streamlit** dashboard.

The project answers questions people actually ask about an election:
how many seats did each party win, what was their vote share, how high was
voter turnout, which contests were the closest, and which party led in each
state.

## What each part does

| Skill   | Where it is used |
|---------|------------------|
| **SQL** | The data is stored in a real SQLite database (`elections.db`). `queries.sql` and `analytics.py` read it with joins and `GROUP BY` aggregation. |
| **Pandas** | Cleaning the raw data, reshaping it into tidy tables, grouping by party and state. |
| **NumPy** | The calculations: vote-share %, turnout %, victory margins, and a z-score to flag unusual turnout. |

## How to run it

1. Install Python 3.10+.
2. From this folder:
   - **Windows:** double-click `run_windows.bat`
   - **macOS / Linux:** `bash run_mac_linux.sh`

   Or do it manually:
   ```
   pip install -r requirements.txt
   python load_data.py     # build the clean tables from the source data
   python build_db.py       # load them into the SQLite database
   streamlit run app.py     # open the dashboard
   ```

## Files

| File | Purpose |
|------|---------|
| `load_data.py` | Reads the source results and reshapes them into four tidy tables (states, parties, constituencies, candidates). |
| `build_db.py`  | Loads those tables into the `elections.db` SQLite database. |
| `analytics.py` | All the analysis functions (SQL + Pandas + NumPy). |
| `queries.sql`  | Example SQL queries that can be run directly against the database. |
| `app.py`       | The Streamlit dashboard. |
| `tests/`       | Automated tests (`pytest -q`). |
| `data/`        | The source data and the generated tidy tables. |

## Data source

The results are the real, publicly available 2024 Lok Sabha general-election
results published by the **Election Commission of India**
(`results.eci.gov.in`), obtained here as a collated spreadsheet. Election
results are factual public records. "None of the Above" (NOTA) is recorded
in the source and is excluded from the party and candidate analysis, while
the official votes-polled figure (which includes NOTA) is used for turnout.

> Note: the Surat constituency was won unopposed in 2024 and therefore has
> no polled-vote row, so a votes-based analysis shows 542 contested seats
> and 239 BJP seats (240 including Surat).

## Author

Bhartik Sharma — B.Tech (Mathematics and Computing), 5th Semester
Industrial Training in Data Analysis (NumPy, Pandas, SQL), SIT Institute, Pathankot (25 May – 9 July 2026)
