# BaaS Usage Metering Runtime Contract

## Purpose

Usage Metering BaaS records immutable tenant-attributed platform usage and
produces deterministic aggregates suitable for later rating, billing, invoice,
and reconciliation services.

P0 implements the metering boundary only. It does not price usage, create
invoices, charge payment methods, or mutate subscription state.

## Initial Metered Resources

The canonical P0 resource categories are:

- API requests
- Database storage
- Database compute
- Object storage
- Bandwidth
- Function executions
- Realtime connections
- AI usage
- Vector operations
- Messaging usage

Internal metric keys:

- `api_requests`
- `database_storage`
- `database_compute`
- `object_storage`
- `bandwidth`
- `function_executions`
- `realtime_connections`
- `ai_usage`
- `vector_operations`
- `messaging_usage`

Units remain explicit on every record. Aggregation never combines different
units.

## Usage Event

Every usage event contains:

- submission_id
- producer
- idempotency_key
- metric
- unit
- quantity
- occurred_at
- dimensions
- source_ref

Tenant scope comes only from verified BaaS request context:

Organization
→ Workspace
→ Project
→ Environment

## Quantity

Quantities are canonical decimal strings.

Rules:

- finite
- non-negative
- no binary floating-point storage
- maximum 18 fractional digits
- normalized before hashing/aggregation

Examples:

- `1`
- `1024`
- `0.25`
- `3600.000001`

## Idempotent Ingestion

Idempotency scope:

- organization_id
- environment_id
- producer
- idempotency_key

Same key + same canonical event returns the existing immutable usage record.

Same key + different canonical event fails closed.

## Immutable Raw Usage

Accepted records contain:

- usage_id
- tenant scope
- producer
- metric
- unit
- canonical quantity
- occurred_at
- dimensions
- source_ref
- correlation_id
- actor_id
- kernel_authorization_ref
- record_hash
- ingested_at

No update or delete API exists in P0.

`record_hash` is SHA-256 over the canonical record body.

## Dimensions

Dimensions are JSON-compatible, bounded metadata for reconciliation and
aggregation.

Sensitive keys such as credentials, tokens, passwords, secrets, cookies, card
authentication data, or provider credentials are rejected rather than stored.

## Auditable Ingestion

Every accepted raw record returns an `audit_event` suitable for Kernel Audit.

The Audit event does not contain raw secret material or pricing decisions.

## Aggregation

Aggregation criteria:

- tenant scope
- metric
- unit
- period_start
- period_end

The period is half-open:

`period_start <= occurred_at < period_end`

Aggregate output contains:

- aggregate_id
- metric
- unit
- total_quantity
- event_count
- period_start
- period_end
- source_hash
- source_usage_ids
- generated_at
- audit_event

`source_hash` is SHA-256 over ordered source record hashes.

## Reconciliation

`reconcile()` recomputes the selected aggregate from immutable raw usage and
compares:

- total_quantity
- event_count
- source_hash
- source_usage_ids

Any mismatch fails reconciliation.

## Separation from Billing

Canonical pipeline:

Platform Usage
→ Metering Event
→ Aggregation
→ Rating
→ Billing
→ Invoice
→ Reconciliation

P0 Usage Metering implements:

Platform Usage
→ Metering Event
→ Aggregation
→ Metering Reconciliation

Rating, pricing versioning, subscription billing, invoices, credits, payment
retries, and entitlements remain the Billing BaaS responsibility.

## Security

- `service=usage_metering` is required.
- Kernel authorization evidence is mandatory.
- Tenant attribution is taken from verified request context.
- Cross-tenant raw-record access fails closed.
- Raw usage records are immutable.
- Secret-bearing dimensions are rejected.
- Usage record identity is deterministic and idempotent.
