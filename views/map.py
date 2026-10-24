import pandas as pd
import pydeck as pdk
import streamlit as st

import engine
import ui
from ui import esc, html

ALPHA = 215  # mostly opaque so each step stays distinct on the pale base map; street names still show around areas
# Each view: what colors the areas, its bins (label, test, color) and a one-line description.
# Every view is one hue, light to dark, with a different hue per view so they never read as the same scale.
# Risk reuses the site's band colors. All ramps pass the dataviz validator (--ordinal) against the map surface.
VIEWS = {
    "Outage risk": {
        "desc": "Typical outage risk for homes in each area, in the storm scenario chosen in the sidebar.",
        "bins": [(b, None, ui.BAND_FILL[b]) for b in engine.BAND_ORDER],
    },
    "Restoration time": {
        "desc": "Typical hours until most customers in each area are back on, in the chosen scenario.",
        "bins": [("Under 24 hours", 24, "#86B6EF"), ("24 to 48 hours", 48, "#5598E7"), ("48 to 72 hours", 72, "#2A78D6"),
                 ("72 to 120 hours", 120, "#1C5CAB"), ("120+ hours", 1e9, "#0D366B")],
    },
    "Feb 2025 storm damage": {
        "desc": "How many damage reports came from each area in the real Feb 2025 storm. This doesn't change with the scenario.",
        "bins": [("None", 0, "#C3C8D1"), ("1 report", 1, "#A99BEA"), ("2 to 3", 3, "#7564D8"), ("4 or more", 1e9, "#4A3AA7")],
    },
    "Underground lines": {
        "desc": "Share of homes in each area with underground service, which wind and falling trees can't reach.",
        "bins": [("Under 20%", 0.2, "#66C2A2"), ("20 to 40%", 0.4, "#36A57F"), ("40 to 60%", 0.6, "#1C8865"),
                 ("60 to 80%", 0.8, "#11684D"), ("80% or more", 1.01, "#094834")],
    },
}


def rgba(hex_color: str, a: int = ALPHA):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


def pick_bin(view: str, value):
    for label, top, color in VIEWS[view]["bins"]:
        if (label == value) if top is None else (value < top if view != "Feb 2025 storm damage" else value <= top):
            return label, color
    label, _, color = VIEWS[view]["bins"][-1]
    return label, color


data = ui.load_hexes()
ui.heading("Outage map", "est")
if data is None:
    st.info("The map data hasn't been built yet. Run build_map.py (see the README).")
    ui.footer()
    st.stop()

sev = ui.ss.sev
view = st.segmented_control("Show", list(VIEWS), default="Outage risk", key="map_view", label_visibility="collapsed") or "Outage risk"
st.caption(VIEWS[view]["desc"] + (f" Scenario: **{sev}**." if view in ("Outage risk", "Restoration time") else ""))

rows = []
for h in data["hexes"]:
    r, t = h["risk"][sev], h["rest"][sev]
    if view == "Outage risk":
        label, color = pick_bin(view, r["band"])
        detail = f"{r['band']} risk (score {r['score']}). {r['high'] * 100:.0f}% of homes rate High or Very high."
    elif view == "Restoration time":
        label, color = pick_bin(view, t["mid"])
        detail = f"Typical restoration: {t['txt']}"
    elif view == "Feb 2025 storm damage":
        label, color = pick_bin(view, h["dmg"])
        detail = f"{h['dmg']} damage report{'s' if h['dmg'] != 1 else ''} in the Feb 2025 storm"
    else:
        label, color = pick_bin(view, h["ug"])
        detail = f"{h['ug'] * 100:.0f}% of homes have underground service"
    rows.append({"poly": h["poly"], "fill": rgba(color), "bin": label, "area": f"{h['city']} area",
                 "detail": detail, "homes": f"About {h['n']} homes", "id": h["id"]})
df = pd.DataFrame(rows)

# The user's own area (never their home's position, only the hexagon it falls in).
mine = ""
if ui.ss.hid in ui.prem.index:
    mine = ui.prem.loc[ui.ss.hid].get("hex", "")
    mine = mine if isinstance(mine, str) else ""
