# BaaS Backups Runtime Contract

## Purpose

Backups BaaS is the tenant-facing backup and recovery control plane above the
Kernel Backup Contract.

P0 manages provider policy, tenant-scoped backup policy, automated-backup due
calculation, backup execution intents, backup evidence, restore-test planning,
restore verification, recovery trust, and restore execution plans.

P0 does not perform snapshots, database dumps, object copies, or restores.

## Authority Boundary

Kernel Backup remains authoritative for:

- production encryption requirement
- immutable production copy
- offsite production copy
- retention
- frequency
- RPO
- RTO
- restore-test interval
- restore verification semantics

BaaS Backups adds:

- Organization → Workspace → Project → Environment scope
- resource binding
- provider-neutral adapter metadata
- secret-reference credentials
- strict timezone-aware evidence
- strict opaque backup references
- restore-test staleness enforcement
- auditable backup/restore plans

## Resource Classes

P0 supports:

- DATABASE
- OBJECT_STORAGE
- KERNEL_STATE

## Provider Configuration

Each provider contains:

- provider_id
- adapter_ref
- credential_ref
- supports_encryption
- supports_immutable_copy
- supports_offsite_copy
- supports_restore
- enabled

Credentials are opaque `secret://`, `vault://`, or `kms://` references only.

A policy cannot demand a capability the provider does not support.

## Tenant Backup Policy

Each policy contains:

- policy_id
- tenant scope
- resource_class
- resource_ref
- environment_type
- provider_id
- encrypted
- retention_days
- frequency_minutes
- rpo_minutes
- rto_minutes
- immutable_copy
- offsite_copy
- restore_test_interval_days
- enabled
- metadata

Registration also creates the canonical Kernel `BackupPolicy`.

## Automated Backup Scheduling

`backup_due()` compares the latest successful backup completion timestamp with
policy `frequency_minutes`.

No prior successful backup means backup is immediately due.

P0 does not run a scheduler.

## Backup Execution Intent

A due/enabled policy produces a `BackupExecutionPlan` containing:

- backup_id
- policy_id
- resource_ref
- provider adapter reference
- provider credential reference
- encryption/immutable/offsite requirements
- retention
- RPO/RTO
- tenant context
- correlation ID
- Kernel authorization reference
- audit event

State:

`READY_FOR_BACKUP_ADAPTER`

No backup is claimed until provider evidence is recorded.

## Backup Evidence

Provider completion evidence contains:

- backup_id
- policy_id
- backup_reference
- checksum_sha256
- started_at
- completed_at
- encrypted
- immutable_copy
- offsite_copy
- success
- error_code

Rules:

- timestamps must be timezone-aware
- successful evidence must satisfy every policy/provider protection requirement
- checksum is mandatory on successful backup
- `backup_reference` must be opaque:
  - `backup://`
  - `snapshot://`
  - `object://`
  - `provider-backup://`
- raw credentials/provider response bodies are forbidden

## Restore Testing

A backup is not operationally trustworthy until restore has been tested.

`plan_restore_test()` produces adapter metadata only.

`record_restore_verification()`:

1. validates tenant/policy/backup linkage
2. requires timezone-aware `tested_at`
3. rejects secret-bearing notes
4. creates canonical Kernel `RestoreVerification`
5. records it through Kernel `BackupPolicyRegistry`

Successful verification requires checksum verification.

## Restore-Test Staleness

BaaS hardens the Kernel P0 trust check.

`trusted_for_recovery(policy_id, now)` requires:

- enabled policy
- latest Kernel restore verification exists
- verification succeeded
- checksum verified
- `tested_at + restore_test_interval_days >= now`

A stale restore test is not trusted for recovery.

## Restore Execution Plan

A restore plan is produced only when:

- policy is trusted for recovery
- provider supports restore
- backup evidence exists and succeeded
- backup belongs to the policy and tenant

State:

`READY_FOR_RESTORE_ADAPTER`

The plan contains metadata/reference material only.

## RPO / RTO

RPO and RTO are explicit policy constraints.

P0 validates policy and exposes them in execution/recovery plans.

Actual RPO/RTO achievement must be measured by production adapters and
operational monitoring; P0 does not claim the objectives were achieved merely
because a plan exists.

## Security

- `service=backups` is required.
- Kernel authorization evidence is mandatory.
- Cross-tenant backup/restore access fails closed.
- Provider credentials remain opaque references.
- Secret-bearing metadata/notes are rejected.
- Production policy requires encryption + immutable + offsite copies.
- No backup/restore provider network execution occurs in P0.
