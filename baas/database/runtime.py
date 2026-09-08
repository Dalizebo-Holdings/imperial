from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import re
from typing import Any


DATABASE_STATES = {
    "PROVISIONING",
    "READY",
    "SUSPENDED",
    "DECOMMISSIONED",
}

STATE_TRANSITIONS = {
    "PROVISIONING": {"READY", "DECOMMISSIONED"},
    "READY": {"SUSPENDED", "DECOMMISSIONED"},
    "SUSPENDED": {"READY", "DECOMMISSIONED"},
    "DECOMMISSIONED": set(),
}

ENVIRONMENTS = {
    "DEVELOPMENT",
    "PREVIEW",
    "PRODUCTION",
}

SSL_MODES = {
    "require",
    "verify-ca",
    "verify-full",
}

SECRET_REF = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
)


class DatabaseBaaSError(ValueError):
    pass


def _iso(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DatabaseBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if result.tzinfo is None:
        raise DatabaseBaaSError(
            "timestamp must be timezone-aware"
        )

    return result


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise DatabaseBaaSError(
            f"{name} must not be empty"
        )
    return result


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    environment_type: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
        }.items():
            _text(name, value)

        if self.environment_type not in ENVIRONMENTS:
            raise DatabaseBaaSError(
                f"unsupported environment_type: {self.environment_type}"
            )


@dataclass(frozen=True)
class ConnectionPolicy:
    max_connections: int
    connect_timeout_seconds: int
    statement_timeout_ms: int
    idle_transaction_timeout_ms: int
    ssl_mode: str
    read_only: bool = False

    def validate(
        self,
        *,
        environment_type: str,
    ) -> None:
        for name, value in {
            "max_connections": self.max_connections,
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "statement_timeout_ms": self.statement_timeout_ms,
            "idle_transaction_timeout_ms": (
                self.idle_transaction_timeout_ms
            ),
        }.items():
            if not isinstance(value, int) or value < 1:
                raise DatabaseBaaSError(
                    f"{name} must be an integer >= 1"
                )

        if self.ssl_mode not in SSL_MODES:
            raise DatabaseBaaSError(
                f"unsupported ssl_mode: {self.ssl_mode}"
            )

        if (
            environment_type == "PRODUCTION"
            and self.ssl_mode != "verify-full"
        ):
            raise DatabaseBaaSError(
                "production database requires ssl_mode=verify-full"
            )


@dataclass(frozen=True)
class ManagedDatabase:
    database_id: str
    tenant: TenantScope
    name: str
    engine: str
    engine_version: str
    dsn_ref: str
    schema: str
    state: str
    connection_policy: ConnectionPolicy
    backup_policy_ref: str | None
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _text("database_id", self.database_id)
        self.tenant.validate()
        _text("name", self.name)
        _text("engine_version", self.engine_version)

        if self.engine != "PostgreSQL":
            raise DatabaseBaaSError(
                "Database BaaS P0 engine must be PostgreSQL"
            )

        if not SECRET_REF.fullmatch(
            str(self.dsn_ref).strip()
        ):
            raise DatabaseBaaSError(
                "dsn_ref must be an opaque secret://, vault://, or kms:// reference"
            )

        if not re.fullmatch(
            r"[a-z_][a-z0-9_]{0,62}",
            str(self.schema).strip(),
        ):
            raise DatabaseBaaSError(
                "schema must be a safe PostgreSQL identifier"
            )

        if self.state not in DATABASE_STATES:
            raise DatabaseBaaSError(
                f"invalid database state: {self.state}"
            )

        self.connection_policy.validate(
            environment_type=self.tenant.environment_type,
        )

        if (
            self.tenant.environment_type == "PRODUCTION"
            and self.state == "READY"
            and not str(self.backup_policy_ref or "").strip()
        ):
            raise DatabaseBaaSError(
                "production READY database requires backup_policy_ref"
            )

        _iso(self.created_at)
        _iso(self.updated_at)


