#!/usr/bin/env python3
"""R21 — parametric redraw of the Russell Periodic Chart (LoC scan p0016) as SVG.

Data-driven, not traced: every mark is generated from the two frozen inputs
  data/russell_1926_elements.json  (137 element rows, R11 dual-witness transcription)
  data/chart_geometry.json         (R13 measured center/rings/spiral/sectors/label clusters)

Coordinate system: SVG user units == scan pixels of source_scans/loc/full/p0016.jpg
(the R13 measurement frame; ring radius_norm * R_ref with R_ref = outermost ring
radius reproduces the same numbers). viewBox is a 2314 px square centered on the
measured chart center.

Placement model (derived from the plate, verified against measured geometry):
  - The ten octaves ride the measured mid-zone spiral, one half-turn per octave,
    winding OUTWARD counterclockwise-as-displayed (theta decreasing in the R13
    angle convention: 0 deg = east, clockwise positive, y down).
  - Each octave's 0= inert gas sits where the spiral crosses the horizontal axis
    (east for even octaves 2,4,6,8,10; west for odd 3,5,7,9; Omeganon closes the
    tenth octave on the west; Alphanon is the chart center).
  - Each octave's 4-double-dagger crest sits on the vertical axis, a quarter turn
    past its 0= gas; inhalation (+) rows are spaced evenly on the first quarter
    turn, exhalation (-) rows evenly on the second.
  - Octave 1 occupies the innermost spiral tail (u in (1800, 2070] deg unwrapped),
    crest at u=1890.
  This computed model is then snapped, row by row, to the measured label clusters
  of chart_geometry.json where a confident geometric match exists (see snap_rows);
  each element group carries data-placement="measured" or "computed".

Spiral turn-duplication in the frozen input is corrected first (see Strand:
the polyline tail beyond the u~1292-1310 discontinuity re-traces a turn; it
is shifted -360 deg after a data-driven duplication test). The corrected
polyline is then split at remaining tracking discontinuities (consecutive
samples jumping > 40 px in radius or > 15 deg in angle);
each segment's radius is then smoothed with a centered moving
average over unwrapped angle, fixed window of 21 samples (~23 deg),
edge-clamped, and resampled at 0.75 deg. Segments are emitted as separate
subpaths (the plate's strand is itself interrupted). Deterministic; keeps the
plate's real non-Archimedean pitch structure while removing hand-drawn wobble.
The residual of the smoothed curve against the raw measured polyline is reported.

Legibility rule: viewport square is 2314 units; scaled to fit a 1080 px display
height the scale is 1080/2314 = 0.46672. Oswald v4.103 metrics (verified from
the Google Fonts build: unitsPerEm 1000, sxHeight 578, sCapHeight 810, mean
capital advance 0.4886 em): minimum font size so x-height >= 7 px at that scale
is 7 / (0.578 * 0.46672) = 25.95 -> every text element uses font-size >= 26.
Where 1926 crowding makes on-strand placement impossible at that size, labels
are radially staggered: greedy first-fit tiering in strand order; a label takes
the first radial tier (glyph-box center offsets from the strand: +21, -21,
+49, -49 px; inner region r<240 uses outward-only +21, +49, +77, +105, +133)
whose occupied unwrapped-angle intervals it does not overlap (1.2 deg padding);
the textPath baseline is derived from the box center per hemisphere so glyphs
never overpaint the strand.

Deterministic output: no timestamps, fixed float formatting (2 decimals),
explicit iteration order everywhere. Reruns are byte-identical.

Usage:
  python3 tools/render_chart.py             # writes charts/russell_periodic.svg, prints report
  python3 tools/render_chart.py --overlay   # also rasterizes via Inkscape, measures alignment
                                            # against the raw scan, writes
                                            # data/geometry/redraw_overlay_proof.png
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_PATH = os.path.join(ROOT, "data", "chart_geometry.json")
ELEM_PATH = os.path.join(ROOT, "data", "russell_1926_elements.json")
SVG_PATH = os.path.join(ROOT, "charts", "russell_periodic.svg")
SCAN_PATH = os.path.join(ROOT, "source_scans", "loc", "full", "p0016.jpg")
PROOF_PATH = os.path.join(ROOT, "data", "geometry", "redraw_overlay_proof.png")

# N2 notice string (data/license_drafts/notice_conventions.md), embedded in the
# SVG metadata block. [YEAR] = 2026, [RIGHTSHOLDER] = Walter Russell Archive.
N2_NOTICE = (
    "Original redraw of a chart from Walter Russell, The Universal One (1926). "
    "Drawn from a hand-verified transcription of the Library of Congress scan, "
    "item 27004508. Copyright 2026 Walter Russell Archive. Licensed CC BY-NC 4.0: "
    "https://creativecommons.org/licenses/by-nc/4.0/. "
    "Credit Line: Library of Congress."
)

# ---- fixed rendering parameters (all documented in module docstring) ----
VIEW_X0, VIEW_Y0, VIEW_S = 397, 420, 2314
FS_NAME = 28          # element names
FS_TAG = 26           # position/sigil tags (minimum size used anywhere)
FS_GAS = 26           # inert-gas hub names
FS_CENTER = 34        # Alphanon center label
OSWALD_XH = 0.578     # sxHeight/upm, Oswald v4.103 (verified)
OSWALD_CAP = 0.810
OSWALD_ADV = 0.50     # mean caps advance 0.4886 em + tracking allowance
SMOOTH_WIN = 21       # moving-average window (samples) for spiral radius
RESAMPLE_STEP = 0.75  # deg
TIER_OFF = [21.0, -21.0, 49.0, -49.0]
TIER_OFF_INNER = [21.0, 49.0, 77.0, 105.0, 133.0]
TIER_PAD_DEG = 1.2
SNAP_DU_MAX = 7.0     # deg: max |cluster u - predicted u| for a match
SNAP_DR_MAX = 70.0    # px: max radial distance cluster<->strand
SNAP_MIN_CLUSTERS = 2
SNAP_MIN_AREA = 500.0  # px^2 total bbox area of matched clusters
STAR_R = 9.0

F = lambda x: f"{x:.2f}"


def load_inputs():
    with open(GEO_PATH) as fh:
        geo = json.load(fh)
    with open(ELEM_PATH) as fh:
        elem = json.load(fh)
    return geo, elem


def unwrap_polyline(poly):
    """R13 polylines are wrapped [0,360) with monotonically increasing theta."""
    out = []
    offset = 0.0
    prev = None
    for th, r in poly:
        if prev is not None and th < prev - 180.0:
            offset += 360.0
        prev = th
        out.append((th + offset, float(r)))
    return out


def smooth_series(pts, win):
    """Centered moving average over the radius column, edge-clamped."""
    n = len(pts)
    half = win // 2
    rs = [p[1] for p in pts]
    sm = []
    for i in range(n):
        a, b = max(0, i - half), min(n, i + half + 1)
        sm.append((pts[i][0], sum(rs[a:b]) / (b - a)))
    return sm


class Strand:
    """Measured spiral strand: duplication-corrected, segmented, smoothed.

    Turn-duplication correction: the R13 spiral0 polyline contains a +90 px
    radius discontinuity with an 18.5 deg tracking coast at u~1292-1310; the
    tail beyond it RE-TRACES the previous turn once (its radii duplicate the
    head's at u-360, and only after shifting the tail by -360 deg do the
    strand's axis crossings land on the plate's inert-gas hub ladder:
    Betanon 157<->~166, Gammanon 214<->~210, Hydron 273<->~288, Helium
    328<->~332, Neon 400<->~410 px). The correction is detected from the
    data itself: at a radius jump > 60 px with an angular gap > 10 deg, the
    tail is shifted -360 deg iff its median radius difference against the
    head over the overlap is < 30 px. Wrapped angles (hence drawn ink
    positions) are unchanged; only the turn labelling is repaired. The plate
    spiral is therefore ~4.8 physical turns, not the 5.81 recorded in the
    frozen input (reported upstream, never edited there).

    The corrected polyline is then split wherever consecutive samples jump by
    more than 40 px in radius or 15 deg in angle; each segment is smoothed
    independently so a measured discontinuity is never smeared into a fake
    wave. Segments are drawn as separate subpaths; label placement
    interpolates across gaps.
    """

    @staticmethod
    def _fix_turn_duplication(pts):
        for i in range(1, len(pts)):
            du = pts[i][0] - pts[i - 1][0]
            dr = pts[i][1] - pts[i - 1][1]
            if abs(dr) > 60.0 and du > 10.0:
                head, tail = pts[:i], [(u - 360.0, r) for u, r in pts[i:]]
                hu = [p[0] for p in head]
                diffs = []
                for u, r in tail:
                    if hu[0] <= u <= hu[-1]:
                        lo, hi = 0, len(hu) - 1
                        while hi - lo > 1:
                            mid = (lo + hi) // 2
                            if hu[mid] <= u:
                                lo = mid
                            else:
                                hi = mid
                        t = (u - hu[lo]) / (hu[hi] - hu[lo])
                        r_head = head[lo][1] + t * (head[hi][1] - head[lo][1])
                        diffs.append(abs(r - r_head))
                if diffs and sorted(diffs)[len(diffs) // 2] < 30.0:
                    return sorted(head + tail), True
        return pts, False

    def __init__(self, poly, win):
        pts = unwrap_polyline(poly)
        pts.sort(key=lambda p: p[0])
        pts, self.duplication_corrected = self._fix_turn_duplication(pts)
        # merge duplicate u values
        merged = []
        for u, r in pts:
            if merged and abs(u - merged[-1][0]) < 1e-9:
                merged[-1] = (u, (merged[-1][1] + r) / 2.0)
            else:
                merged.append((u, r))
        self.raw = merged
        segments = [[merged[0]]]
        for prev, cur in zip(merged, merged[1:]):
            if abs(cur[1] - prev[1]) > 40.0 or cur[0] - prev[0] > 15.0:
                segments.append([cur])
            else:
                segments[-1].append(cur)
        self.segments = [smooth_series(seg, win) for seg in segments if len(seg) >= 3]
        self.smooth = [p for seg in self.segments for p in seg]
        self.u_min = merged[0][0]
        self.u_max = merged[-1][0]
        # smoothing residual vs raw measured polyline (per-segment)
        devs = []
        for raw_seg, sm_seg in zip((s for s in segments if len(s) >= 3), self.segments):
            devs.extend(abs(a[1] - b[1]) for a, b in zip(raw_seg, sm_seg))
        self.smooth_rms = math.sqrt(sum(d * d for d in devs) / len(devs))
        self.smooth_max = max(devs)

    def r_of_u(self, u):
        pts = self.smooth
        if u <= pts[0][0]:
            return pts[0][1]
        if u >= pts[-1][0]:
            return pts[-1][1]
        lo, hi = 0, len(pts) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if pts[mid][0] <= u:
                lo = mid
            else:
                hi = mid
        (u0, r0), (u1, r1) = pts[lo], pts[hi]
        t = (u - u0) / (u1 - u0)
        return r0 + t * (r1 - r0)

    def sample_segments(self, step):
        """Per-segment resampled points: list of [(u, r), ...]."""
        out = []
        for seg in self.segments:
            u0, u1 = seg[0][0], seg[-1][0]
            pts = []
            u = u0
            while u < u1:
                pts.append((u, self.r_of_u(u)))
                u += step
            pts.append((u1, self.r_of_u(u1)))
            out.append(pts)
        return out


def xy(cx, cy, ang_deg, r):
    a = math.radians(ang_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


# ---------------------------------------------------------------- placement
GAS_U = {2: 1800.0, 3: 1620.0, 4: 1440.0, 5: 1260.0,
         6: 1080.0, 7: 900.0, 8: 720.0, 9: 540.0, 10: 360.0}
OMEGANON_U = 180.0
OCT1_INNER_U = 2070.0
OCT1_CREST_U = 1890.0


def predict_rows(elem):
    """Return list of row dicts with predicted unwrapped u (None = center hub)."""
    rows = []
    for oct_block in elem["octaves"]:
        k = oct_block["octave"]
        rlist = oct_block["rows"]
        n = len(rlist)
        crest = next(i for i, r in enumerate(rlist) if "\u2021" in r["position_col"])
        for i, r in enumerate(rlist):
            rec = {"octave": k, "idx": i, "row": r, "kind": "arc",
                   "u": None, "placement": "computed"}
            if k == 1:
                if i == 0:
                    rec["kind"] = "center"
                elif i <= crest:
                    rec["u"] = OCT1_INNER_U - (OCT1_INNER_U - OCT1_CREST_U) * i / crest
                else:
                    m = n - 1 - crest
                    rec["u"] = OCT1_CREST_U - 90.0 * (i - crest) / (m + 1)
            else:
                u0 = GAS_U[k]
                last_gas = (k == 10 and i == n - 1)
                if i == 0:
                    rec["kind"] = "gas"
                    rec["u"] = u0
                elif last_gas:
                    rec["kind"] = "gas"
                    rec["u"] = OMEGANON_U
                elif i <= crest:
                    rec["u"] = u0 - 90.0 * i / crest
                else:
                    m = (n - 2 - crest) if k == 10 else (n - 1 - crest)
                    rec["u"] = (u0 - 90.0) - 90.0 * (i - crest) / (m + 1)
            rows.append(rec)
    return rows


def snap_rows(rows, strand, labels, cx, cy):
    """Snap predicted arc rows to measured label clusters.

    A cluster votes for the spiral turn whose radius is nearest one of its
    radial extremes (<= SNAP_DR_MAX px). Each cluster is assigned to the single
    closest predicted row within SNAP_DU_MAX deg of unwrapped angle. A row
    becomes "measured" iff >= SNAP_MIN_CLUSTERS clusters totalling >=
    SNAP_MIN_AREA px^2 of bbox area matched; its angle is snapped to the
    bbox-area-weighted mean cluster angle (radius stays on the strand).
    """
    arc_rows = [r for r in rows if r["kind"] == "arc"]
    cands = []  # (cluster u, area, dr)
    for lab in labels:
        x, y, w, h = lab["bbox"]
        lx, ly = x + w / 2.0, y + h / 2.0
        r_mid = (lab["r_inner_px"] + lab["r_outer_px"]) / 2.0
        if not (118.0 < r_mid < 770.0):
            continue
        ang = math.degrees(math.atan2(ly - cy, lx - cx)) % 360.0
        best = None
        k0 = int((strand.u_min - ang) // 360.0)
        for k in range(k0, k0 + 8):
            u = ang + 360.0 * k
            if u < strand.u_min - 20 or u > strand.u_max + 20:
                continue
            rs = strand.r_of_u(u)
            dr = min(abs(rs - lab["r_inner_px"]), abs(rs - r_mid),
                     abs(rs - lab["r_outer_px"]))
            if dr <= SNAP_DR_MAX and (best is None or dr < best[2]):
                best = (u, float(w * h), dr)
        if best:
            cands.append(best)
    # assign each cluster to its nearest predicted row
    votes = {}  # row index in arc_rows -> [(u, area)]
    for u, area, dr in cands:
        best_i, best_du = None, SNAP_DU_MAX
        for i, rec in enumerate(arc_rows):
            du = abs(rec["u"] - u)
            if du <= best_du:
                best_i, best_du = i, du
        if best_i is not None:
            votes.setdefault(best_i, []).append((u, area))
    for i, vs in sorted(votes.items()):
        if len(vs) >= SNAP_MIN_CLUSTERS and sum(a for _, a in vs) >= SNAP_MIN_AREA:
            tot = sum(a for _, a in vs)
            arc_rows[i]["u"] = sum(u * a for u, a in vs) / tot
            arc_rows[i]["placement"] = "measured"
    # ordering guard: u must decrease monotonically in dataset order
    prev_u = None
    for rec in rows:
        if rec["kind"] != "arc":
            prev_u = rec["u"] if rec["u"] is not None else prev_u
            continue
        if prev_u is not None and rec["u"] >= prev_u:
            # revert a snap that inverted the printed order
            rec["placement"] = "computed"
            rec["u"] = prev_u - 1.0
        prev_u = rec["u"]


def place_gases(rows, strand):
    """Place inert-gas hubs at the corrected strand's axis crossings.

    After the turn-duplication correction the strand's horizontal-axis
    crossings match the plate's hub-circle ladder within ~20 px, which is
    tighter than any confident match available from the geometry file's
    unlabelled clusters (the plate's hub circles do not survive as clean
    single components there), so hubs are placed computed, on the strand.
    Hub circle radius follows the plate's proportion (~0.10 x axis radius,
    clamped 36..70 px).
    """
    for rec in rows:
        if rec["kind"] != "gas":
            continue
        rec["r"] = strand.r_of_u(rec["u"])
        rec["hub_r"] = max(36.0, min(70.0, 0.10 * rec["r"]))


# ---------------------------------------------------------------- layout
def text_width(row):
    name = row["name"]
    tag = row["position_col"]
    return OSWALD_ADV * (FS_NAME * len(name) + FS_TAG * (len(tag) + 1))


def assign_tiers(rows, strand):
    """Greedy first-fit radial tiering in strand order (decreasing u = outward).

    Tier offsets position the CENTER of the glyph box radially from the strand;
    the textPath baseline is derived per hemisphere (on the south half glyphs
    extend inward from the baseline, on the north half outward), so a label
    never overpaints the strand it annotates. A tier is also refused when the
    label's arc would cross an inert-gas hub circle (12 px clearance).
    """
    caph = FS_NAME * OSWALD_CAP
    hubs = [(rec["u"], rec["r"], rec["hub_r"]) for rec in rows if rec["kind"] == "gas"]
    arc = sorted((r for r in rows if r["kind"] == "arc"), key=lambda r: -r["u"])
    occupied = {}  # tier index -> list of (u_lo, u_hi)

    def hits_hub(u, r_t, half_deg):
        for hu, hr, hrad in hubs:
            if abs(r_t - hr) > hrad + caph / 2.0 + 12.0:
                continue
            d_ang = abs((u - hu + 180.0) % 360.0 - 180.0)
            if (d_ang - half_deg) * math.pi / 180.0 * r_t < hrad + 12.0:
                return True
        return False

    for rec in arc:
        r_strand = strand.r_of_u(rec["u"])
        offs = TIER_OFF_INNER if r_strand < 240.0 else TIER_OFF
        w = text_width(rec["row"])
        placed = False
        for t, off in enumerate(offs):
            r_t = r_strand + off  # glyph-box center radius
            half = math.degrees(w / (2.0 * r_t)) + TIER_PAD_DEG
            lo, hi = rec["u"] - half, rec["u"] + half
            if hits_hub(rec["u"], r_t, half - TIER_PAD_DEG):
                continue
            if all(hi <= a or lo >= b for a, b in occupied.get((id(offs), t), [])):
                occupied.setdefault((id(offs), t), []).append((lo, hi))
                rec["r_box"] = r_t
                rec["tier"] = t
                placed = True
                break
        if not placed:
            # every hub-clear tier is occupied (or the hub blocks all tiers,
            # as on the plate where names crowd against the circles): take
            # the free tier with the largest hub clearance; only if none is
            # free either, force the outermost tier (counted in report).
            best = None
            for t, off in enumerate(offs):
                r_t = r_strand + off
                half = math.degrees(w / (2.0 * r_t)) + TIER_PAD_DEG
                lo, hi = rec["u"] - half, rec["u"] + half
                if all(hi <= a or lo >= b for a, b in occupied.get((id(offs), t), [])):
                    clear = min((abs(r_t - hr) for _, hr, _ in hubs), default=1e9)
                    if best is None or clear > best[0]:
                        best = (clear, t, r_t, lo, hi)
            if best is not None:
                _, t, r_t, lo, hi = best
                occupied.setdefault((id(offs), t), []).append((lo, hi))
                rec["r_box"] = r_t
                rec["tier"] = t
            else:
                rec["r_box"] = r_strand + offs[-1]
                rec["tier"] = len(offs) - 1
                rec["forced"] = True
        south = math.sin(math.radians(rec["u"] % 360.0)) > 0.0
        rec["r_label"] = rec["r_box"] + (caph / 2.0 if south else -caph / 2.0)
        rec["r_strand"] = r_strand
    return sum(1 for r in arc if r.get("forced"))


# ---------------------------------------------------------------- svg emit
def star_path(x, y):
    seg = []
    for ang in (90.0, 150.0, 30.0):
        a = math.radians(ang)
        dx, dy = STAR_R * math.cos(a), STAR_R * math.sin(a)
        seg.append(f"M{F(x-dx)} {F(y-dy)}L{F(x+dx)} {F(y+dy)}")
    return "".join(seg)


def arc_path(cx, cy, r, theta_c, half_deg):
    """Readable arc through wrapped angle theta_c spanning +-half_deg."""
    south = math.sin(math.radians(theta_c)) > 0.0
    if south:
        a1, a2, sweep = theta_c + half_deg, theta_c - half_deg, 0
    else:
        a1, a2, sweep = theta_c - half_deg, theta_c + half_deg, 1
    x1, y1 = xy(cx, cy, a1, r)
    x2, y2 = xy(cx, cy, a2, r)
    return f"M{F(x1)} {F(y1)}A{F(r)} {F(r)} 0 0 {sweep} {F(x2)} {F(y2)}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(geo, elem, strand, strand2, rows, forced_count):
    cx, cy = geo["center"]
    out = []
    a = out.append
    a('<?xml version="1.0" encoding="UTF-8"?>')
    a(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      f'viewBox="{VIEW_X0} {VIEW_Y0} {VIEW_S} {VIEW_S}" width="{VIEW_S}" height="{VIEW_S}">')
    # N2 notice, verbatim (data/license_drafts/notice_conventions.md). Fixed
    # strings only: the renderer stays byte-deterministic.
    a('<metadata>')
    a('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
      'xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:cc="http://creativecommons.org/ns#">')
    a('<cc:Work rdf:about="">')
    a('<dc:title>Russell Periodic Chart (1926) \u2014 original redraw</dc:title>')
    a('<dc:source>https://www.loc.gov/item/27004508/</dc:source>')
    a('<dc:rights>' + esc(N2_NOTICE) + '</dc:rights>')
    a('<cc:license rdf:resource="https://creativecommons.org/licenses/by-nc/4.0/"/>')
    a('</cc:Work>')
    a('</rdf:RDF>')
    a('</metadata>')
    a('<desc>Parametric redraw of The Russell Periodic Chart of Atomic Weights '
      '(The Universal One, 1926, facing p.90; LoC scan p0016). Generated from '
      'data/russell_1926_elements.json and data/chart_geometry.json by '
      'tools/render_chart.py. User units equal scan pixels of the R13 measurement '
      'frame. Prose ring texts, the FEMALE/MALE display letters and marginal '
      'annotations of the plate are not element data and are not reproduced.</desc>')
    a('<style>')
    a("text{font-family:'Oswald','Archivo Narrow','Libre Franklin','DejaVu Sans',sans-serif;"
      "fill:#1a1a1a;}")
    a('.it{font-style:italic}.sc{font-variant:small-caps}')
    a('</style>')
    a(f'<rect x="{VIEW_X0}" y="{VIEW_Y0}" width="{VIEW_S}" height="{VIEW_S}" fill="#ffffff"/>')

    # measured concentric rings (inner mass circle + outer octave bands)
    a('<g id="rings" fill="none" stroke="#1a1a1a">')
    for ring in geo["rings"]:
        a(f'<circle cx="{F(cx)}" cy="{F(cy)}" r="{F(ring["radius_px"])}" '
          f'stroke-width="{F(ring["stroke_width_px"])}" data-ring="{ring["id"]}"/>')
    a('</g>')

    # measured sector axes
    a('<g id="sectors" stroke="#1a1a1a" stroke-width="5">')
    for sec in geo["sectors"]:
        x1, y1 = xy(cx, cy, sec["angle_deg"], sec["r_inner_px"])
        x2, y2 = xy(cx, cy, sec["angle_deg"], sec["r_outer_px"])
        a(f'<line x1="{F(x1)}" y1="{F(y1)}" x2="{F(x2)}" y2="{F(y2)}"/>')
    a('</g>')

    # spiral strands (smoothed measured polylines)
    for sid, st, wdt in (("spiral-main", strand, 4.0), ("spiral-second", strand2, 3.0)):
        d = []
        for pts in st.sample_segments(RESAMPLE_STEP):
            for i, (u, r) in enumerate(pts):
                x, y = xy(cx, cy, u, r)
                d.append(f'{"M" if i == 0 else "L"}{F(x)} {F(y)}')
        a(f'<path id="{sid}" d="{"".join(d)}" fill="none" stroke="#1a1a1a" '
          f'stroke-width="{F(wdt)}" stroke-linejoin="round" stroke-linecap="round"/>')

    # element labels
    defs = ['<defs>']
    body = []
    lab_i = 0
    for rec in rows:
        row = rec["row"]
        typ = row["typography"]
        cls = ' class="it"' if typ == "italic" else (' class="sc"' if typ == "smallcaps" else "")
        pos = esc(row["position_col"])
        name = esc(row["name"])
        grp = (f'<g data-octave="{rec["octave"]}" data-position="{pos}" '
               f'data-name="{name}" data-placement="{rec["placement"]}">')
        if rec["kind"] == "center":
            rec["placement"] = "measured"  # placed at the measured fitted center
            grp = grp.replace('data-placement="computed"', 'data-placement="measured"')
            body.append(grp)
            body.append(f'<path d="{star_path(cx, cy - 62.0)}" stroke="#1a1a1a" '
                        f'stroke-width="2.5" stroke-linecap="round" fill="none"/>')
            body.append(f'<text x="{F(cx)}" y="{F(cy + 10.0)}" font-size="{FS_CENTER}" '
                        f'text-anchor="middle"{cls}>{name}</text>')
            body.append(f'<text x="{F(cx)}" y="{F(cy + 44.0)}" font-size="{FS_TAG}" '
                        f'text-anchor="middle">{pos}</text>')
            body.append('</g>')
            continue
        if rec["kind"] == "gas":
            hx, hy = xy(cx, cy, rec["u"] % 360.0, rec["r"])
            body.append(grp)
            body.append(f'<circle cx="{F(hx)}" cy="{F(hy)}" r="{F(rec["hub_r"])}" '
                        f'fill="#ffffff" stroke="#1a1a1a" stroke-width="6"/>')
            body.append(f'<path d="{star_path(hx, hy - rec["hub_r"] - 14.0)}" '
                        f'stroke="#1a1a1a" stroke-width="2.5" stroke-linecap="round" fill="none"/>')
            body.append(f'<text x="{F(hx)}" y="{F(hy + 9.0)}" font-size="{FS_GAS}" '
                        f'text-anchor="middle"{cls}>{name}</text>')
            body.append(f'<text x="{F(hx)}" y="{F(hy + 38.0)}" font-size="{FS_TAG}" '
                        f'text-anchor="middle">{pos}</text>')
            body.append('</g>')
            continue
        # arc label
        theta = rec["u"] % 360.0
        r_lab = rec["r_label"]
        w = text_width(row)
        half = math.degrees(w / (2.0 * r_lab)) + 3.0
        pid = f"lp{lab_i:03d}"
        lab_i += 1
        defs.append(f'<path id="{pid}" d="{arc_path(cx, cy, r_lab, theta, half)}" fill="none"/>')
        sx, sy = xy(cx, cy, theta, rec["r_strand"])
        body.append(grp)
        body.append(f'<path d="{star_path(sx, sy)}" stroke="#1a1a1a" stroke-width="2.5" '
                    f'stroke-linecap="round" fill="none"/>')
        body.append(f'<text font-size="{FS_NAME}"{cls}><textPath xlink:href="#{pid}" '
                    f'startOffset="50%" text-anchor="middle">{name}'
                    f'<tspan font-size="{FS_TAG}" font-style="normal"> {pos}</tspan>'
                    f'</textPath></text>')
        body.append('</g>')
    defs.append('</defs>')
    a("\n".join(defs))
    a('<g id="elements">')
    a("\n".join(body))
    a('</g>')
    a('</svg>')
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- overlay proof
def overlay_proof(geo, strand, strand2):
    import numpy as np
    from PIL import Image

    png_tmp = "/tmp/r21_redraw_raster.png"
    subprocess.run(
        ["inkscape", SVG_PATH, "--export-type=png",
         f"--export-filename={png_tmp}",
         f"--export-width={VIEW_S}", f"--export-height={VIEW_S}",
         "--export-background=#ffffff", "--export-background-opacity=1.0"],
        check=True, capture_output=True)

    scan = Image.open(SCAN_PATH).convert("L")
    arr = np.asarray(scan, dtype=np.float64)
    H, W = arr.shape
    cx, cy = geo["center"]
    # rendered raster placed into the scan's pixel frame
    raster = Image.open(png_tmp).convert("L")
    rast_page = np.full((H, W), 255.0)
    rast_page[VIEW_Y0:VIEW_Y0 + VIEW_S, VIEW_X0:VIEW_X0 + VIEW_S] = \
        np.asarray(raster, dtype=np.float64)

    def bilinear(img, xs, ys):
        xs = np.clip(xs, 0, W - 1.001)
        ys = np.clip(ys, 0, H - 1.001)
        x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
        fx = xs - x0; fy = ys - y0
        return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
                + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)

    def xcorr_offsets(samples, r_lo_off, r_hi_off):
        """Radial alignment offset (scan minus render) per angular sample.

        The window [r+r_lo_off, r+r_hi_off] is profiled in BOTH rasters; the
        offset is the ink-profile cross-correlation peak (search +-12 px,
        0.25 px steps, parabolic refinement) — robust for the plate's double
        rules (gaps down to 5.5 px), which are windowed as whole groups so
        both rasters see the same multi-stroke structure. A sample is used
        only where BOTH windows are edge-clean (>= 170 at both ends; rejects
        crossing lettering / neighbouring curves) and both contain ink
        (min < 140).
        """
        offs = []
        d_grid = np.arange(r_lo_off, r_hi_off + 0.001, 0.5)
        shifts = np.arange(-12.0, 12.001, 0.25)
        for th, r in samples:
            a = math.radians(th)
            rr = r + d_grid
            xs = cx + rr * math.cos(a)
            ys = cy + rr * math.sin(a)
            p_scan = bilinear(arr, xs, ys)
            p_rend = bilinear(rast_page, xs, ys)
            if p_scan.min() > 140.0 or p_rend.min() > 140.0:
                continue
            if (min(p_scan[0], p_scan[1]) < 170.0 or min(p_scan[-1], p_scan[-2]) < 170.0
                    or min(p_rend[0], p_rend[1]) < 170.0
                    or min(p_rend[-1], p_rend[-2]) < 170.0):
                continue  # a window is contaminated by neighbouring ink
            w_scan = np.clip(200.0 - p_scan, 0.0, None)
            w_rend = np.clip(200.0 - p_rend, 0.0, None)
            if w_scan.sum() < 20.0 or w_rend.sum() < 20.0:
                continue
            corr = np.array([
                float((w_scan * np.interp(d_grid, d_grid - s, w_rend,
                                          left=0.0, right=0.0)).sum())
                for s in shifts])
            i = int(np.argmax(corr))
            sh = 0.0
            if 0 < i < len(corr) - 1:
                den = corr[i - 1] - 2 * corr[i] + corr[i + 1]
                if abs(den) > 1e-9:
                    sh = max(-1.0, min(1.0, 0.5 * (corr[i - 1] - corr[i + 1]) / den))
            offs.append(float(shifts[i]) + sh * 0.25)
        return offs

    report = {}
    # rings: group double rules (gap <= 16 px) and window each group whole
    radii = sorted((rg["radius_px"] for rg in geo["rings"]))
    groups = [[radii[0]]]
    for r in radii[1:]:
        if r - groups[-1][-1] <= 16.0:
            groups[-1].append(r)
        else:
            groups.append([r])
    ring_offs = []
    n_ring_samples = 0
    for grp in groups:
        mid = (grp[0] + grp[-1]) / 2.0
        half = (grp[-1] - grp[0]) / 2.0 + 10.0
        samples = [(k * 0.5, mid) for k in range(720)]
        n_ring_samples += len(samples)
        ring_offs.extend(xcorr_offsets(samples, -half, half))
    ring_offs = np.array(ring_offs)
    report["rings_rms_px"] = float(np.sqrt(np.mean(ring_offs ** 2)))
    report["rings_max_px"] = float(np.max(np.abs(ring_offs)))
    report["rings_coverage"] = round(len(ring_offs) / n_ring_samples, 3)
    report["rings_groups"] = len(groups)

    for key, st in (("spiral_main", strand), ("spiral_second", strand2)):
        samples = [(u % 360.0, r) for seg in st.sample_segments(1.0) for u, r in seg]
        offs = np.array(xcorr_offsets(samples, -10.0, 10.0))
        report[f"{key}_rms_px"] = float(np.sqrt(np.mean(offs ** 2)))
        report[f"{key}_max_px"] = float(np.max(np.abs(offs)))
        report[f"{key}_coverage"] = round(len(offs) / len(samples), 3)

    # 50% opacity overlay: redraw ink tinted red over the raw facsimile
    base = np.stack([arr, arr, arr], axis=-1)
    ink = 255.0 - rast_page
    svg_rgb = np.stack([255.0 - 0.25 * ink, 255.0 - ink, 255.0 - ink], axis=-1)
    blend = (0.5 * base + 0.5 * svg_rgb).clip(0, 255).astype(np.uint8)
    Image.fromarray(blend).save(PROOF_PATH)
    report["proof_png"] = os.path.relpath(PROOF_PATH, ROOT)
    return report


# ---------------------------------------------------------------- main
def main():
    geo, elem = load_inputs()
    cx, cy = geo["center"]
    strand = Strand(geo["spirals"][0]["polyline_theta_deg_r_px"], SMOOTH_WIN)
    strand2 = Strand(geo["spirals"][1]["polyline_theta_deg_r_px"], SMOOTH_WIN)

    rows = predict_rows(elem)
    snap_rows(rows, strand, geo["labels"], cx, cy)
    place_gases(rows, strand)
    forced = assign_tiers(rows, strand)

    svg = build_svg(geo, elem, strand, strand2, rows, forced)
    os.makedirs(os.path.dirname(SVG_PATH), exist_ok=True)
    with open(SVG_PATH, "w") as fh:
        fh.write(svg)

    n_meas = sum(1 for r in rows if r["placement"] == "measured" or r["kind"] == "center")
    n_comp = len(rows) - n_meas
    scale_1080 = 1080.0 / VIEW_S
    report = {
        "svg": os.path.relpath(SVG_PATH, ROOT),
        "rows_total": len(rows),
        "placement_measured": n_meas,
        "placement_computed": n_comp,
        "labels_forced_to_last_tier": forced,
        "min_font_size_units": FS_TAG,
        "min_xheight_px_at_1080p": round(FS_TAG * OSWALD_XH * scale_1080, 2),
        "spiral0_turn_duplication_corrected": strand.duplication_corrected,
        "frozen_input_notes": [
            "data/chart_geometry.json spiral0: the polyline tail beyond the "
            "u~1292-1310 discontinuity re-traces the previous turn once "
            "(duplicated radii; axis crossings match the plate's inert-gas "
            "hub ladder only after a -360 deg tail shift). Physical spiral "
            "is ~4.8 turns, not 5.81. Reported, input not modified."
        ] if strand.duplication_corrected else [],
        "spiral_smoothing": {
            "window_samples": SMOOTH_WIN,
            "main_rms_vs_measured_px": round(strand.smooth_rms, 2),
            "main_max_vs_measured_px": round(strand.smooth_max, 2),
            "second_rms_vs_measured_px": round(strand2.smooth_rms, 2),
            "second_max_vs_measured_px": round(strand2.smooth_max, 2),
        },
    }
    if "--overlay" in sys.argv:
        ov = overlay_proof(geo, strand, strand2)
        report["overlay"] = {k: (round(v, 2) if isinstance(v, float) else v)
                             for k, v in ov.items()}
    print(json.dumps(report, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
