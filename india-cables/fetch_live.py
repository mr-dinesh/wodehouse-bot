#!/usr/bin/env python3
"""Pull the current TeleGeography submarine cable data (the JSON the live map itself loads)
into data/telegeography/web/public/api/v3/, mirroring the layout of the old GitHub repo so
analyze.py and render.py work unchanged.

Usage:
    python3 fetch_live.py                      # live site (default)
    python3 fetch_live.py --base <url>         # alternative base ending in /api/v3
    python3 fetch_live.py --country India      # which country's landings to expand (default India)

Fetches: config.json (if present), cable/all.json, cable/cable-geo.json,
landing-point/landing-point-geo.json, every landing-point/<slug>.json whose name ends in
", <country>", and every cable/<slug>.json that lands there. Writes data/india_cable_ids.txt.
Note: only the 2022 GitHub release carries an explicit CC BY-NC-SA 3.0 LICENSE; the live API is
governed by TeleGeography's site terms. Attribute TeleGeography either way.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE / "data" / "telegeography" / "web" / "public" / "api" / "v3"
LIVE = "https://www.submarinecablemap.com/api/v3"
UA = "india-cables-poster/1.0 (+https://github.com/mr-dinesh/wodehouse-bot)"


def get(base, path, retries=3):
    url = f"{base}/{path}"
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            err = e
        except (urllib.error.URLError, TimeoutError) as e:
            err = e
        time.sleep(2 ** i)
    raise err


def save(base, path, required=True):
    out = DEST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = get(base, path)
    except urllib.error.HTTPError as e:
        if not required and e.code == 404:
            print(f"  skip {path} (404)")
            return None
        raise
    json.loads(data)  # validate before writing
    out.write_bytes(data)
    print(f"  {path}  {len(data):,} bytes")
    return json.loads(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=LIVE)
    ap.add_argument("--country", default="India")
    a = ap.parse_args()
    base = a.base.rstrip("/")
    print(f"Fetching from {base} -> {DEST}")

    cfg = save(base, "config.json", required=False)
    save(base, "cable/all.json")
    save(base, "cable/cable-geo.json")
    lp_geo = save(base, "landing-point/landing-point-geo.json")

    suffix = f", {a.country}"
    lps = sorted(f["properties"]["id"] for f in lp_geo["features"] if f["properties"]["name"].endswith(suffix))
    print(f"{len(lps)} landing points in {a.country}")
    cable_ids = set()
    for slug in lps:
        d = save(base, f"landing-point/{slug}.json")
        cable_ids |= {c["id"] for c in d["cables"]}
    print(f"{len(cable_ids)} cables land in {a.country}")
    for cid in sorted(cable_ids):
        save(base, f"cable/{cid}.json")
    (HERE / "data" / "india_cable_ids.txt").write_text("\n".join(sorted(cable_ids)) + "\n")

    if cfg is None:
        # Live API has no config.json; record when we pulled it so analyze.py can report it.
        (DEST / "config.json").write_text(json.dumps(
            {"creation_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "source": base, "note": "fetched by fetch_live.py"}, indent=2))
    print("done")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        sys.exit(f"network error: {e}. Run this from a machine that can reach {LIVE}.")
