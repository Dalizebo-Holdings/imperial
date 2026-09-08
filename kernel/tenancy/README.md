# Tenant Context

## Hierarchy

User
→ Organization
→ Workspace
→ Project
→ Environment

## Environments

- Development
- Preview
- Production

## Required Context

Every tenant-aware request must resolve:

- organization_id
- workspace_id
- project_id
- environment_id
- actor_id
- actor_type
- correlation_id

## Rules

- Never trust an unverified client-supplied tenant ID.
- Tenant context must be present in logs, traces, audit records, and events.
- Cross-tenant operations require explicit privileged authorization.
- Database Row Level Security should be used where appropriate.
