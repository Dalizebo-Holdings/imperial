# Phase 3 Orchestration Contract

## Scope

Phase 3 turns the canonically classified 269 Operating Systems into a governed orchestration layer.

It consists of:

- Algorithm OS
- Loop OS
- Integrations OS

## Architecture Position

207 Pillars
→ Pillars OS
→ 269 Operating Systems
→ Algorithm OS + Loop OS + Integrations OS
→ Dalizebo Kernel
→ Dalizebo BaaS
→ Dalizebo SaaS

## Shared Execution Path

Request or Event
→ Context Resolution
→ Pillars OS Policy Evaluation
→ Algorithm OS Capability Selection
→ Dependency Resolution
→ Deterministic Execution Plan
→ Kernel Authorization Boundary
→ Loop OS Stateful Execution
→ Integrations OS External Calls
→ Audit Evidence

## Phase 3 Boundary

Phase 3 defines orchestration contracts, registries, deterministic planning,
workflow state, connector behavior, audit semantics, and failure handling.

The Dalizebo Kernel is Phase 4.

Until Phase 4 exists, the Kernel Authorization Boundary is an interface contract,
not permission for uncontrolled production side effects.

## Invariants

1. No capability may bypass Pillars OS policy evaluation.
2. No production action may bypass the Kernel authorization boundary.
3. Every selected capability must resolve to OS-001 through OS-269.
4. Every execution plan must have a correlation identifier.
5. Sensitive operations must produce audit evidence.
6. Retries must be bounded.
7. Jobs must have timeouts.
8. Duplicate execution must be idempotent or safely rejected.
9. External connectors must use explicit authentication and scoped permissions.
10. Connector credentials must never be embedded in plans or audit payloads.
11. Failure defaults to a safe state.
12. Unsafe or retired source interpretations remain unavailable for execution.

## Canonical Registry

`orchestration/capability-registry.csv` is the Phase 3 execution-facing projection
of the Phase 2 canonical catalogue.

Phase 2 remains the source of truth for classification history.

The registry is derived, not independently authored.
