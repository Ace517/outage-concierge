"""engine.py - all scoring, restoration, alert and message logic. No UI code.

Every number here is one of two things:
  1. copied from the AEP-supplied labor workbook (Install_Labor_HackOHIO.xlsx), or
  2. a labeled assumption (marked ASSUMPTION) that the app shows to the user.

The data contains ONE major storm (Feb 12-18, 2025), no weather, and no customer
outage counts, so nothing here is a trained model. It is a transparent scoring
rule that a nontechnical person can read and challenge.
"""
from __future__ import annotations

import math

# --------------------------------------------------------------------------
# Storm scenarios.  ASSUMPTION: "Major storm" = the Feb 2025 storm in the data.
# --------------------------------------------------------------------------
SEVERITIES = {
    "Breezy": {
        "blurb": "Gusty day. A few branches down.",
        "dmg": 0.10, "risk": 0.35, "mob_h": 6, "phrase": "gusty day",
    },
    "Strong wind": {
        "blurb": "Damaging gusts and some downed limbs.",
        "dmg": 0.40, "risk": 0.65, "mob_h": 12, "phrase": "strong wind event",
    },
    "Major storm": {
        "blurb": "About as bad as the Feb 2025 storm in our data.",
        "dmg": 1.00, "risk": 1.00, "mob_h": 24, "phrase": "major storm",
    },
    "Extreme": {
        "blurb": "Derecho-class. Worse than anything in our data.",
        "dmg": 2.00, "risk": 1.25, "mob_h": 36, "phrase": "severe storm system",
    },
}
SEV_ORDER = list(SEVERITIES)
OBSERVED_SEV = "Major storm"

# --------------------------------------------------------------------------
# Labor reference (install + removal hours, from Install_Labor_HackOHIO.xlsx)
# --------------------------------------------------------------------------
ILM = 4.5            # Indirect Labor Multiplier: drive time, safety talk, setup (workbook)
ADDER_ACCESS = 0.5   # Access Constraint Adder, hours per affected repair (workbook)
ADDER_SPECIAL = 0.5  # Specialized Handling Adder, hours per affected repair (workbook)

WORKBOOK_HOURS = {
    # name: (install, removal)
    "pole_medium": (2.50295207667732, 0.9274888178913726),
    "crossarm": (0.3741146496815283, 0.21217834394904417),
    "grounding": (0.5319565217391303, 0.15296086956521746),
    "equipment_lead": (0.6501904761904762, 0.20609523809523825),
    "fuse_cutout": (0.256, 0.128),
    "recloser": (0.5726238532110097, 0.5253577981651364),
    "switch": (1.7579459459459466, 1.0097297297297296),
    "transformer_25kva": (1.1880851063829778, 0.8061276595744681),
    "service": (1.692981132075472, 0.48),
    "secondary_attach": (0.23258536585365866, 0.12682926829268298),
    "dead_end": (0.10760784313725497, 0.06400000000000004),
    "insulator": (0.04923076923076923, 0.0393846153846154),
    "pin": (0.06606451612903229, 0.042322580645161305),
    "connector": (0.215158, 0.0448),
}
_h = {k: i + r for k, (i, r) in WORKBOOK_HOURS.items()}

CATS = ["Wire span", "Service and secondary", "Pole", "Fuse bank",
        "Recloser or switch", "Transformer"]

