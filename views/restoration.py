import streamlit as st

import engine
import ui
from ui import esc, html

ctx = ui.context()
c, keys = ctx.c, ctx.keys

ui.heading("How long could restoration take?", "est")
st.caption("Move the sliders to test what-ifs. The estimate updates right away, and the other pages use these settings too.")
s1, s2, s3 = st.columns(3)
items = ui.kept_slider(s1, "Damaged items on your circuit", 1, int(max(40, ctx.d_items * 3)), int(ctx.d_items), keys["items"])
crews = ui.kept_slider(s2, "Crews working your circuit", 1, 20, engine.default_crews(items), keys["crews"])
access = ui.kept_slider(s3, "Repairs that are hard to reach (%)", 0, 100, int(round(float(c.access_share) * 100)), keys["access"])
ui.set_restoration(ctx, items, crews, access)
base = ctx.base

wi = "".join(f"<tr><td>{esc(a)}</td><td><b>{esc(b)}</b></td></tr>" for a, b in ctx.whatifs)
low_note = " Your own risk is low, so this applies only if you do lose power." if (ctx.band == "Low" and ctx.conf != "Low") else ""
html(f"""
<div class="panel est">
<div class="big">{ctx.rng}</div>
<div>Our estimate for when most customers on your circuit are back on. It is a range because storm repair is uncertain.{low_note}</div>
<div class="confirmed"><b>Confirmed restoration time from the utility:</b> none. This demo has no live utility data, and only the utility can confirm a time.</div>
</div>
<table class="t"><tr><th>What could move it</th><th>New estimate</th></tr>{wi}</table>
""")
st.caption(f"For comparison, in the Feb 2025 storm half of repairs finished within {ui.meta['repair_days_p50']:g} day and 90% within "
           f"{ui.meta['repair_days_p90']:g} days (day-level records). Crews often restore power in steps, so you may be back before the full circuit is done.")
with st.expander("How we got this number"):
    st.markdown(f"""
- {items} damaged items x {base['each_h'] + base['adder_h']:.1f} labor hours each (repair mix on your circuit, plus access adders) = **{base['direct_h']:.0f} labor hours**
- x {engine.ILM} for travel, safety talks and setup = **{base['on_clock_h']:.0f} on-the-clock hours**
- / {base['workers']} workers ({crews} crews of {engine.CREW_SIZE}) = **{base['work_h']:.0f} hours of work**, plus {engine.REST_H}-hour rests between {engine.SHIFT_H}-hour shifts = **{base['elapsed_h']:.0f} hours elapsed**
- + {base['mob_h']} hours to assess damage and wait for crews = **about {base['mid_h']:.0f} hours** in the middle
- Range: {base['lo_h']:.0f} to {base['hi_h']:.0f} hours, wider when access is harder.
""")
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{engine.BUNDLE_H[k]:.2f}</td><td>{ctx.mix[k]:.0%}</td><td>{esc(engine.BUNDLE_NOTE[k])}</td></tr>"
                   for k in engine.CATS)
    html(f'<table class="t"><tr><th>Repair type</th><th>Hours each</th><th>Share on your circuit</th><th>Source</th></tr>{rows}</table>')

ui.next_page("views/prepare.py", "Next: how do I prepare?")
ui.footer()
