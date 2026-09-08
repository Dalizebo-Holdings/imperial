# Kernel Shared Identifiers

## Purpose

Kernel shared identifiers provide globally unique, stable, non-sequential
references that are safe to use in persistence, logs, audit records, events,
and idempotent retries.

## Identifier Forms

### New Resource Identifier

Used when a genuinely new resource is created.

Format:

`<prefix>_<uuid4hex>`

### Retry-Stable Identifier

Used when the same logical operation must reproduce the same resource
identifier across retries.

Inputs:

- namespace
- organization_id
- operation
- idempotency_key

Format:

`<prefix>_<sha256-prefix>`

## Rules

- Prefixes are lowercase slug-like identifiers.
- IDs contain no credentials or personal data.
- Retry-stable IDs are organization-scoped.
- IDs are non-sequential.
- Identifiers are safe for event references and structured logs.
