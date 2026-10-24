# Project brief: AI Outage Concierge (Hack/OHIO 2026, AEP challenge)

Read this first. It is the full context from the chat where this project was started.

## Goal
Build a customer-facing storm outage assistant prototype for the AEP "AI Outage Concierge" challenge at HackOHI/O (Oct 24-25, 2026, 24-hour event).
Organizers say judges score submitted project videos, so the demo video matters as much as the code.
Team: design/pitch/video and frontend. No ML or GIS specialist. Time budget is short (under 8 hours total, ideally ~3).

The challenge's minimum demo: (1) customer picks an anonymized location, (2) risk prediction with confidence and explanation,
(3) damage/restoration scenarios give a restoration range, (4) prep actions and alert eligibility, (5) at least one proactive message,
(6) show how privacy, safety, uncertainty and model limits are handled. Judges should be able to change a scenario input and see the response.

## Where things stand
A working Streamlit app is built and tested (all personas x scenarios, fallback path, clean-room run). Files:
- `app.py`: layout, wording and styling only.
- `engine.py`: all logic (risk score, restoration calculator, alert rules, messages). Every assumption is labeled ASSUMPTION.
- `build_data.py`: optional rebuild of `data/processed/` from the raw AEP zips.
- `data/processed/`: `premises.csv.gz` (anonymized), `circuits.csv`, `meta.json` (personas, benchmarks).
- `README.md`: run steps and a 2-minute demo path.
Run: `pip install -r requirements.txt` then `streamlit run app.py`.

## Data facts (do not rediscover)
- Source repo: github.com/hackohio/aep_challenge_hack26. Data is Appalachian Power territory around Roanoke/Vinton/Salem, Virginia:
  117,642 premises, 110 circuits, 113 life-support-flagged premises (the flag is never exported to the app).
- Customer `circuit_id` looks like `0000027`; the damage file's `Circuit` looks like `CIR27`. Strip zeros and compare as integers.
- The damage file has 1,659 records but one storm (Feb 12-18, 2025) holds ~1,250. Dates are whole days. `Event` is always "Default",
  `Outage_Num` is always 0, and there is no weather. So there is NO ground-truth "did this customer lose power" label.
- `NEAR_FID` does not map to layer ids. Damaged devices were matched by nearest device within 30 m, then traced to premises
  through `matched_upstream.txt`. This works for fuse banks and transformers. Recloser and switch damage did not match topology ids, so those use circuit-level exposure.
- About 2.9% of premises were directly downstream of a damaged fuse or transformer; about 71% sat on a circuit with at least one damage record.
- Labor workbook: 4.5x indirect labor multiplier, install/removal hours by equipment, access adders (+0.5 h). It has NO wire-repair hours,
  so a wire repair is assumed from dead-end, connector, insulator and pin hours.
- Repairs in that storm: half finished within 1 day, 90% within 2 days (day-level).

## Key decisions
- Not a trained ML model (no labels). It is a transparent weighted exposure score: circuit damage rate 45%, own equipment hit before 25%,
  overhead vs underground 20%, protective devices upline 10%; the storm scenario scales it. Output is a band, not a percent chance.
- Restoration = items x labor hours x 4.5, divided by workers, plus rest and queue time. Range is wide on purpose.
  Crew surge (1 per 12 items, max 15) and queue time (~1 day in a major storm) were tuned on the Feb 2025 storm:
  the range contains the observed finish day for 40 of 62 circuits (64%). This is in-sample, so say "calibrated", never "validated".
- Alert rules are challenge assumptions modeled on opt-in text/email alerts. Not official utility terms.
- Visual language: dashed outline = model estimate, solid = confirmed fact (none in the demo), navy and blue palette, Barlow type,
  no all-caps labels. Each section is headed by the customer's question.

## Rules that must not break
- Never show premise numbers, house numbers, coordinates or the life-support flag. Location codes are random one-way hashes.
- Never infer medical or sensitive attributes. Medical steps appear only when the user declares a need.
- Estimates are always ranges and labeled as estimates. Messages keep the "[DEMO]" prefix. Do not imply the utility endorsed this.
- Do not call it a trained or validated model.

## Open items
1. The HackOHI/O Judging Guide and Guidebook (Google Docs) could not be read. Paste the judging criteria and submission deadline here.
2. Team to run the app, click through all three personas, and restyle (fonts load from Google Fonts, so check the look online).
3. Write the ~2-minute video script and the submission text (README has a demo path).
4. Optional if time allows: match recloser/switch damage using `location_n`; add a map; show nearby hospitals/fire stations.
