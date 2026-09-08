# Integrations OS Audit Adapter

## Purpose

The Integration Audit Adapter persists sanitized, tamper-evident audit evidence
for Integrations OS connector activity.

It records connector preparation and normalized provider outcomes. It does not
authorize or execute external side effects.

## Accepted Events

P0 accepts structured events with:

- event_type
- request_id
- connector_id
- correlation_id

Supported event families include:

- integrations_os.connector.prepared
- integrations_os.connector.completed
- integrations_os.connector.error
- integrations_os.connector.authorization_denied
- integrations_os.connector.circuit_open

## Record Format

Each persisted record contains:

- audit_version
- event_id
- recorded_at
- event
- previous_hash
- record_hash

## Secret Redaction

Sensitive keys are recursively redacted before persistence, including:

- authorization
- access_token
- refresh_token
- api_key
- password
- secret
- client_secret
- private_key
- cookie
- session_token
- webhook_secret
- credential_value

Credential references such as `secret://...` are metadata handles and may be
retained when necessary for traceability. Raw credential values must never be
persisted.

## Integrity

Every record is SHA-256 hashed and linked to the prior record hash.

The JSONL sink is append-only.

Verification recomputes the full chain and fails on modified records, removed
intermediate records, malformed JSONL, or broken hash links.

## Runtime Integration

The adapter may persist:

- prepared-call audit events
- `ConnectorResponse.audit_event`
- normalized provider error events

The normalized runtime remains the source of connector state.

## Boundary

Audit evidence never implies execution authorization.

External side effects continue to require:

Algorithm OS planning
→ Pillars OS approval
→ Dalizebo Kernel authorization
→ bounded Loop OS execution
→ registered Integrations OS provider adapter
