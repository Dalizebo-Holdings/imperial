#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "operating-systems/source-os-registry.csv"
REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"

REQUIRED = [
    "domain",
    "owner",
    "priority",
    "implementation_type",
    "dependencies",
    "policies",
    "security_level",
    "roadmap_phase",
    "canonical_interpretation",
    "decision_notes",
]

with SOURCE.open(encoding="utf-8") as f:
    source = {
        r["source_sequence"]: r
        for r in csv.DictReader(f)
    }

with REVIEW.open(encoding="utf-8") as f:
    review = list(csv.DictReader(f))

cluster = [
    r for r in review
    if r["canonical_id"] and 1 <= int(r["canonical_id"]) <= 20
]

if len(cluster) != 20:
    raise SystemExit(
        f"ERROR: expected 20 Cluster A entries, found {len(cluster)}"
    )

for row in cluster:

    seq = row["source_sequence"]

    if row["source_statement"] != source[seq]["source_statement"]:
        raise SystemExit(
            f"ERROR: source statement modified for OS-{row['canonical_id']}"
        )

    if row["review_status"] != "CLASSIFIED":
        raise SystemExit(
            f"ERROR: OS-{row['canonical_id']} not classified"
        )

    missing = [
        field for field in REQUIRED
        if not row[field].strip()
    ]

    if missing:
        raise SystemExit(
            f"ERROR: OS-{row['canonical_id']} missing: "
            + ", ".join(missing)
        )

print("OK: OS-001 through OS-020 classified.")
print("OK: Source statements preserved.")
print("OK: Required governance metadata present.")
print("STATUS: CLUSTER A COMPLETE")
