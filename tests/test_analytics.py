"""
Tests for the IndiaVotes analytics.

They check both that the code is internally consistent (seats add up,
percentages are in range) and that it reproduces well-known facts about
the real 2024 Lok Sabha result (the BJP was the largest party; the
Congress was second).

Run:  pytest -q      (run load_data.py and build_db.py first)
"""

import os
import pytest

import analytics as A

pytestmark = pytest.mark.skipif(
    not os.path.exists(A.DB_PATH),
    reason="elections.db not built; run load_data.py then build_db.py")


@pytest.fixture(scope="module")
def data():
    conn = A.get_connection()
    try:
        cand = A.load_candidates(conn)
    finally:
        conn.close()
    win = A.winners(cand)
    return cand, win


def test_one_winner_per_constituency(data):
    cand, win = data
    assert len(win) == cand["const_id"].nunique()


def test_seats_add_up(data):
    _, win = data
    seats = A.seats_per_party(win)
    assert seats["seats"].sum() == len(win)


def test_bjp_is_largest_party(data):
    _, win = data
    seats = A.seats_per_party(win)
    assert seats.iloc[0]["win_party"] == "BJP"
    # BJP won 240 seats in 2024; one (Surat) was unopposed and carries no
    # vote row, so a votes-based dataset shows 239.
    assert seats.iloc[0]["seats"] >= 239


def test_congress_is_second(data):
    _, win = data
    seats = A.seats_per_party(win)
    assert seats.iloc[1]["win_party"] == "INC"


def test_vote_share_sums_to_100(data):
    cand, _ = data
    share = A.vote_share(cand)
    assert abs(share["vote_share_pct"].sum() - 100.0) < 0.5


def test_turnout_in_range(data):
    _, win = data
    turn = A.turnout(win)
    assert turn["turnout_pct"].between(0, 100).all()


def test_margins_non_negative(data):
    _, win = data
    assert (win["margin"] >= 0).all()
