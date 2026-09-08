#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import py_compile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
ALGO = ROOT / "orchestration/algorithm-os"
RUNTIME = ALGO / "runtime"

MODULES = {
    "policy": RUNTIME / "policy_adapter.py",
    "dependency": RUNTIME / "dependency_resolver.py",
    "rules": RUNTIME / "rule_evaluator.py",
    "planner": RUNTIME / "execution_planner.py",
    "audit": RUNTIME / "audit_adapter.py",
}

for path in MODULES.values():
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


audit = load_module("audit_adapter", MODULES["audit"])

event = {
    "event_type": "algorithm_os.decision_planned",
    "decision_id": "decision_validation",
    "decision_request_id": "request_validation",
    "correlation_id": "correlation_validation",
    "actor_id": "actor_validation",
    "organization_id": "organization_validation",
    "registry_version": "phase3-capability-registry-v1",
    "policy_version": "pillars-os-v1",
    "risk_class": "HIGH",
    "outcome": "REQUIRES_APPROVAL",
    "metadata": {
        "api_key": "should-not-persist",
        "nested": {
            "authorization": "Bearer should-not-persist",
            "safe": "retained",
        },
    },
}

record = audit.build_record(
    event=event,
    recorded_at="2026-01-01T00:00:00+00:00",
)

if record["event"]["metadata"]["api_key"] != "[REDACTED]":
    raise SystemExit("ERROR: api_key was not redacted")

if (
    record["event"]["metadata"]["nested"]["authorization"]
    != "[REDACTED]"
):
    raise SystemExit("ERROR: authorization was not redacted")

if record["event"]["metadata"]["nested"]["safe"] != "retained":
    raise SystemExit("ERROR: safe audit metadata was incorrectly removed")

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "algorithm-audit.jsonl"

    first = audit.append_record(
        path,
        event=event,
        recorded_at="2026-01-01T00:00:00+00:00",
    )

    second_event = dict(event)
    second_event["decision_id"] = "decision_validation_2"
    second_event["correlation_id"] = "correlation_validation_2"

    second = audit.append_record(
        path,
        event=second_event,
        recorded_at="2026-01-01T00:00:01+00:00",
    )

    if second["previous_hash"] != first["record_hash"]:
        raise SystemExit("ERROR: audit chain link is invalid")

    verification = audit.verify_file(path)

    if not verification["valid"]:
        raise SystemExit(
            "ERROR: valid audit file failed verification: "
            + str(verification)
        )

    records = audit.read_records(path)
    tampered = deepcopy(records)
    tampered[0]["event"]["outcome"] = "APPROVED_FOR_AUTHORIZATION"

    tamper_check = audit.verify_records(tampered)

    if tamper_check["valid"]:
        raise SystemExit("ERROR: tampered audit record was accepted")

status = (ALGO / "IMPLEMENTATION_STATUS.md").read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Capability registry",
    "- [x] Policy adapter",
    "- [x] Dependency resolver",
    "- [x] Deterministic rule evaluator",
    "- [x] Execution planner",
    "- [x] Audit adapter",
    "P0 Status",
    "COMPLETE",
]:
    if phrase not in status:
        raise SystemExit(f"ERROR: Algorithm OS P0 status missing: {phrase}")

print("OK: Audit Adapter recursively redacts sensitive values.")
print("OK: Audit records are deterministically hashed.")
print("OK: Append-only hash chaining passed.")
print("OK: Tamper detection passed.")
print("OK: Algorithm OS P0 component checklist is complete.")
print("STATUS: ALGORITHM OS P0 COMPLETE")
