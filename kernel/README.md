# Dalizebo Kernel

## Purpose

The Dalizebo Kernel is the smallest trusted execution layer shared by every BaaS service and SaaS product.

It owns:

- Tenant boundaries
- Identity context
- Authorization
- Shared identifiers
- Transaction rules
- Idempotency
- Auditability
- Domain events
- Observability
- Shared commerce primitives

## Core Principle

The Kernel must remain:

- Small
- Deterministic
- Auditable
- Stable
- Reusable
- Versioned
- Testable
- Observable

## Architecture

Pillars OS
→ Algorithm OS
→ Loop OS
→ Integrations OS
→ Dalizebo Kernel
→ Dalizebo BaaS
→ Dalizebo SaaS

## Kernel Rules

- No product-specific UI logic.
- No direct cross-tenant access.
- No undocumented database side effects.
- No event publication before transaction commit.
- No unbounded retries.
- No secrets in source code.
- No hidden payment or inventory transitions.
- Fail closed for authorization and security.
