# Loop OS Queue Adapter

## Purpose

The Queue Adapter provides the P0 contract between Loop OS job state and a
future durable queue provider.

The P0 implementation is an in-memory reference adapter. It defines semantics;
it is not the production durability layer.

## Enqueue Rules

### New jobs

`CREATED → QUEUED`

The adapter:

- validates the job
- computes the deterministic job fingerprint
- rejects unsafe duplicate submissions
- transitions the job to `QUEUED`
- records queue availability time
- preserves correlation and idempotency identifiers

### Retry jobs

`RETRY_PENDING`

Retry jobs are queued for a future availability time but remain
`RETRY_PENDING` until a worker starts them.

The state machine therefore preserves:

`RETRY_PENDING → RUNNING`

and does not invent a `RETRY_PENDING → QUEUED` transition.

## Duplicate Handling

The queue uses both:

- `idempotency_key`
- deterministic job fingerprint

If an active or terminal job with the same idempotency identity already exists,
a duplicate submission is rejected rather than executed twice.

## Ordering

P0 uses:

1. earliest `available_at`
2. lowest insertion sequence

No priority scheduler is introduced in P0.

## Visibility

The adapter exposes:

- enqueue
- enqueue_retry
- claim_ready
- acknowledge
- release
- get
- list_entries

Production visibility timeouts and distributed leases belong to the provider
adapter implemented after the P0 contract is stable.