# Hours of direct labor to repair ONE item of each kind (swap old part out, put new part in).
BUNDLE_H = {
    # ASSUMPTION: the workbook has no per-span wire hours, so a wire repair is built from
    # 2 dead-ends + 2 connectors + 1 insulator + 1 pin.
    "Wire span": 2 * _h["dead_end"] + 2 * _h["connector"] + _h["insulator"] + _h["pin"],
    "Service and secondary": _h["secondary_attach"] + _h["service"],
    "Pole": _h["pole_medium"] + _h["crossarm"] + _h["grounding"],
    "Fuse bank": _h["fuse_cutout"] + _h["equipment_lead"],
    # ASSUMPTION: 3 in 4 damaged devices of this kind are reclosers, 1 in 4 switches (damage file mix).
    "Recloser or switch": 0.75 * _h["recloser"] + 0.25 * _h["switch"],
    "Transformer": _h["transformer_25kva"] + _h["grounding"] + _h["equipment_lead"],
}
BUNDLE_NOTE = {
    "Wire span": "Assumed: workbook has no per-span wire hours, so built from dead-end, connector, insulator and pin hours",
    "Service and secondary": "Secondary attachment plus service drop (workbook)",
    "Pole": "Medium pole plus crossarm plus grounding (workbook)",
    "Fuse bank": "Fuse cutout plus equipment lead (workbook)",
    "Recloser or switch": "Weighted recloser and switch hours (workbook)",
    "Transformer": "25 kVA transformer plus grounding plus equipment lead (workbook)",
}

ASSET_TO_CAT = {
    "primary": "Wire span", "Light": "Wire span",
    "secondary": "Service and secondary",
    "Pole": "Pole",
    "Fuse Bank": "Fuse bank",
    "Recloser Bank": "Recloser or switch", "Switch": "Recloser or switch",
    "Transformer": "Transformer", "Step Transformer": "Transformer", "Capacitor Bank": "Transformer",
}

# ASSUMPTIONS for crews and queue time. Calibrated on the Feb 2025 storm (not validated on any other):
#  - small circuits wait in the queue (about 24 hours in a major storm) while crews work the biggest pockets first
#  - the utility surges roughly one crew per 12 damaged items, up to 15 crews
CREW_SIZE = 2            # workers per crew
SHIFT_H = 16             # storm shift length
REST_H = 8               # rest after each full shift
ITEMS_PER_CREW = 12      # utility surges about one crew per 12 damaged items
MIN_CREWS, MAX_CREWS = 2, 15


def default_crews(n_items: float) -> int:
    return int(min(MAX_CREWS, max(MIN_CREWS, round(n_items / ITEMS_PER_CREW))))


# --------------------------------------------------------------------------
# Risk
# --------------------------------------------------------------------------
W = {"circuit": 0.45, "chain": 0.25, "service": 0.20, "devices": 0.10}
BANDS = [("Low", 0, 25), ("Moderate", 25, 50), ("High", 50, 75), ("Very high", 75, 1000)]
BAND_ORDER = [b[0] for b in BANDS]


def band_of(score: float) -> str:
    for name, lo, hi in BANDS:
        if lo <= score < hi:
            return name
    return "Very high"


def exposure(circ_pct, hit, svc, devs, chain_ok):
    """Return (normalized values 0-1, weighted parts, total exposure 0-1)."""
    v = {
        "circuit": float(circ_pct),
        "chain": (1.0 if hit else 0.0) if chain_ok else 0.5,
        "service": {"Overhead": 1.0, "Underground": 0.0}.get(svc, 0.5),
        "devices": (min(int(devs), 6) / 6.0) if chain_ok else 0.5,
    }
    parts = {k: W[k] * v[k] for k in v}
    return v, parts, sum(parts.values())


def risk(circ_pct, hit, svc, devs, chain_ok, sev):
    v, parts, E = exposure(circ_pct, hit, svc, devs, chain_ok)
    score = int(min(100, round(100 * E * SEVERITIES[sev]["risk"])))
    return {"score": score, "band": band_of(score), "E": E, "v": v, "parts": parts}


def confidence(circ_dmg, chain_ok, svc, sev):
    pts = (2 if circ_dmg >= 10 else 1 if circ_dmg >= 1 else 0)
    pts += 1 if chain_ok else 0
    pts += 1 if svc in ("Overhead", "Underground") else 0
    pts += 1 if sev == OBSERVED_SEV else 0
    level = "High" if pts >= 4 else "Medium" if pts >= 2 else "Low"
    if sev != OBSERVED_SEV and level == "High":
        level = "Medium"  # we only have one storm, so far-from-it scenarios can't be "High"
    return level, pts


