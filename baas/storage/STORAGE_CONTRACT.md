# Object Storage BaaS Runtime Contract

## Purpose

Object Storage BaaS provides a tenant-scoped control plane for buckets, object
metadata, uploads, downloads, temporary signed access, access policy, retention,
and malware-scan state.

P0 does not store object bytes and does not embed provider credentials.

## Bucket Model

Each bucket contains:

- bucket_id
- organization_id
- workspace_id
- project_id
- environment_id
- name
- provider_bucket_ref
- private
- retention_days
- max_object_bytes
- signed_access_max_seconds
- malware_scan_required
- state
- created_at
- updated_at

P0 buckets are private by default and public buckets are rejected.

## Object Model

Object metadata contains:

- object_id
- bucket_id
- object_key
- content_type
- size_bytes
- checksum_sha256
- provider_object_ref
- state
- malware_scan_status
- retain_until
- metadata
- created_at
- updated_at

Object bytes never enter the BaaS runtime object.

## Upload Lifecycle

`PENDING_UPLOAD → AVAILABLE`

When malware scanning is required:

`PENDING_UPLOAD → QUARANTINED → AVAILABLE`

If malware is detected:

`QUARANTINED → QUARANTINED(INFECTED)`

Only AVAILABLE objects may receive temporary download grants.

## Signed Temporary Access

P0 issues one-time access material and stores only its SHA-256 fingerprint.

A future provider adapter may translate an approved grant into a provider-native
signed URL.

Rules:

- tenant scope must match
- object must be AVAILABLE
- access is temporary
- TTL may not exceed bucket policy
- disabled/deleted/quarantined objects fail closed

## Retention

Objects with an active `retain_until` cannot be deleted before expiry.

## Security

- private by default
- tenant-aware authorization
- Kernel authorization evidence required
- no raw storage credentials
- no object payload logging
- secret-bearing metadata rejected
- malware scanning state is explicit
