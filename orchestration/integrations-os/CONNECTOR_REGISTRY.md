# Integrations OS Connector Registry

## Purpose

The Connector Registry is the authoritative Phase 3 catalogue of external
connector definitions available to Integrations OS.

It stores connector metadata and execution constraints. It does not store
provider secrets.

## Connector Definition

Every registered connector defines the fields required by
`CONNECTOR_STANDARD.md`.

### Identity

- connector_id
- name
- provider
- version
- owner
- category

### Authentication

- supported_auth_methods
- credential_reference_required
- webhook_secret_reference_required

Secrets are referenced by opaque secret-manager identifiers only.

### Interfaces

- supported_operations
- input_schema
- output_schema
- error_schema
- rate_limit

### Reliability

- timeout_seconds
- max_attempts
- retryable_error_codes
- idempotency_supported
- circuit_breaker
- dead_letter_behavior

### Security

- secret_storage
- encryption_required
- permission_scopes
- audit_required

### Operations

- health_check
- metrics
- logs
- alerting
- compatible_versions

## Categories

The canonical P0 categories are inherited from the existing Integrations OS
README:

- Payments
- Banking
- Accounting
- Email
- SMS
- WhatsApp
- Logistics
- E-commerce
- Cloud
- Developer tools
- Analytics
- Government services
- IoT

## Registry Rules

1. Connector IDs are unique.
2. Connector definitions are versioned.
3. A connector may expose only declared operations.
4. No raw secret value may be placed in a connector definition.
5. Authentication uses credential references.
6. Runtime requests must resolve against a registered connector version.
7. Disabled connectors cannot be prepared for execution.
