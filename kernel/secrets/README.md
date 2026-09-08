# Kernel Secret Reference Boundary

## Purpose

The Kernel Secret Reference Boundary allows services to reference secrets
without storing raw secret material in Kernel runtime objects, logs, audit
records, configuration documents, or source code.

P0 models references and metadata only. It does not implement a secret vault.

## Reference Format

Allowed opaque reference schemes:

- `secret://...`
- `vault://...`
- `kms://...`

## Secret Descriptor

A descriptor contains:

- secret_ref
- organization_id
- purpose
- owner
- version
- environment_id
- allowed_consumers
- rotation_required
- enabled
- metadata

## Rules

1. Raw secret values are never stored.
2. Secret references are tenant- and environment-scoped.
3. Consumers must be explicitly allowlisted.
4. Disabled references fail closed.
5. Rotation requirement is metadata, not an automatic secret rotation engine.
6. Metadata containing secret-bearing field names is rejected.
7. Logs and audit records may retain opaque references when needed for
   traceability, but never resolved values.
8. Production secret retrieval belongs to an approved external secret manager.

## Runtime Output

Resolution returns a `SecretContext` containing only:

- secret_ref
- organization_id
- environment_id
- purpose
- consumer
- descriptor_version

No secret value is returned.
