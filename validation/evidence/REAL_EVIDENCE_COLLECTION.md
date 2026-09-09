# Phase 7 — Real Evidence Collection Kit

## Purpose

This operator workflow keeps the active evidence inbox clean and allows Phase 7
evidence to be collected incrementally.

It does not fabricate evidence and does not mark Phase 7 complete.

## Private Paths

Default ledger:

`~/.local/share/dalizebo/imperial/validation/evidence-ledger.jsonl`

Default active inbox:

`~/.local/share/dalizebo/imperial/validation/inbox/`

Default template library:

`~/.local/share/dalizebo/imperial/validation/templates/`

The inbox and template library are outside Git.

## Initialize

```bash
python scripts/validation-evidence.py init
python scripts/phase7-evidence-collect.py init-inbox
```

`init-inbox` now creates:

- an **empty active inbox**
- a separate private template library containing the 11 evidence templates

Templates no longer poison active preflight with placeholder files.

## Create One Evidence Record

```bash
python scripts/phase7-evidence-collect.py new   discovery-interview   interview-001
```

This copies exactly one template into the active inbox as:

`interview-001.json`

The new record intentionally contains `__REPLACE__` placeholders and cannot be
ingested until real source-backed values replace them.

## Inspect Workspace

```bash
python scripts/phase7-evidence-collect.py workspace
```

## Validate Active Inbox

```bash
python scripts/phase7-evidence-collect.py validate-inbox
```

Preflight scans **only active inbox JSON files**. The separate template library
is ignored.

An empty inbox is valid and represents zero ready evidence.

## Ingest

```bash
python scripts/phase7-evidence-collect.py ingest-inbox
```

Whole-inbox preflight still runs before any append.

Rerunning the same batch remains replay-safe.

## Progress

```bash
python scripts/phase7-evidence-collect.py progress
```

`TEST_FIXTURE` evidence remains excluded from real PMF progress.

## Template Types

- discovery-interview
- design-partner-commitment
- pilot-onboarding
- pilot-metric-snapshot
- capacity-snapshot
- technical-attestation
- merchant-feedback
- support-evidence
- incident-evidence
- public-mvp-90d
- gate-proof

## Governing Rule

Real Phase 7 outcomes require source-backed evidence.

Phase 8 remains blocked until the PMF decision engine returns:

`PHASE7_COMPLETE`
