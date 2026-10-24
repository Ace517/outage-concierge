import streamlit as st

import engine
import ui
from ui import esc, html

ctx = ui.context()

ui.heading("What should I do to prepare?", "act")
ui.safety_box()
if ui.ss.medical:
    st.info("You declared a medical need, so we added steps for it. We never guess this from your address or account.")
groups = engine.prep(ctx.band if ctx.conf != "Low" else "Moderate", ctx.base["mid_h"], ui.ss.medical)
gcols = st.columns(2, gap="large")
for gi, (title, its) in enumerate(groups):
    with gcols[gi % 2]:
        html(f'<h3 class="sq">{esc(title)}</h3>')
        st.markdown("\n".join(f"- {i}" for i in its))

ui.next_page("views/alerts.py", "Next: do I qualify for outage alerts?")
ui.footer()
