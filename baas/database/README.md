# Database BaaS

## Engine

PostgreSQL

## Responsibilities

- Managed databases
- Schema migrations
- Tenant isolation
- Transactions
- Connection management
- Backups
- Restore
- Query observability

## Rules

- Tenant isolation is mandatory.
- Production migrations must be reversible where practical.
- Multi-record state changes use transactions.
