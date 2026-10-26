# AI Outage Concierge

**A storm assistant for one home.** Pick a home and a storm scenario, and it answers the three questions customers ask:
**Will I lose power? How long could it last? What should I do?** Built in 24 hours at **HackOHI/O 2026** for the **AEP challenge**
by team **Rio Ganga**: Darsh Patel, Pranav Kottagi, Shishir Joshi and Lucas Teitelbaum (Ohio State).

**Live demo:** _link coming soon_

> A prototype built on the organizers' sanitized sample data for Roanoke, Vinton and Salem, Virginia. Not endorsed or used by AEP.
> Customer names are fictional, and every number is an estimate.

## What you can do in it

| Page | What it shows |
|---|---|
| About this project | What this is and how to try it (the first page new visitors see) |
| Your details | Pick a city, street and anonymous home, or one of four demo customers (Maria, Devon, Priya, David) |
| Overview | Your risk, restoration range and alert status at a glance |
| Outage map | Neighborhood map with four views: outage risk, restoration time, Feb 2025 storm damage, underground lines |
| Will I lose power? | Risk band (Low to Very high), confidence, and the three reasons behind it |
| How long will it last? | Restoration range in hours, what-if sliders, and every step of the math |
| How do I prepare? | Safety steps and a prep checklist for your situation (medical steps only if you declare a need) |
| Outage alerts | Eligibility, sign-up with a phone number (not stored), and when a person steps in |
| Messages we send | The four texts: before the storm, outage confirmed, estimate updated, power restored |
| How this works | Data, method, privacy and limits |

Change the **storm scenario** (Breezy, Strong wind, Major storm, Extreme) in the sidebar and every page and the map update.

## Run it on your computer (about 2 minutes)

You need **Python 3.10 or newer**.

```bash
git clone https://github.com/Ace517/outage-concierge.git
cd outage-concierge
python -m venv .venv
```

Then install and start it:

- **Windows:** `.venv\Scripts\python.exe -m pip install -r requirements.txt` then `.venv\Scripts\python.exe -m streamlit run app.py`
- **Mac / Linux:** `.venv/bin/python -m pip install -r requirements.txt` then `.venv/bin/python -m streamlit run app.py`

Open http://localhost:8501. The processed data is included, so you don't need the raw AEP files.
The outage map needs an internet connection for its street tiles.

## How it works

**Risk** is a transparent exposure score, not a trained model (the data has no "who lost power" labels and no weather):
45% circuit damage per customer in the Feb 2025 storm, 25% whether equipment feeding this exact home was damaged,
20% overhead vs underground service, 10% protective devices between the home and the substation. The storm scenario scales it.

**Restoration** = damaged items x labor hours per repair type (AEP's workbook) x 4.5 for travel, safety and setup,
divided by the crews' workers, plus rests between 16-hour shifts and time to assess damage and wait for crews. Shown as a range in hours.

**Honest limits:** one storm, no weather, no customer outage counts, damage dates only to the day. The crew and queue assumptions
were tuned on that one storm; the range contains the observed finish day for 40 of 62 circuits (calibrated, not validated).
Every assumption is labeled in `engine.py` and on the "How this works" page.

## Privacy

- Premise numbers become random one-way codes. House numbers, coordinates and the life-support flag are not in the app's data.
- The map shows only neighborhoods about 450 m across with at least 10 homes; sparser areas are left off.
- Medical needs are never guessed; only the user can declare them.
- The alert sign-up checks a phone number and keeps only its last 4 digits in the browser session. Nothing is saved or sent.

## Files

| File | What it does |
|---|---|
| `app.py` | Entry point: page list and sidebar |
| `ui.py` | Shared styling, sidebar controls and per-location numbers |
| `views/` | One file per page |
| `engine.py` | All logic: risk score, restoration calculator, alert rules, messages |
| `data/processed/` | Anonymized homes, circuits, personas and benchmarks, map areas |
| `build_data.py`, `build_map.py` | Optional: rebuild `data/processed/` from the raw AEP zips (`pip install -r requirements-build.txt`) |
| `PROJECT_BRIEF.md`, `CHALLENGE_CHECKLIST.md` | Our project notes and how each challenge requirement maps to a page |

To rebuild the data: `python build_data.py --raw path/to/aep_challenge_hack26/data/raw`, then
`python build_map.py --raw path/to/aep_challenge_hack26/data/raw`. A full rebuild changes the anonymous location codes.

## Built with

Python, Streamlit, pandas, NumPy, GeoPandas, Shapely and pydeck, with a CARTO / OpenStreetMap base map.
AI coding assistance from Claude Code; the team made the design and method decisions and checked the numbers.
