#!/usr/bin/env python3
"""Build the chart-edition static site in docs/ from this repository's data.

    python3 tools/build_site.py                 # full build
    python3 tools/build_site.py --skip-images   # HTML only (images already built)
    python3 tools/build_site.py --base https://charts.walterrussellarchive.org

Adapted from the Dube Verdict site build (russell-coil-dube-verdict, CC BY 4.0).

The data in data/, essay/, verification/ and charts/ stays the single source of
truth. docs/ is generated output: never hand-edit it. Image derivatives need
Pillow. Everything else is standard library.

Staging: while this repository sits inside the research workspace, the build
first syncs its inputs from the workspace (one direction only; the frozen
research files are never written). Once the repository stands alone, the sync
step finds no workspace and the repo-local copies are the inputs.

The build FAILS LOUDLY on missing required inputs, malformed dataset rows,
schema-invalid scoreboard entries, or unrecorded image sizes. Optional pages
(methods, FAQ, reading order) are skipped with a loud warning when their
Markdown source is absent.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mdlite  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT.parent  # research workspace during staging; may not exist later
OUT = ROOT / "docs"
ASSETS = Path(__file__).resolve().parent / "assets"

DEFAULT_BASE = "https://charts.walterrussellarchive.org"
ARCHIVE = "https://walterrussellarchive.org"
# Repository slug. The subdomain is charts.walterrussellarchive.org, so the
# repository carries the same boring name.
REPO = "https://github.com/walter-russell-archive/charts"
LOC_ITEM = "https://www.loc.gov/item/27004508/"
CONTACT = "contact@walterrussellarchive.org"
CC_BY_NC = "https://creativecommons.org/licenses/by-nc/4.0/"
RETRIEVED = "September 11, 2026"

WARNINGS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    bar = "!" * 72
    print(f"{bar}\n!! BUILD WARNING: {msg}\n{bar}", file=sys.stderr)


def die(msg: str) -> None:
    raise SystemExit(f"BUILD FAILED: {msg}")


# --------------------------------------------------------------------------
# staging sync (workspace -> repo, never the reverse)
# --------------------------------------------------------------------------

# Every artifact the methods page cites by path and SHA256 ships in the
# repository, at the same relative path the checksum command uses, so the
# re-derivation commands run verbatim for a reader.
SYNC = [
    # (workspace-relative source, repo-relative destination, required)
    ("data/russell_1926_elements.json", "data/russell_1926_elements.json", True),
    ("data/russell_1926_elements.tsv", "data/russell_1926_elements.tsv", True),
    ("data/claims.json", "data/claims.json", True),
    ("data/modern_elements.json", "data/modern_elements.json", True),
    ("data/reconciliation.tsv", "data/reconciliation.tsv", True),
    ("data/disagreements.tsv", "data/disagreements.tsv", True),
    ("data/chart_geometry.json", "data/chart_geometry.json", True),
    ("data/wheel_geometry.json", "data/wheel_geometry.json", True),
    ("data/verdict_taxonomy.md", "data/verdict_taxonomy.md", True),
    ("data/loc_page_map.tsv", "data/loc_page_map.tsv", True),
    ("data/transcription_log_r11.md", "data/transcription_log_r11.md", True),
    ("data/editorial_standards_public.md", "data/editorial_standards_public.md", True),
    ("data/scoreboard_schema.json", "data/scoreboard_schema.json", True),
    ("data/scoreboard.json", "data/scoreboard.json", False),
    ("charts/russell_periodic.svg", "charts/russell_periodic.svg", True),
    ("data/restoration_study/final/p0016_30_clean.png",
     "assets_src/facsimile_p0016_clean.png", True),
    ("data/restoration_study/final/p0016_params.json",
     "assets_src/facsimile_p0016_params.json", True),
    ("verification/methods.md", "verification/methods.md", False),
    ("verification/checksums.tsv", "verification/checksums.tsv", False),
    ("verification/transcription_audit.md", "verification/transcription_audit.md", True),
    ("verification/restoration_study.md", "verification/restoration_study.md", True),
    ("verification/loc_rights.md", "verification/loc_rights.md", True),
    ("verification/deuterium_negative.md", "verification/deuterium_negative.md", True),
    ("verification/image_provenance.tsv", "verification/image_provenance.tsv", False),
    ("verification/image_provenance.md", "verification/image_provenance.md", False),
    ("essay/faq.md", "essay/faq.md", False),
    ("essay/reading_order.md", "essay/reading_order.md", False),
    # The three Library of Congress page images the measurements were taken
    # from. Public domain; the plate, and the two table pages.
    ("source_scans/loc/full/p0016.jpg", "source_scans/loc/full/p0016.jpg", True),
    ("source_scans/loc/full/p0112.jpg", "source_scans/loc/full/p0112.jpg", True),
    ("source_scans/loc/full/p0113.jpg", "source_scans/loc/full/p0113.jpg", True),
    # The generators the methods page names, so every number is re-derivable.
    ("tools/restore.py", "tools/restore.py", True),
    ("tools/measure_geometry.py", "tools/measure_geometry.py", True),
    ("tools/render_chart.py", "tools/render_chart.py", True),
    ("tools/validate_scoreboard.py", "tools/validate_scoreboard.py", True),
    ("tools/audit_diff.py", "tools/audit_diff.py", True),
    ("tools/elements_json_to_tsv.py", "tools/elements_json_to_tsv.py", True),
    ("tools/make_image_provenance.py", "tools/make_image_provenance.py", False),
    ("tools/make_checksums.py", "tools/make_checksums.py", True),
    ("tools/check_image_provenance.py", "tools/check_image_provenance.py", False),
]

# Only these files may ever appear under the repository's source_scans/ tree.
# The USP 1974 scan lives in the private workspace under the same directory
# name, and no pixel of it may reach the repository.
SOURCE_SCAN_WHITELIST = {
    "source_scans/loc/full/p0016.jpg",
    "source_scans/loc/full/p0112.jpg",
    "source_scans/loc/full/p0113.jpg",
}


def sync_inputs() -> None:
    for src_rel, dst_rel, required in SYNC:
        src = PROJECT / src_rel
        dst = ROOT / dst_rel
        if src.exists():
            stale = not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime
            if stale:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                print(f"sync: {src_rel} -> {dst_rel}")
        if required and not dst.exists():
            die(f"required input missing: {dst_rel} "
                f"(and no workspace copy at {src_rel})")


def check_source_scans() -> None:
    """The repository publishes three Library of Congress pages and nothing else
    under source_scans/. A stray file there is a provenance failure."""
    root = ROOT / "source_scans"
    if not root.exists():
        die("source_scans/ is missing: the published pages cite it by path")
    found = {str(p.relative_to(ROOT)) for p in root.rglob("*") if p.is_file()}
    extra = sorted(found - SOURCE_SCAN_WHITELIST)
    if extra:
        die("source_scans/ carries files that are not the whitelisted Library of "
            f"Congress pages: {extra}")
    missing = sorted(SOURCE_SCAN_WHITELIST - found)
    if missing:
        die(f"whitelisted source pages missing from the repository: {missing}")
    print(f"source scans OK: {len(found)} Library of Congress pages, nothing else")


def check_checksums() -> None:
    """A published hash table that no longer matches its files is worse than no
    table at all, so a stale one fails the build."""
    script = ROOT / "tools" / "make_checksums.py"
    if not script.exists():
        die("tools/make_checksums.py is missing: the checksum table cannot be verified")
    proc = subprocess.run([sys.executable, str(script), "--check"],
                          cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        die("checksum table is stale: "
            + (proc.stderr.strip() or proc.stdout.strip()))
    print(proc.stdout.strip())


# --------------------------------------------------------------------------
# dataset (frozen transcription)
# --------------------------------------------------------------------------

ROW_FIELDS = ("position_col", "position", "sigil", "name", "typography",
              "symbol", "atomic_mass", "melting_point_c")
# The printed table has seven cells per row: the position column, the name,
# its typography, the tone number with its sign (one printed cell), the
# symbol, the atomic mass, and the melting point.
CELLS_PER_ROW = 7
TYPOGRAPHY = {"italic", "caps", "smallcaps", "roman"}


def load_elements() -> dict:
    path = ROOT / "data" / "russell_1926_elements.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    octaves = data.get("octaves")
    if not isinstance(octaves, list) or len(octaves) != 10:
        die(f"dataset: expected 10 octaves, found "
            f"{len(octaves) if isinstance(octaves, list) else 'none'}")
    errors: list[str] = []
    n_rows = 0
    for octave in octaves:
        for key in ("octave", "page_printed", "title_verbatim", "footnotes", "rows"):
            if key not in octave:
                errors.append(f"octave {octave.get('octave', '?')}: missing {key}")
        for row in octave.get("rows", []):
            n_rows += 1
            where = f"octave {octave.get('octave', '?')} row {row.get('position_col', '?')}"
            for field in ROW_FIELDS:
                if not isinstance(row.get(field), str):
                    errors.append(f"{where}: missing or non-string cell {field!r}")
            if row.get("typography") not in TYPOGRAPHY:
                errors.append(f"{where}: unknown typography {row.get('typography')!r}")
            if row.get("status") not in ("agreed", "resolved"):
                errors.append(f"{where}: unknown status {row.get('status')!r}")
    counts = data.get("counts", {})
    expect_rows = 137
    expect_cells = counts.get("row_cells_total")
    if n_rows != expect_rows:
        errors.append(f"dataset holds {n_rows} rows; the frozen table has {expect_rows}")
    if n_rows * CELLS_PER_ROW != expect_cells:
        errors.append(f"{n_rows} rows x {CELLS_PER_ROW} cells = "
                      f"{n_rows * CELLS_PER_ROW}, but counts.row_cells_total = {expect_cells}")
    if errors:
        die("dataset validation:\n  " + "\n  ".join(errors))
    print(f"dataset OK: 10 octaves, {n_rows} rows, {n_rows * CELLS_PER_ROW} cells")
    return data


# --------------------------------------------------------------------------
# scoreboard (schema-validated; examples + loud banner until the real file lands)
# --------------------------------------------------------------------------


def _check_type(value, spec: dict, where: str, errors: list[str]) -> None:
    kind = spec.get("type")
    ok = {"string": str, "integer": int, "boolean": bool,
          "array": list, "object": dict}
    if kind in ok and not isinstance(value, ok[kind]):
        errors.append(f"{where}: expected {kind}, got {type(value).__name__}")


def _check_object(value, spec: dict, defs: dict, where: str, errors: list[str]) -> None:
    """Minimal stdlib validation: required keys, enums, primitive types.

    Full draft-2020-12 validation stays with tools/validate_scoreboard.py in
    the research workspace (jsonschema is a validation-time-only dependency).
    This checker is what makes the site build fail loudly rather than render
    a malformed scoreboard.
    """
    while "$ref" in spec:
        spec = defs[spec["$ref"].rsplit("/", 1)[-1]]
    if "enum" in spec:
        if value not in spec["enum"]:
            errors.append(f"{where}: {value!r} not in {spec['enum']}")
        return
    if "const" in spec:
        if value != spec["const"]:
            errors.append(f"{where}: expected {spec['const']!r}, got {value!r}")
        return
    if "pattern" in spec and isinstance(value, str):
        if not re.match(spec["pattern"], value):
            errors.append(f"{where}: {value!r} fails pattern {spec['pattern']}")
    _check_type(value, spec, where, errors)
    if isinstance(value, dict) and spec.get("type") == "object":
        for req in spec.get("required", []):
            if req not in value:
                errors.append(f"{where}: missing required field {req!r}")
        for key, sub in (spec.get("properties") or {}).items():
            if key in value:
                _check_object(value[key], sub, defs, f"{where}.{key}", errors)
    if isinstance(value, list) and spec.get("type") == "array":
        item_spec = spec.get("items")
        if isinstance(item_spec, dict):
            for i, item in enumerate(value):
                _check_object(item, item_spec, defs, f"{where}[{i}]", errors)


def load_scoreboard() -> tuple[list[dict], bool]:
    """Returns (entries, is_preview). Preview = schema examples, not the real file."""
    schema = json.loads((ROOT / "data" / "scoreboard_schema.json").read_text(encoding="utf-8"))
    defs = schema["$defs"]
    real = ROOT / "data" / "scoreboard.json"
    if real.exists():
        doc = json.loads(real.read_text(encoding="utf-8"))
        errors: list[str] = []
        _check_object(doc, schema, defs, "scoreboard", errors)
        entries = doc.get("entries", [])
        preview = False
        label = "data/scoreboard.json"
    else:
        entries = schema["examples"]
        errors = []
        preview = True
        label = "scoreboard_schema.json#examples"
        bar = "!" * 72
        print(f"{bar}\n!! INCOMPLETE: data/scoreboard.json is not written yet.\n"
              f"!! The scoreboard page is built from the schema's five worked\n"
              f"!! examples and says so on the page. Rebuild once the real\n"
              f"!! scoreboard lands.\n{bar}", file=sys.stderr)
        WARNINGS.append("scoreboard built from schema examples (data/scoreboard.json missing)")
    seen: set[str] = set()
    entry_spec = defs["entry"]
    for i, entry in enumerate(entries):
        eid = entry.get("entry_id", f"<entry {i}>")
        _check_object(entry, entry_spec, defs, eid, errors)
        if eid in seen:
            errors.append(f"{eid}: duplicate entry_id")
        seen.add(eid)
    if errors:
        die("scoreboard validation:\n  " + "\n  ".join(errors))
    print(f"scoreboard OK: {len(entries)} entries from {label}")
    return entries, preview


# --------------------------------------------------------------------------
# images (facsimile, redraw SVG, OG card) + recorded intrinsic dimensions
# --------------------------------------------------------------------------

DIMS_FILE = OUT / "assets" / "dimensions.json"
DIMS: dict[str, list[int]] = {}


def load_dims() -> None:
    """Intrinsic image sizes, so pages reserve space before an image loads."""
    global DIMS
    if not DIMS_FILE.exists():
        die("no assets/dimensions.json; run the image step (drop --skip-images)")
    DIMS = json.loads(DIMS_FILE.read_text(encoding="utf-8"))


def dims_for(key: str) -> list[int]:
    got = DIMS.get(key)
    if not got:
        die(f"no recorded size for image {key!r}; run the image step first")
    return got


def svg_viewbox(text: str, where: str) -> tuple[int, int]:
    box = re.search(r'viewBox="([\d.\s+-]+)"', text)
    if not box:
        die(f"{where}: no viewBox, cannot size the image")
    values = [float(v) for v in box.group(1).split()]
    return round(values[2]), round(values[3])


SVG_TITLE = ("The Russell Periodic Chart of Atomic Weights, 1926 "
             "\u2014 measured redraw")

# N1 notice, verbatim (data/license_drafts/notice_conventions.md). Written into
# the tEXt chunks of every published raster. Fixed strings only: no Creation
# Time chunk, so the images stay byte-deterministic.
N1_NOTICE = (
    "Facsimile plate from Walter Russell, The Universal One (Brieger Press, "
    "New York, 1926). The 1926 edition is in the public domain. We claim no "
    "copyright over this reproduction. Restoration used deterministic image "
    "operations only. Source: Library of Congress, "
    "https://www.loc.gov/item/27004508/. Credit Line: Library of Congress."
)
N1_SOURCE = "https://www.loc.gov/item/27004508/"


def png_notice(title: str):
    from PIL.PngImagePlugin import PngInfo

    meta = PngInfo()
    meta.add_text("Title", title)
    meta.add_text("Copyright", N1_NOTICE)
    meta.add_text("Source", N1_SOURCE)
    return meta


def build_images(force: bool = False) -> None:
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        raise SystemExit("Pillow is required for the image step; use --skip-images")

    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "charts").mkdir(parents=True, exist_ok=True)

    # Facsimile: full-resolution 1-bit PNG. This single file is both the
    # page image and the zoom asset (see NOTES_viewer_decision.md).
    src = ROOT / "assets_src" / "facsimile_p0016_clean.png"
    out_png = OUT / "assets" / "facsimile.png"
    stale = force or not out_png.exists() or out_png.stat().st_mtime < src.stat().st_mtime
    if stale:
        with Image.open(src) as im:
            im.point(lambda v: 255 if v > 127 else 0).convert("1").save(
                out_png, "PNG", optimize=True,
                pnginfo=png_notice("The Russell Periodic Chart of Atomic "
                                   "Weights, 1926 \u2014 restored facsimile"))
        print(f"images: facsimile.png written ({out_png.stat().st_size:,} bytes)")
    with Image.open(out_png) as im:
        DIMS["facsimile"] = [im.width, im.height]

    # OG card: deterministic center crop of the facsimile on the site background.
    og_out = OUT / "assets" / "og-card.png"
    if force or not og_out.exists() or og_out.stat().st_mtime < src.stat().st_mtime:
        with Image.open(src) as im:
            # The chart frame is (397,420)-(2711,2734) (the redraw viewBox);
            # the tone annotations extend ~90 px above and below it, so take
            # that vertical headroom too and letterbox the result.
            crop = im.convert("L").crop((397, 330, 2711, 2824))
            h = 630
            w = round(crop.width * h / crop.height)
            crop = crop.resize((w, h), Image.LANCZOS)
            card = Image.new("RGB", (1200, 630), (251, 250, 247))
            card.paste(crop.convert("RGB"), ((1200 - w) // 2, 0))
            card.save(og_out, "PNG", optimize=True,
                      pnginfo=png_notice("The Russell Periodic Chart of Atomic "
                                         "Weights, 1926 \u2014 detail"))
        print("images: og-card.png written")
    DIMS["og-card"] = [1200, 630]

    # Redraw: copy the SVG, injecting an accessible <title> ahead of its <desc>.
    svg_src = ROOT / "charts" / "russell_periodic.svg"
    text = svg_src.read_text(encoding="utf-8")
    w, h = svg_viewbox(text, "charts/russell_periodic.svg")
    if "<title>" not in text:
        opened = text.find(">", text.find("<svg")) + 1
        text = text[:opened] + f"\n<title>{SVG_TITLE}</title>" + text[opened:]
    (OUT / "charts" / "russell_periodic.svg").write_text(text, encoding="utf-8")
    DIMS["redraw"] = [w, h]

    DIMS_FILE.write_text(json.dumps(DIMS, indent=0, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------
# layout
# --------------------------------------------------------------------------

PAGES: list[tuple[str, str]] = []  # (href, nav label) for pages actually built


def page(
    *,
    title: str,
    description: str,
    current: str,
    body: str,
    base: str,
    og_type: str = "article",
    noindex: bool = False,
) -> str:
    # The 404 page (the only noindex page) is served at any missing URL, at any
    # depth, so every internal reference on it must be absolute.
    prefix = f"{base}/" if noindex else ""
    nav = "\n".join(
        '      <a href="{href}"{cur}>{label}</a>'.format(
            href=prefix + href, label=label, cur=' aria-current="page"' if href == current else ""
        )
        for href, label in PAGES
    )
    esc_title = html.escape(title, quote=True)
    esc_desc = html.escape(description, quote=True)
    canonical = f"{base}/{current}" if current != "index.html" else f"{base}/"
    if noindex:
        head_meta = '<meta name="robots" content="noindex">'
    else:
        head_meta = f"""<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc_title}">
