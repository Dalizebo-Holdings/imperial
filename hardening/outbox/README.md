# Transactional Outbox

## Flow

Validate
→ Begin Transaction
→ Domain Mutation
→ Audit Record
→ Outbox Event
→ Commit
→ Async Publisher
→ Subscriber

## Requirements

- Events written inside the same database transaction
- No publication before commit
- Idempotent publishers
- Delivery attempt tracking
- Retry support
- Dead-letter handling
- Correlation IDs
- Event versioning

## Initial Status

P0 for production hardening.
