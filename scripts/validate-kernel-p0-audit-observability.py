#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import py_compile
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

MODULES = {
    "kernel_audit": KERNEL / "audit/persistence.py",
    "kernel_errors": KERNEL / "errors/runtime.py",
    "kernel_logging": KERNEL / "observability/logging.py",
    "kernel_metrics": KERNEL / "observability/metrics.py",
    "kernel_health": KERNEL / "observability/health.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel observability runtime file: {path}"
        )
    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERROR: unable to load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module("kernel_audit", MODULES["kernel_audit"])
errors = load_module("kernel_errors", MODULES["kernel_errors"])
logging = load_module("kernel_logging", MODULES["kernel_logging"])
metrics = load_module("kernel_metrics", MODULES["kernel_metrics"])
health = load_module("kernel_health", MODULES["kernel_health"])

event_one = audit.AuditEvent(
    audit_id="audit_validation_001",
    organization_id="org-validation",
    actor_type="HUMAN_USER",
    actor_id="actor-validation",
    action="order.create",
    resource_type="order",
    resource_id="ord_validation",
    timestamp="2026-01-01T00:00:00+00:00",
    correlation_id="corr-validation",
    metadata={
        "status": "CREATED",
        "api_key": "must-not-persist",
        "nested": {
            "authorization": "Bearer hidden",
            "safe": "retained",
        },
    },
)

event_two = audit.AuditEvent(
    audit_id="audit_validation_002",
    organization_id="org-validation",
    actor_type="HUMAN_USER",
    actor_id="actor-validation",
    action="order.confirm",
    resource_type="order",
    resource_id="ord_validation",
    timestamp="2026-01-01T00:00:01+00:00",
    correlation_id="corr-validation",
    metadata={"status": "CONFIRMED"},
)

with tempfile.TemporaryDirectory() as tmp:
    ledger = Path(tmp) / "kernel-audit.jsonl"

    first = audit.append_event(ledger, event_one)
    second = audit.append_event(ledger, event_two)

    if first["event"]["metadata"]["api_key"] != "[REDACTED]":
        raise SystemExit(
            "ERROR: audit api_key was not redacted"
        )

    if (
        first["event"]["metadata"]["nested"]["authorization"]
        != "[REDACTED]"
    ):
        raise SystemExit(
            "ERROR: nested audit authorization was not redacted"
        )

    if (
        second["previous_hash"]
        != first["record_hash"]
    ):
        raise SystemExit(
            "ERROR: audit hash chain link failed"
        )

    valid = audit.verify_file(ledger)

    if not valid["valid"]:
        raise SystemExit(
            "ERROR: valid Kernel audit ledger failed verification"
        )

    tampered = deepcopy(audit.read_records(ledger))
    tampered[0]["event"]["action"] = "tampered.action"

    if audit.verify_records(tampered)["valid"]:
        raise SystemExit(
            "ERROR: tampered Kernel audit ledger was accepted"
        )

safe_error = errors.create_error(
    code="KERNEL_AUTHORIZATION_DENIED",
    category="AUTHORIZATION",
    message="Operation is not authorized",
    retryable=False,
    correlation_id="corr-validation",
    details={
        "policy": "DENY",
        "api_key": "must-not-expose",
    },
)

safe_dict = safe_error.to_dict()

if safe_dict["details"]["api_key"] != "[REDACTED]":
    raise SystemExit(
        "ERROR: error details did not redact sensitive value"
    )

normalized = errors.normalize_exception(
    exc=RuntimeError("internal secret diagnostic"),
    correlation_id="corr-validation",
)

if "internal secret diagnostic" in normalized.message:
    raise SystemExit(
        "ERROR: internal exception message leaked"
    )

log_sink = logging.InMemoryStructuredLogSink()

record = log_sink.emit(
    level="INFO",
    event="kernel.validation",
    correlation_id="corr-validation",
    organization_id="org-validation",
    actor_id="actor-validation",
    trace_id="trace-validation",
    span_id="span-validation",
    fields={
        "result": "ok",
        "password": "must-not-log",
        "payment": {
            "card_number": "4111111111111111",
            "safe": "retained",
        },
    },
    timestamp="2026-01-01T00:00:02+00:00",
)

if record["fields"]["password"] != "[REDACTED]":
    raise SystemExit(
        "ERROR: log password was not redacted"
    )

if (
    record["fields"]["payment"]["card_number"]
    != "[REDACTED]"
):
    raise SystemExit(
        "ERROR: sensitive payment data was not redacted"
    )

if not record["correlation_id"]:
    raise SystemExit(
        "ERROR: structured log lacks correlation_id"
    )

registry = metrics.MetricRegistry()
registry.increment(
    "kernel_requests_total",
    labels={"status": "success"},
)
registry.set_gauge(
    "kernel_ready",
    1,
)
registry.observe(
    "kernel_request_duration_ms",
    12.5,
    labels={"operation": "validation"},
)

snapshot = registry.snapshot()

if not snapshot["counters"]:
    raise SystemExit(
        "ERROR: counter metric was not recorded"
    )

if not snapshot["gauges"]:
    raise SystemExit(
        "ERROR: gauge metric was not recorded"
    )

if not snapshot["timings"]:
    raise SystemExit(
        "ERROR: timing metric was not recorded"
    )

health_registry = health.HealthRegistry()

health_registry.register(
    "database",
    lambda: health.HealthResult(
        name="database",
        required=True,
        healthy=True,
        details="validation",
    ),
    required=True,
)

health_registry.register(
    "optional-observer",
    lambda: health.HealthResult(
        name="optional-observer",
        required=False,
        healthy=False,
        details="optional validation failure",
    ),
    required=False,
)

health_result = health_registry.evaluate()

if not health_result["live"]:
    raise SystemExit(
        "ERROR: liveness unexpectedly failed"
    )

if not health_result["ready"]:
    raise SystemExit(
        "ERROR: optional dependency incorrectly failed readiness"
    )

required_failure_registry = health.HealthRegistry()
required_failure_registry.register(
    "database",
    lambda: health.HealthResult(
        name="database",
        required=True,
        healthy=False,
        details="validation failure",
    ),
    required=True,
)

if required_failure_registry.evaluate()["ready"]:
    raise SystemExit(
        "ERROR: required unhealthy dependency did not fail readiness"
    )

status = (
    KERNEL / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Kernel audit persistence",
    "- [x] Error contract",
    "- [x] Structured logging",
    "- [x] Health checks",
    "- [x] Metrics",
    "- [ ] Secret reference boundary",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Kernel status missing: " + phrase
        )

print("OK: Kernel audit ledger is tamper-evident.")
print("OK: Audit and log secret redaction passed.")
print("OK: Safe Kernel error normalization passed.")
print("OK: Structured logs require correlation IDs.")
print("OK: Counter, gauge and timing metrics passed.")
print("OK: Liveness/readiness semantics passed.")
print("STATUS: KERNEL P0 AUDIT + OBSERVABILITY READY")
