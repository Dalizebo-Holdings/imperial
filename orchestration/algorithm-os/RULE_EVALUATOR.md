# Algorithm OS Deterministic Rule Evaluator

## Purpose

The Deterministic Rule Evaluator converts policy outcomes, dependency state,
capability metadata, and explicit request constraints into one canonical
Algorithm OS decision outcome.

It does not execute actions and it does not replace Pillars OS.

## Outcome Precedence

Highest-precedence blocking outcomes are evaluated first:

1. `SAFE_FAILURE`
2. `POLICY_DENIED`
3. `REQUIRES_CONTEXT`
4. `DEPENDENCY_UNRESOLVED`
5. `REQUIRES_APPROVAL`
6. `APPROVED_FOR_AUTHORIZATION`

## Deterministic Inputs

- requested canonical capability IDs
- Pillars OS policy outcomes
- dependency resolution result
- capability policy profiles
- explicit request constraints

No hidden user profiling, covert inference, or unstated behavioral scoring is
permitted in P0 deterministic evaluation.

## Rules

- Empty requests fail safely.
- Unknown capability references fail safely.
- Any malformed policy result fails safely.
- Any explicit Pillars OS denial produces `POLICY_DENIED`.
- Missing required policy context produces `REQUIRES_CONTEXT`.
- Canonical dependency cycles produce `DEPENDENCY_UNRESOLVED`.
- Required approvals produce `REQUIRES_APPROVAL`.
- Research-only capabilities cannot become directly authorized for production.
- `APPROVED_FOR_AUTHORIZATION` means only that the plan may be presented to
  the Dalizebo Kernel authorization boundary.

## Risk Classes

- LOW
- MEDIUM
- HIGH
- CRITICAL

Risk is derived deterministically from the highest security level among the
planned canonical capabilities.
