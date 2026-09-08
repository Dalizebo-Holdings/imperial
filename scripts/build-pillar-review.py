#!/usr/bin/env python3

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "constitution" / "pillar-registry.csv"
OUTPUT = ROOT / "constitution" / "reconciliation" / "review" / "pillar-review.csv"

if not SOURCE.exists():
    raise SystemExit("ERROR: constitution/pillar-registry.csv does not exist.")

unsafe_patterns = [
    r"\bsabotage\b",
    r"\bdeception\b",
    r"\bdecoy\b",
    r"\bpropaganda\b",
    r"\bmanipulat",
    r"\bmind-virus",
    r"\bregulatory capture\b",
    r"\bneutralize regulator",
    r"\bevade\b",
    r"\bbypass law",
    r"\bstatus-threat",
    r"\blogical domination",
    r"\bcoerc",
]

rd_patterns = [
    r"\blunar\b",
    r"\boff-planet\b",
    r"\bpost-human\b",
    r"\bdeep-sea\b",
    r"\bdna storage\b",
    r"\bquantum\b",
]

technical_patterns = [
    r"\bencryption\b",
    r"\bbackup",
    r"\bzero-trust\b",
    r"\bsecurity\b",
    r"\bapi\b",
    r"\baudit\b",
    r"\bkernel\b",
    r"\bnetwork\b",
    r"\bsoftware\b",
    r"\bhardware\b",
    r"\bautomation\b",
    r"\bdata\b",
]

policy_patterns = [
    r"\bgovernance\b",
    r"\bcompliance\b",
    r"\bsuccession\b",
    r"\bownership\b",
    r"\bcontract\b",
    r"\ballocation\b",
    r"\bcapital\b",
]

def matches(patterns, text):
    return any(re.search(p, text, re.I) for p in patterns)

def suggest(text):
    if matches(unsafe_patterns, text):
        return "REFRAME"
    if matches(rd_patterns, text):
        return "R&D"
    if matches(technical_patterns, text):
        return "TECHNICAL"
    if matches(policy_patterns, text):
        return "POLICY"
    return "KEEP"

with SOURCE.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 207:
    raise SystemExit(
        f"ERROR: Expected 207 Pillars in registry, found {len(rows)}."
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "pillar_id",
        "name",
        "source_statement",
        "suggested_classification",
        "approved_classification",
        "implementation_domain",
        "safety_action",
        "owner",
        "canonical_interpretation",
        "decision_notes",
    ])

    for row in rows:
        statement = row["source_statement"].strip()
        suggestion = suggest(statement)

        writer.writerow([
            row["pillar_id"],
            row["name"],
            statement,
            suggestion,
            "UNREVIEWED",
            "TBD",
            "MANUAL_REVIEW" if suggestion == "REFRAME" else "NONE",
            "TBD",
            "",
            "",
        ])

print(f"OK: Generated {len(rows)} Pillar review records.")
print(f"Output: {OUTPUT}")
