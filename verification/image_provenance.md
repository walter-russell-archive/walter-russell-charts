# Image provenance of the published site

Proof items **B1** (every published pixel traced to a primary source) and **C1**
(the trace is exhaustive and machine-checked).

Derivation and retrieval date: **2026-09-11**.

Machine-readable manifest: [`image_provenance.tsv`](image_provenance.tsv).
Generator: `tools/make_image_provenance.py`. Verifier:
`tools/check_image_provenance.py`.

**Every path in this file and in the manifest is relative to the repository
root** — the root of `walter-russell-archive/charts`, the repository that holds
`docs/`, `tools/`, `data/`, `charts/`, `assets_src/` and `source_scans/`.

---

## 1. The assertion

**Every image asset served from `docs/` has exactly one row in
`verification/image_provenance.tsv`, and every row carries the SHA256 of the
published bytes, the SHA256 of each source input, and the exact deterministic
operation chain that turns one into the other.**

"Image asset" is taken in the widest sense and enumerated mechanically:

1. every file under the site tree whose extension is `.png`, `.jpg`, `.jpeg`,
   `.gif`, `.webp`, `.avif`, `.bmp`, `.tif`, `.tiff`, `.ico`, `.svg`, `.svgz`;
2. every distinct inline `<svg>…</svg>` element in every generated HTML page;
3. every `data:image/…` URI in every generated HTML page.

Result of the enumeration on 2026-09-11: **five published image assets** — three
files and two inline SVG icons. **Zero `data:image` URIs were found**; the CSS
contains no `url(...)` reference of any kind. Both facts were checked against
the built tree, not assumed.

| Published asset | Kind | Source class |
|---|---|---|
| `docs/assets/facsimile.png` | 2712×3264 bilevel PNG | `loc_facsimile` |
| `docs/assets/og-card.png` | 1200×630 RGB PNG | `loc_facsimile` |
| `docs/charts/russell_periodic.svg` | vector, viewBox 2314×2314 | `data_render` |
| `inline-svg:icon.icon-moon` | vector, 24×24, in all 8 HTML pages | `site_furniture` |
| `inline-svg:icon.icon-sun` | vector, 24×24, in all 8 HTML pages | `site_furniture` |

## 2. Posture claim C — no post-1926 work supplies any published pixel

Of the five assets:

- Two are deterministic restorations of **one** Library of Congress page image,
  `gdc.27004508` image 0016, the 1926 Brieger Press first edition.
- One is a vector render generated from measured geometry plus the transcribed
  1926 element table. It copies, samples and traces **no** pixel; it is a
  data-driven drawing whose data came from the 1926 pages.
- Two are hand-authored 24×24 user-interface glyphs (a crescent and a sun) that
  depict nothing from any book. They are first-party original geometry written
  as literals in the site generator.

No pixel of any post-1926 printing, edition, reprint or third-party reproduction
reaches the published site. In particular, **no pixel from the 1974 University
of Science and Philosophy scan** is used anywhere: that scan is a private
transcription witness, it is not in this repository at all, it is read by no
publication tool, and it appears in no `source_local_path` in the manifest.
`verification/restoration_study.md` §8 records the same for the restoration
pipeline ("No use of the USP 1974 scan").

No generative, diffusion, learned-upscaling or inpainting step exists anywhere
in any chain. Every raster operation is a threshold comparison, a connected-
component set operation, a fixed-box crop, or a Lanczos resample with pinned
parameters.

## 3. Column dictionary

