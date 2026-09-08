# Kernel Backup Contract

## Purpose

The Kernel Backup Contract defines recovery requirements for persistent Kernel
state without binding Phase 4 P0 to a specific database or storage provider.

P0 validates backup policy and recovery metadata. It does not perform backups.

## Backup Policy

Each policy defines:

- policy_id
- resource_class
- environment_type
- encrypted
- retention_days
- frequency_minutes
- rpo_minutes
- rto_minutes
- immutable_copy
- offsite_copy
- restore_test_interval_days
- enabled

## Required P0 Rules

- Production backups must be encrypted.
- Production backups require an immutable copy.
- Production backups require an offsite copy.
- Retention, frequency, RPO, RTO, and restore-test interval must be positive.
- RPO may not exceed the backup frequency.
- Restore verification must be explicitly tracked.
- A backup is not considered operationally trustworthy until restoration has
  been tested according to policy.
- Backup metadata must not contain credentials.

## Recovery Evidence

A restore verification record contains:

- verification_id
- policy_id
- backup_reference
- tested_at
- success
- restored_resource_reference
- checksum_verified
- notes

## Production Boundary

Concrete PostgreSQL, object-storage, snapshot, PITR, encryption-key, and
cross-region implementations come later.

Those implementations must preserve this contract and produce auditable
recovery evidence.
