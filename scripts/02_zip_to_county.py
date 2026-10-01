"""02_zip_to_county.py

Gives every Georgia anesthesia provider a county, using their practice ZIP code
and the HUD-USPS ZIP-COUNTY crosswalk. Each provider goes wholly to the county
that holds the largest share of their ZIP's business addresses (bus_ratio).
Decision and reasoning: METHODOLOGY_LOG.md.

Output: data/processed/ga_anesthesia_individuals_county.csv
"""
import pandas as pd

PROVIDERS_PATH = "data/processed/ga_anesthesia_individuals.csv"
CROSSWALK_PATH = "data/raw/ZIP-COUNTY_062026.xlsx"
OUT_PATH = "data/processed/ga_anesthesia_individuals_county.csv"

ZIP_COL = "Provider Business Practice Location Address Postal Code"

providers = pd.read_csv(PROVIDERS_PATH, dtype=str)
# NPPES ZIPs can be 9 digits (ZIP+4); the crosswalk uses the first 5
providers["zip5"] = providers[ZIP_COL].str[:5]

crosswalk = pd.read_excel(CROSSWALK_PATH, dtype=str)
crosswalk["bus_ratio"] = crosswalk["bus_ratio"].astype(float)
crosswalk["tot_ratio"] = crosswalk["tot_ratio"].astype(float)

# For each ZIP keep only the row (county) with the biggest business share.
# tot_ratio breaks ties, e.g. a ZIP with no business addresses at all.
best = (
    crosswalk.sort_values(["zip", "bus_ratio", "tot_ratio"], ascending=[True, False, False])
    .drop_duplicates(subset="zip", keep="first")
    .rename(columns={"zip": "zip5", "geoid": "county_fips", "bus_ratio": "zip_bus_share"})
)[["zip5", "county_fips", "zip_bus_share"]]

result = providers.merge(best, on="zip5", how="left")
result["county_method"] = "HUD largest business share"

# Atlanta post-office-only ZIPs missing from the HUD file; all are in
# Fulton County (13121). Decision logged in METHODOLOGY_LOG.md.
MANUAL_ZIPS = {"30365": "13121", "30335": "13121", "31193": "13121"}
manual = result["county_fips"].isna() & result["zip5"].isin(MANUAL_ZIPS)
result.loc[manual, "county_fips"] = result.loc[manual, "zip5"].map(MANUAL_ZIPS)
result.loc[manual, "county_method"] = "Manual: Atlanta PO-box ZIP -> Fulton"
print(f"Assigned by hand (PO-box ZIPs):    {manual.sum():,}")

# Sanity checks: nobody should be lost or duplicated by the merge
assert len(result) == len(providers), "merge changed the number of providers"

no_county = result["county_fips"].isna()
outside_ga = result["county_fips"].notna() & ~result["county_fips"].str.startswith("13", na=False)
split_zip = result["zip_bus_share"] < 1

result.to_csv(OUT_PATH, index=False)

print(f"Providers:                         {len(result):,}")
print(f"Assigned to a Georgia county:      {(~no_county & ~outside_ga).sum():,}")
print(f"ZIP not found in crosswalk:        {no_county.sum():,}")
print(f"ZIP's main county is outside GA:   {outside_ga.sum():,}")
print(f"In a ZIP split across counties:    {split_zip.sum():,}")
print(f"Counties with at least 1 provider: {result.loc[~outside_ga, 'county_fips'].nunique()}")
if no_county.any():
    print("\nZIPs not found:")
    print(result.loc[no_county, ["NPI", "zip5", "Provider Business Practice Location Address City Name"]].to_string(index=False))
if outside_ga.any():
    print("\nZIPs whose main county is outside Georgia:")
    print(result.loc[outside_ga, ["NPI", "zip5", "county_fips", "Provider Business Practice Location Address City Name"]].to_string(index=False))