| Column | Meaning |
|---|---|
| `published_path` | repository-relative path of the published file, or the key `inline-svg:<class>` / `data-uri:<sha12>` for assets embedded in HTML |
| `pixel_or_vector` | `pixel` for rasters, `vector` for SVG |
| `dimensions` | `WxH`; pixels for rasters, viewBox user units for vectors. Measured, not declared |
| `sha256_published` | SHA256 of the published bytes (for embedded assets, of the exact UTF-8 markup fragment) |
| `source_class` | `loc_facsimile` \| `data_render` \| `site_furniture` |
| `source_iiif_url` | pipe-separated LoC IIIF URLs of every page image the asset derives from. Empty only for `site_furniture` |
| `source_local_path` | pipe-separated repository-relative inputs, in chain order. A path ending `#literal` means the source is the published markup itself, held verbatim as a literal inside that file (used for the two UI icons, so that unrelated edits to the site generator do not register as provenance drift) |
| `sha256_source` | pipe-separated SHA256s, positionally aligned with `source_local_path`; for a `#literal` source, the hash of the literal rather than of the containing file |
| `op_chain` | the deterministic operations with their pinned parameters, naming the script at each step |
| `generator_script` | the scripts that produce the published bytes |
| `embedded_notice` | licence metadata found **inside** the published bytes: PNG text-chunk keywords, or the element names of the SVG `<metadata>` RDF block. `none` if absent. Detected from the bytes on each regeneration, never typed |
| `notes` | verification record and caveats |

## 4. The three real chains, in brief

**`docs/assets/facsimile.png`** — LoC IIIF image 0016 → `tools/restore.py` with
its pinned defaults (background = grayscale closing, `bg_window=101`; flatten =
`clip(gray/max(bg,1)*255)`; global Otsu on the flattened image, threshold **166**;
despeckle 8-connected components of area ≤ **8 px**, 364 components / 1176 px;
drop ink components touching the image boundary, 486 496 px; `close_iters=0`,
i.e. **no** morphological stroke repair; no resampling) →
`assets_src/facsimile_p0016_clean.png` → `tools/build_site.py build_images()`:
`point(v > 127 → 255 else 0)`, `convert("1")`, `save(PNG, optimize=True)`.
No crop, no resize, no colour transform.

These parameters match `verification/restoration_study.md` §3–§7 and
`assets_src/facsimile_p0016_params.json` exactly — threshold 166, window 101,
speckle ≤ 8, closing 0, border drop on. No discrepancy was found.

**`docs/assets/og-card.png`** — same restored plate, then `convert("L")`,
`crop(397, 330, 2711, 2824)` = 2314×2494, Lanczos resize to 585×630, pasted at
`(307, 0)` on a 1200×630 canvas filled `rgb(251,250,247)`, saved optimized.

**`docs/charts/russell_periodic.svg`** — **not a raster derivative.**
`tools/measure_geometry.py` measures LoC image 0016 into
`data/chart_geometry.json` (centre, rings, spiral polylines, sectors, label
clusters, in scan-pixel coordinates). The R11 dual-witness transcription of the
printed table on LoC images 0112/0114/0116/0118/0120 (printed pp. 92–100) gives
`data/russell_1926_elements.json`. `tools/render_chart.py` draws every mark from
those two frozen inputs — deterministic, no timestamps, fixed 2-decimal float
formatting. `tools/build_site.py` then injects an accessible `<title>` after the
`<svg …>` open tag; that injection is the only difference between
`charts/russell_periodic.svg` and the published copy (verified: an 84-character
delta, byte-equal after removing the injected line).

## 5. Verification performed on 2026-09-11

- `tools/restore.py` rerun from `source_scans/loc/full/p0016.jpg` into a scratch
  directory reproduced `assets_src/facsimile_p0016_clean.png` **byte for byte**
  (`fe19ed558a66a7695a0bcfbdc1be8dbeb93dccd92e30a8dd6f66b70d0ee9a63e`).
- Re-running the `build_images()` raster steps from that file reproduced the
  decoded pixel arrays of both published PNGs **element-wise identically**
  (2712×3264 bilevel; 1200×630 RGB). The published files differ from the
  re-derivations only by their embedded licence metadata chunks, which carry no
  pixel data.
- After the octave-5 chart-witness amendment to `data/russell_1926_elements.json`
  (now `ca2a21cb5439d287a89a8cff4f2751b36b107d9305d70a7c8560190b2162b950`),
  `tools/render_chart.py` was rerun on a scratch copy of the whole repository: it
  reproduced `charts/russell_periodic.svg` **byte for byte**
  (`2e43c1834b058005303f14b649709385e7300c00606e74fe22fcc04871416d71`). The
  published redraw therefore matches its current inputs, amendment included.
