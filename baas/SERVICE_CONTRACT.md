# Dalizebo BaaS Service Contract

## Purpose

Dalizebo BaaS exposes managed platform services on top of the Dalizebo Kernel.

Every BaaS service must reuse Kernel identity, tenancy, authorization,
idempotency, audit, observability, persistence, secret-reference, and recovery
contracts rather than duplicating them.

## P0 Services

- Authentication
- PostgreSQL Database
- Object Storage
- Serverless Functions
- API Gateway
- Events
- Webhooks
- Background Jobs
- Audit
- Logging
- Usage Metering
- Subscription Billing
- Payment Abstraction
- Secrets
- Backups

## Tenant Model

Every tenant-aware request resolves:

Organization
→ Workspace
→ Project
→ Environment

## BaaS Request Envelope

Required fields:

- request_id
- correlation_id
- service
- operation
- organization_id
- workspace_id
- project_id
- environment_id
- actor_id
- actor_type
- kernel_authorization_ref
- idempotency_key

## Rules

1. No BaaS operation may bypass Kernel authorization.
2. No service may trust tenant identifiers without verified Kernel context.
3. Sensitive writes require audit evidence.
4. Side effects use Kernel transaction and idempotency primitives.
5. Secret values remain behind secret references.
6. Errors are safe and correlation-aware.
7. Services remain logical modules until operational evidence justifies
   deployment separation.
