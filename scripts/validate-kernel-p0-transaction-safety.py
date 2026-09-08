#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "kernel"

MODULES = {
    "kernel_identifiers": KERNEL / "data/identifiers.py",
    "kernel_transactions": KERNEL / "transactions/runtime.py",
    "kernel_idempotency": KERNEL / "idempotency/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Kernel primitive runtime file: {path}"
        )
    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERROR: unable to load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


identifiers = load_module(
    "kernel_identifiers",
    MODULES["kernel_identifiers"],
)
transactions = load_module(
    "kernel_transactions",
    MODULES["kernel_transactions"],
)
idempotency = load_module(
    "kernel_idempotency",
    MODULES["kernel_idempotency"],
)

fresh_one = identifiers.new_id("ord")
fresh_two = identifiers.new_id("ord")

if fresh_one == fresh_two:
    raise SystemExit(
        "ERROR: fresh identifiers collided"
    )

identifiers.validate_id(
    fresh_one,
    expected_prefix="ord",
)

stable_one = identifiers.stable_id(
    "pay",
    namespace="kernel.payment",
    organization_id="org-validation",
    operation="payment.create",
    idempotency_key="idem-validation",
)

stable_two = identifiers.stable_id(
    "pay",
    namespace="kernel.payment",
    organization_id="org-validation",
    operation="payment.create",
    idempotency_key="idem-validation",
)

if stable_one != stable_two:
    raise SystemExit(
        "ERROR: retry-stable identifier changed across retries"
    )

backend = transactions.InMemoryTransactionBackend()

tx = transactions.Transaction(
    transaction_id=identifiers.new_id("txn"),
    backend=backend,
    correlation_id="corr-validation",
)

tx.begin(
    now="2026-01-01T00:00:00+00:00",
)

resource_id = identifiers.new_id("ord")

tx.stage_resource(
    resource_key=f"order:{resource_id}",
    value={
        "id": resource_id,
        "organization_id": "org-validation",
        "status": "CREATED",
    },
)

tx.stage_audit({
    "event_type": "kernel.order.created",
    "resource_id": resource_id,
})

event_id = identifiers.new_id("evt")

tx.stage_outbox({
    "event_id": event_id,
    "event_type": "order.created",
    "event_version": "1",
    "organization_id": "org-validation",
    "workspace_id": "workspace-validation",
    "project_id": "project-validation",
    "environment_id": "env-validation",
    "resource_type": "order",
    "resource_id": resource_id,
    "occurred_at": "2026-01-01T00:00:00+00:00",
    "correlation_id": "corr-validation",
    "actor_type": "HUMAN_USER",
    "actor_id": "actor-validation",
    "payload": {"status": "CREATED"},
})

if backend.resources or backend.audit_records or backend.outbox:
    raise SystemExit(
        "ERROR: staged transaction state became visible before commit"
    )

if tx.publishable_outbox:
    raise SystemExit(
        "ERROR: outbox event became publishable before commit"
    )

tx.commit(
    now="2026-01-01T00:00:01+00:00",
)

if f"order:{resource_id}" not in backend.resources:
    raise SystemExit(
        "ERROR: committed resource is missing"
    )

if len(backend.audit_records) != 1:
    raise SystemExit(
        "ERROR: committed audit record is missing"
    )

if len(tx.publishable_outbox) != 1:
    raise SystemExit(
        "ERROR: committed outbox event is not publishable"
    )

snapshot = backend.snapshot()

rollback_tx = transactions.Transaction(
    transaction_id=identifiers.new_id("txn"),
    backend=backend,
    correlation_id="corr-rollback",
)

rollback_tx.begin(
    now="2026-01-01T00:00:02+00:00",
)

rollback_tx.stage_resource(
    resource_key="order:should-not-exist",
    value={"id": "should-not-exist"},
)

rollback_tx.stage_audit({
    "event_type": "kernel.validation.rollback",
})

rollback_tx.rollback(
    now="2026-01-01T00:00:03+00:00",
)

if backend.snapshot() != snapshot:
    raise SystemExit(
        "ERROR: rolled-back transaction changed backend state"
    )

store = idempotency.IdempotencyStore()

payload = {
    "order_id": resource_id,
    "amount": 1000,
    "currency": "ZAR",
}

first_record, created = store.begin(
    organization_id="org-validation",
    operation="payment.create",
    key="idem-payment-validation",
    payload=payload,
    now="2026-01-01T00:00:00+00:00",
    ttl_seconds=3600,
)

if not created:
    raise SystemExit(
        "ERROR: first idempotency request was not created"
    )

retry_record, retry_created = store.begin(
    organization_id="org-validation",
    operation="payment.create",
    key="idem-payment-validation",
    payload=payload,
    now="2026-01-01T00:00:01+00:00",
    ttl_seconds=3600,
)

if retry_created:
    raise SystemExit(
        "ERROR: identical retry created a second idempotency record"
    )

if retry_record.request_hash != first_record.request_hash:
    raise SystemExit(
        "ERROR: identical retry request hash changed"
    )

try:
    store.begin(
        organization_id="org-validation",
        operation="payment.create",
        key="idem-payment-validation",
        payload={
            "order_id": resource_id,
            "amount": 2000,
            "currency": "ZAR",
        },
        now="2026-01-01T00:00:02+00:00",
        ttl_seconds=3600,
    )
except idempotency.IdempotencyConflict:
    pass
else:
    raise SystemExit(
        "ERROR: same key with different request hash was accepted"
    )

completed = store.complete(
    organization_id="org-validation",
    operation="payment.create",
    key="idem-payment-validation",
    response_reference=stable_one,
)

if completed.status != "COMPLETED":
    raise SystemExit(
        "ERROR: idempotency record did not complete"
    )

try:
    idempotency.canonical_request_hash({
        "api_key": "must-not-be-hashed",
    })
except idempotency.IdempotencyError:
    pass
else:
    raise SystemExit(
        "ERROR: sensitive idempotency payload field was accepted"
    )

status = (
    KERNEL / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Shared identifier runtime",
    "- [x] Transaction utilities",
    "- [x] Idempotency runtime",
    "- [ ] Kernel audit persistence",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Kernel status missing: " + phrase
        )

print("OK: Fresh Kernel identifiers are unique and non-sequential.")
print("OK: Retry-stable identifiers are deterministic.")
print("OK: Transaction state is invisible before commit.")
print("OK: Rollback leaves no partial mutation.")
print("OK: Outbox events become publishable only after commit.")
print("OK: Identical idempotent retries reuse the existing record.")
print("OK: Same key with different request hash is rejected.")
print("OK: Sensitive request fields are rejected from idempotency hashing.")
print("STATUS: KERNEL P0 TRANSACTION SAFETY PRIMITIVES READY")
