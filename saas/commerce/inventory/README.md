# Commerce Inventory

## Responsibilities

- Available quantity
- Reserved quantity
- Stock adjustments
- Low-stock status
- Inventory events

## Rules

- Inventory authority belongs to the shared Kernel domain.
- Commerce reads and mutates inventory through platform contracts.
- Concurrent updates must preserve consistency.
