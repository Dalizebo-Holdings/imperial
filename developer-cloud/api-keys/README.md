# API Key Management

## Lifecycle

Create
→ Activate
→ Use
→ Rotate
→ Revoke

## Required Metadata

- key_id
- organization_id
- project_id
- environment_id
- name
- scopes
- created_by
- created_at
- expires_at
- last_used_at
- revoked_at

## Security

- Secret value shown only when appropriate
- Store only secure representations
- Scope keys minimally
- Support rotation
- Audit creation and revocation
