import streamlit as st

import ui
from ui import chip, esc, html

html("""
<div class="hero">
<div class="hero-title">AI Outage Concierge</div>
<p class="hero-sub">Will you lose power, how long could it last, and what should you do about it? Plain answers for one home, before, during and after a storm.</p>
<div class="demo-note">Demo with sample data. Nothing on this page is live utility information.</div>
</div>
""")
html(f"""
<div class="legend">
<div>{chip("conf")}<br>Facts the utility has verified. This demo has none, so this tag marks where live data would appear.</div>
<div>{chip("est")}<br>Our best guess. Always shown as a range, with a dashed outline.</div>
<div>{chip("act")}<br>Steps you can take.</div>
</div>
""")
ctx = ui.context()
greet = f"Hi {ui.ss.name}, here's your storm outlook" if ui.ss.name else "Your storm outlook"
html(f'<h2 class="q">{esc(greet)}</h2>')
st.caption("Change the storm scenario in the sidebar, or use \"Change my details\". Every page updates to match.")
risk_txt = "Not enough data" if ctx.conf == "Low" else f"{ctx.band} risk"
risk_color = "var(--ink)" if ctx.conf == "Low" else ui.BAND_TEXT[ctx.band]
alerts_txt = "Signed up" if ui.ss.enrolled else "Qualifies, not signed up"

cards = [
    ("Will I lose power?", risk_txt, risk_color, "views/risk.py"),
    ("How long could it last?", ctx.rng, "var(--ink)", "views/restoration.py"),
    ("Outage alerts", alerts_txt, "var(--ink)", "views/alerts.py"),
]
cols = st.columns(3)
for col, (k, v, color, path) in zip(cols, cards):
    with col:
        html(f'<div class="card"><div class="k">{esc(k)}</div><div class="v" style="color:{color}">{esc(v)}</div></div>')
        st.page_link(path, label="See details", icon=":material/arrow_forward:")

ui.footer()
