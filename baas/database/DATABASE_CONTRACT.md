# Database BaaS Runtime Contract

## Purpose

Database BaaS manages PostgreSQL database resources above the Dalizebo Kernel
persistence boundary.

P0 is a control-plane contract. It validates tenant scope, lifecycle,
connection policy, migration intent, backup linkage, and query observations.
It does not open PostgreSQL network connections.

## Managed Database Descriptor

Each database resource contains:

- database_id
- organization_id
- workspace_id
- project_id
- environment_id
- name
- engine
- engine_version
- dsn_ref
- schema
- state
- connection_policy
- backup_policy_ref
- created_at
- updated_at

`dsn_ref` is an opaque Kernel secret reference. Raw DSNs are forbidden.

## Lifecycle

`PROVISIONING → READY → SUSPENDED → READY`

Terminal:

`DECOMMISSIONED`

Allowed decommission transitions:

- PROVISIONING → DECOMMISSIONED
- READY → DECOMMISSIONED
- SUSPENDED → DECOMMISSIONED

## Connection Policy

- max_connections
- connect_timeout_seconds
- statement_timeout_ms
- idle_transaction_timeout_ms
- ssl_mode
- read_only

Production requires `ssl_mode = verify-full`.

## Tenant Rules

1. Database resources are bound to one Organization → Workspace → Project →
   Environment scope.
2. A BaaS request may manage only a database in the same tenant scope.
3. Every management operation requires a Kernel authorization reference.
4. Cross-tenant database management fails closed.
5. Client-provided tenant identifiers do not override verified BaaS/Kernel
   context.

## Migrations

Migration requests contain:

- migration_id
- database_id
- version
- checksum
- description
- transactional
- reversible
- rollback_reference
- requested_at

Rules:

- versions are positive
- checksum is SHA-256
- production migrations must be reversible where practical
- a non-reversible production migration must explicitly declare why no
  rollback reference exists
- migration execution belongs to the concrete PostgreSQL adapter
- P0 only validates and records deterministic intent

## Transactions

Multi-record state changes must execute inside the Kernel PostgreSQL transaction
boundary.

Database BaaS does not invent a competing transaction model.

## Backups and Restore

Every production database must reference a backup policy before entering READY.

Restore requests reference:

- database_id
- backup_reference
- target_environment_id
- requested_at

P0 validates restore intent. Actual restore execution remains a provider
operation backed by Kernel backup/recovery contracts.

## Query Observability

Query observations contain metadata only:

- database_id
- correlation_id
- operation
- duration_ms
- row_count
- success
- error_code

SQL text, bind values, credentials, and sensitive payloads are not persisted by
the P0 observation contract.
