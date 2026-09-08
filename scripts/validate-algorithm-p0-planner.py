#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile

ROOT = Path(__file__).resolve().parent.parent
ALGO = ROOT / "orchestration/algorithm-os"
RUNTIME = ALGO / "runtime"

paths = {
    "policy": RUNTIME / "policy_adapter.py",
    "dependency": RUNTIME / "dependency_resolver.py",
    "rules": RUNTIME / "rule_evaluator.py",
    "planner": RUNTIME / "execution_planner.py",
}

for path in paths.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing runtime module: {path}")
    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


policy = load_module("policy_adapter", paths["policy"])
dependency = load_module("dependency_resolver", paths["dependency"])
rules = load_module("rule_evaluator", paths["rules"])
planner = load_module("execution_planner", paths["planner"])

profiles = policy.load_policy_profiles(
    ALGO / "policy-requirements.csv"
)
graph = dependency.load_dependency_graph(
    ALGO / "dependency-graph.csv"
)

decision_request = {
    "decision_request_id": "validation-plan-001",
    "organization_id": "validation-org",
    "actor_id": "validation-actor",
    "source": "validation",
    "requested_capabilities": ["OS-029"],
    "context_ref": "validation-context",
    "policy_context": {},
    "constraints": {},
    "idempotency_key": "validation-idempotency",
    "correlation_id": "validation-correlation",
    "requested_at": "2026-01-01T00:00:00+00:00",
    "environment": "validation",
}

policy_request = policy.build_policy_request(
    profiles,
    capability_id="OS-029",
    decision_request_id=decision_request["decision_request_id"],
    actor_id=decision_request["actor_id"],
    organization_id=decision_request["organization_id"],
    correlation_id=decision_request["correlation_id"],
    requested_operation="plan deployment",
    environment="validation",
)

policy_result = policy.apply_pillars_decision(
    policy_request=policy_request,
    pillars_decision="ALLOW",
)

resolution = dependency.resolve_dependencies(
    graph,
    decision_request["requested_capabilities"],
)

cycle_evaluation = rules.evaluate(
    requested_capabilities=decision_request["requested_capabilities"],
    policy_results=[policy_result],
    dependency_resolution=resolution,
    policy_profiles=profiles,
    constraints=decision_request["constraints"],
)

if not resolution.get("cycles"):
    raise SystemExit(
        "ERROR: expected canonical dependency cycle was not detected"
    )

if cycle_evaluation["outcome"] != "DEPENDENCY_UNRESOLVED":
    raise SystemExit(
        "ERROR: canonical dependency cycle was not blocked: "
        + cycle_evaluation["outcome"]
    )

acyclic_resolution = {
    "requested_capabilities": ["OS-029"],
    "ordered_canonical_capabilities": ["OS-029"],
    "platform_prerequisites": {},
    "external_prerequisites": {},
    "cycles": [],
}

evaluation = rules.evaluate(
    requested_capabilities=decision_request["requested_capabilities"],
    policy_results=[policy_result],
    dependency_resolution=acyclic_resolution,
    policy_profiles=profiles,
    constraints=decision_request["constraints"],
)

if evaluation["outcome"] not in {
    "APPROVED_FOR_AUTHORIZATION",
    "REQUIRES_APPROVAL",
}:
    raise SystemExit(
        "ERROR: acyclic planner fixture did not reach authorization stage: "
        + evaluation["outcome"]
    )

plan1 = planner.build_execution_plan(
    decision_request=decision_request,
    rule_evaluation=evaluation,
    dependency_resolution=acyclic_resolution,
    policy_results=[policy_result],
    created_at="2026-01-01T00:00:00+00:00",
)

plan2 = planner.build_execution_plan(
    decision_request=decision_request,
    rule_evaluation=evaluation,
    dependency_resolution=acyclic_resolution,
    policy_results=[policy_result],
    created_at="2026-01-01T00:00:00+00:00",
)

if plan1["decision_id"] != plan2["decision_id"]:
    raise SystemExit("ERROR: planner decision_id is not deterministic")

if plan1["kernel_authorization"] != "REQUIRED":
    raise SystemExit("ERROR: planner bypassed Kernel authorization")

if "OS-029" not in plan1["dependency_order"]:
    raise SystemExit("ERROR: planner omitted requested capability")

if not plan1["execution_steps"]:
    raise SystemExit("ERROR: planner generated no steps")

for step in plan1["execution_steps"]:
    if step["state"] not in {
        "READY_FOR_KERNEL_AUTHORIZATION",
        "BLOCKED",
    }:
        raise SystemExit(
            "ERROR: planner emitted an executable side-effect state"
        )

denied_result = policy.apply_pillars_decision(
    policy_request=policy_request,
    pillars_decision="DENY",
)

denied_evaluation = rules.evaluate(
    requested_capabilities=decision_request["requested_capabilities"],
    policy_results=[denied_result],
    dependency_resolution=resolution,
    policy_profiles=profiles,
    constraints={},
)

if denied_evaluation["outcome"] != "POLICY_DENIED":
    raise SystemExit("ERROR: Pillars OS denial was not preserved")

denied_plan = planner.build_execution_plan(
    decision_request=decision_request,
    rule_evaluation=denied_evaluation,
    dependency_resolution=resolution,
    policy_results=[denied_result],
    created_at="2026-01-01T00:00:00+00:00",
)

if any(
    step["state"] != "BLOCKED"
    for step in denied_plan["execution_steps"]
):
    raise SystemExit("ERROR: denied plan contains a ready step")

missing_context_eval = rules.evaluate(
    requested_capabilities=["OS-029"],
    policy_results=[],
    dependency_resolution=resolution,
    policy_profiles=profiles,
    constraints={},
)

if missing_context_eval["outcome"] != "REQUIRES_CONTEXT":
    raise SystemExit("ERROR: missing policy result did not require context")

status = (ALGO / "IMPLEMENTATION_STATUS.md").read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Deterministic rule evaluator",
    "- [x] Execution planner",
    "- [ ] Audit adapter",
]:
    if phrase not in status:
        raise SystemExit(f"ERROR: status missing: {phrase}")

print("OK: Deterministic rule evaluation passed.")
print("OK: Pillars OS denial remains blocking.")
print("OK: Missing policy context fails closed.")
print("OK: Execution plan decision IDs are deterministic.")
print("OK: Kernel authorization remains REQUIRED.")
print("OK: Planner emits no side-effect execution state.")
print("STATUS: ALGORITHM OS DETERMINISTIC PLANNING P0 COMPLETE")
