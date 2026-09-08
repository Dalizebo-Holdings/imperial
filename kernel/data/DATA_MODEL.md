# Kernel Data Model

## Persistent Resource Standard

Every persistent resource should contain:

- id
- organization_id
- created_at
- updated_at

Add workspace_id, project_id, environment_id where required.

## Identifier Rules

Identifiers must be:

- Globally unique
- Stable across retries
- Safe for event references
- Safe for logging
- Non-sequential when exposure presents risk

## Transaction Rules

Use database transactions for multi-record state changes.

No partial mutation is allowed when an operation is expected to be atomic.
