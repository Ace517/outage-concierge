"""Shared layout pieces for every page: styling, data loading, sidebar controls and the per-location numbers.

All logic lives in engine.py. This file and views/ are layout and wording only.
"""
from __future__ import annotations

import json
from html import escape as esc
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import streamlit as st

import engine

DATA = Path(__file__).parent / "data" / "processed"

BAND_FILL = {"Low": "#3D8B5F", "Moderate": "#E3B23C", "High": "#E07B39", "Very high": "#B3261E"}
BAND_TEXT = {"Low": "#1E5F3C", "Moderate": "#7A5B00", "High": "#A04A0B", "Very high": "#8F1B14"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@500;600;700&display=swap');
:root{--ink:#14213D;--blue:#1F5FA8;--sky:#E8F0FA;--line:#C9D5E5;--muted:#4A5A72;--gold:#F2B134;}
.stApp{background:#F4F7FB;font-family:'Barlow','Segoe UI',system-ui,sans-serif;color:var(--ink);}
.stApp p,.stApp li,.stApp label,.stApp button,.stApp input,.stApp textarea,.stApp [data-baseweb="select"] div{font-family:'Barlow','Segoe UI',system-ui,sans-serif;}
[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],[data-testid="stDeployButton"],.stDeployButton{display:none;}
.block-container{max-width:1020px;padding-top:1rem;padding-bottom:4rem;}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
section[data-testid="stSidebar"][data-collapsed="true"]{transform:none!important;width:64px!important;min-width:64px!important;max-width:64px!important;visibility:visible!important;transition:none!important;}
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarUserContent"],
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavSeparator"],
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarResizeHandle"],
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavLink"] span[label]{display:none!important;}
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarContent"]{overflow:hidden;padding:12px 0 0!important;}
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNav"],
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavItems"] li,
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavLinkContainer"]{width:100%!important;padding:0!important;margin:0!important;}
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavLink"]{width:40px;height:40px;padding:0!important;margin:2px auto;justify-content:center;align-items:center;border-radius:8px;}
section[data-testid="stSidebar"][data-collapsed="true"] [data-testid="stSidebarNavLink"] > span{margin:0!important;}
.hero{background:var(--ink);color:#fff;border-radius:10px;padding:30px 34px 26px;border-bottom:6px solid var(--gold);margin-bottom:10px;}
.hero-title{font-family:'Barlow Semi Condensed','Barlow',sans-serif;font-weight:700;font-size:3.1rem;line-height:1.08;letter-spacing:.2px;margin-bottom:8px;}
.hero-sub{font-size:1.18rem;line-height:1.45;max-width:46rem;margin:.6rem 0 0;color:#DCE6F5;}
.demo-note{display:inline-block;margin-top:16px;background:#fff;color:var(--ink);font-weight:600;border-radius:6px;padding:6px 12px;font-size:.95rem;}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px;}
.legend div{flex:1 1 220px;font-size:.95rem;color:var(--muted);line-height:1.35;}
.chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.85rem;font-weight:600;margin-right:6px;border:1.5px solid;white-space:nowrap;}
.chip.conf{background:var(--ink);color:#fff;border-color:var(--ink);}
.chip.est{background:#fff;color:var(--blue);border:1.5px dashed var(--blue);}
.chip.act{background:#FFF4D6;color:#6B4A00;border-color:#E7B84A;}
h2.q{font-family:'Barlow Semi Condensed','Barlow',sans-serif;font-weight:700;font-size:2.05rem;line-height:1.1;margin:18px 0 6px;color:var(--ink);}
h3.sq{font-family:'Barlow Semi Condensed','Barlow',sans-serif;font-weight:600;font-size:1.3rem;margin:18px 0 4px;color:var(--ink);}
.panel{background:#fff;border:1px solid var(--line);border-radius:8px;padding:18px 22px;margin:10px 0;}
.panel.est{border:1.5px dashed var(--blue);}
.bandname{font-family:'Barlow Semi Condensed','Barlow',sans-serif;font-weight:700;font-size:2.6rem;line-height:1;}
.sub{color:var(--muted);font-size:1rem;margin:6px 0 16px;}
.gauge-wrap{margin:6px 0 4px;}
.gauge{position:relative;display:flex;height:20px;gap:3px;}
.seg{flex:1;border-radius:3px;opacity:.38;}
.seg.on{opacity:1;}
.marker{position:absolute;top:-9px;width:5px;height:38px;background:var(--ink);border:2px solid #fff;border-radius:3px;transform:translateX(-50%);box-shadow:0 0 0 1px var(--ink);}
.labs{display:flex;gap:3px;margin-top:8px;}
.lab{flex:1;text-align:center;font-size:.95rem;color:var(--muted);}
.lab.on{color:var(--ink);font-weight:700;text-decoration:underline;text-underline-offset:4px;}
.conf-row{display:flex;align-items:center;gap:10px;margin:14px 0 2px;font-weight:600;}
.dots{display:inline-flex;gap:4px;}
.dots i{width:12px;height:12px;border-radius:50%;border:2px solid var(--ink);display:inline-block;}
.dots i.f{background:var(--ink);}
ul.why{margin:6px 0 0;padding-left:0;list-style:none;}
ul.why li{padding:7px 0 7px 0;border-top:1px solid #E4EAF3;line-height:1.4;}
ul.why li:first-child{border-top:none;}
b.up{color:#A04A0B;} b.down{color:#1E5F3C;} b.neutral{color:var(--muted);}
.big{font-family:'Barlow Semi Condensed','Barlow',sans-serif;font-weight:700;font-size:2.8rem;line-height:1.05;color:var(--ink);}
.confirmed{margin-top:12px;padding-top:10px;border-top:1px solid #E4EAF3;color:var(--muted);font-size:.98rem;}
.safety{background:#FDECEA;border:2px solid #B3261E;color:#4A0D08;border-radius:8px;padding:14px 18px;margin:8px 0;}
.safety .head{font-weight:700;font-size:1.1rem;margin-bottom:6px;color:#8F1B14;}
.safety ul{margin:6px 0 0 18px;padding:0;}
.emerg{background:#8F1B14;color:#fff;border-radius:6px;padding:8px 12px;font-weight:600;margin-bottom:8px;}
table.t{width:100%;border-collapse:collapse;font-size:.98rem;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden;}
table.t th{background:var(--sky);text-align:left;padding:9px 12px;font-weight:600;}
table.t td{padding:9px 12px;border-top:1px solid #E4EAF3;vertical-align:top;}
.st-yes{font-weight:700;color:#1E5F3C;} .st-todo{font-weight:700;color:#A04A0B;} .st-no{font-weight:700;color:var(--muted);}
.phone{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px 18px;max-width:560px;line-height:1.45;font-size:1.02rem;}
.meta{color:var(--muted);font-size:.93rem;margin:6px 2px;}
.where{background:var(--sky);border-radius:8px;padding:10px 14px;margin:8px 0 2px;font-size:1rem;}
.fallback{background:#FFF8E6;border:2px solid #E7B84A;border-radius:8px;padding:16px 20px;margin:10px 0;}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 18px;height:100%;}
.card .k{color:var(--muted);font-size:.95rem;margin-bottom:4px;}
.card .v{font-family:'Barlow Semi Condensed','Barlow',sans-serif;font-weight:700;font-size:1.7rem;line-height:1.1;}
@media (max-width:640px){.hero-title{font-size:2.3rem;}.big{font-size:2.1rem;}.bandname{font-size:2rem;}}
</style>
"""


def H(s: str) -> str:
    """Collapse HTML to one line so Streamlit's markdown never treats it as a code block."""
    return "".join(line.strip() for line in s.strip().splitlines())


def html(s: str):
    st.markdown(H(s), unsafe_allow_html=True)


def chip(kind: str) -> str:
    labels = {"conf": "Confirmed by the utility", "est": "Model estimate", "act": "What you can do"}
    return f'<span class="chip {kind}">{labels[kind]}</span>'


def heading(text: str, kind: str):
    html(f'<h2 class="q">{esc(text)}</h2><div>{chip(kind)}</div>')


def fmt_hid(h: str) -> str:
    m = len(h) // 2
    return f"{h[:m]}-{h[m:]}"


@st.cache_data
def load():
    prem = pd.read_csv(DATA / "premises.csv.gz", dtype={"hid": str})
    circ = pd.read_csv(DATA / "circuits.csv").set_index("circuit")
    meta = json.loads((DATA / "meta.json").read_text())
    prem["pct"] = prem.circuit.map(circ.pct)
    prem = prem.set_index("hid", drop=False)
    return prem, circ, meta


prem, circ, meta = load()
personas = meta["personas"]
ss = st.session_state


# ---------------------------------------------------------------- state
def init_state():
    if "hid" not in ss:
        ss.hid = personas[0]["hid"]
        ss.medical = False  # never assumed; only the user (or a demo customer) declares it
        ss.sev = "Major storm"
        ss.enrolled = False
        ss.name = ""
        ss.onboarded = False
    # The sidebar widgets own these keys; re-assigning keeps them while the sidebar is hidden (details page).
    for k in ("sev", "medical", "enrolled"):
        ss[k] = ss[k]


def pick_persona(i: int):
    ss.hid = personas[i]["hid"]
    ss.medical = personas[i]["medical"]
    ss.name = personas[i]["name"]


def kept_slider(col, label: str, lo: int, hi: int, default: int, key: str) -> int:
    """A slider whose value survives page changes (Streamlit drops widget state for widgets not on the current page)."""
    wk = "_w_" + key
    if key not in ss:
        ss[key] = default
    ss[wk] = ss[key]
    col.slider(label, lo, hi, key=wk, on_change=lambda: ss.__setitem__(key, ss[wk]))
    return ss[key]


# ---------------------------------------------------------------- sidebar
def sidebar():
    with st.sidebar:
        who = ss.name or "Your home"
        if ss.hid == "NONE":
            where = "outside our data"
        elif ss.hid in prem.index:
            where = f"{prem.loc[ss.hid].city}, {prem.loc[ss.hid].road}"
        else:
            where = ""
        st.markdown(f"### {who}")
        st.caption(where)
        st.page_link("views/welcome.py", label="Change my details", icon=":material/edit:")
        st.markdown("**Demo customers** (names are fictional)")
        pc = st.columns(len(personas))
        for i, p in enumerate(personas):
            pc[i].button(p["name"], key=f"persona{i}", on_click=pick_persona, args=(i,),
                         use_container_width=True, type="primary" if (ss.hid == p["hid"] and ss.name == p["name"]) else "secondary")
        current = next((p for p in personas if p["hid"] == ss.hid and p["name"] == ss.name), None)
        if current:
            st.caption(current["blurb"])
        st.radio("Storm scenario", engine.SEV_ORDER, key="sev")
        st.caption(engine.SEVERITIES[ss.sev]["blurb"])
        st.checkbox("Medical equipment at home", key="medical", help="You are declaring this. We never guess it from your address or account.")
        st.checkbox("I'm signed up for outage alerts", key="enrolled")


# ---------------------------------------------------------------- shared sections
def safety_box():
    html(f'<div class="safety"><div class="emerg">{esc(engine.EMERGENCY)}</div><div class="head">Staying safe</div><ul>'
         + "".join(f"<li>{esc(s)}</li>" for s in engine.SAFETY) + "</ul></div>")


def limits_text():
    bt = meta["backtest"]
    st.markdown(f"""
**Data used.** {meta['premises']:,} anonymized premises on {meta['circuits']} circuits in the Roanoke, Virginia area; \
{meta['storm_records']:,} damage records from one storm ({meta['storm_window']}); the premise-to-equipment topology file; \
and the labor-hour workbook (hours by equipment type, access adders, and a {engine.ILM}x indirect labor multiplier for travel, safety talks and setup).

**What is missing.** Only one major storm. No weather data. No customer outage counts, so we cannot train or score a true "did this home lose power" model. \
Damage dates are whole days, not hours. The workbook has no wire-repair hours, so a wire repair is built from connector, dead-end, insulator and pin hours.

**How the risk score works.** A weighted exposure score from four things: how many damage reports your circuit had per customer \
(45%), whether equipment that feeds your home was damaged last time (25%), overhead or underground service (20%), and how many protective devices sit \
between you and the substation (10%). The storm scenario scales it. It ranks homes; it is not a percent chance. In the Feb 2025 storm, \
{meta['direct_hit_share']:.1%} of premises sat directly downstream of a damaged fuse or transformer, and {meta['circuit_exposed_share']:.0%} were on a circuit with at least one damage report.

**How the restoration range works.** Damaged items on your circuit, times labor hours for each repair type, times {engine.ILM} for travel and setup, \
divided by the workers on the circuit, plus rest between shifts and time waiting for crews. The range is wide on purpose. \
Two assumptions (about one crew per {engine.ITEMS_PER_CREW} damaged items, and about a day of queue time in a major storm) were tuned to the Feb 2025 storm. \
On that same storm, the range contained the observed finish day for {bt['overlap']} of {bt['circuits']} circuits ({bt['share']:.0%}). \
That was tuned on, not independently tested.

**Privacy.** Premise numbers become a random one-way code. House numbers, coordinates, customer names and the utility's life-support flag are never shown. \
Medical needs are only used when you declare them here.

**When a person takes over.** Low confidence, a location outside our data, two missed estimates in a row, an outage past 24 hours (12 with a declared medical need), \
or any emergency.

**Not a promise.** Only the utility can confirm a restoration time.
""")


def footer():
    st.markdown("---")
    st.caption("Built for the Hack/OHIO 2026 AEP challenge from the organizer's sanitized sample data. "
               "Customer names are fictional. Estimates are not confirmed utility information.")


def next_page(path: str, label: str):
    st.page_link(path, label=label, icon=":material/arrow_forward:")


def fallback_page():
    html("""
<h2 class="q">We can't give you a reliable estimate here</h2>
<div class="fallback"><b>This location is not in the data we have, so we won't guess.</b><br>
What to do now: call your utility's outage line or check its outage map for confirmed information, and use the safety steps below.
In this system, a person would pick this conversation up.</div>
""")
    safety_box()
    for title, items in engine.prep("Moderate", 12, ss.medical):
        st.markdown(f"**{title}**")
        st.markdown("\n".join(f"- {i}" for i in items))
    footer()
    st.stop()


# ---------------------------------------------------------------- per-location numbers
def context(show_where: bool = True) -> SimpleNamespace:
    """Everything the pages need for the current location, scenario and slider settings.

    Shows the fallback page and stops if the location is outside our data.
    """
    if ss.hid == "NONE" or ss.hid not in prem.index:
        fallback_page()
    p = prem.loc[ss.hid]
    c = circ.loc[int(p.circuit)]
    sev = ss.sev
    res = engine.risk(p.pct, p.hit25, p.svc, p.devs, p.chain_ok, sev)
    conf, _ = engine.confidence(c.dmg, p.chain_ok, p.svc, sev)
    band = res["band"]

    mix = {k: float(c["mix_" + k]) for k in engine.CATS}
    d_items = max(1, round(float(c.base_items) * engine.SEVERITIES[sev]["dmg"]))
    suffix = f"{int(p.circuit)}_{sev}"
    keys = {"items": f"items_{suffix}", "crews": f"crews_{suffix}", "access": f"acc_{suffix}"}
    items = ss.get(keys["items"], int(d_items))
    crews = ss.get(keys["crews"], engine.default_crews(items))
    access = ss.get(keys["access"], int(round(float(c.access_share) * 100)))

    ctx = SimpleNamespace(p=p, c=c, sev=sev, res=res, conf=conf, band=band, mix=mix, d_items=d_items, keys=keys)
    set_restoration(ctx, items, crews, access)

    if show_where:
        svc_txt = {"Overhead": "overhead service", "Underground": "underground service"}.get(p.svc, "service type unknown")
        html(f'<div class="where">Showing results for <b>Location {esc(fmt_hid(p.hid))}</b> in the {esc(p.city)} area, '
             f'<b>Circuit {int(p.circuit)}</b>, {svc_txt}, {esc(sev.lower())} scenario.</div>')
    return ctx


def set_restoration(ctx: SimpleNamespace, items: int, crews: int, access: int):
    """Work out the restoration range for the given slider values and store it on ctx."""
    c, sev, mix = ctx.c, ctx.sev, ctx.mix
    base, whatifs = engine.what_if(items, mix, access / 100, float(c.special_share), crews, sev)
    prev = engine.restore(max(1, items * 0.6), mix, access / 100, float(c.special_share), crews, sev)
    ctx.items, ctx.crews, ctx.access = items, crews, access
    ctx.base, ctx.whatifs = base, whatifs
    ctx.rng = engine.fmt_range(base["lo_h"], base["hi_h"])
    ctx.prev_rng = engine.fmt_range(prev["lo_h"], prev["hi_h"])
