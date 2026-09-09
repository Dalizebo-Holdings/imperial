# Phase 7 — Merchant Discovery Interview Guide

## Duration

15–20 minutes.

## Opening

Explain:

- this is product research
- you are not asking for passwords, card data, bank details or customer PII
- the merchant can decline any question
- the goal is to understand their current workflow

## Core Questions

### Business Context

1. What type of retail/business operation do you run?
2. Do you carry physical or trackable inventory?
3. Do you serve real paying customers regularly?
4. Roughly how frequently do transactions happen?

### Current Sales Workflow

5. How do you currently record sales?
6. Do you use a POS, spreadsheet, notebook, WhatsApp, ecommerce platform, or
   another system?
7. What part of recording a sale takes the most effort?

### Inventory

8. How do you know current stock levels?
9. How often is the system/record different from physical stock?
10. What happens when stock is wrong or unavailable?

### Payments

11. How do you handle cash and card payments?
12. How do you reconcile payments against sales?
13. What payment/reconciliation problems occur repeatedly?

### Customers and Orders

14. How do you keep customer/order history?
15. Can you easily find what a customer bought previously?
16. What information do you wish you had but cannot get quickly?

### Material Problem Test

17. Which current problem costs you the most time, money, sales, or customer
    trust?
18. How often does that happen?
19. What do you do today to work around it?
20. If nothing changes, what impact does that problem have on the business?

### Testing Intent

21. Would you be willing to test a Commerce and/or POS workflow using real
    business operations?
22. Would you be willing to give structured feedback during a pilot?

## Classification

`core_problem_material = true` only when the merchant describes a current
problem with meaningful operational, financial, sales, inventory, reconciliation
or customer impact.

Do not mark a problem material merely because the merchant says a new system
"sounds useful."

`willingness_to_test = true` only when the merchant explicitly agrees that they
would test.

`structured_feedback_available = true` only when the merchant explicitly agrees
to provide feedback during testing.

## Privacy

Do not store:

- merchant personal email/phone
- customer names/contact details
- passwords
- API keys
- tokens
- card PAN/CVV
- bank account numbers

Use opaque merchant references such as:

`merchant://phase7/7f32...`
