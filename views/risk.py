import streamlit as st

import engine
import ui
from ui import esc, html

ctx = ui.context()
p, c, res, conf, band, sev = ctx.p, ctx.c, ctx.res, ctx.conf, ctx.band, ctx.sev

ui.heading("Will I lose power?", "est")
if conf == "Low":
    html("""
<div class="fallback"><b>We don't have enough data to rate your risk reliably.</b><br>
Treat an outage as possible, follow the steps on the prepare page, and use your utility's outage line for confirmed information.
A person would follow up in this system.</div>
""")
else:
    dots = {"High": 3, "Medium": 2, "Low": 1}[conf]
    dots_html = "".join(f'<i class="{"f" if k < dots else ""}"></i>' for k in range(3))
    gauge_segs = "".join(f'<div class="seg {"on" if b == band else ""}" style="background:{ui.BAND_FILL[b]}"></div>'
                         for b in engine.BAND_ORDER)
    gauge_labs = "".join(f'<div class="lab {"on" if b == band else ""}">{b}</div>' for b in engine.BAND_ORDER)
    rs = engine.reasons(res, c.dmg, c.dpk, p.svc, p.devs, bool(p.chain_ok), bool(p.hit25))
    verb = {"up": "Raises your risk.", "down": "Lowers your risk.", "neutral": "No effect."}
    why = "".join(f'<li><b class="{r["dir"]}">{verb[r["dir"]]}</b> {esc(r["text"])}</li>' for r in rs)
    html(f"""
<div class="panel est" style="border-left:8px solid {ui.BAND_FILL[band]}">
<div class="bandname" style="color:{ui.BAND_TEXT[band]}">{band} risk</div>
<div class="sub">Exposure score {res['score']} out of 100 in a {esc(sev.lower())} scenario. A relative ranking, not a percent chance.</div>
<div class="gauge-wrap" role="img" aria-label="Outage risk is {band}. Score {res['score']} out of 100.">
<div class="gauge">{gauge_segs}<div class="marker" style="left:{min(max(res['score'], 0), 100)}%"></div></div>
<div class="labs">{gauge_labs}</div></div>
<div class="conf-row"><span class="dots" aria-hidden="true">{dots_html}</span><span>{conf} confidence</span></div>
<h3 class="sq">Why</h3>
<ul class="why">{why}</ul>
</div>
""")
    with st.expander("What could change this answer"):
        for cv in engine.caveats(sev, bool(p.chain_ok), p.svc, c.dmg):
            st.markdown(f"- {cv}")

ui.next_page("views/restoration.py", "Next: how long could it last?")
ui.footer()
