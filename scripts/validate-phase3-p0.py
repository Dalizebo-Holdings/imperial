#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import py_compile
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS = ROOT / "orchestration/integrations-os"
RUNTIME = INTEGRATIONS / "runtime"

MODULES = {
    "connector_model": RUNTIME / "connector_model.py",
    "connector_registry": RUNTIME / "connector_registry.py",
    "runtime_contract": RUNTIME / "runtime_contract.py",
    "credential_reference": RUNTIME / "credential_reference.py",
    "provider_adapter": RUNTIME / "provider_adapter.py",
    "audit_adapter": RUNTIME / "audit_adapter.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Integrations OS runtime file: {path}"
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
audit_adapter = load_module(
    "audit_adapter",
    MODULES["audit_adapter"],
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
    request_id="request-audit-validation",
    connector_id="validation.email",
    connector_version="1.0.0",
    operation="send_message",
    organization_id="org-validation",
    correlation_id="corr-audit-validation",
    idempotency_key="idem-audit-validation",
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

credentials = (
    credential_reference.CredentialReferenceAdapter()
)

credentials.register(
    credential_reference.CredentialDescriptor(
        credential_ref="secret://validation/email",
        organization_id="org-validation",
        connector_id="validation.email",
        auth_method="API_KEY",
        permission_scopes=["message.send"],
        version="1",
        metadata={"purpose": "validation"},
    )
)

context = credentials.resolve_context(
    credential_ref=request.credential_ref,
    organization_id=request.organization_id,
    connector_id=request.connector_id,
    auth_method=request.auth_method,
    requested_scopes=request.permission_scopes,
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
            rate_limit={"remaining": 99},
            audit_event={
                "event_type": (
                    "integrations_os.connector.completed"
                ),
                "request_id": (
                    prepared_call.request.request_id
                ),
                "connector_id": (
                    prepared_call.request.connector_id
                ),
                "correlation_id": (
                    prepared_call.request.correlation_id
                ),
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
adapters.register(ValidationAdapter())

adapter = adapters.prepare_adapter(
    prepared_call=prepared,
    credential_context=context,
)

response = adapter.execute(
    prepared_call=prepared,
    credential_context=context,
)

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "integrations-audit.jsonl"

    prepared_record = (
        audit_adapter.persist_prepared_call(
            path,
            prepared_call=prepared,
            recorded_at="2026-01-01T00:00:00+00:00",
        )
    )

    response_record = audit_adapter.persist_response(
        path,
        response=response,
        recorded_at="2026-01-01T00:00:01+00:00",
    )

    if (
        response_record["previous_hash"]
        != prepared_record["record_hash"]
    ):
        raise SystemExit(
            "ERROR: integration audit chain link failed"
        )

    verification = audit_adapter.verify_file(path)

    if not verification["valid"]:
        raise SystemExit(
            "ERROR: valid integration audit chain failed: "
            + str(verification)
        )

    secret_event = {
        "event_type": (
            "integrations_os.connector.error"
        ),
        "request_id": "request-secret-test",
        "connector_id": "validation.email",
        "correlation_id": "corr-secret-test",
        "api_key": "must-not-persist",
        "metadata": {
            "authorization": "Bearer hidden",
            "safe": "retained",
        },
    }

    secret_record = audit_adapter.append_event(
        path,
        event=secret_event,
        recorded_at="2026-01-01T00:00:02+00:00",
    )

    if secret_record["event"]["api_key"] != "[REDACTED]":
        raise SystemExit(
            "ERROR: integration api_key was not redacted"
        )

    if (
        secret_record["event"]["metadata"]["authorization"]
        != "[REDACTED]"
    ):
        raise SystemExit(
            "ERROR: nested authorization was not redacted"
        )

    if (
        secret_record["event"]["metadata"]["safe"]
        != "retained"
    ):
        raise SystemExit(
            "ERROR: safe metadata was incorrectly removed"
        )

    verification = audit_adapter.verify_file(path)

    if not verification["valid"]:
        raise SystemExit(
            "ERROR: extended integration audit chain failed"
        )

    tampered = deepcopy(
        audit_adapter.read_records(path)
    )
    tampered[0]["event"]["connector_id"] = "tampered.connector"

    tamper_result = audit_adapter.verify_records(
        tampered
    )

    if tamper_result["valid"]:
        raise SystemExit(
            "ERROR: tampered integration audit was accepted"
        )

integration_status = (
    INTEGRATIONS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Credential reference adapter",
    "- [x] Provider adapter interface",
    "- [x] Integration audit adapter",
    "P0 Status",
    "COMPLETE",
]:
    if phrase not in integration_status:
        raise SystemExit(
            "ERROR: Integrations OS P0 status missing: "
            + phrase
        )

phase_status = (
    ROOT / "orchestration/STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "Algorithm OS",
    "Loop OS",
    "Integrations OS",
    "P0 status: COMPLETE",
    "Phase 3 Status",
    "COMPLETE",
    "Phase 4 — Dalizebo Kernel",
]:
    if phrase not in phase_status:
        raise SystemExit(
            "ERROR: Phase 3 closure status missing: "
            + phrase
        )

print("OK: Prepared connector calls persist to audit.")
print("OK: Connector responses persist to audit.")
print("OK: Integration audit recursively redacts sensitive values.")
print("OK: Append-only hash chaining passed.")
print("OK: Audit verification and tamper detection passed.")
print("OK: Integrations OS P0 checklist is complete.")
print("OK: Algorithm OS + Loop OS + Integrations OS P0 are complete.")
print("STATUS: PHASE 3 P0 COMPLETE")
