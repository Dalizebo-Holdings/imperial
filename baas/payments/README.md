# Payments BaaS

Dalizebo orchestrates licensed external payment providers.

## Kernel-Owned State

- Payment Intent
- Status
- Amount
- Currency
- Provider
- Provider Reference
- Reconciliation State
- Refund State
- Idempotency
- Audit

## Rules

- Provider-specific logic remains behind adapters.
- SaaS products must not couple directly to payment providers.
- Payment operations must be idempotent.
