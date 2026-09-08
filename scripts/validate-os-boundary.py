#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "operating-systems/source-os-registry.csv"
REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"

with SOURCE.open(encoding="utf-8") as f:
    source = list(csv.DictReader(f))

with REVIEW.open(encoding="utf-8") as f:
    review = list(csv.DictReader(f))

if len(source) != 279:
    raise SystemExit(
        f"ERROR: source count {len(source)} != 279"
    )

if len(review) != 279:
    raise SystemExit(
        f"ERROR: review count {len(review)} != 279"
    )

source_map = {
    r["source_sequence"]: r
    for r in source
}

canonical_ids = []

for row in review:

    seq = int(row["source_sequence"])

    original = source_map[row["source_sequence"]]

    if row["source_statement"] != original["source_statement"]:
        raise SystemExit(
            f"ERROR: source statement modified at {seq}"
        )

    if seq <= 269:

        expected = f"{seq:03d}"

        if row["canonical_id"] != expected:
            raise SystemExit(
                f"ERROR: {seq} canonical ID "
                f"{row['canonical_id']!r} != {expected}"
            )

        canonical_ids.append(row["canonical_id"])

    else:

        if row["canonical_id"]:
            raise SystemExit(
                f"ERROR: overflow {seq} received canonical ID "
                f"{row['canonical_id']}"
            )

        if row["review_status"] != "RECONCILED_OVERFLOW":
            raise SystemExit(
                f"ERROR: overflow {seq} unresolved"
            )

if len(set(canonical_ids)) != 269:
    raise SystemExit("ERROR: canonical ID uniqueness failure")

expected = {
    f"{i:03d}"
    for i in range(1, 270)
}

if set(canonical_ids) != expected:
    raise SystemExit("ERROR: canonical ID range incomplete")

print("OK: 279 source entries preserved.")
print("OK: Source statements unchanged.")
print("OK: OS-001 through OS-269 unique and complete.")
print("OK: Overflow 270-279 reconciled without new IDs.")
print("STATUS: CANONICAL 269 OS BOUNDARY LOCKED")
