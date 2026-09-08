# Commerce Checkout

## Flow

Customer
→ Cart Validation
→ Inventory Validation
→ Pricing Validation
→ Order Draft
→ Payment Intent
→ Payment Confirmation
→ Order Paid
→ Inventory Deduction
→ Event Publication
→ Notification

## Requirements

- Tenant-aware
- Transaction-safe
- Idempotent
- Auditable
- Observable
- Payment-provider independent

## Critical Rules

- No inventory deduction without valid state transition.
- No duplicate order submission.
- No event publication before transaction commit.
- Payment state must reconcile with provider state.
