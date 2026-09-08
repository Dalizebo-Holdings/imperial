# BaaS API Gateway Runtime Contract

## Purpose

The BaaS API Gateway is the versioned ingress contract for Dalizebo BaaS.

P0 provides deterministic route registration, request validation,
authentication/authorization evidence checks, bounded payload/timeouts,
correlation/request identifiers, a reference rate-limit guard, and safe error
envelopes.

P0 does not claim to be a production reverse proxy, WAF, or distributed rate
limiting service.

## API Version

All public BaaS routes are rooted at:

`/api/v1`

## Route Definition

Each route defines:

- route_id
- method
- path
- target_service
- target_operation
- authentication_required
- required_permission
- max_payload_bytes
- timeout_ms
- rate_limit_requests
- rate_limit_window_seconds
- enabled

## Request Envelope

A gateway request carries:

- request_id
- correlation_id
- method
- path
- content_length
- authenticated
- actor_id
- actor_type
- kernel_authorization_ref
- permission_evidence
- tenant identifiers
- safe metadata

Raw authorization headers, cookies, tokens, passwords, secret values, and raw
body payloads are not stored by the gateway control plane.

## Routing Rules

1. Route method and normalized path must match exactly.
2. Routes outside `/api/v1` are rejected.
3. Disabled routes fail closed.
4. Unknown routes return a safe NOT_FOUND error.
5. Authentication-required routes require authenticated identity evidence.
6. Permission-protected routes require Kernel authorization evidence and the
   required permission in permission evidence.
7. Request tenant identifiers remain subordinate to verified Kernel/BaaS
   context.

## Payload Limits

`content_length` must be an integer >= 0 and may not exceed the route limit.

P0 validates length metadata only. A production network adapter must enforce
streaming/body limits before buffering.

## Timeouts

Route timeout must be 1–120000 ms.

The gateway produces a downstream timeout budget but does not execute or kill
the downstream service itself.

## Rate Limiting

P0 provides an in-memory deterministic reference limiter keyed by:

- route_id
- organization_id
- actor_id

It is suitable for contract validation only.

Production distributed enforcement belongs to a dedicated provider/runtime
adapter and must preserve the same fail-closed contract.

## Safe Error Format

```json
{
  "code": "ERROR_CODE",
  "message": "Safe error message",
  "request_id": "request_identifier",
  "details": {}
}
```

Internal exceptions, tracebacks, secrets, raw provider errors, and request
payloads are not returned.

## Routing Output

A successful route resolution produces a `GatewayDispatchPlan` containing:

- route_id
- target_service
- target_operation
- request_id
- correlation_id
- timeout_ms
- organization_id
- workspace_id
- project_id
- environment_id
- actor_id
- actor_type
- kernel_authorization_ref
- audit_event
- log_context

The plan is metadata only and safe to hand to a future network/service adapter.