mine_df = df[df.id == mine]

layers = [
    pdk.Layer("PolygonLayer", df, get_polygon="poly", get_fill_color="fill", get_line_color=[255, 255, 255, 200],
              line_width_min_pixels=1, stroked=True, filled=True, pickable=True, auto_highlight=True,
              highlight_color=[20, 33, 61, 90]),
    pdk.Layer("PolygonLayer", mine_df, get_polygon="poly", filled=False, stroked=True,
              get_line_color=[20, 33, 61, 255], line_width_min_pixels=4),
    pdk.Layer("TextLayer", pd.DataFrame(data["towns"]), get_position=["lon", "lat"], get_text="name",
              get_size=15, get_color=[20, 33, 61, 255], get_text_anchor='"middle"', get_alignment_baseline='"center"',
              font_family='"Barlow Semi Condensed", Barlow, sans-serif', font_weight=700,
              background=True, get_background_color=[255, 255, 255, 210], background_padding=[4, 2]),
]
if len(mine_df):
    h = next(x for x in data["hexes"] if x["id"] == mine)
    center = {"latitude": h["lat"], "longitude": h["lon"], "zoom": 11.5}
else:
    center = {"latitude": sum(x["lat"] for x in data["hexes"]) / len(data["hexes"]),
              "longitude": sum(x["lon"] for x in data["hexes"]) / len(data["hexes"]), "zoom": 10.3}

deck = pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(pitch=0, **center),
    map_provider="carto", map_style=pdk.map_styles.CARTO_LIGHT,
    tooltip={"html": "<b>{area}</b><br/>{detail}<br/><span style='opacity:.75'>{homes}</span>",
             "style": {"backgroundColor": "#14213D", "color": "white", "fontFamily": "Barlow, sans-serif", "fontSize": "14px"}},
)
st.pydeck_chart(deck, height=520, use_container_width=True)

# Legend: every color has a text label; the user's area is an outline.
swatches = "".join(
    f'<span class="lg"><i style="background:{c}"></i>{esc(label)}</span>' for label, _, c in VIEWS[view]["bins"])
you = ('<span class="lg"><i style="background:transparent;border:3px solid #14213D"></i>Your area</span>' if len(mine_df) else "")
html(f"""
<style>.legendrow{{display:flex;flex-wrap:wrap;gap:6px 16px;margin:8px 0 2px;font-size:.95rem;color:var(--ink);}}
.lg{{display:inline-flex;align-items:center;gap:6px;}}
.lg i{{width:16px;height:16px;border-radius:4px;display:inline-block;border:1px solid rgba(20,33,61,.15);}}</style>
<div class="legendrow">{swatches}{you}</div>
""")

# One plain-language takeaway per view.
counts = df.bin.value_counts()
total = len(df)
if view == "Outage risk":
    share = (counts.get("High", 0) + counts.get("Very high", 0)) / total
    takeaway = f"In the {sev} scenario, {share:.0%} of areas rate High or Very high."
elif view == "Restoration time":
    top = counts.idxmax()
    takeaway = f"In the {sev} scenario, the most common wait is {top.lower()} ({counts.max() / total:.0%} of areas)."
elif view == "Feb 2025 storm damage":
    takeaway = f"{1 - counts.get('None', 0) / total:.0%} of areas had at least one damage report in the Feb 2025 storm."
else:
    takeaway = f"{(counts.get('60 to 80%', 0) + counts.get('80% or more', 0)) / total:.0%} of areas are mostly underground."
st.markdown(f"**{takeaway}**")

if ui.ss.hid in ui.prem.index and not len(mine_df):
    st.caption("Your area has too few homes to show on its own, so it isn't outlined. We never show areas with fewer than "
               f"{data['min_homes']} homes.")
st.caption(f"Each hexagon is a neighborhood about 450 m across with at least {data['min_homes']} homes. "
           "Areas with fewer homes are left off so no single home can be picked out. Hover an area for details.")

ui.next_page("views/risk.py", "Next: will I lose power?")
ui.footer()
