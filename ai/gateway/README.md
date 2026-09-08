# AI Gateway

## Responsibilities

- Unified AI API
- Authentication
- Tenant context
- Provider abstraction
- Model routing
- Usage metering
- Rate limiting
- Policy enforcement
- Structured logging
- Audit events

## Request Flow

Request
→ Authentication
→ Tenant Context
→ Authorization
→ Pillars OS
→ Model Routing
→ Provider
→ Response Validation
→ Usage Metering
→ Audit

## Rule

SaaS products must not integrate directly with AI model providers.
