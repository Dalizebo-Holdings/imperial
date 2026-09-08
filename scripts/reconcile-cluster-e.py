#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "constitution/reconciliation/review/pillar-review.csv"
REPORT = ROOT / "constitution/reconciliation/reports/CLUSTER_E.md"
STATUS = ROOT / "constitution/reconciliation/reports/STATUS.md"
POLICY = ROOT / "constitution/reconciliation/policy/SINGULARITY_GOVERNANCE_POLICY.md"

DECISIONS = {
    "201": (
        "TECHNICAL",
        "Institutional Continuity / Kernel",
        "Platform Architecture",
        "NONE",
        "Design the Kernel, governance records, source control, backups, runbooks, reproducible deployments, delegated authority, and succession processes so critical Dalizebo logic and operations survive the unavailability of any individual.",
        "Strategic persistence becomes institutional continuity rather than dependence on a biological node.",
    ),

    "202": (
        "REFRAME",
        "Automation / Growth Governance",
        "Automation Governance",
        "CANONICAL_REFRAME",
        "Automate repeatable growth and operating workflows where evidence supports automation while enforcing bounded autonomy, authorization, observability, rate limits, rollback, stop controls, and accountable human oversight.",
        "Automation-by-default is retained; unstoppable autonomous growth is not.",
    ),

    "203": (
        "R&D",
        "Frontier Resilience / Archival",
        "R&D Governance",
        "RESEARCH_BOUNDARY",
        "Research off-planet archival only as long-horizon resilience work after geographically independent terrestrial backups, tested restores, durable archival formats, and disaster-recovery controls are mature.",
        "Lunar archival remains Frontier R&D and is not a production dependency.",
    ),

    "204": (
        "REFRAME",
        "Legal / Treasury / Platform Sovereignty",
        "Legal & Compliance",
        "CANONICAL_REFRAME",
        "Reduce avoidable dependency on any single currency, provider, jurisdiction, or infrastructure vendor through portability, diversification, open standards, exit plans, and lawful alternatives while remaining compliant with applicable law and regulation.",
        "Operational sovereignty is retained; abandoning applicable law for growth is prohibited.",
    ),

    "205": (
        "REFRAME",
        "Autonomous Systems / Governance",
        "AI & Automation Governance",
        "CANONICAL_REFRAME",
        "Design systems that can process and coordinate workloads beyond manual human scale while preserving policy boundaries, auditability, observability, approval requirements, emergency intervention, rollback, and accountable human governance.",
        "Machine-scale execution may exceed human throughput but must never exceed governance and control.",
    ),

    "206": (
        "REFRAME",
        "Platform Resilience / Supply Chain",
        "Platform Architecture",
        "CANONICAL_REFRAME",
        "Minimize critical third-party concentration through provider abstraction, interoperability, self-hosting where justified, multi-provider strategies, owned capabilities, redundancy, export paths, and tested migration procedures.",
        "The objective is controlled dependency and portability rather than absolute zero reliance on intermediaries.",
    ),

    "207": (
        "REFRAME",
        "Legal / Contracts / Automation",
        "Legal Governance",
        "CANONICAL_REFRAME",
        "Automate breach detection, evidence preservation, notices, escalation, contractual remedies, mediation, arbitration, recovery workflows, and other lawful dispute-resolution processes with proportionality, review, and auditability.",
        "Lawful automated remedies are permitted; retaliatory or unlawful counter-strikes are not.",
    ),
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid pillar-review.csv")

expected = {f"{i:03d}" for i in range(201, 208)}
found = set()

for row in rows:
    pid = row["pillar_id"].zfill(3)

    if pid not in DECISIONS:
        continue

    (
        classification,
        domain,
        owner,
        safety,
        canonical,
        notes,
    ) = DECISIONS[pid]

    row["approved_classification"] = classification
    row["implementation_domain"] = domain
    row["safety_action"] = safety
    row["owner"] = owner
    row["canonical_interpretation"] = canonical
    row["decision_notes"] = notes

    found.add(pid)

missing = expected - found

if missing:
    raise SystemExit(
        "ERROR: Missing Cluster E Pillars: "
        + ", ".join(sorted(missing))
    )

tmp = REVIEW.with_suffix(".tmp")

with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(REVIEW)

cluster = [
    row for row in rows
    if 201 <= int(row["pillar_id"]) <= 207
]

counts = Counter(
    row["approved_classification"]
    for row in cluster
)

lines = [
    "# Cluster E Constitutional Reconciliation",
    "",
    "## Source",
    "",
    "Cluster E: The Singularity Laws (201–207).",
    "",
    "Original source statements remain unchanged.",
    "",
    "## Classification Summary",
    "",
]

for classification in [
    "KEEP",
    "POLICY",
    "TECHNICAL",
    "REFRAME",
    "R&D",
    "RETIRE",
]:
    lines.append(
        f"- {classification}: {counts.get(classification, 0)}"
    )

lines.extend(["", "## Decisions", ""])

for row in cluster:
    lines.extend([
        f"### Pillar {row['pillar_id']} — {row['name']}",
        "",
        f"**Classification:** {row['approved_classification']}",
        "",
        f"**Domain:** {row['implementation_domain']}",
        "",
        f"**Owner:** {row['owner']}",
        "",
        "**Original Source Statement**",
        "",
        f"> {row['source_statement']}",
        "",
        "**Canonical Interpretation**",
        "",
        row["canonical_interpretation"],
        "",
        "**Decision**",
        "",
        row["decision_notes"],
        "",
        "---",
        "",
    ])

REPORT.write_text("\n".join(lines), encoding="utf-8")

remaining = sum(
    row["approved_classification"] == "UNREVIEWED"
    for row in rows
)

STATUS.write_text(
    f"""# Pillar Reconciliation Status

## Total Pillars

207

## Required Final States

KEEP / POLICY / TECHNICAL / R&D / REFRAME / RETIRE

## Current Stage

{"Constitutionally reconciled." if remaining == 0 else "Reconciliation in progress."}

## Remaining Unreviewed

{remaining}

## Source Integrity

Original statements remain authoritative historical source material.

## Completed Review Order

Cluster A → Cluster B → Cluster C → Cluster D → Cluster E

## Next Phase

{"Phase 2 — 269 Operating Systems Catalogue." if remaining == 0 else "Complete remaining Pillar reconciliation."}
""",
    encoding="utf-8",
)

POLICY.write_text(
"""# Singularity & Continuity Governance Policy

## Scope

This policy implements the approved canonical interpretations of Pillars 201–207.

## Institutional Continuity

Dalizebo systems must not depend on the continuous availability of a single individual.

Critical knowledge, authority, infrastructure, source code, credentials, recovery procedures, and operating processes require governed continuity mechanisms.

## Bounded Automation

Automation may operate beyond manual human throughput only when it remains:

- Authorized
- Observable
- Auditable
- Rate-limited where appropriate
- Reversible where practical
- Subject to policy controls
- Subject to emergency intervention
- Owned by an accountable authority

Unbounded or deliberately unstoppable automation is prohibited.

## Infrastructure Sovereignty

Dalizebo should reduce critical concentration risk through:

- Open standards
- Provider abstraction
- Portability
- Data export
- Multiple providers
- Self-hosting where justified
- Tested migration procedures
- Redundant infrastructure
- Documented exit plans

Sovereignty does not override applicable law or regulation.

## Frontier Archival

Off-planet or unconventional archival systems remain Frontier R&D.

Production resilience must first rely on tested terrestrial backups, geographic redundancy, restoration exercises, and durable archival formats.

## Contract Enforcement

Automated contract systems may support:

- Breach detection
- Evidence preservation
- Notice generation
- Escalation
- Mediation workflows
- Arbitration workflows
- Lawful remedies
- Recovery processes
- Audit records

Retaliatory, destructive, coercive, or unlawful counter-strikes are prohibited.

## Governing Principle

Machine-scale execution may exceed human throughput.

It must never exceed constitutional governance, legal obligations, safety boundaries, authorization, observability, or accountability.
""",
    encoding="utf-8",
)

print("OK: Cluster E Pillars 201–207 reconciled.")
print()

for classification in [
    "KEEP",
    "POLICY",
    "TECHNICAL",
    "REFRAME",
    "R&D",
    "RETIRE",
]:
    print(
        f"{classification}: "
        f"{counts.get(classification, 0)}"
    )

print()
print(f"Remaining unreviewed Pillars: {remaining}")
print(f"Report: {REPORT}")
print(f"Policy: {POLICY}")
