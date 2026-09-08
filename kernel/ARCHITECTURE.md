# Kernel Architecture

## Logical Service Boundaries

- Identity & Access
- Tenant Context
- Catalog
- Inventory
- Customer
- Order
- Payment
- Event
- Audit
- Observability

These are logical boundaries.

They should not become separate microservices until operational evidence justifies that split.

## Kernel P0

- Organizations
- Workspaces
- Projects
- Environments
- Authentication
- RBAC
- Tenant Context
- PostgreSQL
- Migrations
- Transaction Utilities
- Shared IDs
- Commerce Primitives
- Idempotency
- Audit
- Logging
- Errors
- Health Checks
- Metrics
- Secrets
- Backups

## Kernel P1

- Domain Event Bus
- Webhooks
- Background Jobs
- Scheduled Jobs
- Basic Realtime
- Rate Limits
- Validation Schemas
- Usage Metering
- Subscription Billing
- Payment Abstraction
- CLI
- Documentation
