# Loop OS Audit Adapter

## Purpose

The Loop OS Audit Adapter converts worker lifecycle events into sanitized,
tamper-evident audit records.

It records execution evidence. It does not authorize work and it does not
replace Algorithm OS, Pillars OS, or Dalizebo Kernel authorization.

## Accepted Worker Events

- `loop_os.job.claimed`
- `loop_os.job.started`
- `loop_os.job.completed`
- `loop_os.job.retry_pending`
- `loop_os.job.dead_lettered`
- `loop_os.job.authorization_denied`

## Required Event Fields

Every event must contain:

- event_type
- job_id
- correlation_id

Event-specific fields such as attempt, retry time, authorization reference,
error code, and status are preserved when present.

## Output Record

Each persisted audit record contains:

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

## Integrity

`record_hash` is a SHA-256 digest over the complete sanitized record body
excluding `record_hash` itself.

Every record stores the previous record hash, creating an append-only chain.

## Worker Integration

`persist_worker_result(...)` writes every structured event emitted by a
`WorkerResult` in order.

The final job state is not independently invented by the audit adapter; the
worker remains the source of lifecycle state.

## Verification

Verification recomputes every hash and validates every chain link.

Any modified event, removed intermediate record, malformed JSONL entry, or
broken previous-hash link fails verification.
