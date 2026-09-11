# R20 — Deterministic Cleanup Parameter Study: Russell Periodic Chart (LoC plate 0016)

Prepared 2026-09-11 (project item R20). This study fixes the parameters of the deterministic
cleanup behind the restored facsimile, and records the sweeps and the failure boundary behind
every choice. It supports `tools/restore.py` and the published facsimile plate.
Source plate: `source_scans/loc/full/p0016.jpg` — Library of Congress digitization of
*The Universal One* (1926), item 27004508, image 0016; native 2712×3264 px, 8-bit
grayscale, ~300 dpi of the physical page. No external claims are made in this study;
all numbers below were measured locally on this file.

Deliverables:
- `tools/restore.py` — the recommended pipeline, parameterized, end-to-end runnable.
- `data/restoration_study/` — every intermediate and proof image (inventory at the end). That
  directory is private working staging and is not published; of its contents only the final
  cleaned plate and its parameter record travel with the edition, as the facsimile asset.
- This file — protocol, sweep tables, failure boundary, recommendation.

Scope: one plate only. No batching and no vectorization. The study was run to fix parameters,
not to make artwork; its final cleaned plate was afterwards adopted as the source of the
published facsimile. All operations deterministic (see "What was not done").

---

## 1. Scoring protocol (fixed before any variant was scored)

Frozen in `data/restoration_study/scoring_protocol.json` before the first
binarization was produced. Metrics region of interest (ROI): x=380, y=50,
w=2290, h=3190 — the page content, excluding the black scanner border and the
left endpaper.

| # | Metric | Definition |
|---|--------|-----------|
| M1 | Stroke width | Erosion-depth distribution on ink pixels in ROI: d(p) = number of successive 3×3 binary erosions survived; approx. stroke width ≈ 2d−1 px. Report median and P90 of d. |
| M2 | Min label x-height | Cap-height (px) of the smallest label class (inner rare-earth ring), via bounding-box short side of isolated single-glyph connected components in a fixed crop. |
| M3 | Broken/touching glyphs | Visual count over the FIXED 20-label sample: glyphs fragmented into >1 piece (broken) and letter pairs merged that are separate in the raw scan (falsely touching). |
| M4 | Speckle | Count of 8-connected ink components with area ≤ 4 px in ROI; plus total component count. |
| M5 | Ink fraction | Fraction of ROI pixels that are ink (sanity guard against over/under-binarization). |

### The fixed 20-label sample

Chosen on the RAW scan from a contact sheet before any pipeline variant existed.
Mix: node labels (L01–L08), small inner-ring radial text (L09–L12, L19, L20),
large outer arc text (L13–L15, L18), letterpress header/caption (L16, L17).
Crop boxes (x, y, w, h in raw-scan pixel coordinates):

| Label | Box | Label | Box |
|-------|-----|-------|-----|
| L01_xenon_node | 880,1500,200,110 | L11_sodium | 1930,1320,220,110 |
| L02_argon_node | 1035,1500,170,110 | L12_rubidium | 2020,1300,220,110 |
| L03_helium_node | 1165,1500,170,110 | L13_carbon_top | 1340,420,300,140 |
| L04_center_alphanon | 1420,1430,330,220 | L14_nitrogen_ul | 980,470,300,150 |
| L05_hydron_node | 1750,1500,180,110 | L15_boron_ur | 1760,470,300,150 |
| L06_neon_node | 1890,1500,160,110 | L16_header | 640,220,1800,90 |
| L07_krypton_node | 2010,1500,180,110 | L17_caption | 740,2790,1600,90 |
| L08_niton_node | 2140,1500,170,110 | L18_sphere_arc | 960,1030,320,220 |
| L09_silver_cluster | 1420,860,260,200 | L19_cobalt_cluster | 1450,2020,300,220 |
| L10_iodine | 880,1240,220,110 | L20_lanthanum | 1180,2120,260,200 |

---

## 2. Bleed-through / illumination arm

Background estimated by grayscale morphological closing (van Herk sliding
max→min), window 101 px — wider than the widest dark feature (~60 px arrowheads).
Two normalizations tried on the grayscale original:

