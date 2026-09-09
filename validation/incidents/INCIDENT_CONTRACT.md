# Phase 7 — Incident Evidence Contract

## Required Production Incident Evidence

Every incident records:

- incident ID
- severity
- start time
- detection source
- owner
- affected tenants
- affected services
- customer impact
- root cause
- resolution
- recovery validation
- corrective actions

Because root cause/resolution/recovery/corrective actions may not be known at
incident start, P0 enforces them before RESOLVED state.

## Critical Ownership

No P0 incident may exist without an assigned owner.

## Lifecycle

OPEN → MITIGATED → RESOLVED

OPEN → RESOLVED is allowed when mitigation and resolution are simultaneous.

RESOLVED is terminal.

## Tenant Isolation

Incident evidence explicitly records whether a material tenant-isolation defect
occurred.

Any unresolved material tenant-isolation defect blocks the derived operational
readiness summary.

## Recovery

RESOLVED requires:

- root cause
- resolution
- recovery validation
- at least one corrective action
- resolution evidence reference

## Integrity

- timestamps are timezone-aware
- affected tenants use opaque `organization://...` references
- owner uses `user://...` or `service://...`
- same incident ID + changed creation evidence fails closed
- updates are explicit evidence-backed transitions
