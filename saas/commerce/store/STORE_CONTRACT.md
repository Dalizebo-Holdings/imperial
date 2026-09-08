# Commerce P0 — Store Contract

## Purpose

Dalizebo Commerce Store Setup is a product orchestration surface over the
authoritative Kernel `STORE` entity.

Commerce does not create a second Store database or Store authority.

## Authoritative Persistence

Kernel owns the Store record:

- id
- organization_id
- workspace_id
- project_id
- environment_id
- name
- status
- created_at
- updated_at

Canonical statuses:

- ACTIVE
- INACTIVE

## Store Setup Request

A Store setup command contains:

- store_id
- name
- status
- requested_at
- idempotency_key

`store_id` is a shared platform identifier. This runtime does not mint a
competing SaaS-local identity namespace.

## Store Status

Allowed status changes:

- ACTIVE → INACTIVE
- INACTIVE → ACTIVE

A status change requires Kernel authority evidence proving the Store belongs to
the same Organization → Workspace → Project → Environment context.

## Execution

Commerce emits a `ProductCommand` routed to:

- authority: `kernel.commerce`
- BaaS service: `baas.database`

The command state is:

`READY_FOR_PLATFORM_CONTRACT_ADAPTER`

No direct SQL is executed by this product runtime.

## Integrity

- product must be COMMERCE
- Kernel authorization evidence is mandatory
- mutations require idempotency
- authority evidence must be `kernel.commerce`
- cross-tenant evidence fails closed
- Store state is never cached as authoritative SaaS state
