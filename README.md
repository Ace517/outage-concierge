# AI Outage Concierge (Hack/OHIO 2026, AEP challenge)

One-page Streamlit app: pick a customer and a storm scenario, get an outage-risk band with reasons,
a restoration range you can stress-test with sliders, a tailored prep checklist, alert eligibility,
and the four customer messages (before the storm, outage confirmed, estimate updated, power restored).

## Run it (2 minutes)

    pip install -r requirements.txt
    streamlit run app.py

The processed data is already in `data/processed/`, so you do NOT need the raw shapefiles.

## Files

| File | What it does |
|---|---|
| `app.py` | Entry point: page list (navigation) and sidebar. |
| `ui.py` | Shared styling, sidebar controls (customer, scenario, medical, alerts) and per-location numbers. |
| `views/` | One file per page: overview, risk, restoration, prepare, alerts, messages, about. |
| `CHALLENGE_CHECKLIST.md` | Challenge requirements mapped to pages, with ideas to improve each. |
| `engine.py` | All logic: risk score, restoration calculator, alert rules, messages. Every assumption is labeled in here. |
| `build_data.py` | Optional. Rebuilds `data/processed/` from the raw AEP zips. |
| `data/processed/` | `premises.csv.gz` (anonymized), `circuits.csv`, `meta.json` (personas and benchmarks). |

## Rebuild the data (optional)

    pip install -r requirements-build.txt
    python build_data.py --raw path/to/aep_challenge_hack26/data/raw --workbook path/to/Install_Labor_HackOHIO.xlsx

Each rebuild uses a new random salt, so location codes change and the personas are re-picked automatically.

## What is real and what is assumed

Real (from the AEP package): customer, circuit and damage tables, the premise-to-equipment topology, and the labor-hour workbook
(equipment hours, access adders, 4.5x indirect labor multiplier).

Assumed (all labeled in `engine.py` and shown in the app's "How this works" box):
storm scenario multipliers, risk weights (45/25/20/10), wire-repair hours (not in the workbook), crew surge (1 crew per 12 items, max 15),
queue time (about a day in a major storm), range width, and the alert rules.

Honest limits: one storm in the data, no weather, no customer outage counts, day-level dates only.
The restoration crew and queue assumptions were tuned on that one storm; the range contains the observed finish day for 64% of circuits (in-sample).

## Demo path for the video (the submission video is 3 minutes and must also cover team name, project name, concept and development process)

0. The site opens on "Your details": enter a first name, city, street and home, or tap a demo customer.
1. Maria (Very high risk, medical need). Show the gauge, the three reasons, the confidence dots.
2. Drag the crews slider and the damaged-items slider. The range and the "what could move it" table update.
3. Scroll: red safety box, medical steps, alert rules (tick "signed up"), then the four message tabs.
4. Switch to Devon (Low risk) to show the same questions get a calm answer.
5. Switch the scenario to Extreme, then open "Pick another location" and click "Try a location outside our data" to show the fallback.
6. Open "How this works and what it can't do" and say the limits out loud.

## Privacy

Premise numbers become a random one-way code. House numbers, coordinates and the life-support flag are not in the app's data at all.
Medical steps appear only when the user declares a need.
