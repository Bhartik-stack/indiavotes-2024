"""
app.py - IndiaVotes 2024 dashboard
----------------------------------
A simple Streamlit dashboard over the 2024 Lok Sabha election results.

It reads the SQLite database built by build_db.py and uses the functions
in analytics.py (SQL + Pandas + NumPy) to show:
  * headline numbers (seats, turnout, leading party)
  * seats won per party
  * vote share per party
  * voter turnout (highest and lowest seats)
  * the closest contests
  * the leading party in each state

Run:  streamlit run app.py
"""

import os
import pandas as pd
import streamlit as st

import analytics as A

st.set_page_config(page_title="IndiaVotes 2024", page_icon="🗳️",
                   layout="wide")


def indian_commas(n):
    """Format a whole number with Indian grouping, e.g. 161500 -> 1,61,500."""
    n = int(round(n))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return sign + ",".join(parts) + "," + last3


def crore(n):
    """Express a number in crore, e.g. 646420869 -> '64.64 Cr'."""
    return f"{n / 1e7:,.2f} Cr"


# ---------------------------------------------------------------------------
# Load everything once and cache it.
# ---------------------------------------------------------------------------

@st.cache_data
def load_all():
    conn = A.get_connection()
    try:
        cand = A.load_candidates(conn)
    finally:
        conn.close()
    win = A.winners(cand)
    seats = A.seats_per_party(win)
    share = A.vote_share(cand)
    turn = A.turnout(win)
    leaders = A.state_leaders(win)
    summ = A.summary(win, seats, turn)
    return cand, win, seats, share, turn, leaders, summ


def group_top(df, label_col, value_col, n=10):
    """Keep the top n rows and roll the rest into a single 'Others' row."""
    top = df.head(n).copy()
    rest = df.iloc[n:]
    if len(rest) > 0:
        others = pd.DataFrame({label_col: ["Others"],
                               value_col: [rest[value_col].sum()]})
        top = pd.concat([top, others], ignore_index=True)
    return top


if not os.path.exists(A.DB_PATH):
    st.error("Database not found. Run `python load_data.py` and "
             "`python build_db.py` first.")
    st.stop()

cand, win, seats, share, turn, leaders, summ = load_all()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🗳️ IndiaVotes 2024")
st.caption("An analysis of the 2024 Lok Sabha general election results "
           "using SQL, Pandas and NumPy. Data source: Election Commission "
           "of India (results.eci.gov.in).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Seats analysed", f"{summ['total_seats']}")
c2.metric("Votes polled", crore(summ["total_votes"]))
c3.metric("Average turnout", f"{summ['avg_turnout_pct']} %")
c4.metric("Largest party",
          f"{summ['largest_party']} ({summ['largest_party_seats']})")

st.divider()

# ---------------------------------------------------------------------------
# Seats and vote share, side by side
# ---------------------------------------------------------------------------

left, right = st.columns(2)

with left:
    st.subheader("Seats won by party")
    s = group_top(seats.rename(columns={"win_party": "party"}),
                  "party", "seats", n=10)
    st.bar_chart(s.set_index("party")["seats"], horizontal=True)
    st.caption("Top 10 parties; remaining parties grouped as 'Others'.")

with right:
    st.subheader("Vote share by party (%)")
    vs = group_top(share.rename(columns={"abbr": "party"}),
                   "party", "vote_share_pct", n=10)
    st.bar_chart(vs.set_index("party")["vote_share_pct"], horizontal=True)
    st.caption("Share of total votes won by each party's candidates.")

st.divider()

# ---------------------------------------------------------------------------
# Turnout
# ---------------------------------------------------------------------------

st.subheader("Voter turnout")
t1, t2 = st.columns(2)
with t1:
    st.markdown("**Highest-turnout constituencies**")
    st.dataframe(turn.head(10)[["const_name", "state_name", "turnout_pct"]],
                 hide_index=True, use_container_width=True)
with t2:
    st.markdown("**Lowest-turnout constituencies**")
    st.dataframe(turn.tail(10).sort_values("turnout_pct")
                 [["const_name", "state_name", "turnout_pct"]],
                 hide_index=True, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Closest contests and state leaders
# ---------------------------------------------------------------------------

b1, b2 = st.columns(2)
with b1:
    st.subheader("Closest contests")
    cc = A.closest_contests(win, n=10).copy()
    cc["margin"] = cc["margin"].apply(indian_commas)
    st.dataframe(cc, hide_index=True, use_container_width=True)
    st.caption("Smallest victory margins, as a share of votes polled.")
with b2:
    st.subheader("Leading party by state")
    st.dataframe(leaders, hide_index=True, use_container_width=True)

st.divider()
st.caption("IndiaVotes 2024 · built with Streamlit, Pandas, NumPy and SQLite "
           "· data from the Election Commission of India.")
