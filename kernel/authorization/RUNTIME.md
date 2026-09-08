# Kernel Authorization Runtime

## Purpose

The Kernel Authorization Runtime implements the live repository model:

Authentication
→ Tenant Context
→ Role Resolution
→ Permission Evaluation
→ Policy Evaluation
→ Authorization Decision

## P0 Components

- Permission Registry
- Role Registry
- Resource Scope
- Tenant Scope
- Policy Result Adapter
- Privileged Access Rule
- Deterministic Authorization Decision
- Authorization Audit Event

## Policy Outcomes

Accepted upstream policy outcomes:

- ALLOW
- DENY
- REQUIRE_APPROVAL
- REQUIRE_CONTEXT

Only `ALLOW` can produce a positive Kernel authorization.

## Fail-Closed Rules

Authorization is denied when any required element is missing or invalid,
including:

- unauthenticated identity
- unverified tenant context
- actor mismatch
- unknown permission
- missing role
- role without required permission
- resource scope mismatch
- tenant scope mismatch
- upstream policy denial
- missing privileged permission for cross-tenant access

## Authorization Reference

Every decision receives a deterministic authorization reference derived from
material decision inputs.

The reference is suitable for passing to Algorithm OS, Loop OS, and
Integrations OS as evidence that Kernel authorization was evaluated.

It is not a credential and contains no secret material.
