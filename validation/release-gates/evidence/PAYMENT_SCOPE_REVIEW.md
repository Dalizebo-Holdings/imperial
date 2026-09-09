# Phase 7 South Africa Payment Scope Review

Jurisdiction: South Africa
Review date: 2026-09-09

## Current Dalizebo P0 Scope

Dalizebo BaaS Payment Abstraction:

- orchestrates licensed external payment providers
- creates provider-neutral operation plans
- does not execute provider network calls in P0
- does not hold customer funds
- does not perform clearing or settlement
- does not issue electronic money
- does not persist competing authoritative provider payment state
- does not store raw card credentials or authentication data
- keeps provider credentials as opaque secret/vault/KMS references
- delegates provider-specific execution behind external adapters

Kernel retains authoritative payment/refund lifecycle state.

## Activities Not Claimed

Current P0 does not claim to operate as:

- an acquirer
- a settlement participant
- a clearing participant
- an e-money issuer
- a beneficiary service provider holding merchant funds
- a payer service provider disbursing customer funds

## Regulatory Confirmation Required

External confirmation is still required on whether Dalizebo's planned provider
adapter/orchestration model constitutes any regulated activity including:

- system operator activity
- third-party payment provision
- payment initiation
- acquiring activity
- another authorised payment activity under the evolving SARB framework

## Required Confirmation

Obtain written confirmation from the relevant SARB payment-regulation channel
or qualified South African payments counsel before production activation of
payment execution adapters.

Technical scope: DEFINED

PAYMENT_SCOPE_CONFIRMED: PENDING_EXTERNAL_CONFIRMATION
NO_UNRESOLVED_CRITICAL_REGULATORY_BLOCKER: PENDING
