from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Any


RESOURCE_CLASSES = {
    "DATABASE",
    "OBJECT_STORAGE",
    "KERNEL_STATE",
}

ENVIRONMENT_TYPES = {
    "DEVELOPMENT",
    "PREVIEW",
    "PRODUCTION",
}

SECRET_REF_PATTERN = re.compile(
    r"(?:secret|vault|kms)://[A-Za-z0-9._~:/-]+"
)

ADAPTER_REF_PATTERN = re.compile(
    r"adapter://[A-Za-z0-9._~:/-]+"
)

BACKUP_REF_PATTERN = re.compile(
    r"(?:backup|snapshot|object|provider-backup)://[A-Za-z0-9._~:/-]+"
)

PROVIDER_ID_PATTERN = re.compile(
    r"[a-z][a-z0-9._-]{1,63}"
)

SHA256_PATTERN = re.compile(
    r"[a-f0-9]{64}"
)

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "secret_value",
    "client_secret",
    "private_key",
    "session_token",
    "webhook_secret",
    "provider_credentials",
    "card_number",
    "cvv",
    "cvc",
    "pan",
}


class BackupsBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise BackupsBaaSError(
            f"{name} must not be empty"
        )
    return result


def _time(
    value: str | None = None,
) -> datetime:
    if value is None:
        return datetime.now(
            timezone.utc
        )

    try:
        parsed = datetime.fromisoformat(
            value
        )
    except ValueError as exc:
        raise BackupsBaaSError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise BackupsBaaSError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _contains_sensitive(
    value: Any,
) -> bool:
    if isinstance(
        value,
        dict,
    ):
        for key, item in value.items():
            if (
                str(key).strip().lower()
                in SENSITIVE_KEYS
            ):
                return True

            if _contains_sensitive(
                item
            ):
                return True

    elif isinstance(
        value,
        (list, tuple),
    ):
        return any(
            _contains_sensitive(item)
            for item in value
        )

    return False


def _validate_metadata(
    value: dict[str, Any],
) -> None:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise BackupsBaaSError(
            "backup metadata must be JSON-compatible"
        ) from exc

    if len(encoded) > 8192:
        raise BackupsBaaSError(
            "backup metadata exceeds 8192 bytes"
        )

    if _contains_sensitive(
        value
    ):
        raise BackupsBaaSError(
            "backup metadata contains secret-bearing fields"
        )


def _validate_notes(
    notes: str,
) -> str:
    value = str(notes)

    if len(value) > 2048:
        raise BackupsBaaSError(
            "restore verification notes exceed 2048 characters"
        )

    lowered = value.lower()

    for key in SENSITIVE_KEYS:
        if key in lowered:
            raise BackupsBaaSError(
                "restore verification notes contain secret-bearing terms"
            )

    return value


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": (
                self.organization_id
            ),
            "workspace_id": (
                self.workspace_id
            ),
            "project_id": (
                self.project_id
            ),
            "environment_id": (
                self.environment_id
            ),
        }.items():
            _text(
                name,
                value,
            )


@dataclass(frozen=True)
class BackupProvider:
    provider_id: str
    adapter_ref: str
    credential_ref: str
    supports_encryption: bool
    supports_immutable_copy: bool
    supports_offsite_copy: bool
    supports_restore: bool
    enabled: bool = True

    def validate(self) -> None:
        if not PROVIDER_ID_PATTERN.fullmatch(
            str(
                self.provider_id
            ).strip()
        ):
            raise BackupsBaaSError(
                "provider_id must be a safe identifier"
            )

        if not ADAPTER_REF_PATTERN.fullmatch(
            str(
                self.adapter_ref
            ).strip()
        ):
            raise BackupsBaaSError(
                "adapter_ref must use adapter://"
            )

        if not SECRET_REF_PATTERN.fullmatch(
            str(
                self.credential_ref
            ).strip()
        ):
            raise BackupsBaaSError(
                "credential_ref must be an opaque secret reference"
            )


