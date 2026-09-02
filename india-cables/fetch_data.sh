#!/usr/bin/env bash
# Re-fetch the source data used by analyze.py / render.py.
#
# Intended source: git clone --depth 1 https://github.com/telegeography/www.submarinecablemap.com
# As of 2026-09 that repository returns 404 on GitHub (removed or made private), so the files are
# pulled from lintaojlu/submarine_cable_information, which preserves TeleGeography's repo layout
# (RedwoodJS app; static API under web/public/api/v3) and its CC BY-NC-SA 3.0 LICENSE. The snapshot
# is dated 2022-04-25 (see web/public/api/v3/config.json).
#
# Coastlines: Natural Earth 1:50m land (public domain), via the official Natural Earth GitHub mirror.
set -euo pipefail
cd "$(dirname "$0")/data"
TG=https://raw.githubusercontent.com/lintaojlu/submarine_cable_information/master
API=$TG/web/public/api/v3
D=telegeography/web/public/api/v3
mkdir -p $D/cable $D/landing-point $D/country natural_earth
curl -sSfL -o telegeography/README.md $TG/README.md
curl -sSfL -o telegeography/LICENSE   $TG/LICENSE
for p in config.json search.json cable/cable-geo.json cable/all.json landing-point/landing-point-geo.json country/india.json; do
  curl -sSfL -o $D/$p $API/$p
done
# Indian landing points (13), then every cable that lands at one of them (21).
for s in mumbai-india chennai-india cochin-india tuticorine-india trivendrum-india port-blair-india \
         havelock-india long-island-india rangat-india little-andaman-india car-nicobar-india kamorta-india great-nicobar-india; do
  curl -sSfL -o $D/landing-point/$s.json $API/landing-point/$s.json
done
while read -r c; do curl -sSfL -o $D/cable/$c.json $API/cable/$c.json; done < india_cable_ids.txt
NE=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master
curl -sSfL -o natural_earth/ne_50m_land.geojson $NE/geojson/ne_50m_land.geojson
curl -sSfL -o natural_earth/LICENSE.md $NE/LICENSE.md
