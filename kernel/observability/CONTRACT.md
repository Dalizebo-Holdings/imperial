# Kernel Observability Contract

## P0 Components

- Structured logs
- Metrics
- Health checks
- Readiness checks
- Error monitoring hooks
- Correlation IDs
- Trace context fields

## Structured Logging

Every log record contains:

- timestamp
- level
- event
- correlation_id
- organization_id when tenant-aware
- actor_id when available
- trace_id when available
- span_id when available
- fields

Sensitive values are recursively redacted.

Logs never replace Kernel audit records.

## Metrics

P0 supports provider-neutral:

- counters
- gauges
- timing observations

Metric names are validated and labels are bounded string metadata.

## Health

Health reports separate:

- liveness
- readiness

Liveness answers whether the Kernel process/runtime is operational.

Readiness answers whether declared required dependencies are ready to serve
traffic.

A failed optional dependency does not make readiness fail.

## Production Boundary

P0 exposes provider-neutral runtime contracts only.

OpenTelemetry exporters, metrics backends, log shipping, alert routing, and
external health dependencies are attached later without changing these
contracts.