- **divide**: `flat = clip(gray / max(bg,1) × 255)` → `11_flattened_divide_close101.png`
- **subtract**: `flat = clip(gray − bg + 255)` → `12_flattened_subtract_close101.png`

Observations: the scan is evenly lit; visible verso bleed-through in the blank
margins is faint (margin p5 ≈ 230 on flattened vs 57 ROI-wide raw) and is
already rejected by every thresholder tested (see
`45_zoom_margin_bleedcheck_variants_2x.png` — margins come out blank in all
arms). The real wins of flattening are (a) page-shading robustness (the
threshold no longer depends on the shading field, `44_zoom_right_edge_shadow_variants_2x.png`),
and (b) it turns the black scanner border into near-white, making global
thresholding stable. Divide and subtract behaved near-identically
(`div_otsu` 174 vs `sub_otsu` 209 speckles); divide kept slightly bolder
strokes and was selected.

## 3. Binarization sweep (57 variants)

Methods: global Otsu; adaptive mean (T = m − C); Niblack (T = m + k·s, k<0
written as −k below); Sauvola (T = m·(1 + k·(s/R − 1)), R = 128). Local methods
via integral-image mean/std, windows w ∈ {31, 61, 121}, three parameter
settings each. Applied to the raw grayscale (`raw_`) and the divide-flattened
image (`div_`). Full table (M5 ink %, M1 median/P90, M4 total/speckle):

