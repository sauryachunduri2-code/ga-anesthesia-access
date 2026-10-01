# Georgia Anesthesia Access: Methodology

*Version 1.0, September 30, 2026. Every decision below is logged with its date and reasoning in `METHODOLOGY_LOG.md`.*

## 1. Purpose

This project maps where anesthesia providers practice across Georgia's 159 counties and compares that with where hospitals still perform surgery and deliver babies. Surgery and childbirth (including cesarean sections and epidurals) depend on anesthesia, so a county with an operating room or labor unit but no local anesthesia workforce is a warning sign for access.

## 2. Key findings

| Measure | Value |
|---|---|
| Anesthesia providers with a Georgia primary practice address | **4,996** (1,412 anesthesiologists, 30 pediatric anesthesiologists, 1,995 CRNAs, 1,559 anesthesiologist assistants) |
| Statewide providers per 100,000 residents | **44.2** |
| Counties with **no** provider at a primary practice address | **63 of 159**, home to 856,879 people (7.6% of Georgians) |
| Zero-provider counties that contain a Critical Access Hospital | 17 |
| Counties with a surgical hospital but no provider | **9**: Bacon, Ben Hill, Candler, Cook, Elbert, Murray, Putnam, Rabun, Worth |
| Counties with OB services but no physician anesthesiologist | **5**: Bacon, Franklin, Grady, Sumter, Wilkes |

Providers are heavily concentrated: Fulton County alone has 1,321 (26% of the state total). Among counties with at least one provider, the median rate is 15.6 per 100,000, about a third of the statewide average.

## 3. Data sources

| Source | Version | Used for |
|---|---|---|
| CMS NPPES NPI Registry, full data dissemination file | September 2026 (built 2026-09-14) | Provider identity, type, practice address |
| HUD-USPS ZIP Code Crosswalk, ZIP-COUNTY | Q2 2026 | Practice ZIP → county |
| CMS Provider of Services (POS) file, Hospital & Non-Hospital Facilities | Q2 2026 (published 2026-07-16) | Hospital list, type, surgical services |
| Georgia DCH / State Office of Rural Health, "Georgia Counties Offering CON-authorized Obstetrical Services" | Updated September 2025 | Which counties deliver babies |
| U.S. Census Bureau county population estimates | Vintage 2025 (July 1, 2025) | Per-capita rates |
| U.S. Census Bureau cartographic boundary file, counties, 1:5,000,000 | 2023 | Map shapes |

Download URLs and dates are in `METHODOLOGY_LOG.md`.

## 4. Method

The pipeline is six Python (pandas) scripts in `scripts/`, run in order. Raw files are never modified.

**Step 1: Find anesthesia providers (`01_filter_nppes.py`).** The 11.7 GB NPPES file (9,798,758 records) is read in 200,000-row chunks directly from the zip. A record is kept when its practice-location state is Georgia and its **primary** taxonomy code is one of:

- 207L00000X Anesthesiology
- 207LP3000X Pediatric Anesthesiology
- 367500000X Certified Registered Nurse Anesthetist (CRNA)
- 367H00000X Anesthesiologist Assistant

