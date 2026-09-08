#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import csv
import importlib.util
import py_compile

ROOT = Path(__file__).resolve().parent.parent
ALGO = ROOT / "orchestration/algorithm-os"

REGISTRY = ROOT / "orchestration/capability-registry.csv"
POLICY_CSV = ALGO / "policy-requirements.csv"
DEPENDENCY_CSV = ALGO / "dependency-graph.csv"
POLICY_RUNTIME = ALGO / "runtime/policy_adapter.py"
DEPENDENCY_RUNTIME = ALGO / "runtime/dependency_resolver.py"
STATUS = ALGO / "IMPLEMENTATION_STATUS.md"

EXPECTED_IDS = {f"{i:03d}" for i in range(1, 270)}

for path in [
    REGISTRY,
    POLICY_CSV,
    DEPENDENCY_CSV,
    POLICY_RUNTIME,
    DEPENDENCY_RUNTIME,
    STATUS,
]:
    if not path.exists():
        raise SystemExit(f"ERROR: missing artifact: {path}")

py_compile.compile(str(POLICY_RUNTIME), doraise=True)
py_compile.compile(str(DEPENDENCY_RUNTIME), doraise=True)

with REGISTRY.open(encoding="utf-8", newline="") as f:
    registry_rows = list(csv.DictReader(f))

with POLICY_CSV.open(encoding="utf-8", newline="") as f:
    policy_rows = list(csv.DictReader(f))

with DEPENDENCY_CSV.open(encoding="utf-8", newline="") as f:
    dependency_rows = list(csv.DictReader(f))

if len(registry_rows) != 269:
    raise SystemExit("ERROR: registry row count is not 269")

if {row["canonical_id"] for row in registry_rows} != EXPECTED_IDS:
    raise SystemExit("ERROR: registry ID set is incomplete")

if len(policy_rows) != 269:
    raise SystemExit("ERROR: policy profile row count is not 269")

if {row["canonical_id"] for row in policy_rows} != EXPECTED_IDS:
    raise SystemExit("ERROR: policy profile ID set is incomplete")

allowed_eligibility = {
    "ELIGIBLE_FOR_POLICY_EVALUATION",
    "RESEARCH_ONLY",
    "CANONICAL_REFRAME_ONLY",
}

for row in policy_rows:
    if row["policy_route"] != "PILLARS_OS":
        raise SystemExit(
            f"ERROR: OS-{row['canonical_id']} bypasses Pillars OS"
        )
    if row["execution_eligibility"] not in allowed_eligibility:
        raise SystemExit(
            f"ERROR: invalid eligibility for OS-{row['canonical_id']}"
        )
    if not row["required_controls"].strip():
        raise SystemExit(
            f"ERROR: missing controls for OS-{row['canonical_id']}"
        )

allowed_dependency_kinds = {
    "CANONICAL_OS",
    "PLATFORM_PRIMITIVE",
    "EXTERNAL_DEPENDENCY",
}

for row in dependency_rows:
    kind = row["dependency_kind"]
    if kind not in allowed_dependency_kinds:
        raise SystemExit(f"ERROR: invalid dependency kind: {kind}")
    if kind == "CANONICAL_OS" and row["target_id"] not in EXPECTED_IDS:
        raise SystemExit(
            f"ERROR: invalid canonical target OS-{row['target_id']}"
        )


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


policy_adapter = load_module("policy_adapter", POLICY_RUNTIME)
dependency_resolver = load_module(
    "dependency_resolver",
    DEPENDENCY_RUNTIME,
)

profiles = policy_adapter.load_policy_profiles(POLICY_CSV)

request = policy_adapter.build_policy_request(
    profiles,
    capability_id="OS-038",
    decision_request_id="validation-request",
    actor_id="validation-actor",
    organization_id="validation-org",
    correlation_id="validation-correlation",
    requested_operation="evaluate security capability",
    environment="validation",
)

if request["policy_route"] != "PILLARS_OS":
    raise SystemExit("ERROR: policy route is not Pillars OS")

if request["status"] != "PILLARS_OS_EVALUATION_REQUIRED":
    raise SystemExit("ERROR: invalid pre-policy state")

denied = policy_adapter.apply_pillars_decision(
    policy_request=request,
    pillars_decision="DENY",
)

if denied["outcome"] != "POLICY_DENIED":
    raise SystemExit("ERROR: DENY mapping failed")

unknown = policy_adapter.apply_pillars_decision(
    policy_request=request,
    pillars_decision="UNKNOWN",
)

if unknown["outcome"] != "SAFE_FAILURE":
    raise SystemExit("ERROR: malformed decision did not fail safely")

graph = dependency_resolver.load_dependency_graph(DEPENDENCY_CSV)
resolution = dependency_resolver.resolve_dependencies(graph, ["OS-029"])

if "OS-029" not in resolution["ordered_canonical_capabilities"]:
    raise SystemExit("ERROR: dependency resolver omitted OS-029")

status_text = STATUS.read_text(encoding="utf-8")

for phrase in [
    "- [x] Policy adapter",
    "- [x] Dependency resolver",
    "- [ ] Deterministic rule evaluator",
    "- [ ] Execution planner",
]:
    if phrase not in status_text:
        raise SystemExit(f"ERROR: status missing: {phrase}")

print("OK: Policy profiles cover 269/269 capabilities.")
print("OK: All policy routes terminate at Pillars OS.")
print("OK: Dependency graph uses explicit dependency classes.")
print("OK: Canonical dependency targets remain within OS-001..OS-269.")
print("OK: Policy adapter fails closed on malformed decisions.")
print("OK: Dependency resolver runtime passed validation.")
print("STATUS: ALGORITHM OS POLICY + DEPENDENCY P0 COMPLETE")
