# Audit BaaS

## Purpose

Audit BaaS exposes tenant-scoped verification, query, and export access over
authoritative Kernel audit evidence.

It does not create a competing audit ledger.

## Responsibilities

- Verify Kernel audit evidence before reads/exports
- Tenant-scoped audit queries
- Correlation/resource/action filtering
- Deterministic pagination
- Tamper-evident export manifests
- Access audit planning
- Safe metadata projection

## Rules

- Kernel audit persistence remains authoritative.
- Application logs are never substituted for audit records.
- Cross-tenant audit access fails closed.
- Invalid Kernel audit chains fail closed.
- Audit records are never modified or deleted by BaaS Audit.
- Query/export access itself produces Kernel audit evidence metadata.
