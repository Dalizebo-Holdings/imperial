# Algorithm OS Audit Adapter

## Purpose

The Audit Adapter converts Algorithm OS decisions and plans into sanitized,
tamper-evident audit records.

It records planning and authorization-boundary evidence. It does not authorize
or execute side effects.

## Input

The primary input is the `audit_event` emitted by the Execution Planner.

Required fields:

- event_type
- decision_id
- decision_request_id
- correlation_id
- actor_id
- organization_id
- registry_version
- policy_version
- risk_class
- outcome

## Output

Each persisted record contains:

- audit_version
- event_id
- recorded_at
- event
- previous_hash
- record_hash

## Security

The adapter must redact secrets before persistence.

Sensitive key names include:

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

Redaction is recursive for nested dictionaries and lists.

## Integrity

`record_hash` is a SHA-256 digest over:

- audit version
- event ID
- recorded timestamp
- sanitized event
- previous record hash

The JSONL sink is append-only.

Each new record links to the previous record hash.

## Verification

The verifier recomputes every record hash and checks the hash chain.

Any malformed record, altered event, removed intermediate record, or broken
link fails verification.

## Boundary

Audit evidence does not imply authorization.

`APPROVED_FOR_AUTHORIZATION` still requires Dalizebo Kernel authorization
before any production side effect.