<meta property="og:description" content="{esc_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{base}/assets/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">"""
    # N4 footer notice, verbatim (data/license_drafts/notice_conventions.md),
    # with its two designated links.
    n4 = (f'Original work on this site is licensed '
          f'<a href="{CC_BY_NC}" rel="noopener">CC BY-NC 4.0</a>. '
          f'The 1926 facsimile plates are in the public domain. '
          f'We claim no copyright over them. Credit Line: Library of Congress. '
          f'Copyright holders with concerns may '
          f'<a href="{REPO}/issues" rel="noopener">open an issue</a> in the repository. '
          f'We correct demonstrated factual errors promptly.')
    # Non-affiliation notice (legal playbook proof item E2, posture claim F:
    # nominative use of the names, no affiliation implied). Every page carries
    # it, including the 404 page.
    non_affiliation = (
        'This site is an independent archive project. It has no affiliation with '
        'the University of Science and Philosophy, with the Walter Russell estate, '
        'or with any successor organization. The name of the author and the title '
        'of the book identify the subject of study only.')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{esc_title}</title>
<meta name="description" content="{esc_desc}">
{head_meta}
<link rel="stylesheet" href="{prefix}assets/site.css">
<script>document.documentElement.classList.add("js");try{{var t=localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
</head>
<body>
<header class="masthead">
  <div class="masthead-inner">
    <a class="wordmark" href="{prefix}index.html">Walter Russell Archive</a>
    <nav>
{nav}
      <button class="theme-toggle" type="button" data-theme-toggle aria-pressed="false"
              aria-label="Switch to the dark theme" title="Switch to the dark theme">
        <svg class="icon icon-moon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        <svg class="icon icon-sun" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="4.6"/><path d="M12 1.4v2.4M12 20.2v2.4M4.4 4.4l1.7 1.7M17.9 17.9l1.7 1.7M1.4 12h2.4M20.2 12h2.4M4.4 19.6l1.7-1.7M17.9 6.1l1.7-1.7"/></svg>
      </button>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site">
  <div class="footer-inner">
    <p>{n4}</p>
    <p>{non_affiliation}</p>
    <p>Source scan: Walter Russell, <em>The Universal One</em> (Brieger Press, New York, 1926),
       Library of Congress, <a href="{LOC_ITEM}" rel="noopener">item 27004508</a>.
       This edition is part of the <a href="{ARCHIVE}" rel="noopener">Walter Russell Archive</a>.</p>
    <p>Contact: <a href="mailto:{CONTACT}">{CONTACT}</a>
       &middot; The pages are generated from the repository data by <code>tools/build_site.py</code>.</p>
  </div>
</footer>
<script src="{prefix}assets/site.js"></script>
</body>
</html>
"""


