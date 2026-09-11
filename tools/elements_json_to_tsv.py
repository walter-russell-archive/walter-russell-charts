#!/usr/bin/env python3
"""Regenerate data/russell_1926_elements.tsv from data/russell_1926_elements.json.

Usage: python3 tools/elements_json_to_tsv.py [in.json] [out.tsv]
"""
import json
import sys


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "data/russell_1926_elements.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "data/russell_1926_elements.tsv"
    with open(src, encoding="utf-8") as f:
        doc = json.load(f)
    cols = [
        "octave", "page_printed", "position_col", "position", "sigil", "name",
        "typography", "symbol", "atomic_mass", "melting_point_c",
        "status", "loc", "usp", "chart", "variants",
    ]
    lines = ["\t".join(cols)]
    for octv in doc["octaves"]:
        for row in octv["rows"]:
            w = row["witnesses"]
            lines.append("\t".join([
                str(octv["octave"]), str(octv["page_printed"]),
                row["position_col"], row["position"], row["sigil"], row["name"],
                row["typography"], row["symbol"], row["atomic_mass"],
                row["melting_point_c"], row["status"],
                w["loc"], w["usp"], w["chart"],
                "; ".join(row.get("variants", [])),
            ]))
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {dst}: {len(lines) - 1} rows")


if __name__ == "__main__":
    main()
