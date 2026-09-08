# Serverless Functions BaaS Runtime Contract

## Purpose

Functions BaaS manages tenant-scoped server-side function definitions and
builds bounded invocation plans.

P0 is a control-plane and execution-contract layer. It does not execute
arbitrary user code and does not provide the production scheduler itself.

## Function Types

Supported trigger definitions:

- HTTP
- EVENT
- SCHEDULED
- MANUAL

The function descriptor may define scheduled trigger metadata in P0. The shared
production scheduling service remains a later BaaS capability.

## Function Descriptor

Each function contains:

- function_id
- organization_id
- workspace_id
- project_id
- environment_id
- name
- runtime
- entrypoint
- code_bundle_ref
- trigger
- timeout_seconds
- memory_mb
- secret_refs
- state
- created_at
- updated_at

`code_bundle_ref` points to immutable code stored outside the Functions runtime.

Secret values are never stored. Only approved secret references are attached.

## Lifecycle

`DRAFT → ACTIVE → SUSPENDED → ACTIVE`

Terminal:

`RETIRED`

Only ACTIVE functions may produce invocation plans.

## Execution Bounds

P0 platform limits:

- timeout: 1–900 seconds
- memory: 128–4096 MB
- secret references: maximum 64
- request payload metadata: bounded and secret-free

These are P0 control-plane limits and can later be tightened by plan, tenant, or
runtime policy.

## Tenant and Authorization Rules

1. Every management or invocation operation requires BaaS request context.
2. Kernel authorization evidence is mandatory.
3. Function tenant scope must exactly match request tenant scope.
4. Cross-tenant function access fails closed.
5. Invocation identity does not replace Kernel resource authorization.

## Trigger Contracts

### HTTP

- method
- path

### EVENT

- event_type

### SCHEDULED

- schedule_expression

P0 validates schedule metadata only. It does not run a scheduler.

### MANUAL

No extra trigger fields.

## Invocation Plan

A valid invocation produces:

- execution_id
- function_id
- runtime
- entrypoint
- code_bundle_ref
- trigger_type
- timeout_seconds
- memory_mb
- secret_refs
- tenant_context
- correlation_id
- kernel_authorization_ref
- audit_event
- log_context

The plan contains references and metadata only. It is safe to hand to a future
isolated execution adapter.

## Runtime Security Boundary

A production executor must provide:

- process/container isolation
- filesystem isolation
- network egress policy
- resource quotas
- bounded execution
- secret injection at execution time
- structured logging
- audit events
- kill-on-timeout behavior

None of those production execution claims are implied by the P0 reference
control plane.
