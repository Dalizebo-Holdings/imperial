# POS P0 — Daily Summary Contract

## Purpose

Daily Summaries provide branch-scoped operational reporting without creating a
new authoritative reporting database.

## Business Day

A query contains:

- business_date in `YYYY-MM-DD`
- IANA timezone name
- currency
- Store
- Branch

The adapter derives the timezone-aware business-day start/end interval.

## Metrics

P0 metrics:

- completed_order_count
- gross_sales_minor
- cash_sales_minor
- card_sales_minor
- refund_count
- refund_minor
- net_sales_minor
- items_sold
- items_returned

Money remains integer minor units and currency-specific.

## Sources

Read-only sources:

- kernel.orders
- kernel.order_items
- kernel.payments
- kernel.refunds
- kernel.inventory_items
- kernel.audit

## Filters

Every query includes exact:

- Organization
- Workspace
- Project
- Environment
- Store
- Branch
- currency
- business-day UTC interval

## State

`READY_FOR_POS_DAILY_SUMMARY_ADAPTER`

A durable analytics/read-model accelerator is deferred. Any future accelerator
is a projection only and cannot become business-data authority.
