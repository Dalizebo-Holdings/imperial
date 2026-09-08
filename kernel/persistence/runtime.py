from __future__ import annotations

from dataclasses import dataclass
import re


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

SECRET_REF_PATTERN = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
)


class PostgresBoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class PostgresConfig:
    dsn_ref: str
    environment_type: str
    application_name: str = "dalizebo-kernel"
    schema: str = "kernel"
    ssl_mode: str = "require"
    connect_timeout_seconds: int = 10
    statement_timeout_ms: int = 30000
    idle_transaction_timeout_ms: int = 30000

    def validate(self) -> None:
        if not SECRET_REF_PATTERN.fullmatch(
            str(self.dsn_ref).strip()
        ):
            raise PostgresBoundaryError(
                "dsn_ref must be an opaque secret://, vault://, or kms:// reference"
            )

        env = str(self.environment_type).strip().upper()
        if env not in ENVIRONMENTS:
            raise PostgresBoundaryError(
                f"unsupported environment_type: {env}"
            )

        if not str(self.application_name).strip():
            raise PostgresBoundaryError(
                "application_name must not be empty"
            )

        if not re.fullmatch(
            r"[a-z_][a-z0-9_]{0,62}",
            str(self.schema).strip(),
        ):
            raise PostgresBoundaryError(
                "schema must be a safe PostgreSQL identifier"
            )

        if self.ssl_mode not in SSL_MODES:
            raise PostgresBoundaryError(
                f"unsupported ssl_mode: {self.ssl_mode}"
            )

        for name, value in {
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "statement_timeout_ms": self.statement_timeout_ms,
            "idle_transaction_timeout_ms": (
                self.idle_transaction_timeout_ms
            ),
        }.items():
            if not isinstance(value, int) or value < 1:
                raise PostgresBoundaryError(
                    f"{name} must be an integer >= 1"
                )

        if env == "PRODUCTION" and self.ssl_mode != "verify-full":
            raise PostgresBoundaryError(
                "production PostgreSQL requires ssl_mode=verify-full"
            )


@dataclass(frozen=True)
class TenantSessionContext:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    actor_id: str
    correlation_id: str

    def validate(self) -> None:
        values = {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
        }

        missing = [
            name
            for name, value in values.items()
            if not str(value).strip()
        ]

        if missing:
            raise PostgresBoundaryError(
                "missing tenant session fields: "
                + ", ".join(missing)
            )


def transaction_prelude(
    *,
    config: PostgresConfig,
    tenant: TenantSessionContext,
) -> list[tuple[str, tuple[str, ...]]]:
    config.validate()
    tenant.validate()

    return [
        ("BEGIN", ()),
        (
            "SELECT set_config('app.organization_id', %s, true)",
            (tenant.organization_id,),
        ),
        (
            "SELECT set_config('app.workspace_id', %s, true)",
            (tenant.workspace_id,),
        ),
        (
            "SELECT set_config('app.project_id', %s, true)",
            (tenant.project_id,),
        ),
        (
            "SELECT set_config('app.environment_id', %s, true)",
            (tenant.environment_id,),
        ),
        (
            "SELECT set_config('app.actor_id', %s, true)",
            (tenant.actor_id,),
        ),
        (
            "SELECT set_config('app.correlation_id', %s, true)",
            (tenant.correlation_id,),
        ),
        (
            "SET LOCAL statement_timeout = %s",
            (str(config.statement_timeout_ms),),
        ),
        (
            "SET LOCAL idle_in_transaction_session_timeout = %s",
            (str(config.idle_transaction_timeout_ms),),
        ),
    ]


def commit_statement() -> str:
    return "COMMIT"


def rollback_statement() -> str:
    return "ROLLBACK"
