"""
build_db.py
-----------
Loads the four CSV files into a single SQLite database, elections.db,
with one table each: states, parties, constituencies, candidates.

This is the SQL part of the project: the data is stored in a real
relational database and later read back with SQL queries.

Run:  python build_db.py   (run load_data.py first)
"""

import os
import sqlite3
import pandas as pd

BASE = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE, "data")
DB_PATH = os.path.join(BASE, "elections.db")

SCHEMA = """
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS constituencies;
DROP TABLE IF EXISTS parties;
DROP TABLE IF EXISTS states;

CREATE TABLE states (
    state_id   INTEGER PRIMARY KEY,
    state_name TEXT NOT NULL,
    num_seats  INTEGER NOT NULL
);

CREATE TABLE parties (
    party_id   INTEGER PRIMARY KEY,
    party_name TEXT NOT NULL,
    abbr       TEXT NOT NULL
);

CREATE TABLE constituencies (
    const_id       INTEGER PRIMARY KEY,
    const_name     TEXT NOT NULL,
    state_id       INTEGER NOT NULL REFERENCES states(state_id),
    total_electors INTEGER NOT NULL,
    total_polled   INTEGER NOT NULL
);

CREATE TABLE candidates (
    cand_id   INTEGER PRIMARY KEY,
    cand_name TEXT NOT NULL,
    party_id  INTEGER NOT NULL REFERENCES parties(party_id),
    const_id  INTEGER NOT NULL REFERENCES constituencies(const_id),
    votes     INTEGER NOT NULL
);
"""


def build():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        for name in ("states", "parties", "constituencies", "candidates"):
            df = pd.read_csv(os.path.join(DATA_DIR, f"{name}.csv"))
            df.to_sql(name, conn, if_exists="append", index=False)
        conn.commit()
        n = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        print(f"Database built at {DB_PATH} with {n} candidate rows.")
    finally:
        conn.close()


if __name__ == "__main__":
    build()