def _circuit_phrase(pct):
    if pct >= 0.9:
        return "among the hardest-hit 10% of circuits"
    if pct >= 0.5:
        return "more than the typical circuit"
    if pct >= 0.1:
        return "fewer than the typical circuit"
    return "among the quietest circuits"


def reasons(res, circ_dmg, circ_dpk, svc, devs, chain_ok, hit, n=3):
    """Top factors in plain language, ranked by how far each is from neutral."""
    v = res["v"]
    texts = {}
    texts["circuit"] = (
        f"Your circuit had {int(circ_dmg)} damage reports in the Feb 2025 storm "
        f"({circ_dpk:.0f} per 1,000 customers), {_circuit_phrase(v['circuit'])}."
    )
    if not chain_ok:
        texts["chain"] = "We could not trace the equipment that feeds your home, so this factor is left neutral."
    elif hit:
        texts["chain"] = "Equipment that feeds your home was damaged in the Feb 2025 storm."
    else:
        texts["chain"] = "The equipment that feeds your home came through the Feb 2025 storm undamaged."
    if svc == "Overhead":
        texts["service"] = "Your service line is overhead, so wind, ice and falling branches can reach it."
    elif svc == "Underground":
        texts["service"] = "Your service line is underground, which shields it from wind and falling trees."
    else:
        texts["service"] = "We do not know if your service line is overhead or underground, so this factor is neutral."
    if not chain_ok:
        texts["devices"] = "We could not count the protective devices between you and the substation."
    elif int(devs) >= 3:
        texts["devices"] = (f"{int(devs)} protective devices (fuses, reclosers) sit between you and the "
                            "substation. A problem at any one of them can cut your power.")
    else:
        texts["devices"] = (f"Only {int(devs)} protective devices sit between you and the substation, "
                            "so there are fewer places for a failure to cut you off.")
    ranked = sorted(W, key=lambda k: W[k] * abs(v[k] - 0.5), reverse=True)[:n]
    out = []
    for k in ranked:
        direction = "up" if v[k] > 0.5 else "down" if v[k] < 0.5 else "neutral"
        out.append({"key": k, "dir": direction, "text": texts[k]})
    return out


def caveats(sev, chain_ok, svc, circ_dmg):
    c = [
        "We have data from one major storm. A different kind of storm (ice instead of wind) could damage different equipment.",
        "This demo has no live weather, crew, or outage data.",
    ]
    if sev != OBSERVED_SEV:
        c.insert(0, f"The '{sev}' scenario is outside the one storm we have data for, so treat it as a rough guide.")
    if not chain_ok:
        c.append("We could not trace the equipment that feeds this location.")
    if svc not in ("Overhead", "Underground"):
        c.append("We are missing whether this service line is overhead or underground.")
    if circ_dmg < 1:
        c.append("Your circuit has no damage history in our data.")
    return c


# --------------------------------------------------------------------------
# Restoration
# --------------------------------------------------------------------------
def restore(n_items, mix, access_share, special_share, crews, sev):
    """Estimate hours until most customers on the circuit are back on.

    labor hours x indirect multiplier -> on-the-clock hours
    divided by workers on the circuit -> elapsed work hours (plus rest between shifts)
    plus time to assess damage, mobilize and wait in the crew queue.
    """
    n_items = max(1, float(n_items))
    each = sum(mix.get(c, 0.0) * BUNDLE_H[c] for c in CATS)
    adders = access_share * ADDER_ACCESS + special_share * ADDER_SPECIAL
    direct = n_items * (each + adders)
    on_clock = direct * ILM
    workers = max(1, int(crews)) * CREW_SIZE
    work_h = on_clock / workers
    elapsed = work_h + REST_H * math.floor(work_h / SHIFT_H)
    mob = SEVERITIES[sev]["mob_h"]
    mid = mob + elapsed
    lo = max(1.5, mid * 0.6)
    hi = max(lo + 1.0, mid * (1.4 + 0.6 * access_share) + 12)
    return {
        "direct_h": direct, "each_h": each, "adder_h": adders, "on_clock_h": on_clock,
        "workers": workers, "work_h": work_h, "elapsed_h": elapsed, "mob_h": mob,
        "mid_h": mid, "lo_h": lo, "hi_h": hi,
    }


