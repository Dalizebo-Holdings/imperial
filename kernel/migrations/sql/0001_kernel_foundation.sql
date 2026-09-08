-- Dalizebo Kernel P0 PostgreSQL foundation.
-- This migration contains schema only. No credentials or secret values.

CREATE SCHEMA IF NOT EXISTS kernel;

CREATE TABLE IF NOT EXISTS kernel.schema_migrations (
    version integer PRIMARY KEY,
    name text NOT NULL UNIQUE,
    checksum char(64) NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS kernel.organizations (
    id text PRIMARY KEY,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS kernel.workspaces (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE CASCADE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id)
);

CREATE INDEX IF NOT EXISTS idx_workspaces_organization
    ON kernel.workspaces (organization_id);

CREATE TABLE IF NOT EXISTS kernel.projects (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE CASCADE,
    workspace_id text NOT NULL
        REFERENCES kernel.workspaces(id) ON DELETE CASCADE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, workspace_id, id)
);

CREATE INDEX IF NOT EXISTS idx_projects_tenant
    ON kernel.projects (organization_id, workspace_id);

CREATE TABLE IF NOT EXISTS kernel.environments (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE CASCADE,
    workspace_id text NOT NULL
        REFERENCES kernel.workspaces(id) ON DELETE CASCADE,
    project_id text NOT NULL
        REFERENCES kernel.projects(id) ON DELETE CASCADE,
    environment_type text NOT NULL
        CHECK (environment_type IN ('DEVELOPMENT', 'PREVIEW', 'PRODUCTION')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, workspace_id, project_id, id)
);

CREATE INDEX IF NOT EXISTS idx_environments_tenant
    ON kernel.environments (
        organization_id,
        workspace_id,
        project_id
    );

CREATE TABLE IF NOT EXISTS kernel.idempotency_records (
    key text NOT NULL,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE CASCADE,
    operation text NOT NULL,
    request_hash char(64) NOT NULL,
    status text NOT NULL
        CHECK (status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED')),
    response_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (organization_id, operation, key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_expiry
    ON kernel.idempotency_records (expires_at);

CREATE TABLE IF NOT EXISTS kernel.audit_records (
    audit_id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    actor_type text NOT NULL,
    actor_id text NOT NULL,
    action text NOT NULL,
    resource_type text NOT NULL,
    resource_id text NOT NULL,
    timestamp timestamptz NOT NULL,
    correlation_id text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    previous_hash char(64) NOT NULL DEFAULT '',
    record_hash char(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_time
    ON kernel.audit_records (organization_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_correlation
    ON kernel.audit_records (correlation_id);

CREATE TABLE IF NOT EXISTS kernel.outbox_events (
    event_id text PRIMARY KEY,
    event_type text NOT NULL,
    event_version text NOT NULL,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text,
    project_id text,
    environment_id text,
    resource_type text NOT NULL,
    resource_id text NOT NULL,
    occurred_at timestamptz NOT NULL,
    correlation_id text NOT NULL,
    actor_type text NOT NULL,
    actor_id text NOT NULL,
    payload jsonb NOT NULL,
    outbox_status text NOT NULL DEFAULT 'COMMITTED'
        CHECK (outbox_status IN ('COMMITTED', 'PUBLISHED', 'FAILED')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_outbox_unpublished
    ON kernel.outbox_events (created_at)
    WHERE published_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_outbox_tenant
    ON kernel.outbox_events (organization_id, created_at);
