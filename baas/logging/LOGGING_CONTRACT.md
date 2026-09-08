# BaaS Logging Runtime Contract

## Authority Boundary

BaaS Logging reuses the Kernel Observability structured log contract.

Canonical Kernel fields:

- timestamp
- level
- event
- correlation_id
- organization_id when tenant-aware
- actor_id when available
- trace_id when available
- span_id when available
- fields

Kernel recursive redaction is authoritative.

## Log Stream Policy

Each tenant environment may register one policy:

- policy_id
- organization_id
- workspace_id
- project_id
- environment_id
- minimum_level
- retention_days
- max_fields_bytes
- enabled

P0 bounds:

- retention: 1–3650 days
- field payload: 256–65536 canonical JSON bytes

The policy is control-plane metadata. P0 does not claim physical deletion from
a production logging backend.

## Ingestion

A log ingestion request contains:

- source_service
- level
- event
- correlation_id
- actor_id
- trace_id
- span_id
- fields
- timestamp

Rules:

1. BaaS request context must use `service=logging`.
2. Kernel authorization evidence is mandatory.
3. Correlation ID must match the BaaS request context.
4. Organization ID is injected from verified request context.
5. Actor ID may not contradict request context.
6. Fields must be JSON-compatible and within policy size bounds.
7. Records below policy minimum level are deterministically dropped.
8. Accepted records are built by the Kernel structured logging sink.
9. Raw unredacted records are never retained by BaaS Logging.

## Levels

Ordered severity:

`DEBUG < INFO < WARNING < ERROR < CRITICAL`

## Query Contract

Queries are tenant-scoped to the verified Organization.

Optional filters:

- minimum_level
- source_service
- event_prefix
- actor_id
- correlation_id
- trace_id
- timestamp_from
- timestamp_to
- after_sequence

Query page size:

- 1–1000

Results are returned in ascending BaaS ingestion sequence.

## Query Projection

Each accepted record is projected as:

- sequence
- source_service
- timestamp
- level
- event
- correlation_id
- organization_id
- actor_id
- trace_id
- span_id
- fields

The record is already Kernel-redacted before it enters the BaaS query index.

## Retention

`retention_cutoff(policy, now)` calculates the oldest timestamp allowed by
policy.

P0 does not automatically delete production logs. A future durable log backend
adapter must enforce retention without changing this contract.

## Access Observability

Query operations return `access_log_context` containing:

- service=logging
- operation=logging.query
- request_id
- correlation_id
- organization_id
- selected_count

This is operational logging context only.

Sensitive or material actions still require Kernel Audit evidence separately.

## Production Boundary

Deferred adapters:

- OpenTelemetry/log exporter
- durable log index/search backend
- retention/deletion worker
- alert routing
- trace backend

No production exporter is implied by the P0 reference service.
