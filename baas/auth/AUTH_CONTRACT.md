# Authentication BaaS Runtime Contract

## Purpose

Authentication BaaS provides the user/session/API-client boundary above Kernel
Identity.

P0 implements provider-neutral identity registration records, session lifecycle,
API-key lifecycle, and authentication evidence contracts.

It does not implement email delivery, passkey ceremonies, MFA providers, or
password-reset delivery yet.

## Responsibilities Covered in This Slice

- User identity registration record
- Session creation
- Session invalidation
- API key issuance
- API key verification
- Service-account identity records
- Token/session lifecycle metadata
- Authentication evidence suitable for Kernel Identity Context

## Security Rules

1. Raw session tokens and API keys are returned once at issuance and never
   persisted.
2. Runtime storage contains only SHA-256 fingerprints of high-entropy random
   tokens/keys.
3. Expired, revoked, disabled, or cross-tenant credentials fail closed.
4. Every successful authentication produces an immutable principal context.
5. BaaS authentication does not grant resource authorization; Kernel
   authorization remains mandatory.
6. Passwords are outside this P0 runtime slice.
7. MFA/passkey claims are evidence flags only until concrete providers are
   implemented.

## Session Status

- ACTIVE
- REVOKED
- EXPIRED

## Identity Types

- HUMAN_USER
- SERVICE_ACCOUNT
- API_CLIENT

## Output Principal

- actor_id
- actor_type
- organization_id
- authenticated
- authentication_method
- identity_ref
- session_ref
- mfa_verified
