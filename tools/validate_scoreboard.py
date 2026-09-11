#!/usr/bin/env python3
"""R18 scoreboard validator.

Usage:
    python3 tools/validate_scoreboard.py                       # validate the schema's embedded examples
    python3 tools/validate_scoreboard.py data/scoreboard.json  # validate a built scoreboard file

Checks, per data/verdict_taxonomy.md §7:
  1. Schema validation: each entry against #/$defs/entry of data/scoreboard_schema.json
     (draft 2020-12; requires the locally installed `jsonschema` package — validation-time
     only, not part of any publication pipeline). When a scoreboard file is given, the whole
     document is additionally validated against the root schema.
  2. Referential integrity (stdlib): every cited claim_id exists in the frozen
     data/claims.json; every evidence_1926.quote_verbatim is a verbatim substring of that
     claim's quote_verbatim; printed_page and loc_index (when given) match the claim record.
  3. Rule spot-checks the schema cannot express: dual-evidence rule; entry_id uniqueness;
     class_base_rate hits+misses == class_size.

Exit status 0 iff everything passes. Deterministic; read-only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "data" / "scoreboard_schema.json"
CLAIMS_PATH = ROOT / "data" / "claims.json"


def fail(errors: list[str]) -> None:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)


def main() -> None:
    try:
        import jsonschema
    except ImportError:
        fail(["the `jsonschema` package is required for schema validation "
              "(validation-time tool dependency; see data/verdict_taxonomy.md §7)"])

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    claims = {c["id"]: c for c in json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))}
    errors: list[str] = []

    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    print(f"schema OK: {SCHEMA_PATH.name} is a valid "
          f"{schema['$schema'].rsplit('/', 2)[-2]} schema")

    if len(sys.argv) > 1:
        doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        validator_cls(schema).validate(doc)
        entries = doc["entries"]
        label = sys.argv[1]
        print(f"document OK: {label} validates against the root schema")
    else:
        entries = schema["examples"]
        label = f"{SCHEMA_PATH.name}#examples"

    entry_validator = validator_cls(
        {"$ref": "#/$defs/entry", "$defs": schema["$defs"]})

    seen_ids: set[str] = set()
    for entry in entries:
        eid = entry.get("entry_id", "<missing entry_id>")
        errs = sorted(entry_validator.iter_errors(entry), key=str)
        for err in errs:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"{eid}: schema violation at {loc}: {err.message}")
        if errs:
            continue

        if eid in seen_ids:
            errors.append(f"{eid}: duplicate entry_id")
        seen_ids.add(eid)

        # Referential integrity against the frozen claims.json.
        for cid in entry["claim_ids"] + entry.get("related_claim_ids", []):
            if cid not in claims:
                errors.append(f"{eid}: claim_id {cid} not in data/claims.json")
        for ev in entry["evidence_1926"]:
            cid = ev["claim_id"]
            claim = claims.get(cid)
            if claim is None:
                errors.append(f"{eid}: evidence_1926 cites unknown claim {cid}")
                continue
            if ev["quote_verbatim"] not in claim["quote_verbatim"]:
                errors.append(f"{eid}: evidence_1926[{cid}] quote is not a verbatim "
                              f"substring of the frozen claims.json quote")
            if ev["printed_page"] != claim["printed_page"]:
                errors.append(f"{eid}: evidence_1926[{cid}] printed_page "
                              f"{ev['printed_page']!r} != claims.json "
                              f"{claim['printed_page']!r}")
            if "loc_index" in ev and ev["loc_index"] != claim["loc_index"]:
                errors.append(f"{eid}: evidence_1926[{cid}] loc_index "
                              f"{ev['loc_index']} != claims.json {claim['loc_index']}")

        # Dual-evidence rule (taxonomy §2): belt-and-braces beside the schema conditional.
        if entry["verdict"] != "unfalsifiable" and not entry.get("evidence_modern"):
            errors.append(f"{eid}: non-unfalsifiable verdict without a modern source")

        cbr = entry.get("class_base_rate")
        if cbr and cbr["hits"] + cbr["misses"] != cbr["class_size"]:
            errors.append(f"{eid}: class_base_rate hits+misses != class_size")

        print(f"entry OK: {eid} — verdict '{entry['verdict']}', "
              f"{len(entry['evidence_1926'])} × 1926 evidence, "
              f"{len(entry.get('evidence_modern', []))} × modern source, "
              f"{len(entry.get('components', []))} component(s)")

    if errors:
        fail(errors)
    print(f"PASS: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} "
          f"validated from {label}")


if __name__ == "__main__":
    main()
