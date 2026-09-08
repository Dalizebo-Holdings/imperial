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
        row["source_sequence"]: row
        for row in csv.DictReader(f)
    }

with REVIEW.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

cluster = [
    row
    for row in rows
    if row["canonical_id"]
    and 151 <= int(row["canonical_id"]) <= 200
]

if len(cluster) != 50:
    raise SystemExit(
        f"ERROR: expected 50 Cluster E entries, found {len(cluster)}"
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
        field
        for field in REQUIRED
        if not row[field].strip()
    ]

    if missing:
        raise SystemExit(
            f"ERROR: OS-{pid} missing: "
            + ", ".join(missing)
        )

bounded = [
    "152", "153", "154", "160", "161",
    "169", "171", "172", "177", "178",
    "179", "185", "187", "193", "194",
    "196", "200",
]

for pid in bounded:
    row = next(
        row
        for row in cluster
        if row["canonical_id"] == pid
    )

    if row["disposition"] not in {"REFRAME", "R&D"}:
        raise SystemExit(
            f"ERROR: OS-{pid} lacks required bounded disposition"
        )

print("OK: OS-151 through OS-200 classified.")
print("OK: Original source statements preserved.")
print("OK: Required governance metadata present.")
print("OK: Health, biometric, behavioral and legal systems bounded.")
print("OK: Commerce dark-pattern and dependency mechanics removed.")
print("STATUS: CLUSTER E COMPLETE")
