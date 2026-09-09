# Phase 7 — Evidence Ingestion Contract

## Purpose

Phase 7 decisions must be derived from recorded evidence rather than status
files, test fixtures, or manually entered pass/fail flags.

This contract provides an append-only evidence ledger for Discovery, Pilot,
Operations, Commercial, Reliability, and Release-Gate evidence.

## Envelope

Each evidence envelope records:

- envelope_id
- evidence_type
- origin
- observed_at
- evidence_ref
- source_system_ref
- payload
- content_sha256

Origins:

- REAL_MERCHANT
- REAL_OPERATIONAL
- REAL_COMMERCIAL
- REAL_RELIABILITY
- TEST_FIXTURE

`TEST_FIXTURE` evidence is valid for validator/runtime tests but is never
decision-eligible.

## Integrity

The ledger enforces:

- timezone-aware timestamps
- `evidence://` references
- `source://` source-system references
- canonical SHA-256 payload verification
- append-only/idempotent envelope IDs
- same ID + changed content fails closed
- chain digest over prior entry + canonical envelope
- sensitive/direct-contact/credential metadata rejection
- decision evidence must be non-fixture

The ledger validates declared provenance and content integrity. It does not claim
cryptographic third-party attestation or independently prove that a merchant,
transaction, payment, incident, or commercial outcome happened.

## Decision Binding

A PMF gate proof must be bound to a decision-eligible evidence envelope whose
payload contains the same `evidence_digest`.

This prevents a gate result from being supplied without a corresponding ledger
entry.

## Rule

No `TEST_FIXTURE` envelope can be used to close Phase 7.
