# Phase 6 — Commerce + POS Foundation Contract

## Purpose

Phase 6 begins the first Dalizebo SaaS product pair:

- Dalizebo Commerce
- Dalizebo POS

Both products run above Dalizebo Backend and Dalizebo Kernel and consume one
shared authoritative commerce domain.

The foundation is intentionally thin. It creates product execution context,
shared-entity references, idempotent command planning, and authority routing.
It does not create duplicate Product, Inventory, Customer, Cart, Order,
Payment, Refund, Discount, Store, or Branch stores.

## Architecture

Dalizebo Commerce / Dalizebo POS
→ Dalizebo Backend
→ Dalizebo Kernel
→ Shared Commerce Primitives

## Canonical Shared Entities

Phase 6 consumes the shared SaaS domain contract:

- Organization
- Workspace
- User
- Role
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
- Audit Event

Products hold references and workflow state only where explicitly allowed.
Authoritative business state remains in Kernel/BaaS.

## Product Context

Every product command contains:

- product: COMMERCE or POS
- organization_id
- workspace_id
- project_id
- environment_id
- actor_id
- actor_type
- kernel_authorization_ref
- correlation_id
- store_id when available
- branch_id when applicable

POS operational commands require branch context.

## Command Contract

A product command contains:

- action
- entity_type
- entity_id when addressing an existing entity
- idempotency_key for every mutation
- safe bounded input metadata
- product context

Supported foundation actions:

- CREATE
- READ
- UPDATE
- TRANSITION
- EXECUTE

Mutation actions are idempotent:

- CREATE
- UPDATE
- TRANSITION
- EXECUTE

The same idempotency scope plus the same canonical command returns one
deterministic command identity.

The same idempotency key with different command material fails closed.

## Authority Routing

The router derives the authority. Products cannot choose an arbitrary database
or competing domain implementation.

- Organization / Workspace → Kernel tenant authority
- User / Role → Authentication + Kernel identity/RBAC
- Store / Branch / Product / Product Variant / Inventory Item / Customer /
  Cart / Order / Order Item / Discount → Kernel shared commerce authority
- Payment / Refund → Payment Abstraction + Kernel commerce authority
- Audit Event → Kernel Audit authority

Direct product-to-product database coupling is prohibited.

## Store and Branch Scope

Commerce:

- STORE creation may occur before a store_id exists.
- Commands for Branch, Inventory, Cart, Order, Payment, Refund, and Discount
  require store context.
- Product/customer catalogue commands may be tenant-level during initial setup.

POS:

- STORE/BRANCH setup commands may occur without an active branch context.
- Operational POS commands require both store_id and branch_id.

## Safety and Integrity

- Kernel authorization evidence is mandatory.
- Tenant IDs are explicit on every command context.
- Sensitive credential/token/payment-authentication metadata is rejected.
- Product commands do not accept raw provider credentials.
- Payment provider logic remains behind Payment Abstraction.
- Event publication remains after commit through the existing outbox/events
  boundary.
- Product logs do not replace Kernel Audit.
- Critical mutations are idempotent.
- No hidden payment or inventory transitions are introduced here.

## Phase 6 Delivery Sequence

1. Shared Commerce + POS Foundation
2. Commerce Store + Catalogue
3. Commerce Inventory + Customers
4. Commerce Cart + Checkout + Orders
5. Commerce Payments + Discounts + Notifications + Dashboard
6. POS Branch + Staff + Product Lookup
7. POS Cart + Checkout + Payments + Receipts
8. POS Inventory + Returns + Daily Summaries
9. Commerce + POS MVP acceptance closure
