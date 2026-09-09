# BaaS Webhooks Runtime Contract

## Purpose

Webhooks BaaS converts approved event deliveries into tenant-scoped,
cryptographically signed HTTPS delivery plans.

P0 provides endpoint registration, signing metadata, deterministic delivery
identity, bounded retries, timeout policy, status tracking, replay metadata,
dead-letter handling, and signing-secret rotation state.

P0 does not perform outbound HTTP requests.

## Endpoint Model

Each endpoint contains:

- endpoint_id
- tenant scope
- url
- event_patterns
- signing_secret_ref
- signing_secret_version
- timeout_seconds
- max_attempts
- enabled

Security rules:

- HTTPS is mandatory.
- URL userinfo is forbidden.
- Literal loopback/private/link-local/reserved/multicast addresses are rejected.
- Production adapters must still defend against DNS rebinding and enforce
  outbound network policy at connect time.
- Phase 8 adapters must use the connect-time network policy to resolve only
  globally routable, non-multicast addresses and pin the connected peer to that
  authorized resolution.
- Signing secrets are stored as opaque `secret://`, `vault://`, or `kms://`
  references only.

## Signed Payload Contract

Delivery signing uses:

`HMAC-SHA256(secret, timestamp + "." + raw_body)`

Headers:

- `X-Dalizebo-Webhook-Id`
- `X-Dalizebo-Webhook-Timestamp`
- `X-Dalizebo-Webhook-Signature`
- `X-Dalizebo-Webhook-Secret-Version`

The raw signing secret is transient input to the signing function and is never
stored in endpoint or delivery records.

## Delivery States

- PENDING
- DELIVERED
- RETRY_PENDING
- DEAD_LETTER

Retries are bounded by endpoint `max_attempts`.

## Delivery Identity

The initial delivery ID is deterministic for:

- event_id
- endpoint_id

Consumers must assume duplicate delivery and implement idempotency using the
delivery ID and their own processed-event ledger.

## Replay

A replay creates a new delivery ID linked to the original delivery.

Replay metadata contains:

- replay_of
- replay_sequence
- replay_reason

Replay does not erase or mutate the original delivery record.

## Secret Rotation

Endpoint signing-secret rotation increments `signing_secret_version` and
replaces the secret reference.

Raw secrets never enter endpoint state.

## Delivery Plan

A delivery plan contains:

- delivery_id
- endpoint_id
- event_id
- url
- timeout_seconds
- attempt
- signing_secret_ref
- signing_secret_version
- tenant context
- correlation_id
- audit_event
- log_context

The plan remains metadata-only until a future outbound HTTP adapter resolves the
secret reference, signs the body, and sends the HTTPS request.

## Response Tracking

P0 records safe metadata only:

- HTTP status code
- stable error code
- delivered/retry/dead-letter state

Raw response bodies, headers, cookies, credentials, and provider traces are not
stored.