@dataclass(frozen=True)
class TenantBackupPolicy:
    policy_id: str
    tenant: TenantScope
    resource_class: str
    resource_ref: str
    environment_type: str
    provider_id: str
    encrypted: bool
    retention_days: int
    frequency_minutes: int
    rpo_minutes: int
    rto_minutes: int
    immutable_copy: bool
    offsite_copy: bool
    restore_test_interval_days: int
    enabled: bool
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "policy_id",
            self.policy_id,
        )
        self.tenant.validate()

        if (
            self.resource_class
            not in RESOURCE_CLASSES
        ):
            raise BackupsBaaSError(
                "unsupported resource_class"
            )

        _text(
            "resource_ref",
            self.resource_ref,
        )

        if (
            self.environment_type
            not in ENVIRONMENT_TYPES
        ):
            raise BackupsBaaSError(
                "unsupported environment_type"
            )

        if not PROVIDER_ID_PATTERN.fullmatch(
            str(
                self.provider_id
            ).strip()
        ):
            raise BackupsBaaSError(
                "provider_id must be a safe identifier"
            )

        for name, value in {
            "retention_days": (
                self.retention_days
            ),
            "frequency_minutes": (
                self.frequency_minutes
            ),
            "rpo_minutes": (
                self.rpo_minutes
            ),
            "rto_minutes": (
                self.rto_minutes
            ),
            "restore_test_interval_days": (
                self.restore_test_interval_days
            ),
        }.items():
            if (
                not isinstance(
                    value,
                    int,
                )
                or isinstance(
                    value,
                    bool,
                )
                or value < 1
            ):
                raise BackupsBaaSError(
                    f"{name} must be an integer >= 1"
                )

        if (
            self.rpo_minutes
            > self.frequency_minutes
        ):
            raise BackupsBaaSError(
                "rpo_minutes may not exceed frequency_minutes"
            )

        if (
            self.environment_type
            == "PRODUCTION"
        ):
            if not self.encrypted:
                raise BackupsBaaSError(
                    "production backups must be encrypted"
                )

            if not self.immutable_copy:
                raise BackupsBaaSError(
                    "production backups require immutable_copy"
                )

            if not self.offsite_copy:
                raise BackupsBaaSError(
                    "production backups require offsite_copy"
                )

        _validate_metadata(
            self.metadata
        )


@dataclass(frozen=True)
class BackupExecutionPlan:
    backup_id: str
    policy_id: str
    resource_class: str
    resource_ref: str
    provider_id: str
    provider_adapter_ref: str
    provider_credential_ref: str
    encrypted_required: bool
    immutable_copy_required: bool
    offsite_copy_required: bool
    retention_days: int
    rpo_minutes: int
    rto_minutes: int
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[str, Any]
    state: str = "READY_FOR_BACKUP_ADAPTER"


@dataclass(frozen=True)
class BackupEvidence:
    backup_id: str
    policy_id: str
    backup_reference: str
    checksum_sha256: str | None
    started_at: str
    completed_at: str
    encrypted: bool
    immutable_copy: bool
    offsite_copy: bool
    success: bool
    error_code: str | None = None

    def validate(self) -> None:
        _text(
            "backup_id",
            self.backup_id,
        )
        _text(
            "policy_id",
            self.policy_id,
        )

        if not BACKUP_REF_PATTERN.fullmatch(
            str(
                self.backup_reference
            ).strip()
        ):
            raise BackupsBaaSError(
                "backup_reference must use an approved opaque backup scheme"
            )

        started = _time(
            self.started_at
        )
        completed = _time(
            self.completed_at
        )

        if completed < started:
            raise BackupsBaaSError(
                "completed_at may not precede started_at"
            )

        if self.success:
            if (
                self.checksum_sha256 is None
                or not SHA256_PATTERN.fullmatch(
                    str(
                        self.checksum_sha256
                    )
                )
            ):
                raise BackupsBaaSError(
                    "successful backup requires checksum_sha256"
                )

            if self.error_code is not None:
                raise BackupsBaaSError(
                    "successful backup may not contain error_code"
                )
        else:
            _text(
                "error_code",
                self.error_code,
            )


