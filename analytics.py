"""
analytics.py
------------
All the analysis for the project. This is where SQL, Pandas and NumPy meet:

  * SQL   - we read the tables from the SQLite database with queries that
            join candidates to their party, constituency and state.
  * Pandas- we clean and group the data (group by party, by state, etc.).
  * NumPy - we do the arithmetic (vote share %, turnout %, margins, and
            a z-score to flag unusually high or low turnout).

Every function returns a pandas DataFrame or a plain number, so the
Streamlit dashboard (app.py) and the tests can both use them.
"""

import os
import sqlite3
import numpy as np
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "elections.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


# ---------------------------------------------------------------------------
# Base table: every candidate with party, constituency and state attached.
# Built with a single SQL query (three joins).
# ---------------------------------------------------------------------------

def load_candidates(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT  c.cand_id,
                c.cand_name,
                c.votes,
                p.party_id,
                p.party_name,
                p.abbr,
                con.const_id,
                con.const_name,
                con.total_electors,
                con.total_polled,
                s.state_id,
                s.state_name
        FROM candidates       AS c
        JOIN parties          AS p   ON c.party_id = p.party_id
        JOIN constituencies   AS con ON c.const_id = con.const_id
        JOIN states           AS s   ON con.state_id = s.state_id
    """
    return pd.read_sql_query(query, conn)


# ---------------------------------------------------------------------------
# Winners: the top candidate in each constituency, plus the victory margin.
# ---------------------------------------------------------------------------

def winners(cand: pd.DataFrame) -> pd.DataFrame:
    """
    Return one row per constituency: the winning candidate, the runner-up,
    the winning party, votes, and the victory margin (winner - runner-up),
    both as an absolute number and as a percentage of votes polled.
    """
    rows = []
    for const_id, grp in cand.groupby("const_id"):
        grp = grp.sort_values("votes", ascending=False)
        top = grp.iloc[0]
        runner_votes = int(grp.iloc[1]["votes"]) if len(grp) > 1 else 0
        # Official total votes polled in the seat (includes NOTA).
        votes_polled = int(top["total_polled"])
        margin = int(top["votes"]) - runner_votes
        # NumPy is used here for the safe division into a percentage.
        margin_pct = float(np.divide(margin, votes_polled) * 100)
        rows.append({
            "const_id": const_id,
            "const_name": top["const_name"],
            "state_name": top["state_name"],
            "winner": top["cand_name"],
            "win_party": top["abbr"],
            "win_votes": int(top["votes"]),
            "runner_up_votes": runner_votes,
            "votes_polled": votes_polled,
            "total_electors": int(top["total_electors"]),
            "margin": margin,
            "margin_pct": round(margin_pct, 2),
        })
    return pd.DataFrame(rows).sort_values("const_id").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Seats won per party (the headline result).
# ---------------------------------------------------------------------------

def seats_per_party(win: pd.DataFrame) -> pd.DataFrame:
    out = (win.groupby("win_party")
              .size()
              .reset_index(name="seats")
              .sort_values("seats", ascending=False)
              .reset_index(drop=True))
    out["share_of_seats_pct"] = (out["seats"] / out["seats"].sum() * 100).round(2)
    return out


# ---------------------------------------------------------------------------
# Vote share per party (over all candidates, not just winners).
# ---------------------------------------------------------------------------

def vote_share(cand: pd.DataFrame) -> pd.DataFrame:
    total = cand["votes"].sum()
    out = (cand.groupby("abbr")["votes"]
               .sum()
               .reset_index(name="total_votes")
               .sort_values("total_votes", ascending=False)
               .reset_index(drop=True))
    out["vote_share_pct"] = (out["total_votes"] / total * 100).round(2)
    return out


# ---------------------------------------------------------------------------
# Turnout per constituency, with a z-score to flag unusual turnout.
# ---------------------------------------------------------------------------

def turnout(win: pd.DataFrame) -> pd.DataFrame:
    out = win[["const_name", "state_name", "votes_polled",
               "total_electors"]].copy()
    out["turnout_pct"] = (out["votes_polled"] / out["total_electors"]
                          * 100).round(2)
    # NumPy: z-score = how many standard deviations from the mean turnout.
    mean = np.mean(out["turnout_pct"])
    std = np.std(out["turnout_pct"])
    out["turnout_z"] = ((out["turnout_pct"] - mean) / std).round(2)
    return out.sort_values("turnout_pct", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# State-wise leading party (which party won the most seats in each state).
# ---------------------------------------------------------------------------

def state_leaders(win: pd.DataFrame) -> pd.DataFrame:
    by_state = (win.groupby(["state_name", "win_party"])
                   .size()
                   .reset_index(name="seats"))
    # For each state keep the party with the most seats.
    idx = by_state.groupby("state_name")["seats"].idxmax()
    out = by_state.loc[idx].sort_values("state_name").reset_index(drop=True)
    return out.rename(columns={"win_party": "leading_party"})


# ---------------------------------------------------------------------------
# Closest and safest contests.
# ---------------------------------------------------------------------------

def closest_contests(win: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cols = ["const_name", "state_name", "win_party", "margin", "margin_pct"]
    return win.sort_values("margin_pct").head(n)[cols].reset_index(drop=True)


def safest_contests(win: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cols = ["const_name", "state_name", "win_party", "margin", "margin_pct"]
    return (win.sort_values("margin_pct", ascending=False)
               .head(n)[cols].reset_index(drop=True))


# ---------------------------------------------------------------------------
# A single headline summary used on the dashboard.
# ---------------------------------------------------------------------------

def summary(win: pd.DataFrame, seats: pd.DataFrame,
            turn: pd.DataFrame) -> dict:
    return {
        "total_seats": int(len(win)),
        "total_votes": int(win["votes_polled"].sum()),
        "avg_turnout_pct": round(float(turn["turnout_pct"].mean()), 2),
        "largest_party": seats.iloc[0]["win_party"],
        "largest_party_seats": int(seats.iloc[0]["seats"]),
        "closest_seat": win.sort_values("margin_pct").iloc[0]["const_name"],
    }


if __name__ == "__main__":
    conn = get_connection()
    try:
        cand = load_candidates(conn)
    finally:
        conn.close()
    win = winners(cand)
    seats = seats_per_party(win)
    turn = turnout(win)
    print("Summary:", summary(win, seats, turn))
    print("\nSeats per party:\n", seats.to_string(index=False))
    print("\nVote share:\n", vote_share(cand).to_string(index=False))
