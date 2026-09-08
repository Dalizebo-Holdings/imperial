# Events BaaS

## Responsibilities

- Domain events
- Event publication
- Event subscriptions
- Transactional outbox processing
- Delivery tracking

## Delivery Model

Database Transaction
→ Outbox
→ Event Worker
→ Subscriber

## Rule

Never publish domain events before transaction commit.
