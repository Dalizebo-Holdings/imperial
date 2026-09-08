# Regional Payments

## Architecture

SaaS
→ Dalizebo Payments BaaS
→ Regional Payment Adapter
→ Licensed Payment Provider

## Requirements

Each adapter must define:

- Provider
- Supported currencies
- Payment methods
- Refund behavior
- Settlement model
- Webhook contract
- Reconciliation
- Failure mapping
- Idempotency support

## Rule

Regional SaaS products must not integrate directly with payment providers.