def title_block(kicker: str, heading: str, subtitle: str, tools: list[tuple[str, str]]) -> str:
    buttons = "".join(
        '<a href="{href}"{rel}>{label}</a>'.format(
            href=href,
            label=html.escape(label),
            rel=' rel="noopener"' if href.startswith("http") else "",
        )
        for label, href in tools
    )
    return f"""<div class="title-block">
  <p class="kicker">{kicker}</p>
  <h1>{heading}</h1>
  <p class="subtitle">{subtitle}</p>
  <div class="toolbar">{buttons}</div>
</div>"""


def link_map() -> dict[str, str]:
    links = {
        "essay/faq.md": "faq.html",
        "essay/reading_order.md": "reading-order.html",
        "verification/methods.md": "methods.html",
        "data/russell_1926_elements.json": "dataset.html",
        "data/scoreboard.json": "scoreboard.html",
        "data/scoreboard_schema.json": "scoreboard.html",
        "charts/russell_periodic.svg": "charts/russell_periodic.svg",
        "verification/checksums.tsv": "verification/checksums.tsv",
    }
    for href, _ in PAGES:
        links[f"./{href}"] = href
    return links


# --------------------------------------------------------------------------
# home
# --------------------------------------------------------------------------


def build_index(base: str, have: dict[str, bool]) -> str:
    head = title_block(
        "Free web edition",
        "The Russell periodic chart, 1926",
        "A restored facsimile, a measured redraw, and the full ten-octave element "
        "table from <em>The Universal One</em>.",
        [
            ("The chart", "chart.html"),
            ("The dataset", "dataset.html"),
            ("The scoreboard", "scoreboard.html"),
            ("Walter Russell Archive", ARCHIVE),
        ],
    )

    reading = ""
    extras = []
    if have["methods.html"]:
        extras.append('<li><a href="methods.html">Methods</a> &mdash; how every image and every cell was produced, step by step.</li>')
    if have["faq.html"]:
        extras.append('<li><a href="faq.html">FAQ</a> &mdash; direct answers to the questions this chart attracts.</li>')
    if have["reading-order.html"]:
        extras.append('<li><a href="reading-order.html">Reading order</a> &mdash; a suggested path through the material.</li>')
    if extras:
        reading = "\n".join(extras)

    body = f"""{head}
<article class="prose">
<p class="lede">Walter Russell published <em>The Universal One</em> in New York in 1926.
The book prints a circular chart of the elements and a ten-octave table of 137 rows.
This site is a free web edition of both.</p>

<h2 id="what-is-here">What is here</h2>
<ul>
  <li><a href="chart.html">The chart</a> &mdash; the restored 1926 plate and a measured
      redraw, in one viewer.</li>
  <li><a href="dataset.html">The dataset</a> &mdash; all 137 rows and 959 cells of the
      printed table, as an HTML table.</li>
  <li><a href="scoreboard.html">The scoreboard</a> &mdash; claims printed in the book,
      each with a verdict and its evidence.</li>
{reading}
</ul>

<h2 id="provenance">Where the images come from</h2>
<p>Every image on this site derives from one source: the Library of Congress scan of the
1926 edition, <a href="{LOC_ITEM}" rel="noopener">item 27004508</a>.
The Library's
<a href="https://www.loc.gov/collections/selected-digitized-books/about-this-collection/rights-and-access/" rel="noopener">rights
statement</a> covers this collection (retrieved {RETRIEVED}). It reads: &ldquo;The books
in this collection are in the public domain and are free to use and reuse.&rdquo;
Credit Line: Library of Congress.</p>
<p>Restoration used deterministic image operations only: background flattening, one global
threshold, and despeckling. No pixel was drawn by hand or by a model. The redraw was
measured from the scan and generated from the transcribed table.</p>

<h2 id="what-this-edition-is-not">What this edition is not</h2>
<p>This edition does not argue that the 1926 book anticipated modern chemistry.
Where the book makes a testable claim, <a href="scoreboard.html">the scoreboard</a> tests
it and shows the evidence. Verdicts attach to claims, never to people. The plates and the
table are presented whole, so readers can check every verdict against the source.</p>

<h2 id="about-the-archive">Part of the archive</h2>
<p>This edition is one project of the
<a href="{ARCHIVE}" rel="noopener">Walter Russell Archive</a>, which publishes primary
sources for Walter Russell's scientific claims with their provenance stated.
Corrections are welcome: write to <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
</article>"""
    return page(
        title="The Russell periodic chart, 1926 — free web edition",
        description=(
            "Walter Russell's 1926 periodic chart from The Universal One: a restored "
            "facsimile from the Library of Congress scan, a measured redraw, the full "
            "137-row element table, and a claim-by-claim scoreboard."
        ),
        current="index.html",
        body=body,
        base=base,
        og_type="website",
    )


