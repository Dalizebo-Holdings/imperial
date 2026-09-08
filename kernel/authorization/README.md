# Authorization

## Model

Authentication
→ Tenant Context
→ Role Resolution
→ Permission Evaluation
→ Policy Evaluation
→ Authorization Decision

## Core Components

- RBAC
- Permission Registry
- Resource Scopes
- Policy Adapter
- Privileged Access Rules
- Authorization Audit

## Rules

Authorization must fail closed.

Every sensitive operation must define:

- Required permission
- Resource scope
- Tenant scope
- Audit behavior
