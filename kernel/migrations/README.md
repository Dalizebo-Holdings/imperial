# Kernel Migration Framework

## Purpose

The migration framework provides deterministic, ordered, checksummed PostgreSQL
schema evolution.

## Migration Definition

Each migration defines:

- version
- name
- path
- checksum
- transactional

## Rules

1. Versions are positive, strictly increasing integers.
2. Duplicate versions are rejected.
3. Duplicate names are rejected.
4. Applied migration checksums are immutable.
5. Checksum drift fails closed.
6. Missing historical migrations fail closed.
7. New migrations are applied in ascending version order.
8. P0 migrations are transactional.
9. Migration files must not contain database passwords, API keys, tokens, or
   secret values.
10. Rollback is not assumed to be safe. Recovery uses forward migrations and
    tested backups unless a migration explicitly defines a reversible procedure.

## Migration Ledger

Production PostgreSQL maintains `kernel.schema_migrations` with:

- version
- name
- checksum
- applied_at

The P0 runtime produces the deterministic plan and validates history. A concrete
database runner can execute the plan later without changing migration identity.
