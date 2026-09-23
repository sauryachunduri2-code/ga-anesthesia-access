# Georgia Anesthesia Access Project

## What this is
A public, county-level map and open dataset of anesthesia providers in Georgia's 159 counties, cross-referenced with hospitals that still perform surgery and deliver babies. Outputs: an interactive map (GitHub Pages), a downloadable cleaned dataset, and a 2 to 4 page methodology document.

I'm a high school student learning Python as I go. Explain what code does in plain language before running it, and keep the code simple enough that I can read and defend every line.

## How I learn
I'm trying to become proficient in Python and bash fast, not just finish the project.
- Before running any bash command, explain it in one line.
- After writing any code, stop and ask me to explain it back before moving on.
- When a task is small (under ~15 lines or a single command), don't write it. Give me a hint, let me try first, then review my attempt.
- Flashcards: whenever a response introduces new commands or concepts (aim for 3 to 5 per session), list them in the response AND append them to `flashcards.tsv` in the same turn. Don't wait for the end of the session.
  - `flashcards.tsv` is one running Anki import file. Never start a new file or deck.
  - Each row: `ID<TAB>Front<TAB>Back<TAB>Tags`. IDs continue the sequence (`ga-0001`, `ga-0002`, ...) and never change once written; Anki uses them to recognize cards it already has.
  - Before appending, check the file so no concept is added twice. Never edit or delete existing rows unless I ask.
  - No tab characters inside a card. Tags are space-separated words like `bash`, `git`, `uv`, `python`, `pandas`.
- I have basic Python knowledge and almost no bash knowledge. Pitch explanations at that level.
- After every response, include an explanation of what happened (how and why it worked), not a summary of what was done. Keep it short, just enough for me to understand.
- Don't make the answers to your explain-back questions easy to find in the explanation. I should piece it together myself; I'll ask if I need help.
- Always end every response with a "Next steps" section saying what needs to happen next.

## Data sources
- NPPES NPI Registry bulk file (CMS). Very large; lives in `data/raw/`, never committed.
- NUCC taxonomy codes: 207L00000X (anesthesiology), 367500000X (CRNA), 367H00000X (anesthesiologist assistant). Subspecialty codes (207LP2900X, 207LP3000X, 207LA0401X) are a deliberate choice; ask me before including or excluding them.
- HUD USPS ZIP to county crosswalk (quarterly). ZIPs cross county lines; the crosswalk gives allocation ratios, not clean assignments.
- CMS Provider of Services file (hospital type, surgical services).
- Georgia State Office of Rural Health county maps (OB services, rural/CAH/REH hospitals).

## Rules
- Never make a methodology decision silently. Any choice that could move the headline number (taxonomy codes, ZIP-to-county method, deduplication, address type) must be flagged to me and logged in `METHODOLOGY_LOG.md` with the date and reasoning.
- Record the download date and URL for every raw file in `METHODOLOGY_LOG.md`.
- Raw data is read-only. Write cleaned outputs to `data/processed/`.
- Use pandas. Prefer small scripts in `scripts/` numbered in run order (01_filter_nppes.py, 02_zip_to_county.py, ...).
- Filter the NPPES file in chunks; it will not fit comfortably in memory at once.
- Don't commit anything in `data/raw/`. Keep `.gitignore` up to date.

## Layout
- `data/raw/` original downloads (gitignored)
- `data/processed/` cleaned outputs
- `scripts/` numbered pipeline scripts
- `map/` map files for GitHub Pages
- `METHODOLOGY_LOG.md` running log of decisions
