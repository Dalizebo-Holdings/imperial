#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "operating-systems/source-os-registry.csv"
OUTPUT = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/OVERFLOW_REVIEW.md"

FIELDS = [
    "source_sequence",
    "cluster",
    "cluster_name",
    "local_id",
    "declared_id",
    "name",
    "source_statement",

    "canonical_id",
    "review_status",
    "domain",
    "owner",
    "priority",
    "implementation_type",

    "dependencies",
    "inputs",
    "outputs",
    "policies",
    "events",
    "apis",
    "data_requirements",
    "security_level",
    "roadmap_phase",

    "disposition",
    "canonical_interpretation",
    "decision_notes",
]

with SOURCE.open(encoding="utf-8") as f:
    source = list(csv.DictReader(f))

if len(source) != 279:
    raise SystemExit(
        f"ERROR: expected 279 preserved source entries, found {len(source)}"
    )

rows = []

for src in source:

    seq = int(src["source_sequence"])

    row = {field: "" for field in FIELDS}

    for field in [
        "source_sequence",
        "cluster",
        "cluster_name",
        "local_id",
        "declared_id",
        "name",
        "source_statement",
    ]:
        row[field] = src[field]

    if seq <= 269:
        row["canonical_id"] = f"{seq:03d}"
        row["review_status"] = "UNREVIEWED"
        row["disposition"] = "CANONICAL_CANDIDATE"

    else:
        row["review_status"] = "OVERFLOW_REVIEW"
        row["disposition"] = "UNRESOLVED_OVERFLOW"

    rows.append(row)

# Repo architecture already establishes these as layers
# outside the 269 capability catalogue.

known_layers = {
    "274": (
        "ORCHESTRATION_LAYER",
        "Algorithm OS is the policy-aware decision and orchestration layer "
        "operating across the canonical Operating Systems catalogue.",
    ),
    "275": (
        "ORCHESTRATION_LAYER",
        "Loop OS is the recurring and event-driven execution layer operating "
        "across canonical capabilities.",
    ),
    "276": (
        "GOVERNANCE_LAYER",
        "Pillars OS is the constitutional governance and policy layer above "
        "the Operating Systems catalogue.",
    ),
    "277": (
        "ORCHESTRATION_LAYER",
        "Integrations OS provides controlled connectivity between the "
        "platform and external systems.",
    ),
}

for row in rows:
    seq = row["source_sequence"]

    if seq not in known_layers:
        continue

    disposition, interpretation = known_layers[seq]

    row["disposition"] = disposition
    row["canonical_interpretation"] = interpretation
    row["review_status"] = "STRUCTURALLY_RECONCILED"
    row["roadmap_phase"] = "3"

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

overflow = [row for row in rows if int(row["source_sequence"]) > 269]

lines = [
    "# Phase 2 Overflow Reconciliation",
    "",
    "## Source",
    "",
    "The Imperial Architect source contains 279 preserved raw OS entries "
    "while declaring a canonical Operating Systems range of 001–269.",
    "",
    "No source entry has been deleted or renumbered.",
    "",
    "## Overflow Entries",
    "",
    "| Seq | Name | Disposition | Status |",
    "|---:|---|---|---|",
]

for row in overflow:
    lines.append(
        f"| {row['source_sequence']} | "
        f"{row['name']} | "
        f"{row['disposition']} | "
        f"{row['review_status']} |"
    )

lines += [
    "",
    "## Remaining Decision Set",
    "",
    "The following overflow capabilities require duplicate/alias/merge review:",
    "",
]

for row in overflow:
    if row["review_status"] == "OVERFLOW_REVIEW":
        lines.append(
            f"- {row['source_sequence']} — {row['name']}"
        )

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("OK: Phase 2 review ledger created.")
print(f"Preserved source entries: {len(rows)}")
print("Canonical candidates: 269")
print(f"Overflow entries: {len(overflow)}")
print("Structurally reconciled overflow: 4")
print("Remaining overflow review: 6")
print(f"Ledger: {OUTPUT}")
print(f"Report: {REPORT}")