Pain Medicine (207LP2900X) and Addiction Medicine (207LA0401X) are excluded because those physicians mainly practice in clinics, not operating rooms or labor units. Requiring the code to be *primary* (rather than any of a provider's 15 listed codes) counts people who mainly practice anesthesia. Every Georgia record had a primary code marked, so this rule dropped no one by accident. The filter found 5,525 records: 4,996 individuals and 529 organizations (group practices). **Only individuals are counted**; organizations are saved separately so they never inflate a count of people. There were no duplicate NPIs. Three records had deactivation dates, but all three were later reactivated.

**Step 2: Assign counties (`02_zip_to_county.py`).** ZIP codes don't follow county lines, and HUD reports what share of each ZIP's addresses falls in each county. Each provider is assigned wholly to the county holding the **largest share of business addresses** in their practice ZIP. Whole-person counts are easy to interpret, and practice addresses are businesses. 1,070 providers (21%) are in ZIPs split across counties. Fourteen providers used Atlanta post-office ZIPs (30365, 30335, 31193) that are not in the crosswalk; they were assigned to Fulton County by hand.

**Step 3: County rates (`03_county_provider_counts.py`).** Providers are counted per county by type and divided by 2025 population to give providers per 100,000 residents. Counties with no providers stay in the table with zeros.

**Step 4: Hospitals (`04_hospitals.py`).** Active Georgia hospitals in the CMS POS file were kept: 96 short-term general hospitals, 32 Critical Access Hospitals, and 1 Rural Emergency Hospital. A hospital **performs surgery** if its inpatient surgical services code shows the service is provided by its own staff, under arrangement, or both: 107 hospitals in 84 counties. The Rural Emergency Hospital has no inpatient care and is never counted as surgical.

A county **has obstetric services** if it appears on the Georgia DCH map (54 counties). CMS's own OB code was tested first but proved stale. It disagreed with DCH in 15 counties, marking OB as present at rural hospitals known to have closed labor units and absent at large delivering hospitals (Northside Forsyth, Tift Regional). Each of the 15 was checked by web search. Four closures were confirmed by dated news reports (Barrow, Emanuel, Lumpkin, Stephens), all agreeing with DCH, and no search contradicted DCH. The CMS count is kept in the dataset for comparison.

**Step 5: Secondary locations (`05_secondary_locations.py`).** NPPES lets providers list additional practice addresses. For each county, the "also serves" number counts providers who list a secondary location there in addition to a primary address elsewhere. It is shown separately and **never added** to the headline count, so no one is counted twice. 498 providers list a secondary Georgia location; only 4 of the 63 zero-provider counties gain anyone this way.

**Step 6: Dataset and map (`06_build_map_data.py`, `map/index.html`).** All county results are joined into one 159-row table and attached to Census county shapes. The interactive map colors counties by providers per 100,000 residents (other metrics available in a menu). Zero-provider counties get a distinct color, OB counties are outlined in purple, and surgical-hospital counties with no provider are outlined in red.

## 5. Limitations

1. **Address ≠ where care happens.** NPPES records one primary practice address, often a group's billing office. Anesthesia providers commonly work at several hospitals, so county counts show where providers are *based*, not every place they work. The 9 counties with a surgical hospital but no provider almost certainly receive anesthesia care from providers based elsewhere. These counties depend on outside coverage, which is a fragility the map highlights but cannot measure.
2. **Secondary locations are rarely filled in.** The "also serves" layer is a floor, not a complete picture.
3. **Out-of-state providers are not counted.** Providers based in Chattanooga, Jacksonville, Tallahassee or other border cities who serve Georgia counties are missing.
4. **NPPES is self-reported and not always current.** Providers who retired or moved may still list Georgia addresses. NPPES does not show whether someone is actively practicing or how many hours they work.
5. **County assignment at borders.** The largest-share rule places every provider in a split ZIP entirely in one county.
6. **Stale hospital records.** CMS still lists Chestatee Regional Hospital (Lumpkin County) as an active surgical hospital, although it closed and reopened as NGMC Lumpkin, which CMS lists separately without surgery. The record was left unedited by choice, so Lumpkin County shows a surgical hospital it likely no longer has. Other stale records may exist.
7. **OB data date.** The DCH OB map is dated September 2025, so labor units that opened or closed after that are not reflected.
8. **Counts, not capacity.** A per-capita rate does not capture case volume, travel time, or whether a CRNA practices with or without anesthesiologist supervision.

## 6. Reproducing this work

Download the raw files listed in section 3 into `data/raw/`, then run `uv run python scripts/01_filter_nppes.py` through `06_build_map_data.py` in order. The HUD crosswalk requires a free huduser.gov account. Outputs: `data/processed/ga_county_dataset.csv` (the public dataset), `data/processed/ga_hospitals.csv`, and the map files in `map/`.
