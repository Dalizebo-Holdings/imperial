# Algorithm OS Policy Adapter

## Purpose

The Policy Adapter is the mandatory interface between Algorithm OS planning and Pillars OS constitutional policy evaluation.

Algorithm OS does not self-authorize actions.

## Execution Boundary

Capability Request
→ Capability Registry Lookup
→ Policy Profile Lookup
→ Policy Evaluation Request
→ Pillars OS
→ Policy Decision
→ Algorithm OS Outcome

## Responsibilities

- Validate the canonical OS identifier.
- Attach tenant and actor context.
- Attach capability security and disposition metadata.
- Route every decision to Pillars OS.
- Require explicit approval for CRITICAL capabilities.
- Prevent production use of research-only capabilities.
- Restrict RETIRED_REFRAMED capabilities to canonical interpretations.
- Preserve correlation and audit identifiers.
- Fail closed on missing policy context.

## Execution Eligibility

- `ELIGIBLE_FOR_POLICY_EVALUATION`
- `RESEARCH_ONLY`
- `CANONICAL_REFRAME_ONLY`

## Pillars OS Decision Mapping

- ALLOW → APPROVED_FOR_AUTHORIZATION
- DENY → POLICY_DENIED
- REQUIRE_APPROVAL → REQUIRES_APPROVAL
- REQUIRE_CONTEXT → REQUIRES_CONTEXT
- unknown or malformed → SAFE_FAILURE

`APPROVED_FOR_AUTHORIZATION` still requires the Dalizebo Kernel authorization boundary before side effects can occur.

## Required Context

Every policy request must include:

- decision_request_id
- capability_id
- actor_id
- organization_id
- correlation_id
- requested_operation
- environment
- execution_eligibility
- security_level
- required_controls

## Security Rule

The Policy Adapter must never place credentials, secrets, raw authentication tokens, or unnecessary personal data into policy or audit payloads.
