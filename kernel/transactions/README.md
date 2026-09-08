# Kernel Transaction Primitives

## Purpose

The P0 transaction primitive models the Kernel atomicity contract before the
PostgreSQL adapter is implemented.

It is a reference transaction boundary, not a substitute for a production
database transaction.

## Lifecycle

`NEW → ACTIVE → COMMITTED`

or:

`NEW → ACTIVE → ROLLED_BACK`

Terminal transactions cannot be reused.

## Atomic Commit Contract

A transaction may stage:

- resource mutations
- audit records
- transactional outbox events

Nothing becomes visible in the backing store before commit.

Commit applies the complete staged state atomically to the reference backend.

Rollback applies nothing.

## Transactional Outbox

The required order is preserved:

Validate
→ Begin Transaction
→ Change State
→ Write Audit Record
→ Write Event to Outbox
→ Commit
→ Publish Asynchronously

P0 does not publish events.

It only exposes committed outbox records as eligible for a future asynchronous
publisher.

## Production Boundary

The later PostgreSQL implementation must preserve these semantics with one
database transaction covering business state, audit evidence, and outbox rows.
