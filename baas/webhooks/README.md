# Webhooks BaaS

## Requirements

- Signed payloads
- Delivery IDs
- Retry policy
- Timeout
- Delivery status
- Replay
- Dead-letter handling
- Secret rotation

## Rule

Consumers must assume duplicate delivery and implement idempotency.
