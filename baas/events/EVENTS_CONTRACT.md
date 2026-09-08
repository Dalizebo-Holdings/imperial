# BaaS Events Runtime Contract

## Purpose

Events BaaS provides tenant-scoped domain event publication, subscriptions,
transactional outbox handoff, and delivery tracking above the Kernel event
contract.

P0 is a control-plane and delivery-planning layer. It does not claim a
production message broker.

## Canonical Delivery Model

Database Transaction
→ Transactional Outbox
→ Commit
→ Event Worker
→ Subscriber

Domain events must never be published before transaction commit.

## Event Envelope

Events preserve the Kernel envelope:

- event_id
- event_type
- event_version
- organization_id
- workspace_id
- project_id
- environment_id
- resource_type
- resource_id
- occurred_at
- correlation_id
- actor_type
- actor_id
- payload

## Outbox Handoff

Events BaaS accepts only outbox records in `COMMITTED` state.

Rejected:

- staged/uncommitted events
- rolled-back events
- already-published duplicate publication attempts with conflicting content
- malformed tenant/event envelopes

## Subscription Model

A subscription contains:

- subscription_id
- tenant scope
- event_pattern
- target_type
- target_ref
- max_attempts
- enabled

P0 target types:

- FUNCTION
- WEBHOOK
- INTERNAL

Event patterns support:

- exact match: `order.created`
- namespace wildcard: `order.*`
- all events: `*`

## Delivery Tracking

Delivery states:

- PENDING
- DELIVERED
- RETRY_PENDING
- DEAD_LETTER

Every event/subscription pair has one deterministic `delivery_id`.

Retries are bounded by `max_attempts`.

## Delivery Plan

A committed event matched to an enabled subscription produces metadata for a
future worker/provider adapter:

- delivery_id
- event_id
- subscription_id
- target_type
- target_ref
- attempt
- tenant context
- correlation_id
- audit_event
- log_context

The P0 runtime does not perform network delivery.

## Idempotency

The same event/subscription pair always maps to the same deterministic delivery
identity.

A delivered record cannot be delivered again.

## Security

- Kernel authorization evidence is required for management/publication actions.
- Cross-tenant subscription/event access fails closed.
- Secret-bearing payload keys are rejected.
- Provider credentials are references only.
- Raw delivery response bodies are not stored.