@dataclass(frozen=True)
class MigrationIntent:
    migration_id: str
    database_id: str
    version: int
    checksum: str
    description: str
    transactional: bool
    reversible: bool
    rollback_reference: str | None
    requested_at: str
    non_reversible_reason: str | None = None

    def validate(
        self,
        *,
        environment_type: str,
    ) -> None:
        for name, value in {
            "migration_id": self.migration_id,
            "database_id": self.database_id,
            "description": self.description,
        }.items():
            _text(name, value)

        if not isinstance(self.version, int) or self.version < 1:
            raise DatabaseBaaSError(
                "migration version must be an integer >= 1"
            )

        if not re.fullmatch(r"[a-f0-9]{64}", self.checksum):
            raise DatabaseBaaSError(
                "migration checksum must be SHA-256 hex"
            )

        if not self.transactional:
            raise DatabaseBaaSError(
                "BaaS P0 migrations must be transactional"
            )

        _iso(self.requested_at)

        if environment_type == "PRODUCTION":
            if self.reversible:
                if not str(
                    self.rollback_reference or ""
                ).strip():
                    raise DatabaseBaaSError(
                        "reversible production migration requires rollback_reference"
                    )
            else:
                if not str(
                    self.non_reversible_reason or ""
                ).strip():
                    raise DatabaseBaaSError(
                        "non-reversible production migration requires explicit reason"
                    )


@dataclass(frozen=True)
class RestoreIntent:
    restore_id: str
    database_id: str
    backup_reference: str
    target_environment_id: str
    requested_at: str

    def validate(self) -> None:
        for name, value in {
            "restore_id": self.restore_id,
            "database_id": self.database_id,
            "backup_reference": self.backup_reference,
            "target_environment_id": self.target_environment_id,
        }.items():
            _text(name, value)

        _iso(self.requested_at)


@dataclass(frozen=True)
class QueryObservation:
    database_id: str
    correlation_id: str
    operation: str
    duration_ms: float
    row_count: int | None
    success: bool
    error_code: str | None = None

    def validate(self) -> None:
        for name, value in {
            "database_id": self.database_id,
            "correlation_id": self.correlation_id,
            "operation": self.operation,
        }.items():
            _text(name, value)

        if not isinstance(self.duration_ms, (int, float)):
            raise DatabaseBaaSError(
                "duration_ms must be numeric"
            )

        if self.duration_ms < 0:
            raise DatabaseBaaSError(
                "duration_ms must be >= 0"
            )

        if (
            self.row_count is not None
            and (
                not isinstance(self.row_count, int)
                or self.row_count < 0
            )
        ):
            raise DatabaseBaaSError(
                "row_count must be an integer >= 0 when provided"
            )


