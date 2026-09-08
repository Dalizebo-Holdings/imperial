# Loop OS Runtime Schema

## Purpose

The Runtime Schema defines the canonical P0 job model consumed by Loop OS.

It preserves the required fields already declared in `EXECUTION_MODEL.md` and
adds explicit validation rules needed for deterministic state transitions.

## Required Fields

- job_id
- organization_id
- workflow_id
- job_type
- status
- attempt
- max_attempts
- scheduled_at
- started_at
- completed_at
- timeout
- idempotency_key
- correlation_id
- payload
- result
- error_code

## Status Values

- CREATED
- QUEUED
- RUNNING
- COMPLETED
- FAILED
- RETRY_PENDING
- DEAD_LETTERED

## Invariants

1. `attempt` is never negative.
2. `max_attempts` must be at least 1.
3. `attempt` may never exceed `max_attempts`.
4. `timeout` must be a positive integer number of seconds.
5. `job_id`, `organization_id`, `workflow_id`, `job_type`,
   `idempotency_key`, and `correlation_id` must be non-empty.
6. Terminal statuses are `COMPLETED` and `DEAD_LETTERED`.
7. A terminal job may not transition again.
8. Payload and result must be JSON-compatible structures.
9. The schema stores no credentials by design; secrets belong in approved
   secret-management and connector layers.

## Idempotency

P0 exposes the idempotency key as part of every job and provides a deterministic
job fingerprint that can be used by the later queue/worker implementation to
detect duplicate submissions safely.
