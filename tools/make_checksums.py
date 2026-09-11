#!/usr/bin/env python3
"""Regenerate verification/checksums.tsv and the checksum table in
verification/methods.md from the files themselves.

One list of published artifacts lives here, and both the machine-readable TSV
and the human-readable table in the methods page come from it. Nothing is typed
by hand, so the two cannot drift apart.

Usage:
    python3 tools/make_checksums.py            # rewrite both files
    python3 tools/make_checksums.py --check    # verify, change nothing

The script runs from the workspace root and from the published repository root:
the artifact paths are identical in both, because the repository mirrors them.
Exit status 1 means a file is missing, or --check found a stale entry.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The published artifact set: the data, the evidence documents, the two
# generated charts, the Library of Congress pages the measurements come from,
# and every tool that produces one of them.
FILES = [
    "data/russell_1926_elements.json",
    "data/russell_1926_elements.tsv",
    "data/claims.json",
    "data/modern_elements.json",
    "data/reconciliation.tsv",
    "data/scoreboard.json",
    "data/disagreements.tsv",
    "data/chart_geometry.json",
    "data/wheel_geometry.json",
    "data/scoreboard_schema.json",
    "data/verdict_taxonomy.md",
    "data/loc_page_map.tsv",
    "data/transcription_log_r11.md",
    "data/editorial_standards_public.md",
    "data/claims_notes.md",
    "data/plate_audit.md",
    "data/comparison.tsv",
    "data/restoration_study/scoring_protocol.json",
    "charts/russell_periodic.svg",
    "essay/comparison.md",
    "verification/transcription_audit.md",
    "verification/restoration_study.md",
    "verification/loc_rights.md",
    "verification/deuterium_negative.md",
    "verification/image_provenance.tsv",
    "source_scans/loc/full/p0016.jpg",
    "source_scans/loc/full/p0112.jpg",
    "source_scans/loc/full/p0113.jpg",
    "tools/restore.py",
    "tools/measure_geometry.py",
    "tools/render_chart.py",
    "tools/elements_json_to_tsv.py",
    "tools/validate_scoreboard.py",
    "tools/audit_diff.py",
    "tools/make_image_provenance.py",
    "tools/check_image_provenance.py",
    "tools/make_checksums.py",
]

TSV_PATH = ROOT / "verification" / "checksums.tsv"
METHODS_PATH = ROOT / "verification" / "methods.md"
TABLE_HEADER = "| File | Bytes | SHA256 |"


def digest(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def rows() -> list[tuple[str, str, int]]:
    out = []
    missing = []
    for rel in FILES:
        path = ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        sha, size = digest(path)
        out.append((rel, sha, size))
    if missing:
        raise SystemExit("missing published artifact(s): " + ", ".join(missing))
    return out


def tsv_text(data: list[tuple[str, str, int]]) -> str:
    lines = ["file\tsha256\tbytes"]
    lines += [f"{rel}\t{sha}\t{size}" for rel, sha, size in data]
    return "\n".join(lines) + "\n"


def table_text(data: list[tuple[str, str, int]]) -> str:
    lines = [TABLE_HEADER, "|---|---|---|"]
    lines += [f"| `{rel}` | {size} | `{sha}` |" for rel, sha, size in data]
    return "\n".join(lines)


def patched_methods(data: list[tuple[str, str, int]]) -> str:
    text = METHODS_PATH.read_text(encoding="utf-8")
    start = text.find(TABLE_HEADER)
    if start < 0:
        raise SystemExit(f"{METHODS_PATH.name}: checksum table header not found")
    end = text.find("\n\n", start)
    if end < 0:
        raise SystemExit(f"{METHODS_PATH.name}: checksum table has no end")
    return text[:start] + table_text(data) + text[end:]


def main(argv: list[str]) -> int:
    check = "--check" in argv
    data = rows()
    tsv = tsv_text(data)
    methods = patched_methods(data)
    stale = []
    if TSV_PATH.read_text(encoding="utf-8") != tsv:
        stale.append(str(TSV_PATH.relative_to(ROOT)))
    if METHODS_PATH.read_text(encoding="utf-8") != methods:
        stale.append(str(METHODS_PATH.relative_to(ROOT)))
    if check:
        if stale:
            print("STALE: " + ", ".join(stale)
                  + " — run python3 tools/make_checksums.py", file=sys.stderr)
            return 1
        print(f"checksums OK: {len(data)} artifacts, table and TSV both current")
        return 0
    TSV_PATH.write_text(tsv, encoding="utf-8")
    METHODS_PATH.write_text(methods, encoding="utf-8")
    print(f"wrote {TSV_PATH.relative_to(ROOT)} and the table in "
          f"{METHODS_PATH.relative_to(ROOT)}: {len(data)} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
