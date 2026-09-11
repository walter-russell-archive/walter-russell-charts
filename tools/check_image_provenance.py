#!/usr/bin/env python3
"""Verify verification/image_provenance.tsv against the published site tree.

Exits 0 and prints a PASS line only when all of the following hold:

  1. exhaustiveness — every image file under the site tree, every inline <svg>
     and every `data:image` URI in the generated HTML has a manifest row;
  2. no orphans    — every manifest row names a published asset that exists;
  3. uniqueness    — exactly one row per published asset;
  4. published integrity — every sha256_published matches the bytes on disk,
     and every `dimensions` value matches the measured size;
  5. source integrity   — every source_local_path resolves inside the
     repository and every sha256_source matches; counts of paths and hashes
     line up; a source that exists only outside the repository is reported;
  6. shape         — known source_class values, and source_iiif_url may be
     empty only for site_furniture (which must then name its source inputs).

Paths in the manifest are relative to the repository root, which is detected
the same way as in tools/make_image_provenance.py: the parent of tools/ when
it holds docs/index.html, otherwise that parent's charts_repo/. So the check
runs both from the private workspace and from inside the published repository.

Usage:
  python3 tools/check_image_provenance.py [MANIFEST_TSV] [DOCS_ROOT]

Regenerate the manifest with tools/make_image_provenance.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_image_provenance import (  # noqa: E402
    COLUMNS, DEFAULT_DOCS, DEFAULT_MANIFEST, REPO_ROOT, discover, resolve_source,
    source_hash,
)

VALID_CLASS = {"loc_facsimile", "data_render", "site_furniture"}


def load(manifest: Path) -> list[dict[str, str]]:
    if not manifest.is_file():
        raise SystemExit(f"manifest not found: {manifest}")
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for n, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if header is None:
            header = cells
            if header != COLUMNS:
                raise SystemExit(
                    f"{manifest} line {n}: unexpected columns\n"
                    f"  expected: {COLUMNS}\n  found:    {header}")
            continue
        if len(cells) != len(header):
            raise SystemExit(f"{manifest} line {n}: {len(cells)} cells, "
                             f"expected {len(header)}")
        row = dict(zip(header, cells))
        row["_line"] = str(n)
        rows.append(row)
    if header is None:
        raise SystemExit(f"{manifest}: no header row")
    return rows


def check(manifest: Path, docs: Path) -> list[str]:
    errors: list[str] = []
    rows = load(manifest)
    assets = {a.key: a for a in discover(docs, REPO_ROOT)}

    seen: dict[str, str] = {}
    for row in rows:
        key, line = row["published_path"], row["_line"]
        if key in seen:
            errors.append(f"duplicate row for {key!r} (lines {seen[key]} and {line})")
            continue
        seen[key] = line

        asset = assets.get(key)
        if asset is None:
            errors.append(f"line {line}: row names {key!r}, which is not published "
                          f"under {docs}")
            continue

        actual = asset.sha256
        if row["sha256_published"] != actual:
            errors.append(
                f"line {line}: {key}: sha256_published drift\n"
                f"    manifest {row['sha256_published']}\n    on disk  {actual}")
        measured = asset.dimensions()
        if row["dimensions"] != measured:
            errors.append(f"line {line}: {key}: dimensions {row['dimensions']!r} "
                          f"but measured {measured!r}")
        expect_kind = "vector" if asset.vector else "pixel"
        if row["pixel_or_vector"] != expect_kind:
            errors.append(f"line {line}: {key}: pixel_or_vector "
                          f"{row['pixel_or_vector']!r}, expected {expect_kind!r}")

        klass = row["source_class"]
        if klass not in VALID_CLASS:
            errors.append(f"line {line}: {key}: unknown source_class {klass!r} "
                          f"(expected one of {sorted(VALID_CLASS)})")

        paths = [p for p in row["source_local_path"].split("|") if p]
        hashes = [h for h in row["sha256_source"].split("|") if h]
        if not paths:
            errors.append(f"line {line}: {key}: no source_local_path")
        if len(paths) != len(hashes):
            errors.append(f"line {line}: {key}: {len(paths)} source paths but "
                          f"{len(hashes)} source hashes")
        for path, want in zip(paths, hashes):
            _, problem = resolve_source(path, asset, REPO_ROOT)
            if problem:
                errors.append(f"line {line}: {key}: {problem}")
                continue
            got = source_hash(path, asset, REPO_ROOT)
            if got != want:
                errors.append(
                    f"line {line}: {key}: sha256_source drift for {path}\n"
                    f"    manifest {want}\n    on disk  {got}\n"
                    f"    if the change is intended, re-run "
                    f"tools/make_image_provenance.py")

        if not row["source_iiif_url"] and klass != "site_furniture":
            errors.append(f"line {line}: {key}: empty source_iiif_url is allowed "
                          f"only for site_furniture, not {klass!r}")
        if not row["op_chain"]:
            errors.append(f"line {line}: {key}: empty op_chain")
        if not row["generator_script"]:
            errors.append(f"line {line}: {key}: empty generator_script")

    for key in sorted(assets):
        if key not in seen:
            where = (f"file {assets[key].path}" if assets[key].path
                     else "embedded in " + ", ".join(assets[key].html_pages))
            errors.append(f"published image has NO manifest row: {key!r} ({where})")
    return errors


def main(argv: list[str]) -> int:
    manifest = Path(argv[0]).resolve() if len(argv) > 0 else DEFAULT_MANIFEST
    docs = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_DOCS
    if not docs.is_dir():
        print(f"FAIL: site tree not found: {docs}", file=sys.stderr)
        return 2
    try:
        errors = check(manifest, docs)
    except SystemExit as exc:  # discovery or manifest-shape errors
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if errors:
        print(f"FAIL: image provenance check found {len(errors)} problem(s) "
              f"in {manifest}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    n = len(discover(docs, REPO_ROOT))
    print(f"PASS: image provenance — {n}/{n} published image assets under {docs} "
          f"have exactly one manifest row; every published SHA256, dimension and "
          f"source SHA256 matches. Repository root: {REPO_ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
