# Commerce Orders

## States

draft
→ pending_payment
→ paid
→ fulfilled

Failure and exception states:

- payment_failed
- cancelled
- returned
- refunded

## Rules

All state changes must use Kernel state-transition rules.

Invalid transitions must fail without partial mutation.
