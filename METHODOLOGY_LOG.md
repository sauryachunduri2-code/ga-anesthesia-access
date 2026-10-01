# Methodology Log

## NPPES Download
- Download date: 2026-09-26

- URL: https://download.cms.gov/nppes/NPPES_Data_Dissemination_September_2026_V2.zip

- Zip size: 1.1gb

- Data Built on: 2026-09-14

## Decision: Primary taxonomy only (2026-09-29)
- NPPES lets a provider list up to 15 taxonomy codes, with one marked primary ("Healthcare Provider Primary Taxonomy Switch_N" = Y).
- We count a provider only if an anesthesia code is their PRIMARY taxonomy.
- Reasoning: counts people who mainly practice anesthesia, not those who list it as a side specialty. This gives a stricter, lower count than matching any of the 15 slots.

## Decision: Subspecialty codes, mixed (2026-09-29)
- INCLUDED: 207LP3000X Pediatric Anesthesiology (delivers anesthesia for surgery).
- EXCLUDED: 207LP2900X Pain Medicine and 207LA0401X Addiction Medicine (mostly clinic work, not surgical or obstetric anesthesia).
- Final code list: 207L00000X, 207LP3000X, 367500000X, 367H00000X. (Confirmed 2026-09-30.)

## Decision: Individuals and organizations kept separate (2026-09-30)
- NPPES "Entity Type Code" 1 = individual, 2 = organization. 01_filter_nppes.py found 4,996 individuals and 529 organizations (Sept 2026 file).
- Headline provider counts use INDIVIDUALS ONLY. Organizations are anesthesia group practices, not people, and their clinicians already have their own individual NPIs.
- Organizations are saved to their own file and may be shown as a separate layer (e.g. anesthesia groups per county), never added to the people count.

## Check: deactivated NPIs (2026-09-30)
- 3 kept NPIs had a deactivation date; all 3 also had a later reactivation date, so all were kept. No filter needed.

## Downloads (2026-09-30)
- CMS Provider of Services, Hospital & Non-Hospital Facilities, Q2 2026 (period 2026-04-01 to 2026-06-30, published 2026-07-16)
  - URL: https://data.cms.gov/sites/default/files/2026-07/7780b4e3-4c4b-4811-8884-65ca23b7a4e8/Hospital_and_other.DATA.Q2_2026.csv
  - File: data/raw/Hospital_and_other.DATA.Q2_2026.csv (30 MB)
- Census cartographic boundary file, US counties 2023, 1:5,000,000
  - URL: https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_5m.zip
- Census Population Estimates, county totals, Vintage 2025 (July 1, 2025 estimates)
  - URL: https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv
- Georgia DCH / State Office of Rural Health, "Georgia Counties Offering CON-authorized Obstetrical (OB) Services", updated September 2025 (map PDF: 68 facilities, 54 counties)
  - URL: https://dch.georgia.gov/document/document/georgia-counties-offering-obstetrical-servicessept-2025/download
  - File: data/raw/ga_dch_ob_counties_sept2025.pdf

## Decision: ZIP to county = largest business-address share (2026-09-30)
- HUD's crosswalk splits each ZIP across counties by ratio. Each provider is assigned wholly to the county with the largest BUS_RATIO (share of business addresses) for their practice ZIP.
- Reasoning: keeps counts as whole people and is easy to explain; practice addresses are businesses, so BUS_RATIO fits better than RES_RATIO. Tradeoff: some error for providers in border ZIPs.

## Decision: "Performs surgery" = CMS inpatient surgery code (2026-09-30)
- A hospital counts as surgical if it is an active (PGM_TRMNTN_CD = 00) short-term general hospital (subtype 01) or Critical Access Hospital (subtype 11) and IP_SRGCL_SRVC_CD is 1, 2, or 3 (provided by staff, under arrangement, or both).
- Excluded: psychiatric, rehab, long-term care, children's-only and transplant-center records, and the Rural Emergency Hospital (subtype 28, Irwin County Hospital), which has no inpatient care.
- Rejected alternative: OPRTG_ROOM_CNT > 0, because only 49 GA hospitals fill in that field.

## Decision: "Delivers babies" = CMS OB code, checked against Georgia DCH (2026-09-30)
- Primary source: CMS POS Q2 2026 OB_SRVC_CD in 1, 2, 3 for the same active short-term + CAH hospitals (74 facilities before checking).
- Check: compare county by county with DCH's Sept 2025 CON-authorized OB map (68 facilities, 54 counties). Every mismatch is listed for a decision, not resolved silently.

## Decision: Population = Census Vintage 2025 estimates (2026-09-30)
- Per-capita rates use POPESTIMATE2025 (July 1, 2025) from the Census county estimates file. Closest in time to the Sept 2026 NPPES data.

