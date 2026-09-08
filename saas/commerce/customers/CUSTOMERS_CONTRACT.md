# Commerce P0 — Customers Contract

## Purpose

Dalizebo Commerce Customers orchestrates the shared Kernel `CUSTOMER` entity.

Commerce does not maintain a separate authoritative customer database.

## Kernel Customer Fields

The current Kernel schema includes:

- id
- tenant scope
- external_identity_ref
- display_name
- email
- phone
- created_at
- updated_at

## Customer Creation / Update

P0 supports:

- customer creation
- customer profile update
- external identity reference
- optional email
- optional phone

Existing customer updates require exact-tenant Kernel commerce authority
evidence.

## Contact PII Boundary

Email and phone are personal data.

If either field is supplied, the request must include:

- `pii_policy_ref` using `pii-policy://...`
- `retention_policy_ref` using `retention-policy://...`

The command marks contact fields as `PERSONAL_DATA` and instructs the
persistence adapter not to include contact values in audit/log metadata.

This is a control-plane protection boundary only.

The current Kernel table contains direct email/phone fields. Production
activation still requires the planned database PII hardening work for
classification, encryption/appropriate protection, retention, and deletion
policy enforcement.

P0 does not falsely claim those persistence protections are complete.

## Validation

- display name max 512 characters
- email max 320 characters and basic address shape
- phone max 64 characters
- no credentials/tokens are accepted as customer metadata
- cross-tenant authority evidence fails closed
- mutations are idempotent

## Audit

Product command audit metadata identifies the Customer operation and IDs but
does not copy input metadata, email, or phone into the audit event.
