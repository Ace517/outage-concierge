import streamlit as st

import engine
import ui
from ui import esc, html

ctx = ui.context()
enrolled = ui.ss.enrolled

ui.heading("Do I qualify for outage alerts?", "act")
rules, plan, triggers = engine.alerts(ctx.band, ui.ss.medical, enrolled, ctx.conf)
label = {"yes": ("Yes", "st-yes"), "todo": ("Not yet", "st-todo"), "no": ("No", "st-no")}
if enrolled:
    html('<div class="panel"><b>Yes. You qualify, and you are signed up.</b> Here is what you would get.</div>')
else:
    html('<div class="panel"><b>Yes, you qualify. One step left: sign up.</b> Alerts are opt-in. '
         'Tick "I\'m signed up for outage alerts" in the sidebar to mark yourself as signed up.</div>')
rr = "".join(f'<tr><td>{esc(a)}</td><td class="{label[s][1]}">{label[s][0]}</td><td>{esc(d)}</td></tr>' for a, s, d in rules)
html(f'<table class="t"><tr><th>Rule</th><th>Met?</th><th>Details</th></tr>{rr}</table>')
st.caption("These rules are challenge assumptions modeled on opt-in text and email outage alerts. The utility's own terms decide your real eligibility.")
html('<h3 class="sq">When, where and how we would reach you</h3>')
pr = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(d)}</td></tr>" for a, b, d in plan)
html(f'<table class="t"><tr><th>Message</th><th>Timing</th><th>Channel</th></tr>{pr}</table>')
html('<h3 class="sq">When a person steps in</h3>')
st.markdown("\n".join(f"- {t}" for t in triggers))

ui.next_page("views/messages.py", "Next: the messages we would send")
ui.footer()
