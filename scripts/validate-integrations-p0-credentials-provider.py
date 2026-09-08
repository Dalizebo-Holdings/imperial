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
    "credential_reference": RUNTIME / "credential_reference.py",
    "provider_adapter": RUNTIME / "provider_adapter.py",
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
credential_reference = load_module(
    "credential_reference",
    MODULES["credential_reference"],
)
provider_adapter = load_module(
    "provider_adapter",
    MODULES["provider_adapter"],
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
    supported_operations=["send_message"],
    input_schema={"type": "object"},
    output_schema={"type": "object"},
    error_schema={"type": "object"},
    rate_limit=connector_model.RateLimitPolicy(
        requests=100,
        per_seconds=60,
    ),
    timeout_seconds=20,
    permission_scopes=["message.send"],
)

registry.register(definition)

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

credentials = credential_reference.CredentialReferenceAdapter()

descriptor = credential_reference.CredentialDescriptor(
    credential_ref="secret://validation/email",
    organization_id="org-validation",
    connector_id="validation.email",
    auth_method="API_KEY",
    permission_scopes=["message.send"],
    owner="Integrations Platform",
    version="1",
    metadata={
        "purpose": "validation descriptor",
    },
)

credentials.register(descriptor)

context = credentials.resolve_context(
    credential_ref=request.credential_ref,
    organization_id=request.organization_id,
    connector_id=request.connector_id,
    auth_method=request.auth_method,
    requested_scopes=request.permission_scopes,
)

if context.credential_ref != request.credential_ref:
    raise SystemExit(
        "ERROR: credential context reference mismatch"
    )

if not isinstance(context.approved_scopes, tuple):
    raise SystemExit(
        "ERROR: credential context scopes are not immutable"
    )

bad_org = False
try:
    credentials.resolve_context(
        credential_ref=request.credential_ref,
        organization_id="other-org",
        connector_id=request.connector_id,
        auth_method=request.auth_method,
        requested_scopes=request.permission_scopes,
    )
except credential_reference.CredentialReferenceError:
    bad_org = True

if not bad_org:
    raise SystemExit(
        "ERROR: cross-organization credential resolution was accepted"
    )

bad_metadata = credential_reference.CredentialDescriptor(
    credential_ref="secret://validation/bad",
    organization_id="org-validation",
    connector_id="validation.email",
    auth_method="API_KEY",
    permission_scopes=[],
    metadata={
        "api_key": "must-not-be-stored",
    },
)

try:
    credentials.register(bad_metadata)
except credential_reference.CredentialReferenceError:
    pass
else:
    raise SystemExit(
        "ERROR: raw secret-bearing credential metadata was accepted"
    )


class ValidationAdapter(provider_adapter.ProviderAdapter):
    connector_id = "validation.email"
    connector_version = "1.0.0"
    adapter_version = "1"
    supported_operations = {"send_message"}

    def execute(
        self,
        *,
        prepared_call,
        credential_context,
    ):
        self.validate_context(
            prepared_call=prepared_call,
            credential_context=credential_context,
        )

        response = runtime_contract.ConnectorResponse(
            request_id=prepared_call.request.request_id,
            connector_id=prepared_call.request.connector_id,
            correlation_id=prepared_call.request.correlation_id,
            status="SUCCESS",
            provider_status="VALIDATION_ONLY",
            data={"message_id": "validation-message"},
            retryable=False,
            rate_limit={},
            audit_event={
                "event_type": "integrations_os.connector.completed",
                "request_id": prepared_call.request.request_id,
                "connector_id": prepared_call.request.connector_id,
                "correlation_id": prepared_call.request.correlation_id,
            },
        )
        response.validate()
        return response

    def health_check(self):
        return provider_adapter.AdapterHealth(
            healthy=True,
            status="VALIDATION_ONLY",
            details={"network_calls": 0},
        )


adapters = provider_adapter.ProviderAdapterRegistry()
adapter = ValidationAdapter()
adapters.register(adapter)

resolved_adapter = adapters.prepare_adapter(
    prepared_call=prepared,
    credential_context=context,
)

health = resolved_adapter.health_check()

if not health.healthy:
    raise SystemExit(
        "ERROR: validation provider adapter health failed"
    )

if health.details.get("network_calls") != 0:
    raise SystemExit(
        "ERROR: P0 validation adapter performed a network call"
    )

response = resolved_adapter.execute(
    prepared_call=prepared,
    credential_context=context,
)

if response.status != "SUCCESS":
    raise SystemExit(
        "ERROR: validation provider adapter response failed"
    )

try:
    adapters.register(adapter)
except provider_adapter.ProviderAdapterError:
    pass
else:
    raise SystemExit(
        "ERROR: duplicate provider adapter registration was accepted"
    )

normalized = provider_adapter.normalize_adapter_exception(
    prepared_call=prepared,
    exc=RuntimeError("must not leak"),
    retryable=True,
    provider_code="VALIDATION_ERROR",
)

if normalized.status != "ERROR":
    raise SystemExit(
        "ERROR: normalized adapter exception status is invalid"
    )

if "must not leak" in normalized.error.message:
    raise SystemExit(
        "ERROR: provider exception details leaked into normalized error"
    )

status = (
    INTEGRATIONS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Credential reference adapter",
    "- [x] Provider adapter interface",
    "- [ ] Integration audit adapter",
]:
    if phrase not in status:
        raise SystemExit(
            f"ERROR: Integrations OS status missing: {phrase}"
        )

print("OK: Credential references are tenant-scoped.")
print("OK: Raw secret-bearing metadata is rejected.")
print("OK: Credential context contains references only.")
print("OK: Provider adapter identity and context validation passed.")
print("OK: Duplicate provider adapters are rejected.")
print("OK: Provider errors normalize without leaking exception details.")
print("OK: P0 validation performed zero network calls.")
print("STATUS: INTEGRATIONS OS CREDENTIAL + PROVIDER P0 COMPLETE")
