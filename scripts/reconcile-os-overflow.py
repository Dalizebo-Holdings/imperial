#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CANONICAL_BOUNDARY.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

D = {
    "270": {
        "disposition": "MERGE",
        "target": "OS-085",
        "domain": "Data & Knowledge",
        "interpretation":
            "Treat file and object storage as a subordinate capability of "
            "Imperial-Library OS, the canonical raw data-bank capability.",
        "notes":
            "Files OS remains preserved as source history but does not consume "
            "a separate canonical OS ID.",
    },

    "271": {
        "disposition": "ALIAS",
        "target": "OS-250",
        "domain": "Data & Knowledge",
        "interpretation":
            "Links OS maps to Network OS for governed relationship and "
            "authority-graph mapping.",
        "notes":
            "Network OS already defines authority-mesh mapping; Links OS is "
            "therefore a source alias rather than an additional canonical OS.",
    },

    "272": {
        "disposition": "MERGE",
        "target": "OS-269",
        "domain": "Data & Knowledge",
        "interpretation":
            "Document storage, metadata, lifecycle, manifests, retention and "
            "retrieval become capabilities within Records OS.",
        "notes":
            "Documents OS is retained as source terminology but merged into "
            "the canonical Records capability.",
    },

    "273": {
        "disposition": "ALIAS",
        "target": "OS-066",
        "domain": "Data & Knowledge",
        "interpretation":
            "Information OS maps to the governed external-information "
            "ingestion capability represented by Information-Vacuum OS.",
        "notes":
            "Both source definitions describe ingestion of external or "
            "regional information signals.",
    },

    "274": {
        "disposition": "ORCHESTRATION_LAYER",
        "target": "",
        "domain": "Automation & Workflow",
        "interpretation":
            "Algorithm OS remains the decision and orchestration layer acting "
            "across the canonical 269 OS catalogue.",
        "notes":
            "It is architecturally outside the canonical capability ID space.",
    },

    "275": {
        "disposition": "ORCHESTRATION_LAYER",
        "target": "",
        "domain": "Automation & Workflow",
        "interpretation":
            "Loop OS remains the recurring and event-driven execution layer "
            "across canonical Operating Systems.",
        "notes":
            "It is architecturally outside the canonical capability ID space.",
    },

    "276": {
        "disposition": "GOVERNANCE_LAYER",
        "target": "",
        "domain": "Governance & Audit",
        "interpretation":
            "Pillars OS remains the constitutional policy and governance "
            "layer enforcing the reconciled 207 Pillars.",
        "notes":
            "Pillars OS sits above the 269 OS catalogue.",
    },

    "277": {
        "disposition": "ORCHESTRATION_LAYER",
        "target": "",
        "domain": "Developer Platform",
        "interpretation":
            "Integrations OS remains the controlled interface between "
            "canonical capabilities and external systems.",
        "notes":
            "It belongs to the orchestration layer rather than the canonical "
            "269 capability ID space.",
    },

    "278": {
        "disposition": "MERGE",
        "target": "OS-068;OS-069",
        "domain": "AI & Intelligence",
        "interpretation":
            "Fallacy detection and syllogistic verification are implemented "
            "through Logic-Chain OS and Reasoning OS.",
        "notes":
            "Logic-Reasoning OS combines capabilities already represented by "
            "OS-068 and OS-069.",
    },

    "279": {
        "disposition": "MERGE",
        "target": "OS-073;OS-260",
        "domain": "Automation & Workflow",
        "interpretation":
            "Final authorized execution combines Tactical-Execution OS with "
            "the Terminal OS interface, subject to governance and audit.",
        "notes":
            "Execution-Terminal OS overlaps the existing execution and "
            "terminal capabilities and therefore receives no new canonical ID.",
    },
}

if not REVIEW.exists():
    raise SystemExit(
        "ERROR: os-review.csv missing. Run scripts/build-os-review.py first."
    )

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

found = set()

for row in rows:

    seq = str(int(row["source_sequence"]))

    if seq not in D:
        continue

    decision = D[seq]

    # Overflow entries never receive a new canonical ID.
    row["canonical_id"] = ""
    row["review_status"] = "RECONCILED_OVERFLOW"
    row["domain"] = decision["domain"]
    row["disposition"] = decision["disposition"]

    # Record canonical target without consuming another ID.
    row["dependencies"] = decision["target"]

    row["canonical_interpretation"] = decision["interpretation"]
    row["decision_notes"] = decision["notes"]

    found.add(seq)

expected = {str(i) for i in range(270, 280)}
missing = expected - found

if missing:
    raise SystemExit(
        "ERROR: Missing overflow entries: "
        + ", ".join(sorted(missing))
    )

tmp = REVIEW.with_suffix(".tmp")

with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(REVIEW)

canonical = [
    r for r in rows
    if 1 <= int(r["source_sequence"]) <= 269
]

overflow = [
    r for r in rows
    if 270 <= int(r["source_sequence"]) <= 279
]

lines = [
    "# Canonical Operating Systems Boundary",
    "",
    "## Decision",
    "",
    "The canonical Imperial Architect Operating Systems ID space is:",
    "",
    "**OS-001 through OS-269**",
    "",
    "The 10 additional source entries remain preserved but do not receive "
    "new canonical IDs.",
    "",
    "## Source Integrity",
    "",
    f"- Preserved raw entries: {len(rows)}",
    f"- Canonical OS IDs: {len(canonical)}",
    f"- Source-preserved overflow entries: {len(overflow)}",
    "",
    "No raw source entry has been deleted or renumbered.",
    "",
    "## Overflow Reconciliation",
    "",
    "| Source | Name | Disposition | Canonical Target |",
    "|---:|---|---|---|",
]

for row in overflow:
    lines.append(
        f"| {row['source_sequence']} | "
        f"{row['name']} | "
        f"{row['disposition']} | "
        f"{row['dependencies'] or 'Architecture layer'} |"
    )

REPORT.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

STATUS.write_text(
    """# Phase 2 Operating Systems Status

## Canonical ID Space

OS-001 → OS-269

## Raw Source Entries Preserved

279

## Overflow Reconciliation

10 / 10 reconciled

## Canonical Classification

0 / 269 complete

## Current Stage

Canonical ID boundary locked.

## Next Work

Classify and reconcile OS-001 through OS-269.

## Governing Rule

Source statements remain preserved.

Canonical implementation decisions are recorded separately from source history.
""",
    encoding="utf-8",
)

print("OK: OS overflow reconciliation complete.")
print("Canonical OS IDs: 269")
print("Overflow reconciled: 10/10")
print("Canonical ID boundary: LOCKED")
print(f"Report: {REPORT}")