class TenantDatabaseManager:
    def __init__(self) -> None:
        self._databases: dict[str, ManagedDatabase] = {}
        self._migration_intents: dict[
            tuple[str, int],
            MigrationIntent,
        ] = {}
        self._restore_intents: dict[
            str,
            RestoreIntent,
        ] = {}
        self._observations: list[QueryObservation] = []

    @staticmethod
    def _validate_request_context(
        request_context: Any,
    ) -> None:
        if hasattr(request_context, "validate"):
            request_context.validate()

        required = [
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
            "kernel_authorization_ref",
            "correlation_id",
        ]

        for name in required:
            value = getattr(
                request_context,
                name,
                None,
            )
            _text(name, value)

        if not str(
            request_context.kernel_authorization_ref
        ).startswith("kernel_auth_"):
            raise DatabaseBaaSError(
                "database management requires Kernel authorization evidence"
            )

    @staticmethod
    def _same_tenant(
        database: ManagedDatabase,
        request_context: Any,
    ) -> bool:
        tenant = database.tenant

        return (
            tenant.organization_id
            == request_context.organization_id
            and tenant.workspace_id
            == request_context.workspace_id
            and tenant.project_id
            == request_context.project_id
            and tenant.environment_id
            == request_context.environment_id
        )

    def register(
        self,
        *,
        database: ManagedDatabase,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        database.validate()

        if not self._same_tenant(
            database,
            request_context,
        ):
            raise DatabaseBaaSError(
                "database tenant scope does not match request context"
            )

        if database.database_id in self._databases:
            raise DatabaseBaaSError(
                f"database already registered: {database.database_id}"
            )

        self._databases[
            database.database_id
        ] = database

    def get(
        self,
        *,
        database_id: str,
        request_context: Any,
    ) -> ManagedDatabase:
        self._validate_request_context(
            request_context
        )

        database = self._databases.get(
            str(database_id).strip()
        )

        if database is None:
            raise DatabaseBaaSError(
                "database not found"
            )

        if not self._same_tenant(
            database,
            request_context,
        ):
            raise DatabaseBaaSError(
                "cross-tenant database access denied"
            )

        return database

    def transition(
        self,
        *,
        database_id: str,
        target_state: str,
        request_context: Any,
        now: str | None = None,
        backup_policy_ref: str | None = None,
    ) -> ManagedDatabase:
        database = self.get(
            database_id=database_id,
            request_context=request_context,
        )

        target = str(target_state).strip().upper()

        if target not in DATABASE_STATES:
            raise DatabaseBaaSError(
                f"invalid target state: {target}"
            )

        if target not in STATE_TRANSITIONS[
            database.state
        ]:
            raise DatabaseBaaSError(
                f"illegal database transition: {database.state} -> {target}"
            )

        updated = replace(
            database,
            state=target,
            backup_policy_ref=(
                backup_policy_ref
                if backup_policy_ref is not None
                else database.backup_policy_ref
            ),
            updated_at=(
                _now_iso(now)
            ),
        )
        updated.validate()

        self._databases[
            database.database_id
        ] = updated
        return updated

    def record_migration_intent(
        self,
        *,
        intent: MigrationIntent,
        request_context: Any,
    ) -> None:
        database = self.get(
            database_id=intent.database_id,
            request_context=request_context,
        )

        intent.validate(
            environment_type=(
                database.tenant.environment_type
            )
        )

        key = (
            intent.database_id,
            intent.version,
        )

        existing = self._migration_intents.get(key)

        if existing is not None:
            if existing.checksum != intent.checksum:
                raise DatabaseBaaSError(
                    "migration version checksum conflict"
                )
            raise DatabaseBaaSError(
                "migration intent already recorded"
            )

        self._migration_intents[
            key
        ] = intent

    def record_restore_intent(
        self,
        *,
        intent: RestoreIntent,
        request_context: Any,
    ) -> None:
        self.get(
            database_id=intent.database_id,
            request_context=request_context,
        )
        intent.validate()

        if (
            intent.target_environment_id
            != request_context.environment_id
        ):
            raise DatabaseBaaSError(
                "restore target environment must match request context"
            )

        if intent.restore_id in self._restore_intents:
            raise DatabaseBaaSError(
                "restore intent already recorded"
            )

        self._restore_intents[
            intent.restore_id
        ] = intent

    def observe_query(
        self,
        *,
        observation: QueryObservation,
        request_context: Any,
    ) -> None:
        self.get(
            database_id=observation.database_id,
            request_context=request_context,
        )
        observation.validate()

        if (
            observation.correlation_id
            != request_context.correlation_id
        ):
            raise DatabaseBaaSError(
                "query observation correlation_id mismatch"
            )

        self._observations.append(
            observation
        )

    def connection_plan(
        self,
        *,
        database_id: str,
        request_context: Any,
    ) -> dict[str, Any]:
        database = self.get(
            database_id=database_id,
            request_context=request_context,
        )

        if database.state != "READY":
            raise DatabaseBaaSError(
                "database must be READY before connection planning"
            )

        return {
            "database_id": database.database_id,
            "dsn_ref": database.dsn_ref,
            "schema": database.schema,
            "engine": database.engine,
            "engine_version": database.engine_version,
            "ssl_mode": (
                database.connection_policy.ssl_mode
            ),
            "connect_timeout_seconds": (
                database.connection_policy.connect_timeout_seconds
            ),
            "statement_timeout_ms": (
                database.connection_policy.statement_timeout_ms
            ),
            "idle_transaction_timeout_ms": (
                database.connection_policy.idle_transaction_timeout_ms
            ),
            "read_only": (
                database.connection_policy.read_only
            ),
            "tenant_context": {
                "organization_id": (
                    database.tenant.organization_id
                ),
                "workspace_id": (
                    database.tenant.workspace_id
                ),
                "project_id": (
                    database.tenant.project_id
                ),
                "environment_id": (
                    database.tenant.environment_id
                ),
                "correlation_id": (
                    request_context.correlation_id
                ),
            },
        }


def _now_iso(value: str | None = None) -> str:
    if value is None:
        return datetime.now(
            timezone.utc
        ).isoformat()

    _iso(value)
    return value
