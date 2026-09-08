#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

MODULES = {
    "baas_request_context": BAAS / "runtime/request_context.py",
    "baas_storage": BAAS / "storage/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing Object Storage runtime file: {path}")
    py_compile.compile(str(path), doraise=True)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

request_context = load_module("baas_request_context", MODULES["baas_request_context"])
storage = load_module("baas_storage", MODULES["baas_storage"])

ctx = request_context.BaaSRequestContext(
    request_id="req-storage-validation",
    correlation_id="corr-storage-validation",
    service="storage",
    operation="object.upload",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_storage_validation",
    idempotency_key="idem-storage-validation",
)
ctx.validate()

tenant = storage.TenantScope(
    organization_id=ctx.organization_id,
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
)

bucket = storage.BucketDescriptor(
    bucket_id="bucket-validation",
    tenant=tenant,
    name="Validation Bucket",
    provider_bucket_ref="object-store://validation/bucket",
    private=True,
    retention_days=1,
    max_object_bytes=1024 * 1024,
    signed_access_max_seconds=900,
    malware_scan_required=True,
    state="ACTIVE",
    created_at="2026-01-01T00:00:00+00:00",
    updated_at="2026-01-01T00:00:00+00:00",
)

manager = storage.ObjectStorageManager()
manager.register_bucket(bucket=bucket, request_context=ctx)

try:
    manager.register_bucket(
        bucket=storage.BucketDescriptor(
            bucket_id="bucket-public",
            tenant=tenant,
            name="Public Bucket",
            provider_bucket_ref="object-store://validation/public",
            private=False,
            retention_days=0,
            max_object_bytes=100,
            signed_access_max_seconds=60,
            malware_scan_required=False,
            state="ACTIVE",
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        ),
        request_context=ctx,
    )
except storage.StorageBaaSError:
    pass
else:
    raise SystemExit("ERROR: public P0 bucket was accepted")

intent = storage.UploadIntent(
    upload_id="upload-validation",
    bucket_id=bucket.bucket_id,
    object_id="object-validation",
    object_key="documents/validation.txt",
    content_type="text/plain",
    size_bytes=10,
    checksum_sha256="a" * 64,
    metadata={"classification": "validation"},
    requested_at="2026-01-01T00:00:01+00:00",
)

manager.create_upload_intent(intent=intent, request_context=ctx)

obj = manager.complete_upload(
    upload_id=intent.upload_id,
    provider_object_ref="object://validation/object",
    request_context=ctx,
    now="2026-01-01T00:00:02+00:00",
)

if obj.state != "QUARANTINED" or obj.malware_scan_status != "PENDING":
    raise SystemExit("ERROR: scan-required upload was not quarantined")

try:
    manager.issue_signed_download(
        object_id=obj.object_id,
        ttl_seconds=60,
        request_context=ctx,
        now="2026-01-01T00:00:03+00:00",
    )
except storage.StorageBaaSError:
    pass
else:
    raise SystemExit("ERROR: quarantined object received download access")

clean = manager.mark_malware_scan(
    object_id=obj.object_id,
    clean=True,
    request_context=ctx,
    now="2026-01-01T00:00:04+00:00",
)

if clean.state != "AVAILABLE" or clean.malware_scan_status != "CLEAN":
    raise SystemExit("ERROR: clean scan did not release object")

grant, raw_token = manager.issue_signed_download(
    object_id=obj.object_id,
    ttl_seconds=300,
    request_context=ctx,
    now="2026-01-01T00:00:05+00:00",
)

if raw_token == grant.token_fingerprint:
    raise SystemExit("ERROR: raw signed-access token was stored")

manager.verify_signed_download(
    grant_id=grant.grant_id,
    raw_token=raw_token,
    now="2026-01-01T00:00:06+00:00",
)

try:
    manager.issue_signed_download(
        object_id=obj.object_id,
        ttl_seconds=901,
        request_context=ctx,
        now="2026-01-01T00:00:07+00:00",
    )
except storage.StorageBaaSError:
    pass
else:
    raise SystemExit("ERROR: signed-access TTL exceeded bucket policy")

try:
    manager.delete_object(
        object_id=obj.object_id,
        request_context=ctx,
        now="2026-01-01T00:00:08+00:00",
    )
except storage.StorageBaaSError:
    pass
else:
    raise SystemExit("ERROR: active retention was bypassed")

cross = request_context.BaaSRequestContext(
    request_id="req-storage-cross",
    correlation_id="corr-storage-cross",
    service="storage",
    operation="bucket.read",
    organization_id="org-other",
    workspace_id=ctx.workspace_id,
    project_id=ctx.project_id,
    environment_id=ctx.environment_id,
    actor_id=ctx.actor_id,
    actor_type=ctx.actor_type,
    kernel_authorization_ref="kernel_auth_storage_cross",
    idempotency_key="idem-storage-cross",
)

try:
    manager.get_bucket(bucket_id=bucket.bucket_id, request_context=cross)
except storage.StorageBaaSError:
    pass
else:
    raise SystemExit("ERROR: cross-tenant bucket access was accepted")

try:
    storage.UploadIntent(
        upload_id="upload-secret",
        bucket_id=bucket.bucket_id,
        object_id="object-secret",
        object_key="secret.txt",
        content_type="text/plain",
        size_bytes=1,
        checksum_sha256="b" * 64,
        metadata={"api_key": "must-not-store"},
        requested_at="2026-01-01T00:00:01+00:00",
    ).validate()
except storage.StorageBaaSError:
    pass
else:
    raise SystemExit("ERROR: secret-bearing object metadata was accepted")

status = (BAAS / "IMPLEMENTATION_STATUS.md").read_text(encoding="utf-8")
for phrase in [
    "- [x] Object Storage",
    "- [x] Signed temporary download access",
    "- [x] Retention enforcement",
    "- [x] Malware-scan state",
    "- [ ] Serverless Functions",
]:
    if phrase not in status:
        raise SystemExit("ERROR: BaaS storage status missing: " + phrase)

print("OK: Private bucket policy passed.")
print("OK: Tenant bucket isolation passed.")
print("OK: Scan-required uploads are quarantined.")
print("OK: Quarantined objects cannot receive signed downloads.")
print("OK: Signed access stores fingerprints only and enforces TTL.")
print("OK: Retention prevents premature deletion.")
print("OK: Secret-bearing metadata is rejected.")
print("STATUS: BAAS P0 OBJECT STORAGE READY")
