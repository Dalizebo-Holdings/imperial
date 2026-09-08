# Webhook Reliability

## Delivery Lifecycle

PENDING
→ DELIVERING
→ DELIVERED

Failure:

DELIVERING
→ RETRY_PENDING
→ DELIVERING

Terminal:

RETRY_PENDING
→ DEAD_LETTERED

## Requirements

- Signed payloads
- Unique delivery IDs
- Request timeout
- Exponential backoff
- Maximum retry count
- Replay
- Dead-letter queue
- Delivery logs
- Secret rotation
- Idempotency expectations

## Target

At least 99% of webhook deliveries must eventually be delivered or explicitly dead-lettered.
