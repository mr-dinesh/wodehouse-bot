#!/usr/bin/env python3
"""Step 1: analyse India's submarine cable landings from the TeleGeography data.

Reads data/telegeography/web/public/api/v3/... and writes out/analysis.json (consumed by render.py)
plus a human-readable summary table on stdout. No drawing happens here.
"""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = HERE / "data" / "telegeography" / "web" / "public" / "api" / "v3"
OUT = HERE / "out"

# Coarse regions for the "regions reached" column. Sri Lanka kept separate on request.
REGION = {
    "Sri Lanka": "Sri Lanka",
    "Pakistan": "South Asia (other)", "Bangladesh": "South Asia (other)", "Maldives": "South Asia (other)",
    "Bahrain": "Middle East", "Iran": "Middle East", "Iraq": "Middle East", "Jordan": "Middle East",
    "Kuwait": "Middle East", "Lebanon": "Middle East", "Oman": "Middle East", "Qatar": "Middle East",
    "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East", "Yemen": "Middle East",
    "Egypt": "Africa", "Libya": "Africa", "Tunisia": "Africa", "Algeria": "Africa", "Morocco": "Africa",
    "Sudan": "Africa", "Djibouti": "Africa", "Somalia": "Africa", "Kenya": "Africa", "Tanzania": "Africa",
    "Mozambique": "Africa", "South Africa": "Africa", "Madagascar": "Africa", "Mauritius": "Africa",
    "Réunion": "Africa", "Seychelles": "Africa", "Comoros": "Africa", "Angola": "Africa", "Gabon": "Africa",
    "Congo, Rep.": "Africa", "Congo, Dem. Rep.": "Africa", "Nigeria": "Africa", "Ghana": "Africa",
    "Côte d'Ivoire": "Africa", "Senegal": "Africa",
    "Turkey": "Europe", "Cyprus": "Europe", "Greece": "Europe", "Italy": "Europe", "Monaco": "Europe",
    "France": "Europe", "Spain": "Europe", "Gibraltar": "Europe", "Portugal": "Europe", "Belgium": "Europe",
    "United Kingdom": "Europe",
    "Myanmar": "Southeast Asia", "Thailand": "Southeast Asia", "Malaysia": "Southeast Asia",
    "Singapore": "Southeast Asia", "Indonesia": "Southeast Asia", "Vietnam": "Southeast Asia",
    "Cambodia": "Southeast Asia", "Brunei": "Southeast Asia", "Philippines": "Southeast Asia",
    "China": "East Asia", "Taiwan": "East Asia", "South Korea": "East Asia", "Japan": "East Asia",
    "Australia": "Australia",
}
REGION_ORDER = ["Middle East", "Europe", "Africa", "Sri Lanka", "South Asia (other)",
                "Southeast Asia", "East Asia", "Australia"]
