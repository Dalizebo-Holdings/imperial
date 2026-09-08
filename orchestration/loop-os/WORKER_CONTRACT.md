# Loop OS Worker Execution Contract

## Purpose

The Worker Execution Contract defines how Loop OS may invoke a registered job
handler after queue claim and authorization checks.

## Authorization Boundary

A worker may invoke a handler only when all of the following are true:

- `pillars_approved == true`
- `kernel_authorized == true`
- the job has a registered handler
- the job is in an executable state
- another retry attempt remains when required

If either policy or Kernel authorization is absent, the worker does not invoke
the handler.

## Execution Path

For a newly queued job:

`QUEUED → RUNNING → COMPLETED`

For a retry:

`RETRY_PENDING → RUNNING → COMPLETED`

Failure:

`RUNNING → FAILED → RETRY_PENDING`

Exhausted failure:

`RUNNING → FAILED → DEAD_LETTERED`

## Handler Contract

A handler receives a validated `LoopJob`.

A successful return value becomes `job.result`.

An exception is converted to a stable error code and enters bounded retry logic.

P0 does not expose exception tracebacks or secrets through the job result.

## Timeout Boundary

The worker contract preserves the job timeout value and uses Loop OS timeout
evaluation semantics.

P0 does not forcibly terminate arbitrary Python handlers. Production worker
process isolation and hard cancellation belong to the durable worker runtime.

## Audit Boundary

The worker emits structured execution events suitable for the pending
Loop OS Audit Adapter:

- loop_os.job.claimed
- loop_os.job.started
- loop_os.job.completed
- loop_os.job.retry_pending
- loop_os.job.dead_lettered
- loop_os.job.authorization_denied

## Safety

The worker must not bypass Algorithm OS, Pillars OS, or Dalizebo Kernel
authorization.
