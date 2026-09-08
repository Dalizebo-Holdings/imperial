# Integrations OS Runtime Contract

## Purpose

The Runtime Contract defines provider-neutral request, response, error,
authorization, and execution-preparation semantics for Integrations OS.

P0 validates and prepares external operations but does not perform network
calls.

## Request Envelope

Required fields:

- request_id
- connector_id
- connector_version
- operation
- organization_id
- correlation_id
- idempotency_key
- auth_method
- credential_ref
- payload

Optional fields:

- permission_scopes
- timeout_seconds
- metadata

## Authorization Boundary

A connector request may be marked `READY_FOR_ADAPTER_EXECUTION` only when:

- Pillars OS approval is present.
- Dalizebo Kernel authorization is present.
- Connector is registered and enabled.
- Connector version is compatible.
- Operation is supported.
- Authentication method is supported.
- Required credential reference is present.
- Requested scopes are within connector-declared scopes.
- Timeout is positive and does not exceed the connector maximum.
- Payload is JSON-compatible.
- Required idempotency key is present.

P0 does not perform the provider call.

## Credential Rule

`credential_ref` is an opaque reference to future credential storage.

Raw API keys, passwords, OAuth access tokens, webhook secrets, private keys,
or session tokens must not be embedded in runtime requests.

## Response Envelope

A normalized connector response defines:

- request_id
- connector_id
- correlation_id
- status
- provider_status
- data
- error
- retryable
- rate_limit
- audit_event

Allowed status values:

- SUCCESS
- ERROR
- RATE_LIMITED
- AUTHORIZATION_REQUIRED
- CIRCUIT_OPEN
- SAFE_FAILURE

## Error Contract

Normalized errors define:

- code
- message
- provider_code
- retryable
- category

P0 error messages must not expose credentials or secret material.

## Circuit Breaker Contract

State values:

- CLOSED
- OPEN
- HALF_OPEN

The runtime model defines state and thresholds. Actual distributed circuit
state storage belongs to the provider execution layer.

## Loop OS Boundary

Retry and dead-letter execution is delegated to Loop OS.

Integrations OS declares retryability, timeout, idempotency, and error
classification; Loop OS owns bounded scheduling and execution state.
