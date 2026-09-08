# Kernel Idempotency Runtime

## Purpose

The Kernel Idempotency Runtime enforces duplicate-safe operations and the
existing idempotency record contract.

## Record

Every record contains:

- key
- organization_id
- operation
- request_hash
- status
- response_reference
- created_at
- expires_at

## Status

- IN_PROGRESS
- COMPLETED
- FAILED

## Rules

1. Idempotency identity is scoped by organization, operation, and key.
2. The first request creates an `IN_PROGRESS` record.
3. Repeating the same identity with the same request hash returns the existing
   record.
4. Reusing the same identity with a different request hash is rejected.
5. Completion records a response reference rather than embedding arbitrary
   response bodies.
6. Expired records may be replaced by a new operation.
7. Request hashes are generated from canonical JSON.
8. Raw credentials or secret material must not be present in hashed request
   payloads.
