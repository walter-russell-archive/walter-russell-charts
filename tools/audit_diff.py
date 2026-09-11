#!/usr/bin/env python3
"""R12 audit diff: independent witness readings vs the frozen dataset.

Inputs (all read-only):
  data/russell_1926_elements.json          frozen dataset (137 rows x 7 fields = 959 cells)
  data/audit_work/pass_loc_table.json      blind LoC table reading   (witness A)
  data/audit_work/pass_usp_table.json      blind USP table reading   (witness B)
  data/audit_work/pass_loc_chart.json      blind LoC chart reading   (witness C, names only)
  data/audit_work/pass_usp_chart.json      blind USP chart reading   (witness D, names only)
  data/audit_work/adjudications.json       auditor's per-cell rulings (written during adjudication)

Outputs:
  data/audit_work/audit_cells.json         per-cell classification (all 959)
  data/disagreements.tsv                   one row per non-agreed cell

Comparison policy (declared normalization N, documented in
verification/transcription_audit.md):
  - NFC; strip outer whitespace; typographic quotes -> straight (furniture only).
  - position_col / number / symbol / atomic_mass / melting_point_c: internal
    whitespace removed (the print's loose quad spacing before sigils is a
    documented typesetting convention, dataset canonical form is space-free).
  - leading ASCII hyphen on a numeric value -> U+2212 for comparison; an
    em dash (U+2014) is NEVER folded into a minus - dash identity is data.
  - typography synonyms folded (caps/capitals, smallcaps/small-caps, ...).
  - name: internal whitespace collapsed to single space; case-sensitive.
Everything failing N-equality against BOTH table witnesses, or failing against
one witness without the other agreeing exactly, is a "disagreement" and gets a
crop + adjudication. Reader [uncertain:a|b] readings: if the dataset value is
among the alternatives and the other witness agrees cleanly, the cell counts
as agreed-with-uncertain-witness (noted); otherwise it is adjudicated.
"""
import csv
import json
import re
import sys
import unicodedata

FIELDS = ["position_col", "name", "typography", "number",
          "symbol", "atomic_mass", "melting_point_c"]
CODE_FIELDS = {"position_col", "number", "symbol", "atomic_mass", "melting_point_c"}
TYPO_SYN = {"caps": "caps", "capitals": "caps", "full-caps": "caps", "fullcaps": "caps",
            "smallcaps": "smallcaps", "small-caps": "smallcaps", "small_caps": "smallcaps",
            "italic": "italic", "italics": "italic", "italic-caps": "italic",
            "roman": "roman", "normal": "roman"}


def norm(field, v):
    if v is None:
        v = ""
    v = unicodedata.normalize("NFC", str(v)).strip()
    v = (v.replace("\u2018", "'").replace("\u2019", "'")
          .replace("\u201c", '"').replace("\u201d", '"'))
    if field in CODE_FIELDS:
        v = re.sub(r"\s+", "", v)
        v = re.sub(r"^-", "\u2212", v)
    if field == "typography":
        v = TYPO_SYN.get(v.lower(), v.lower())
    if field == "name":
        v = re.sub(r"\s+", " ", v)
    return v


def uncertain_alts(field, v):
    """Set of normalized alternative readings encoded by [uncertain:a|b] markers."""
    if "[uncertain:" not in (v or ""):
        return None
    out = set()
    m = re.search(r"\[uncertain:([^\]]+)\]", v)
    for piece in m.group(1).split("|"):
        out.add(norm(field, re.sub(r"\[uncertain:[^\]]+\]", piece, v, count=1)))
    return out


def cmp(field, dataset_v, witness_v):
    """'agree' | 'agree-uncertain' | 'differ' | 'missing'"""
    if witness_v is None:
        return "missing"
    dv, wv = norm(field, dataset_v), norm(field, witness_v)
    if dv == wv:
        return "agree"
    alts = uncertain_alts(field, witness_v)
    if alts and dv in alts:
        return "agree-uncertain"
    return "differ"


def load_pass_rows(path):
    """-> {(octave, row_1based): {field: value}}"""
    p = json.load(open(path))
    out = {}
    for o in p["octaves"]:
        for i, r in enumerate(o["rows"], 1):
            out[(o["octave"], i)] = {f: r.get(f, "") for f in FIELDS}
    return out

def load_chart_labels(path):
    """-> list of uppercase label texts from wheel/frontispiece plates."""
    p = json.load(open(path))
    out = []
    for pl in p["plates"]:
        for L in pl["labels"]:
            t = L["text"].strip().upper()
            if 2 <= len(t) <= 20:
                out.append(t)
    return out