## Decision REVISED: "Delivers babies" = Georgia DCH map, not CMS (2026-09-30)
- Replaces the earlier "CMS OB code + DCH check" decision from today.
- Why: CMS and DCH disagreed on 15 counties. CMS marked OB as present at rural hospitals known to have closed L&D, and absent at large hospitals that clearly deliver babies (Northside Forsyth, Tift Regional). CMS OB codes are only refreshed at infrequent surveys, so they are stale.
- User's rule: search the web for each of the 15 counties; use DCH unless a search definitively shows otherwise.
- Web search results (2026-09-30):
  - Confirmed closed L&D, agreeing with DCH: Barrow (NGMC Barrow), Emanuel (Emanuel Medical Center), Lumpkin (Chestatee Regional, L&D suspended 2013-04-30), Stephens (Stephens County Hospital, recent closure).
  - Not definitive (undated or unclear): Ben Hill, Dodge, Forsyth, Grady, Meriwether, Pulaski, Seminole, Tift, Washington, Wilkes, Worth. DCH used.
  - No search contradicted DCH.
- Result: map uses the 54 DCH counties (column has_ob_services). CMS count kept as cms_ob_hospitals; the disagreements are saved in data/processed/ob_source_mismatches.csv.
- Limitation: DCH is dated September 2025, so L&D openings or closings after that date are not captured.

## Decision: Keep CMS hospital records as published, including a known stale one (2026-09-30)
- CMS POS Q2 2026 lists both CHESTATEE REGIONAL HOSPITAL (surgery = yes) and NORTHEAST GEORGIA MEDICAL CENTER LUMPKIN (surgery = no) as active in Lumpkin County. Chestatee closed and reopened as NGMC Lumpkin, so its record is stale.
- User chose to keep CMS data unedited (no manual corrections) and document the error. Effect: Lumpkin County shows a surgical hospital that likely no longer operates as one.
- Listed as a known limitation in the methodology document.

## Download: HUD-USPS ZIP Code Crosswalk, ZIP-COUNTY, 2nd Quarter 2026 (2026-09-30)
- Downloaded 2026-09-30 from https://www.huduser.gov/apps/public/uspscrosswalk/home (login required; landing page https://www.huduser.gov/portal/datasets/usps_crosswalk.html)
- File: data/raw/ZIP-COUNTY_062026.xlsx (2.5 MB, 54,570 rows; columns zip, geoid, city, state, res_ratio, bus_ratio, oth_ratio, tot_ratio)

## Decision: Atlanta PO-box ZIPs assigned to Fulton County (2026-09-30)
- 14 providers had practice ZIPs not in the HUD crosswalk: 30365 (12), 30335 (1), 31193 (1). All are Atlanta post-office / unique ZIPs, likely billing addresses.
- Assigned by hand to Fulton County (FIPS 13121), keeping all 4,996 individuals in the totals. Marked in column county_method.
- Tie-break rule in 02_zip_to_county.py: if two counties tie on bus_ratio, the higher tot_ratio wins.
- Result: 1,070 providers (21%) sit in ZIPs split across counties; each is counted wholly in the county with the largest business share.

## Decision: Secondary practice locations as a separate "also serves" layer (2026-09-30)
- Headline counts stay PRIMARY practice address only, so each person is counted exactly once and county counts add up to the state total (4,996).
- A second, separate per-county number counts providers who list a SECONDARY practice location (NPPES pl_pfile) in that county. Never added to the headline.
- Why: 9 counties have a CMS surgical hospital but zero providers by primary address (Bacon, Ben Hill, Candler, Cook, Elbert, Murray, Putnam, Rabun, Worth). Anesthesia providers often work at several hospitals or list a group billing address as primary, so primary-only undercounts where care actually happens.

## Decision: Map color = all anesthesia providers per 100,000 residents (2026-09-30)
- Main choropleth: (anesthesiologists + pediatric anesthesiologists + CRNAs + AAs) / 2025 population x 100,000. Zero-provider counties get their own distinct color.
- Raw counts and physician-only rates available as secondary views.
- Result (2026-09-30): 498 of the 4,996 providers list a secondary GA location in a county other than their primary one, reaching 60 counties. Of the 63 zero-provider counties, only 4 gain any "also serves" provider (e.g. Cook 7, Bacon 1); 59 remain at zero. Secondary locations are self-reported and rarely filled in, so this layer is a floor, not a full picture.
- Limitation: only providers with a Georgia PRIMARY address are included. Out-of-state providers (e.g. Chattanooga, Jacksonville, Tallahassee) who serve Georgia border counties are not counted.
