#!/usr/bin/env python3
"""Step 2: draw the poster. Reads out/analysis.json (from analyze.py), the TeleGeography cable
geometry and Natural Earth land, writes out/poster.svg and out/poster.png (A3 portrait, 300 dpi).

Everything visual lives in the STYLE / LAYOUT blocks below; rerun after tweaking.
"""
import base64
import json
import math
from pathlib import Path

from shapely.geometry import shape, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
API = HERE / "data" / "telegeography" / "web" / "public" / "api" / "v3"
LAND = HERE / "data" / "natural_earth" / "ne_50m_land.geojson"
OUT = HERE / "out"
FONTS = HERE / "fonts"

# ---------------------------------------------------------------- page & map
PAGE_W, PAGE_H = 297.0, 420.0                  # mm, A3 portrait
LON0, LON1, LAT0, LAT1 = 30.0, 110.0, -15.0, 35.0   # crop
MAP_X, MAP_W = 0.0, PAGE_W                     # full-bleed band
MAP_H = MAP_W * (LAT1 - LAT0) / (LON1 - LON0)  # plate carrée: 1 deg lon = 1 deg lat
MAP_Y = 88.0
MARGIN = 20.0

# ---------------------------------------------------------------- style
BG = "#f4efe6"          # cream
LAND_FILL = "#d8d1c3"   # single flat land tone
ACCENT = "#1b4a86"      # international cables + Indian landing points
CABLE_W = 0.38          # mm
CABLE_OPACITY = 0.5
DOMESTIC = "#8b867d"
DOMESTIC_W = 0.38
DOMESTIC_DASH = "1.6 1.1"
INK = "#1f1d1a"
INK_SOFT = "#6f6a62"
FONT_FAMILY = "'IBM Plex Sans', 'Inter', 'Source Sans 3', 'Helvetica Neue', Helvetica, Arial, sans-serif"
FS_SMALL = 3.4          # mm  (~9.6 pt)
FS_LARGE = 11.0         # mm  (~31 pt)
LABEL_PAD = 1.2

# Label placement for mainland points: (dx, dy, text-anchor), mm, relative to the circle edge.
LABEL = {
    "mumbai-india":     ( 1.0,  0.0, "start"),
    "chennai-india":    ( 1.0,  0.0, "start"),
    "cochin-india":     (-1.0,  0.0, "end"),
    "trivendrum-india": (-0.6,  3.2, "end"),
    "tuticorine-india": ( 0.8,  3.4, "start"),
}
DISPLAY_NAME = {
    "mumbai-india": "Mumbai", "chennai-india": "Chennai", "cochin-india": "Kochi",
    "trivendrum-india": "Thiruvananthapuram", "tuticorine-india": "Thoothukudi",
    "port-blair-india": "Port Blair", "havelock-india": "Havelock", "long-island-india": "Long Island",
    "rangat-india": "Rangat", "little-andaman-india": "Little Andaman", "car-nicobar-india": "Car Nicobar",
    "kamorta-india": "Kamorta", "great-nicobar-india": "Great Nicobar",
}
ISLAND_LABEL_LON = 96.3      # x column for the Andaman & Nicobar label stack
ISLAND_LABEL_STEP = 4.3      # mm between stacked labels

TITLE = "India's international submarine cables"
SUBTITLE = "Where the cables that carry the country's overseas internet traffic come ashore"
CAPTION = "Two coastal cities, most of a country's internet"
CAPTION_2 = "18 of the 20 international cable systems landing in India come ashore at Mumbai or Chennai. " \
            "Mumbai alone takes 16. Circles are scaled by cable count; the dashed line is the domestic " \
            "Chennai–Andaman & Nicobar system."
ATTRIBUTION = "Data: TeleGeography submarine cable map, CC BY-NC-SA 3.0 (April 2022 snapshot). Coastlines: Natural Earth."


