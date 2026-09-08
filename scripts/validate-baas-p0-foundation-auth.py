#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

MODULES = {
    "baas_request_context": BAAS / "runtime/request_context.py",
    "baas_auth": BAAS / "auth/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing BaaS runtime file: {path}"
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


request_context = load_module(
    "baas_request_context",
    MODULES["baas_request_context"],
)
auth = load_module(
    "baas_auth",
    MODULES["baas_auth"],
)

context = request_context.BaaSRequestContext(
    request_id="req-validation",
    correlation_id="corr-validation",
    service="authentication",
    operation="session.create",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_validation",
    idempotency_key="idem-validation",
)
context.validate()

try:
    request_context.BaaSRequestContext(
        request_id="req-invalid",
        correlation_id="corr-invalid",
        service="authentication",
        operation="session.create",
        organization_id="org-validation",
        workspace_id="workspace-validation",
        project_id="project-validation",
        environment_id="env-validation",
        actor_id="actor-validation",
        actor_type="HUMAN_USER",
        kernel_authorization_ref="",
        idempotency_key="idem-invalid",
    ).validate()
except request_context.BaaSRequestError:
    pass
else:
    raise SystemExit(
        "ERROR: BaaS request without Kernel authorization reference was accepted"
    )

registry = auth.AuthenticationRegistry()

human = auth.IdentityRecord(
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    organization_id="org-validation",
    identity_ref="identity://validation/human",
    metadata={"source": "validation"},
)
registry.register_identity(human)

service = auth.IdentityRecord(
    actor_id="service-validation",
    actor_type="SERVICE_ACCOUNT",
    organization_id="org-validation",
    identity_ref="identity://validation/service",
)
registry.register_identity(service)

session, raw_token = registry.issue_session(
    actor_id=human.actor_id,
    organization_id=human.organization_id,
    authentication_method="PASSKEY",
    ttl_seconds=3600,
    mfa_verified=True,
    now="2026-01-01T00:00:00+00:00",
)

if raw_token == session.token_fingerprint:
    raise SystemExit(
        "ERROR: raw session token was persisted directly"
    )

principal = registry.authenticate_session(
    session_id=session.session_id,
    raw_token=raw_token,
    organization_id="org-validation",
    now="2026-01-01T00:00:01+00:00",
)

if not principal.authenticated:
    raise SystemExit(
        "ERROR: valid session did not authenticate"
    )

if not principal.mfa_verified:
    raise SystemExit(
        "ERROR: MFA evidence was not preserved"
    )

registry.revoke_session(
    session.session_id,
    now="2026-01-01T00:00:02+00:00",
)

try:
    registry.authenticate_session(
        session_id=session.session_id,
        raw_token=raw_token,
        organization_id="org-validation",
        now="2026-01-01T00:00:03+00:00",
    )
except auth.AuthenticationError:
    pass
else:
    raise SystemExit(
        "ERROR: revoked session still authenticated"
    )

api_key_record, raw_key = registry.issue_api_key(
    actor_id=service.actor_id,
    organization_id=service.organization_id,
    scopes=["database.read", "events.publish"],
    ttl_seconds=3600,
    now="2026-01-01T00:00:00+00:00",
)

if raw_key == api_key_record.key_fingerprint:
    raise SystemExit(
        "ERROR: raw API key was persisted directly"
    )

api_principal = registry.authenticate_api_key(
    key_id=api_key_record.key_id,
    raw_key=raw_key,
    organization_id="org-validation",
    required_scope="database.read",
    now="2026-01-01T00:00:01+00:00",
)

if api_principal.actor_type != "SERVICE_ACCOUNT":
    raise SystemExit(
        "ERROR: API key principal identity type changed"
    )

try:
    registry.authenticate_api_key(
        key_id=api_key_record.key_id,
        raw_key=raw_key,
        organization_id="org-validation",
        required_scope="billing.admin",
        now="2026-01-01T00:00:01+00:00",
    )
except auth.AuthenticationError:
    pass
else:
    raise SystemExit(
        "ERROR: API key missing required scope authenticated"
    )

registry.disable_api_key(api_key_record.key_id)

try:
    registry.authenticate_api_key(
        key_id=api_key_record.key_id,
        raw_key=raw_key,
        organization_id="org-validation",
        required_scope="database.read",
        now="2026-01-01T00:00:01+00:00",
    )
except auth.AuthenticationError:
    pass
else:
    raise SystemExit(
        "ERROR: disabled API key still authenticated"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Shared BaaS service/request contract",
    "- [x] Authentication identity registry",
    "- [x] Session lifecycle",
    "- [x] API key lifecycle",
    "- [ ] PostgreSQL Database BaaS",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: BaaS status missing: " + phrase
        )

print("OK: BaaS request context requires Kernel authorization evidence.")
print("OK: Human and service identities register correctly.")
print("OK: Session tokens are persisted as fingerprints only.")
print("OK: Revoked sessions fail closed.")
print("OK: API keys are persisted as fingerprints only.")
print("OK: API-key scope enforcement passed.")
print("OK: Disabled API keys fail closed.")
print("STATUS: BAAS P0 FOUNDATION + AUTHENTICATION READY")
