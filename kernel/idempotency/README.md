# Idempotency

## Required Operations

Idempotency is mandatory for:

- Order submission
- Payment creation
- Payment confirmation
- Refund creation
- Inventory deduction
- Webhook processing
- Background jobs

## Record

Each idempotency record must contain:

- key
- organization_id
- operation
- request_hash
- status
- response_reference
- created_at
- expires_at

## Rule

The same key with a different request hash must be rejected.
