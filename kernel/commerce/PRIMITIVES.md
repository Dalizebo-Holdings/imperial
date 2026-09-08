# Kernel Shared Commerce Primitives

## Purpose

The Kernel owns one authoritative commerce model reused by Dalizebo Commerce,
Dalizebo POS, Dalizebo BaaS services, and later SaaS products.

No SaaS product may create a competing authoritative model for the same
business resource.

## Canonical Entities

- Store
- Branch
- Product
- Product Variant
- Inventory Item
- Customer
- Cart
- Order
- Order Item
- Payment
- Refund
- Discount

## Tenant Standard

Every persistent commerce resource carries:

- id
- organization_id
- created_at
- updated_at

Workspace, project, and environment identifiers are included for execution
scope where required.

## Money

Monetary values use integer minor units plus a three-letter uppercase currency.

Examples:

- ZAR 10.00 → `amount_minor = 1000`, `currency = "ZAR"`
- USD 5.99 → `amount_minor = 599`, `currency = "USD"`

Floating point money is prohibited.

## Product and Inventory Rules

- Product Variants belong to one Product.
- Inventory Items reference one Product Variant.
- Inventory quantity may not become negative.
- Inventory mutations must use Kernel transaction + idempotency boundaries.
- Inventory state changes must be explicit and auditable.

## Order Rules

Order lifecycle:

`DRAFT → PLACED → CONFIRMED → COMPLETED`

Cancellation is allowed from:

- DRAFT
- PLACED
- CONFIRMED

Terminal states:

- COMPLETED
- CANCELLED

Illegal transitions fail closed.

## Payment Rules

Payment lifecycle:

`PENDING → AUTHORIZED → CAPTURED`

Failure/cancellation may occur before capture.

Refunds are separate authoritative resources linked to the captured payment.

No hidden payment transitions are allowed.

## Cart Rules

Cart lifecycle:

- OPEN
- CONVERTED
- ABANDONED

A converted or abandoned cart is terminal.

## Discounts

Discounts must be explicit, bounded, auditable business rules.

P0 supports:

- FIXED
- PERCENTAGE

Percentage discounts are integer basis points from 1 to 10,000.

## Architectural Boundary

Kernel commerce primitives define authoritative shared data and deterministic
state rules.

Product-specific storefront UX, promotions UI, POS screens, merchandising,
recommendation logic, and channel presentation belong outside the Kernel.
