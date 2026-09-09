# Phase 7 — Pilot Support Evidence Contract

## Severity

- P0 — critical outage, security incident, cross-tenant exposure, or data-loss risk
- P1 — major business workflow unavailable
- P2 — degraded functionality with workaround
- P3 — minor defect or usability issue

## Required Ticket Fields

- merchant reference
- organization ID
- severity
- product
- environment
- description
- correlation ID
- owner reference
- resolution

Resolution may remain pending while the ticket is OPEN, but a ticket cannot move
to RESOLVED without a resolution and resolution evidence.

## P1 Response Target

P1 first response must occur within one business day.

The P0 runtime uses weekday business days (Monday–Friday) because the canonical
source does not define business hours or a holiday calendar. Holiday-specific
SLA policy remains an operational extension.

## Lifecycle

OPEN → IN_PROGRESS → RESOLVED

OPEN → RESOLVED is allowed for immediately resolved cases.

RESOLVED is terminal.

## Evidence

Response and resolution updates require `evidence://` references.

The registry derives:

- ticket counts by severity
- resolved/open counts
- P1 first-response compliance
- support intervention evidence digest