# --------------------------------------------------------------------------
# chart page (facsimile / redraw toggle, pan-zoom, tabular record linked first)
# --------------------------------------------------------------------------


def build_chart(base: str, have: dict[str, bool]) -> str:
    fw, fh = dims_for("facsimile")
    rw, rh = dims_for("redraw")
    params = json.loads(
        (ROOT / "assets_src" / "facsimile_p0016_params.json").read_text(encoding="utf-8"))
    threshold = params["otsu_threshold"]
    speckle = params["speckle_max_area"]
    window = params["bg_window"]

    head = title_block(
        "The chart",
        "The Russell Periodic Chart of Atomic Weights",
        "The 1926 plate, restored, beside a redraw measured from it. One viewer, two "
        "fidelities.",
        [
            ("The dataset", "dataset.html"),
            ("Full facsimile image", "assets/facsimile.png"),
            ("Redraw SVG", "charts/russell_periodic.svg"),
            ("LoC source scan", LOC_ITEM),
        ],
    )

    methods_link = (' The full pipeline is on <a href="methods.html">the methods page</a>.'
                    if have["methods.html"] else "")

    facsimile_alt = ("Restored 1926 plate: concentric octave rings of element names "
                     "around a central spiral, with hand-lettered labels.")
    redraw_alt = ("Vector redraw of the same chart: the measured rings and all 137 "
                  "element labels, in clean type.")

    body = f"""{head}
<div class="prose">
<p>Every label on this chart is transcribed in <a href="dataset.html">the dataset
table</a>. The table is the citable record; the images are the witness.</p>
</div>
<div class="viewer">
  <input type="radio" name="view" id="view-facsimile" checked>
  <input type="radio" name="view" id="view-redraw">
  <div class="view-toggle" role="group" aria-label="Chart view">
    <span class="group-label" aria-hidden="true">View</span>
    <label for="view-facsimile">Facsimile</label>
    <label for="view-redraw">Redraw</label>
  </div>
  <div class="pane pane-facsimile" data-panzoom tabindex="0" role="group"
       aria-label="Facsimile viewer. Zoomable image.">
    <img src="assets/facsimile.png" alt="{facsimile_alt}" width="{fw}" height="{fh}">
  </div>
  <div class="pane pane-redraw" data-panzoom tabindex="0" role="group"
       aria-label="Redraw viewer. Zoomable image.">
    <img src="charts/russell_periodic.svg" alt="{redraw_alt}" width="{rw}" height="{rh}" decoding="async">
  </div>
  <p class="viewer-help">Keyboard: Tab to the image, then + and &minus; zoom, arrow keys
  pan, 0 resets. Mouse: scroll zooms, drag pans, double-click zooms in.</p>
  <p class="pane-caption"><b>Facsimile.</b> The 1926 plate, cleaned. Source: Library of
  Congress, <a href="{LOC_ITEM}" rel="noopener">item 27004508</a>, image 0016.
  Credit Line: Library of Congress. The image above is the full-resolution file
  ({fw}&times;{fh}).
  <b>Redraw.</b> Generated from the measured plate geometry and the transcribed table.
  License: <a href="{CC_BY_NC}" rel="noopener">CC BY-NC 4.0</a>.</p>
</div>
<div class="prose">
<h2 id="how-the-facsimile-was-made">How the facsimile was made</h2>
<p>Restoration is deterministic. Every output pixel is a function of the Library of
Congress scan.{methods_link} The steps, in order:</p>
<ol>
  <li>Estimate the page background by grayscale closing, window {window}&nbsp;px.</li>
  <li>Divide the scan by the background to flatten illumination.</li>
  <li>Binarize with one global Otsu threshold (value {threshold} on this scan).</li>
  <li>Remove ink specks of {speckle}&nbsp;px or less.</li>
  <li>Drop components that touch the image border (the scanner frame).</li>
</ol>
<p>Not done: no inpainting, no learned enhancement, no manual retouching. The unmodified
scan remains available from the
<a href="{LOC_ITEM}" rel="noopener">Library of Congress</a> at full resolution.</p>

<h2 id="how-the-redraw-was-made">How the redraw was made</h2>
<p>The redraw places 117 element labels at positions measured on the scan. Twenty more
placements are computed from the measured ring geometry. The renderer reads the
<a href="dataset.html">transcribed dataset</a> and the measured geometry, and its output
is byte-deterministic. Prose ring texts and marginal annotations of the plate are not
element data and are not reproduced. The SVG labels use the Oswald typeface when
installed and fall back to a system sans-serif.</p>
</div>"""
    return page(
        title="The chart — the Russell Periodic Chart of Atomic Weights, 1926",
        description=(
            "Russell's 1926 periodic chart in two fidelities: the restored Library of "
            "Congress plate and a measured vector redraw, with a keyboard-accessible "
            "toggle and pan-zoom viewer."
        ),
        current="chart.html",
        body=body,
        base=base,
    )


