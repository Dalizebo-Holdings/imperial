# Phase 6 — Commerce + POS MVP Acceptance & Integration Closure

## Purpose

This gate closes Phase 6 only when the repository demonstrates the formal
`saas/MVP_ACCEPTANCE.md` criteria across Commerce, POS, and the shared platform.

A status flag alone is insufficient.

## Acceptance Model

### Commerce

| MVP criterion | Phase 6 evidence |
| --- | --- |
| Store can be configured | Commerce Store contract/runtime + Kernel STORE authority |
| Products can be created | Commerce Catalogue runtime + Kernel PRODUCT authority |
| Inventory can be maintained | Commerce Inventory runtime + Kernel InventoryItem invariants |
| Customers can checkout | Commerce Cart/Checkout/Orders transaction plan |
| Orders reach correct final state | Kernel OrderState lifecycle |
| Payments reconcile | BaaS Payment Abstraction reconciliation |
| Refunds are auditable | Commerce Refund runtime + shared Kernel REFUND command/audit metadata |

### POS

| MVP criterion | Phase 6 evidence |
| --- | --- |
| Staff can authenticate | BaaS HUMAN_USER identity + Kernel RBAC binding |
| Products can be searched | Branch-scoped Product/SKU/barcode read plan |
| Sales can be completed | POS Cart/Checkout/Payment settlement |
| Inventory is deducted correctly | Reservation → atomic sale deduction |
| Returns are recorded correctly | POS Returns + Kernel Refund + restock |
| Receipts can be issued | Post-commit sale/return receipt plans |
| Branch reports are available | Daily Summary branch/currency/timezone read plan |

### Platform

| MVP criterion | Phase 6 evidence |
| --- | --- |
| No cross-tenant exposure | Exact-tenant evidence checks and fail-closed validation |
| No duplicated authoritative business models | SaaS has no authoritative SQL schema; Kernel/BaaS routes remain canonical |
| Critical operations are idempotent | Shared ProductCommand + payment/refund/checkout/return idempotency |
| Audit events exist | Product command audit metadata + BaaS Audit |
| Logs and metrics are available | Kernel/BaaS logging + metrics/usage metering status |
| Backup restore has been tested | BaaS restore-testing and trusted-recovery gate |

## Commerce Refund Closure

The acceptance sweep found a missing Commerce refund orchestration path even
though the MVP contract requires auditable refunds.

Phase 6 closure therefore adds a dedicated Commerce Refund service that:

- consumes exact-tenant Order and Payment evidence
- requires a captured Payment
- validates the shared Kernel Refund cap
- delegates external provider refunds to BaaS Payment Abstraction
- records a shared REFUND command only after successful provider evidence
- emits auditable metadata through the shared ProductCommand boundary
- keeps partial refunds on CAPTURED Payment state
- explicitly transitions CAPTURED → REFUNDED only after a full cumulative refund
- never exposes provider credential values

## Closure Result

Phase 6 is complete only when:

1. Kernel P0 remains complete.
2. BaaS P0 remains complete.
3. Commerce P0 remains complete.
4. POS P0 remains complete.
5. Commerce refund acceptance passes.
6. Payment reconciliation passes.
7. shared authority/idempotency/audit checks pass.
8. platform logging, metrics, and restore-testing evidence remains complete.
9. the Phase 6 acceptance validator exits successfully.

## Deferred Work

Phase 6 completion is an MVP/P0 implementation milestone, not a declaration of
full production hardening.

Existing deferred work remains tracked, including durable Cart Item
persistence, customer PII persistence hardening, provider production adapters,
analytics accelerators, POS offline mode, printer integration, split tender,
and other P1/hardening items.

## Next Phase

Phase 7 — Product-Market Validation.