| Variant | ink % | d med | d P90 | comps | speckle≤4 |
|---------|-------|-------|-------|-------|-----------|
| raw_otsu | 23.3 | 2 | 8 | 3579 | 116 |
| raw_adapt_w31_C5 | 23.6 | 2 | 3 | 4654 | 680 |
| raw_adapt_w31_C10 | 22.6 | 2 | 3 | 4273 | 447 |
| raw_adapt_w31_C15 | 21.9 | 2 | 3 | 4305 | 431 |
| raw_niblack_w31_k0.1 | 36.1 | 2 | 4 | 7388 | 1211 |
| raw_niblack_w31_k0.2 | 33.2 | 2 | 4 | 8144 | 1340 |
| raw_niblack_w31_k0.3 | 30.6 | 2 | 3 | 8686 | 1449 |
| raw_sauvola_w31_k0.2 | 22.0 | 2 | 3 | 4254 | 448 |
| raw_sauvola_w31_k0.34 | 20.6 | 1 | 3 | 4086 | 279 |
| raw_sauvola_w31_k0.5 | 19.2 | 1 | 3 | 4226 | 308 |
| raw_adapt_w61_C5 | 24.8 | 2 | 4 | 3868 | 439 |
| raw_adapt_w61_C10 | 23.7 | 2 | 4 | 3799 | 334 |
| raw_adapt_w61_C15 | 22.9 | 2 | 4 | 3914 | 335 |
| raw_niblack_w61_k0.1 | 33.2 | 2 | 5 | 5400 | 775 |
| raw_niblack_w61_k0.2 | 30.8 | 2 | 5 | 5496 | 662 |
| raw_niblack_w61_k0.3 | 28.6 | 2 | 4 | 5739 | 671 |
| raw_sauvola_w61_k0.2 | 23.1 | 2 | 4 | 3814 | 318 |
| raw_sauvola_w61_k0.34 | 21.7 | 2 | 4 | 3845 | 215 |
| raw_sauvola_w61_k0.5 | 20.1 | 1 | 3 | 4034 | 218 |
| raw_adapt_w121_C5 | 26.2 | 2 | 5 | 3692 | 471 |
| raw_adapt_w121_C10 | 24.9 | 2 | 4 | 3608 | 284 |
| raw_adapt_w121_C15 | 23.9 | 2 | 4 | 3698 | 251 |
| raw_niblack_w121_k0.1 | 29.6 | 2 | 6 | 4485 | 635 |
| raw_niblack_w121_k0.2 | 27.8 | 2 | 5 | 4449 | 450 |
| raw_niblack_w121_k0.3 | 26.2 | 2 | 5 | 4496 | 451 |
| raw_sauvola_w121_k0.2 | 24.2 | 2 | 5 | 3623 | 241 |
| raw_sauvola_w121_k0.34 | 22.7 | 2 | 4 | 3661 | 161 |
| raw_sauvola_w121_k0.5 | 21.0 | 2 | 4 | 3925 | 184 |
| div_otsu | 23.0 | 2 | 4 | 3633 | 174 |
| div_adapt_w31_C5 | 24.0 | 2 | 3 | 4755 | 751 |
| div_adapt_w31_C10 | 23.0 | 2 | 3 | 4428 | 459 |
| div_adapt_w31_C15 | 22.2 | 2 | 3 | 4521 | 456 |
| div_niblack_w31_k0.1 | 35.3 | 2 | 4 | 7873 | 1385 |
| div_niblack_w31_k0.2 | 32.8 | 2 | 4 | 8366 | 1464 |
| div_niblack_w31_k0.3 | 30.6 | 2 | 3 | 8735 | 1473 |
| div_sauvola_w31_k0.2 | 21.8 | 2 | 3 | 4381 | 464 |
| div_sauvola_w31_k0.34 | 20.4 | 1 | 3 | 4258 | 361 |
| div_sauvola_w31_k0.5 | 18.9 | 1 | 3 | 4438 | 418 |
| div_adapt_w61_C5 | 25.0 | 2 | 4 | 4029 | 498 |
| div_adapt_w61_C10 | 24.0 | 2 | 3 | 3901 | 355 |
| div_adapt_w61_C15 | 23.2 | 2 | 3 | 4000 | 344 |
| div_niblack_w61_k0.1 | 32.5 | 2 | 5 | 5368 | 698 |
| div_niblack_w61_k0.2 | 30.5 | 2 | 4 | 5474 | 644 |
| div_niblack_w61_k0.3 | 28.7 | 2 | 4 | 5704 | 683 |
| div_sauvola_w61_k0.2 | 22.7 | 2 | 3 | 4049 | 410 |
| div_sauvola_w61_k0.34 | 21.3 | 2 | 3 | 4031 | 289 |
| div_sauvola_w61_k0.5 | 19.8 | 1 | 3 | 4240 | 321 |
| div_adapt_w121_C5 | 25.8 | 2 | 4 | 4102 | 726 |
| div_adapt_w121_C10 | 24.8 | 2 | 4 | 3886 | 418 |
| div_adapt_w121_C15 | 24.0 | 2 | 4 | 3872 | 328 |
| div_niblack_w121_k0.1 | 28.6 | 2 | 5 | 4718 | 814 |
| div_niblack_w121_k0.2 | 27.2 | 2 | 5 | 4643 | 568 |
| div_niblack_w121_k0.3 | 25.9 | 2 | 4 | 4621 | 497 |
| div_sauvola_w121_k0.2 | 23.5 | 2 | 4 | 3855 | 313 |
| div_sauvola_w121_k0.34 | 22.1 | 2 | 4 | 3882 | 238 |
| div_sauvola_w121_k0.5 | 20.4 | 1 | 3 | 4125 | 294 |
| sub_otsu | 21.0 | 2 | 3 | 3644 | 209 |

(Same data machine-readable in `binarization_metrics.json`.)

Readings:
- Niblack is uncompetitive at every setting (speckle 450–1473; it fires inside
  large blank/large-black areas by construction).
- Sauvola k=0.5 and k=0.34@w31 thin the median stroke depth from 2 to 1 —
  strokes reduced to ~1 px, a fragmentation risk for the 8-px inner text.
- The best local variant, `raw_sauvola_w121_k0.34` (161 speckles), does not
  beat plain Otsu (116) and adds salt noise inside the dark scanner-border
  zones (visible at the top/bottom edges of `13_bin_*sauvola*.png`).
- `raw_otsu`'s P90 stroke depth of 8 comes from the page-edge dark band inside
  the ROI, not from strokes; `div_otsu` (P90=4) does not have this pathology
  because flattening whitens that band.
- **Winner: `div_otsu`** — global Otsu on the divide-flattened image. Within
  1σ of the best speckle count, keeps median stroke depth 2, illumination-
  and border-robust, and has the fewest parameters (window 101 for the
  background; the threshold itself is data-derived: T=166 full-frame).
  At 1:1 zoom on the smallest text (`43_zoom_rare_earths_variants_4x.png`)
  `raw_otsu`, `div_otsu`, and `div_sauvola_w121_k0.34` are equally legible.

