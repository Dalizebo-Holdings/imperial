# Dalizebo Commerce

Dalizebo Commerce is the first SaaS application built on Dalizebo Kernel and Dalizebo Backend.

## P0 Capabilities

- Store setup
- Product catalogue
- Variants
- Pricing
- Inventory
- Customers
- Cart
- Checkout
- Orders
- Payments
- Discounts
- Notifications
- Dashboard

## P1 Capabilities

- Custom domains
- Import/export
- Low-stock alerts
- Refunds
- Customer segmentation
- Themes
- Delivery status

## Architecture

Dalizebo Commerce
→ Dalizebo Backend
→ Dalizebo Kernel
→ Shared Commerce Primitives

## Rule

Commerce must not maintain duplicate authoritative models for Products, Customers, Inventory, Orders, or Payments.
