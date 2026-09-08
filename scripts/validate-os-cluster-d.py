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
    and 101 <= int(r["canonical_id"]) <= 150
]

if len(cluster) != 50:
    raise SystemExit(
        f"ERROR: expected 50 Cluster D entries, found {len(cluster)}"
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

# Explicit safety-sensitive source entries.
for pid in [
    "106", "107", "111", "113", "121",
    "123", "124", "125", "133", "134",
    "135", "139", "144", "150",
]:
    row = next(
        r for r in cluster
        if r["canonical_id"] == pid
    )

    if row["disposition"] not in {"REFRAME", "R&D"}:
        raise SystemExit(
            f"ERROR: OS-{pid} lacks required safety disposition"
        )

print("OK: OS-101 through OS-150 classified.")
print("OK: Original source statements preserved.")
print("OK: Required governance metadata present.")
print("OK: Physical and regional capabilities safety-bounded.")
print("STATUS: CLUSTER D COMPLETE")
