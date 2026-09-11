#!/usr/bin/env python3
"""Generate verification/image_provenance.tsv — the published-image provenance manifest.

Every row is recomputed from disk on each run: published SHA256, source SHA256,
measured dimensions, and whether an embedded licence notice is present in the
published bytes. Nothing in the TSV is typed by hand except the declarative
per-asset specs in SPECS below (op chains, source lists, notes).

Discovery is exhaustive by construction: the site tree is walked for image
files, and every generated HTML page is scanned for inline <svg> elements and
`data:image` URIs. An asset with no SPEC entry is a hard error — the manifest
cannot silently omit a published pixel.

Every path written to the manifest is relative to the REPOSITORY root, so the
file reads correctly after publication. The script runs both from the private
workspace (where the repository is the `charts_repo/` subdirectory) and from
inside the published repository itself:

    repo root = <parent of tools/>          if <parent>/docs/index.html exists
    repo root = <parent of tools/>/charts_repo   otherwise

The manifest is written beside the script's own tree, so a workspace run
refreshes the workspace copy and a repository run refreshes the repository
copy. Both runs produce byte-identical content.

Usage:
  python3 tools/make_image_provenance.py [MANIFEST_TSV] [DOCS_ROOT] [--date YYYY-MM-DD]

Output is deterministic: fixed row order, fixed derivation date, no timestamps.
Verify with tools/check_image_provenance.py.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = (SCRIPT_ROOT if (SCRIPT_ROOT / "docs" / "index.html").is_file()
             else SCRIPT_ROOT / "charts_repo")
DEFAULT_DOCS = REPO_ROOT / "docs"
DEFAULT_MANIFEST = SCRIPT_ROOT / "verification" / "image_provenance.tsv"
DEFAULT_DATE = "2026-09-11"

RASTER_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp",
              ".tif", ".tiff", ".ico"}
IMAGE_EXT = RASTER_EXT | {".svg", ".svgz"}

COLUMNS = ["published_path", "pixel_or_vector", "dimensions", "sha256_published",
           "source_class", "source_iiif_url", "source_local_path", "sha256_source",
           "op_chain", "generator_script", "embedded_notice", "notes"]

IIIF = "https://tile.loc.gov/image-services/iiif/public:gdc:27004508:{0}/full/full/0/default.jpg"

# --------------------------------------------------------------------------
# declarative per-asset specs (the only hand-written content in the manifest)
#
# Keys are repository-relative published paths, or inline-svg:<class> /
# data-uri:<sha12> for assets embedded in the generated HTML. Source paths are
# repository-relative; a `#literal` suffix means the source is the published
# markup itself, held verbatim inside that file.
# --------------------------------------------------------------------------

SPECS: dict[str, dict[str, object]] = {
    "docs/assets/facsimile.png": {
        "source_class": "loc_facsimile",
        "iiif": [IIIF.format("0016")],
        "sources": ["source_scans/loc/full/p0016.jpg",
                    "assets_src/facsimile_p0016_clean.png"],
        "op_chain": (
            "1. fetch LoC IIIF image 0016 -> source_scans/loc/full/p0016.jpg "
            "(2712x3264, 8-bit grayscale JPEG); "
            "2. tools/restore.py with pinned defaults: background = grayscale "
            "morphological closing, bg_window=101 (van Herk max->min); "
            "flatten = clip(gray/max(bg,1)*255) [divide]; binarize = global Otsu "
            "on the flattened image, otsu_threshold=166 (recomputed per input); "
            "despeckle = drop 8-connected ink components with area <= 8 px "
            "(364 components / 1176 px); frame removal = drop ink components "
            "touching the image boundary (486496 px); close_iters=0, i.e. NO "
            "morphological stroke repair; no resampling "
            "-> assets_src/facsimile_p0016_clean.png (mode L, 2712x3264); "
            "3. tools/build_site.py build_images(): "
            "PIL point(v -> 255 if v > 127 else 0), convert(\"1\"), "
            "save(PNG, optimize=True) -> docs/assets/facsimile.png. "
            "No crop, no resize, no colour transform at any step."
        ),
        "generator": "tools/restore.py; tools/build_site.py::build_images",
        "notes": (
            "Re-derived on 2026-09-11: tools/restore.py rerun from p0016.jpg "
            "reproduced assets_src/facsimile_p0016_clean.png byte for byte, and the "
            "build_images threshold/convert/save step reproduced the published PNG's "
            "decoded pixel array exactly (element-wise identical, 2712x3264 bilevel); "
            "the published file differs from that re-derivation only by the embedded "
            "licence text chunks. Parameters match verification/restoration_study.md "
            "sections 3-7 and assets_src/facsimile_p0016_params.json exactly."
        ),
    },
    "docs/assets/og-card.png": {
        "source_class": "loc_facsimile",
        "iiif": [IIIF.format("0016")],
        "sources": ["source_scans/loc/full/p0016.jpg",
                    "assets_src/facsimile_p0016_clean.png"],
        "op_chain": (
            "1. fetch LoC IIIF image 0016; "
            "2. tools/restore.py, same pinned parameters as docs/assets/facsimile.png "
            "(bg_window=101, Otsu T=166, speckle_max_area=8, close_iters=0, "
            "drop_border=True) -> assets_src/facsimile_p0016_clean.png; "
            "3. tools/build_site.py build_images(): convert(\"L\"); "
            "crop(397, 330, 2711, 2824) = 2314x2494 px (the redraw viewBox plus "
            "90 px of vertical headroom for the tone annotations); "
            "resize to 585x630 with PIL LANCZOS; paste onto an RGB 1200x630 canvas "
            "filled rgb(251,250,247) at offset (307, 0); save(PNG, optimize=True) "
            "-> docs/assets/og-card.png."
        ),
        "generator": "tools/restore.py; tools/build_site.py::build_images",
        "notes": (
            "Social-card crop of the same restored plate; no pixel from any other "
            "source. Re-derived on 2026-09-11: the decoded 1200x630 RGB pixel array "
            "is element-wise identical to the published card, which differs only by "
            "the embedded licence text chunks. The letterbox bars are flat site "
            "background, not image content."
        ),
    },
    "docs/charts/russell_periodic.svg": {
        "source_class": "data_render",
        "iiif": [IIIF.format(n) for n in
                 ("0016", "0112", "0114", "0116", "0118", "0120")],
        "sources": ["data/chart_geometry.json",
                    "data/russell_1926_elements.json",
                    "charts/russell_periodic.svg"],
        "op_chain": (
            "Not a raster derivative: no pixel of the LoC scan is copied, sampled or "
            "traced into this file. "
            "1. fetch LoC IIIF image 0016 (chart plate) and images 0112/0114/0116/0118/0120 "
            "(printed element table, pp. 92/94/96/98/100); "
            "2. tools/measure_geometry.py measures the plate -> data/chart_geometry.json "
            "(center, rings, spiral polylines, sectors, label clusters, in scan-pixel "
            "coordinates); "
            "3. R11 dual-witness transcription of the printed table -> "
            "data/russell_1926_elements.json (137 rows / 959 cells, 0 uncertain); "
            "4. tools/render_chart.py renders the SVG from those two frozen inputs: "
            "viewBox \"397 420 2314 2314\" (scan-pixel frame), spiral turn-duplication "
            "correction, 21-sample moving-average radius smoothing resampled at 0.75 deg, "
            "font-size floor 26 units from Oswald v4.103 metrics, greedy first-fit radial "
            "label tiering, fixed 2-decimal float formatting, no timestamps "
            "-> charts/russell_periodic.svg; "
            "5. tools/build_site.py build_images() injects an accessible "
            "<title> immediately after the <svg ...> open tag and writes "
            "docs/charts/russell_periodic.svg. That injection is the only difference "
            "between the repository SVG and the published SVG."
        ),
        "generator": "tools/measure_geometry.py; tools/render_chart.py; "
                     "tools/build_site.py::build_images",
        "notes": (
            "Source class is data_render: the published marks are generated from "
            "measured geometry plus the transcribed 1926 dataset, both derived from the "
            "LoC page images listed in source_iiif_url. Re-verified on 2026-09-11 after "
            "the octave-5 chart-witness amendment to data/russell_1926_elements.json: "
            "tools/render_chart.py rerun on a scratch copy of the repository reproduced "
            "charts/russell_periodic.svg byte for byte from the amended dataset, so the "
            "published redraw matches its current inputs. The published file was "
            "verified equal to charts/russell_periodic.svg plus the injected <title>."
        ),
    },
    "inline-svg:icon.icon-moon": {
        "source_class": "site_furniture",
        "iiif": [],
        "sources": ["tools/build_site.py#literal"],
        "op_chain": (
            "Hand-authored 24x24 vector path literal (one <path> crescent) in the "
            "masthead theme-toggle button of tools/build_site.py; emitted "
            "verbatim into every generated HTML page. No image input of any kind."
        ),
        "generator": "tools/build_site.py (page template)",
        "notes": (
            "Decorative UI icon, aria-hidden, first-party original geometry. Carries no "
            "1926 content and no LoC pixel. The source is the markup literal itself, "
            "so sha256_source is the hash of that literal as found verbatim in the "
            "generator; unrelated edits to build_site.py do not disturb it."
        ),
    },
    "inline-svg:icon.icon-sun": {
        "source_class": "site_furniture",
        "iiif": [],
        "sources": ["tools/build_site.py#literal"],
        "op_chain": (
            "Hand-authored 24x24 vector literal (one <circle> plus eight ray strokes in "
            "a single <path>) in the masthead theme-toggle button of "
            "tools/build_site.py; emitted verbatim into every generated "
            "HTML page. No image input of any kind."
        ),
        "generator": "tools/build_site.py (page template)",
        "notes": (
            "Decorative UI icon, aria-hidden, first-party original geometry. Carries no "
            "1926 content and no LoC pixel. The source is the markup literal itself, "
            "so sha256_source is the hash of that literal as found verbatim in the "
            "generator; unrelated edits to build_site.py do not disturb it."
        ),
    },
}

PREAMBLE = [
    "# Image provenance manifest for the published site tree docs/.",
    "# GENERATED by tools/make_image_provenance.py -- do not hand-edit; regenerate.",
    "# Verified by tools/check_image_provenance.py. Prose, assertions and re-derivation",
    "# commands: verification/image_provenance.md. Derivation/retrieval date: {date}.",
    "# All paths are relative to the repository root.",
    "# EXHAUSTIVE: every image file under docs/, every inline <svg> and every data:image",
    "# URI in the generated HTML has exactly one row below. No post-1926 work supplies",
    "# any published pixel of 1926 content (posture claim C).",
]


# --------------------------------------------------------------------------
# discovery (shared with the checker)
# --------------------------------------------------------------------------

SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg>", re.S)
CLASS_RE = re.compile(r'\bclass="([^"]*)"')
VIEWBOX_RE = re.compile(r'viewBox="([-\d.\s]+)"')
DATA_URI_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+[;,][^\"'\s)]*")


class Asset:
    """One published image: a file on disk or a fragment embedded in HTML."""

    __slots__ = ("key", "kind", "path", "payload", "html_pages")

    def __init__(self, key: str, kind: str, path: Path | None,
                 payload: bytes, html_pages: list[str]):
        self.key = key            # manifest published_path
        self.kind = kind          # "file" | "inline-svg" | "data-uri"
        self.path = path
        self.payload = payload
        self.html_pages = html_pages

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()

    @property
    def vector(self) -> bool:
        if self.kind == "file":
            return self.path.suffix.lower() in {".svg", ".svgz"}
        return self.kind == "inline-svg"

    def dimensions(self) -> str:
        if self.vector:
            text = self.payload.decode("utf-8", "replace")
            box = VIEWBOX_RE.search(text)
            if not box:
                raise SystemExit(f"{self.key}: SVG has no viewBox; cannot size it")
            values = [float(v) for v in box.group(1).split()]
            return f"{round(values[2])}x{round(values[3])}"
        return "{0}x{1}".format(*raster_size(self.payload, self.key))


def raster_size(payload: bytes, where: str) -> tuple[int, int]:
    if payload[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", payload[16:24])
        return int(w), int(h)
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        raise SystemExit(f"{where}: Pillow needed to measure this raster format")
    import io
    with Image.open(io.BytesIO(payload)) as im:
        return im.width, im.height


def published_key(path: Path, docs: Path, repo_root: Path) -> str:
    """Repository-relative key for a published file."""
    if path.is_relative_to(repo_root):
        return path.relative_to(repo_root).as_posix()
    # docs root given outside the repository (a scratch copy): keep the shape
    return f"{docs.name}/{path.relative_to(docs).as_posix()}"


def discover(docs: Path, repo_root: Path = REPO_ROOT) -> list[Asset]:
    """Every published image asset under `docs`, in deterministic key order."""
    assets: list[Asset] = []
    for path in sorted(p for p in docs.rglob("*") if p.is_file()):
        if path.suffix.lower() in IMAGE_EXT:
            assets.append(Asset(published_key(path, docs, repo_root), "file",
                                path, path.read_bytes(), []))

    inline: dict[str, tuple[str, list[str]]] = {}
    for page in sorted(docs.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        name = page.relative_to(docs).as_posix()
        for frag in SVG_RE.findall(text):
            klass = CLASS_RE.search(frag)
            token = ".".join(klass.group(1).split()) if klass else ""
            key = f"inline-svg:{token}" if token else \
                  f"inline-svg:{hashlib.sha256(frag.encode()).hexdigest()[:12]}"
            seen = inline.get(key)
            if seen is None:
                inline[key] = (frag, [name])
            elif seen[0] != frag:
                raise SystemExit(
                    f"{key}: two different inline SVGs share one key "
                    f"({seen[1][0]} vs {name}); give them distinct classes")
            else:
                seen[1].append(name)
        for uri in DATA_URI_RE.findall(text):
            key = f"data-uri:{hashlib.sha256(uri.encode()).hexdigest()[:12]}"
            seen = inline.get(key)
            if seen is None:
                inline[key] = (uri, [name])
            else:
                seen[1].append(name)

    for key, (frag, pages) in sorted(inline.items()):
        kind = "data-uri" if key.startswith("data-uri:") else "inline-svg"
        assets.append(Asset(key, kind, None, frag.encode("utf-8"), sorted(set(pages))))

    assets.sort(key=lambda a: a.key)
    return assets


# --------------------------------------------------------------------------
# source resolution
# --------------------------------------------------------------------------

LITERAL_SUFFIX = "#literal"


def resolve_source(spec_path: str, asset: Asset,
                   repo_root: Path = REPO_ROOT) -> tuple[Path, str | None]:
    """Map a repository-relative source_local_path to (file on disk, error).

    A path ending in `#literal` means the source is the published markup
    itself, held verbatim as a literal inside that file. That pins an inline
    icon to its own geometry instead of to the whole generator, so unrelated
    edits to the generator do not register as provenance drift.
    """
    base = spec_path[:-len(LITERAL_SUFFIX)] if spec_path.endswith(LITERAL_SUFFIX) \
        else spec_path
    full = repo_root / base
    if not full.is_file():
        outside = SCRIPT_ROOT / base
        if repo_root != SCRIPT_ROOT and outside.is_file():
            return full, (f"source lives outside the repository: {base} exists at "
                          f"{outside} but not under {repo_root}; sync it into the "
                          f"repository or record it as external")
        return full, f"source missing: {base}"
    if spec_path.endswith(LITERAL_SUFFIX):
        if asset.payload.decode("utf-8") not in full.read_text(encoding="utf-8"):
            return full, (f"the published markup of {asset.key} is not present "
                          f"verbatim in {base}")
    return full, None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_hash(spec_path: str, asset: Asset,
                repo_root: Path = REPO_ROOT) -> str:
    if spec_path.endswith(LITERAL_SUFFIX):
        return hashlib.sha256(asset.payload).hexdigest()
    return sha256_file(repo_root / spec_path)


# --------------------------------------------------------------------------
# embedded licence notices (N1 PNG tEXt, N2 SVG RDF)
# --------------------------------------------------------------------------

def png_text_keywords(payload: bytes) -> list[str]:
    """Keywords of every tEXt/zTXt/iTXt chunk, in file order."""
    out: list[str] = []
    pos = 8
    while pos + 8 <= len(payload):
        (length,) = struct.unpack(">I", payload[pos:pos + 4])
        ctype = payload[pos + 4:pos + 8]
        body = payload[pos + 8:pos + 8 + length]
        if ctype in (b"tEXt", b"zTXt", b"iTXt"):
            out.append(body.split(b"\x00", 1)[0].decode("latin-1", "replace"))
        elif ctype == b"IEND":
            break
        pos += 12 + length
    return out


def svg_metadata_tags(payload: bytes) -> list[str]:
    text = payload.decode("utf-8", "replace")
    block = re.search(r"<metadata\b.*?</metadata>", text, re.S)
    if not block:
        return []
    seen: list[str] = []
    for tag in re.findall(r"<([A-Za-z_][\w.:-]*)", block.group(0)):
        if tag not in seen and tag != "metadata":
            seen.append(tag)
    return seen


def embedded_notice(asset: Asset) -> str:
    """What licence metadata is embedded in the published bytes, as found."""
    if asset.kind == "file" and asset.path.suffix.lower() == ".png":
        keys = png_text_keywords(asset.payload)
        return "PNG tEXt/iTXt: " + ", ".join(keys) if keys else "none"
    if asset.vector:
        tags = svg_metadata_tags(asset.payload)
        return "SVG <metadata>: " + ", ".join(tags) if tags else "none"
    return "none"


NOTICE_STEP = {
    "PNG": ("Licence notice embedding (N1): PNG text chunks [{0}] written into the "
            "published file; pixel data unchanged."),
    "SVG": ("Licence notice embedding (N2): RDF metadata block [{0}] written into the "
            "published file; drawn geometry unchanged."),
}


def notice_op_step(asset: Asset, notice: str) -> str:
    if notice == "none":
        return ""
    kind = "SVG" if asset.vector else "PNG"
    return " " + NOTICE_STEP[kind].format(notice.split(": ", 1)[1])


# --------------------------------------------------------------------------
# manifest assembly
# --------------------------------------------------------------------------

def build_rows(docs: Path, repo_root: Path = REPO_ROOT) -> list[list[str]]:
    rows: list[list[str]] = []
    for asset in discover(docs, repo_root):
        spec = SPECS.get(asset.key)
        if spec is None:
            raise SystemExit(
                f"no provenance spec for published image {asset.key!r}.\n"
                f"Add it to SPECS in {Path(__file__).name}; the manifest must be "
                f"exhaustive.")
        sources = [str(p) for p in spec["sources"]]
        problems = [err for err in
                    (resolve_source(p, asset, repo_root)[1] for p in sources) if err]
        if problems:
            raise SystemExit(f"{asset.key}: " + "; ".join(problems))
        notice = embedded_notice(asset)
        rows.append([
            asset.key,
            "vector" if asset.vector else "pixel",
            asset.dimensions(),
            asset.sha256,
            str(spec["source_class"]),
            "|".join(spec["iiif"]),
            "|".join(sources),
            "|".join(source_hash(p, asset, repo_root) for p in sources),
            str(spec["op_chain"]) + notice_op_step(asset, notice),
            str(spec["generator"]),
            notice,
            str(spec["notes"]),
        ])
    rows.sort(key=lambda r: r[0])
    return rows


def render(rows: list[list[str]], date: str) -> str:
    lines = [line.format(date=date) for line in PREAMBLE]
    lines.append("\t".join(COLUMNS))
    for row in rows:
        if len(row) != len(COLUMNS):
            raise SystemExit(f"row width {len(row)} != {len(COLUMNS)}: {row[0]}")
        for cell in row:
            if "\t" in cell or "\n" in cell:
                raise SystemExit(f"cell contains a tab or newline: {row[0]}")
        lines.append("\t".join(row))
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    date = DEFAULT_DATE
    args: list[str] = []
    rest = list(argv)
    while rest:
        arg = rest.pop(0)
        if arg == "--date":
            if not rest:
                raise SystemExit("--date needs a value")
            date = rest.pop(0)
        elif arg.startswith("--date="):
            date = arg.split("=", 1)[1]
        elif arg.startswith("--"):
            raise SystemExit(f"unknown option {arg}")
        else:
            args.append(arg)
    manifest = Path(args[0]).resolve() if len(args) > 0 else DEFAULT_MANIFEST
    docs = Path(args[1]).resolve() if len(args) > 1 else DEFAULT_DOCS
    if not docs.is_dir():
        raise SystemExit(f"site tree not found: {docs}")
    rows = build_rows(docs, REPO_ROOT)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(render(rows, date), encoding="utf-8")
    print(f"wrote {manifest} — {len(rows)} published image assets "
          f"from {docs}\nrepository root: {REPO_ROOT}")
    for row in rows:
        print(f"  {row[0]:<34} {row[1]:<6} {row[2]:<10} {row[4]:<14} notice={row[10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
