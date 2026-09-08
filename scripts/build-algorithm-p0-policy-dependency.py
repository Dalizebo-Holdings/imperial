#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "orchestration/capability-registry.csv"
ALGO = ROOT / "orchestration/algorithm-os"

POLICY_CSV = ALGO / "policy-requirements.csv"
DEPENDENCY_CSV = ALGO / "dependency-graph.csv"
ALGO_STATUS = ALGO / "IMPLEMENTATION_STATUS.md"
ORCH_STATUS = ROOT / "orchestration/STATUS.md"

EXPECTED_IDS = {f"{i:03d}" for i in range(1, 270)}

REQUIRED_FIELDS = [
    "canonical_id",
    "name",
    "domain",
    "owner",
    "priority",
    "implementation_type",
    "security_level",
    "dependencies",
    "disposition",
    "roadmap_phase",
]


def normalize(value: str) -> str:
    value = value.strip().lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if value.endswith(" os"):
        value = value[:-3].strip()
    return value


def classify_unresolved(raw: str) -> str:
    n = normalize(raw)

    external_markers = (
        "provider",
        "market data",
        "government",
        "external",
        "bank",
        "satellite",
    )

    if any(marker in n for marker in external_markers):
        return "EXTERNAL_DEPENDENCY"

    return "PLATFORM_PRIMITIVE"


if not REGISTRY.exists():
    raise SystemExit(f"ERROR: missing capability registry: {REGISTRY}")

with REGISTRY.open(encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames or []
    rows = list(reader)

missing = [field for field in REQUIRED_FIELDS if field not in fields]
if missing:
    raise SystemExit(
        "ERROR: capability registry missing fields: " + ", ".join(missing)
    )

ids = {row["canonical_id"] for row in rows}
if len(rows) != 269 or ids != EXPECTED_IDS:
    raise SystemExit(
        f"ERROR: expected OS-001..OS-269, found {len(rows)} rows"
    )

name_index: dict[str, str] = {}
canonical_names: dict[str, str] = {}

for row in rows:
    cid = row["canonical_id"]
    name = row["name"].strip()
    canonical_names[cid] = name

    aliases = {
        normalize(name),
        normalize(name.replace("-", " ")),
        normalize(f"OS {cid}"),
        normalize(cid),
    }

    if name.lower().endswith(" os"):
        aliases.add(normalize(name[:-3]))

    for alias in aliases:
        if alias:
            name_index.setdefault(alias, cid)

policy_fields = [
    "canonical_id",
    "name",
    "security_level",
    "implementation_type",
    "disposition",
    "execution_eligibility",
    "policy_route",
    "approval_mode",
    "required_controls",
]

with POLICY_CSV.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=policy_fields)
    writer.writeheader()

    for row in sorted(rows, key=lambda item: int(item["canonical_id"])):
        security = row["security_level"].strip().upper()
        impl_type = row["implementation_type"].strip().upper()
        disposition = row["disposition"].strip().upper()
        priority = row["priority"].strip().upper()
        domain = row["domain"].strip()

        if disposition == "R&D" or impl_type == "R&D" or priority == "R&D":
            eligibility = "RESEARCH_ONLY"
        elif impl_type == "RETIRED_REFRAMED":
            eligibility = "CANONICAL_REFRAME_ONLY"
        else:
            eligibility = "ELIGIBLE_FOR_POLICY_EVALUATION"

        if security == "CRITICAL":
            approval = "EXPLICIT_APPROVAL_REQUIRED"
        elif security == "HIGH":
            approval = "POLICY_DEPENDENT"
        else:
            approval = "STANDARD"

        controls = [
            "pillar_policy",
            "actor_authorization",
            "tenant_scope",
            "audit",
        ]

        if security == "CRITICAL":
            controls.append("explicit_approval")
        if impl_type == "AUTOMATION":
            controls.append("bounded_automation")
        if impl_type == "INTEGRATION":
            controls.append("connector_scope")
        if eligibility == "RESEARCH_ONLY":
            controls.append("research_boundary")
        if eligibility == "CANONICAL_REFRAME_ONLY":
            controls.append("canonical_reframe_only")
        if domain in {
            "AI & Intelligence",
            "Data & Knowledge",
            "Marketing & Customer",
        }:
            controls.append("data_governance")

        writer.writerow({
            "canonical_id": row["canonical_id"],
            "name": row["name"],
            "security_level": security,
            "implementation_type": impl_type,
            "disposition": disposition,
            "execution_eligibility": eligibility,
            "policy_route": "PILLARS_OS",
            "approval_mode": approval,
            "required_controls": ";".join(controls),
        })

dependency_fields = [
    "source_id",
    "source_name",
    "dependency_raw",
    "dependency_normalized",
    "dependency_kind",
    "target_id",
    "target_name",
]

with DEPENDENCY_CSV.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=dependency_fields)
    writer.writeheader()

    for row in sorted(rows, key=lambda item: int(item["canonical_id"])):
        dependencies = [
            item.strip()
            for item in row["dependencies"].split(";")
            if item.strip()
        ]

        for dependency in dependencies:
            normalized = normalize(dependency)
            target_id = name_index.get(normalized, "")

            if target_id:
                kind = "CANONICAL_OS"
                target_name = canonical_names[target_id]
            else:
                kind = classify_unresolved(dependency)
                target_name = ""

            writer.writerow({
                "source_id": row["canonical_id"],
                "source_name": row["name"],
                "dependency_raw": dependency,
                "dependency_normalized": normalized,
                "dependency_kind": kind,
                "target_id": target_id,
                "target_name": target_name,
            })

ALGO_STATUS.write_text(
"""# Algorithm OS Implementation Status

## Phase

Phase 3

## P0 Components

- [x] Capability registry
- [x] Policy adapter
- [x] Dependency resolver
- [ ] Deterministic rule evaluator
- [ ] Execution planner
- [ ] Audit adapter

## P1 Components

- [ ] Dynamic routing
- [ ] Priority management
- [ ] Cost-aware execution
- [ ] Policy simulation

## P2 Components

- [ ] AI-assisted planning
- [ ] Optimization engine
- [ ] Predictive orchestration

## Current Next Work

Implement the P0 deterministic rule evaluator and execution planner using the policy adapter and dependency resolver as mandatory planning gates.
""",
encoding="utf-8",
)

ORCH_STATUS.write_text(
"""# Phase 3 Orchestration Status

## Phase

Phase 3 — Algorithm OS + Loop OS + Integrations OS

## Prerequisite

Phase 2 canonical catalogue: 269 / 269 classified

## Current Stage

Algorithm OS P0 policy and dependency layer complete.

## Capability Registry

269 / 269 canonical capabilities projected

## Algorithm OS

Capability registry: COMPLETE

Policy adapter: COMPLETE

Dependency resolver: COMPLETE

Deterministic rule evaluator: PENDING

Execution planner: PENDING

Audit adapter: PENDING

## Loop OS

Execution model: DEFINED

Runtime schema and state-machine implementation: PENDING

## Integrations OS

Connector standard: DEFINED

Connector registry and runtime contracts: PENDING

## Next Work

Algorithm OS P0 — deterministic rule evaluator + execution planner.

## Governing Rule

Every plan must pass Pillars OS policy evaluation and the Dalizebo Kernel authorization boundary before production side effects may occur.
""",
encoding="utf-8",
)

print("OK: Policy requirements generated for 269/269 capabilities.")
print("OK: Dependency graph generated.")
print("OK: Policy Adapter marked complete.")
print("OK: Dependency Resolver marked complete.")
print("NEXT: Deterministic rule evaluator + execution planner.")
