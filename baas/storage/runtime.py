from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
import re
import secrets
from typing import Any


BUCKET_STATES = {"ACTIVE", "SUSPENDED", "DECOMMISSIONED"}
OBJECT_STATES = {"PENDING_UPLOAD", "QUARANTINED", "AVAILABLE", "DELETED"}
SCAN_STATES = {"NOT_REQUIRED", "PENDING", "CLEAN", "INFECTED"}
SENSITIVE_KEYS = {
    "authorization", "access_token", "refresh_token", "api_key", "password",
    "secret", "secret_value", "client_secret", "private_key", "session_token",
    "webhook_secret", "provider_credentials",
}


class StorageBaaSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    result = str(value).strip()
    if not result:
        raise StorageBaaSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise StorageBaaSError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise StorageBaaSError("timestamp must be timezone-aware")
    return parsed


def _contains_sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive(item) for item in value)
    return False


def _validate_metadata(metadata: dict[str, Any]) -> None:
    try:
        json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise StorageBaaSError("metadata must be JSON-compatible") from exc
    if _contains_sensitive(metadata):
        raise StorageBaaSError("metadata contains secret-bearing fields")


def _validate_key(value: str) -> str:
    key = _text("object_key", value)
    if key.startswith("/") or ".." in key.split("/"):
        raise StorageBaaSError("object_key must be a relative safe path")
    if any(ord(ch) < 32 for ch in key):
        raise StorageBaaSError("object_key contains control characters")
    if len(key) > 1024:
        raise StorageBaaSError("object_key exceeds 1024 characters")
    return key


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
        }.items():
            _text(name, value)


@dataclass(frozen=True)
class BucketDescriptor:
    bucket_id: str
    tenant: TenantScope
    name: str
    provider_bucket_ref: str
    private: bool
    retention_days: int
    max_object_bytes: int
    signed_access_max_seconds: int
    malware_scan_required: bool
    state: str
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _text("bucket_id", self.bucket_id)
        self.tenant.validate()
        _text("name", self.name)
        _text("provider_bucket_ref", self.provider_bucket_ref)
        if not self.private:
            raise StorageBaaSError("Object Storage P0 buckets must be private")
        if not isinstance(self.retention_days, int) or self.retention_days < 0:
            raise StorageBaaSError("retention_days must be an integer >= 0")
        if not isinstance(self.max_object_bytes, int) or self.max_object_bytes < 1:
            raise StorageBaaSError("max_object_bytes must be an integer >= 1")
        if (
            not isinstance(self.signed_access_max_seconds, int)
            or self.signed_access_max_seconds < 1
            or self.signed_access_max_seconds > 86400
        ):
            raise StorageBaaSError(
                "signed_access_max_seconds must be an integer from 1 to 86400"
            )
        if self.state not in BUCKET_STATES:
            raise StorageBaaSError(f"invalid bucket state: {self.state}")
        _time(self.created_at)
        _time(self.updated_at)


@dataclass(frozen=True)
class UploadIntent:
    upload_id: str
    bucket_id: str
    object_id: str
    object_key: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    metadata: dict[str, Any]
    requested_at: str

    def validate(self) -> None:
        for name, value in {
            "upload_id": self.upload_id,
            "bucket_id": self.bucket_id,
            "object_id": self.object_id,
            "content_type": self.content_type,
        }.items():
            _text(name, value)
        _validate_key(self.object_key)
        if not isinstance(self.size_bytes, int) or self.size_bytes < 0:
            raise StorageBaaSError("size_bytes must be an integer >= 0")
        if not re.fullmatch(r"[a-f0-9]{64}", self.checksum_sha256):
            raise StorageBaaSError("checksum_sha256 must be SHA-256 hex")
        _validate_metadata(self.metadata)
        _time(self.requested_at)


@dataclass(frozen=True)
class ObjectDescriptor:
    object_id: str
    bucket_id: str
    object_key: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    provider_object_ref: str
    state: str
    malware_scan_status: str
    retain_until: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str

    def validate(self) -> None:
        for name, value in {
            "object_id": self.object_id,
            "bucket_id": self.bucket_id,
            "content_type": self.content_type,
            "provider_object_ref": self.provider_object_ref,
        }.items():
            _text(name, value)
        _validate_key(self.object_key)
        if not isinstance(self.size_bytes, int) or self.size_bytes < 0:
            raise StorageBaaSError("size_bytes must be an integer >= 0")
        if not re.fullmatch(r"[a-f0-9]{64}", self.checksum_sha256):
            raise StorageBaaSError("checksum_sha256 must be SHA-256 hex")
        if self.state not in OBJECT_STATES:
            raise StorageBaaSError(f"invalid object state: {self.state}")
        if self.malware_scan_status not in SCAN_STATES:
            raise StorageBaaSError(
                f"invalid malware_scan_status: {self.malware_scan_status}"
            )
        if self.retain_until is not None:
            _time(self.retain_until)
        _validate_metadata(self.metadata)
        _time(self.created_at)
        _time(self.updated_at)


