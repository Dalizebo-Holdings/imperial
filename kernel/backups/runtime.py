from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from typing import Any


ENVIRONMENTS = {
    "DEVELOPMENT",
    "PREVIEW",
    "PRODUCTION",
}

SENSITIVE_KEYS = {
    "authorization",
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
}


class BackupContractError(ValueError):
    pass


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


@dataclass(frozen=True)
class BackupPolicy:
    policy_id: str
    resource_class: str
    environment_type: str
    encrypted: bool
    retention_days: int
    frequency_minutes: int
    rpo_minutes: int
    rto_minutes: int
    immutable_copy: bool
    offsite_copy: bool
    restore_test_interval_days: int
    enabled: bool = True
    metadata: dict[str, Any] | None = None

    def validate(self) -> None:
        required_text = {
            "policy_id": self.policy_id,
            "resource_class": self.resource_class,
        }

        missing = [
            name
            for name, value in required_text.items()
            if not str(value).strip()
        ]

        if missing:
            raise BackupContractError(
                "missing backup policy fields: "
                + ", ".join(missing)
            )

        env = str(self.environment_type).strip().upper()

        if env not in ENVIRONMENTS:
            raise BackupContractError(
                f"unsupported environment_type: {env}"
            )

        numeric = {
            "retention_days": self.retention_days,
            "frequency_minutes": self.frequency_minutes,
            "rpo_minutes": self.rpo_minutes,
            "rto_minutes": self.rto_minutes,
            "restore_test_interval_days": (
                self.restore_test_interval_days
            ),
        }

        for name, value in numeric.items():
            if not isinstance(value, int) or value < 1:
                raise BackupContractError(
                    f"{name} must be an integer >= 1"
                )

        if self.rpo_minutes > self.frequency_minutes:
            raise BackupContractError(
                "rpo_minutes may not exceed frequency_minutes"
            )

        if env == "PRODUCTION":
            if not self.encrypted:
                raise BackupContractError(
                    "production backups must be encrypted"
                )
            if not self.immutable_copy:
                raise BackupContractError(
                    "production backups require immutable_copy"
                )
            if not self.offsite_copy:
                raise BackupContractError(
                    "production backups require offsite_copy"
                )

        metadata = self.metadata or {}

        try:
            json.dumps(
                metadata,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise BackupContractError(
                "backup metadata must be JSON-compatible"
            ) from exc

        if _contains_sensitive_key(metadata):
            raise BackupContractError(
                "backup metadata contains secret material"
            )


@dataclass(frozen=True)
class RestoreVerification:
    verification_id: str
    policy_id: str
    backup_reference: str
    tested_at: str
    success: bool
    restored_resource_reference: str
    checksum_verified: bool
    notes: str = ""

    def validate(self) -> None:
        required = {
            "verification_id": self.verification_id,
            "policy_id": self.policy_id,
            "backup_reference": self.backup_reference,
            "tested_at": self.tested_at,
            "restored_resource_reference": (
                self.restored_resource_reference
            ),
        }

        missing = [
            name
            for name, value in required.items()
            if not str(value).strip()
        ]

        if missing:
            raise BackupContractError(
                "missing restore verification fields: "
                + ", ".join(missing)
            )

        try:
            datetime.fromisoformat(self.tested_at)
        except ValueError as exc:
            raise BackupContractError(
                "tested_at must be ISO-8601"
            ) from exc

        if self.success and not self.checksum_verified:
            raise BackupContractError(
                "successful restore verification requires checksum_verified"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class BackupPolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, BackupPolicy] = {}
        self._verifications: list[RestoreVerification] = []

    def register(self, policy: BackupPolicy) -> None:
        policy.validate()

        if policy.policy_id in self._policies:
            raise BackupContractError(
                f"backup policy already registered: {policy.policy_id}"
            )

        self._policies[policy.policy_id] = policy

    def record_restore_verification(
        self,
        verification: RestoreVerification,
    ) -> None:
        verification.validate()

        if verification.policy_id not in self._policies:
            raise BackupContractError(
                f"unknown backup policy: {verification.policy_id}"
            )

        self._verifications.append(verification)

    def latest_verification(
        self,
        policy_id: str,
    ) -> RestoreVerification | None:
        matches = [
            item
            for item in self._verifications
            if item.policy_id == policy_id
        ]

        if not matches:
            return None

        return sorted(
            matches,
            key=lambda item: item.tested_at,
        )[-1]

    def trusted_for_recovery(
        self,
        policy_id: str,
    ) -> bool:
        policy = self._policies.get(policy_id)

        if policy is None or not policy.enabled:
            return False

        verification = self.latest_verification(policy_id)

        return bool(
            verification
            and verification.success
            and verification.checksum_verified
        )
