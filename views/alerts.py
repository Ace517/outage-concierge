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
    to = ui.masked_phone()
    where = f"Texts go to <b>{esc(to)}</b>." if to else "Demo customer: no phone number on file."
    html(f'<div class="panel"><b>Yes. You qualify, and you are signed up.</b> {where} Here is what you would get.</div>')
    st.button("Stop alerts", on_click=ui.stop_alerts)
else:
    html('<div class="panel"><b>Yes, you qualify. One step left: sign up.</b> Alerts are opt-in.</div>')
    with st.form("alert_signup", border=True):
        html('<h3 class="sq" style="margin-top:2px">Sign up for outage texts</h3>')
        st.text_input("Mobile number", key="alert_phone_input", max_chars=20, placeholder="(614) 555-0123")
        st.checkbox("Text me outage alerts for this home. Message and data rates may apply. Reply STOP to opt out.",
                    key="alert_consent")
        st.form_submit_button("Sign up for alerts", type="primary", on_click=ui.sign_up_alerts)
    if ui.ss.get("alert_err"):
        st.error(ui.ss.alert_err)
    st.caption("Demo: we check the number, then keep only its last 4 digits in this browser tab to confirm your sign-up. "
               "Nothing is saved or sent, and no real text is delivered.")
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