ANDAMAN_NICOBAR = {"port-blair-india", "havelock-india", "long-island-india", "rangat-india",
                   "little-andaman-india", "car-nicobar-india", "kamorta-india", "great-nicobar-india"}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    lp_geo = load(API / "landing-point" / "landing-point-geo.json")
    coords = {f["properties"]["id"]: f["geometry"]["coordinates"] for f in lp_geo["features"]}
    india_lps = sorted((f["properties"] for f in lp_geo["features"]
                       if f["properties"]["name"].endswith(", India")), key=lambda p: p["id"])
    assert india_lps, "no Indian landing points found"

    # Landing point -> cables (from the per-landing-point files).
    lp_cables = {}
    for lp in india_lps:
        d = load(API / "landing-point" / f"{lp['id']}.json")
        lp_cables[lp["id"]] = [c["id"] for c in d["cables"]]

    # Every cable that lands in India, with its full landing-point list.
    cable_ids = sorted({c for cs in lp_cables.values() for c in cs})
    cables = {}
    for cid in cable_ids:
        d = load(API / "cable" / f"{cid}.json")
        countries = sorted({lp["country"] for lp in d["landing_points"]})
        foreign = [c for c in countries if c != "India"]
        unknown = [c for c in foreign if c not in REGION]
        assert not unknown, f"{cid}: unmapped countries {unknown}"
        regions = sorted({REGION[c] for c in foreign}, key=REGION_ORDER.index)
        cables[cid] = {
            "id": cid, "name": d["name"], "rfs_year": d.get("rfs_year"), "is_planned": bool(d.get("is_planned")),
            "length": d.get("length"), "owners": d.get("owners"),
            "indian_landing_points": [lp["id"] for lp in d["landing_points"] if lp["country"] == "India"],
            "foreign_landing_points": [lp["name"] for lp in d["landing_points"] if lp["country"] != "India"],
            "foreign_countries": foreign, "regions": regions,
            "domestic_only": not foreign,
        }

    # Per-landing-point summary.
    summary = []
    for lp in india_lps:
        cs = [cables[c] for c in lp_cables[lp["id"]]]
        intl = [c for c in cs if not c["domestic_only"]]
        dom = [c for c in cs if c["domestic_only"]]
        regions = sorted({r for c in intl for r in c["regions"]}, key=REGION_ORDER.index)
        summary.append({
            "id": lp["id"], "name": lp["name"].replace(", India", ""), "lon": coords[lp["id"]][0], "lat": coords[lp["id"]][1],
            "andaman_nicobar": lp["id"] in ANDAMAN_NICOBAR,
            "international": [c["id"] for c in intl], "domestic": [c["id"] for c in dom],
            "international_planned": sum(c["is_planned"] for c in intl),
            "regions": regions,
        })
    summary.sort(key=lambda s: (-len(s["international"]), -len(s["domestic"]), s["name"]))

    OUT.mkdir(exist_ok=True)
    snapshot = load(API / "config.json").get("creation_time")
    with open(OUT / "analysis.json", "w", encoding="utf-8") as f:
        json.dump({"snapshot": snapshot, "landing_points": summary, "cables": cables}, f, indent=2, ensure_ascii=False)

    # ---- report ----
    print(f"TeleGeography snapshot: {snapshot}")
    print(f"Indian landing points: {len(india_lps)}   cables landing in India: {len(cables)} "
          f"({sum(not c['domestic_only'] for c in cables.values())} international, "
          f"{sum(c['domestic_only'] for c in cables.values())} domestic-only)\n")

    print("== Cables landing in India ==")
    for c in sorted(cables.values(), key=lambda c: (c["domestic_only"], c["rfs_year"] or 0)):
        tag = "DOMESTIC-ONLY" if c["domestic_only"] else ("planned" if c["is_planned"] else "live")
        lands = ", ".join(l.replace("-india", "") for l in c["indian_landing_points"])
        print(f"- {c['name']}  [{c['rfs_year']}, {tag}]  lands: {lands}")
        if c["foreign_countries"]:
            print(f"    -> {len(c['foreign_countries'])} countries: {', '.join(c['foreign_countries'])}")

    print("\n== Summary by landing point ==")
    hdr = f"{'Landing point':<16}{'Intl':>5}{'(planned)':>10}{'Dom':>5}  Regions reached"
    print(hdr); print("-" * len(hdr))
    for s in summary:
        print(f"{s['name']:<16}{len(s['international']):>5}{s['international_planned']:>10}{len(s['domestic']):>5}  "
              f"{', '.join(s['regions']) or '-'}")

    intl_total = [c for c in cables.values() if not c["domestic_only"]]
    top2 = summary[:2]
    covered = {c for s in top2 for c in s["international"]}
    print(f"\nTop two ({top2[0]['name']}, {top2[1]['name']}) touch {len(covered)} of {len(intl_total)} international cables "
          f"({100*len(covered)/len(intl_total):.0f}%).")
    only_elsewhere = [c["name"] for c in intl_total if c["id"] not in covered]
    print(f"International cables landing only elsewhere: {only_elsewhere or 'none'}")
    both = [c["name"] for c in intl_total if {"mumbai-india", "chennai-india"} <= set(c["indian_landing_points"])]
    print(f"Cables landing at both Mumbai and Chennai: {both}")
    print(f"\nWrote {OUT / 'analysis.json'}")


if __name__ == "__main__":
    main()
