"""05_secondary_locations.py

Builds the "also serves" layer: for each Georgia county, how many of our
Georgia anesthesia providers list a SECONDARY practice location there
(NPPES pl_pfile). This is never added to the headline count; it shows where
providers whose main address is elsewhere also work. See METHODOLOGY_LOG.md.

Output: data/processed/county_secondary_counts.csv
"""
import zipfile

import pandas as pd

ZIP_PATH = "data/raw/NPPES_Data_Dissemination_September_2026_V2.zip"
PL_NAME = "pl_pfile_20050523-20260913.csv"
PROVIDERS_PATH = "data/processed/ga_anesthesia_individuals_county.csv"
CROSSWALK_PATH = "data/raw/ZIP-COUNTY_062026.xlsx"
OUT_PATH = "data/processed/county_secondary_counts.csv"

STATE_COL = "Provider Secondary Practice Location Address - State Name"
ZIP_COL = "Provider Secondary Practice Location Address - Postal Code"

# Our providers and their primary county (from 02_zip_to_county.py)
providers = pd.read_csv(PROVIDERS_PATH, dtype=str)[["NPI", "county_fips"]]
providers = providers.rename(columns={"county_fips": "primary_county_fips"})

# Read the secondary-locations file straight from the zip (~120 MB, fits in memory)
with zipfile.ZipFile(ZIP_PATH) as z:
    with z.open(PL_NAME) as f:
        pl = pd.read_csv(f, dtype=str, usecols=["NPI", STATE_COL, ZIP_COL])

# Keep only our providers' secondary locations that are in Georgia
pl = pl[pl["NPI"].isin(providers["NPI"]) & (pl[STATE_COL] == "GA")].copy()
pl["zip5"] = pl[ZIP_COL].str[:5]

# Same ZIP -> county rule as 02_zip_to_county.py: largest business share wins
crosswalk = pd.read_excel(CROSSWALK_PATH, dtype=str)
crosswalk["bus_ratio"] = crosswalk["bus_ratio"].astype(float)
crosswalk["tot_ratio"] = crosswalk["tot_ratio"].astype(float)
best = (
    crosswalk.sort_values(["zip", "bus_ratio", "tot_ratio"], ascending=[True, False, False])
    .drop_duplicates(subset="zip", keep="first")
    .rename(columns={"zip": "zip5", "geoid": "county_fips"})
)[["zip5", "county_fips"]]

pl = pl.merge(best, on="zip5", how="left").merge(providers, on="NPI")
unmatched = pl["county_fips"].isna().sum()

# Only count a secondary location in a county that is NOT the provider's primary county,
# and count each provider at most once per county
pl = pl[pl["county_fips"].notna() & (pl["county_fips"] != pl["primary_county_fips"])]
pl = pl.drop_duplicates(subset=["NPI", "county_fips"])

counts = pl.groupby("county_fips")["NPI"].nunique().reset_index(name="also_serves_providers")
counts.to_csv(OUT_PATH, index=False)

print(f"Providers with a secondary GA location in another county: {pl['NPI'].nunique():,}")
print(f"Counties reached by secondary locations: {len(counts)}")
print(f"Secondary locations with ZIP not in crosswalk (skipped): {unmatched}")