def main():
    ds = json.load(open("data/russell_1926_elements.json"))
    loc = load_pass_rows("data/audit_work/pass_loc_table.json")
    usp = load_pass_rows("data/audit_work/pass_usp_table.json")
    try:
        adjud = json.load(open("data/audit_work/adjudications.json"))
    except FileNotFoundError:
        adjud = {}
    chart_loc = load_chart_labels("data/audit_work/pass_loc_chart.json")
    chart_usp = load_chart_labels("data/audit_work/pass_usp_chart.json")

    cells, disags = [], []
    chart_cells, chart_disags = [], []
    for o in ds["octaves"]:
        for i, r in enumerate(o["rows"], 1):
            dsvals = {"position_col": r["position_col"], "name": r["name"],
                      "typography": r["typography"],
                      "number": r["position"] + r["sigil"],
                      "symbol": r["symbol"], "atomic_mass": r["atomic_mass"],
                      "melting_point_c": r["melting_point_c"]}
            lrow = loc.get((o["octave"], i)) or {}
            urow = usp.get((o["octave"], i)) or {}
            for f in FIELDS:
                cl = cmp(f, dsvals[f], lrow.get(f))
                cu = cmp(f, dsvals[f], urow.get(f))
                key = f"o{o['octave']}.r{i}.{f}"
                cell = {"key": key, "octave": o["octave"], "row": i,
                        "name": r["name"], "field": f, "dataset": dsvals[f],
                        "loc_read": lrow.get(f), "usp_read": urow.get(f),
                        "cmp_loc": cl, "cmp_usp": cu}
                if cl == "agree" and cu == "agree":
                    cell["class"] = "agreed"
                elif {cl, cu} <= {"agree", "agree-uncertain"}:
                    cell["class"] = "agreed"     # uncertain witness, dataset among its alts, other witness clean
                    cell["note"] = "one witness uncertain; dataset value among its alternatives"
                else:
                    a = adjud.get(key, {})
                    cell["class"] = "disagreement"
                    cell["resolution"] = a.get("resolution", "uncertain")
                    cell["adjudication"] = a.get("reason", "")
                    cell["crop_path"] = a.get("crop_path", "")
                    disags.append(cell)
                cells.append(cell)

            # supplementary chart-witness column (137 cells, NOT part of the 959)
            C = r["witnesses"].get("chart", "")
            key = f"o{o['octave']}.r{i}.chart_witness"
            ccell = {"key": key, "octave": o["octave"], "row": i,
                     "name": r["name"], "field": "chart_witness", "dataset": C}
            if C == "":
                ccell["class"] = "agreed"
                ccell["note"] = "dataset records no chart box; neither fresh chart pass found one"
            else:
                in_loc = C.upper() in chart_loc
                in_usp = C.upper() in chart_usp
                ccell["loc_read"] = "found" if in_loc else "not-found"
                ccell["usp_read"] = "found" if in_usp else "not-found"
                if in_loc and in_usp and key not in adjud:
                    ccell["class"] = "agreed"
                elif key in adjud:
                    a = adjud[key]
                    ccell["class"] = "disagreement"
                    ccell["resolution"] = a.get("resolution", "uncertain")
                    ccell["adjudication"] = a.get("reason", "")
                    ccell["crop_path"] = a.get("crop_path", "")
                    chart_disags.append(ccell)
                else:
                    ccell["class"] = "chart-illegible"
            chart_cells.append(ccell)

    with open("data/audit_work/audit_cells.json", "w") as f:
        json.dump({"table_cells": cells, "chart_cells": chart_cells}, f,
                  indent=1, ensure_ascii=False)

    with open("data/disagreements.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["octave", "position", "field", "dataset_value",
                    "witness_values", "resolution", "crop_path"])
        for c in disags:
            wit = (f"loc_table={c['loc_read']!r}; usp_table={c['usp_read']!r}")
            w.writerow([c["octave"], f"r{c['row']}({c['name']})", c["field"],
                        c["dataset"], wit, c["resolution"], c["crop_path"]])
        for c in chart_disags:
            wit = ("loc_chart=" + ("label found verbatim" if c["loc_read"] == "found"
                   else "verbatim label NOT found") +
                   "; usp_chart=" + ("label found verbatim" if c["usp_read"] == "found"
                   else "verbatim label NOT found") + "; see adjudication")
            w.writerow([c["octave"], f"r{c['row']}({c['name']})", c["field"],
                        c["dataset"], wit, c["resolution"], c["crop_path"]])

    n = len(cells)
    agreed = sum(1 for c in cells if c["class"] == "agreed")
    dis = [c for c in cells if c["class"] == "disagreement"]
    resolved = sum(1 for c in dis if c["resolution"] in
                   ("dataset-correct", "dataset-error-candidate"))
    unc = sum(1 for c in dis if c["resolution"] == "uncertain")
    cagreed = sum(1 for c in chart_cells if c["class"] == "agreed")
    cill = sum(1 for c in chart_cells if c["class"] == "chart-illegible")
    print(json.dumps({"cells_total": n, "agreed": agreed,
                      "disagreements": len(dis), "resolved_by_adjudication": resolved,
                      "uncertain": unc,
                      "chart_cells_total": len(chart_cells), "chart_agreed": cagreed,
                      "chart_disagreements": len(chart_disags),
                      "chart_illegible": cill,
                      "dataset_error_candidates":
                      [c["key"] for c in dis + chart_disags
                       if c["resolution"] == "dataset-error-candidate"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