# --------------------------------------------------------------------------
# dataset page (the 137-row table)
# --------------------------------------------------------------------------

NAME_CLASS = {"italic": "name-italic", "caps": "name-caps",
              "smallcaps": "name-smallcaps", "roman": ""}
SPACING_NOTE = "spacing only"


def octave_table(octave: dict) -> str:
    o = octave["octave"]
    title = html.escape(" — ".join(octave["title_verbatim"][:1]))
    sub = html.escape(" ".join(octave["title_verbatim"][1:]))
    sub_html = f'<span class="octave-sub">{sub}</span>' if sub else ""
    rows_html: list[str] = []
    notes: list[str] = []
    for row in octave["rows"]:
        cls = NAME_CLASS[row["typography"]]
        name = html.escape(row["name"])
        if cls:
            name = f'<span class="{cls}">{name}</span>'
        marker = ""
        resolution = row.get("resolution", "")
        substantive = resolution and not resolution.startswith(SPACING_NOTE)
        row_notes = [n for n in (resolution if substantive else "",
                                 row.get("notes", "")) if n]
        if row_notes:
            notes.append(f"<b>{html.escape(row['position_col'])} "
                         f"{html.escape(row['name'])}:</b> "
                         + " ".join(html.escape(n) for n in row_notes))
            marker = f'<sup><a href="#o{o}-notes" aria-label="Note for this row">&dagger;</a></sup>'
        tone = html.escape(row["position"] + row["sigil"])
        rows_html.append(
            f'<tr><td class="sigil">{html.escape(row["position_col"])}</td>'
            f"<td>{name}{marker}</td>"
            f'<td class="sigil">{tone}</td>'
            f"<td>{html.escape(row['symbol'])}</td>"
            f'<td class="num">{html.escape(row["atomic_mass"])}</td>'
            f'<td class="num">{html.escape(row["melting_point_c"])}</td></tr>'
        )
    for foot in octave["footnotes"]:
        notes.append(f"<b>Printed footnote:</b> {html.escape(foot)}")
    if octave.get("margin_anomaly"):
        notes.append(f"<b>Margin anomaly:</b> {html.escape(octave['margin_anomaly'])}")
    if octave.get("layout_anomaly"):
        notes.append(f"<b>Layout anomaly:</b> {html.escape(octave['layout_anomaly'])}")
    for line in octave.get("trailing_lines", []):
        notes.append(f"<b>Printed after the table:</b> {html.escape(line)}")
    notes_html = ""
    if notes:
        notes_html = (f'<div class="table-note" id="o{o}-notes">'
                      + "".join(f"<p>{n}</p>" for n in notes) + "</div>")
    return f"""<div class="table-wrap">
<table>
<caption id="octave-{o}">Octave {o}: {title}{sub_html}
<span class="octave-sub">Printed page {octave["page_printed"]}.</span></caption>
<thead><tr><th scope="col">Position</th><th scope="col">Name</th><th scope="col">Tone</th>
<th scope="col">Symbol</th><th scope="col" class="num">Atomic mass</th>
<th scope="col" class="num">Melting point (&deg;C)</th></tr></thead>
<tbody>
{chr(10).join(rows_html)}
</tbody>
</table>
</div>
{notes_html}"""


