# Commerce State Transitions

## Order Example

draft
→ pending_payment

pending_payment
→ paid
→ payment_failed

paid
→ fulfilled
→ cancelled

fulfilled
→ returned

## Rules

- Invalid transitions return typed errors.
- No partial state modifications.
- Every material transition is audited.
- Relevant transitions publish domain events.
