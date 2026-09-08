#!/usr/bin/env python3

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REGISTRY = ROOT / "orchestration/capability-registry.csv"
CONTRACT = ROOT / "orchestration/PHASE3_CONTRACT.md"
STATUS = ROOT / "orchestration/STATUS.md"
ALGORITHM = ROOT / "orchestration/algorithm-os/README.md"
DECISION = ROOT / "orchestration/algorithm-os/DECISION_CONTRACT.md"
LOOP = ROOT / "orchestration/loop-os/EXECUTION_MODEL.md"
INTEGRATION = ROOT / "orchestration/integrations-os/CONNECTOR_STANDARD.md"

required_files = [
    REVIEW,
    REGISTRY,
    CONTRACT,
    STATUS,
    ALGORITHM,
    DECISION,
    LOOP,
    INTEGRATION,
]

for path in required_files:
    if not path.exists():
        raise SystemExit(f"ERROR: missing required Phase 3 file: {path}")

with REVIEW.open(encoding="utf-8", newline="") as f:
    phase2_rows = [
        row for row in csv.DictReader(f)
        if row["canonical_id"].isdigit()
        and 1 <= int(row["canonical_id"]) <= 269
    ]

with REGISTRY.open(encoding="utf-8", newline="") as f:
    registry_rows = list(csv.DictReader(f))

if len(phase2_rows) != 269:
    raise SystemExit(
        f"ERROR: expected 269 Phase 2 rows, found {len(phase2_rows)}"
    )

if len(registry_rows) != 269:
    raise SystemExit(
        f"ERROR: expected 269 registry rows, found {len(registry_rows)}"
    )

phase2 = {row["canonical_id"]: row for row in phase2_rows}
registry = {row["canonical_id"]: row for row in registry_rows}

expected = {f"{i:03d}" for i in range(1, 270)}

if set(phase2) != expected:
    raise SystemExit("ERROR: Phase 2 canonical ID set is incomplete")

if set(registry) != expected:
    raise SystemExit("ERROR: Phase 3 capability registry ID set is incomplete")

for cid in sorted(expected):
    source = phase2[cid]
    target = registry[cid]

    if source["review_status"] != "CLASSIFIED":
        raise SystemExit(f"ERROR: OS-{cid} is not classified")

    if source["name"] != target["name"]:
        raise SystemExit(f"ERROR: registry name mismatch for OS-{cid}")

    for field in [
        "domain",
        "owner",
        "priority",
        "implementation_type",
        "security_level",
        "disposition",
        "roadmap_phase",
    ]:
        if source[field].strip() != target[field].strip():
            raise SystemExit(
                f"ERROR: registry mismatch for OS-{cid} field {field}"
            )

contract = CONTRACT.read_text(encoding="utf-8")
decision = DECISION.read_text(encoding="utf-8")
loop = LOOP.read_text(encoding="utf-8")
integration = INTEGRATION.read_text(encoding="utf-8")

for phrase in [
    "Pillars OS Policy Evaluation",
    "Kernel Authorization Boundary",
    "bounded",
    "idempotent",
]:
    if phrase not in contract:
        raise SystemExit(
            f"ERROR: Phase 3 contract missing invariant: {phrase}"
        )

for phrase in [
    "APPROVED_FOR_AUTHORIZATION",
    "POLICY_DENIED",
    "SAFE_FAILURE",
    "correlation_id",
]:
    if phrase not in decision:
        raise SystemExit(
            f"ERROR: decision contract missing: {phrase}"
        )

for phrase in [
    "idempotency_key",
    "max_attempts",
    "DEAD_LETTERED",
]:
    if phrase not in loop:
        raise SystemExit(
            f"ERROR: Loop OS execution model missing: {phrase}"
        )

for phrase in [
    "Permission scopes",
    "Circuit breaker",
    "Secret storage",
]:
    if phrase not in integration:
        raise SystemExit(
            f"ERROR: Integrations OS standard missing: {phrase}"
        )

print("OK: Phase 2 prerequisite is 269/269.")
print("OK: Phase 3 capability registry is 269/269 and source-aligned.")
print("OK: Algorithm OS decision boundary is defined.")
print("OK: Loop OS execution safety contract is present.")
print("OK: Integrations OS connector safety contract is present.")
print("STATUS: PHASE 3 FOUNDATION READY")