def build_dataset(base: str, elements: dict) -> str:
    counts = elements["counts"]
    head = title_block(
        "The dataset",
        "The ten-octave table",
        "All 137 rows of Russell's element table, printed pages 92&ndash;100, "
        "transcribed cell by cell.",
        [
            ("The chart", "chart.html"),
            ("The scoreboard", "scoreboard.html"),
            ("LoC source scan", LOC_ITEM),
        ],
    )
    toc = "\n".join(
        f'    <li><a href="#octave-{o["octave"]}">Octave {o["octave"]}</a>'
        f' &mdash; {html.escape(o["title_verbatim"][0].title())}</li>'
        for o in elements["octaves"]
    )
    plate_title = html.escape(" ".join(elements["page_title_p92_verbatim"]))
    tables = "\n".join(octave_table(o) for o in elements["octaves"])
    body = f"""{head}
<div class="prose">
<p>The tables below reproduce the ten-octave element table of
<em>The Universal One</em> (1926). The book titles it:</p>
<blockquote><p>{plate_title}</p></blockquote>
<p>The transcription source is the Library of Congress scan,
<a href="{LOC_ITEM}" rel="noopener">item 27004508</a>. A second, independent scan of the
same 1926 printing plates was read blind and reconciled against it. Of
{counts["row_cells_total"]} cells, {counts["agreed_first_pass"]} agreed on the first
pass. {counts["resolved"]} were resolved: {counts["resolved_spacing_convention"]} by a
stated spacing convention and {counts["resolved_glyph_adjudication"]} by glyph
measurement. {counts["uncertain"]} remain uncertain.</p>
<h2 id="conventions">Reading the table</h2>
<ul>
  <li>Signs are printed characters: + and &minus; and = follow the print. A dagger mark
      (&#8225;) is Russell's.</li>
  <li>A conspicuously long dash in the print is kept as a long dash (&mdash;); the
      ordinary minus is kept as a minus (&minus;).</li>
  <li><span class="name-italic">Italic</span> and
      <span class="name-smallcaps">small-capital</span> names follow the print.</li>
  <li>An empty cell is empty in the print.</li>
  <li>A &dagger; on a row links to a note: an adjudicated reading or a plate anomaly.
      Row notes quote the reconciliation record verbatim. In them, USP names the second
      witness: a 1974 photographic reprint of the same plates.</li>
</ul>
<nav class="callout toc" aria-label="Octaves">
  <h2>The ten octaves</h2>
  <ul>
{toc}
  </ul>
</nav>
</div>
<div class="prose-wide">
{tables}
</div>"""
    return page(
        title="The dataset — Russell's ten-octave element table, 1926",
        description=(
            "The complete 137-row, 959-cell transcription of Walter Russell's ten-octave "
            "element table from The Universal One (1926), double-witnessed against two "
            "scans, with every printed footnote and layout anomaly."
        ),
        current="dataset.html",
        body=body,
        base=base,
    )


# --------------------------------------------------------------------------
# scoreboard page
# --------------------------------------------------------------------------


