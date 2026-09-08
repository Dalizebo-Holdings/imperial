# Phase 10 Acceptance Criteria

## Platform

- All AI requests pass through AI Gateway
- Model providers are abstracted
- Usage is metered
- Tenant isolation is tested
- AI actions are observable
- Material actions are audited

## RAG

- Permission-aware retrieval
- Source attribution
- Tenant-scoped vector indexes

## Agents

- Bounded execution
- Tool allowlists
- Cost limits
- Approval controls
- Audit trail
- Failure recovery

## Security

- No direct provider credentials in SaaS clients
- No cross-tenant retrieval
- No unrestricted autonomous execution
