from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
from typing import Any

from validation.runtime import (
    DesignPartnerCommitment,
    DiscoveryInterview,
    ProductMarketValidationRegistry,
    ValidationEvidenceError,
)
from validation.evidence.collection import (
    DEFAULT_INBOX,
    EvidenceCollectionError,
    envelope_from_input,
)
from validation.evidence.store import (
    DurableEvidenceStore,
    EvidenceStoreError,
    envelope_from_mapping,
)


class EvidenceDerivationError(ValueError):
    pass


def _iter_real_envelopes(
    store: DurableEvidenceStore,
):
    """
    Yield validated, decision-eligible durable envelopes in ledger order.

    TEST_FIXTURE records are intentionally excluded.
    """
    if not store.path.exists():
        return

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
                mapping = json.loads(
                    raw
                )
            except json.JSONDecodeError as exc:
                raise EvidenceDerivationError(
                    f"invalid JSON at ledger line {line_number}"
                ) from exc

            if not isinstance(
                mapping,
                dict,
            ):
                raise EvidenceDerivationError(
                    f"ledger line {line_number} must be a JSON object"
                )

            try:
                envelope = envelope_from_mapping(
                    mapping
                )
            except (
                EvidenceStoreError,
                Exception,
            ) as exc:
                raise EvidenceDerivationError(
                    f"invalid evidence at ledger line {line_number}: {exc}"
                ) from exc

            if (
                str(
                    envelope.origin
                ).strip().upper()
                == "TEST_FIXTURE"
            ):
                continue

            yield envelope


def _tuple_products(
    value: Any,
) -> tuple[str, ...]:
    if not isinstance(
        value,
        (list, tuple),
    ):
        raise EvidenceDerivationError(
            "products must be an array"
        )

    return tuple(
        str(item)
        for item in value
    )


