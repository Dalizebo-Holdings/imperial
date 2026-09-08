# BaaS Secrets Runtime Contract

## Purpose

Secrets BaaS is the tenant-facing control plane above the Kernel Secret
Reference Boundary.

P0 manages secret-reference metadata, tenant/environment scope, consumer
allowlists, access planning, disablement, rotation planning/confirmation, and
access audit evidence.

P0 never stores or returns raw secret values.

## Authority Boundary

Kernel owns the canonical secret-reference rules:

- only `secret://`, `vault://`, and `kms://` references
- organization/environment scope
- explicit consumer allowlists
- disabled references fail closed
- raw values never enter Kernel runtime state
- production retrieval belongs to an approved external secret manager

BaaS Secrets extends that boundary with workspace/project scope and lifecycle
orchestration. It does not implement a competing vault.

## Provider Configuration

A provider configuration contains:

- provider_id
- adapter_ref
- control_credential_ref
- encryption_at_rest_required
- supports_rotation
- enabled

Rules:

- `adapter_ref` is provider-neutral adapter metadata
- `control_credential_ref` is itself an opaque Kernel-approved secret reference
- raw provider credentials are forbidden
- `encryption_at_rest_required` must be true for P0 provider registration

The flag is a control-plane requirement. P0 does not claim physical encryption
has occurred; the production provider adapter must prove/enforce it.

## Secret Registration

Each BaaS secret registration contains:

- secret_id
- tenant scope
- name
- purpose
- owner
- provider_id
- secret_ref
- version
- allowed_consumers
- rotation_interval_days
- rotated_at
- state
- metadata

States:

- ACTIVE
- DISABLED

Raw values are not fields in the model.

## Registration

Registration:

1. validates the full BaaS tenant scope
2. validates provider policy
3. rejects secret-bearing metadata
4. registers the opaque reference through Kernel `SecretReferenceRegistry`
5. stores BaaS lifecycle metadata only
6. emits audit-event metadata

## Access

Access requires:

- `service=secrets`
- Kernel authorization evidence
- exact organization/workspace/project/environment match
- ACTIVE BaaS registration
- ACTIVE Kernel descriptor
- consumer present in Kernel allowlist

The result is a `SecretAccessPlan` containing only:

- secret_ref
- provider adapter reference
- purpose
- consumer
- descriptor version
- tenant context
- correlation ID
- Kernel authorization reference
- access audit event

State:

`READY_FOR_SECRET_MANAGER_ADAPTER`

The actual secret value may only be retrieved/injected by an approved production
adapter outside the BaaS control-plane object.

## Rotation

Rotation is explicit and two-step.

### Plan

`plan_rotation()` returns:

- current secret reference
- provider adapter reference
- provider control credential reference
- next descriptor version
- rotation audit metadata

State:

`READY_FOR_SECRET_MANAGER_ROTATION_ADAPTER`

No secret value is generated or stored by P0.

### Confirm

After an approved adapter rotates the secret externally, `confirm_rotation()`
accepts only:

- new opaque secret reference
- new version
- rotated_at timestamp

It:

1. validates the new opaque reference
2. registers a new Kernel descriptor
3. disables the old Kernel reference
4. updates BaaS metadata
5. emits rotation audit evidence

## Rotation Due

When `rotation_interval_days` is configured, `rotation_due()` compares
`rotated_at + interval` with the supplied current time.

P0 does not automatically execute rotation.

## Disablement

Disablement fails closed:

- BaaS registration becomes DISABLED
- Kernel secret reference is disabled
- future access planning is rejected

## Metadata Safety

Metadata must:

- be JSON-compatible
- remain <= 8192 canonical JSON bytes
- contain no credential/token/password/secret-bearing field names

## Access Auditing

Successful registration, access, disablement, rotation planning, and rotation
confirmation return audit-event metadata suitable for Kernel Audit.

Opaque secret references may appear for traceability; resolved values never do.

## Deferred Runtime

P0 does not implement:

- secret value storage
- physical encryption at rest
- secret generation
- secret retrieval
- runtime secret injection
- automatic rotation execution
- cloud/Vault/KMS provider SDK calls

Those belong to approved secret-manager adapters.
