"""06_build_map_data.py

Joins every county-level result into one table (the downloadable dataset)
and attaches it to Georgia county shapes for the web map.

Outputs:
  data/processed/ga_county_dataset.csv   (159 rows: the public dataset)
  map/ga_county_dataset.csv              (copy, so the map page can link to it)
  map/ga_counties.geojson                (county shapes + data, read by map/index.html)
  map/ga_hospitals.csv                   (hospital list, for map markers)
"""
import io
import json
import shutil
import string
import zipfile

import pandas as pd
import shapefile  # the pyshp package: reads Census shapefiles

PROVIDERS_PATH = "data/processed/county_provider_counts.csv"
SECONDARY_PATH = "data/processed/county_secondary_counts.csv"
HOSPITALS_PATH = "data/processed/county_hospital_flags.csv"
HOSPITAL_LIST_PATH = "data/processed/ga_hospitals.csv"
SHAPES_ZIP = "data/raw/cb_2023_us_county_5m.zip"
DATASET_OUT = "data/processed/ga_county_dataset.csv"
GEOJSON_OUT = "map/ga_counties.geojson"

# --- One table with everything per county ----------------------------------
providers = pd.read_csv(PROVIDERS_PATH, dtype={"county_fips": str})
secondary = pd.read_csv(SECONDARY_PATH, dtype={"county_fips": str})
hospitals = pd.read_csv(HOSPITALS_PATH, dtype={"county_fips": str})

data = providers.merge(secondary, on="county_fips", how="left")
data["also_serves_providers"] = data["also_serves_providers"].fillna(0).astype(int)
data = data.merge(hospitals.drop(columns="county"), on="county_fips", how="left")

# Plain-language flags for the gaps this project is about
data["no_providers"] = data["total_providers"] == 0
data["surgery_but_no_providers"] = (data["surgical_hospitals"] > 0) & data["no_providers"]
data["ob_but_no_physician"] = data["has_ob_services"] & (data["physician_anesthesiologists"] == 0)

assert len(data) == 159, "expected 159 Georgia counties"
data.to_csv(DATASET_OUT, index=False)
shutil.copy(DATASET_OUT, "map/ga_county_dataset.csv")
shutil.copy(HOSPITAL_LIST_PATH, "map/ga_hospitals.csv")

# --- County shapes ----------------------------------------------------------
# Read the shapefile straight out of the zip, keeping only Georgia (state FIPS 13)
with zipfile.ZipFile(SHAPES_ZIP) as z:
    reader = shapefile.Reader(
        shp=io.BytesIO(z.read("cb_2023_us_county_5m.shp")),
        dbf=io.BytesIO(z.read("cb_2023_us_county_5m.dbf")),
    )
    shapes = [sr for sr in reader.shapeRecords() if sr.record["STATEFP"] == "13"]


def round_coords(coords):
    """Round every longitude/latitude to 4 decimals (about 10 m) to shrink the file."""
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 4), round(coords[1], 4)]
    return [round_coords(c) for c in coords]


rows = data.set_index("county_fips").to_dict(orient="index")

# Each county's hospitals, so clicking a county on the map can list them
hospital_list = pd.read_csv(HOSPITAL_LIST_PATH, dtype=str)
hospitals_by_county = {}
for h in hospital_list.itertuples():
    hospitals_by_county.setdefault(h.county_fips, []).append({
        "name": string.capwords(h.name),  # capwords keeps "Joseph's" (title() gives "Joseph'S")
        "city": string.capwords(h.city),
        "type": h.hospital_type,
        "beds": h.beds,
        "surgery": h.performs_surgery == "True",
    })

features = []
for sr in shapes:
    fips = sr.record["GEOID"]
    geometry = sr.shape.__geo_interface__
    geometry["coordinates"] = round_coords(geometry["coordinates"])
    props = {"county_fips": fips, **rows[fips], "hospital_list": hospitals_by_county.get(fips, [])}
    features.append({"type": "Feature", "properties": props, "geometry": geometry})

assert len(features) == 159, "expected 159 county shapes"
with open(GEOJSON_OUT, "w") as f:
    json.dump({"type": "FeatureCollection", "features": features}, f, default=bool)

print(f"Dataset: {DATASET_OUT} ({len(data)} counties, {len(data.columns)} columns)")
print(f"Map shapes: {GEOJSON_OUT} ({len(features)} counties)")
print(f"Counties with no providers:              {data['no_providers'].sum()}")
print(f"Surgical hospital but no providers:      {data['surgery_but_no_providers'].sum()}")
print(f"OB services but no physician anesthesiologist: {data['ob_but_no_physician'].sum()}")