def _mapping(
    name: str,
    value: Any,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(
        value,
        dict,
    ):
        raise EvidenceDerivationError(
            f"{name} must be a JSON object"
        )

    return dict(
        value
    )


def _discovery_interview(
    payload: dict[str, Any],
) -> DiscoveryInterview:
    required = {
        "interview_id",
        "merchant_ref",
        "merchant_segment",
        "conducted_at",
        "products",
        "core_problem_material",
        "willingness_to_test",
        "structured_feedback_available",
        "evidence_ref",
    }

    missing = required - set(
        payload
    )
    if missing:
        raise EvidenceDerivationError(
            "DISCOVERY_INTERVIEW payload missing fields: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    interview = DiscoveryInterview(
        interview_id=payload[
            "interview_id"
        ],
        merchant_ref=payload[
            "merchant_ref"
        ],
        merchant_segment=payload[
            "merchant_segment"
        ],
        conducted_at=payload[
            "conducted_at"
        ],
        products=_tuple_products(
            payload[
                "products"
            ]
        ),
        core_problem_material=payload[
            "core_problem_material"
        ],
        willingness_to_test=payload[
            "willingness_to_test"
        ],
        structured_feedback_available=payload[
            "structured_feedback_available"
        ],
        evidence_ref=payload[
            "evidence_ref"
        ],
        metadata=_mapping(
            "metadata",
            payload.get(
                "metadata",
                {},
            ),
        ),
    )
    interview.validate()
    return interview


def _design_partner_commitment(
    payload: dict[str, Any],
) -> DesignPartnerCommitment:
    required = {
        "commitment_id",
        "merchant_ref",
        "products",
        "committed_at",
        "active_retail_operations",
        "real_inventory",
        "real_customers",
        "transaction_volume_confirmed",
        "willingness_to_test",
        "structured_feedback_available",
        "pilot_status",
        "evidence_ref",
    }

    missing = required - set(
        payload
    )
    if missing:
        raise EvidenceDerivationError(
            "DESIGN_PARTNER_COMMITMENT payload missing fields: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    commitment = DesignPartnerCommitment(
        commitment_id=payload[
            "commitment_id"
        ],
        merchant_ref=payload[
            "merchant_ref"
        ],
        products=_tuple_products(
            payload[
                "products"
            ]
        ),
        committed_at=payload[
            "committed_at"
        ],
        active_retail_operations=payload[
            "active_retail_operations"
        ],
        real_inventory=payload[
            "real_inventory"
        ],
        real_customers=payload[
            "real_customers"
        ],
        transaction_volume_confirmed=payload[
            "transaction_volume_confirmed"
        ],
        willingness_to_test=payload[
            "willingness_to_test"
        ],
        structured_feedback_available=payload[
            "structured_feedback_available"
        ],
        pilot_status=payload[
            "pilot_status"
        ],
        evidence_ref=payload[
            "evidence_ref"
        ],
        metadata=_mapping(
            "metadata",
            payload.get(
                "metadata",
                {},
            ),
        ),
    )
    commitment.validate()
    return commitment




def _pilot_status_transition(
    payload: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "transition_id", "commitment_id", "merchant_ref",
        "from_status", "to_status", "changed_at", "evidence_ref",
    }
    missing = required - set(payload)
    if missing:
        raise EvidenceDerivationError(
            "PILOT_STATUS_TRANSITION payload missing fields: "
            + ", ".join(sorted(missing))
        )
    result = {
        "transition_id": str(payload["transition_id"]).strip(),
        "commitment_id": str(payload["commitment_id"]).strip(),
        "merchant_ref": str(payload["merchant_ref"]).strip(),
        "from_status": str(payload["from_status"]).strip().upper(),
        "to_status": str(payload["to_status"]).strip().upper(),
        "changed_at": str(payload["changed_at"]).strip(),
        "evidence_ref": str(payload["evidence_ref"]).strip(),
        "metadata": _mapping("metadata", payload.get("metadata", {})),
    }
    if not result["transition_id"]:
        raise EvidenceDerivationError("PILOT_STATUS_TRANSITION transition_id must not be empty")
    return result
def derive_discovery_gate(
    store: DurableEvidenceStore,
) -> dict[str, Any]:
    """
    Reconstruct ProductMarketValidationRegistry from durable real evidence.

    The canonical ProductMarketValidationRegistry remains the source of truth
    for the discovery/design-partner gate. This function does not weaken or
    bypass any threshold.
    """
    try:
        ledger = store.load()
    except EvidenceStoreError as exc:
        raise EvidenceDerivationError(
            str(
                exc
            )
        ) from exc

    if not ledger.verify_chain():
        raise EvidenceDerivationError(
            "evidence ledger chain verification failed"
        )

    registry = ProductMarketValidationRegistry()
    current_commitments: dict[str, DesignPartnerCommitment] = {}

    source_evidence_refs: list[str] = []
    source_envelope_ids: list[str] = []
    counts = {
        "DISCOVERY_INTERVIEW": 0,
        "DESIGN_PARTNER_COMMITMENT": 0,
        "PILOT_STATUS_TRANSITION": 0,
    }

    try:
        envelopes = _iter_real_envelopes(
            store
        )
        if envelopes is not None:
            for envelope in envelopes:
                evidence_type = str(
                    envelope.evidence_type
                ).strip().upper()

                if evidence_type == "DISCOVERY_INTERVIEW":
                    registry.record_interview(
                        _discovery_interview(
                            envelope.payload
                        )
                    )
                elif evidence_type == "DESIGN_PARTNER_COMMITMENT":
                    commitment = _design_partner_commitment(
                        envelope.payload
                    )
                    registry.record_commitment(commitment)
                    current_commitments[commitment.commitment_id] = commitment
                elif evidence_type == "PILOT_STATUS_TRANSITION":
                    transition = _pilot_status_transition(envelope.payload)
                    current = current_commitments.get(transition["commitment_id"])
                    if current is None:
                        raise EvidenceDerivationError(
                            "pilot status transition references missing commitment"
                        )
                    if current.merchant_ref != transition["merchant_ref"]:
                        raise EvidenceDerivationError(
                            "pilot status transition merchant_ref mismatch"
                        )
                    if current.pilot_status != transition["from_status"]:
                        raise EvidenceDerivationError(
                            "pilot status transition from_status does not match current status"
                        )
                    updated = registry.transition_pilot_status(
                        commitment_id=transition["commitment_id"],
                        target_status=transition["to_status"],
                        changed_at=transition["changed_at"],
                        evidence_ref=transition["evidence_ref"],
                    )
                    current_commitments[updated.commitment_id] = updated
                else:
                    continue

                counts[
                    evidence_type
                ] += 1
                source_evidence_refs.append(
                    envelope.evidence_ref
                )
                source_envelope_ids.append(
                    envelope.envelope_id
                )
    except (
        ValidationEvidenceError,
        EvidenceDerivationError,
    ) as exc:
        raise EvidenceDerivationError(
            f"cannot derive discovery gate from durable evidence: {exc}"
        ) from exc

    gate = registry.discovery_gate()

    return {
        "gate": asdict(
            gate
        ),
        "source_counts": counts,
        "source_evidence_refs": tuple(
            source_evidence_refs
        ),
        "source_envelope_ids": tuple(
            source_envelope_ids
        ),
        "ledger_head_digest": ledger.head_digest,
        "ledger_count": ledger.count,
        "decision_eligible_only": True,
        "fixture_evidence_excluded": True,
        "thresholds_waived": False,
    }


def discovery_gate_proof_input(
    *,
    derivation: dict[str, Any],
) -> dict[str, Any]:
    gate = dict(
        derivation[
            "gate"
        ]
    )

    state = str(
        gate.get(
            "state",
            "",
        )
    ).strip().upper()

    if state != "PASS":
        raise EvidenceDerivationError(
            "discovery gate is not PASS; GATE_PROOF emission is prohibited"
        )

    evidence_digest = str(
        gate.get(
            "evidence_digest",
            "",
        )
    ).strip().lower()

    if len(
        evidence_digest
    ) != 64:
        raise EvidenceDerivationError(
            "canonical discovery evidence_digest is invalid"
        )

    now = datetime.now().astimezone()
    suffix = evidence_digest[
        :24
    ]

    return {
        "envelope_id": (
            "gate-proof-discovery-"
            + suffix
        ),
        "evidence_type": "GATE_PROOF",
        "origin": "REAL_OPERATIONAL",
        "observed_at": now.isoformat(),
        "evidence_ref": (
            "evidence://phase7/gate-proof/discovery/"
            + evidence_digest
        ),
        "source_system_ref": (
            "source://validation/evidence-derivation"
        ),
        "payload": {
            "label": "discovery",
            "state": "PASS",
            "evidence_digest": (
                evidence_digest
            ),
            "gate": gate.get(
                "gate",
                "DISCOVERY_DESIGN_PARTNER_GATE",
            ),
            "source_ledger_head_digest": derivation[
                "ledger_head_digest"
            ],
            "source_evidence_refs": list(
                derivation[
                    "source_evidence_refs"
                ]
            ),
            "source_envelope_ids": list(
                derivation[
                    "source_envelope_ids"
                ]
            ),
            "derived_at": now.isoformat(),
            "thresholds_waived": False,
            "fixture_evidence_excluded": True,
        },
    }


def emit_discovery_gate_proof(
    *,
    derivation: dict[str, Any],
    inbox: str | Path | None = None,
) -> dict[str, Any]:
    proof_input = discovery_gate_proof_input(
        derivation=derivation
    )

    try:
        envelope = envelope_from_input(
            proof_input
        )
    except EvidenceCollectionError as exc:
        raise EvidenceDerivationError(
            f"derived GATE_PROOF failed canonical envelope validation: {exc}"
        ) from exc

    target_dir = (
        Path(
            inbox
        ).expanduser().resolve()
        if inbox is not None
        else DEFAULT_INBOX
    )

    target_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = (
        target_dir
        / (
            envelope.envelope_id
            + ".json"
        )
    )

    serialized = (
        json.dumps(
            proof_input,
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
            raise EvidenceDerivationError(
                "derived proof target already exists with different content"
            )

        return {
            "created": False,
            "path": str(
                target
            ),
            "evidence_ref": (
                envelope.evidence_ref
            ),
            "evidence_digest": (
                envelope.payload[
                    "evidence_digest"
                ]
            ),
            "state": "PASS",
        }

    target.write_text(
        serialized,
        encoding="utf-8",
    )
    target.chmod(
        0o600
    )

    return {
        "created": True,
        "path": str(
            target
        ),
        "evidence_ref": (
            envelope.evidence_ref
        ),
        "evidence_digest": (
            envelope.payload[
                "evidence_digest"
            ]
        ),
        "state": "PASS",
    }
