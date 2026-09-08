# Algorithm OS Execution Planner

## Purpose

The Execution Planner transforms an evaluated Algorithm OS decision and
resolved dependency graph into a deterministic, auditable execution plan.

The planner does not perform side effects.

## Plan Lifecycle

Decision Request
→ Pillars OS Policy Result
→ Dependency Resolution
→ Deterministic Rule Evaluation
→ Execution Plan
→ Kernel Authorization Boundary
→ Loop OS / Integrations OS execution

## Required Plan Fields

The planner emits:

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
- platform_prerequisites
- risk_class
- audit_event
- kernel_authorization
- created_at

## Deterministic Identifier

`decision_id` is derived from a canonical SHA-256 digest of material planning
inputs. Identical material inputs produce the same identifier.

## Execution Step State

P0 steps are emitted only as:

- `READY_FOR_KERNEL_AUTHORIZATION`
- `BLOCKED`

No step is marked executed by Algorithm OS.

## Kernel Boundary

Even when the outcome is `APPROVED_FOR_AUTHORIZATION`, the plan carries:

`kernel_authorization = REQUIRED`

until Phase 4 Kernel authorization explicitly permits side effects.

## External Integrations

External prerequisites are surfaced as `required_integrations`. Credentials,
tokens, secrets, and provider authentication material must never be copied into
the plan.
