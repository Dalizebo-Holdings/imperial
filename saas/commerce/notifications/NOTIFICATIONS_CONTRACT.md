# Commerce P0 — Notifications Contract

## Purpose

Commerce P0 Notifications produces post-commit notification intents from
business events.

P0 does not invent an email service or bypass BaaS Events/Webhooks.

## Delivery Boundary

Canonical path:

Committed Commerce Transaction
→ Kernel Outbox
→ BaaS Events
→ Subscriber
→ Webhook / Internal Function

Events are never published before commit.

Webhook consumers must assume duplicate delivery and remain idempotent.

## P0 Channels

- WEBHOOK
- INTERNAL

Email delivery remains deferred to the BaaS Email P1 capability.

## Notification Intent

A notification intent contains:

- notification_id
- event_type
- resource_type
- resource_id
- template_ref
- recipient_ref
- channel
- target_ref
- correlation_id
- tenant scope
- idempotency key

`recipient_ref` is a reference such as `customer://...`; raw customer email or
phone values are not placed into the notification control-plane record.

## State

`READY_FOR_POST_COMMIT_EVENTS_ADAPTER`

The plan is not a claim that delivery already happened.