def fmt_range(lo, hi):
    """Always in hours. Rounded outward to 1 h (short outages), 6 h (up to 5 days) or 12 h (longer)."""
    step = 1 if hi <= 30 else 6 if hi <= 120 else 12
    a = math.floor(lo / step) * step or max(1, round(lo))
    b = max(a + step, math.ceil(hi / step) * step)
    return f"{a} to {b} hours"


def what_if(n_items, mix, access_share, special_share, crews, sev):
    base = restore(n_items, mix, access_share, special_share, crews, sev)
    out = []
    more = restore(n_items * 1.5, mix, access_share, special_share, crews, sev)
    out.append(("If crews find 50% more damage than assumed", fmt_range(more["lo_h"], more["hi_h"])))
    crew2 = restore(n_items, mix, access_share, special_share, crews + 2, sev)
    out.append(("If 2 more crews are sent to your circuit", fmt_range(crew2["lo_h"], crew2["hi_h"])))
    bad = restore(n_items, mix, min(1.0, access_share + 0.3), special_share, crews, sev)
    out.append(("If 30% more repairs are hard to reach (flooding, backyards, no road)", fmt_range(bad["lo_h"], bad["hi_h"])))
    return base, out


# --------------------------------------------------------------------------
# Prep guidance
# --------------------------------------------------------------------------
def prep(band, mid_h, medical):
    groups = [("Today", [
        "Charge phones and power banks. Charge rechargeable lights.",
        "Put fresh batteries in flashlights. Skip candles.",
        "Store drinking water: about a gallon per person per day, enough for 3 days.",
        "Stock food that needs no cooking or fridge.",
        "Learn how to open your garage door by hand.",
        "Refill any prescriptions that are due soon.",
    ])]
    longish = band in ("High", "Very high") or mid_h > 24
    if longish:
        groups.append(("If the outage could last more than a day", [
            "Keep the fridge and freezer shut. A fridge keeps food safe for about 4 hours, a full freezer about 48 hours.",
            "Buy ice or fill a cooler for the most important foods.",
            "Fill your car's gas tank and keep some cash on hand.",
            "Unplug sensitive electronics. Leave one light switch on so you notice when power returns.",
            "Check on neighbors who live alone or have trouble getting around.",
        ]))
    if mid_h > 72:
        groups.append(("If it could last several days", [
            "Pick a place you could stay if your home gets too hot or cold, such as family or a local shelter.",
            "Pack a go-bag with medications, chargers, documents and clothes.",
            "Plan for pets: food, water and where they will stay.",
        ]))
    if medical:
        groups.append(("Because you told us someone at home relies on medical equipment", [
            "Make sure your utility account lists the need, and turn on outage alerts.",
            "Know how many hours your backup battery or generator lasts, and where you would go if it runs low.",
            "Ask your care provider now what to do if power is out for 4, 12 and 24 hours.",
            "Check storage instructions for any medicine that needs to stay cold, or ask your pharmacist.",
            "Move to your backup location before batteries run low, not after.",
        ]))
    return groups


SAFETY = [
    "Treat every downed line as energized. Stay far back from it and anything it touches, then call 911 and the utility.",
    "Never run a generator, grill or camp stove inside your home, garage or near a window. Carbon monoxide can kill.",
    "Do not drive through flooded roads or walk through standing water near power lines.",
]
EMERGENCY = "Medical emergency, fire, or a downed line that is sparking or on a car or home: call 911 first."


