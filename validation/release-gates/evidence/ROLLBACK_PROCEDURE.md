# Phase 7 Rollback Procedure

## Trigger Conditions

Rollback/recovery is initiated for:
- failed health/readiness checks
- critical tenant-isolation defect
- payment or inventory integrity failure
- release causing critical operational regression
- failed migration or migration-integrity validation

## Application Release Recovery

1. Stop further rollout.
2. Identify the last known-good release/commit.
3. Preserve logs, metrics, correlation IDs and audit evidence.
4. Redeploy the previous immutable application release.
5. Run health/readiness validation.
6. Run tenant-isolation, payment-consistency and inventory-consistency validators.
7. Re-enable traffic only after validation succeeds.

## Database / Migration Recovery

Kernel migration history is immutable and checksum protected.

- Never manually delete or rewrite `kernel.schema_migrations`.
- Never assume a schema downgrade is safe.
- Use a corrective forward migration where possible.
- Use an explicitly documented reversible migration only when its reversal is verified.
- For unrecoverable state, restore from a verified backup and replay safe forward migrations.

## Validation After Recovery

Required validation includes:

- Kernel trust-boundary validation
- Kernel observability validation
- BaaS payment validation
- Commerce inventory validation
- POS transaction validation
- backup/recovery validation where data restoration occurred

## Exit Criteria

Recovery completes only when:

- health and readiness pass
- tenant boundaries pass
- payment consistency passes
- inventory consistency passes
- migration history validates
- no unresolved critical integrity defect remains

This procedure defines the rollback/recovery path.
It does not claim that a production rollback has been executed.

Status: SATISFIED
