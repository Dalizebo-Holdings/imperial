# Integrations OS Provider Adapter Interface

## Purpose

The Provider Adapter Interface defines the boundary between the provider-neutral
Integrations OS runtime and future concrete external-provider implementations.

P0 defines the interface and validation semantics only. It performs no network
calls.

## Adapter Identity

Every adapter declares:

- connector_id
- connector_version
- adapter_version
- supported_operations

## Input

A provider adapter receives:

- `PreparedConnectorCall`
- `CredentialContext`

The prepared call has already passed:

- Pillars OS approval
- Dalizebo Kernel authorization
- connector registration
- version compatibility
- operation validation
- scope validation
- timeout validation
- circuit-breaker validation

## Required Methods

- `validate_context(...)`
- `execute(...)`
- `health_check(...)`

`execute(...)` is the future provider boundary. Concrete production adapters
must implement it explicitly.

The base adapter never performs a provider call.

## Result Contract

Provider adapters return the existing normalized `ConnectorResponse` contract.

No adapter may return raw secrets in:

- response data
- normalized errors
- audit events
- rate-limit metadata

## Error Boundary

Adapter exceptions are normalized to stable Integrations OS error categories.

P0 provides a safe normalization helper without exposing exception tracebacks.

## Loop OS Boundary

Provider retries are not unbounded inside adapters.

The adapter marks an error as retryable according to the connector definition;
Loop OS owns retry scheduling, attempt bounds, timeout state, and dead-letter
execution.

## Security Boundary

Credential references are metadata handles.

Future production adapters must retrieve secret material only from an approved
secret-management boundary at the moment of provider execution and must never
persist that material in Integrations OS runtime objects.
