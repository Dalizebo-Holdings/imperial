# Phase 7 — Design-Partner Eligibility Triage

The design-partner CLI must separate uncommitted discovery interviews into
`eligible` and `discovery_only` before selection.

Canonical eligibility requires all six criteria:

- active retail operations
- real inventory
- real customers
- recurring transaction volume confirmed
- willingness to test
- structured feedback available

`discovery_only` interviews remain valid discovery evidence and must not be
mutated to manufacture eligibility.

Run:

```bash
python scripts/phase7-design-partner.py list
```

Only entries in `eligible` may be selected by:

```bash
python scripts/phase7-design-partner.py create
```

The output also reports `missing_criteria` and
`recruitment_priority_missing_criteria`.

Discovery remains deferred, not waived. Phase 8 remains blocked.
