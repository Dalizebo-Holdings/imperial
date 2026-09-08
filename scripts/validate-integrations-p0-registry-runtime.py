#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "orchestration/integrations-os"
RUNTIME = INTEGRATIONS / "runtime"

MODULES = {
    "connector_model": RUNTIME / "connector_model.py",
    "connector_registry": RUNTIME / "connector_registry.py",
    "runtime_contract": RUNTIME / "runtime_contract.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Integrations OS runtime file: {path}"
        )
    py_compile.compile(str(path), doraise=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


connector_model = load_module(
    "connector_model",
    MODULES["connector_model"],
)
connector_registry = load_module(
    "connector_registry",
    MODULES["connector_registry"],
)
runtime_contract = load_module(
    "runtime_contract",
    MODULES["runtime_contract"],
)

registry = connector_registry.ConnectorRegistry()

definition = connector_model.ConnectorDefinition(
    connector_id="validation.email",
    name="Validation Email Connector",
    provider="validation-provider",
    version="1.0.0",
    owner="Integrations Platform",
    category="Email",
    supported_auth_methods=["API_KEY"],
    supported_operations=["send_message", "health_check"],
    input_schema={
        "type": "object",
        "required": ["recipient", "body"],
    },
    output_schema={
        "type": "object",
        "required": ["message_id"],
    },
    error_schema={
        "type": "object",
        "required": ["code", "message"],
    },
    rate_limit=connector_model.RateLimitPolicy(
        requests=100,
        per_seconds=60,
    ),
    timeout_seconds=20,
    max_attempts=3,
    retryable_error_codes=["TIMEOUT", "RATE_LIMITED"],
    idempotency_supported=True,
    circuit_breaker=connector_model.CircuitBreakerPolicy(
        failure_threshold=5,
        recovery_timeout_seconds=60,
        half_open_max_calls=1,
    ),
    permission_scopes=["message.send"],
    compatible_versions=["1.0.0"],
)

registry.register(definition)

resolved = registry.get(
    "validation.email",
    "1.0.0",
)

if resolved.connector_id != "validation.email":
    raise SystemExit("ERROR: connector registry lookup failed")

try:
    registry.register(definition)
except connector_registry.ConnectorRegistryError:
    pass
else:
    raise SystemExit(
        "ERROR: duplicate connector registration was accepted"
    )

request = runtime_contract.ConnectorRequest(
    request_id="request-validation-001",
    connector_id="validation.email",
    connector_version="1.0.0",
    operation="send_message",
    organization_id="org-validation",
    correlation_id="corr-validation",
    idempotency_key="idem-validation",
    auth_method="API_KEY",
    credential_ref="secret://validation/email",
    payload={
        "recipient": "user@example.invalid",
        "body": "validation",
    },
    permission_scopes=["message.send"],
    timeout_seconds=10,
)

authorization = runtime_contract.IntegrationAuthorization(
    pillars_approved=True,
    kernel_authorized=True,
    authorization_ref="auth-validation",
)

prepared = runtime_contract.prepare_call(
    registry=registry,
    request=request,
    authorization=authorization,
)

if prepared.state != "READY_FOR_ADAPTER_EXECUTION":
    raise SystemExit(
        "ERROR: valid connector request was not prepared"
    )

if prepared.effective_timeout_seconds != 10:
    raise SystemExit(
        "ERROR: effective connector timeout is incorrect"
    )

denied_authorization = runtime_contract.IntegrationAuthorization(
    pillars_approved=True,
    kernel_authorized=False,
    authorization_ref="auth-denied",
)

try:
    runtime_contract.prepare_call(
        registry=registry,
        request=request,
        authorization=denied_authorization,
    )
except runtime_contract.RuntimeContractError:
    pass
else:
    raise SystemExit(
        "ERROR: connector prepared without Kernel authorization"
    )

bad_scope = runtime_contract.ConnectorRequest(
    request_id="request-validation-002",
    connector_id="validation.email",
    connector_version="1.0.0",
    operation="send_message",
    organization_id="org-validation",
    correlation_id="corr-validation-2",
    idempotency_key="idem-validation-2",
    auth_method="API_KEY",
    credential_ref="secret://validation/email",
    payload={"recipient": "x", "body": "y"},
    permission_scopes=["admin.everything"],
)

try:
    runtime_contract.prepare_call(
        registry=registry,
        request=bad_scope,
        authorization=authorization,
    )
except runtime_contract.RuntimeContractError:
    pass
else:
    raise SystemExit(
        "ERROR: undeclared connector scope was accepted"
    )

secret_payload = runtime_contract.ConnectorRequest(
    request_id="request-validation-003",
    connector_id="validation.email",
    connector_version="1.0.0",
    operation="send_message",
    organization_id="org-validation",
    correlation_id="corr-validation-3",
    idempotency_key="idem-validation-3",
    auth_method="API_KEY",
    credential_ref="secret://validation/email",
    payload={
        "recipient": "x",
        "body": "y",
        "api_key": "must-not-be-here",
    },
)

try:
    runtime_contract.prepare_call(
        registry=registry,
        request=secret_payload,
        authorization=authorization,
    )
except runtime_contract.RuntimeContractError:
    pass
else:
    raise SystemExit(
        "ERROR: raw sensitive payload field was accepted"
    )

open_circuit = runtime_contract.CircuitState(
    state="OPEN",
    failure_count=5,
)

try:
    runtime_contract.prepare_call(
        registry=registry,
        request=request,
        authorization=authorization,
        circuit_state=open_circuit,
    )
except runtime_contract.RuntimeContractError:
    pass
else:
    raise SystemExit(
        "ERROR: OPEN circuit allowed connector preparation"
    )

response = runtime_contract.ConnectorResponse(
    request_id=request.request_id,
    connector_id=request.connector_id,
    correlation_id=request.correlation_id,
    status="SUCCESS",
    provider_status="200",
    data={"message_id": "validation-message"},
    retryable=False,
    rate_limit={"remaining": 99},
    audit_event={
        "event_type": "integrations_os.connector.completed",
        "request_id": request.request_id,
    },
)
response.validate()

status = (
    INTEGRATIONS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Connector definition model",
    "- [x] Connector registry",
    "- [x] Runtime request contract",
    "- [x] Authorization gate",
    "- [x] Version compatibility contract",
    "- [x] Operation and scope validation",
    "- [x] Timeout and circuit-breaker contract",
    "- [x] Normalized response and error contract",
]:
    if phrase not in status:
        raise SystemExit(
            f"ERROR: Integrations OS status missing: {phrase}"
        )

print("OK: Connector definition validation passed.")
print("OK: Connector registry registration and lookup passed.")
print("OK: Duplicate connector registration is blocked.")
print("OK: Pillars OS + Kernel authorization gate passed.")
print("OK: Operation, scope and timeout validation passed.")
print("OK: Raw sensitive payload fields are rejected.")
print("OK: OPEN circuit blocks connector preparation.")
print("OK: Normalized connector response validation passed.")
print("STATUS: INTEGRATIONS OS REGISTRY + RUNTIME CONTRACTS P0 COMPLETE")
