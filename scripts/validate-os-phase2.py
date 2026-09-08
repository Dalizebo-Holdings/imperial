#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "operating-systems/source-os-registry.csv"
REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

REQUIRED = [
    "domain",
    "owner",
    "priority",
    "implementation_type",
    "dependencies",
    "policies",
    "security_level",
    "roadmap_phase",
    "disposition",
    "canonical_interpretation",
    "decision_notes",
]

with SOURCE.open(encoding="utf-8") as f:
    source_rows = list(csv.DictReader(f))

with REVIEW.open(encoding="utf-8") as f:
    review_rows = list(csv.DictReader(f))

if len(source_rows) != 279:
    raise SystemExit("ERROR: source count %d != 279" % len(source_rows))

if len(review_rows) != 279:
    raise SystemExit("ERROR: review count %d != 279" % len(review_rows))

source = {r["source_sequence"]: r for r in source_rows}

canonical = [
    r for r in review_rows
    if r["canonical_id"]
]

if len(canonical) != 269:
    raise SystemExit(
        "ERROR: canonical row count %d != 269" % len(canonical)
    )

ids = [r["canonical_id"] for r in canonical]
expected_ids = {"%03d" % i for i in range(1, 270)}

if set(ids) != expected_ids or len(set(ids)) != 269:
    raise SystemExit("ERROR: canonical ID set is not exactly OS-001 through OS-269")

for row in canonical:
    pid = row["canonical_id"]
    seq = row["source_sequence"]

    if row["source_statement"] != source[seq]["source_statement"]:
        raise SystemExit("ERROR: source modified for OS-" + pid)

    if row["review_status"] != "CLASSIFIED":
        raise SystemExit("ERROR: OS-" + pid + " is not CLASSIFIED")

    missing = [field for field in REQUIRED if not row[field].strip()]
    if missing:
        raise SystemExit(
            "ERROR: OS-" + pid + " missing: " + ", ".join(missing)
        )

overflow = [
    r for r in review_rows
    if 270 <= int(r["source_sequence"]) <= 279
]

if len(overflow) != 10:
    raise SystemExit(
        "ERROR: expected 10 overflow entries, found %d" % len(overflow)
    )

for row in overflow:
    seq = row["source_sequence"]

    if row["canonical_id"]:
        raise SystemExit(
            "ERROR: overflow source " + seq + " received canonical ID"
        )

    if row["review_status"] != "RECONCILED_OVERFLOW":
        raise SystemExit(
            "ERROR: overflow source " + seq + " is unresolved"
        )

    if row["source_statement"] != source[seq]["source_statement"]:
        raise SystemExit(
            "ERROR: overflow source statement modified at " + seq
        )

status_text = STATUS.read_text(encoding="utf-8")

if "269 / 269 complete" not in status_text:
    raise SystemExit("ERROR: STATUS.md does not report 269 / 269 complete")

if "Phase 2 complete." not in status_text:
    raise SystemExit("ERROR: STATUS.md does not mark Phase 2 complete")

print("OK: 279 source entries preserved.")
print("OK: OS-001 through OS-269 classified.")
print("OK: Required governance metadata complete.")
print("OK: Source statements unchanged.")
print("OK: Overflow 270-279 remains reconciled outside canonical ID space.")
print("STATUS: PHASE 2 COMPLETE")