@dataclass(frozen=True)
class SignedAccessGrant:
    grant_id: str
    object_id: str
    operation: str
    token_fingerprint: str
    expires_at: str
    correlation_id: str

    def validate(self) -> None:
        for name, value in {
            "grant_id": self.grant_id,
            "object_id": self.object_id,
            "operation": self.operation,
            "token_fingerprint": self.token_fingerprint,
            "correlation_id": self.correlation_id,
        }.items():
            _text(name, value)
        if self.operation != "DOWNLOAD":
            raise StorageBaaSError("P0 signed access supports DOWNLOAD only")
        if not re.fullmatch(r"[a-f0-9]{64}", self.token_fingerprint):
            raise StorageBaaSError("token_fingerprint must be SHA-256 hex")
        _time(self.expires_at)


class ObjectStorageManager:
    def __init__(self) -> None:
        self._buckets: dict[str, BucketDescriptor] = {}
        self._uploads: dict[str, UploadIntent] = {}
        self._objects: dict[str, ObjectDescriptor] = {}
        self._grants: dict[str, SignedAccessGrant] = {}

    @staticmethod
    def _validate_request_context(request_context: Any) -> None:
        if hasattr(request_context, "validate"):
            request_context.validate()
        for name in [
            "organization_id", "workspace_id", "project_id", "environment_id",
            "kernel_authorization_ref", "correlation_id",
        ]:
            _text(name, getattr(request_context, name, None))
        if not str(request_context.kernel_authorization_ref).startswith(
            "kernel_auth_"
        ):
            raise StorageBaaSError(
                "storage management requires Kernel authorization evidence"
            )

    @staticmethod
    def _same_tenant(bucket: BucketDescriptor, request_context: Any) -> bool:
        tenant = bucket.tenant
        return (
            tenant.organization_id == request_context.organization_id
            and tenant.workspace_id == request_context.workspace_id
            and tenant.project_id == request_context.project_id
            and tenant.environment_id == request_context.environment_id
        )

    def register_bucket(
        self, *, bucket: BucketDescriptor, request_context: Any
    ) -> None:
        self._validate_request_context(request_context)
        bucket.validate()
        if not self._same_tenant(bucket, request_context):
            raise StorageBaaSError("bucket tenant scope mismatch")
        if bucket.bucket_id in self._buckets:
            raise StorageBaaSError("bucket already registered")
        self._buckets[bucket.bucket_id] = bucket

    def get_bucket(
        self, *, bucket_id: str, request_context: Any
    ) -> BucketDescriptor:
        self._validate_request_context(request_context)
        bucket = self._buckets.get(str(bucket_id).strip())
        if bucket is None:
            raise StorageBaaSError("bucket not found")
        if not self._same_tenant(bucket, request_context):
            raise StorageBaaSError("cross-tenant bucket access denied")
        if bucket.state == "DECOMMISSIONED":
            raise StorageBaaSError("bucket is decommissioned")
        return bucket

    def create_upload_intent(
        self, *, intent: UploadIntent, request_context: Any
    ) -> None:
        bucket = self.get_bucket(
            bucket_id=intent.bucket_id, request_context=request_context
        )
        if bucket.state != "ACTIVE":
            raise StorageBaaSError("bucket must be ACTIVE for uploads")
        intent.validate()
        if intent.size_bytes > bucket.max_object_bytes:
            raise StorageBaaSError("object exceeds bucket size policy")
        if intent.upload_id in self._uploads:
            raise StorageBaaSError("upload intent already exists")
        if intent.object_id in self._objects:
            raise StorageBaaSError("object_id already exists")
        self._uploads[intent.upload_id] = intent

    def complete_upload(
        self,
        *,
        upload_id: str,
        provider_object_ref: str,
        request_context: Any,
        now: str | None = None,
    ) -> ObjectDescriptor:
        intent = self._uploads.get(upload_id)
        if intent is None:
            raise StorageBaaSError("upload intent not found")
        bucket = self.get_bucket(
            bucket_id=intent.bucket_id, request_context=request_context
        )
        current = _time(now)
        retain_until = None
        if bucket.retention_days > 0:
            retain_until = (
                current + timedelta(days=bucket.retention_days)
            ).isoformat()
        scan_status = "PENDING" if bucket.malware_scan_required else "NOT_REQUIRED"
        state = "QUARANTINED" if bucket.malware_scan_required else "AVAILABLE"
        obj = ObjectDescriptor(
            object_id=intent.object_id,
            bucket_id=intent.bucket_id,
            object_key=intent.object_key,
            content_type=intent.content_type,
            size_bytes=intent.size_bytes,
            checksum_sha256=intent.checksum_sha256,
            provider_object_ref=_text("provider_object_ref", provider_object_ref),
            state=state,
            malware_scan_status=scan_status,
            retain_until=retain_until,
            metadata=dict(intent.metadata),
            created_at=current.isoformat(),
            updated_at=current.isoformat(),
        )
        obj.validate()
        self._objects[obj.object_id] = obj
        return obj

    def mark_malware_scan(
        self,
        *,
        object_id: str,
        clean: bool,
        request_context: Any,
        now: str | None = None,
    ) -> ObjectDescriptor:
        obj = self.get_object(object_id=object_id, request_context=request_context)
        bucket = self.get_bucket(
            bucket_id=obj.bucket_id, request_context=request_context
        )
        if not bucket.malware_scan_required:
            raise StorageBaaSError("bucket does not require malware scanning")
        if obj.state != "QUARANTINED" or obj.malware_scan_status != "PENDING":
            raise StorageBaaSError("object is not pending malware scan")
        updated = replace(
            obj,
            state="AVAILABLE" if clean else "QUARANTINED",
            malware_scan_status="CLEAN" if clean else "INFECTED",
            updated_at=_time(now).isoformat(),
        )
        updated.validate()
        self._objects[object_id] = updated
        return updated

    def get_object(
        self, *, object_id: str, request_context: Any
    ) -> ObjectDescriptor:
        self._validate_request_context(request_context)
        obj = self._objects.get(str(object_id).strip())
        if obj is None:
            raise StorageBaaSError("object not found")
        self.get_bucket(bucket_id=obj.bucket_id, request_context=request_context)
        if obj.state == "DELETED":
            raise StorageBaaSError("object is deleted")
        return obj

    def issue_signed_download(
        self,
        *,
        object_id: str,
        ttl_seconds: int,
        request_context: Any,
        now: str | None = None,
    ) -> tuple[SignedAccessGrant, str]:
        obj = self.get_object(object_id=object_id, request_context=request_context)
        bucket = self.get_bucket(
            bucket_id=obj.bucket_id, request_context=request_context
        )
        if obj.state != "AVAILABLE":
            raise StorageBaaSError("only AVAILABLE objects may be downloaded")
        if (
            not isinstance(ttl_seconds, int)
            or ttl_seconds < 1
            or ttl_seconds > bucket.signed_access_max_seconds
        ):
            raise StorageBaaSError("signed access TTL exceeds bucket policy")

        raw_token = "dzs_" + secrets.token_urlsafe(32)
        grant = SignedAccessGrant(
            grant_id="grant_" + secrets.token_hex(12),
            object_id=obj.object_id,
            operation="DOWNLOAD",
            token_fingerprint=sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=(_time(now) + timedelta(seconds=ttl_seconds)).isoformat(),
            correlation_id=request_context.correlation_id,
        )
        grant.validate()
        self._grants[grant.grant_id] = grant
        return grant, raw_token

    def verify_signed_download(
        self,
        *,
        grant_id: str,
        raw_token: str,
        now: str | None = None,
    ) -> SignedAccessGrant:
        grant = self._grants.get(grant_id)
        if grant is None:
            raise StorageBaaSError("signed access grant not found")
        grant.validate()
        if _time(now) >= _time(grant.expires_at):
            raise StorageBaaSError("signed access grant expired")
        supplied = sha256(str(raw_token).encode("utf-8")).hexdigest()
        if not hmac.compare_digest(supplied, grant.token_fingerprint):
            raise StorageBaaSError("signed access credential mismatch")
        return grant

    def delete_object(
        self,
        *,
        object_id: str,
        request_context: Any,
        now: str | None = None,
    ) -> ObjectDescriptor:
        obj = self.get_object(object_id=object_id, request_context=request_context)
        current = _time(now)
        if obj.retain_until is not None and current < _time(obj.retain_until):
            raise StorageBaaSError("object retention period is still active")
        updated = replace(
            obj,
            state="DELETED",
            updated_at=current.isoformat(),
        )
        self._objects[object_id] = updated
        return updated
