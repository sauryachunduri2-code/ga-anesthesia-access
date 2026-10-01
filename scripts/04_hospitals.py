"""04_hospitals.py

Finds Georgia hospitals that still perform surgery and that deliver babies,
using the CMS Provider of Services (POS) file, then checks the baby-delivery
list against the Georgia DCH map of OB counties.
Decisions behind the rules are in METHODOLOGY_LOG.md.

Outputs:
  data/processed/ga_hospitals.csv           (one row per active GA hospital)
  data/processed/county_hospital_flags.csv  (one row per GA county, all 159)
  data/processed/ob_source_mismatches.csv   (counties where CMS and DCH disagree)
"""
import pandas as pd

POS_PATH = "data/raw/Hospital_and_other.DATA.Q2_2026.csv"
POP_PATH = "data/raw/co-est2025-alldata.csv"
HOSPITALS_OUT = "data/processed/ga_hospitals.csv"
COUNTY_OUT = "data/processed/county_hospital_flags.csv"
MISMATCH_OUT = "data/processed/ob_source_mismatches.csv"

# POS hospital subtypes (PRVDR_CTGRY_SBTYP_CD) we care about
SUBTYPES = {
    "01": "Short-term general",
    "11": "Critical Access Hospital",
    "28": "Rural Emergency Hospital",
}

# POS service codes: 0 = not provided, 1 = by own staff,
# 2 = under arrangement, 3 = both. Anything 1-3 means "provided".
PROVIDED = ["1", "2", "3"]

# Counties shaded on Georgia DCH / SORH "Georgia Counties Offering CON-authorized
# Obstetrical (OB) Services", updated September 2025. Typed by hand from the map
# (data/raw/ga_dch_ob_counties_sept2025.pdf): 32 urban + 19 rural + 3 CAH = 54.
DCH_OB_COUNTIES = [
    # urban counties with OB
    "Bartow", "Bibb", "Bulloch", "Carroll", "Chatham", "Cherokee", "Clarke",
    "Clayton", "Cobb", "Coweta", "DeKalb", "Dougherty", "Douglas", "Fayette",
    "Floyd", "Forsyth", "Fulton", "Glynn", "Gordon", "Gwinnett", "Hall",
    "Henry", "Houston", "Lowndes", "Muscogee", "Newton", "Richmond",
    "Rockdale", "Spalding", "Troup", "Walton", "Whitfield",
    # rural counties with OB
    "Baldwin", "Camden", "Coffee", "Colquitt", "Crisp", "Decatur", "Franklin",
    "Grady", "Habersham", "Laurens", "Pickens", "Sumter", "Thomas", "Tift",
    "Toombs", "Union", "Upson", "Ware", "Wayne",
    # counties with a Critical Access Hospital offering OB
    "Bacon", "Liberty", "Wilkes",
]

# --- Hospitals -------------------------------------------------------------
pos = pd.read_csv(POS_PATH, dtype=str, encoding="latin-1")

hospitals = pos[
    (pos["STATE_CD"] == "GA")
    & (pos["PRVDR_CTGRY_CD"] == "01")          # 01 = hospital
    & (pos["PGM_TRMNTN_CD"] == "00")           # 00 = still active in Medicare
    & (pos["PRVDR_CTGRY_SBTYP_CD"].isin(SUBTYPES))
].copy()

hospitals["county_fips"] = hospitals["FIPS_STATE_CD"] + hospitals["FIPS_CNTY_CD"]
hospitals["hospital_type"] = hospitals["PRVDR_CTGRY_SBTYP_CD"].map(SUBTYPES)
hospitals["performs_surgery"] = hospitals["IP_SRGCL_SRVC_CD"].isin(PROVIDED)
hospitals["delivers_babies"] = hospitals["OB_SRVC_CD"].isin(PROVIDED)

# A Rural Emergency Hospital has no inpatient care, so it never counts
is_reh = hospitals["hospital_type"] == "Rural Emergency Hospital"
hospitals.loc[is_reh, ["performs_surgery", "delivers_babies"]] = False

