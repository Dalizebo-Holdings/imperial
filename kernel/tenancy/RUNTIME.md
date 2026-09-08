# Kernel Tenant Context Runtime

## Purpose

Tenant Context resolves the hierarchy:

User
→ Organization
→ Workspace
→ Project
→ Environment

for every tenant-aware Kernel authorization decision.

## Required Context

- organization_id
- workspace_id
- project_id
- environment_id
- actor_id
- actor_type
- correlation_id

## Verification Rule

Client-provided tenant identifiers are not trusted directly.

P0 therefore requires:

`verified = true`

before a tenant context may enter the Kernel authorization boundary.

## Cross-Tenant Boundary

A target organization different from the verified tenant organization is a
cross-tenant operation.

Cross-tenant execution requires:

- explicit privileged mode
- `kernel.cross_tenant` permission
- Pillars OS policy approval
- Kernel authorization audit evidence

## Environments

Canonical environment classes:

- DEVELOPMENT
- PREVIEW
- PRODUCTION
