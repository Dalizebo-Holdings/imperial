#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "constitution/reconciliation/review/pillar-review.csv"

ALLOWED = {
    "KEEP",
    "POLICY",
    "TECHNICAL",
    "REFRAME",
    "R&D",
    "RETIRE",
}

with FILE.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

cluster = {
    row["pillar_id"].zfill(3): row
    for row in rows
    if 151 <= int(row["pillar_id"]) <= 200
}

if len(cluster) != 50:
    raise SystemExit(
        f"ERROR: Expected 50 Cluster D Pillars, found {len(cluster)}."
    )

for i in range(151, 201):

    pid = f"{i:03d}"
    row = cluster[pid]

    if row["approved_classification"] not in ALLOWED:
        raise SystemExit(
            f"ERROR: Pillar {pid} is not reconciled."
        )

    if not row["canonical_interpretation"].strip():
        raise SystemExit(
            f"ERROR: Pillar {pid} lacks canonical interpretation."
        )

    if not row["owner"].strip() or row["owner"] == "TBD":
        raise SystemExit(
            f"ERROR: Pillar {pid} lacks ownership."
        )

print("OK: Cluster D 151–200 constitutionally reconciled.")
