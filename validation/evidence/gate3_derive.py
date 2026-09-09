from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
from typing import Any

from validation.evidence.collection import (
    DEFAULT_INBOX,
    EvidenceCollectionError,
    envelope_from_input,
)
from validation.evidence.store import (
    DurableEvidenceStore,
    EvidenceStoreError,
)
from validation.pilot_runtime import (
    CapacitySnapshot,
    OnboardingEvent,
    PilotMetricSnapshot,
    PilotOnboarding,
    PilotValidationError,
    PilotValidationRegistry,
    TechnicalAttestation,
)
from validation.runtime import (
    DesignPartnerCommitment,
    ProductMarketValidationRegistry,
    ValidationEvidenceError,
)


class Gate3DerivationError(ValueError):
    pass


def _mapping(name: str, value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise Gate3DerivationError(
            f"{name} must be a JSON object"
        )
    return dict(value)


def _products(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise Gate3DerivationError(
            "products must be an array"
        )
    return tuple(str(item) for item in value)


def _read_rows(
    store: DurableEvidenceStore,
) -> list[dict[str, Any]]:
    if not store.path.exists():
        return []

    ordered_rows: list[dict[str, Any]] = []
    prior_by_envelope_id: dict[str, dict[str, Any]] = {}
    voided_envelope_ids: set[str] = set()

    with store.path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line_number, raw in enumerate(
            handle,
            start=1,
        ):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise Gate3DerivationError(
                    f"invalid JSON at ledger line {line_number}"
                ) from exc

            if not isinstance(value, dict):
                raise Gate3DerivationError(
                    f"ledger line {line_number} must be an object"
                )

            if (
                str(value.get("origin", "")).strip().upper()
                == "TEST_FIXTURE"
            ):
                continue

            envelope_id = str(
                value.get("envelope_id", "")
            ).strip()
            evidence_type = str(
                value.get("evidence_type", "")
            ).strip().upper()

            if not envelope_id:
                raise Gate3DerivationError(
                    f"ledger line {line_number} missing envelope_id"
                )

            if envelope_id in prior_by_envelope_id:
                raise Gate3DerivationError(
                    f"duplicate envelope_id at ledger line {line_number}"
                )

            if evidence_type == "EVIDENCE_VOID":
                payload = value.get("payload", {})
                if not isinstance(payload, dict):
                    raise Gate3DerivationError(
                        "EVIDENCE_VOID payload must be an object"
                    )

                target_envelope_id = str(
                    payload.get("target_envelope_id", "")
                ).strip()
                target_type = str(
                    payload.get("target_evidence_type", "")
                ).strip().upper()
                target_event_id = str(
                    payload.get("target_event_id", "")
                ).strip()
                target_digest = str(
                    payload.get("target_content_sha256", "")
                ).strip().lower()

                target = prior_by_envelope_id.get(
                    target_envelope_id
                )
                if target is None:
                    raise Gate3DerivationError(
                        "EVIDENCE_VOID target must reference a prior envelope"
                    )

                if target_envelope_id in voided_envelope_ids:
                    raise Gate3DerivationError(
                        "duplicate EVIDENCE_VOID for target envelope"
                    )

                actual_type = str(
                    target.get("evidence_type", "")
                ).strip().upper()
                if (
                    target_type != "PILOT_ONBOARDING_EVENT"
                    or actual_type != target_type
                ):
                    raise Gate3DerivationError(
                        "EVIDENCE_VOID may only target PILOT_ONBOARDING_EVENT"
                    )

                actual_digest = str(
                    target.get("content_sha256", "")
                ).strip().lower()
                if (
                    len(target_digest) != 64
                    or target_digest != actual_digest
                ):
                    raise Gate3DerivationError(
                        "EVIDENCE_VOID target content digest mismatch"
                    )

                target_payload = target.get("payload", {})
                if not isinstance(target_payload, dict):
                    raise Gate3DerivationError(
                        "void target payload must be an object"
                    )

                actual_event_id = str(
                    target_payload.get("event_id", "")
                ).strip()
                if (
                    not target_event_id
                    or target_event_id != actual_event_id
                ):
                    raise Gate3DerivationError(
                        "EVIDENCE_VOID target event_id mismatch"
                    )

                voided_envelope_ids.add(
                    target_envelope_id
                )
                prior_by_envelope_id[envelope_id] = value
                continue

            prior_by_envelope_id[envelope_id] = value
            ordered_rows.append(value)

    return [
        row
        for row in ordered_rows
        if str(row.get("envelope_id", "")).strip()
        not in voided_envelope_ids
    ]

def _commitment(
    payload: dict[str, Any],
) -> DesignPartnerCommitment:
    result = DesignPartnerCommitment(
        commitment_id=payload["commitment_id"],
        merchant_ref=payload["merchant_ref"],
        products=_products(payload["products"]),
        committed_at=payload["committed_at"],
        active_retail_operations=payload[
            "active_retail_operations"
        ],
        real_inventory=payload["real_inventory"],
        real_customers=payload["real_customers"],
        transaction_volume_confirmed=payload[
            "transaction_volume_confirmed"
        ],
        willingness_to_test=payload["willingness_to_test"],
        structured_feedback_available=payload[
            "structured_feedback_available"
        ],
        pilot_status=payload["pilot_status"],
        evidence_ref=payload["evidence_ref"],
        metadata=_mapping(
            "commitment.metadata",
            payload.get("metadata", {}),
        ),
    )
    result.validate()
    return result


def _transition(
    payload: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "transition_id",
        "commitment_id",
        "merchant_ref",
        "from_status",
        "to_status",
        "changed_at",
        "evidence_ref",
    }
    missing = required - set(payload)
    if missing:
        raise Gate3DerivationError(
            "PILOT_STATUS_TRANSITION missing fields: "
            + ", ".join(sorted(missing))
        )
    return {
        "transition_id": str(payload["transition_id"]).strip(),
        "commitment_id": str(payload["commitment_id"]).strip(),
        "merchant_ref": str(payload["merchant_ref"]).strip(),
        "from_status": str(payload["from_status"]).strip().upper(),
        "to_status": str(payload["to_status"]).strip().upper(),
        "changed_at": str(payload["changed_at"]).strip(),
        "evidence_ref": str(payload["evidence_ref"]).strip(),
    }


def _onboarding(
    payload: dict[str, Any],
) -> PilotOnboarding:
    result = PilotOnboarding(
        onboarding_id=payload["onboarding_id"],
        commitment_id=payload["commitment_id"],
        merchant_ref=payload["merchant_ref"],
        products=_products(payload["products"]),
        started_at=payload["started_at"],
        evidence_ref=payload["evidence_ref"],
        metadata=_mapping(
            "onboarding.metadata",
            payload.get("metadata", {}),
        ),
    )
    result.validate()
    return result


def _event(
    payload: dict[str, Any],
) -> OnboardingEvent:
    result = OnboardingEvent(
        event_id=payload["event_id"],
        onboarding_id=payload["onboarding_id"],
        merchant_ref=payload["merchant_ref"],
        step=payload["step"],
        status=payload["status"],
        occurred_at=payload["occurred_at"],
        evidence_ref=payload["evidence_ref"],
        failure_code=payload.get("failure_code"),
        training_required=payload.get(
            "training_required",
            False,
        ),
        support_intervention=payload.get(
            "support_intervention",
            False,
        ),
        metadata=_mapping(
            "event.metadata",
            payload.get("metadata", {}),
        ),
    )
    result.validate()
    return result


def _metric(
    payload: dict[str, Any],
) -> PilotMetricSnapshot:
    fields = {
        key: value
        for key, value in payload.items()
        if key != "metadata"
    }
    fields["metadata"] = _mapping(
        "metric.metadata",
        payload.get("metadata", {}),
    )
    result = PilotMetricSnapshot(**fields)
    result.validate()
    return result


def _capacity(
    payload: dict[str, Any],
) -> CapacitySnapshot:
    result = CapacitySnapshot(
        snapshot_id=payload["snapshot_id"],
        observed_at=payload["observed_at"],
        organizations=payload["organizations"],
        pos_branches=payload["pos_branches"],
        monthly_orders=payload["monthly_orders"],
        evidence_ref=payload["evidence_ref"],
    )
    result.validate()
    return result


def _attestation(
    payload: dict[str, Any],
) -> TechnicalAttestation:
    result = TechnicalAttestation(
        attestation_id=payload["attestation_id"],
        requirement=payload["requirement"],
        satisfied=payload["satisfied"],
        observed_at=payload["observed_at"],
        evidence_ref=payload["evidence_ref"],
        valid_until=payload.get("valid_until"),
        metadata=_mapping(
            "attestation.metadata",
            payload.get("metadata", {}),
        ),
    )
    result.validate()
    return result


def reconstruct_gate3_registry(
    store: DurableEvidenceStore,
) -> dict[str, Any]:
    try:
        ledger = store.load()
    except EvidenceStoreError as exc:
        raise Gate3DerivationError(str(exc)) from exc

    if not ledger.verify_chain():
        raise Gate3DerivationError(
            "evidence ledger chain verification failed"
        )

    partner_registry = ProductMarketValidationRegistry()
    pilot_registry = PilotValidationRegistry()

    current_commitments: dict[
        str,
        DesignPartnerCommitment,
    ] = {}

    source_refs: list[str] = []
    source_envelope_ids: list[str] = []
    metric_ids: list[str] = []
    capacity_ids: list[str] = []

    counts = {
        "DESIGN_PARTNER_COMMITMENT": 0,
        "PILOT_STATUS_TRANSITION": 0,
        "PILOT_ONBOARDING": 0,
        "PILOT_ONBOARDING_EVENT": 0,
        "PILOT_METRIC_SNAPSHOT": 0,
        "CAPACITY_SNAPSHOT": 0,
        "TECHNICAL_ATTESTATION": 0,
    }

    try:
        for row in _read_rows(store):
            evidence_type = str(
                row.get("evidence_type", "")
            ).strip().upper()

            payload = row.get("payload", {})
            if not isinstance(payload, dict):
                raise Gate3DerivationError(
                    f"{evidence_type} payload must be an object"
                )

            consumed = False

            if evidence_type == "DESIGN_PARTNER_COMMITMENT":
                commitment = _commitment(payload)
                partner_registry.record_commitment(
                    commitment
                )
                current_commitments[
                    commitment.commitment_id
                ] = commitment
                consumed = True

            elif evidence_type == "PILOT_STATUS_TRANSITION":
                transition = _transition(payload)
                current = current_commitments.get(
                    transition["commitment_id"]
                )
                if current is None:
                    raise Gate3DerivationError(
                        "pilot status transition references missing commitment"
                    )
                if (
                    current.merchant_ref
                    != transition["merchant_ref"]
                ):
                    raise Gate3DerivationError(
                        "pilot status transition merchant_ref mismatch"
                    )
                if (
                    current.pilot_status
                    != transition["from_status"]
                ):
                    raise Gate3DerivationError(
                        "pilot status transition from_status does not match current status"
                    )
                updated = partner_registry.transition_pilot_status(
                    commitment_id=transition["commitment_id"],
                    target_status=transition["to_status"],
                    changed_at=transition["changed_at"],
                    evidence_ref=transition["evidence_ref"],
                )
                current_commitments[
                    updated.commitment_id
                ] = updated
                consumed = True

            elif evidence_type == "PILOT_ONBOARDING":
                onboarding = _onboarding(payload)
                commitment = current_commitments.get(
                    onboarding.commitment_id
                )
                if commitment is None:
                    raise Gate3DerivationError(
                        "pilot onboarding references missing commitment"
                    )
                pilot_registry.start_onboarding(
                    commitment=commitment,
                    onboarding=onboarding,
                )
                consumed = True

            elif evidence_type == "PILOT_ONBOARDING_EVENT":
                pilot_registry.record_onboarding_event(
                    _event(payload)
                )
                consumed = True

            elif evidence_type == "PILOT_METRIC_SNAPSHOT":
                metric = _metric(payload)
                pilot_registry.record_metric_snapshot(
                    metric
                )
                metric_ids.append(
                    metric.snapshot_id
                )
                consumed = True

            elif evidence_type == "CAPACITY_SNAPSHOT":
                capacity = _capacity(payload)
                pilot_registry.record_capacity_snapshot(
                    capacity
                )
                capacity_ids.append(
                    capacity.snapshot_id
                )
                consumed = True

            elif evidence_type == "TECHNICAL_ATTESTATION":
                pilot_registry.record_attestation(
                    _attestation(payload)
                )
                consumed = True

            if consumed:
                counts[evidence_type] += 1
                source_refs.append(
                    str(row.get("evidence_ref", ""))
                )
                source_envelope_ids.append(
                    str(row.get("envelope_id", ""))
                )

    except (
        Gate3DerivationError,
        PilotValidationError,
        ValidationEvidenceError,
        KeyError,
        TypeError,
    ) as exc:
        raise Gate3DerivationError(
            f"cannot reconstruct Gate 3 registry: {exc}"
        ) from exc

    return {
        "pilot_registry": pilot_registry,
        "source_counts": counts,
        "source_evidence_refs": tuple(source_refs),
        "source_envelope_ids": tuple(
            source_envelope_ids
        ),
        "metric_snapshot_ids": tuple(metric_ids),
        "capacity_snapshot_ids": tuple(capacity_ids),
        "current_commitments": {
            key: {
                "merchant_ref": value.merchant_ref,
                "pilot_status": value.pilot_status,
                "products": list(value.products),
            }
            for key, value in sorted(
                current_commitments.items()
            )
        },
        "ledger_head_digest": ledger.head_digest,
        "ledger_count": ledger.count,
        "fixture_evidence_excluded": True,
        "thresholds_waived": False,
    }


def derive_release_gate_3(
    store: DurableEvidenceStore,
    *,
    snapshot_id: str,
    capacity_snapshot_id: str,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    state = reconstruct_gate3_registry(
        store
    )

    if snapshot_id not in state[
        "metric_snapshot_ids"
    ]:
        raise Gate3DerivationError(
            "metric snapshot not found in real durable evidence"
        )

    if capacity_snapshot_id not in state[
        "capacity_snapshot_ids"
    ]:
        raise Gate3DerivationError(
            "capacity snapshot not found in real durable evidence"
        )

    evaluated_at = (
        evaluated_at
        or datetime.now().astimezone().isoformat()
    )

    registry = state["pilot_registry"]

    try:
        pilot_exit = registry.pilot_exit_gate(
            snapshot_id
        )
        capacity = registry.capacity_gate(
            capacity_snapshot_id
        )
        gate = registry.release_gate_3(
            snapshot_id=snapshot_id,
            capacity_snapshot_id=capacity_snapshot_id,
            evaluated_at=evaluated_at,
        )
    except PilotValidationError as exc:
        raise Gate3DerivationError(
            f"canonical Gate 3 evaluation failed: {exc}"
        ) from exc

    return {
        "label": "release_gate_3",
        "gate": asdict(gate),
        "pilot_exit": asdict(pilot_exit),
        "capacity": asdict(capacity),
        "snapshot_id": snapshot_id,
        "capacity_snapshot_id": capacity_snapshot_id,
        "evaluated_at": evaluated_at,
        "source_counts": state["source_counts"],
        "source_evidence_refs": state[
            "source_evidence_refs"
        ],
        "source_envelope_ids": state[
            "source_envelope_ids"
        ],
        "ledger_head_digest": state[
            "ledger_head_digest"
        ],
        "ledger_count": state["ledger_count"],
        "fixture_evidence_excluded": True,
        "thresholds_waived": False,
    }


def _proof_input(
    derivation: dict[str, Any],
) -> dict[str, Any]:
    gate = dict(
        derivation.get("gate", {})
    )

    state = str(
        gate.get("state", "")
    ).strip().upper()

    if state != "PASS":
        raise Gate3DerivationError(
            "release_gate_3 is not PASS; GATE_PROOF emission is prohibited"
        )

    digest = str(
        gate.get("evidence_digest", "")
    ).strip().lower()

    if len(digest) != 64:
        raise Gate3DerivationError(
            "canonical Gate 3 evidence_digest is invalid"
        )

    return {
        "envelope_id": (
            "gate-proof-release-gate-3-"
            + digest[:24]
        ),
        "evidence_type": "GATE_PROOF",
        "origin": "REAL_OPERATIONAL",
        "observed_at": derivation["evaluated_at"],
        "evidence_ref": (
            "evidence://phase7/gate-proof/release_gate_3/"
            + digest
        ),
        "source_system_ref": (
            "source://validation/release-gate3-derivation"
        ),
        "payload": {
            "label": "release_gate_3",
            "state": "PASS",
            "evidence_digest": digest,
        },
    }


def emit_release_gate_3_proof(
    derivation: dict[str, Any],
    *,
    inbox: str | Path | None = None,
) -> dict[str, Any]:
    proof = _proof_input(
        derivation
    )

    try:
        envelope = envelope_from_input(
            proof
        )
    except EvidenceCollectionError as exc:
        raise Gate3DerivationError(
            f"derived Gate 3 proof failed evidence validation: {exc}"
        ) from exc

    target_dir = (
        Path(inbox).expanduser().resolve()
        if inbox is not None
        else DEFAULT_INBOX
    )
    target_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = target_dir / (
        envelope.envelope_id + ".json"
    )

    serialized = (
        json.dumps(
            proof,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    if target.exists():
        existing = target.read_text(
            encoding="utf-8"
        )
        if existing != serialized:
            raise Gate3DerivationError(
                "Gate 3 proof target exists with different evidence"
            )
        return {
            "created": False,
            "path": str(target),
            "state": "PASS",
            "label": "release_gate_3",
        }

    target.write_text(
        serialized,
        encoding="utf-8",
    )
    target.chmod(0o600)

    return {
        "created": True,
        "path": str(target),
        "state": "PASS",
        "label": "release_gate_3",
    }