# --------------------------------------------------------------------------
# Alerts (challenge assumptions modeled on opt-in text/email outage alerts)
# --------------------------------------------------------------------------
def alerts(band, medical, enrolled, conf_level):
    rules = [
        ("Residential account with a phone number or email on file", "yes",
         "Assumed for this demo."),
        ("Signed up for outage alerts", "yes" if enrolled else "todo",
         "Done." if enrolled else "Not yet. Alerts are opt-in; sign up on the utility's alerts page with your account."),
        ("Pre-storm heads-up (risk is Moderate or higher)", "yes" if band != "Low" else "no",
         "Your risk is " + band.lower() + "." + ("" if band != "Low" else " We would only send one if the forecast worsens.")),
        ("Priority outreach (need declared by you)", "yes" if medical else "no",
         "You declared a medical or life-support need." if medical else "No need declared. You can declare one at any time."),
    ]
    plan = [
        ("Pre-storm heads-up",
         "48 hours and 12 hours before expected impact" if band != "Low" else "Only if the forecast worsens",
         "Text and email" + (", plus a phone call at 12 hours" if medical else "")),
        ("Outage confirmed",
         "Within minutes of confirmation",
         "Text" + (", plus a phone call and a human follow-up" if medical else " and email")),
        ("Estimate updated",
         "When the range moves by about a quarter or more, and at least every 6 hours",
         "Text"),
        ("Restoration complete",
         "When your circuit is re-energized, then a check-in 2 hours later",
         "Text and email"),
    ]
    triggers = [
        "The restoration estimate slips twice: a person reviews it and contacts you.",
        "The outage passes 24 hours" + (" (12 hours because you declared a medical need)" if medical else "") + ": outbound call.",
    ]
    if medical:
        triggers.append("Outage confirmed with a declared medical need: a person follows up right away.")
    triggers.append("Our confidence is Low or the location is not in our data: a person answers instead of an automated estimate.")
    triggers.append("You report still being out after we say power is back: crews check your service line.")
    return rules, plan, triggers


# --------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------
def messages(band, range_txt, prev_txt, medical, city, sev):
    phrase = SEVERITIES[sev]["phrase"]
    if band == "Low":
        pre = (f"[DEMO] A {phrase} is forecast near {city}. Your outage risk looks low, but outages can still happen. "
               "Charge your phone and know where your flashlight is. This is an estimate.")
    else:
        pre = (f"[DEMO] A {phrase} is forecast near {city}. Your outage risk is {band.lower()}. "
               "Today: charge phones, gather flashlights, fill water jugs. If power goes out we will text you an estimate. Estimates can change.")
    out_conf = (f"[DEMO] Your power is out. We confirmed an outage in your area and crews are being lined up. "
                f"Our model estimate: back on in {range_txt}. This is an estimate, not a confirmed time. "
                "Stay away from downed lines. Call 911 for emergencies.")
    upd = (f"[DEMO] Update: crews found more damage than first expected. New estimate: {range_txt} "
           f"(earlier estimate: {prev_txt}). Still an estimate. We will update you again within 6 hours.")
    done = ("[DEMO] Power is back on in your area. If your lights are still out, check your breakers, "
            "then reply or report it so we can check your service. Thank you for your patience.")
    if medical:
        pre += " You told us someone relies on medical equipment: check your backup power now."
        out_conf += " Medical equipment at home? Switch to your backup plan now."
    return [
        {"title": "Before the storm", "when": "48 and 12 hours before impact", "channel": "Text and email", "text": pre},
        {"title": "Outage confirmed", "when": "Within minutes of confirmation", "channel": "Text", "text": out_conf},
        {"title": "Estimate updated", "when": "When the range moves or every 6 hours", "channel": "Text", "text": upd},
        {"title": "Power restored", "when": "When your circuit is re-energized", "channel": "Text and email", "text": done},
    ]
