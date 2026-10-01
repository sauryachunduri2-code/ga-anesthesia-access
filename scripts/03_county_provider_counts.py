"""03_county_provider_counts.py

Counts anesthesia providers in each of Georgia's 159 counties, by provider type,
and turns the counts into rates per 100,000 residents (Census Vintage 2025).

Output: data/processed/county_provider_counts.csv
"""
import pandas as pd

PROVIDERS_PATH = "data/processed/ga_anesthesia_individuals_county.csv"
POP_PATH = "data/raw/co-est2025-alldata.csv"
OUT_PATH = "data/processed/county_provider_counts.csv"

# Short column names for each provider type
TYPE_COLS = {
    "Anesthesiologist": "anesthesiologists",
    "Pediatric Anesthesiologist": "pediatric_anesthesiologists",
    "CRNA": "crnas",
    "Anesthesiologist Assistant": "anesthesiologist_assistants",
}

providers = pd.read_csv(PROVIDERS_PATH, dtype=str)

# One row per county, one column per provider type, each cell a count
counts = pd.crosstab(providers["county_fips"], providers["Provider Type"])
counts = counts.rename(columns=TYPE_COLS).reset_index()

# All 159 GA counties with their population and births (Census Vintage 2025)
pop = pd.read_csv(POP_PATH, dtype=str, encoding="latin-1")
counties = pop[(pop["STATE"] == "13") & (pop["SUMLEV"] == "050")].copy()
counties["county_fips"] = counties["STATE"] + counties["COUNTY"]
counties["county"] = counties["CTYNAME"].str.replace(" County", "", regex=False)
counties["population_2025"] = counties["POPESTIMATE2025"].astype(int)
counties["births_2025"] = counties["BIRTHS2025"].astype(int)
counties = counties[["county_fips", "county", "population_2025", "births_2025"]]

# Left merge keeps counties with zero providers; fill their counts with 0
table = counties.merge(counts, on="county_fips", how="left")
type_cols = list(TYPE_COLS.values())
table[type_cols] = table[type_cols].fillna(0).astype(int)

table["total_providers"] = table[type_cols].sum(axis=1)
# Physicians = anesthesiologists of either kind
table["physician_anesthesiologists"] = (
    table["anesthesiologists"] + table["pediatric_anesthesiologists"]
)
table["providers_per_100k"] = (table["total_providers"] / table["population_2025"] * 100_000).round(1)
table["physicians_per_100k"] = (
    table["physician_anesthesiologists"] / table["population_2025"] * 100_000
).round(1)

table.to_csv(OUT_PATH, index=False)

# Checks: nothing lost between script 02 and here
assert len(table) == 159, "expected 159 Georgia counties"
assert table["total_providers"].sum() == len(providers), "provider total changed"

zero = table["total_providers"] == 0
print(f"Counties:                     {len(table)}")
print(f"Providers counted:            {table['total_providers'].sum():,}")
print(f"Counties with zero providers: {zero.sum()}")
print(f"People living in those counties: {table.loc[zero, 'population_2025'].sum():,}")
print(f"Statewide providers per 100k: {table['total_providers'].sum() / table['population_2025'].sum() * 100_000:.1f}")
print("\nTop 5 counties by count:")
print(table.nlargest(5, "total_providers")[["county", "total_providers", "providers_per_100k"]].to_string(index=False))
