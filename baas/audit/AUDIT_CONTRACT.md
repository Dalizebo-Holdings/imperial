# BaaS Audit Runtime Contract

## Authority Boundary

Kernel Audit is the source of truth.

Kernel records are append-only and hash chained:

- audit_version
- sequence
- event
- previous_hash
- record_hash

Audit BaaS must verify the complete supplied Kernel ledger before any query or
export.

## Required Event Fields

The Kernel event fields remain:

- audit_id
- organization_id
- actor_type
- actor_id
- action
- resource_type
- resource_id
- timestamp
- correlation_id
- metadata

## Query Contract

Audit queries are always scoped to the Organization from verified BaaS request
context.

Optional filters:

- actor_id
- action
- resource_type
- resource_id
- correlation_id
- timestamp_from
- timestamp_to
- after_sequence

Limits:

- query page size: 1–1000

Records are returned in ascending Kernel sequence order.

## Safe Projection

Query results expose:

- sequence
- record_hash
- audit_id
- actor_type
- actor_id
- action
- resource_type
- resource_id
- timestamp
- correlation_id
- metadata

Metadata is defensively redacted for sensitive keys.

The authoritative Kernel record itself is not rewritten.

## Export Contract

Exports are metadata packages, not a second ledger.

An export contains:

- export_id
- organization_id
- generated_at
- source_count
- source_last_hash
- selected_count
- selection_hash
- criteria
- projected_records
- access_audit_event

`selection_hash` is SHA-256 over the canonical projected-record list.

The source Kernel chain must be valid before export generation.

## Access Audit

Audit query/export operations are themselves sensitive actions.

Every successful access operation produces an `access_audit_event` suitable for
persistence through the Kernel audit path.

BaaS Audit does not directly append that event to an independent store.

## Security

- Kernel authorization evidence is mandatory.
- `service` must be `audit`.
- Cross-tenant records never appear in results.
- Invalid/tampered source ledger fails closed.
- Sensitive metadata is recursively redacted.
- No delete or mutation API exists in P0.
- No raw secrets, tokens, credentials, or payment authentication data may be
  surfaced through projections.
