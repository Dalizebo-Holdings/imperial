from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
import json
from typing import Any

from .runtime import (
    EvidenceEnvelope,
    EvidenceLedger,
    payload_sha256,
)
from .store import (
    DurableEvidenceStore,
    EvidenceStoreError,
    envelope_from_mapping,
)


DEFAULT_VALIDATION_HOME = (
    Path.home()
    / ".local"
    / "share"
    / "dalizebo"
    / "imperial"
    / "validation"
)

DEFAULT_INBOX = (
    DEFAULT_VALIDATION_HOME
    / "inbox"
)

DEFAULT_TEMPLATE_LIBRARY = (
    DEFAULT_VALIDATION_HOME
    / "templates"
)

REQUIRED_PROOF_LABELS = (
    "discovery",
    "pilot_exit",
    "release_gate_1",
    "release_gate_2",
    "release_gate_3",
    "operational_readiness",
    "public_mvp_90d",
)

PLACEHOLDERS = {
    "__REPLACE__",
    "REPLACE_ME",
    "<REPLACE>",
}


class EvidenceCollectionError(ValueError):
    pass


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip() in PLACEHOLDERS
    if isinstance(value, dict):
        return any(
            _contains_placeholder(key)
            or _contains_placeholder(nested)
            for key, nested in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(
            _contains_placeholder(item)
            for item in value
        )
    return False


def _require_mapping(
    name: str,
    value: Any,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceCollectionError(
            f"{name} must be a JSON object"
        )
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise EvidenceCollectionError(
            f"file not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise EvidenceCollectionError(
            f"invalid JSON in {path}: {exc}"
        ) from exc

    return _require_mapping(
        str(path),
        value,
    )


def envelope_from_input(
    value: dict[str, Any],
) -> EvidenceEnvelope:
    required = {
        "envelope_id",
        "evidence_type",
        "origin",
        "observed_at",
        "evidence_ref",
        "source_system_ref",
        "payload",
    }

    allowed = (
        required
        | {
            "content_sha256",
        }
    )

    missing = required - set(value)
    if missing:
        raise EvidenceCollectionError(
            "input missing fields: "
            + ", ".join(
                sorted(missing)
            )
        )

    extra = set(value) - allowed
    if extra:
        raise EvidenceCollectionError(
            "input contains unsupported fields: "
            + ", ".join(
                sorted(extra)
            )
        )

    if _contains_placeholder(value):
        raise EvidenceCollectionError(
            "input still contains __REPLACE__/REPLACE_ME placeholder values"
        )

    payload = _require_mapping(
        "payload",
        value["payload"],
    )

    calculated = payload_sha256(
        payload
    )

    supplied = value.get(
        "content_sha256"
    )

    if (
        supplied is not None
        and str(
            supplied
        ).strip().lower()
        != calculated
    ):
        raise EvidenceCollectionError(
            "supplied content_sha256 does not match canonical payload"
        )

    envelope = EvidenceEnvelope(
        envelope_id=value["envelope_id"],
        evidence_type=value["evidence_type"],
        origin=value["origin"],
        observed_at=value["observed_at"],
        evidence_ref=value["evidence_ref"],
        source_system_ref=value["source_system_ref"],
        payload=dict(payload),
        content_sha256=calculated,
    )
    envelope.validate()

    return envelope


def _template(
    *,
    evidence_type: str,
    origin: str,
    source_system_ref: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "envelope_id": "__REPLACE__",
        "evidence_type": evidence_type,
        "origin": origin,
        "observed_at": "__REPLACE__",
        "evidence_ref": "__REPLACE__",
        "source_system_ref": source_system_ref,
        "payload": payload,
    }


def templates() -> dict[str, dict[str, Any]]:
    return {
        "discovery-interview": _template(
            evidence_type="DISCOVERY_INTERVIEW",
            origin="REAL_MERCHANT",
            source_system_ref="source://validation/discovery",
            payload={
                "interview_id": "__REPLACE__",
                "merchant_ref": "__REPLACE__",
                "merchant_segment": "__REPLACE__",
                "conducted_at": "__REPLACE__",
                "products": [
                    "COMMERCE",
                    "POS",
                ],
                "core_problem_material": False,
                "willingness_to_test": False,
                "structured_feedback_available": False,
                "evidence_ref": "__REPLACE__",
                "metadata": {},
            },
        ),
        "design-partner-commitment": _template(
            evidence_type="DESIGN_PARTNER_COMMITMENT",
            origin="REAL_MERCHANT",
            source_system_ref="source://validation/design-partners",
            payload={
                "commitment_id": "__REPLACE__",
                "merchant_ref": "__REPLACE__",
                "products": [
                    "COMMERCE",
                    "POS",
                ],
                "committed_at": "__REPLACE__",
                "active_retail_operations": False,
                "real_inventory": False,
                "real_customers": False,
                "transaction_volume_confirmed": False,
                "willingness_to_test": False,
                "structured_feedback_available": False,
                "pilot_status": "CANDIDATE",
                "evidence_ref": "__REPLACE__",
                "metadata": {},
            },
        ),
        "pilot-onboarding": _template(
            evidence_type="PILOT_ONBOARDING",
            origin="REAL_MERCHANT",
            source_system_ref="source://validation/pilot-onboarding",
            payload={
                "onboarding_id": "__REPLACE__",
                "commitment_id": "__REPLACE__",
                "merchant_ref": "__REPLACE__",
                "products": [
                    "COMMERCE",
                    "POS",
                ],
                "started_at": "__REPLACE__",
                "evidence_ref": "__REPLACE__",
                "metadata": {},
            },
        ),
        "pilot-onboarding-event": _template(
            evidence_type="PILOT_ONBOARDING_EVENT",
            origin="REAL_MERCHANT",
            source_system_ref="source://validation/pilot-onboarding-events",
            payload={
                "event_id": "__REPLACE__",
                "onboarding_id": "__REPLACE__",
                "merchant_ref": "__REPLACE__",
                "step": "__REPLACE__",
                "status": "__REPLACE__",
                "occurred_at": "__REPLACE__",
                "evidence_ref": "__REPLACE__",
                "failure_code": None,
                "training_required": False,
                "support_intervention": False,
                "metadata": {},
            },
        ),
        "pilot-metric-snapshot": _template(
            evidence_type="PILOT_METRIC_SNAPSHOT",
            origin="REAL_RELIABILITY",
            source_system_ref="source://validation/pilot-metrics",
            payload={
                "snapshot_id": "__REPLACE__",
                "period_start": "__REPLACE__",
                "period_end": "__REPLACE__",
                "evidence_ref": "__REPLACE__",
                "weekly_active_merchants": 0,
                "orders_total": 0,
                "orders_correct_final_state": 0,
                "pos_transactions": 0,
                "commerce_transactions": 0,
                "active_branches": 0,
                "active_pos_locations": 0,
                "checkout_attempts": 0,
                "successful_checkouts": 0,
                "payment_reconciliation_total": 0,
                "payment_reconciliation_matches": 0,
                "inventory_checks": 0,
                "inventory_accurate_checks": 0,
                "api_requests": 0,
                "api_errors": 0,
                "paying_merchants": 0,
                "trial_merchants": 0,
                "trial_to_paid_merchants": 0,
                "mrr_minor": 0,
                "logo_start_count": 0,
                "logo_churned_count": 0,
                "merchants_willing_to_continue": 0,
                "merchants_willing_to_pay": 0,
                "support_tickets": 0,
                "engineering_interventions": 0,
                "critical_cross_tenant_defects": 0,
                "metadata": {},
            },
        ),
        "capacity-snapshot": _template(
            evidence_type="CAPACITY_SNAPSHOT",
            origin="REAL_OPERATIONAL",
            source_system_ref="source://validation/capacity",
            payload={
                "snapshot_id": "__REPLACE__",
                "observed_at": "__REPLACE__",
                "organizations": 0,
                "pos_branches": 0,
                "monthly_orders": 0,
                "evidence_ref": "__REPLACE__",
            },
        ),
        "technical-attestation": _template(
            evidence_type="TECHNICAL_ATTESTATION",
            origin="REAL_OPERATIONAL",
            source_system_ref="source://validation/release-gates",
            payload={
                "attestation_id": "__REPLACE__",
                "requirement": "__REPLACE__",
                "satisfied": False,
                "observed_at": "__REPLACE__",
                "evidence_ref": "__REPLACE__",
                "valid_until": None,
                "metadata": {},
            },
        ),
        "merchant-feedback": _template(
            evidence_type="MERCHANT_FEEDBACK",
            origin="REAL_MERCHANT",
            source_system_ref="source://validation/feedback",
            payload={
                "feedback_id": "__REPLACE__",
                "merchant_ref": "__REPLACE__",
                "category": "__REPLACE__",
                "problem": "__REPLACE__",
                "frequency": 1,
                "severity": "P2",
                "business_impact": "__REPLACE__",
                "requested_outcome": "__REPLACE__",
                "existing_workaround": "__REPLACE__",
                "product_decision": "PENDING",
                "recorded_at": "__REPLACE__",
                "evidence_ref": "__REPLACE__",
                "metadata": {},
            },
        ),
        "support-evidence": _template(
            evidence_type="SUPPORT_EVIDENCE",
            origin="REAL_OPERATIONAL",
            source_system_ref="source://validation/support",
            payload={
                "ticket_id": "__REPLACE__",
                "merchant_ref": "__REPLACE__",
                "organization_id": "__REPLACE__",
                "severity": "P2",
                "product": "POS",
                "environment_id": "__REPLACE__",
                "description": "__REPLACE__",
                "correlation_id": "__REPLACE__",
                "owner_ref": "__REPLACE__",
                "opened_at": "__REPLACE__",
                "first_response_at": None,
                "resolved_at": None,
                "resolution": None,
                "evidence_ref": "__REPLACE__",
                "metadata": {},
            },
        ),
        "incident-evidence": _template(
            evidence_type="INCIDENT_EVIDENCE",
            origin="REAL_OPERATIONAL",
            source_system_ref="source://validation/incidents",
            payload={
                "incident_id": "__REPLACE__",
                "severity": "P2",
                "start_time": "__REPLACE__",
                "detection_source": "__REPLACE__",
                "owner_ref": "__REPLACE__",
                "affected_tenants": [
                    "__REPLACE__"
                ],
                "affected_services": [
                    "__REPLACE__"
                ],
                "customer_impact": "__REPLACE__",
                "tenant_isolation_impact": False,
                "material_tenant_isolation_defect": False,
                "state": "OPEN",
                "root_cause": None,
                "resolution": None,
                "recovery_validation": None,
                "corrective_actions": [],
                "resolved_at": None,
                "evidence_ref": "__REPLACE__",
                "metadata": {},
            },
        ),
        "public-mvp-90d": _template(
            evidence_type="PUBLIC_MVP_90D_SNAPSHOT",
            origin="REAL_COMMERCIAL",
            source_system_ref="source://validation/public-mvp",
            payload={
                "snapshot_id": "__REPLACE__",
                "period_start": "__REPLACE__",
                "period_end": "__REPLACE__",
                "activated_organizations": 0,
                "monthly_transacting_organizations": 0,
                "active_three_consecutive_months": 0,
                "logo_start_count": 0,
                "logo_churned_count": 0,
                "first_transaction_eligible_organizations": 0,
                "first_transaction_within_24h": 0,
                "weekly_usage_eligible_organizations": 0,
                "weekly_active_organizations": 0,
                "payment_reconciliation_total": 0,
                "payment_reconciliation_matches": 0,
                "uptime_total_minutes": 0,
                "uptime_available_minutes": 0,
                "p95_core_api_latency_ms": 0,
                "checkout_api_p95_ms": 0,
                "paying_customers": 0,
                "customer_references": 0,
                "critical_tenant_isolation_defects": 0,
                "backup_restore_test_passed": False,
                "evidence_refs": [
                    "__REPLACE__"
                ],
            },
        ),
        "gate-proof": _template(
            evidence_type="GATE_PROOF",
            origin="__REPLACE__",
            source_system_ref="source://validation/gate-evaluator",
            payload={
                "label": "__REPLACE__",
                "state": "__REPLACE__",
                "evidence_digest": "__REPLACE__",
            },
        ),
    }


def _resolve_inbox(
    path: str | Path | None = None,
) -> Path:
    return (
        Path(path).expanduser().resolve()
        if path is not None
        else DEFAULT_INBOX
    )


def _resolve_template_library(
    path: str | Path | None = None,
) -> Path:
    return (
        Path(path).expanduser().resolve()
        if path is not None
        else DEFAULT_TEMPLATE_LIBRARY
    )


def initialize_inbox(
    path: str | Path | None = None,
    *,
    template_library: str | Path | None = None,
) -> dict[str, Any]:
    """
    Initialize an EMPTY active inbox and a separate template library.

    Templates must never be seeded directly into the active inbox because
    preflight intentionally rejects placeholder-bearing JSON.
    """
    inbox = _resolve_inbox(
        path
    )
    library = _resolve_template_library(
        template_library
    )

    inbox.mkdir(
        parents=True,
        exist_ok=True,
    )
    library.mkdir(
        parents=True,
        exist_ok=True,
    )

    created_templates = []
    skipped_templates = []

    for name, value in templates().items():
        target = library / f"{name}.json"

        if target.exists():
            skipped_templates.append(
                str(target)
            )
            continue

        target.write_text(
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        target.chmod(
            0o600
        )
        created_templates.append(
            str(target)
        )

    return {
        "inbox": str(
            inbox
        ),
        "template_library": str(
            library
        ),
        "inbox_json_count": len(
            list(
                inbox.glob(
                    "*.json"
                )
            )
        ),
        "created_templates": (
            created_templates
        ),
        "skipped_templates": (
            skipped_templates
        ),
    }


def create_record(
    *,
    template_type: str,
    record_name: str,
    inbox: str | Path | None = None,
    template_library: str | Path | None = None,
) -> Path:
    available = templates()

    if template_type not in available:
        raise EvidenceCollectionError(
            "unsupported evidence template type: "
            + str(
                template_type
            )
        )

    clean_name = str(
        record_name
    ).strip()

    if not clean_name:
        raise EvidenceCollectionError(
            "record_name must not be empty"
        )

    if clean_name.endswith(
        ".json"
    ):
        clean_name = clean_name[:-5]

    if (
        "/" in clean_name
        or "\\" in clean_name
        or clean_name in {
            ".",
            "..",
        }
    ):
        raise EvidenceCollectionError(
            "record_name must be a simple file name"
        )

    active_inbox = _resolve_inbox(
        inbox
    )
    library = _resolve_template_library(
        template_library
    )

    active_inbox.mkdir(
        parents=True,
        exist_ok=True,
    )
    library.mkdir(
        parents=True,
        exist_ok=True,
    )

    library_template = (
        library
        / f"{template_type}.json"
    )

    if not library_template.exists():
        initialize_inbox(
            active_inbox,
            template_library=library,
        )

    value = _read_json(
        library_template
    )

    target = (
        active_inbox
        / f"{clean_name}.json"
    )

    if target.exists():
        raise EvidenceCollectionError(
            f"evidence record already exists: {target}"
        )

    target.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    target.chmod(
        0o600
    )

    return target


def workspace_status(
    *,
    inbox: str | Path | None = None,
    template_library: str | Path | None = None,
) -> dict[str, Any]:
    active_inbox = _resolve_inbox(
        inbox
    )
    library = _resolve_template_library(
        template_library
    )

    inbox_files = (
        sorted(
            path.name
            for path in active_inbox.glob(
                "*.json"
            )
            if path.is_file()
        )
        if active_inbox.exists()
        else []
    )

    template_files = (
        sorted(
            path.name
            for path in library.glob(
                "*.json"
            )
            if path.is_file()
        )
        if library.exists()
        else []
    )

    return {
        "inbox": str(
            active_inbox
        ),
        "template_library": str(
            library
        ),
        "inbox_files": inbox_files,
        "template_files": template_files,
        "inbox_count": len(
            inbox_files
        ),
        "template_count": len(
            template_files
        ),
    }


def _json_files(
    path: str | Path | None = None,
) -> list[Path]:
    inbox = (
        Path(path).expanduser().resolve()
        if path is not None
        else DEFAULT_INBOX
    )

    if not inbox.exists():
        raise EvidenceCollectionError(
            f"inbox does not exist: {inbox}"
        )

    return sorted(
        item
        for item in inbox.glob(
            "*.json"
        )
        if item.is_file()
    )


def preflight_inbox(
    *,
    store: DurableEvidenceStore,
    inbox: str | Path | None = None,
) -> dict[str, Any]:
    files = _json_files(
        inbox
    )

    existing = store.load()
    staging = EvidenceLedger()

    # Reconstruct existing entries into staging through the durable file because
    # EvidenceLedger intentionally does not expose mutable entry APIs.
    if store.path.exists():
        with store.path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                mapping = json.loads(
                    raw
                )
                staging.ingest(
                    envelope_from_mapping(
                        mapping
                    )
                )

    envelopes = []
    errors = []

    for path in files:
        try:
            value = _read_json(
                path
            )
            envelope = envelope_from_input(
                value
            )
            staging.ingest(
                envelope
            )
            envelopes.append(
                (
                    path,
                    envelope,
                )
            )
        except Exception as exc:
            errors.append({
                "file": str(path),
                "error": str(exc),
            })

    if errors:
        return {
            "valid": False,
            "files": len(files),
            "ready": len(envelopes),
            "errors": errors,
            "ledger_head_digest": existing.head_digest,
        }

    return {
        "valid": True,
        "files": len(files),
        "ready": len(envelopes),
        "errors": [],
        "ledger_head_digest": existing.head_digest,
        "envelopes": envelopes,
    }


def ingest_inbox(
    *,
    store: DurableEvidenceStore,
    inbox: str | Path | None = None,
) -> dict[str, Any]:
    preflight = preflight_inbox(
        store=store,
        inbox=inbox,
    )

    if not preflight["valid"]:
        raise EvidenceCollectionError(
            "inbox preflight failed; no new records were appended"
        )

    created = 0
    replayed = 0

    for _path, envelope in preflight[
        "envelopes"
    ]:
        result = store.append(
            envelope
        )
        if result["created"]:
            created += 1
        else:
            replayed += 1

    summary = store.summary()

    return {
        "created": created,
        "replayed": replayed,
        "summary": summary,
    }


def progress(
    store: DurableEvidenceStore,
) -> dict[str, Any]:
    counts = Counter()
    proof_labels = {}
    active_partners = 0

    if store.path.exists():
        with store.path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue

                value = json.loads(
                    raw
                )

                origin = str(
                    value.get(
                        "origin",
                        "",
                    )
                ).strip().upper()

                if origin == "TEST_FIXTURE":
                    continue

                evidence_type = str(
                    value.get(
                        "evidence_type",
                        "",
                    )
                ).strip().upper()

                counts[
                    evidence_type
                ] += 1

                payload = value.get(
                    "payload",
                    {}
                )

                if (
                    evidence_type
                    == "DESIGN_PARTNER_COMMITMENT"
                    and str(
                        payload.get(
                            "pilot_status",
                            "",
                        )
                    ).strip().upper()
                    == "ACTIVE"
                ):
                    active_partners += 1

                if evidence_type == "GATE_PROOF":
                    label = str(
                        payload.get(
                            "label",
                            "",
                        )
                    ).strip()
                    state = str(
                        payload.get(
                            "state",
                            "",
                        )
                    ).strip().upper()

                    if label:
                        proof_labels[
                            label
                        ] = state

    summary = store.summary()

    missing = [
        label
        for label in REQUIRED_PROOF_LABELS
        if label not in proof_labels
    ]

    return {
        "ledger": summary,
        "counts_by_evidence_type": dict(
            sorted(
                counts.items()
            )
        ),
        "discovery_interviews": counts[
            "DISCOVERY_INTERVIEW"
        ],
        "design_partner_commitments": counts[
            "DESIGN_PARTNER_COMMITMENT"
        ],
        "active_partner_evidence": (
            active_partners
        ),
        "pilot_onboarding_records": counts[
            "PILOT_ONBOARDING"
        ],
        "pilot_metric_snapshots": counts[
            "PILOT_METRIC_SNAPSHOT"
        ],
        "merchant_feedback_records": counts[
            "MERCHANT_FEEDBACK"
        ],
        "support_evidence_records": counts[
            "SUPPORT_EVIDENCE"
        ],
        "incident_evidence_records": counts[
            "INCIDENT_EVIDENCE"
        ],
        "public_mvp_90d_snapshots": counts[
            "PUBLIC_MVP_90D_SNAPSHOT"
        ],
        "gate_proofs": proof_labels,
        "missing_gate_proofs": missing,
        "phase7_complete_claimed": False,
    }
