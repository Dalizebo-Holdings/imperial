# Integrations OS Credential Reference Adapter

## Purpose

The Credential Reference Adapter manages metadata about external credentials
without storing, returning, logging, or embedding raw credential material.

P0 models credential references only.

## Credential Descriptor

Each descriptor contains:

- credential_ref
- organization_id
- connector_id
- auth_method
- permission_scopes
- owner
- version
- enabled
- metadata

## Reference Format

P0 accepts opaque references using:

- `secret://...`
- `credential://...`

The adapter never dereferences these URIs into secret values.

## Isolation Rules

1. Credential references are organization-scoped.
2. A reference may be bound to one connector.
3. Authentication method must match the connector request.
4. Requested permission scopes must be a subset of the credential descriptor.
5. Disabled descriptors cannot be used.
6. Duplicate references cannot be silently replaced.
7. Raw secret-bearing field names are rejected from descriptor metadata.
8. No API key, password, access token, refresh token, private key, webhook
   secret, session token, or authorization header may be stored.

## Runtime Output

Credential resolution returns a `CredentialContext` containing:

- credential_ref
- organization_id
- connector_id
- auth_method
- approved_scopes
- descriptor_version

This context proves metadata compatibility only.

It contains no secret value.