@dataclass(frozen=True)
class RestoreTestPlan:
    restore_test_id: str
    policy_id: str
    backup_id: str
    backup_reference: str
    provider_id: str
    provider_adapter_ref: str
    provider_credential_ref: str
    target_ref: str
    rto_minutes: int
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[str, Any]
    state: str = "READY_FOR_RESTORE_TEST_ADAPTER"


@dataclass(frozen=True)
class RestoreEvidence:
    verification_id: str
    policy_id: str
    backup_id: str
    backup_reference: str
    tested_at: str
    success: bool
    restored_resource_reference: str
    checksum_verified: bool
    notes: str = ""

    def validate(self) -> None:
        for name, value in {
            "verification_id": (
                self.verification_id
            ),
            "policy_id": (
                self.policy_id
            ),
            "backup_id": (
                self.backup_id
            ),
            "restored_resource_reference": (
                self.restored_resource_reference
            ),
        }.items():
            _text(
                name,
                value,
            )

        if not BACKUP_REF_PATTERN.fullmatch(
            str(
                self.backup_reference
            ).strip()
        ):
            raise BackupsBaaSError(
                "restore evidence backup_reference is invalid"
            )

        _time(
            self.tested_at
        )

        if (
            self.success
            and not self.checksum_verified
        ):
            raise BackupsBaaSError(
                "successful restore verification requires checksum_verified"
            )

        _validate_notes(
            self.notes
        )


@dataclass(frozen=True)
class RestoreExecutionPlan:
    restore_id: str
    policy_id: str
    backup_id: str
    backup_reference: str
    target_ref: str
    provider_id: str
    provider_adapter_ref: str
    provider_credential_ref: str
    rpo_minutes: int
    rto_minutes: int
    tenant_context: dict[str, str]
    correlation_id: str
    kernel_authorization_ref: str
    audit_event: dict[str, Any]
    state: str = "READY_FOR_RESTORE_ADAPTER"


