"""01_filter_nppes.py

Reads the huge NPPES file in chunks, straight out of the zip, and keeps only
Georgia providers whose PRIMARY taxonomy is one of our anesthesia codes.
Decisions behind the code list and "primary only" are in METHODOLOGY_LOG.md.

Outputs:
  data/processed/ga_anesthesia_individuals.csv  (people: the headline count)
  data/processed/ga_anesthesia_orgs.csv         (group practices, counted separately)
"""
import zipfile

import pandas as pd

ZIP_PATH = "data/raw/NPPES_Data_Dissemination_September_2026_V2.zip"
CSV_NAME = "npidata_pfile_20050523-20260913.csv"
INDIVIDUALS_PATH = "data/processed/ga_anesthesia_individuals.csv"
ORGS_PATH = "data/processed/ga_anesthesia_orgs.csv"

# The taxonomy codes we count, with a readable label for each
CODES = {
    "207L00000X": "Anesthesiologist",
    "207LP3000X": "Pediatric Anesthesiologist",
    "367500000X": "CRNA",
    "367H00000X": "Anesthesiologist Assistant",
}

STATE_COL = "Provider Business Practice Location Address State Name"

# The columns we want to keep in the output
KEEP_COLS = [
    "NPI",
    "Entity Type Code",
    "Provider Last Name (Legal Name)",
    "Provider First Name",
    "Provider Credential Text",
    "Provider Organization Name (Legal Business Name)",
    "Provider First Line Business Practice Location Address",
    "Provider Business Practice Location Address City Name",
    STATE_COL,
    "Provider Business Practice Location Address Postal Code",
    "NPI Deactivation Date",
    "NPI Reactivation Date",
]

# A provider can list up to 15 taxonomy codes, each with a Y/N "primary" switch
TAX_COLS = [f"Healthcare Provider Taxonomy Code_{i}" for i in range(1, 16)]
SWITCH_COLS = [f"Healthcare Provider Primary Taxonomy Switch_{i}" for i in range(1, 16)]


def find_primary_taxonomy(df):
    """Return a column holding each row's primary taxonomy code ("" if none marked)."""
    primary = pd.Series("", index=df.index)
    for i in range(15):
        is_primary = df[SWITCH_COLS[i]] == "Y"
        primary[is_primary] = df.loc[is_primary, TAX_COLS[i]]
    return primary


kept_chunks = []
rows_read = 0
ga_rows = 0
ga_no_primary = 0

with zipfile.ZipFile(ZIP_PATH) as z:
    with z.open(CSV_NAME) as f:
        chunks = pd.read_csv(
            f,
            usecols=KEEP_COLS + TAX_COLS + SWITCH_COLS,
            dtype=str,  # read everything as text so ZIPs and NPIs keep leading zeros
            chunksize=200_000,
        )
        for chunk in chunks:
            rows_read += len(chunk)

            ga = chunk[chunk[STATE_COL] == "GA"].copy()
            ga_rows += len(ga)

            ga["Primary Taxonomy"] = find_primary_taxonomy(ga)
            ga_no_primary += (ga["Primary Taxonomy"] == "").sum()

            matches = ga[ga["Primary Taxonomy"].isin(CODES)].copy()
            matches["Provider Type"] = matches["Primary Taxonomy"].map(CODES)
            kept_chunks.append(matches[KEEP_COLS + ["Primary Taxonomy", "Provider Type"]])

            print(f"{rows_read:,} rows read")

result = pd.concat(kept_chunks)

# Entity Type Code: 1 = individual person, 2 = organization (e.g. group practice).
# Kept in separate files so organizations never inflate the count of people.
individuals = result[result["Entity Type Code"] == "1"]
orgs = result[result["Entity Type Code"] == "2"]
individuals.to_csv(INDIVIDUALS_PATH, index=False)
orgs.to_csv(ORGS_PATH, index=False)

print()
print(f"Total rows read:            {rows_read:,}")
print(f"Georgia rows:               {ga_rows:,}")
print(f"Georgia rows with no primary taxonomy marked: {ga_no_primary:,}")
print(f"Anesthesia providers kept:  {len(result):,}")
print(result["Provider Type"].value_counts())
print(result["Entity Type Code"].value_counts())
print(f"Saved {len(individuals):,} individuals to {INDIVIDUALS_PATH}")
print(f"Saved {len(orgs):,} organizations to {ORGS_PATH}")
