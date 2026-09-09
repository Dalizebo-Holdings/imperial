# Phase 7 — Parallel Design-Partner Execution

## Purpose

This workflow allows design-partner recruitment to proceed while the canonical
Discovery interview target is still incomplete.

The interview target is **deferred, not waived**.

This workflow must not:

- mark the Discovery Gate PASS
- mark Phase 7 complete
- authorize Phase 8
- fabricate a design-partner commitment

## Linkage

A design-partner candidate must link to a previously ingested real
`DISCOVERY_INTERVIEW` evidence record through the same opaque `merchant_ref`.

The runner reads the durable evidence ledger and lists eligible interviewed
merchants.

## Eligibility

A design partner must truthfully satisfy all canonical criteria:

- active retail operations
- real inventory
- real customers
- confirmed transaction volume
- willingness to test Commerce and/or POS
- ability to provide structured feedback

The runner fails closed if any criterion is false.

## Execute

List eligible interviewed merchants:

```bash
python scripts/phase7-design-partner.py list
```

Create a real candidate commitment:

```bash
python scripts/phase7-design-partner.py create
```

Then validate and ingest:

```bash
python scripts/phase7-evidence-collect.py validate-inbox
python scripts/phase7-evidence-collect.py ingest-inbox
python scripts/phase7-evidence-collect.py progress
```

New commitments start as:

`CANDIDATE`

Pilot activation remains a separate evidence-backed step.

## Phase Boundary

The canonical Discovery Gate still requires:

- 20+ interviews
- >=80% material-problem confirmation
- 5+ commitments
- 3+ active pilots

Phase 8 remains blocked until `PHASE7_COMPLETE`.
