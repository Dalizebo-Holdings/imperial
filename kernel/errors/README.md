# Kernel Error Contract

## Purpose

The Kernel Error Contract provides stable, safe, observable errors across BaaS
and SaaS callers without leaking internal exceptions or secrets.

## Error Envelope

- error_id
- code
- category
- message
- retryable
- correlation_id
- details

## Categories

- VALIDATION
- AUTHENTICATION
- AUTHORIZATION
- TENANCY
- CONFLICT
- NOT_FOUND
- RATE_LIMIT
- DEPENDENCY
- INTERNAL

## Rules

- `code` is stable machine-readable text.
- `message` is safe for the caller.
- Internal exception messages and tracebacks are not exposed.
- Every error carries a correlation ID.
- Details are JSON-compatible and recursively redacted.
- Authorization/security failures fail closed.
- Retryability is explicit.
