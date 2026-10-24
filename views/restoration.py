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
st.caption(f"For comparison, in the Feb 2025 storm half of repairs finished within {ui.meta['repair_days_p50'] * 24:g} hours and 90% within "
           f"{ui.meta['repair_days_p90'] * 24:g} hours (the records only give whole days). Crews often restore power in steps, "
           "so you may be back before the full circuit is done.")
with st.expander("How we got this number"):
    sev_cfg = engine.SEVERITIES[ctx.sev]
    shifts = int(base["work_h"] // engine.SHIFT_H)
    st.markdown(f"""
Every number below follows your current slider settings and the **{esc(ctx.sev)}** scenario.

1. **Damaged items: {items}.** We start from the damage your circuit had in the Feb 2025 storm, scaled by
   {sev_cfg['dmg']:g}x for this scenario ({ctx.d_items} items). The first slider changes it.
2. **Labor per item: {base['each_h'] + base['adder_h']:.2f} hours.** That's {base['each_h']:.2f} hours for the mix of repair types on
   your circuit (table below), plus {base['adder_h']:.2f} hours on average for hard-to-reach and special-equipment jobs
   (each such job adds {engine.ADDER_ACCESS:g} hours, from the workbook).
   {items} items x {base['each_h'] + base['adder_h']:.2f} hours = **{base['direct_h']:.0f} labor hours**.
3. **Travel, safety talks and setup: x {engine.ILM:g}** (the workbook's indirect labor multiplier)
   = **{base['on_clock_h']:.0f} on-the-clock hours**.
4. **Split across the crews: / {base['workers']} workers** ({crews} crews of {engine.CREW_SIZE}). By default we assume about one crew per
   {engine.ITEMS_PER_CREW} damaged items ({engine.MIN_CREWS} to {engine.MAX_CREWS} crews); the second slider changes it.
   = **{base['work_h']:.0f} hours of work**.
5. **Rest between shifts: + {engine.REST_H} hours** after each {engine.SHIFT_H}-hour shift ({shifts} rest{'s' if shifts != 1 else ''})
   = **{base['elapsed_h']:.0f} hours on site**.
6. **Assessing damage and waiting for crews: + {base['mob_h']} hours** in this scenario
   = **about {base['mid_h']:.0f} hours** (our middle estimate).
7. **The range.** Low end: 60% of the middle = {base['lo_h']:.0f} hours. High end: the middle x
   (1.4 + 0.6 x your hard-to-reach share of {ctx.access}%) + 12 hours = {base['hi_h']:.0f} hours.
   Rounded outward to whole hours, 6-hour or 12-hour steps: **{ctx.rng}**.

The crew numbers and the waiting time were tuned so the range matched the Feb 2025 storm. Only the utility can confirm a time.
""")
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{engine.BUNDLE_H[k]:.2f}</td><td>{ctx.mix[k]:.0%}</td><td>{esc(engine.BUNDLE_NOTE[k])}</td></tr>"
                   for k in engine.CATS)
    html(f'<table class="t"><tr><th>Repair type</th><th>Labor hours each</th><th>Share on your circuit</th><th>Source</th></tr>{rows}</table>')

ui.next_page("views/prepare.py", "Next: how do I prepare?")
ui.footer()
