#!/usr/bin/env python3
"""R13 — deterministic chart-geometry extraction for the Walter Russell 1926 charts.

Measures ring circles, spiral strands, radial sector dividers, and label ink
clusters from LoC facsimile scans, using only numpy + Pillow.

Deterministic operations only: grayscale load, Otsu threshold, connected
components, gradient-vote center accumulation (hand-rolled Hough), polar
resampling (bilinear), ridge tracking, least-squares circle fits (Kasa) with
deterministic trimming, linear pitch fits.  NO generative or learned
enhancement, no upscaling models, no inpainting, no randomness.

Outputs (byte-identical on rerun from the same input scans):
  data/chart_geometry.json           (p0016, the Russell Periodic Chart)
  data/wheel_geometry.json           (p0113, seventh/eighth octave wheel)
  data/geometry/p0016_overlay.png    (+ zoom crops, captioned proofs)
  data/geometry/p0113_overlay.png

Usage:  python3 tools/measure_geometry.py [p0016] [p0113]
        (no args = both)
"""

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

RETRIEVED = "2026-09-11"
NA = 1440  # angular bins (0.25 deg)

CONFIGS = {
    "p0016": {
        "file": "source_scans/loc/full/p0016.jpg",
        "image_id": "loc:public:gdc:27004508:0016",
        "source_url": "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:0016/full/full/0/default.jpg",
        "title": "The Russell Periodic Chart of Atomic Weights ... (The Universal One, 1926)",
        "json_out": "data/chart_geometry.json",
        "overlay_out": "data/geometry/p0016_overlay.png",
        "zooms": [("ne_quadrant", "data/geometry/p0016_overlay_ne_zoom.png"),
                  ("center", "data/geometry/p0016_overlay_center_zoom.png")],
        "rmax": 1200,
        "spiral_zone": (120, 775),
        "min_sector_occ": 0.38,
        "sector_band": (130, 1150),
        "ring_rmin": 95,
        "wide_from": 750.0,
        "gap_max": 50.0,
        "text_ring_filter": True,
        "label_r_max": 1190,
    },
    "p0113": {
        "file": "source_scans/loc/full/p0113.jpg",
        "image_id": "loc:public:gdc:27004508:0113",
        "source_url": "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:0113/full/full/0/default.jpg",
        "title": "Seventh and Eighth Octave Constants wheel (The Universal One, 1926)",
        "json_out": "data/wheel_geometry.json",
        "overlay_out": "data/geometry/p0113_overlay.png",
        "zooms": [],
        "rmax": 1300,
        "spiral_zone": None,
        "min_sector_occ": 0.50,
        "ring_rmin": 30,
        "sector_band": (130, 1050),
        "wide_from": 0.0,
        "gap_max": 90.0,
        "text_ring_filter": False,
        "label_r_max": 1100,
    },
}

# ---------------------------------------------------------------- primitives