## 4. Despeckle sweep

On `div_otsu` (ROI): component-area thresholds. `despeckle_sweep.json`.

| max area (px) | components removed | ink px removed | % of ink |
|---------------|--------------------|----------------|----------|
| ≤2 | 114 | 157 | 0.009 |
| ≤4 | 174 | 360 | 0.021 |
| ≤8 | 258 | 890 | 0.053 |
| ≤16 | 374 | 2344 | 0.139 |
| ≤32 | 481 | 4740 | 0.282 |
| ≤64 | 587 | 10019 | 0.595 |

Content-safety check (`30_despeckle_removed_overlay.png` — red = removed at ≤8,
orange = additionally at ≤16, blue = additionally at ≤32): sampled removals are
scanner-border edge noise and paper flecks. Verified survivors at ≤32:
caption commas (`32_...caption_2x.png`), the tiny stars ★ and the dot of the
lowercase i (`33_...smalltext_stars_4x.png`), dashes/tick-combs
(`34_...nodes_4x.png`). **Chosen: ≤8** — conservative margin (a period in the
smallest ring text is ~5–9 px; ≤8 only ever removed isolated flecks in the
sampled crops, and the risk-free band ends there).

## 5. Morphological stroke repair — failure boundary

3×3 closing, r iterations of dilate then r of erode, on despeckled `div_otsu`
(ROI). `closing_sweep.json`:

| closing r | components | ink % | d med | d P90 |
|-----------|-----------|-------|-------|-------|
| 0 (none) | 3375 | 23.0 | 2 | 4 |
| 1 | 1613 | 23.9 | 2 | 5 |
| 2 | 442 | 28.1 | 3 | 6 |
| 3 | 227 | 31.7 | 3 | 9 |

**The failure boundary is r=1.** Halving of the component count (3375→1613)
means ~1750 merges plate-wide; the proof crop
`40_closing_failure_boundary.png` (rare-earth stack, 4×) shows r=1 gluing
adjacent letters inside PRASEODYMIUM/NEODYMIUM and filling the counters of
R/A/O; r=2 collapses whole words into bars. Letter gaps in the 8-px inner-ring
text are 1–2 px — the same scale as any gap a 3×3 closing can bridge, so
*any* closing that could heal a broken stroke also invents letter joins.
Inspection of the despeckled `div_otsu` at 1:1 found no broken glyphs needing
repair (M3 below). **Recommended pipeline therefore performs NO closing**;
`restore.py --close N` exists only to reproduce this boundary.

## 6. Objective scores of the final pipeline

Final = flatten(close 101, divide) → Otsu (T=166) → despeckle ≤8 → drop
frame-touching components → no closing. (`data/restoration_study/final/`.)

- **M1 stroke width**: median erosion depth 2 (≈3 px strokes), P90 = 4 — identical
  to the raw-scan Otsu baseline; no thinning introduced.
- **M2 min label x-height**: isolated single-glyph components in the rare-earth
  crop (x 1270–1360, y 2260–2400): bbox short sides 10, 11, 11, 12, 13, 14,
  14, 17, 17, 18, 19 px (FINAL) vs 10, 11, 11, 11, 12, 13, 14, 14, 17, 17, 18,
  19, 20 px (raw_otsu). Smallest glyph class ≈ 10–11 px in both — the pipeline
  loses no small-text height.
- **M3 broken/touching glyphs**, fixed 20-label sample, visual inspection of
  the 3× sheets (`42_smalltext_*.png`, `20_labels_*.png`, header/caption
  proofs `52_`/`53_`):

| Variant | broken glyphs | falsely touching pairs | notes |
|---------|---------------|------------------------|-------|
| raw_otsu | 0 | 0 | slightly bolder than print |
| div_otsu | 0 | 0 | |
| div_sauvola_w121_k0.34 | 0 | 0 | adds edge roughness + border salt noise |
| FINAL (div_otsu, desp≤8) | 0 | 0 | |
| FINAL + close r=1 | 0 | many (~1750 merges plate-wide) | failure boundary — rejected |
| FINAL + close r=2 | 0 | catastrophic (words→bars) | rejected |

  Pre-existing print contacts (e.g. P–R in PRASEODYMIUM, letters crossing the
  ruled rings) are present in the RAW scan and are not counted. Zero broken
  glyphs includes the thin-serif letterpress header and caption
  (`52_detail_header_raw_vs_final_2x.png`, `53_detail_caption_raw_vs_final_2x.png`).
