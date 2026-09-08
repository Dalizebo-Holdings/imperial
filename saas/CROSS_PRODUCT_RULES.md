# Cross-Product Rules

## Shared Platform Principle

Every Dalizebo SaaS product must reuse:

- Identity
- Organizations
- Workspaces
- Billing
- Audit
- Events
- Notifications
- Shared business entities

## Data Authority

Each business entity must have one authoritative source.

Examples:

Customer → Kernel Customer Domain
Product → Kernel Catalog Domain
Inventory → Kernel Inventory Domain
Order → Kernel Order Domain
Payment → Kernel Payment Domain

## Integration

Products communicate through:

- Versioned APIs
- Domain events
- Shared Kernel contracts

Direct product-to-product database coupling is prohibited.
