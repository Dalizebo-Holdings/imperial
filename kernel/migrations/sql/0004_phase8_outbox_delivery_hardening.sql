-- Phase 8: durable transactional-outbox delivery state.

ALTER TABLE kernel.outbox_events
    DROP CONSTRAINT IF EXISTS outbox_events_outbox_status_check;

ALTER TABLE kernel.outbox_events
    ADD CONSTRAINT outbox_events_outbox_status_check
    CHECK (
        outbox_status IN (
            'COMMITTED',
            'RETRY_PENDING',
            'PUBLISHED',
            'DEAD_LETTER',
            'FAILED'
        )
    );

ALTER TABLE kernel.outbox_events
    ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_attempts integer NOT NULL DEFAULT 8,
    ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS last_error_code text,
    ADD COLUMN IF NOT EXISTS lock_owner text,
    ADD COLUMN IF NOT EXISTS locked_at timestamptz,
    ADD COLUMN IF NOT EXISTS lock_expires_at timestamptz,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE kernel.outbox_events
    ADD CONSTRAINT outbox_events_attempt_count_check
        CHECK (attempt_count >= 0),
    ADD CONSTRAINT outbox_events_max_attempts_check
        CHECK (max_attempts BETWEEN 1 AND 25),
    ADD CONSTRAINT outbox_events_attempt_bound_check
        CHECK (attempt_count <= max_attempts),
    ADD CONSTRAINT outbox_events_lock_shape_check
        CHECK (
            (
                lock_owner IS NULL
                AND locked_at IS NULL
                AND lock_expires_at IS NULL
            )
            OR
            (
                lock_owner IS NOT NULL
                AND locked_at IS NOT NULL
                AND lock_expires_at IS NOT NULL
            )
        );

CREATE INDEX IF NOT EXISTS idx_outbox_claimable
    ON kernel.outbox_events (next_attempt_at, created_at)
    WHERE published_at IS NULL
      AND outbox_status IN ('COMMITTED', 'RETRY_PENDING');

CREATE INDEX IF NOT EXISTS idx_outbox_expired_lease
    ON kernel.outbox_events (lock_expires_at)
    WHERE lock_expires_at IS NOT NULL
      AND published_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_outbox_dead_letter
    ON kernel.outbox_events (organization_id, updated_at DESC)
    WHERE outbox_status = 'DEAD_LETTER';
