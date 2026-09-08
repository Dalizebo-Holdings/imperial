# Algorithm OS Decision Contract

## Purpose

Define the deterministic request and response contract used by Algorithm OS
to select and sequence canonical capabilities.

## Decision Request

Required fields:

- decision_request_id
- organization_id
- actor_id
- source
- requested_capabilities
- context_ref
- policy_context
- constraints
- idempotency_key
- correlation_id
- requested_at

Optional fields:

- workspace_id
- project_id
- environment
- priority
- deadline
- cost_budget
- latency_budget
- integration_preferences

## Capability Reference

Every capability reference must use:

`OS-NNN`

where `NNN` is in the canonical range `001` through `269`.

## Decision Response

Required fields:

- decision_id
- decision_request_id
- correlation_id
- policy_result
- selected_capabilities
- dependency_order
- execution_steps
- required_approvals
- required_loop_jobs
- required_integrations
- risk_class
- audit_event
- created_at

## Decision Outcomes

Allowed outcomes:

- APPROVED_FOR_AUTHORIZATION
- REQUIRES_APPROVAL
- REQUIRES_CONTEXT
- POLICY_DENIED
- CAPABILITY_UNAVAILABLE
- DEPENDENCY_UNRESOLVED
- SAFE_FAILURE

`APPROVED_FOR_AUTHORIZATION` does not itself authorize execution.

Kernel authorization remains a separate boundary.

## Determinism

For identical canonical registry version, policy version, material context,
constraints, and request payload, deterministic rules should produce the same
plan where practical.

AI-assisted planning may propose alternatives but must not silently override
policy, dependencies, approvals, or deterministic safety constraints.

## Audit Requirements

Every decision must record:

- decision_id
- correlation_id
- actor
- policy version
- registry version
- selected capabilities
- rejected alternatives where materially relevant
- approval requirements
- risk classification
- final outcome