def entry_section(entry: dict) -> str:
    eid = entry["entry_id"]
    parts: list[str] = [f'<section class="entry" id="{eid}">']
    parts.append(f"<h2>{eid}. {html.escape(entry['title'])}</h2>")
    parts.append(f'<p><span class="verdict">{html.escape(entry["verdict"])}</span></p>')
    parts.append(f'<p class="verdict-sentence">{html.escape(entry["verdict_sentence"])}</p>')

    meta: list[str] = []
    if entry.get("claim_ids"):
        meta.append("<li><b>Claims:</b> " + ", ".join(entry["claim_ids"]) + "</li>")
    if entry.get("related_claim_ids"):
        meta.append("<li><b>Related claims:</b> " + ", ".join(entry["related_claim_ids"]) + "</li>")
    meta.append(f"<li><b>Scope:</b> {html.escape(entry['claim_scope'])}"
                + (f" &mdash; {html.escape(entry['scope_note'])}" if entry.get("scope_note") else "")
                + "</li>")
    if entry.get("novelty_1926"):
        meta.append(f"<li><b>Novelty in 1926:</b> {html.escape(entry['novelty_1926'])}</li>")
    parts.append('<ul class="entry-meta">' + "".join(meta) + "</ul>")

    fp = entry.get("folklore_provenance")
    if fp:
        parts.append("<h3>The claim under test</h3>")
        parts.append(f"<p>&ldquo;{html.escape(fp['statement'])}&rdquo;</p>")
        parts.append(f'<p class="evidence-cite">Provenance: {html.escape(fp["provenance"])}</p>')

    av = entry.get("absence_verification")
    if av:
        parts.append("<h3>Absence verification</h3>")
        parts.append(f"<p>{html.escape(av['method_summary'])} "
                     f"Documented in <code>{html.escape(av['document'])}</code>.</p>")

    ra = entry.get("reading_adopted")
    if ra:
        parts.append("<h3>Reading adopted</h3>")
        parts.append(f"<p>{html.escape(ra['reading'])}</p>")

    if entry.get("evidence_1926"):
        parts.append("<h3>What the 1926 text prints</h3>")
        for ev in entry["evidence_1926"]:
            cite = f"Printed page {html.escape(ev['printed_page'])}"
            if ev.get("claim_id"):
                cite += f", claim {ev['claim_id']}"
            note = f" {html.escape(ev['note'])}" if ev.get("note") else ""
            parts.append(
                f'<blockquote class="evidence-quote"><p>{html.escape(ev["quote_verbatim"])}</p>'
                f'</blockquote><p class="evidence-cite">{cite}.{note}</p>'
            )

    if entry.get("evidence_modern"):
        parts.append("<h3>Modern evidence</h3><ul>")
        for src in entry["evidence_modern"]:
            note = f" {html.escape(src['note'])}" if src.get("note") else ""
            parts.append(
                f'<li><a href="{html.escape(src["url"], quote=True)}" rel="noopener">'
                f"{html.escape(src['name'])}</a> (retrieved {html.escape(src['retrieved'])}).{note}</li>"
            )
        parts.append("</ul>")

    if entry.get("components"):
        parts.append("<h3>Components</h3><ul>")
        for c in entry["components"]:
            flag = " Rests on an uncertain datum." if c.get("rests_on_uncertain_datum") else ""
            note = f" {html.escape(c['note'])}" if c.get("note") else ""
            parts.append(
                f"<li><b>{html.escape(c['status'])}</b> ({html.escape(c['role'])}): "
                f"{html.escape(c['statement'])}{flag}{note}</li>"
            )
        parts.append("</ul>")

    cbr = entry.get("class_base_rate")
    if cbr:
        parts.append("<h3>Class base rate</h3>")
        parts.append(f"<p>{html.escape(cbr.get('class_description', ''))} "
                     f"Class size {cbr.get('class_size')}: {cbr.get('hits')} hit(s), "
                     f"{cbr.get('misses')} miss(es).</p>")

    if entry.get("printed_variants"):
        parts.append("<h3>Printed variants</h3><ul>")
        for v in entry["printed_variants"]:
            parts.append(f"<li>{v.get('claim_id', '')}: "
                         f"{html.escape(v.get('printed_value', ''))} "
                         f"{html.escape(v.get('note', ''))}</li>")
        parts.append("</ul>")

    parts.append("<h3>Analysis</h3>")
    parts.append(f"<p>{html.escape(entry['analysis'])}</p>")

    if entry.get("uncertainty_flags"):
        parts.append("<h3>Uncertainty</h3><ul>")
        for u in entry["uncertainty_flags"]:
            parts.append(f"<li><b>{html.escape(u['resolution'])}:</b> "
                         f"{html.escape(u['description'])}</li>")
        parts.append("</ul>")
    if entry.get("resolution_needed"):
        parts.append(f"<p><b>What would resolve it:</b> {html.escape(entry['resolution_needed'])}</p>")

    parts.append("</section>")
    return "\n".join(parts)


def build_scoreboard(base: str, entries: list[dict], preview: bool) -> str:
    head = title_block(
        "The scoreboard",
        "Claims and verdicts",
        "Claims printed in <em>The Universal One</em> (1926), or attached to it later, "
        "each tested against stated evidence.",
        [
            ("The dataset", "dataset.html"),
            ("The chart", "chart.html"),
        ],
    )
    preview_note = ""
    if preview:
        preview_note = """<div class="callout" role="note">
<p><b>Preview.</b> This page currently shows the five worked entries that ship with the
scoreboard schema. The full scoreboard replaces them when it is finished.</p>
</div>"""
    summary_rows = "\n".join(
        f'<tr><td><a href="#{e["entry_id"]}">{e["entry_id"]}</a></td>'
        f'<td><span class="verdict">{html.escape(e["verdict"])}</span></td>'
        f"<td>{html.escape(e['title'])}</td>"
        f"<td>{', '.join(e.get('claim_ids', [])) or '&mdash;'}</td></tr>"
        for e in entries
    )
    sections = "\n".join(entry_section(e) for e in entries)
    body = f"""{head}
<div class="prose">
<p>Each entry below tests one claim. The verdict vocabulary is closed: confirmed,
partially confirmed, unfalsifiable, refuted, never claimed, terminology only,
undetermined. The subject of every verdict is the claim, not a person. Every entry cites
its evidence: verbatim 1926 quotations with page numbers, and modern sources with URLs
and retrieval dates. Each entry states what evidence would change it.</p>
{preview_note}
</div>
<div class="prose-wide">
<h2 id="summary">All entries</h2>
<div class="table-wrap">
<table>
<caption class="sr-only">Scoreboard entries with their verdicts</caption>
<thead><tr><th scope="col">Entry</th><th scope="col">Verdict</th>
<th scope="col">Claim under test</th><th scope="col">Claim ids</th></tr></thead>
<tbody>
{summary_rows}
</tbody>
</table>
</div>
{sections}
</div>"""
    return page(
        title="The scoreboard — claims and verdicts, The Universal One (1926)",
        description=(
            "Claim-by-claim verdicts on Walter Russell's The Universal One (1926): "
            "verbatim 1926 evidence, modern sources with retrieval dates, and a closed "
            "verdict vocabulary."
        ),
        current="scoreboard.html",
        body=body,
        base=base,
    )


# --------------------------------------------------------------------------
# markdown-sourced pages (methods, FAQ, reading order)
# --------------------------------------------------------------------------

MD_PAGES = [
    # (source, output page, nav label, kicker)
    ("verification/methods.md", "methods.html", "Methods", "Methods"),
    ("essay/faq.md", "faq.html", "FAQ", "Questions"),
    ("essay/reading_order.md", "reading-order.html", "Reading order", "Orientation"),
]


CODE_REF_LINKS = {
    "data/russell_1926_elements.json": "dataset.html",
    "data/scoreboard.json": "scoreboard.html",
    "data/scoreboard_schema.json": "scoreboard.html",
    "charts/russell_periodic.svg": "charts/russell_periodic.svg",
}


