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
    "disposition",
    "canonical_interpretation",
    "decision_notes",
]

with SOURCE.open(encoding="utf-8") as f:
    source = {
        r["source_sequence"]: r
        for r in csv.DictReader(f)
    }

with REVIEW.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

cluster = [
    r for r in rows
    if r["canonical_id"]
    and 51 <= int(r["canonical_id"]) <= 100
]

if len(cluster) != 50:
    raise SystemExit(
        f"ERROR: expected 50 Cluster C entries, found {len(cluster)}"
    )

for row in cluster:

    pid = row["canonical_id"]
    seq = row["source_sequence"]

    if row["source_statement"] != source[seq]["source_statement"]:
        raise SystemExit(
            f"ERROR: source modified for OS-{pid}"
        )

    if row["review_status"] != "CLASSIFIED":
        raise SystemExit(
            f"ERROR: OS-{pid} not classified"
        )

    missing = [
        field for field in REQUIRED
        if not row[field].strip()
    ]

    if missing:
        raise SystemExit(
            f"ERROR: OS-{pid} missing "
            + ", ".join(missing)
        )

# Explicit safety boundaries for high-risk source concepts.
for pid in ["053","054","055","064","074","076","077","078","089"]:
    row = next(r for r in cluster if r["canonical_id"] == pid)

    if row["disposition"] != "REFRAME":
        raise SystemExit(
            f"ERROR: OS-{pid} must remain canonically reframed"
        )

print("OK: OS-051 through OS-100 classified.")
print("OK: Original source statements preserved.")
print("OK: Required governance metadata present.")
print("OK: High-risk source concepts canonically bounded.")
print("STATUS: CLUSTER C COMPLETE")
