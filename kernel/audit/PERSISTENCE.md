# Kernel Audit Persistence

## Purpose

Kernel Audit Persistence provides durable, tamper-evident evidence for
sensitive or material Kernel actions.

Application logs are not audit records.

## Required Audit Fields

Every audit event contains:

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

## Persistence Record

The persistence layer wraps the audit event with:

- audit_version
- sequence
- previous_hash
- record_hash

## Rules

1. Required audit fields must be present.
2. Sensitive metadata is recursively redacted before persistence.
3. Records are append-only.
4. Every record links to the prior record hash.
5. Verification recomputes every hash and chain link.
6. Altered, removed, malformed, or reordered records fail verification.
7. Application logs never substitute for this ledger.

## Transaction Boundary

For atomic business operations, audit evidence must be staged in the same
transaction as business state and outbox events.

This adapter persists committed audit evidence; it does not weaken the existing
transactional atomicity contract.
