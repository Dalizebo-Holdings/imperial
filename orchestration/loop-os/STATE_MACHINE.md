# Loop OS State Machine

## Purpose

The P0 State Machine implements the lifecycle already defined by Loop OS:

`CREATED → QUEUED → RUNNING → COMPLETED`

Failure path:

`RUNNING → FAILED → RETRY_PENDING → RUNNING`

Terminal failure:

`FAILED → DEAD_LETTERED`

## Allowed Transitions

- CREATED → QUEUED
- QUEUED → RUNNING
- RUNNING → COMPLETED
- RUNNING → FAILED
- FAILED → RETRY_PENDING
- FAILED → DEAD_LETTERED
- RETRY_PENDING → RUNNING

Any other transition is rejected.

## Retry Rules

- Retries are bounded by `max_attempts`.
- Starting a RUNNING attempt increments `attempt`.
- A FAILED job may enter RETRY_PENDING only when another attempt remains.
- A FAILED job with exhausted attempts must transition to DEAD_LETTERED.
- Exponential backoff is deterministic from the attempt number and configured
  base/cap values.

## Timeout Rules

Every job has a positive timeout in seconds.

The runtime exposes timeout evaluation but does not kill processes in P0.
Actual cancellation/worker enforcement belongs to the worker runtime.

## Side-Effect Boundary

The state machine tracks job execution state only.

It does not bypass Algorithm OS planning, Pillars OS policy evaluation, or
Dalizebo Kernel authorization.
