# Dalizebo Automate

## Purpose

Dalizebo Automate exposes Loop OS capabilities as customer-facing workflow automation.

## Workflow Model

Trigger
→ Conditions
→ Pillars OS Policy Check
→ Actions
→ Result
→ Audit
→ Metrics

## P0 Triggers

- Order created
- Order paid
- Order fulfilled
- Inventory low
- Customer created
- Payment failed
- Refund completed
- Scheduled time

## P0 Actions

- Send notification
- Update record
- Create task
- Call webhook
- Execute function
- Add CRM activity

## Requirements

- Idempotency
- Bounded retries
- Timeouts
- Audit
- Run history
