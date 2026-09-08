# Logging BaaS

## Purpose

Logging BaaS exposes tenant-scoped structured-log ingestion and query services
while preserving the Kernel Observability logging contract.

It does not define a competing log format and it never replaces Kernel Audit.

## Responsibilities

- Tenant log-stream policy
- Structured log ingestion through Kernel logging
- Correlation/trace propagation
- Safe bounded fields
- Tenant-scoped log queries
- Deterministic pagination
- Retention metadata
- Log access observability

## Rules

- Kernel Structured Logging remains the canonical record shape.
- Correlation IDs are mandatory.
- Tenant-aware BaaS logs require `organization_id`.
- Sensitive fields are redacted by Kernel logging before storage/query.
- Cross-tenant log access fails closed.
- Logs are operational telemetry, not durable audit evidence.
- Production log shipping/indexing is a deferred adapter.
