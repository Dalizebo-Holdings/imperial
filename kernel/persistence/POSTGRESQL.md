# Kernel PostgreSQL Persistence Boundary

## Purpose

The PostgreSQL Persistence Boundary defines the Kernel's relational persistence
contract without embedding credentials or coupling domain logic to one driver.

P0 defines configuration, tenant session context, transaction semantics, and
baseline relational requirements. It does not open a network connection.

## Configuration

Required:

- dsn_ref
- environment_type
- application_name
- schema
- ssl_mode
- connect_timeout_seconds
- statement_timeout_ms
- idle_transaction_timeout_ms

`dsn_ref` must be an opaque secret reference. Raw PostgreSQL URLs with embedded
credentials are not accepted by the Kernel runtime contract.

## Production Requirements

Production requires:

- `ssl_mode = verify-full`
- positive connection and statement timeouts
- explicit application name
- secret reference based DSN resolution

## Tenant Session Context

Every tenant-aware transaction carries:

- organization_id
- workspace_id
- project_id
- environment_id
- actor_id
- correlation_id

The database adapter must set transaction-local tenant context before executing
tenant-aware SQL.

## Transaction Boundary

The adapter contract is:

1. BEGIN
2. apply transaction-local tenant/correlation context
3. execute business mutations
4. write audit evidence
5. write transactional outbox rows
6. COMMIT
7. publish asynchronously after commit

Rollback makes no staged mutation visible.

## Row-Level Security

P0 creates tenant-bearing columns and database indexes required for later RLS
policies.

RLS policy rollout must be explicit and tested before production enforcement;
the Kernel must never trust client-supplied tenant IDs.
