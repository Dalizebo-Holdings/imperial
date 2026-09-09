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

## Connect-Time Network Policy

Status: IMPLEMENTED

Before each outbound connection, the delivery adapter must resolve the endpoint
hostname through `OutboundWebhookNetworkPolicy.resolve_for_connection`. Every
resolved address must be globally routable and non-multicast. The adapter must
then verify the connected peer with `authorize_connected_peer` so a second DNS
lookup or rebinding cannot redirect delivery outside the authorized address
set.

The policy does not perform network delivery and does not weaken the existing
HTTPS-only endpoint contract.
