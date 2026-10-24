import streamlit as st

import engine
import ui
from ui import esc, html

ctx = ui.context()

ui.heading("What we would send you", "est")
st.caption("These use the restoration range from the sliders on the \"How long will it last?\" page.")
msgs = engine.messages(ctx.band, ctx.rng, ctx.prev_rng, ui.ss.medical, ctx.p.city, ctx.sev)
tabs = st.tabs([m["title"] for m in msgs])
for tab, m in zip(tabs, msgs):
    with tab:
        html(f'<div class="phone">{esc(m["text"])}</div><div class="meta">{len(m["text"])} characters. Sent: {esc(m["when"])}. Channel: {esc(m["channel"])}.</div>')

ui.next_page("views/about.py", "Next: how this works and what it can't do")
ui.footer()
