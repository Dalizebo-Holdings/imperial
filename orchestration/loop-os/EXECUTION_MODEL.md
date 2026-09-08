# Loop OS Execution Model

## Job Lifecycle

CREATED
→ QUEUED
→ RUNNING
→ COMPLETED

Failure path:

RUNNING
→ FAILED
→ RETRY_PENDING
→ RUNNING

Terminal failure:

FAILED
→ DEAD_LETTERED

## Required Job Fields

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

## Retry Strategy

- Exponential backoff
- Maximum retry count
- Provider-specific retry policy
- Dead-letter queue after exhaustion
