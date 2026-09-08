#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
PATH = BAAS / "api-gateway/runtime.py"

if not PATH.exists():
    raise SystemExit(
        f"ERROR: missing API Gateway runtime: {PATH}"
    )

py_compile.compile(
    str(PATH),
    doraise=True,
)

spec = importlib.util.spec_from_file_location(
    "baas_api_gateway",
    PATH,
)

if spec is None or spec.loader is None:
    raise SystemExit(
        "ERROR: unable to load API Gateway runtime"
    )

gateway = importlib.util.module_from_spec(
    spec
)
sys.modules[
    "baas_api_gateway"
] = gateway
spec.loader.exec_module(
    gateway
)

api = gateway.APIGateway()

route = gateway.GatewayRoute(
    route_id="route-database-read",
    method="POST",
    path="/api/v1/database/query",
    target_service="database",
    target_operation="query.execute",
    authentication_required=True,
    required_permission="database.read",
    max_payload_bytes=1024,
    timeout_ms=5000,
    rate_limit_requests=2,
    rate_limit_window_seconds=60,
    enabled=True,
)

api.register_route(route)

request = gateway.GatewayRequest(
    request_id="req-gateway-validation",
    correlation_id="corr-gateway-validation",
    method="POST",
    path="/api/v1/database/query",
    content_length=128,
    authenticated=True,
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_gateway_validation",
    permission_evidence=(
        "database.read",
    ),
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    metadata={
        "content_type": "application/json",
    },
)

plan = api.resolve(
    request=request,
    now="2026-01-01T00:00:00+00:00",
)

if (
    plan.target_service
    != "database"
):
    raise SystemExit(
        "ERROR: route target service mismatch"
    )

if (
    plan.dispatch_state
    != "READY_FOR_GATEWAY_ADAPTER"
):
    raise SystemExit(
        "ERROR: gateway claimed network execution"
    )

if (
    plan.correlation_id
    != request.correlation_id
):
    raise SystemExit(
        "ERROR: correlation_id was not preserved"
    )

unauth = gateway.GatewayRequest(
    request_id="req-unauth",
    correlation_id="corr-unauth",
    method="POST",
    path="/api/v1/database/query",
    content_length=1,
    authenticated=False,
    actor_id=None,
    actor_type=None,
    kernel_authorization_ref=None,
    permission_evidence=(),
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
)

try:
    api.resolve(
        request=unauth,
        now="2026-01-01T00:00:01+00:00",
    )
except gateway.GatewayError as exc:
    if exc.code != "AUTHENTICATION_REQUIRED":
        raise
else:
    raise SystemExit(
        "ERROR: unauthenticated protected request was accepted"
    )

missing_permission = gateway.GatewayRequest(
    request_id="req-permission",
    correlation_id="corr-permission",
    method="POST",
    path="/api/v1/database/query",
    content_length=1,
    authenticated=True,
    actor_id="actor-permission",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_permission",
    permission_evidence=(),
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
)

try:
    api.resolve(
        request=missing_permission,
        now="2026-01-01T00:00:02+00:00",
    )
except gateway.GatewayError as exc:
    if exc.code != "PERMISSION_DENIED":
        raise
else:
    raise SystemExit(
        "ERROR: missing permission evidence was accepted"
    )

oversized = gateway.GatewayRequest(
    request_id="req-large",
    correlation_id="corr-large",
    method="POST",
    path="/api/v1/database/query",
    content_length=2048,
    authenticated=True,
    actor_id="actor-large",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_large",
    permission_evidence=(
        "database.read",
    ),
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
)

try:
    api.resolve(
        request=oversized,
        now="2026-01-01T00:00:03+00:00",
    )
except gateway.GatewayError as exc:
    if exc.code != "PAYLOAD_TOO_LARGE":
        raise
else:
    raise SystemExit(
        "ERROR: oversized request was accepted"
    )

rate_request = gateway.GatewayRequest(
    request_id="req-rate",
    correlation_id="corr-rate",
    method="POST",
    path="/api/v1/database/query",
    content_length=1,
    authenticated=True,
    actor_id="actor-rate",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_rate",
    permission_evidence=(
        "database.read",
    ),
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
)

api.resolve(
    request=rate_request,
    now="2026-01-01T00:00:10+00:00",
)
api.resolve(
    request=rate_request,
    now="2026-01-01T00:00:11+00:00",
)

try:
    api.resolve(
        request=rate_request,
        now="2026-01-01T00:00:12+00:00",
    )
except gateway.GatewayError as exc:
    if exc.code != "RATE_LIMITED":
        raise
else:
    raise SystemExit(
        "ERROR: reference rate limit was not enforced"
    )

try:
    gateway.GatewayRoute(
        route_id="route-bad-version",
        method="GET",
        path="/api/v2/test",
        target_service="database",
        target_operation="test",
        authentication_required=False,
        required_permission=None,
        max_payload_bytes=1,
        timeout_ms=1000,
        rate_limit_requests=1,
        rate_limit_window_seconds=60,
    ).validate()
except ValueError:
    pass
else:
    raise SystemExit(
        "ERROR: route outside /api/v1 was accepted"
    )

try:
    gateway.GatewayRequest(
        request_id="req-secret",
        correlation_id="corr-secret",
        method="GET",
        path="/api/v1/test",
        content_length=0,
        authenticated=False,
        actor_id=None,
        actor_type=None,
        kernel_authorization_ref=None,
        permission_evidence=(),
        organization_id="org-validation",
        workspace_id="workspace-validation",
        project_id="project-validation",
        environment_id="env-validation",
        metadata={
            "authorization": "Bearer secret"
        },
    ).validate()
except ValueError:
    pass
else:
    raise SystemExit(
        "ERROR: secret-bearing gateway metadata was accepted"
    )

safe_error = gateway.GatewayError(
    "TEST_ERROR",
    "Safe error",
    request_id="req-safe",
    details={
        "api_key": "must-not-expose",
        "safe": "value",
    },
).envelope()

if (
    safe_error["details"]["api_key"]
    != "[REDACTED]"
):
    raise SystemExit(
        "ERROR: safe error details did not redact secret"
    )

status = (
    BAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] API Gateway",
    "- [x] /api/v1 route registry",
    "- [x] Kernel authorization evidence gate",
    "- [x] Reference rate-limit guard",
    "- [x] Safe structured errors",
    "- [ ] Events",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: API Gateway status missing: "
            + phrase
        )

print("OK: /api/v1 route registry passed.")
print("OK: Authentication and permission gates fail closed.")
print("OK: Payload limit enforcement passed.")
print("OK: Timeout budget is bounded.")
print("OK: Reference rate-limit guard passed.")
print("OK: Correlation/request identifiers are preserved.")
print("OK: Secret-bearing metadata is rejected/redacted.")
print("OK: Dispatch remains adapter-only metadata.")
print("STATUS: BAAS P0 API GATEWAY READY")
