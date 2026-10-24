import streamlit as st

import engine
import ui
from ui import esc, html, personas, prem, ss

html("""
<div class="hero">
<div class="hero-title">AI Outage Concierge</div>
<p class="hero-sub">Tell us about your home and we'll answer three questions: will you lose power, how long could it last, and what should you do about it?</p>
<div class="demo-note">Demo with sample data. No account or password. Nothing you enter here is saved.</div>
</div>
""")

# Start from whatever the user chose last time (these widget keys are dropped when they leave this page).
here = prem.loc[ss.hid] if ss.hid in prem.index else None
for k, v in {"w_name": ss.get("name", ""), "w_sev": ss.sev, "w_medical": ss.medical, "w_enrolled": ss.enrolled,
             "w_outside": ss.hid == "NONE"}.items():
    if k not in ss:
        ss[k] = v
cities = [c for c in prem.city.value_counts().index if c != ui.NO_TOWN]
if (prem.city == ui.NO_TOWN).any():
    cities.append(ui.NO_TOWN)
if "w_city" not in ss:
    ss.w_city = here.city if here is not None else cities[0]

left, right = st.columns([3, 2], gap="large")

with left:
    with st.container(border=True):
        html('<h3 class="sq" style="margin-top:2px">Your details</h3>')
        st.text_input("First name (optional)", key="w_name", max_chars=40, placeholder="e.g. Maria",
                      help="Only used to greet you. It stays in this browser tab.")
        outside = st.checkbox("My city isn't listed", key="w_outside")
        city = st.selectbox("City", cities, key="w_city", disabled=outside)
        roads = sorted(prem[prem.city == city].road.unique())
        road_key = f"w_road_{city}"
        if road_key not in ss and here is not None and here.city == city:
            ss[road_key] = here.road
        road = st.selectbox("Street", roads, key=road_key, disabled=outside)
        homes = sorted(prem[(prem.city == city) & (prem.road == road)].hid)[:40]
        if here is not None and here.hid not in homes and here.city == city and here.road == road:
            homes = [here.hid] + homes
        home_key = f"w_home_{city}_{road}"
        if home_key not in ss and here is not None and here.hid in homes:
            ss[home_key] = here.hid
        st.selectbox("Your home", homes, key=home_key, disabled=outside, format_func=lambda h: f"Home {ui.fmt_hid(h)}",
                     help="We never show house numbers, so homes appear as anonymous codes. In a real app this would come from your account.")
        st.radio("Storm scenario", engine.SEV_ORDER, key="w_sev", horizontal=True)
        st.checkbox("Someone at home uses medical equipment", key="w_medical",
                    help="You are declaring this. We never guess it from your address or account.")
        st.checkbox("I'm signed up for outage alerts", key="w_enrolled")
        go = st.button("See my outage outlook", type="primary", use_container_width=True)

with right:
    with st.container(border=True):
        html('<h3 class="sq" style="margin-top:2px">Or try a demo customer</h3>')
        st.caption("Names are fictional. Each one shows a different situation.")
        demo = None
        for i, p in enumerate(personas):
            if st.button(p["name"], key=f"demo{i}", use_container_width=True):
                demo = i
            st.caption(p["blurb"])
    st.caption("Privacy: we use your street and an anonymous home code, never your house number or exact location. "
               "Medical steps appear only if you tick the box.")

if go:
    ss.name = ss.w_name.strip()
    ss.hid = "NONE" if outside else ss[home_key]
    ss.sev, ss.medical, ss.enrolled = ss.w_sev, ss.w_medical, ss.w_enrolled
    ss.onboarded = True
    st.switch_page("views/overview.py")
if demo is not None:
    ui.pick_persona(demo)
    ss.onboarded = True
    st.switch_page("views/overview.py")