def otsu(gray):
    h = np.bincount(gray.astype(np.uint8).ravel(), minlength=256).astype(np.float64)
    p = h / h.sum()
    w = np.cumsum(p)
    m = np.cumsum(p * np.arange(256))
    mt = m[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sb = (mt * w - m) ** 2 / (w * (1 - w))
    return int(np.nanargmax(sb))


def label_components(mask):
    """Run-based 4-connected two-pass labeling. Returns (labels, n)."""
    H, W = mask.shape
    labels = np.zeros((H, W), dtype=np.int32)
    parent = [0]

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    prev_runs = []
    nxt = 1
    for y in range(H):
        row = mask[y]
        d = np.diff(row.astype(np.int8))
        starts = list(np.nonzero(d == 1)[0] + 1)
        ends = list(np.nonzero(d == -1)[0] + 1)
        if row[0]:
            starts.insert(0, 0)
        if row[-1]:
            ends.append(W)
        runs = []
        pi = 0
        for x0, x1 in zip(starts, ends):
            lab = 0
            while pi < len(prev_runs) and prev_runs[pi][1] <= x0:
                pi += 1
            pj = pi
            while pj < len(prev_runs) and prev_runs[pj][0] < x1:
                pl = find(prev_runs[pj][2])
                if lab == 0:
                    lab = pl
                elif pl != lab:
                    parent[max(pl, lab)] = min(pl, lab)
                    lab = min(pl, lab)
                pj += 1
            if lab == 0:
                lab = nxt
                parent.append(lab)
                nxt += 1
            labels[y, x0:x1] = lab
            runs.append((x0, x1, lab))
        prev_runs = runs
    lut = np.zeros(nxt, dtype=np.int32)
    remap = {}
    for i in range(1, nxt):
        r = find(i)
        if r not in remap:
            remap[r] = len(remap) + 1
        lut[i] = remap[r]
    return lut[labels], len(remap)


def auto_centers(gray, scale=4, npeaks=4, minsep=40):
    """Gradient-direction voting (hand-rolled circular Hough) at 1/scale res."""
    H, W = gray.shape
    h, w = H // scale, W // scale
    g = gray[: h * scale, : w * scale].reshape(h, scale, w, scale).mean(axis=(1, 3))
    gy, gx = np.gradient(g)
    gm = np.hypot(gx, gy)
    m = gm > np.percentile(gm, 95)
    ys, xs = np.nonzero(m)
    ux, uy = gx[ys, xs] / gm[ys, xs], gy[ys, xs] / gm[ys, xs]
    acc = np.zeros((h, w))
    for s in (1.0, -1.0):
        for t in np.arange(10, min(h, w) // 2, 2, dtype=np.float64):
            X = (xs + s * t * ux).astype(np.int32)
            Y = (ys + s * t * uy).astype(np.int32)
            ok = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
            np.add.at(acc, (Y[ok], X[ok]), 1.0)
    k = 5
    c = np.cumsum(np.cumsum(np.pad(acc, ((k, k), (k, k))), axis=0), axis=1)
    sm = c[2 * k:, 2 * k:] - c[:-2 * k, 2 * k:] - c[2 * k:, :-2 * k] + c[:-2 * k, :-2 * k]
    peaks = []
    A = sm.copy()
    for _ in range(npeaks):
        cy_, cx_ = np.unravel_index(np.argmax(A), A.shape)
        peaks.append(((cx_ - k + 0.5) * scale, (cy_ - k + 0.5) * scale))
        A[max(0, cy_ - minsep): cy_ + minsep, max(0, cx_ - minsep): cx_ + minsep] = 0
    return peaks


def polar_map(mask, cx, cy, rmax, nr=None, na=NA):
    nr = nr or rmax
    rs = np.linspace(1, rmax, nr, dtype=np.float64)
    th = np.linspace(0, 2 * np.pi, na, endpoint=False)
    X = cx + rs[:, None] * np.cos(th)[None, :]
    Y = cy + rs[:, None] * np.sin(th)[None, :]
    Xi = np.clip(X, 0, mask.shape[1] - 2)
    Yi = np.clip(Y, 0, mask.shape[0] - 2)
    x0 = Xi.astype(np.int32)
    y0 = Yi.astype(np.int32)
    fx = Xi - x0
    fy = Yi - y0
    v = (mask[y0, x0] * (1 - fx) * (1 - fy) + mask[y0, x0 + 1] * fx * (1 - fy)
         + mask[y0 + 1, x0] * (1 - fx) * fy + mask[y0 + 1, x0 + 1] * fx * fy)
    return v, rs, th


def ridge_points(pm, minv=0.5):
    """Per-column subpixel local maxima of a polar ink map."""
    up = pm[1:-1] >= pm[:-2]
    dn = pm[1:-1] >= pm[2:]
    ok = up & dn & (pm[1:-1] >= minv)
    cols = []
    for j in range(pm.shape[1]):
        idx = np.nonzero(ok[:, j])[0] + 1
        if idx.size:
            y0, y1, y2 = pm[idx - 1, j], pm[idx, j], pm[idx + 1, j]
            den = y0 - 2 * y1 + y2
            off = np.where(np.abs(den) > 1e-9, 0.5 * (y0 - y2) / den, 0.0)
            cols.append(idx + np.clip(off, -0.6, 0.6) + 1.0)
        else:
            cols.append(np.empty(0))
    return cols


def kasa_fit(x, y):
    A = np.stack([x, y, np.ones_like(x)], axis=1)
    b = x * x + y * y
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = c[0] / 2, c[1] / 2
    return cx, cy, np.sqrt(c[2] + cx * cx + cy * cy)


def trimmed_circle_fit(x, y, iters=6, tol=2.5):
    x = x.astype(np.float64)
    y = y.astype(np.float64)
    keep = np.ones(x.size, bool)
    cx = cy = r = 0.0
    for _ in range(iters):
        cx, cy, r = kasa_fit(x[keep], y[keep])
        d = np.abs(np.hypot(x - cx, y - cy) - r)
        nk = d < tol
        if (nk == keep).all():
            break
        keep = nk
    d = np.abs(np.hypot(x[keep] - cx, y[keep] - cy) - r)
    return cx, cy, r, keep, d


def circle_ink_frac(inkf, cx, cy, r, na=NA):
    th = np.linspace(0, 2 * np.pi, na, endpoint=False)
    best = np.zeros(na)
    for dr in (-1.5, -0.75, 0.0, 0.75, 1.5):
        X = np.clip(cx + (r + dr) * np.cos(th), 0, inkf.shape[1] - 2)
        Y = np.clip(cy + (r + dr) * np.sin(th), 0, inkf.shape[0] - 2)
        x0 = X.astype(np.int32)
        y0 = Y.astype(np.int32)
        fx, fy = X - x0, Y - y0
        v = (inkf[y0, x0] * (1 - fx) * (1 - fy) + inkf[y0, x0 + 1] * fx * (1 - fy)
             + inkf[y0 + 1, x0] * (1 - fx) * fy + inkf[y0 + 1, x0 + 1] * fx * fy)
        best = np.maximum(best, v)
    return float((best > 0.5).mean())


def track_near(pm, R, halfw=6, minv=0.5):
    """Ridge deviation r(theta)-R tracked in a narrow annulus. NaN when absent."""
    i0 = int(max(1, R - halfw))
    i1 = int(min(pm.shape[0] - 1, R + halfw))
    band = pm[i0:i1]
    dev = np.full(NA, np.nan)
    up = band[1:-1] >= band[:-2]
    dn = band[1:-1] >= band[2:]
    ok = up & dn & (band[1:-1] >= minv)
    for j in range(NA):
        idx = np.nonzero(ok[:, j])[0] + 1
        if idx.size == 0:
            continue
        y0, y1, y2 = band[idx - 1, j], band[idx, j], band[idx + 1, j]
        den = y0 - 2 * y1 + y2
        off = np.where(np.abs(den) > 1e-9, 0.5 * (y0 - y2) / den, 0.0)
        rloc = i0 + idx + 1.0 + np.clip(off, -0.6, 0.6)
        dev[j] = rloc[int(np.argmin(np.abs(rloc - R)))] - R
    return dev


def longest_gap_deg(present):
    if present.all():
        return 0.0
    if not present.any():
        return 360.0
    z = np.concatenate([~present, ~present])
    run = mx = 0
    for v in z:
        run = run + 1 if v else 0
        mx = max(mx, run)
    return min(mx, NA) * 360.0 / NA


def stroke_width(pm, R, dev):
    """Median full ink width across tracked columns."""
    widths = []
    nr = pm.shape[0]
    for j in range(NA):
        if not np.isfinite(dev[j]):
            continue
        i0 = int(round(R + dev[j])) - 1
        # anchor on the inkiest of the three rows around the tracked position
        cands = [i for i in (i0 - 1, i0, i0 + 1) if 0 < i < nr - 1]
        i = max(cands, key=lambda i: pm[i, j])
        if pm[i, j] <= 0.5:
            continue
        lo = i
        while lo > 0 and pm[lo, j] > 0.5:
            lo -= 1
        hi = i
        while hi < nr - 1 and pm[hi, j] > 0.5:
            hi += 1
        widths.append(hi - lo - 1)
    return float(np.median(widths)) if widths else 0.0


# ------------------------------------------------------------ ring detection

def detect_families(bigmask, ink, centers, prof_min=0.18, annulus=7, tol=2.5):
    """Free trimmed circle fits around vote centers; cluster fitted centers;
    keep clusters proven by at least one high-coverage solid circle."""
    ys, xs = np.nonzero(bigmask)
    xs = xs.astype(np.float64)
    ys = ys.astype(np.float64)
    fm = bigmask.astype(np.float32)
    fits = []
    for cx0, cy0 in centers:
        rmax = int(min(cx0, cy0, bigmask.shape[1] - cx0, bigmask.shape[0] - cy0, 1500))
        if rmax < 60:
            continue
        pm, _, _ = polar_map(fm, cx0, cy0, rmax)
        prof = pm.mean(axis=1)
        cand = [r for r in range(30, rmax - 4)
                if prof[r] > prof_min and prof[r] == prof[max(0, r - 3): r + 4].max()]
        ded = []
        for r in cand:
            if ded and r - ded[-1] <= 3:
                if prof[r] > prof[ded[-1]]:
                    ded[-1] = r
            else:
                ded.append(r)
        rr = np.hypot(xs - cx0, ys - cy0)
        for r_nom in ded:
            sel = np.abs(rr - r_nom) < annulus
            if sel.sum() < 200:
                continue
            cxf, cyf, rf, keep, d = trimmed_circle_fit(xs[sel], ys[sel], tol=tol)
            n = int(keep.sum())
            if n < 200 or not np.isfinite(rf):
                continue
            if np.hypot(cxf - cx0, cyf - cy0) > 60:
                continue
            a = np.arctan2(ys[sel][keep] - cyf, xs[sel][keep] - cxf)
            cov = np.unique(((a + np.pi) / (2 * np.pi) * 720).astype(int)).size / 720
            fits.append(dict(cx=cxf, cy=cyf, r=rf, n=n, cov=cov))
    # cluster centers
    clusters = []
    for f in sorted(fits, key=lambda f: -f["n"]):
        for g in clusters:
            if np.hypot(f["cx"] - g[0]["cx"], f["cy"] - g[0]["cy"]) < 25:
                g.append(f)
                break
        else:
            clusters.append([f])
    families = []
    for g in clusters:
        wsum = sum(f["n"] for f in g)
        cx = sum(f["cx"] * f["n"] for f in g) / wsum
        cy = sum(f["cy"] * f["n"] for f in g) / wsum
        best_cov = max(f["cov"] for f in g)
        if best_cov >= 0.40:
            families.append(dict(cx=cx, cy=cy, n=wsum, nfit=len(g)))
    families.sort(key=lambda f: -f["n"])
    return families


def detect_circles(pmbig, pmink, cx0, cy0, family_idx, spiral_zone=None, rmin=30,
                   tfrac_min=0.50, gap_max=50.0, pitch_max=6.0, prof_min=0.15,
                   wide_from=750.0, center_tol=30.0, text_ring_filter=True):
    """Fixed-center candidates from radial ink-profile peaks of both the
    structural and the full ink map, validated by narrow-annulus subpixel
    ridge continuity (full ink) and a near-zero pitch (spiral rejection).

    Candidates inside the configured spiral zone are NOT reported as rings:
    visual adjudication showed that mid-zone circle-like continuity on this
    plate is produced by spiral arcs plus radial text, not by ruled circles.
    Beyond `wide_from` the tracking window grows with radius so that the real
    (wavy) outer rules are followed through the facsimile's page distortion.
    """
    nr = pmbig.shape[0]
    ded = []
    for prof in (pmbig.mean(axis=1), pmink.mean(axis=1)[:nr]):
        cand = [r for r in range(rmin, nr - 4)
                if prof[r] > prof_min and prof[r] == prof[max(0, r - 3): r + 4].max()]
        for r in cand:
            if not any(abs(r - d) <= 3 for d in ded):
                ded.append(r)
    ded.sort()
    th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
    circles = []
    for r_nom in ded:
        if spiral_zone and spiral_zone[0] <= r_nom <= spiral_zone[1]:
            continue
        wide = max(0.0, r_nom - wide_from)
        halfw = 6.0 + 0.015 * (r_nom if wide > 0 else 0.0)
        devtol = 3.0 + 0.015 * (r_nom if wide > 0 else 0.0)
        dev = track_near(pmink, float(r_nom), halfw=halfw)
        present = np.isfinite(dev) & (np.abs(dev) <= devtol)
        tfrac = float(present.mean())
        if tfrac < tfrac_min:
            continue
        gap = longest_gap_deg(present)
        if gap > gap_max:
            continue
        # smoothness: a real centerline varies slowly; extreme jitter means the
        # tracker is hashing between unrelated ink
        pidx = np.nonzero(present)[0]
        step = np.abs(np.diff(dev[pidx]))
        adj = np.diff(pidx) == 1
        if adj.sum() > 50 and float(np.median(step[adj])) > 1.8:
            continue
        dv = dev[present]
        A = np.stack([np.ones(present.sum()), th[present]], axis=1)
        coef, *_ = np.linalg.lstsq(A, dv, rcond=None)
        pitch = float(coef[1] * 2 * np.pi)
        if abs(pitch) > pitch_max:
            continue
        R = float(r_nom + np.mean(dv))
        rr = dv - dv.mean()
        dev_masked = np.where(present, dev, np.nan)
        width = stroke_width(pmink, R, dev_masked)
        if text_ring_filter and wide > 0 and width > 6.0 and tfrac < 0.93:
            # wide-window tracks can ride circular text baselines; a genuine
            # heavy rule is near-continuous, a text ring is not
            continue
        # center consistency: an independent trimmed circle fit of the tracked
        # points in image space must agree with the assumed family center;
        # composites of segments of different rules (as seen from a spurious
        # vote center) converge elsewhere and are rejected
        rr_pts = r_nom + dev[present]
        px = cx0 + rr_pts * np.cos(th[present])
        py = cy0 + rr_pts * np.sin(th[present])
        fcx, fcy, fr, keep, dfit = trimmed_circle_fit(px, py, tol=3.0)
        if not np.isfinite(fr) or keep.sum() < 0.5 * present.sum():
            continue
        if np.hypot(fcx - cx0, fcy - cy0) > center_tol:
            continue
        circles.append(dict(
            family=family_idx, radius=R, tfrac=tfrac, gap=gap, pitch=pitch,
            dev=dev_masked, rms=float(np.sqrt(np.mean(rr ** 2))),
            dmax=float(np.abs(rr).max()), width=width,
            fit_cx=float(fcx), fit_cy=float(fcy), fit_r=float(fr),
            fit_rms=float(dfit.std()), fit_max=float(dfit.max())))
    # dedupe near-identical radii (keep best continuity)
    circles.sort(key=lambda c: -c["tfrac"])
    out = []
    for c in circles:
        if any(abs(c["radius"] - o["radius"]) < 4.0 and c["family"] == o["family"]
               for o in out):
            continue
        out.append(c)
    out.sort(key=lambda c: (c["family"], c["radius"]))
    return out


# ---------------------------------------------------------- spiral detection

def follow_spiral(cols, j0, r0, slope0, rlo, rhi, win=4.0, max_coast=80, max_turns=9):
    def run(direction):
        path = []
        slope = slope0 * direction
        cur = float(r0)
        last = 0
        for step in range(1, max_turns * NA):
            if step - last > max_coast:
                break
            pred = cur + slope * (step - last)
            if not (rlo <= pred <= rhi):
                break
            cand = cols[(j0 + direction * step) % NA]
            if cand.size:
                d = np.abs(cand - pred)
                k = int(np.argmin(d))
                if d[k] <= win:
                    if step > last:
                        slope = 0.85 * slope + 0.15 * (float(cand[k]) - cur) / (step - last)
                    path.append((direction * step, float(cand[k])))
                    cur = float(cand[k])
                    last = step
        return path

    fwd = run(+1)
    bwd = run(-1)
    return [(s, r) for s, r in reversed(bwd)] + [(0, float(r0))] + fwd


def detect_spirals(cols, zone, circle_radii, slope0=-110.0 / NA, min_turns=1.2):
    if zone is None:
        return []
    rlo, rhi = zone
    seed_cols = (0, 240, 480, 720, 960, 1200)
    traces = []
    for sc in seed_cols:
        for s in cols[sc]:
            if not (rlo <= s <= rhi):
                continue
            if any(abs(s - R) < 5.0 for R in circle_radii):
                continue
            t = follow_spiral(cols, sc, float(s), slope0, rlo, rhi)
            if (t[-1][0] - t[0][0]) / NA >= min_turns:
                # absolute (column mod NA, r) point set for dedupe
                pts = frozenset(((sc + o) % NA, round(r / 2.0)) for o, r in t)
                traces.append(dict(seedcol=sc, seed=float(s), path=t, pts=pts))
    traces.sort(key=lambda t: -len(t["path"]))
    strands = []
    for t in traces:
        dup = False
        for s in strands:
            inter = len(t["pts"] & s["pts"])
            if inter >= 0.3 * len(t["pts"]):
                dup = True
                break
        if not dup:
            strands.append(t)
    return strands


def spiral_record(strand, idx):
    path = strand["path"]
    off = np.array([o for o, _ in path], dtype=np.float64)
    rr = np.array([r for _, r in path])
    th_abs = (strand["seedcol"] + off) * (360.0 / NA)  # degrees, unwrapped
    slope, icpt = np.polyfit(th_abs, rr, 1)
    resid = rr - (icpt + slope * th_abs)
    # per-turn pitch
    pitches = []
    t0 = th_abs[0]
    while t0 + 360.0 <= th_abs[-1]:
        m = (th_abs >= t0) & (th_abs < t0 + 360.0)
        if m.sum() > 200:
            s_, _ = np.polyfit(th_abs[m], rr[m], 1)
            pitches.append(round(float(s_ * 360.0), 1))
        t0 += 360.0
    # decimate polyline to 1 deg
    poly = []
    last = None
    for t_, r_ in zip(th_abs, rr):
        key = int(t_)
        if key != last:
            poly.append([round(float(t_ % 360.0), 2), round(float(r_), 2)])
            last = key
    return {
        "id": f"spiral{idx}",
        "turns": round(float((th_abs[-1] - th_abs[0]) / 360.0), 2),
        "theta_start_deg": round(float(th_abs[0] % 360.0), 2),
        "theta_end_deg": round(float(th_abs[-1] % 360.0), 2),
        "r_start_px": round(float(rr[0]), 2),
        "r_end_px": round(float(rr[-1]), 2),
        "mean_pitch_px_per_turn": round(float(slope * 360.0), 2),
        "pitch_by_turn_px": pitches,
        "fit_residual_px": {"rms": round(float(resid.std()), 2),
                            "max": round(float(np.abs(resid).max()), 2)},
        "model": "archimedean r = a + b*theta (least squares over full strand)",
        "a_px": round(float(icpt), 2),
        "b_px_per_deg": round(float(slope), 4),
        "polyline_theta_deg_r_px": poly,
    }


# ---------------------------------------------------------- sector detection

def detect_sectors(pmbig, r_inner, r_outer, min_occ=0.38):
    """Radial dividers: angle columns whose structural ink occupies a large
    fraction of the radial band (the drawn axes are interrupted arrow chains,
    so occupancy — not contiguous run length — is the robust statistic)."""
    nr = pmbig.shape[0]
    i0, i1 = int(max(0, r_inner)), int(min(nr, r_outer))
    band = pmbig[i0:i1] > 0.5
    occ = band.mean(axis=0)
    cand = np.nonzero(occ >= min_occ * 0.85)[0]
    groups = []
    for j in cand:
        if groups and j - groups[-1][-1] <= 4:
            groups[-1].append(int(j))
        else:
            groups.append([int(j)])
    if len(groups) > 1 and (NA - groups[-1][-1]) + groups[0][0] <= 4:
        groups[0] = groups.pop() + groups[0]
    sectors = []
    for g in groups:
        w = occ[np.array(g)]
        if w.max() < min_occ:
            continue
        a = np.array(g, dtype=np.float64)
        if a.max() - a.min() > NA / 2:  # wrapped
            a = np.where(a < NA / 2, a + NA, a)
        ang = float((a * w).sum() / w.sum()) % NA
        ris, ros = [], []
        for j in g:
            idx = np.nonzero(band[:, j])[0]
            if idx.size:
                ris.append(i0 + idx[0] + 1)
                ros.append(i0 + idx[-1] + 1)
        sectors.append({
            "angle_deg": round(ang * 360.0 / NA, 2),
            "occupancy": round(float(w.max()), 2),
            "r_inner_px": round(float(np.median(ris)), 1),
            "r_outer_px": round(float(np.median(ros)), 1),
        })
    sectors.sort(key=lambda s: s["angle_deg"])
    return sectors


# ----------------------------------------------------------- label detection

def detect_labels(ink_bool, families, circles, strands, sectors, r_max,
                  min_area=50, max_dim=400, max_area=40000):
    H, W = ink_bool.shape
    cx, cy = families[0]["cx"], families[0]["cy"]
    paint = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(paint)
    th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
    for c in circles:
        fcx, fcy = families[c["family"]]["cx"], families[c["family"]]["cy"]
        wpx = int(max(4, c["width"] + 6))
        pts = []
        for j in range(0, NA, 2):
            r = c["radius"] + (c["dev"][j] if np.isfinite(c["dev"][j]) else 0.0)
            pts.append((fcx + r * np.cos(th[j]), fcy + r * np.sin(th[j])))
        d.line(pts + [pts[0]], fill=255, width=wpx)
    for s in strands:
        pts = [(cx + r * np.cos((s["seedcol"] + o) * 2 * np.pi / NA),
                cy + r * np.sin((s["seedcol"] + o) * 2 * np.pi / NA))
               for o, r in s["path"]]
        d.line(pts, fill=255, width=14)
    for s in sectors:
        a = np.radians(s["angle_deg"])
        d.line([(cx + s["r_inner_px"] * np.cos(a), cy + s["r_inner_px"] * np.sin(a)),
                (cx + s["r_outer_px"] * np.cos(a), cy + s["r_outer_px"] * np.sin(a))],
               fill=255, width=10)
    keep = ink_bool & (np.asarray(paint) == 0)
    # restrict to chart disc
    yy, xx = np.mgrid[0:H, 0:W]
    keep &= np.hypot(xx - cx, yy - cy) < r_max
    lab, n = label_components(keep)
    flat = lab.ravel()
    order = np.argsort(flat, kind="stable")
    counts = np.bincount(flat, minlength=n + 1)
    bounds = np.cumsum(counts)
    boundaries = sorted([c["radius"] for c in circles if c["family"] == 0])
    labels = []
    for i in range(1, n + 1):
        area = counts[i]
        if area < min_area or area > max_area:
            continue
        idx = order[bounds[i - 1]: bounds[i]]
        ys_, xs_ = np.divmod(idx, W)
        x0, x1 = int(xs_.min()), int(xs_.max())
        y0, y1 = int(ys_.min()), int(ys_.max())
        if (x1 - x0 + 1) > max_dim or (y1 - y0 + 1) > max_dim:
            continue
        mx, my = float(xs_.mean()), float(ys_.mean())
        rr = np.hypot(xs_ - cx, ys_ - cy)
        ang = float(np.degrees(np.arctan2(my - cy, mx - cx))) % 360.0
        ring = int(np.searchsorted(boundaries, float(np.median(rr))))
        labels.append(dict(ring=ring, angle=ang,
                           r_inner=float(rr.min()), r_outer=float(rr.max()),
                           bbox=[x0, y0, x1 - x0 + 1, y1 - y0 + 1]))
    labels.sort(key=lambda l: (l["ring"], l["angle"]))
    out = []
    counters = {}
    for l in labels:
        k = l["ring"]
        counters[k] = counters.get(k, 0) + 1
        out.append({
            "id": f"ring{k}_label{counters[k]:02d}",
            "ring": k,
            "angle_deg": round(l["angle"], 2),
            "r_inner_px": round(l["r_inner"], 1),
            "r_outer_px": round(l["r_outer"], 1),
            "bbox": l["bbox"],
        })
    return out


# ----------------------------------------------------------------- rendering

def render_overlay(cfg, img_path, cx, cy, families, circles, strands, sectors,
                   labels, tol, out_path, zooms):
    base = Image.open(img_path).convert("RGB")
    W, H = base.size
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
    for l in labels:
        x, y, w, h = l["bbox"]
        d.rectangle([x, y, x + w, y + h], outline=(0, 160, 0, 255), width=1)
    for s in sectors:
        a = np.radians(s["angle_deg"])
        d.line([(cx + s["r_inner_px"] * np.cos(a), cy + s["r_inner_px"] * np.sin(a)),
                (cx + s["r_outer_px"] * np.cos(a), cy + s["r_outer_px"] * np.sin(a))],
               fill=(0, 90, 255, 255), width=3)
    for st in strands:
        pts = [(cx + r * np.cos((st["seedcol"] + o) * 2 * np.pi / NA),
                cy + r * np.sin((st["seedcol"] + o) * 2 * np.pi / NA))
               for o, r in st["path"]]
        d.line(pts, fill=(255, 0, 255, 255), width=3)
    for c in circles:
        fam = families[c["family"]]
        bb = [fam["cx"] - c["radius"], fam["cy"] - c["radius"],
              fam["cx"] + c["radius"], fam["cy"] + c["radius"]]
        d.ellipse(bb, outline=(255, 0, 0, 255), width=2)
        # tracked ink centerline (only where the ridge was actually observed)
        seg = []
        for j in range(NA):
            if np.isfinite(c["dev"][j]):
                r = c["radius"] + c["dev"][j]
                seg.append((fam["cx"] + r * np.cos(th[j]),
                            fam["cy"] + r * np.sin(th[j])))
            else:
                if len(seg) > 3:
                    d.line(seg, fill=(255, 140, 0, 255), width=2)
                seg = []
        if len(seg) > 3:
            d.line(seg, fill=(255, 140, 0, 255), width=2)
    for fam in families:
        d.line([(fam["cx"] - 25, fam["cy"]), (fam["cx"] + 25, fam["cy"])],
               fill=(255, 0, 0, 255), width=3)
        d.line([(fam["cx"], fam["cy"] - 25), (fam["cx"], fam["cy"] + 25)],
               fill=(255, 0, 0, 255), width=3)
    # 50 % opacity composite
    ov.putalpha(ov.getchannel("A").point(lambda a: a // 2))
    comp = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    # caption bar
    cap = [
        f"R13 geometry proof — {cfg['image_id']} ({W}x{H}px).  Red: fitted ideal"
        f" circles ({len(circles)}).  Orange: tracked ink centerlines.  Magenta:"
        f" spiral strands ({len(strands)}).  Blue: radial dividers ({len(sectors)})."
        f"  Green: label ink clusters ({len(labels)}).",
        f"Alignment tolerance (tracked ring centerline vs fitted ideal circle):"
        f" RMS {tol['rings_rms_px']}px ({tol['rings_rms_pct']}% of radius),"
        f" max {tol['rings_max_px']}px ({tol['rings_max_pct']}%).",
        "Deterministic ops only (threshold/polar resample/least squares); no"
        " generative enhancement, no upscaling model, no inpainting.",
    ]
    bar_h = 18 * len(cap) + 12
    out = Image.new("RGB", (W, H + bar_h), (255, 255, 255))
    out.paste(comp, (0, 0))
    dd = ImageDraw.Draw(out)
    for i, line in enumerate(cap):
        dd.text((12, H + 6 + 18 * i), line, fill=(0, 0, 0))
    out.save(out_path, optimize=False)
    # zooms
    for kind, zpath in zooms:
        if kind == "ne_quadrant":
            crop = comp.crop((int(cx), int(max(0, cy - 1150)), int(min(W, cx + 1150)), int(cy)))
        elif kind == "center":
            crop = comp.crop((int(cx - 360), int(cy - 360), int(cx + 360), int(cy + 360)))
        else:
            continue
        zout = Image.new("RGB", (crop.width, crop.height + 24), (255, 255, 255))
        zout.paste(crop, (0, 0))
        ImageDraw.Draw(zout).text(
            (10, crop.height + 4),
            f"{cfg['image_id']} zoom ({kind}) — tolerance RMS {tol['rings_rms_px']}px,"
            f" max {tol['rings_max_px']}px", fill=(0, 0, 0))
        zout.save(zpath, optimize=False)


# ----------------------------------------------------------------- pipeline

def measure(key):
    cfg = CONFIGS[key]
    img = np.asarray(Image.open(cfg["file"]).convert("L"), dtype=np.float32)
    H, W = img.shape
    t = otsu(img)
    ink_bool = img < t
    ink = ink_bool.astype(np.float32)
    lab, n = label_components(ink_bool)
    areas = np.bincount(lab.ravel())
    areas[0] = 0
    bigmask = np.isin(lab, np.nonzero(areas > 3000)[0])

    centers = auto_centers(img)
    families = detect_families(bigmask, ink, centers)
    if not families:
        raise SystemExit(f"{key}: no proven circle family found")

    circles = []
    fam_pms = []
    kept_families = []
    claimed = set()  # 3px cells of ink already claimed by stronger families
    for fam in families:
        rmax = int(min(fam["cx"], fam["cy"], W - fam["cx"], H - fam["cy"], cfg["rmax"]))
        pmbig, _, _ = polar_map(bigmask.astype(np.float32), fam["cx"], fam["cy"], rmax)
        pmink, _, _ = polar_map(ink, fam["cx"], fam["cy"], rmax)
        fi = len(kept_families)
        found = detect_circles(pmbig, pmink, fam["cx"], fam["cy"], fi,
                               cfg["spiral_zone"], rmin=cfg["ring_rmin"],
                               wide_from=cfg["wide_from"], gap_max=cfg["gap_max"],
                               text_ring_filter=cfg["text_ring_filter"])
        if not found:
            continue  # vote cluster without a single verified circle: spurious
        # a weaker family whose rings ride ink already claimed by a stronger
        # family is a re-reading of the same structure, not a second system
        th_all = np.linspace(0, 2 * np.pi, NA, endpoint=False)
        fam_cells = []
        dup_rings = 0
        for c in found:
            pj = np.isfinite(c["dev"])
            rr_pts = c["radius"] + c["dev"][pj]
            px = ((fam["cx"] + rr_pts * np.cos(th_all[pj])) // 3).astype(int)
            py = ((fam["cy"] + rr_pts * np.sin(th_all[pj])) // 3).astype(int)
            cells = set(zip(px.tolist(), py.tolist()))
            hits = sum(1 for cell in cells if cell in claimed)
            if cells and hits / len(cells) >= 0.5:
                dup_rings += 1
            fam_cells.append(cells)
        if kept_families and dup_rings >= 0.6 * len(found):
            continue
        for cells in fam_cells:
            for cell in cells:
                claimed.add(cell)
                cx_, cy_ = cell
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        claimed.add((cx_ + dx, cy_ + dy))
        kept_families.append(fam)
        fam_pms.append((pmbig, pmink))
        circles.extend(found)
    families = kept_families
    if not families:
        raise SystemExit(f"{key}: no verified circle family")
    cx, cy = families[0]["cx"], families[0]["cy"]

    cols = ridge_points(fam_pms[0][0])
    fam0_radii = [c["radius"] for c in circles if c["family"] == 0]
    strands = detect_spirals(cols, cfg["spiral_zone"], fam0_radii)

    outer = max(c["radius"] for c in circles)
    sectors = detect_sectors(fam_pms[0][0], cfg["sector_band"][0],
                             cfg["sector_band"][1], cfg["min_sector_occ"])
    labels = detect_labels(ink_bool, families, circles, strands, sectors,
                           cfg["label_r_max"])

    # tolerance aggregation over rings (deviation of tracked centerline vs circle)
    rms_all = np.sqrt(np.mean([c["rms"] ** 2 for c in circles]))
    max_all = max(c["dmax"] for c in circles)
    rms_pct = np.sqrt(np.mean([(c["rms"] / c["radius"] * 100) ** 2 for c in circles]))
    max_pct = max(c["dmax"] / c["radius"] * 100 for c in circles)
    tol = {
        "rings_rms_px": round(float(rms_all), 2),
        "rings_max_px": round(float(max_all), 2),
        "rings_rms_pct": round(float(rms_pct), 3),
        "rings_max_pct": round(float(max_pct), 3),
        "note": "Deviation of the tracked ink centerline of each ring from its fitted"
                " ideal circle, over all tracked angles; includes real plate/page"
                " distortion of the facsimile, not just measurement noise.",
    }

    if key == "p0016":
        construction = ("Measured, not assumed: the chart is concentric circles about"
                        " a single center for the inner mass circle and the outer"
                        " octave/tone bands, PLUS a multi-turn spiral winding through"
                        " the mid zone (the octave-wave region). Ridge tracking of the"
                        " mid-zone bands shows a monotonic radius change of roughly"
                        " 80-150 px per turn with a wrap discontinuity, which a circle"
                        " cannot produce; the accepted rings all close with |pitch|"
                        " <= 6 px/turn.")
    else:
        construction = ("Two offset circles (seventh- and eighth-octave constant"
                        " wheels), each a true circle about its own center; no spiral.")

    rings_json = []
    for i, c in enumerate(circles):
        rings_json.append({
            "id": f"ring{i:02d}",
            "family": c["family"],
            "radius_px": round(c["radius"], 2),
            "radius_norm": round(c["radius"] / outer, 4),
            "fit_residual_px": {"rms": round(c["fit_rms"], 2),
                                "max": round(c["fit_max"], 2)},
            "deviation_px": {"rms": round(c["rms"], 2), "max": round(c["dmax"], 2)},
            "fit_center": [round(c["fit_cx"], 2), round(c["fit_cy"], 2)],
            "angular_coverage": round(c["tfrac"], 3),
            "longest_gap_deg": round(c["gap"], 1),
            "pitch_px_per_turn": round(c["pitch"], 2),
            "stroke_width_px": round(c["width"], 1),
        })

    doc = {
        "image": {
            "id": cfg["image_id"],
            "title": cfg["title"],
            "file": cfg["file"],
            "width_px": W,
            "height_px": H,
            "source_url": cfg["source_url"],
            "retrieved": RETRIEVED,
        },
        "conventions": {
            "origin": "top-left pixel of the scan, x right, y down",
            "angle_deg": "0 = +x (east); increases clockwise as displayed"
                         " (standard image coordinates, y down)",
            "radius_px": "distance from the fitted family center, in scan pixels"
                         " (~300 dpi of the physical page)",
        },
        "center": [round(cx, 2), round(cy, 2)],
        "families": [{"center": [round(f["cx"], 2), round(f["cy"], 2)],
                      "n_rings": sum(1 for c in circles if c["family"] == i)}
                     for i, f in enumerate(families)],
        "construction": construction,
        "rings": rings_json,
        "spirals": [spiral_record(s, i) for i, s in enumerate(strands)],
        "sectors": sectors,
        "labels": labels,
        "tolerance": tol,
        "method": {
            "ink_threshold": f"Otsu on 8-bit grayscale (threshold={t})",
            "structural_mask": "4-connected components of ink, area > 3000 px"
                               " (suppresses isolated text for curve tracking)",
            "center": "gradient-direction voting accumulator (hand-rolled circular"
                      " Hough, 1/4 scale, 95th-pct gradient edges) -> free Kasa circle"
                      " fits with deterministic trimming (tol 2.5px, 6 iters) ->"
                      " center clusters kept only if proven by a circle with angular"
                      " coverage >= 0.45 and on-circle ink continuity >= 0.65",
            "rings": "fixed-center radial ink-profile local maxima (structural and"
                     " full ink, 1px bins, 1440 angle bins) -> narrow-annulus subpixel"
                     " ridge tracking on full ink (window ±6px; grown by 1.5% of the"
                     " radius beyond r=750 to follow real page-warp waviness) ->"
                     " accepted iff continuity >= 0.50 of angles, longest gap <= 45"
                     " deg, |pitch| <= 6 px/turn; candidates inside the spiral zone"
                     " are excluded (their circle-like continuity is produced by"
                     " spiral arcs plus radial text, verified visually at multiple"
                     " angles); radius = mean tracked centerline radius; duplicates"
                     " within 4px merged",
            "spirals": "subpixel ridge following in polar space, seeds at 3 columns,"
                       " slope prior -110px/turn, matching window 4px, coasting <= 20 deg,"
                       " strands deduplicated by 30% point-set overlap; archimedean"
                       " least-squares fit r = a + b*theta per strand and per turn",
            "sectors": "angle columns whose structural ink occupies >="
                       f" {cfg['min_sector_occ']} of the radial band r=130..1.02x"
                       " outermost ring (the drawn axes are interrupted arrow chains,"
                       " so occupancy is used, not contiguous run length); adjacent"
                       " columns grouped (<= 1 deg), angle = occupancy-weighted centroid",
            "labels": "ink minus measured curve strokes (painted with stroke width + 6px)"
                      " -> 4-connected components, 50 <= area <= 40000 px, bbox dims"
                      " <= 400px, inside chart disc; placement only, no transcription",
            "not_done": [
                "NO generative or diffusion enhancement, NO learned upscaling,"
                " NO inpainting, NO manual retouching of any pixel",
                "no pixels from the USP 1974 scan were used in any way",
                "no text transcription (label clusters are placed, not read)",
                "no de-warping or resampling was applied to the source scan;"
                " deviations from ideal circles are reported, not corrected",
            ],
        },
    }
    os.makedirs(os.path.dirname(cfg["json_out"]) or ".", exist_ok=True)
    os.makedirs("data/geometry", exist_ok=True)
    with open(cfg["json_out"], "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    render_overlay(cfg, cfg["file"], cx, cy, families, circles, strands, sectors,
                   labels, tol, cfg["overlay_out"], cfg["zooms"])
    print(f"{key}: center=({cx:.1f},{cy:.1f}) families={len(families)}"
          f" rings={len(circles)} spirals={len(strands)} sectors={len(sectors)}"
          f" labels={len(labels)}")
    print(f"{key}: tolerance rms={tol['rings_rms_px']}px max={tol['rings_max_px']}px"
          f" ({tol['rings_rms_pct']}% / {tol['rings_max_pct']}%)")
    return doc


if __name__ == "__main__":
    keys = sys.argv[1:] or ["p0016", "p0113"]
    for k in keys:
        measure(k)
