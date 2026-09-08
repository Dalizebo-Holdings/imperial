# POS Checkout

## Flow

Staff Authentication
→ Branch Context
→ Product Lookup
→ Cart
→ Inventory Validation
→ Payment Recording
→ Order Creation
→ Inventory Deduction
→ Receipt
→ Audit
→ Event Publication

## Payment Types

- Cash
- Card
- External Payment Provider

## Requirements

- Staff authorization
- Branch context
- Idempotency
- Inventory consistency
- Payment reconciliation
- Audit trail
