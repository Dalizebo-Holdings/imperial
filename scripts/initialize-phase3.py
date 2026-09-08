#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
ORCH = ROOT / "orchestration"
REGISTRY = ORCH / "capability-registry.csv"
CONTRACT = ORCH / "PHASE3_CONTRACT.md"
STATUS = ORCH / "STATUS.md"
DECISION = ORCH / "algorithm-os/DECISION_CONTRACT.md"
ALGO_STATUS = ORCH / "algorithm-os/IMPLEMENTATION_STATUS.md"

REQUIRED_SOURCE_FIELDS = [
    "canonical_id",
    "name",
    "domain",
    "owner",
    "priority",
    "implementation_type",
    "dependencies",
    "security_level",
    "roadmap_phase",
    "disposition",
    "review_status",
]

REGISTRY_FIELDS = [
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

if not REVIEW.exists():
    raise SystemExit(f"ERROR: missing Phase 2 ledger: {REVIEW}")

with REVIEW.open(encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fields = reader.fieldnames or []

missing_fields = [field for field in REQUIRED_SOURCE_FIELDS if field not in fields]
if missing_fields:
    raise SystemExit(
        "ERROR: Phase 2 ledger missing fields: " + ", ".join(missing_fields)
    )

canonical = [
    row for row in rows
    if row["canonical_id"].isdigit()
    and 1 <= int(row["canonical_id"]) <= 269
]

expected_ids = {f"{i:03d}" for i in range(1, 270)}
actual_ids = {row["canonical_id"] for row in canonical}

if len(canonical) != 269:
    raise SystemExit(
        f"ERROR: expected 269 canonical rows, found {len(canonical)}"
    )

if actual_ids != expected_ids:
    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    raise SystemExit(
        f"ERROR: canonical ID mismatch; missing={missing}, extra={extra}"
    )

unclassified = [
    row["canonical_id"]
    for row in canonical
    if row["review_status"] != "CLASSIFIED"
]
if unclassified:
    raise SystemExit(
        "ERROR: Phase 2 is not fully classified: " + ", ".join(unclassified)
    )

ORCH.mkdir(parents=True, exist_ok=True)
(ORCH / "algorithm-os").mkdir(parents=True, exist_ok=True)
(ORCH / "loop-os").mkdir(parents=True, exist_ok=True)
(ORCH / "integrations-os").mkdir(parents=True, exist_ok=True)

with REGISTRY.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=REGISTRY_FIELDS)
    writer.writeheader()

    for row in sorted(canonical, key=lambda item: int(item["canonical_id"])):
        writer.writerow({
            field: row[field].strip()
            for field in REGISTRY_FIELDS
        })

CONTRACT.write_text(
"""# Phase 3 Orchestration Contract

## Scope

Phase 3 turns the canonically classified 269 Operating Systems into a governed orchestration layer.

It consists of:

- Algorithm OS
- Loop OS
- Integrations OS

## Architecture Position

207 Pillars
→ Pillars OS
→ 269 Operating Systems
→ Algorithm OS + Loop OS + Integrations OS
→ Dalizebo Kernel
→ Dalizebo BaaS
→ Dalizebo SaaS

## Shared Execution Path

Request or Event
→ Context Resolution
→ Pillars OS Policy Evaluation
→ Algorithm OS Capability Selection
→ Dependency Resolution
→ Deterministic Execution Plan
→ Kernel Authorization Boundary
→ Loop OS Stateful Execution
→ Integrations OS External Calls
→ Audit Evidence

## Phase 3 Boundary

Phase 3 defines orchestration contracts, registries, deterministic planning,
workflow state, connector behavior, audit semantics, and failure handling.

The Dalizebo Kernel is Phase 4.

Until Phase 4 exists, the Kernel Authorization Boundary is an interface contract,
not permission for uncontrolled production side effects.

## Invariants

1. No capability may bypass Pillars OS policy evaluation.
2. No production action may bypass the Kernel authorization boundary.
3. Every selected capability must resolve to OS-001 through OS-269.
4. Every execution plan must have a correlation identifier.
5. Sensitive operations must produce audit evidence.
6. Retries must be bounded.
7. Jobs must have timeouts.
8. Duplicate execution must be idempotent or safely rejected.
9. External connectors must use explicit authentication and scoped permissions.
10. Connector credentials must never be embedded in plans or audit payloads.
11. Failure defaults to a safe state.
12. Unsafe or retired source interpretations remain unavailable for execution.

## Canonical Registry

`orchestration/capability-registry.csv` is the Phase 3 execution-facing projection
of the Phase 2 canonical catalogue.

Phase 2 remains the source of truth for classification history.

The registry is derived, not independently authored.
""",
encoding="utf-8",
)

DECISION.write_text(
"""# Algorithm OS Decision Contract

## Purpose

Define the deterministic request and response contract used by Algorithm OS
to select and sequence canonical capabilities.

## Decision Request

Required fields:

- decision_request_id
- organization_id
- actor_id
- source
- requested_capabilities
- context_ref
- policy_context
- constraints
- idempotency_key
- correlation_id
- requested_at

Optional fields:

- workspace_id
- project_id
- environment
- priority
- deadline
- cost_budget
- latency_budget
- integration_preferences

## Capability Reference

Every capability reference must use:

`OS-NNN`

where `NNN` is in the canonical range `001` through `269`.

## Decision Response

Required fields:

- decision_id
- decision_request_id
- correlation_id
- policy_result
- selected_capabilities
- dependency_order
- execution_steps
- required_approvals
- required_loop_jobs
- required_integrations
- risk_class
- audit_event
- created_at

## Decision Outcomes

Allowed outcomes:

- APPROVED_FOR_AUTHORIZATION
- REQUIRES_APPROVAL
- REQUIRES_CONTEXT
- POLICY_DENIED
- CAPABILITY_UNAVAILABLE
- DEPENDENCY_UNRESOLVED
- SAFE_FAILURE

`APPROVED_FOR_AUTHORIZATION` does not itself authorize execution.

Kernel authorization remains a separate boundary.

## Determinism

For identical canonical registry version, policy version, material context,
constraints, and request payload, deterministic rules should produce the same
plan where practical.

AI-assisted planning may propose alternatives but must not silently override
policy, dependencies, approvals, or deterministic safety constraints.

## Audit Requirements

Every decision must record:

- decision_id
- correlation_id
- actor
- policy version
- registry version
- selected capabilities
- rejected alternatives where materially relevant
- approval requirements
- risk classification
- final outcome
""",
encoding="utf-8",
)

ALGO_STATUS.write_text(
"""# Algorithm OS Implementation Status

## Phase

Phase 3

## P0 Components

- [x] Capability registry
- [ ] Policy adapter
- [ ] Dependency resolver
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

Implement the P0 policy adapter and dependency resolver against the canonical
269-capability registry.
""",
encoding="utf-8",
)

STATUS.write_text(
"""# Phase 3 Orchestration Status

## Phase

Phase 3 — Algorithm OS + Loop OS + Integrations OS

## Prerequisite

Phase 2 canonical catalogue: 269 / 269 classified

## Current Stage

P0 orchestration foundation initialized.

## Capability Registry

269 / 269 canonical capabilities projected

## Algorithm OS

Capability registry: COMPLETE

Policy adapter: PENDING

Dependency resolver: PENDING

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

Algorithm OS P0 — policy adapter + dependency resolver.

## Governing Rule

Phase 3 may plan and model execution but may not bypass Pillars OS policy
or the Dalizebo Kernel authorization boundary.
""",
encoding="utf-8",
)

print("OK: Phase 3 orchestration foundation initialized.")
print("OK: 269/269 capabilities projected into orchestration registry.")
print("NEXT: Algorithm OS P0 policy adapter + dependency resolver.")
