# Kernel Identity Context

## Purpose

Identity Context is the authenticated actor envelope consumed by the Dalizebo
Kernel trust boundary.

It models identity state. It does not perform credential verification itself.

## Supported Actor Types

- HUMAN_USER
- SERVICE_ACCOUNT
- API_CLIENT
- BACKGROUND_WORKER
- SYSTEM_ACTOR

These correspond to the identity types already defined by the Kernel.

## Required Fields

- actor_id
- actor_type
- authenticated
- authentication_method
- identity_ref

Optional:

- session_ref
- mfa_verified
- attributes

## Rules

1. Actor IDs must be non-empty.
2. Actor type must be canonical.
3. Unauthenticated identities cannot receive Kernel authorization.
4. Authentication material and raw secrets must never be embedded in identity
   context.
5. Authentication context is immutable for one authorization evaluation.
