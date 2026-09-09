ALTER TABLE kernel.outbox_events
    ADD COLUMN IF NOT EXISTS publish_ack_ref text;

ALTER TABLE kernel.outbox_events
    ADD CONSTRAINT outbox_events_publish_ack_ref_check
    CHECK (
        publish_ack_ref IS NULL
        OR length(btrim(publish_ack_ref)) > 0
    );
