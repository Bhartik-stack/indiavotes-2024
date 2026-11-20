"""
load_data.py
------------
Reads the real 2024 Lok Sabha (Indian general election) results and
reshapes them into four clean tables for the project.

Source data: constituency-wise, candidate-level results of the 2024
Lok Sabha general election, originally published by the Election
Commission of India (results.eci.gov.in) and obtained here as a
collated spreadsheet (data/source_2024.xlsx, sheet "raw dataset").
Election results are public, factual government records.

Output: four CSV files in the data/ folder
    states.csv          one row per state / union territory
    parties.csv         one row per party
    constituencies.csv  one row per parliamentary constituency (seat)
    candidates.csv      one row per contesting candidate

NOTA ("None of the Above") rows are kept out of the candidate table,
because NOTA is not a party or a candidate; the votes polled figure
used for turnout still comes from the official constituency total,
which includes NOTA.

Run:  python load_data.py
"""

import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE, "data")
SOURCE = os.path.join(DATA_DIR, "source_2024.xlsx")

# Full names for the larger parties so the report and dashboard read well.
# Any party not listed keeps its official abbreviation as its name.
PARTY_FULL = {
    "BJP": "Bharatiya Janata Party",
    "INC": "Indian National Congress",
    "SP": "Samajwadi Party",
    "AITC": "All India Trinamool Congress",
    "DMK": "Dravida Munnetra Kazhagam",
    "TDP": "Telugu Desam Party",
    "JD(U)": "Janata Dal (United)",
    "SHSUBT": "Shiv Sena (Uddhav Balasaheb Thackeray)",
    "NCPSP": "Nationalist Congress Party (Sharadchandra Pawar)",
    "SHS": "Shiv Sena",
    "LJPRV": "Lok Janshakti Party (Ram Vilas)",
    "YSRCP": "Yuvajana Sramika Rythu Congress Party",
    "RJD": "Rashtriya Janata Dal",
    "CPI(M)": "Communist Party of India (Marxist)",
    "IND": "Independent",
    "AAP": "Aam Aadmi Party",
    "JMM": "Jharkhand Mukti Morcha",
    "BSP": "Bahujan Samaj Party",
}


def load_raw() -> pd.DataFrame:
    df = pd.read_excel(SOURCE, sheet_name="raw dataset")
    df = df.rename(columns={
        "State Name": "state",
        "PC Name": "pc",
        "Candidate Name": "cand",
        "Party Name": "party",
        "Votes Secured - Total": "votes",
        "Total Electors": "electors",
        "Total Votes Polled In The Constituency": "polled",
    })
    df = df[["state", "pc", "cand", "party", "votes", "electors", "polled"]]
    df = df.dropna(subset=["state", "pc", "party", "votes"])
    df["votes"] = df["votes"].astype(int)
    df["electors"] = df["electors"].astype(int)
    df["polled"] = df["polled"].astype(int)
    return df


def main():
    raw = load_raw()

    # ---- states -----------------------------------------------------------
    state_names = sorted(raw["state"].unique())
    state_id = {s: i + 1 for i, s in enumerate(state_names)}

    # ---- constituencies (one per state + PC pair) -------------------------
    const_groups = (raw.groupby(["state", "pc"])
                        .agg(total_electors=("electors", "max"),
                             total_polled=("polled", "max"))
                        .reset_index())
    const_groups["const_id"] = range(1, len(const_groups) + 1)
    const_key = {(r["state"], r["pc"]): r["const_id"]
                 for _, r in const_groups.iterrows()}

    constituencies = pd.DataFrame({
        "const_id": const_groups["const_id"],
        "const_name": const_groups["pc"],
        "state_id": const_groups["state"].map(state_id),
        "total_electors": const_groups["total_electors"],
        "total_polled": const_groups["total_polled"],
    })

    states = pd.DataFrame({
        "state_id": [state_id[s] for s in state_names],
        "state_name": state_names,
        "num_seats": [int((const_groups["state"] == s).sum())
                      for s in state_names],
    })

    # ---- parties (exclude NOTA) ------------------------------------------
    party_rows = raw[raw["party"] != "NOTA"].copy()
    party_names = sorted(party_rows["party"].unique())
    party_id = {p: i + 1 for i, p in enumerate(party_names)}
    parties = pd.DataFrame({
        "party_id": [party_id[p] for p in party_names],
        "party_name": [PARTY_FULL.get(p, p) for p in party_names],
        "abbr": party_names,
    })

    # ---- candidates -------------------------------------------------------
    party_rows["const_id"] = [const_key[(r.state, r.pc)]
                              for r in party_rows.itertuples()]
    party_rows["party_id"] = party_rows["party"].map(party_id)
    candidates = pd.DataFrame({
        "cand_id": range(1, len(party_rows) + 1),
        "cand_name": party_rows["cand"].values,
        "party_id": party_rows["party_id"].astype(int).values,
        "const_id": party_rows["const_id"].astype(int).values,
        "votes": party_rows["votes"].astype(int).values,
    })

    states.to_csv(os.path.join(DATA_DIR, "states.csv"), index=False)
    parties.to_csv(os.path.join(DATA_DIR, "parties.csv"), index=False)
    constituencies.to_csv(os.path.join(DATA_DIR, "constituencies.csv"),
                          index=False)
    candidates.to_csv(os.path.join(DATA_DIR, "candidates.csv"), index=False)

    print("Real 2024 Lok Sabha dataset reshaped into:", DATA_DIR)
    print(f"  States / UTs  : {len(states)}")
    print(f"  Parties       : {len(parties)}")
    print(f"  Constituencies: {len(constituencies)}")
    print(f"  Candidates    : {len(candidates)}")


if __name__ == "__main__":
    main()
