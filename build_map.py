#!/usr/bin/env python3
"""build_map.py - make the neighborhood hexagons for the Outage map page.

Optional, like build_data.py. Run it after build_data.py (or against the processed files already in the repo):

    pip install -r requirements-build.txt
    python build_map.py --raw path/to/aep_challenge_hack26/data/raw

Privacy: homes are grouped into hexagons about 450 m across, and any hexagon with fewer than
MIN_HOMES homes is dropped. Only hexagon-level numbers leave this script; no home's position does.
It also adds a "hex" column to premises.csv.gz so the map can outline the user's own area.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # so `python -I build_map.py` still finds engine.py and build_data.py

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import build_data  # noqa: E402
import engine  # noqa: E402

OUT = HERE / "data" / "processed"
CRS_M = 32617   # UTM zone 17N, metres (Roanoke area)
R_M = 260.0     # hexagon circumradius; 260 m gives about 450 m across the flats
MIN_HOMES = 10  # privacy floor per hexagon
SQ3 = math.sqrt(3)


def hex_of(x: np.ndarray, y: np.ndarray):
    """Pointy-top axial hexagon coordinates (q, r) for points in metres."""
    q = (SQ3 / 3 * x - y / 3) / R_M
    r = (2 / 3 * y) / R_M
    s = -q - r
    rq, rr, rs = np.round(q), np.round(r), np.round(s)
    dq, dr, ds = np.abs(rq - q), np.abs(rr - r), np.abs(rs - s)
    fix_q = (dq > dr) & (dq > ds)
    fix_r = ~fix_q & (dr > ds)
    rq = np.where(fix_q, -rr - rs, rq)
    rr = np.where(fix_r, -rq - rs, rr)
    return rq.astype(int), rr.astype(int)


def hex_center(q, r):
    return R_M * SQ3 * (q + r / 2), R_M * 1.5 * r


def main():
    import geopandas as gpd
    from shapely.geometry import Point, Polygon

    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="folder with Data1.zip, Data2.zip, matched_upstream.zip")
    args = ap.parse_args()

    cust, storm, _, raw_prem, _ = build_data.load(Path(args.raw))

    # The processed premises file must line up row-for-row with the raw customers, so existing location codes stay valid.
    prem = pd.read_csv(OUT / "premises.csv.gz", dtype={"hid": str})
    cols = ["city", "road", "circuit", "svc", "devs", "chain_ok", "hit25"]
    if len(prem) != len(raw_prem) or not (prem[cols].reset_index(drop=True) == raw_prem[cols].reset_index(drop=True)).all().all():
        sys.exit("premises.csv.gz does not match the raw data row-for-row. Re-run build_data.py first.")

    pts = cust.geometry.to_crs(CRS_M).centroid
    q, r = hex_of(pts.x.to_numpy(), pts.y.to_numpy())
    prem["hex"] = [f"{a}_{b}" for a, b in zip(q, r)]
    counts = prem.hex.value_counts()
    keep = set(counts[counts >= MIN_HOMES].index)
    print(f"hexagons: {len(counts)}, kept {len(keep)} with >= {MIN_HOMES} homes "
          f"({prem.hex.isin(keep).mean():.1%} of homes)")

    # Storm damage reports per hexagon (equipment locations, not homes).
    sp = storm.geometry.to_crs(CRS_M)
    sq, sr = hex_of(sp.x.to_numpy(), sp.y.to_numpy())
    dmg_by_hex = pd.Series([f"{a}_{b}" for a, b in zip(sq, sr)]).value_counts()

    # Per-home risk score for each scenario, exactly as the pages compute it.
    circ = pd.read_csv(OUT / "circuits.csv").set_index("circuit")
    prem["pct"] = prem.circuit.map(circ.pct)
    E = np.array([engine.exposure(p, h, s, d, c)[2]
                  for p, h, s, d, c in zip(prem.pct, prem.hit25, prem.svc, prem.devs, prem.chain_ok)])
    for sev in engine.SEV_ORDER:
        prem["score_" + sev] = np.minimum(100, np.round(100 * E * engine.SEVERITIES[sev]["risk"]))

    # Restoration range for each circuit and scenario, with the default slider values the pages start from.
    for sev in engine.SEV_ORDER:
        lo, mid, hi = {}, {}, {}
        for cid, c in circ.iterrows():
            mix = {k: float(c["mix_" + k]) for k in engine.CATS}
            items = max(1, round(float(c.base_items) * engine.SEVERITIES[sev]["dmg"]))
            e = engine.restore(items, mix, float(c.access_share), float(c.special_share), engine.default_crews(items), sev)
            lo[cid], mid[cid], hi[cid] = e["lo_h"], e["mid_h"], e["hi_h"]
        for name, d in (("lo", lo), ("mid", mid), ("hi", hi)):
            prem[f"{name}_{sev}"] = prem.circuit.map(d)

    hexes = []
    for hx, g in prem[prem.hex.isin(keep)].groupby("hex"):
        a, b = map(int, hx.split("_"))
        cx, cy = hex_center(a, b)
        ring = [(cx + R_M * math.cos(math.radians(60 * i - 30)), cy + R_M * math.sin(math.radians(60 * i - 30))) for i in range(6)]
        poly = gpd.GeoSeries([Polygon(ring)], crs=CRS_M).to_crs(4326).iloc[0]
        center = gpd.GeoSeries([Point(cx, cy)], crs=CRS_M).to_crs(4326).iloc[0]
        n = len(g)
        h = {
            "id": hx, "lon": round(center.x, 5), "lat": round(center.y, 5),
            "poly": [[round(x, 5), round(y, 5)] for x, y in list(poly.exterior.coords)[:-1]],
            "n": n, "city": g.city.mode().iat[0],
            "ug": round(float((g.svc == "Underground").mean()), 3),
            "hit": round(float(g.hit25.mean()), 3),
            "dmg": int(dmg_by_hex.get(hx, 0)),
            "dmg_pk": round(1000 * dmg_by_hex.get(hx, 0) / n, 1),
            "risk": {}, "rest": {},
        }
        for sev in engine.SEV_ORDER:
            s = g["score_" + sev]
            med = float(s.median())
            h["risk"][sev] = {"score": int(round(med)), "band": engine.band_of(med), "high": round(float((s >= 50).mean()), 3)}
            lo_h, mid_h, hi_h = (float(g[f"{k}_{sev}"].median()) for k in ("lo", "mid", "hi"))
            h["rest"][sev] = {"mid": round(mid_h, 1), "txt": engine.fmt_range(lo_h, hi_h)}
        hexes.append(h)

    # Town labels: the middle of each larger town's kept homes.
    kept = prem[prem.hex.isin(keep)].assign(x=pts.x.to_numpy()[prem.hex.isin(keep).to_numpy()],
                                            y=pts.y.to_numpy()[prem.hex.isin(keep).to_numpy()])
    towns = []
    for city, g in kept.groupby("city"):
        if len(g) < 1500 or city == "Unknown":
            continue
        c = gpd.GeoSeries([Point(g.x.median(), g.y.median())], crs=CRS_M).to_crs(4326).iloc[0]
        towns.append({"name": city, "lon": round(c.x, 4), "lat": round(c.y, 4), "n": int(len(g))})

    (OUT / "hexes.json").write_text(json.dumps({"r_m": R_M, "min_homes": MIN_HOMES, "hexes": hexes, "towns": towns}))
    prem["hex"] = prem.hex.where(prem.hex.isin(keep), "")
    prem[["hid", "city", "road", "circuit", "svc", "devs", "chain_ok", "hit25", "hex"]].to_csv(OUT / "premises.csv.gz", index=False)
    print(f"wrote hexes.json ({len(hexes)} hexagons, {len(towns)} town labels) and added hex to premises.csv.gz")


if __name__ == "__main__":
    main()
