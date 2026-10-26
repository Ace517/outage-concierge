import streamlit as st

import ui
from ui import esc, html

meta = ui.meta

html("""
<div class="hero">
<div style="color:var(--gold);font-weight:700;letter-spacing:.06em;font-size:.9rem;margin-bottom:6px">HACKOHI/O 2026 · AEP CHALLENGE</div>
<div class="hero-title">AI Outage Concierge</div>
<p class="hero-sub">A storm assistant for one home. Before, during and after a storm, it answers the three questions customers actually ask, in plain language.</p>
<div class="demo-note">A prototype built on the organizers' sample data. Not endorsed or used by AEP.</div>
</div>
""")

cards = [
    ("Will I lose power?", "A risk band from Low to Very high, a confidence rating, and the three reasons behind it."),
    ("How long could it last?", "A restoration range in hours, with sliders to test what-ifs and every step of the math shown."),
    ("What should I do?", "Safety steps, a prep checklist for your situation, alert eligibility, and the texts we would send."),
]
cols = st.columns(3)
for col, (q, a) in zip(cols, cards):
    with col:
        html(f'<div class="card"><div class="v" style="font-size:1.35rem">{esc(q)}</div>'
             f'<div class="k" style="margin-top:8px;font-size:1rem">{esc(a)}</div></div>')

html('<h2 class="q">How to try it</h2>')
st.markdown("""
1. **Pick a home** on the next page (city, street and an anonymous home code), or tap a **demo customer**:
   Maria, Devon, Priya or David each show a different situation.
2. **Choose a storm scenario**, from Breezy to Extreme. Every page and the map update to match.
3. **Explore the pages** in the sidebar: your outlook, the outage map, risk, restoration time, prep, alerts and messages.
   Try dragging the crew slider on "How long will it last?".
""")

left, right = st.columns(2, gap="large")
with left:
    html('<h3 class="sq">Built on real utility data</h3>')
    st.markdown(f"""
- **{meta['premises']:,} anonymized homes** on {meta['circuits']} circuits around Roanoke, Vinton and Salem, Virginia
- **{meta['storm_records']:,} damage records** from the {meta['storm_window']} storm
- The equipment map, the chain of devices feeding each home, and AEP's **labor-hour workbook**
""")
with right:
    html('<h3 class="sq">Honest by design</h3>')
    st.markdown("""
- Every number is an **estimate shown as a range**, never a promise
- **No house numbers, coordinates or names**; the map only shows neighborhoods
- Medical needs are **never guessed**; only you can declare them
- Outside our data, or when we're unsure, it **says so and hands you to a person**
""")

html('<h3 class="sq">Who made it</h3>')
st.markdown("**Team Rio Ganga**, Ohio State: Darsh Patel, Pranav Kottagi, Shishir Joshi and Lucas Teitelbaum.")
st.caption('Want the details? "How this works" in the sidebar explains the method, the data and its limits.')

if st.button("Get started", type="primary"):
    st.switch_page("views/welcome.py")
ui.footer()
