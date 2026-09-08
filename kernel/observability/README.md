# Kernel Observability

## Components

- Structured Logs
- Metrics
- Distributed Tracing
- Health Checks
- Readiness Checks
- Error Monitoring
- Correlation IDs

## Rules

Every request must have a correlation ID.

Logs must never expose:

- Passwords
- Tokens
- API secrets
- Provider credentials
- Sensitive payment data
