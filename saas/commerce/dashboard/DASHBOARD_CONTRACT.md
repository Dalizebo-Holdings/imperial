# Commerce P0 — Dashboard Contract

## Purpose

Commerce Dashboard is a read-only projection contract over existing
Kernel/BaaS authorities.

It does not create a new authoritative Orders, Payments, Customers, Inventory,
Audit, or Usage database.

## P0 Dashboard Metrics

- order_count
- gross_sales_minor
- captured_payment_count
- customer_count
- low_stock_item_count

## Query Scope

Every query is scoped by:

- Organization
- Workspace
- Project
- Environment
- Store
- timezone-aware period_start
- timezone-aware period_end
- currency

P0 bounds one query window to at most 366 days.

## Sources

The read adapter is instructed to read from:

- Kernel commerce Orders / Order Items
- Kernel commerce Payments
- Kernel commerce Customers
- Kernel commerce Inventory Items
- Kernel Audit when evidence is required

## Money

Dashboard monetary aggregation is currency-specific and integer minor-unit
based.

Different currencies must never be silently combined.

## State

`READY_FOR_DASHBOARD_READ_ADAPTER`

P0 defines the safe read contract. A durable analytics/read-model accelerator is
deferred; if added later it must remain a projection, never an authority.