def project(lon, lat):
    x = MAP_X + (lon - LON0) / (LON1 - LON0) * MAP_W
    y = MAP_Y + (LAT1 - lat) / (LAT1 - LAT0) * MAP_H
    return x, y


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def ring_path(coords):
    pts = [project(*c[:2]) for c in coords]
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def line_path(geom):
    lines = [geom] if geom.geom_type == "LineString" else list(getattr(geom, "geoms", []))
    parts = []
    for ln in lines:
        if ln.is_empty or ln.geom_type != "LineString":
            continue
        pts = [project(*c[:2]) for c in ln.coords]
        parts.append("M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts))
    return "".join(parts)


def polygon_path(geom):
    polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    d = []
    for p in polys:
        if p.is_empty or p.geom_type != "Polygon":
            continue
        d.append(ring_path(p.exterior.coords))
        d.extend(ring_path(r.coords) for r in p.interiors)
    return "".join(d)


def radius(n):
    return 0.5 + 1.05 * math.sqrt(n)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def label(x, y, inner, anchor="start", fill=INK, halo=True):
    """Text with a background-coloured halo so it stays legible over cable lines."""
    attrs = f'x="{f(x)}" y="{f(y)}" font-size="{FS_SMALL}" text-anchor="{anchor}"'
    out = []
    if halo:
        out.append(f'<text {attrs} fill="{BG}" stroke="{BG}" stroke-width="{FS_SMALL * 0.32:.2f}" '
                   f'stroke-linejoin="round">{inner}</text>')
    out.append(f'<text {attrs} fill="{fill}">{inner}</text>')
    return "\n".join(out)


def font_face_css():
    """Embed the fonts if present so the SVG prints identically anywhere."""
    css = []
    for fname, weight in (("IBMPlexSans-Regular.ttf", 400), ("IBMPlexSans-Medium.ttf", 500)):
        p = FONTS / fname
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            css.append(f"@font-face{{font-family:'IBM Plex Sans';font-weight:{weight};"
                       f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")
    return "\n".join(css)


def main():
    analysis = json.load(open(OUT / "analysis.json", encoding="utf-8"))
    cable_geo = json.load(open(API / "cable" / "cable-geo.json", encoding="utf-8"))
    land = json.load(open(LAND, encoding="utf-8"))
    bbox = box(LON0, LAT0, LON1, LAT1)

    cables = analysis["cables"]
    geoms = {ft["properties"]["id"]: shape(ft["geometry"]) for ft in cable_geo["features"]
             if ft["properties"]["id"] in cables}
    missing = set(cables) - set(geoms)
    assert not missing, f"no geometry for {missing}"

    # --- land
    land_geom = unary_union([shape(ft["geometry"]).intersection(bbox) for ft in land["features"]
                             if shape(ft["geometry"]).intersects(bbox)])
    land_d = polygon_path(land_geom)

    # --- cables
    intl_paths, dom_paths = [], []
    for cid, c in sorted(cables.items()):
        g = geoms[cid].intersection(bbox)
        if g.is_empty:
            continue
        d = line_path(g)
        (dom_paths if c["domestic_only"] else intl_paths).append((cid, d))

    # --- landing points
    lps = analysis["landing_points"]
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" '
               f'viewBox="0 0 {PAGE_W} {PAGE_H}">')
    svg.append("<title>India's international submarine cables</title>")
    svg.append(f"<style>{font_face_css()}\ntext{{font-family:{FONT_FAMILY};fill:{INK};}}</style>")
    svg.append("<defs>"
               f'<clipPath id="map"><rect x="{f(MAP_X)}" y="{f(MAP_Y)}" width="{f(MAP_W)}" height="{f(MAP_H)}"/></clipPath>'
               "</defs>")
    svg.append(f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="{BG}"/>')

    # header
    y = MARGIN + FS_SMALL
    svg.append(f'<text x="{MARGIN}" y="{f(y)}" font-size="{FS_SMALL}" font-weight="500">{esc(TITLE)}</text>')
    svg.append(f'<text x="{MARGIN}" y="{f(y + FS_SMALL * 1.5)}" font-size="{FS_SMALL}" fill="{INK_SOFT}">{esc(SUBTITLE)}</text>')

    # map
    svg.append('<g clip-path="url(#map)">')
    svg.append(f'<path d="{land_d}" fill="{LAND_FILL}" fill-rule="evenodd"/>')
    svg.append(f'<g fill="none" stroke="{ACCENT}" stroke-width="{CABLE_W}" stroke-opacity="{CABLE_OPACITY}" '
               'stroke-linecap="round" stroke-linejoin="round">')
    for cid, d in intl_paths:
        svg.append(f'<path id="cable-{cid}" d="{d}"/>')
    svg.append("</g>")
    svg.append(f'<g fill="none" stroke="{DOMESTIC}" stroke-width="{DOMESTIC_W}" stroke-dasharray="{DOMESTIC_DASH}" '
               'stroke-linecap="round" stroke-linejoin="round">')
    for cid, d in dom_paths:
        svg.append(f'<path id="cable-{cid}" d="{d}"/>')
    svg.append("</g>")

    # circles + labels
    islands = sorted([p for p in lps if p["andaman_nicobar"]], key=lambda p: -p["lat"])
    mainland = [p for p in lps if not p["andaman_nicobar"]]
    svg.append('<g id="landing-points">')
    for p in mainland:
        n = len(p["international"]) + len(p["domestic"])
        x, yy = project(p["lon"], p["lat"])
        r = radius(n)
        svg.append(f'<circle cx="{f(x)}" cy="{f(yy)}" r="{f(r)}" fill="{ACCENT}" stroke="{BG}" stroke-width="0.35"/>')
        dx, dy, anchor = LABEL[p["id"]]
        lx = x + (r + LABEL_PAD + dx if anchor == "start" else -(r + LABEL_PAD) + dx)
        ly = yy + dy + FS_SMALL * 0.35
        # single text run: cairosvg mis-anchors tspans inside end-anchored text
        svg.append(label(lx, ly, f'{esc(DISPLAY_NAME[p["id"]])} {len(p["international"])}', anchor))

    # Andaman & Nicobar: small grey markers, labels stacked in a column with leader lines.
    if islands:
        col_x, _ = project(ISLAND_LABEL_LON, 0)
        ys = [project(p["lon"], p["lat"])[1] for p in islands]
        mid = (min(ys) + max(ys)) / 2
        top = mid - ISLAND_LABEL_STEP * (len(islands) - 1) / 2
        svg.append(f'<g stroke="{DOMESTIC}" stroke-width="0.25" fill="none">')
        for i, p in enumerate(islands):
            x, yy = project(p["lon"], p["lat"])
            ly = top + i * ISLAND_LABEL_STEP
            svg.append(f'<path d="M{f(x + 1.6)} {f(yy)}L{f(col_x - 1.2)} {f(ly)}"/>')
        svg.append("</g>")
        for i, p in enumerate(islands):
            x, yy = project(p["lon"], p["lat"])
            ly = top + i * ISLAND_LABEL_STEP
            svg.append(f'<circle cx="{f(x)}" cy="{f(yy)}" r="{f(radius(1))}" fill="{DOMESTIC}" stroke="{BG}" stroke-width="0.35"/>')
            svg.append(label(col_x, ly + FS_SMALL * 0.35, esc(DISPLAY_NAME[p["id"]]), fill=INK_SOFT))
    svg.append("</g></g>")

    # footer
    cap_y = MAP_Y + MAP_H + 44
    svg.append(f'<text x="{MARGIN}" y="{f(cap_y)}" font-size="{FS_LARGE}" font-weight="500">{esc(CAPTION)}</text>')
    # wrap CAPTION_2 to the text column by character budget (approx 0.5em per char)
    max_chars = int((PAGE_W - 2 * MARGIN) / (FS_SMALL * 0.5))
    words, lines, cur = CAPTION_2.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > max_chars and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    for i, ln in enumerate(lines):
        svg.append(f'<text x="{MARGIN}" y="{f(cap_y + 9 + i * FS_SMALL * 1.5)}" font-size="{FS_SMALL}" fill="{INK_SOFT}">{esc(ln)}</text>')
    svg.append(f'<text x="{MARGIN}" y="{f(PAGE_H - MARGIN)}" font-size="{FS_SMALL}" fill="{INK_SOFT}">{esc(ATTRIBUTION)}</text>')
    svg.append("</svg>")

    OUT.mkdir(exist_ok=True)
    svg_path = OUT / "poster.svg"
    svg_path.write_text("\n".join(svg), encoding="utf-8")
    print(f"wrote {svg_path} ({svg_path.stat().st_size/1024:.0f} KB); "
          f"{len(intl_paths)} international, {len(dom_paths)} domestic cable paths")

    import cairosvg
    w_px = round(PAGE_W / 25.4 * 300)
    h_px = round(PAGE_H / 25.4 * 300)
    cairosvg.svg2png(url=str(svg_path), write_to=str(OUT / "poster.png"), output_width=w_px, output_height=h_px,
                     background_color=BG)
    from PIL import Image
    with Image.open(OUT / "poster.png") as im:   # stamp physical size for print software
        im.save(OUT / "poster.png", dpi=(300, 300))
    print(f"wrote {OUT / 'poster.png'} ({w_px}x{h_px} px, 300 dpi)")


if __name__ == "__main__":
    main()