class BackupsService:
    def __init__(
        self,
        *,
        kernel_registry: Any,
        kernel_policy_type: Any,
        kernel_restore_verification_type: Any,
    ) -> None:
        if kernel_registry is None:
            raise BackupsBaaSError(
                "kernel_registry is required"
            )

        if not callable(
            kernel_policy_type
        ):
            raise BackupsBaaSError(
                "kernel_policy_type must be callable"
            )

        if not callable(
            kernel_restore_verification_type
        ):
            raise BackupsBaaSError(
                "kernel_restore_verification_type must be callable"
            )

        self._kernel_registry = (
            kernel_registry
        )
        self._kernel_policy_type = (
            kernel_policy_type
        )
        self._kernel_restore_verification_type = (
            kernel_restore_verification_type
        )

        self._providers: dict[
            str,
            BackupProvider,
        ] = {}
        self._policies: dict[
            str,
            TenantBackupPolicy,
        ] = {}
        self._evidence: dict[
            str,
            BackupEvidence,
        ] = {}
        self._policy_backups: dict[
            str,
            list[str],
        ] = {}
        self._restore_evidence: dict[
            str,
            RestoreEvidence,
        ] = {}

    @staticmethod
    def _validate_request_context(
        request_context: Any,
    ) -> None:
        if hasattr(
            request_context,
            "validate",
        ):
            request_context.validate()

        for name in [
            "request_id",
            "correlation_id",
            "service",
            "operation",
            "organization_id",
            "workspace_id",
            "project_id",
            "environment_id",
            "actor_id",
            "actor_type",
            "kernel_authorization_ref",
        ]:
            _text(
                name,
                getattr(
                    request_context,
                    name,
                    None,
                ),
            )

        if (
            str(
                request_context.service
            ).strip()
            != "backups"
        ):
            raise BackupsBaaSError(
                "BackupsService requires service=backups"
            )

        if not str(
            request_context.kernel_authorization_ref
        ).startswith(
            "kernel_auth_"
        ):
            raise BackupsBaaSError(
                "backup operations require Kernel authorization evidence"
            )

    @staticmethod
    def _tenant_from_context(
        request_context: Any,
    ) -> TenantScope:
        tenant = TenantScope(
            organization_id=(
                request_context.organization_id
            ),
            workspace_id=(
                request_context.workspace_id
            ),
            project_id=(
                request_context.project_id
            ),
            environment_id=(
                request_context.environment_id
            ),
        )
        tenant.validate()
        return tenant

    @staticmethod
    def _same_tenant(
        left: TenantScope,
        right: TenantScope,
    ) -> bool:
        return (
            left.organization_id
            == right.organization_id
            and left.workspace_id
            == right.workspace_id
            and left.project_id
            == right.project_id
            and left.environment_id
            == right.environment_id
        )

    def register_provider(
        self,
        *,
        provider: BackupProvider,
        request_context: Any,
    ) -> None:
        self._validate_request_context(
            request_context
        )
        provider.validate()

        if (
            provider.provider_id
            in self._providers
        ):
            raise BackupsBaaSError(
                "backup provider already registered"
            )

        self._providers[
            provider.provider_id
        ] = provider

    def register_policy(
        self,
        *,
        policy: TenantBackupPolicy,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(
            request_context
        )
        policy.validate()

        tenant = self._tenant_from_context(
            request_context
        )

        if not self._same_tenant(
            policy.tenant,
            tenant,
        ):
            raise BackupsBaaSError(
                "backup policy tenant scope mismatch"
            )

        provider = self._require_provider(
            policy.provider_id
        )

        if (
            policy.encrypted
            and not provider.supports_encryption
        ):
            raise BackupsBaaSError(
                "provider does not support required encryption"
            )

        if (
            policy.immutable_copy
            and not provider.supports_immutable_copy
        ):
            raise BackupsBaaSError(
                "provider does not support immutable copies"
            )

        if (
            policy.offsite_copy
            and not provider.supports_offsite_copy
        ):
            raise BackupsBaaSError(
                "provider does not support offsite copies"
            )

        if (
            policy.policy_id
            in self._policies
        ):
            raise BackupsBaaSError(
                "backup policy already registered"
            )

        kernel_policy = (
            self._kernel_policy_type(
                policy_id=(
                    policy.policy_id
                ),
                resource_class=(
                    policy.resource_class
                ),
                environment_type=(
                    policy.environment_type
                ),
                encrypted=(
                    policy.encrypted
                ),
                retention_days=(
                    policy.retention_days
                ),
                frequency_minutes=(
                    policy.frequency_minutes
                ),
                rpo_minutes=(
                    policy.rpo_minutes
                ),
                rto_minutes=(
                    policy.rto_minutes
                ),
                immutable_copy=(
                    policy.immutable_copy
                ),
                offsite_copy=(
                    policy.offsite_copy
                ),
                restore_test_interval_days=(
                    policy.restore_test_interval_days
                ),
                enabled=(
                    policy.enabled
                ),
                metadata={
                    "organization_id": (
                        policy.tenant.organization_id
                    ),
                    "workspace_id": (
                        policy.tenant.workspace_id
                    ),
                    "project_id": (
                        policy.tenant.project_id
                    ),
                    "environment_id": (
                        policy.tenant.environment_id
                    ),
                    "resource_ref": (
                        policy.resource_ref
                    ),
                    "provider_id": (
                        policy.provider_id
                    ),
                    **dict(
                        policy.metadata
                    ),
                },
            )
        )

        self._kernel_registry.register(
            kernel_policy
        )
        self._policies[
            policy.policy_id
        ] = policy
        self._policy_backups[
            policy.policy_id
        ] = []

        return {
            "policy": policy,
            "audit_event": (
                self._audit_event(
                    action=(
                        "backups.policy.register"
                    ),
                    resource_id=(
                        policy.policy_id
                    ),
                    policy=policy,
                    request_context=(
                        request_context
                    ),
                    timestamp=(
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    ),
                    metadata={
                        "resource_class": (
                            policy.resource_class
                        ),
                        "environment_type": (
                            policy.environment_type
                        ),
                        "provider_id": (
                            policy.provider_id
                        ),
                    },
                )
            ),
        }

    def backup_due(
        self,
        *,
        policy_id: str,
        request_context: Any,
        now: str | None = None,
    ) -> bool:
        policy = self._get_policy(
            policy_id=policy_id,
            request_context=(
                request_context
            ),
        )

        if not policy.enabled:
            return False

        successful = [
            self._evidence[
                backup_id
            ]
            for backup_id in self._policy_backups[
                policy.policy_id
            ]
            if (
                self._evidence[
                    backup_id
                ].success
            )
        ]

        if not successful:
            return True

        latest = max(
            successful,
            key=lambda item: (
                _time(
                    item.completed_at
                )
            ),
        )

        due_at = (
            _time(
                latest.completed_at
            )
            + timedelta(
                minutes=(
                    policy.frequency_minutes
                )
            )
        )

        return _time(
            now
        ) >= due_at

    def plan_backup(
        self,
        *,
        policy_id: str,
        request_context: Any,
        requested_at: str | None = None,
    ) -> BackupExecutionPlan:
        policy = self._get_policy(
            policy_id=policy_id,
            request_context=(
                request_context
            ),
        )

        if not policy.enabled:
            raise BackupsBaaSError(
                "backup policy is disabled"
            )

        current = _time(
            requested_at
        )

        if not self.backup_due(
            policy_id=policy_id,
            request_context=(
                request_context
            ),
            now=(
                current.isoformat()
            ),
        ):
            raise BackupsBaaSError(
                "backup is not due"
            )

        provider = self._require_provider(
            policy.provider_id
        )

        material = {
            "policy_id": (
                policy.policy_id
            ),
            "resource_ref": (
                policy.resource_ref
            ),
            "requested_at": (
                current.isoformat()
            ),
            "organization_id": (
                policy.tenant.organization_id
            ),
            "environment_id": (
                policy.tenant.environment_id
            ),
        }

        backup_id = (
            "backup_"
            + sha256(
                json.dumps(
                    material,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return BackupExecutionPlan(
            backup_id=backup_id,
            policy_id=(
                policy.policy_id
            ),
            resource_class=(
                policy.resource_class
            ),
            resource_ref=(
                policy.resource_ref
            ),
            provider_id=(
                provider.provider_id
            ),
            provider_adapter_ref=(
                provider.adapter_ref
            ),
            provider_credential_ref=(
                provider.credential_ref
            ),
            encrypted_required=(
                policy.encrypted
            ),
            immutable_copy_required=(
                policy.immutable_copy
            ),
            offsite_copy_required=(
                policy.offsite_copy
            ),
            retention_days=(
                policy.retention_days
            ),
            rpo_minutes=(
                policy.rpo_minutes
            ),
            rto_minutes=(
                policy.rto_minutes
            ),
            tenant_context={
                "organization_id": (
                    policy.tenant.organization_id
                ),
                "workspace_id": (
                    policy.tenant.workspace_id
                ),
                "project_id": (
                    policy.tenant.project_id
                ),
                "environment_id": (
                    policy.tenant.environment_id
                ),
            },
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            audit_event=(
                self._audit_event(
                    action=(
                        "backups.execution.plan"
                    ),
                    resource_id=(
                        backup_id
                    ),
                    policy=policy,
                    request_context=(
                        request_context
                    ),
                    timestamp=(
                        current.isoformat()
                    ),
                    metadata={
                        "provider_id": (
                            provider.provider_id
                        ),
                        "resource_ref": (
                            policy.resource_ref
                        ),
                    },
                )
            ),
        )

    def record_backup_evidence(
        self,
        *,
        evidence: BackupEvidence,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(
            request_context
        )
        evidence.validate()

        policy = self._get_policy(
            policy_id=(
                evidence.policy_id
            ),
            request_context=(
                request_context
            ),
        )

        if (
            evidence.backup_id
            in self._evidence
        ):
            existing = self._evidence[
                evidence.backup_id
            ]

            if existing != evidence:
                raise BackupsBaaSError(
                    "backup_id evidence conflict"
                )

            return {
                "created": False,
                "evidence": existing,
                "audit_event": None,
            }

        if evidence.success:
            if (
                policy.encrypted
                and not evidence.encrypted
            ):
                raise BackupsBaaSError(
                    "successful evidence lacks required encryption"
                )

            if (
                policy.immutable_copy
                and not evidence.immutable_copy
            ):
                raise BackupsBaaSError(
                    "successful evidence lacks required immutable copy"
                )

            if (
                policy.offsite_copy
                and not evidence.offsite_copy
            ):
                raise BackupsBaaSError(
                    "successful evidence lacks required offsite copy"
                )

        self._evidence[
            evidence.backup_id
        ] = evidence
        self._policy_backups[
            policy.policy_id
        ].append(
            evidence.backup_id
        )

        return {
            "created": True,
            "evidence": evidence,
            "audit_event": (
                self._audit_event(
                    action=(
                        "backups.evidence.record"
                    ),
                    resource_id=(
                        evidence.backup_id
                    ),
                    policy=policy,
                    request_context=(
                        request_context
                    ),
                    timestamp=(
                        evidence.completed_at
                    ),
                    metadata={
                        "success": (
                            evidence.success
                        ),
                        "backup_reference": (
                            evidence.backup_reference
                        ),
                        "checksum_sha256": (
                            evidence.checksum_sha256
                        ),
                        "error_code": (
                            evidence.error_code
                        ),
                    },
                )
            ),
        }

    def plan_restore_test(
        self,
        *,
        backup_id: str,
        target_ref: str,
        request_context: Any,
        requested_at: str | None = None,
    ) -> RestoreTestPlan:
        evidence, policy = (
            self._get_backup(
                backup_id=backup_id,
                request_context=(
                    request_context
                ),
            )
        )

        if not evidence.success:
            raise BackupsBaaSError(
                "failed backup cannot be restore-tested"
            )

        provider = self._require_provider(
            policy.provider_id
        )

        if not provider.supports_restore:
            raise BackupsBaaSError(
                "provider does not support restore"
            )

        target = _text(
            "target_ref",
            target_ref,
        )

        now = _time(
            requested_at
        ).isoformat()

        restore_test_id = (
            "restore_test_"
            + sha256(
                (
                    f"{backup_id}"
                    f"\x1f{target}"
                    f"\x1f{now}"
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return RestoreTestPlan(
            restore_test_id=(
                restore_test_id
            ),
            policy_id=(
                policy.policy_id
            ),
            backup_id=(
                evidence.backup_id
            ),
            backup_reference=(
                evidence.backup_reference
            ),
            provider_id=(
                provider.provider_id
            ),
            provider_adapter_ref=(
                provider.adapter_ref
            ),
            provider_credential_ref=(
                provider.credential_ref
            ),
            target_ref=target,
            rto_minutes=(
                policy.rto_minutes
            ),
            tenant_context={
                "organization_id": (
                    policy.tenant.organization_id
                ),
                "workspace_id": (
                    policy.tenant.workspace_id
                ),
                "project_id": (
                    policy.tenant.project_id
                ),
                "environment_id": (
                    policy.tenant.environment_id
                ),
            },
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            audit_event=(
                self._audit_event(
                    action=(
                        "backups.restore_test.plan"
                    ),
                    resource_id=(
                        restore_test_id
                    ),
                    policy=policy,
                    request_context=(
                        request_context
                    ),
                    timestamp=now,
                    metadata={
                        "backup_id": (
                            evidence.backup_id
                        ),
                        "backup_reference": (
                            evidence.backup_reference
                        ),
                        "target_ref": (
                            target
                        ),
                    },
                )
            ),
        )

    def record_restore_verification(
        self,
        *,
        evidence: RestoreEvidence,
        request_context: Any,
    ) -> dict[str, Any]:
        self._validate_request_context(
            request_context
        )
        evidence.validate()

        backup, policy = (
            self._get_backup(
                backup_id=(
                    evidence.backup_id
                ),
                request_context=(
                    request_context
                ),
            )
        )

        if (
            evidence.policy_id
            != policy.policy_id
        ):
            raise BackupsBaaSError(
                "restore verification policy mismatch"
            )

        if (
            evidence.backup_reference
            != backup.backup_reference
        ):
            raise BackupsBaaSError(
                "restore verification backup reference mismatch"
            )

        if (
            evidence.verification_id
            in self._restore_evidence
        ):
            existing = (
                self._restore_evidence[
                    evidence.verification_id
                ]
            )

            if existing != evidence:
                raise BackupsBaaSError(
                    "verification_id evidence conflict"
                )

            return {
                "created": False,
                "evidence": existing,
                "audit_event": None,
            }

        kernel_verification = (
            self._kernel_restore_verification_type(
                verification_id=(
                    evidence.verification_id
                ),
                policy_id=(
                    evidence.policy_id
                ),
                backup_reference=(
                    evidence.backup_reference
                ),
                tested_at=(
                    evidence.tested_at
                ),
                success=(
                    evidence.success
                ),
                restored_resource_reference=(
                    evidence.restored_resource_reference
                ),
                checksum_verified=(
                    evidence.checksum_verified
                ),
                notes=(
                    evidence.notes
                ),
            )
        )

        self._kernel_registry.record_restore_verification(
            kernel_verification
        )

        self._restore_evidence[
            evidence.verification_id
        ] = evidence

        return {
            "created": True,
            "evidence": evidence,
            "audit_event": (
                self._audit_event(
                    action=(
                        "backups.restore_test.verify"
                    ),
                    resource_id=(
                        evidence.verification_id
                    ),
                    policy=policy,
                    request_context=(
                        request_context
                    ),
                    timestamp=(
                        evidence.tested_at
                    ),
                    metadata={
                        "backup_id": (
                            evidence.backup_id
                        ),
                        "success": (
                            evidence.success
                        ),
                        "checksum_verified": (
                            evidence.checksum_verified
                        ),
                    },
                )
            ),
        }

    def trusted_for_recovery(
        self,
        *,
        policy_id: str,
        request_context: Any,
        now: str | None = None,
    ) -> bool:
        policy = self._get_policy(
            policy_id=policy_id,
            request_context=(
                request_context
            ),
        )

        if not policy.enabled:
            return False

        if not self._kernel_registry.trusted_for_recovery(
            policy.policy_id
        ):
            return False

        latest = (
            self._kernel_registry.latest_verification(
                policy.policy_id
            )
        )

        if latest is None:
            return False

        tested_at = _time(
            latest.tested_at
        )

        valid_until = (
            tested_at
            + timedelta(
                days=(
                    policy.restore_test_interval_days
                )
            )
        )

        return _time(
            now
        ) <= valid_until

    def plan_restore(
        self,
        *,
        backup_id: str,
        target_ref: str,
        request_context: Any,
        requested_at: str | None = None,
    ) -> RestoreExecutionPlan:
        evidence, policy = (
            self._get_backup(
                backup_id=backup_id,
                request_context=(
                    request_context
                ),
            )
        )

        current = _time(
            requested_at
        )

        if not self.trusted_for_recovery(
            policy_id=(
                policy.policy_id
            ),
            request_context=(
                request_context
            ),
            now=(
                current.isoformat()
            ),
        ):
            raise BackupsBaaSError(
                "backup policy is not trusted for recovery"
            )

        if not evidence.success:
            raise BackupsBaaSError(
                "failed backup cannot be restored"
            )

        provider = self._require_provider(
            policy.provider_id
        )

        if not provider.supports_restore:
            raise BackupsBaaSError(
                "provider does not support restore"
            )

        target = _text(
            "target_ref",
            target_ref,
        )

        restore_id = (
            "restore_"
            + sha256(
                (
                    f"{backup_id}"
                    f"\x1f{target}"
                    f"\x1f{current.isoformat()}"
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return RestoreExecutionPlan(
            restore_id=restore_id,
            policy_id=(
                policy.policy_id
            ),
            backup_id=(
                evidence.backup_id
            ),
            backup_reference=(
                evidence.backup_reference
            ),
            target_ref=target,
            provider_id=(
                provider.provider_id
            ),
            provider_adapter_ref=(
                provider.adapter_ref
            ),
            provider_credential_ref=(
                provider.credential_ref
            ),
            rpo_minutes=(
                policy.rpo_minutes
            ),
            rto_minutes=(
                policy.rto_minutes
            ),
            tenant_context={
                "organization_id": (
                    policy.tenant.organization_id
                ),
                "workspace_id": (
                    policy.tenant.workspace_id
                ),
                "project_id": (
                    policy.tenant.project_id
                ),
                "environment_id": (
                    policy.tenant.environment_id
                ),
            },
            correlation_id=(
                request_context.correlation_id
            ),
            kernel_authorization_ref=(
                request_context.kernel_authorization_ref
            ),
            audit_event=(
                self._audit_event(
                    action=(
                        "backups.restore.plan"
                    ),
                    resource_id=(
                        restore_id
                    ),
                    policy=policy,
                    request_context=(
                        request_context
                    ),
                    timestamp=(
                        current.isoformat()
                    ),
                    metadata={
                        "backup_id": (
                            evidence.backup_id
                        ),
                        "backup_reference": (
                            evidence.backup_reference
                        ),
                        "target_ref": (
                            target
                        ),
                        "rpo_minutes": (
                            policy.rpo_minutes
                        ),
                        "rto_minutes": (
                            policy.rto_minutes
                        ),
                    },
                )
            ),
        )

    def _get_policy(
        self,
        *,
        policy_id: str,
        request_context: Any,
    ) -> TenantBackupPolicy:
        self._validate_request_context(
            request_context
        )

        policy = self._policies.get(
            str(
                policy_id
            ).strip()
        )

        if policy is None:
            raise BackupsBaaSError(
                "backup policy not found"
            )

        tenant = self._tenant_from_context(
            request_context
        )

        if not self._same_tenant(
            policy.tenant,
            tenant,
        ):
            raise BackupsBaaSError(
                "cross-tenant backup policy access denied"
            )

        return policy

    def _get_backup(
        self,
        *,
        backup_id: str,
        request_context: Any,
    ) -> tuple[
        BackupEvidence,
        TenantBackupPolicy,
    ]:
        self._validate_request_context(
            request_context
        )

        evidence = self._evidence.get(
            str(
                backup_id
            ).strip()
        )

        if evidence is None:
            raise BackupsBaaSError(
                "backup evidence not found"
            )

        policy = self._get_policy(
            policy_id=(
                evidence.policy_id
            ),
            request_context=(
                request_context
            ),
        )

        return (
            evidence,
            policy,
        )

    def _require_provider(
        self,
        provider_id: str,
    ) -> BackupProvider:
        provider = self._providers.get(
            str(
                provider_id
            ).strip()
        )

        if provider is None:
            raise BackupsBaaSError(
                "backup provider not found"
            )

        if not provider.enabled:
            raise BackupsBaaSError(
                "backup provider is disabled"
            )

        return provider

    @staticmethod
    def _audit_event(
        *,
        action: str,
        resource_id: str,
        policy: TenantBackupPolicy,
        request_context: Any,
        timestamp: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        material = {
            "action": action,
            "resource_id": (
                resource_id
            ),
            "policy_id": (
                policy.policy_id
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "timestamp": (
                timestamp
            ),
        }

        audit_id = (
            "audit_backup_"
            + sha256(
                json.dumps(
                    material,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()[:24]
        )

        return {
            "audit_id": audit_id,
            "organization_id": (
                policy.tenant.organization_id
            ),
            "actor_type": (
                request_context.actor_type
            ),
            "actor_id": (
                request_context.actor_id
            ),
            "action": action,
            "resource_type": (
                "backup"
            ),
            "resource_id": (
                resource_id
            ),
            "timestamp": (
                timestamp
            ),
            "correlation_id": (
                request_context.correlation_id
            ),
            "metadata": {
                "policy_id": (
                    policy.policy_id
                ),
                **metadata,
            },
        }