def link_refs(doc_html: str, entry_ids: set[str]) -> str:
    """Link <code>file</code> mentions to their pages, and bare scoreboard
    entry ids (V001) to their sections. Only ids built this run are linked,
    so a preview scoreboard never produces a dead anchor."""
    for name, href in CODE_REF_LINKS.items():
        doc_html = doc_html.replace(
            f"<code>{name}</code>", f'<a href="{href}"><code>{name}</code></a>')

    def link_id(m: re.Match[str]) -> str:
        eid = m.group(0)
        if eid not in entry_ids:
            return eid
        return f'<a href="scoreboard.html#{eid}">{eid}</a>'

    return re.sub(r"(?<![#\w/-])V\d{3}\b", link_id, doc_html)


def build_md_page(base: str, src_rel: str, current: str, kicker: str,
                  entry_ids: set[str]) -> str:
    text = (ROOT / src_rel).read_text(encoding="utf-8")
    lines = text.replace("\r\n", "\n").split("\n")
    heading = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else current
    body_md = "\n".join(lines[1:]) if lines and lines[0].startswith("#") else text
    rendered = mdlite.render(body_md, links=link_map(), anchors=True)
    rendered = link_refs(rendered, entry_ids)
    contents = ""
    h2s = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', rendered)
    if len(h2s) >= 3:
        items = "\n".join(f'    <li><a href="#{i}">{t}</a></li>' for i, t in h2s)
        contents = f"""<nav class="callout toc" aria-label="Contents">
  <h2>Contents</h2>
  <ul>
{items}
  </ul>
</nav>"""
    head = title_block(kicker, html.escape(heading), "", [])
    body = f"""{head}
<article class="prose">
{contents}
{rendered}
</article>"""
    description = f"{heading} — the Russell chart edition."
    return page(
        title=f"{heading} — the Russell chart edition",
        description=description,
        current=current,
        body=body,
        base=base,
    )


def build_notfound(base: str) -> str:
    links = "".join(
        f'<a href="{base}/{href if href != "index.html" else ""}">{label}</a>'
        for href, label in PAGES
    )
    body = f"""<div class="title-block">
  <p class="kicker">404</p>
  <h1>Page not found</h1>
  <p class="subtitle">There is no page at this address.</p>
  <div class="toolbar">{links}</div>
</div>
<div class="prose">
<p>Possibly the page moved, or the link has an error. The pages above hold all the
content of this site. If a link on this site sent you here, please tell
<a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
</div>"""
    return page(
        title="Page not found — Walter Russell Archive",
        description="There is no page at this address.",
        current="404.html",
        body=body,
        base=base,
        noindex=True,
    )


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# The archive never links the store, in any spelling. Checked on every build.
# The needles are assembled from parts so this file never contains one itself.
_STORE_WORDS = ("fair", "copy", "press")
FORBIDDEN = tuple(sep.join(_STORE_WORDS) for sep in ("", " ", "-"))


def check_one_way_rule() -> None:
    """The whole repository is checked, not only the generated pages: every file
    here is published the moment the repository is public."""
    text_suffixes = (".html", ".xml", ".txt", ".svg", ".json", ".md", ".tsv",
                     ".py", ".css", ".js", "")
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or ".git" in path.parts:
            continue
        if path.suffix not in text_suffixes:
            continue
        low = path.read_text(encoding="utf-8", errors="ignore").lower()
        checked += 1
        for needle in FORBIDDEN:
            if needle in low:
                die(f"one-way rule: {path.relative_to(ROOT)} contains {needle!r}")
    print(f"one-way rule OK: no store reference in {checked} repository files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="canonical site base URL")
    parser.add_argument("--skip-images", action="store_true", help="do not rebuild images")
    parser.add_argument("--force-images", action="store_true", help="rebuild every image")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    sync_inputs()
    check_source_scans()
    check_checksums()
    elements = load_elements()
    entries, preview = load_scoreboard()

    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    for asset in ("site.css", "site.js"):
        shutil.copyfile(ASSETS / asset, OUT / "assets" / asset)

    # A custom base means a custom domain: Pages needs the CNAME file in docs/.
    host = base.split("//", 1)[-1].split("/")[0]
    if host.endswith(".github.io"):
        (OUT / "CNAME").unlink(missing_ok=True)
    else:
        (OUT / "CNAME").write_text(host + "\n", encoding="utf-8")

    if args.skip_images:
        load_dims()
        print("images: skipped")
    else:
        build_images(force=args.force_images)

    # Which pages exist this build? Nav, sitemap and 404 all follow this list.
    have = {out: (ROOT / src).exists() for src, out, _, _ in MD_PAGES}
    PAGES.clear()
    PAGES.extend([
        ("index.html", "Home"),
        ("chart.html", "The chart"),
        ("dataset.html", "The dataset"),
        ("scoreboard.html", "The scoreboard"),
    ])
    for src, out, label, _ in MD_PAGES:
        if have[out]:
            PAGES.append((out, label))
        else:
            warn(f"{src} not present; {out} skipped this build")

    checksums = ROOT / "verification" / "checksums.tsv"
    if checksums.exists():
        (OUT / "verification").mkdir(exist_ok=True)
        shutil.copyfile(checksums, OUT / "verification" / "checksums.tsv")

    write(OUT / "index.html", build_index(base, have))
    write(OUT / "chart.html", build_chart(base, have))
    write(OUT / "dataset.html", build_dataset(base, elements))
    write(OUT / "scoreboard.html", build_scoreboard(base, entries, preview))
    for src, out, _, kicker in MD_PAGES:
        if have[out]:
            entry_ids = {e["entry_id"] for e in entries}
            write(OUT / out, build_md_page(base, src, out, kicker, entry_ids))
    write(OUT / "404.html", build_notfound(base))

    urls = "".join(
        f"  <url><loc>{base}/{'' if href == 'index.html' else href}</loc></url>\n"
        for href, _ in PAGES
    )
    write(
        OUT / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n",
    )
    write(OUT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    check_one_way_rule()
    index_html = (OUT / "index.html").read_text(encoding="utf-8")
    if ARCHIVE not in index_html:
        die("home page lost its archive cross-link")

    for href, _ in PAGES + [("404.html", "")]:
        size = (OUT / href).stat().st_size
        print(f"{href}: {size:,} bytes")
    if WARNINGS:
        print("build finished WITH WARNINGS:", file=sys.stderr)
        for w in WARNINGS:
            print(f"  !! {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
