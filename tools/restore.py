#!/usr/bin/env python3
"""
restore.py -- deterministic cleanup pipeline for Walter Russell 1926 chart plates.

Recommended pipeline (chosen by the R20 parameter study on LoC plate 0016,
see verification/restoration_study.md):

    1. Background estimation : grayscale morphological closing, window 101 px
                               (van Herk sliding max then min; window must
                               exceed the widest dark feature, ~60 px arrows).
    2. Flattening            : divide original by background, rescale to 255.
                               Removes page-shading / illumination gradient and
                               whites out the scanner border; suppresses any
                               verso bleed-through together with step 3.
    3. Binarization          : global Otsu threshold on the flattened image.
                               (Beat Sauvola/Niblack/adaptive-mean sweeps on
                               speckle count at equal stroke preservation.)
    4. Despeckle             : remove 8-connected ink components with
                               area <= 8 px (0.05 % of ink; verified to spare
                               all punctuation, stars and tick marks).
    5. Frame removal         : drop ink components touching the image boundary
                               (black scanner border / page-edge band; chart
                               content is inset on all LoC scans). --keep-border
                               disables.
    6. Stroke repair         : NONE. Morphological closing at radius 1 already
                               invents letter-to-letter connections in the 8 px
                               inner-ring text (failure boundary documented in
                               the study); the pipeline therefore performs no
                               closing. --close N is available for experiments
                               but is NOT part of the recommended pipeline.

Explicitly NOT done (deterministic-ops-only program rule): no generative or
diffusion enhancement, no learned upscaling, no inpainting, no manual retouch.
Every output pixel is a deterministic function of the input scan.

Usage:
    python3 tools/restore.py source_scans/loc/full/p0016.jpg \
        --outdir data/restoration_study/final [--close 0] [--speckle 8] \
        [--bg-window 101]

Outputs in --outdir (PREFIX = input stem):
    PREFIX_10_gray.png        8-bit grayscale of the input
    PREFIX_11_background.png  estimated background (closing, window W)
    PREFIX_12_flattened.png   divide-normalized grayscale
    PREFIX_20_binary.png      Otsu binarization of the flattened image
    PREFIX_30_clean.png       final cleaned bilevel image (after despeckle)
    PREFIX_params.json        every parameter + measured values for the run

Requires only numpy + Pillow. Python 3.11, numpy 1.26, Pillow 10.4 tested.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


# ----------------------------------------------------------------- morphology
def _vanherk_1d(a: np.ndarray, w: int, op) -> np.ndarray:
    """Exact sliding max/min (odd window w) along the last axis, O(n)."""
    n = a.shape[-1]
    r = w // 2
    ident = -np.inf if op is np.maximum else np.inf
    pad_total = (-(n + 2 * r)) % w
    ap = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(r, r + pad_total)],
                constant_values=ident)
    m = ap.shape[-1]
    blocks = ap.reshape(a.shape[:-1] + (m // w, w))
    acc = np.maximum.accumulate if op is np.maximum else np.minimum.accumulate
    fwd = acc(blocks, axis=-1).reshape(a.shape[:-1] + (m,))
    bwd = acc(blocks[..., ::-1], axis=-1)[..., ::-1].reshape(a.shape[:-1] + (m,))
    return op(bwd[..., 0:n], fwd[..., 2 * r:2 * r + n])


def max_filter(a, w):
    t = _vanherk_1d(a, w, np.maximum)
    return _vanherk_1d(t.T, w, np.maximum).T


def min_filter(a, w):
    t = _vanherk_1d(a, w, np.minimum)
    return _vanherk_1d(t.T, w, np.minimum).T


def gray_close(a, w):
    """Grayscale closing for dark-ink-on-light: dilation (max) then erosion (min)."""
    return min_filter(max_filter(a, w), w)


def dilate3(m):
    out = m.copy()
    out[1:, :] |= m[:-1, :]; out[:-1, :] |= m[1:, :]
    out[:, 1:] |= m[:, :-1]; out[:, :-1] |= m[:, 1:]
    out[1:, 1:] |= m[:-1, :-1]; out[:-1, :-1] |= m[1:, 1:]
    out[1:, :-1] |= m[:-1, 1:]; out[:-1, 1:] |= m[1:, :-1]
    return out


def erode3(m):
    out = m.copy()
    out[1:, :] &= m[:-1, :]; out[:-1, :] &= m[1:, :]
    out[:, 1:] &= m[:, :-1]; out[:, :-1] &= m[:, 1:]
    out[1:, 1:] &= m[:-1, :-1]; out[:-1, :-1] &= m[1:, 1:]
    out[1:, :-1] &= m[:-1, 1:]; out[:-1, 1:] &= m[1:, :-1]
    out[0, :] = False; out[-1, :] = False
    out[:, 0] = False; out[:, -1] = False
    return out


def binary_close(mask, iters):
    m = mask
    for _ in range(iters):
        m = dilate3(m)
    for _ in range(iters):
        m = erode3(m)
    return m


# --------------------------------------------------------------- thresholding
def otsu_threshold(a: np.ndarray) -> int:
    hist, _ = np.histogram(a.ravel(), bins=256, range=(0, 256))
    p = hist.astype(np.float64) / hist.sum()
    bins = np.arange(256)
    w0 = np.cumsum(p)
    w1 = 1.0 - w0
    mu = np.cumsum(p * bins)
    mu_t = mu[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sb = (mu_t * w0 - mu) ** 2 / (w0 * w1)
    sb[~np.isfinite(sb)] = 0.0
    return int(np.argmax(sb))


# ------------------------------------------------------- connected components
def label_components(mask: np.ndarray):
    """8-connected run-based labeling. Returns (label array int32, sizes int64).
    sizes[k] = pixel count of component k; index 0 is background."""
    H, W = mask.shape
    padded = np.zeros((H, W + 2), dtype=bool)
    padded[:, 1:-1] = mask
    d = np.diff(padded.astype(np.int8), axis=1)
    starts_r, starts_c = np.where(d == 1)
    ends_r, ends_c = np.where(d == -1)          # end-exclusive columns
    nruns = len(starts_c)
    parent = np.arange(nruns, dtype=np.int64)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    row_start = np.searchsorted(starts_r, np.arange(H + 1))
    for row in range(1, H):
        a0, a1 = row_start[row], row_start[row + 1]
        b0, b1 = row_start[row - 1], row_start[row]
        if a0 == a1 or b0 == b1:
            continue
        j = b0
        for i in range(a0, a1):
            s, e = starts_c[i], ends_c[i]
            while j < b1 and ends_c[j] < s:      # 8-conn: diagonal touch counts
                j += 1
            jj = j
            while jj < b1 and starts_c[jj] <= e:
                ra, rb = find(i), find(jj)
                if ra != rb:
                    parent[rb] = ra
                jj += 1
    roots = np.fromiter((find(i) for i in range(nruns)),
                        dtype=np.int64, count=nruns)
    uniq, run_label = np.unique(roots, return_inverse=True)
    run_label = (run_label + 1).astype(np.int64)
    lab = np.zeros((H, W), dtype=np.int32)
    flat = lab.ravel()
    for i in range(nruns):
        flat[starts_r[i] * W + starts_c[i]: starts_r[i] * W + ends_c[i]] = run_label[i]
    run_len = (ends_c - starts_c).astype(np.int64)
    sizes = np.bincount(run_label, weights=run_len,
                        minlength=len(uniq) + 1).astype(np.int64)
    return lab, sizes



# ------------------------------------------------------------------- pipeline
def restore(src: Path, outdir: Path, bg_window: int = 101,
            speckle: int = 8, close_iters: int = 0,
            drop_border: bool = True) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    stem = src.stem

    img = Image.open(src).convert("L")
    g = np.asarray(img, dtype=np.float64)

    # 1-2. background estimation + flattening
    bg = gray_close(g, bg_window)
    flat = np.clip(g / np.maximum(bg, 1.0) * 255.0, 0, 255)

    # 3. global Otsu on the flattened image
    T = otsu_threshold(flat)
    ink = flat < T

    # 4. despeckle + scanner-frame removal (single labeling pass).
    #    Frame rule: drop ink components that touch the image boundary --
    #    the chart/page content is inset from the frame on all LoC scans,
    #    while the black scanner border and page-edge band always touch it.
    lab, sizes = label_components(ink)
    keep = sizes > speckle
    keep[0] = False
    n_removed = int((~keep[1:]).sum())
    px_removed = int(sizes[1:][~keep[1:]].sum())
    border_removed_px = 0
    if drop_border:
        edge_labels = np.unique(np.concatenate(
            [lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
        edge_labels = edge_labels[edge_labels != 0]
        border_removed_px = int(sizes[edge_labels].sum())
        keep[edge_labels] = False
    clean = keep[lab]

    # 5. optional closing -- NOT part of the recommended pipeline (default 0).
    if close_iters > 0:
        clean = binary_close(clean, close_iters)

    def save_gray(a, name):
        Image.fromarray(a.astype(np.uint8)).save(outdir / f"{stem}_{name}.png")

    save_gray(g, "10_gray")
    save_gray(bg, "11_background")
    save_gray(flat, "12_flattened")
    save_gray(np.where(ink, 0, 255), "20_binary")
    save_gray(np.where(clean, 0, 255), "30_clean")

    params = {
        "input": str(src),
        "input_size": [int(g.shape[1]), int(g.shape[0])],
        "pipeline": [
            f"gray_close background estimation, window={bg_window}",
            "flatten = clip(gray/max(bg,1)*255)",
            f"global Otsu on flattened -> threshold={T}",
            f"despeckle: drop 8-connected components with area<={speckle}px "
            f"(removed {n_removed} components, {px_removed} px)",
            (f"scanner-frame removal: drop ink components touching the image "
             f"boundary ({border_removed_px} px)" if drop_border
             else "scanner-frame removal disabled (--keep-border)"),
            ("binary closing radius " + str(close_iters) if close_iters
             else "NO stroke-repair closing (failure boundary at radius 1; "
                  "see verification/restoration_study.md)"),
        ],
        "otsu_threshold": T,
        "bg_window": bg_window,
        "speckle_max_area": speckle,
        "close_iters": close_iters,
        "removed_speckle_components": n_removed,
        "removed_speckle_px": px_removed,
        "drop_border": drop_border,
        "removed_border_px": border_removed_px,
        "ink_fraction": float(clean.mean()),
        "not_done": [
            "no generative/diffusion enhancement",
            "no learned upscaling",
            "no inpainting",
            "no manual retouching",
            "no morphological stroke repair (documented failure boundary)",
        ],
    }
    with open(outdir / f"{stem}_params.json", "w") as f:
        json.dump(params, f, indent=2)
    return params


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("input", type=Path, help="raw scan (grayscale page image)")
    ap.add_argument("--outdir", type=Path,
                    default=Path("data/restoration_study/final"))
    ap.add_argument("--bg-window", type=int, default=101,
                    help="background closing window in px (odd; default 101)")
    ap.add_argument("--speckle", type=int, default=8,
                    help="max area (px) of ink components to remove (default 8)")
    ap.add_argument("--close", type=int, default=0, dest="close_iters",
                    help="binary closing iterations; default 0 = recommended. "
                         ">=1 invents glyph connections on 1926-chart small text")
    ap.add_argument("--keep-border", action="store_true",
                    help="keep ink components touching the image frame "
                         "(default: removed as scanner-border artifacts)")
    args = ap.parse_args(argv)
    if args.bg_window % 2 == 0:
        ap.error("--bg-window must be odd")
    params = restore(args.input, args.outdir, args.bg_window,
                     args.speckle, args.close_iters,
                     drop_border=not args.keep_border)
    print(json.dumps(params, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
