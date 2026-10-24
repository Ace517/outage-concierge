"""AI Outage Concierge - Hack/OHIO 2026 AEP challenge prototype.

Run:  streamlit run app.py
All logic lives in engine.py. Shared layout is in ui.py, and each page is a file in views/.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="AI Outage Concierge", page_icon="⚡", layout="wide")

import ui  # noqa: E402  (set_page_config must run first)

ui.init_state()
ui.html(ui.CSS)

welcome = st.Page("views/welcome.py", title="Your details", icon=":material/person:", url_path="welcome")
pg = st.navigation([
    st.Page("views/overview.py", title="Overview", icon=":material/home:", default=True),
    st.Page("views/risk.py", title="Will I lose power?", icon=":material/bolt:"),
    st.Page("views/restoration.py", title="How long will it last?", icon=":material/schedule:"),
    st.Page("views/prepare.py", title="How do I prepare?", icon=":material/checklist:"),
    st.Page("views/alerts.py", title="Outage alerts", icon=":material/notifications:"),
    st.Page("views/messages.py", title="Messages we send", icon=":material/sms:"),
    st.Page("views/about.py", title="How this works", icon=":material/info:"),
    welcome,
], position="sidebar" if ui.ss.onboarded else "hidden")

# Everyone starts on the details page.
if not ui.ss.onboarded and pg.url_path != "welcome":
    st.switch_page(welcome)
if pg.url_path != "welcome":
    ui.sidebar()
pg.run()