- The published SVG was verified equal to `charts/russell_periodic.svg` plus the
  injected `<title>`.
- `tools/check_image_provenance.py` exits **0** with a PASS line from both
  locations: from the private workspace root, and from inside the repository
  with no arguments. The manifest generated in the two locations is **byte
  identical**, because every path it records is repository-relative.
- Negative controls, all run against temporary copies of the site tree and of
  the manifest, never in place. Each made the checker exit **1** with a specific
  message naming the asset:
  1. tampering one `sha256_published` → "sha256_published drift", both hashes printed;
  2. deleting the `docs/charts/russell_periodic.svg` row → "published image has NO manifest row";
  3. pointing `source_local_path` at a non-existent file → "source missing";
  4. adding an unlisted `extra.png` to the tree → "published image has NO manifest row";
  5. injecting a `data:image/gif` URI into a page → "published image has NO manifest row: 'data-uri:288f40f56ab5' (embedded in index.html)";
  6. altering the published sun icon in every page → "sha256_published drift" plus
     "the published markup … is not present verbatim in tools/build_site.py";
  7. changing one `dimensions` cell to `1200x631` → "dimensions '1200x631' but measured '1200x630'";
  8. naming a source that exists in the private workspace but not in the
     repository → "source lives outside the repository: … sync it into the
     repository or record it as external".

  Controls 1–5 were rerun inside the repository after the retarget; all still
  exit 1. Control 8 is meaningful only from the workspace, where the two roots
  differ.

## 6. Re-derive and re-check

```
# Fetch the source page images from the Library of Congress
#  (stay under 10 requests/minute, as the Library asks)
curl -s "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:0016/full/full/0/default.jpg" \
     -o source_scans/loc/full/p0016.jpg

# Rebuild the restored plate, the measured geometry and the redraw
python3 tools/restore.py source_scans/loc/full/p0016.jpg --outdir data/restoration_study/final
python3 tools/measure_geometry.py
python3 tools/render_chart.py

# Rebuild the site, then regenerate and verify this manifest
python3 tools/build_site.py
python3 tools/make_image_provenance.py
python3 tools/check_image_provenance.py
```

Both tools take two optional positional arguments, the manifest and the site
tree:

```
python3 tools/make_image_provenance.py [MANIFEST_TSV] [DOCS_ROOT] [--date YYYY-MM-DD]
python3 tools/check_image_provenance.py [MANIFEST_TSV] [DOCS_ROOT]
```

The defaults derive from a detected repository root: the parent of `tools/` when
that parent holds `docs/index.html`, otherwise that parent's `charts_repo/`. So
the same scripts run unchanged inside the published repository and from the
private workspace that contains it. The manifest is written beside the script's
own tree, so each location refreshes its own copy; the content is identical
either way.

The manifest is **generated**, never hand-edited. Every hash, dimension and
embedded-notice value is recomputed from disk on each run; only the operation
chains, source lists and notes are declared, in `SPECS` inside the generator.
Adding an image to the site without adding a spec entry makes the generator
fail; publishing an image without a manifest row makes the checker fail.

## 7. Known drift to reconcile elsewhere

Two inputs moved after `verification/checksums.tsv` was last written, so that
table and the checksum table in `verification/methods.md` are behind the files
on disk:

| File | Listed in `checksums.tsv` | On disk 2026-09-11 |
|---|---|---|
| `charts/russell_periodic.svg` | `c6be7062821b7e3eff6b6d28b69bb97d483686279c50664f958c2d7fef75a201`, 121793 B | `2e43c1834b058005303f14b649709385e7300c00606e74fe22fcc04871416d71` |
| `data/russell_1926_elements.json` | `bae4ce953a32d374baba5adc7b9025a52708aaf4f6f0e7d7bb84c80edd867a44`, 74074 B | `ca2a21cb5439d287a89a8cff4f2751b36b107d9305d70a7c8560190b2162b950` |

The SVG changed because the licence-notice RDF block is now emitted into it; the
dataset changed with the octave-5 chart-witness amendment. Both changes are
accounted for in this manifest, which was regenerated after them. The two
checksum files are owned by their own tooling — this is a note, not an edit.
