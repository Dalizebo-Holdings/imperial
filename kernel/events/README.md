# Kernel Events

## Transactional Outbox

Execution order:

Validate
→ Begin Transaction
→ Change State
→ Write Audit Record
→ Write Event to Outbox
→ Commit
→ Publish Asynchronously

Events must never be published before transaction commit.

## Event Envelope

- event_id
- event_type
- event_version
- organization_id
- workspace_id
- project_id
- environment_id
- resource_type
- resource_id
- occurred_at
- correlation_id
- actor_type
- actor_id
- payload
