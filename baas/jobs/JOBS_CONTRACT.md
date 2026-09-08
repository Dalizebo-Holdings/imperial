# BaaS Background Jobs Runtime Contract

## Purpose

Background Jobs BaaS provides the tenant-facing control plane for queued,
delayed, and scheduled work.

P0 validates job definitions, tenant scope, idempotency, execution bounds,
readiness, retry/dead-letter state, and Loop OS handoff metadata.

P0 does not implement a competing worker runtime. Production execution is
delegated to Loop OS through a future adapter that resolves authorization
evidence into the existing Loop OS `ExecutionAuthorization` contract.

## Job Definition

Each job definition contains:

- definition_id
- tenant scope
- job_type
- handler_ref
- timeout_seconds
- max_attempts
- queue_name
- enabled

P0 `handler_ref` types:

- `function://...`
- `internal://...`

## Submission Modes

- QUEUED
- DELAYED
- SCHEDULED

QUEUED jobs are immediately eligible.

DELAYED jobs require `available_at`.

SCHEDULED jobs require both:

- `schedule_expression`
- `available_at`

P0 validates schedule metadata only. A production scheduler adapter determines
future occurrences.

## Job Request

Each request contains:

- submission_id
- definition_id
- idempotency_key
- mode
- payload_metadata
- available_at
- schedule_expression
- requested_at

Raw credentials, tokens, secret values, or executable code are forbidden in
payload metadata.

## Idempotency

Job identity is deterministic for:

- organization_id
- definition_id
- idempotency_key
- canonical payload metadata

Submitting the same idempotency key with the same payload returns the same job.

Reusing the same idempotency key with different payload metadata fails closed.

## Execution Bounds

- timeout: 1–3600 seconds
- retries: 1–25 attempts
- retry delay: bounded exponential metadata, capped at 3600 seconds
- no infinite retries
- no unbounded execution

## Job State

- QUEUED
- DELAYED
- SCHEDULED
- DISPATCHED
- RETRY_PENDING
- COMPLETED
- DEAD_LETTER
- CANCELLED

Terminal:

- COMPLETED
- DEAD_LETTER
- CANCELLED

## Loop OS Handoff

A due job produces a `LoopDispatchPlan` containing:

- job_id
- job_type
- handler_ref
- attempt
- timeout_seconds
- tenant context
- correlation_id
- idempotency_key
- kernel_authorization_ref
- pillars_approval_ref
- payload_metadata
- audit_event
- log_context

The plan deliberately does not synthesize Loop OS authorization booleans.

The production handoff adapter must verify the supplied evidence and construct
Loop OS:

- `pillars_approved`
- `kernel_authorized`
- `authorization_ref`

before worker execution.

## Failure Handling

Execution failure records:

- stable error_code
- retry_at when attempts remain
- DEAD_LETTER when attempts are exhausted

Raw exception messages and tracebacks are not stored.

## Observability

Every job exposes safe status metadata:

- state
- attempt
- max_attempts
- available_at
- last_error_code
- correlation_id
- updated_at

Failed jobs remain visible.

## Safety

- Kernel authorization evidence is mandatory.
- Pillars approval evidence is mandatory before Loop OS handoff.
- Cross-tenant job access fails closed.
- Duplicate execution must be safe through idempotency.
- All execution is timeout-bounded.
- Retries are bounded.
- Infinite execution loops are prohibited.
