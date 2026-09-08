# Cross-Product Audit

## Purpose

Provide a unified audit trail across all Dalizebo products and shared services.

## Event Sources

- Identity
- Commerce
- POS
- CRM
- Desk
- Projects
- Billing
- Payments
- Automate
- AI
- Developer Cloud

## Standard Audit Fields

- audit_id
- organization_id
- workspace_id
- actor_type
- actor_id
- product
- action
- resource_type
- resource_id
- timestamp
- correlation_id
- metadata

## Requirements

- Immutable history
- Tenant isolation
- Searchability
- Retention policy
- Export support