hospitals = hospitals.rename(columns={
    "PRVDR_NUM": "ccn",
    "FAC_NAME": "name",
    "ST_ADR": "address",
    "CITY_NAME": "city",
    "ZIP_CD": "zip",
    "CRTFD_BED_CNT": "beds",
    "CBSA_URBN_RRL_IND": "urban_rural",
})
keep = ["ccn", "name", "address", "city", "zip", "county_fips", "hospital_type",
        "beds", "urban_rural", "performs_surgery", "delivers_babies"]
hospitals = hospitals[keep].sort_values(["county_fips", "name"])
hospitals.to_csv(HOSPITALS_OUT, index=False)

# --- Counties --------------------------------------------------------------
pop = pd.read_csv(POP_PATH, dtype=str, encoding="latin-1")
counties = pop[(pop["STATE"] == "13") & (pop["SUMLEV"] == "050")].copy()  # 050 = county
counties["county_fips"] = counties["STATE"] + counties["COUNTY"]
counties["county"] = counties["CTYNAME"].str.replace(" County", "", regex=False)
counties = counties[["county_fips", "county"]]

# Count hospitals of each kind in every county
per_county = hospitals.groupby("county_fips").agg(
    hospitals=("ccn", "count"),
    surgical_hospitals=("performs_surgery", "sum"),
    cms_ob_hospitals=("delivers_babies", "sum"),
    critical_access_hospitals=("hospital_type", lambda t: (t == "Critical Access Hospital").sum()),
    rural_emergency_hospitals=("hospital_type", lambda t: (t == "Rural Emergency Hospital").sum()),
).reset_index()

# Left merge keeps all 159 counties, even ones with no hospital at all
county_flags = counties.merge(per_county, on="county_fips", how="left")
count_cols = ["hospitals", "surgical_hospitals", "cms_ob_hospitals",
              "critical_access_hospitals", "rural_emergency_hospitals"]
county_flags[count_cols] = county_flags[count_cols].fillna(0).astype(int)
county_flags["dch_ob_county"] = county_flags["county"].isin(DCH_OB_COUNTIES)
# Official "delivers babies" answer for the map = DCH (CMS OB codes proved stale;
# see METHODOLOGY_LOG.md). The CMS count stays in the file for comparison.
county_flags["has_ob_services"] = county_flags["dch_ob_county"]
county_flags.to_csv(COUNTY_OUT, index=False)

# --- Check CMS OB flag against DCH map --------------------------------------
cms_ob = county_flags["cms_ob_hospitals"] > 0
mismatches = county_flags[cms_ob != county_flags["dch_ob_county"]].copy()
mismatches["cms_says_ob"] = mismatches["cms_ob_hospitals"] > 0
mismatches[["county_fips", "county", "cms_ob_hospitals", "cms_says_ob", "dch_ob_county"]].to_csv(
    MISMATCH_OUT, index=False)

# Every DCH county name must match a real county name, or the check is broken
unknown = set(DCH_OB_COUNTIES) - set(counties["county"])
if unknown:
    raise ValueError(f"DCH county names not found in Census list: {unknown}")

print(f"Active GA hospitals kept: {len(hospitals)}")
print(hospitals["hospital_type"].value_counts().to_string())
print(f"Perform surgery: {hospitals['performs_surgery'].sum()}")
print(f"Deliver babies:  {hospitals['delivers_babies'].sum()}")
print()
print(f"Counties: {len(county_flags)}")
print(f"Counties with a surgical hospital: {(county_flags['surgical_hospitals'] > 0).sum()}")
print(f"Counties with OB (CMS):            {cms_ob.sum()}")
print(f"Counties with OB (DCH Sept 2025, used for map): {county_flags['has_ob_services'].sum()}")
print(f"Counties where they disagree:      {len(mismatches)}")
print(mismatches[["county", "cms_ob_hospitals", "dch_ob_county"]].to_string(index=False))