- **M4 speckle**: 174 → 0 components ≤4 px after despeckle (ROI).
- **M5 ink fraction**: 0.175 full-frame (0.23 in ROI) — consistent with the
  chart's actual density.

## 7. Recommendation and proof

**Pipeline (all parameters recorded in `tools/restore.py`, defaults = recommended):**

```
python3 tools/restore.py source_scans/loc/full/p0016.jpg --outdir data/restoration_study/final
```

1. Background: grayscale closing, window **101 px** (van Herk max→min).
2. Flatten: divide by background, ×255, clip.
3. Binarize: **global Otsu** on flattened (measured T=166 on this plate;
   recomputed per input).
4. Despeckle: remove 8-connected components **area ≤ 8 px**
   (364 comps / 1176 px on this plate).
5. Frame removal: drop ink components touching the image boundary
   (486,496 px of scanner border/page-edge band; `--keep-border` disables).
6. Stroke repair: **none** (§5).

Runtime 3.6 s; reruns bit-identically from the raw scan (pure numpy/Pillow,
no randomness). Intermediates + `p0016_params.json` land beside the output.

Proof images:
- `50_sidebyside_fullplate.png` — raw vs recommended, full plate.
- `51_detail_A_inner_ring_smalltext.png` — 8-px rare-earth text, 3×.
- `51_detail_B_node_row.png` — XENON…GAMMANON node row, 3×.
- `51_detail_C_outer_arc_and_edge.png` — page-curvature shadow zone, 3×
  (worst case for global thresholds; fully legible, zero shadow ink).

Known residual: a few endpaper-texture flecks outside the page content survive
(left of the page edge, not frame-touching, >8 px). They are outside any
future crop box for the chart; no attempt was made to remove them by
region-specific rules, which would be manual retouching by another name.

## 8. What was not done

- **No generative or diffusion enhancement, no learned upscaling, no
  inpainting, no synthesis of any pixel.** Every output pixel is a
  deterministic function of the input scan (threshold comparisons and
  set-operations on measured values only).
- **No manual retouching**, no hand-erasure of the residual endpaper flecks.
- **No morphological stroke repair**: closing was bounded at the documented
  failure boundary (r=1 already invents glyph connections, §5,
  `40_closing_failure_boundary.png`) and is therefore excluded from the
  recommended pipeline entirely.
- **No resampling**: output is at native scan resolution (2712×3264).
- **No use of the USP 1974 scan**: no pixel from `source_scans/usp*` was read
  or used by this study or by `restore.py`.
- No batching to other plates: this study takes one plate end to end.

## Appendix — `data/restoration_study/` inventory

| File | What it is |
|------|-----------|
| `scoring_protocol.json` | frozen metrics + 20-label sample boxes |
| `binarization_metrics.json` | full 57-variant scoring table |
| `despeckle_sweep.json`, `closing_sweep.json` | sweep numbers (§4, §5) |
| `10_background_close101.png` | estimated background |
| `11/12_flattened_*.png` | divide / subtract normalizations |
| `13_bin_<variant>.png` | shortlisted binarizations, full ROI |
| `20_labels_<variant>.png` | 20-label contact sheets (incl. RAW reference) |
| `30–34_despeckle_*.png` | despeckle removal overlays + safety crops |
| `40_closing_failure_boundary.png` | closing r=0/1/2 on 8-px text, 4× |
| `42_smalltext_<variant>_3x.png` | M3 small-text inspection sheets |
| `43–45_zoom_*.png` | variant comparisons: tiny text, shadow zone, margin |
| `50/51_*.png` | final side-by-side proofs (§7) |
| `52/53_detail_*.png` | letterpress header/caption raw vs final |
| `final/p0016_*.png`, `final/p0016_params.json` | restore.py end-to-end output |
