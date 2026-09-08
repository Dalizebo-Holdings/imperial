#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "constitution" / "pillar-registry.csv"
REVIEW = ROOT / "constitution" / "reconciliation" / "review" / "pillar-review.csv"

ALLOWED = {
    "KEEP",
    "POLICY",
    "TECHNICAL",
    "R&D",
    "REFRAME",
    "RETIRE",
    "UNREVIEWED",
}

with SOURCE.open(encoding="utf-8") as f:
    source_rows = {
        row["pillar_id"]: row
        for row in csv.DictReader(f)
    }

with REVIEW.open(encoding="utf-8") as f:
    review_rows = list(csv.DictReader(f))

if len(source_rows) != 207:
    raise SystemExit(
        f"ERROR: Source contains {len(source_rows)} Pillars, expected 207."
    )

if len(review_rows) != 207:
    raise SystemExit(
        f"ERROR: Review contains {len(review_rows)} Pillars, expected 207."
    )

seen = set()
unreviewed = 0

for row in review_rows:
    pid = row["pillar_id"]

    if pid in seen:
        raise SystemExit(f"ERROR: Duplicate Pillar {pid}")

    seen.add(pid)

    if pid not in source_rows:
        raise SystemExit(f"ERROR: Unknown Pillar {pid}")

    original = source_rows[pid]["source_statement"].strip()
    review_source = row["source_statement"].strip()

    if original != review_source:
        raise SystemExit(
            f"ERROR: Source statement modified for Pillar {pid}"
        )

    classification = row["approved_classification"]

    if classification not in ALLOWED:
        raise SystemExit(
            f"ERROR: Invalid classification '{classification}' for Pillar {pid}"
        )

    if classification == "UNREVIEWED":
        unreviewed += 1

print("OK: 207 Pillars accounted for.")
print("OK: Original statements preserved.")
print(f"Remaining unreviewed Pillars: {unreviewed}")

if unreviewed:
    print("STATUS: RECONCILIATION IN PROGRESS")
else:
    print("STATUS: CONSTITUTIONALLY RECONCILED")
