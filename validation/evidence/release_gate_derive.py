from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import json
from typing import Any

from validation.evidence.collection import (
    DEFAULT_INBOX,
    EvidenceCollectionError,
    envelope_from_input,
)
from validation.evidence.derive import (
    EvidenceDerivationError,
    derive_discovery_gate,
)
from validation.evidence.store import (
    DurableEvidenceStore,
    EvidenceStoreError,
)
from validation.pilot_runtime import (
    PilotValidationError,
    PilotValidationRegistry,
    TechnicalAttestation,
)


class ReleaseGateDerivationError(ValueError):
    pass


def _read_rows(
    store: DurableEvidenceStore,
) -> list[dict[str, Any]]:
    if not store.path.exists():
        return []

    rows: list[dict[str, Any]] = []

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
                value = json.loads(
                    raw
                )
            except json.JSONDecodeError as exc:
                raise ReleaseGateDerivationError(
                    f"invalid JSON at ledger line {line_number}"
                ) from exc

            if not isinstance(
                value,
                dict,
            ):
                raise ReleaseGateDerivationError(
                    f"ledger line {line_number} must be an object"
                )

            rows.append(
                value
            )

    return rows


def _technical_attestations(
    store: DurableEvidenceStore,
) -> tuple[
    list[TechnicalAttestation],
    list[str],
    list[str],
]:
    attestations: list[
        TechnicalAttestation
    ] = []
    evidence_refs: list[str] = []
    envelope_ids: list[str] = []

    for value in _read_rows(
        store
    ):
        origin = str(
            value.get(
                "origin",
                "",
            )
        ).strip().upper()

        if origin == "TEST_FIXTURE":
            continue

        if origin != "REAL_OPERATIONAL":
            continue

        if (
            str(
                value.get(
                    "evidence_type",
                    "",
                )
            ).strip().upper()
            != "TECHNICAL_ATTESTATION"
        ):
            continue

        payload = value.get(
            "payload",
            {},
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise ReleaseGateDerivationError(
                "TECHNICAL_ATTESTATION payload must be an object"
            )

        required = {
            "attestation_id",
            "requirement",
            "satisfied",
            "observed_at",
            "evidence_ref",
            "valid_until",
        }

        missing = required - set(
            payload
        )

        if missing:
            raise ReleaseGateDerivationError(
                "TECHNICAL_ATTESTATION payload missing fields: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        metadata = payload.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            raise ReleaseGateDerivationError(
                "TECHNICAL_ATTESTATION metadata must be an object"
            )

        attestation = TechnicalAttestation(
            attestation_id=payload[
                "attestation_id"
            ],
            requirement=payload[
                "requirement"
            ],
            satisfied=payload[
                "satisfied"
            ],
            observed_at=payload[
                "observed_at"
            ],
            evidence_ref=payload[
                "evidence_ref"
            ],
            valid_until=payload[
                "valid_until"
            ],
            metadata=dict(
                metadata
            ),
        )

        try:
            attestation.validate()
        except PilotValidationError as exc:
            raise ReleaseGateDerivationError(
                f"invalid TECHNICAL_ATTESTATION: {exc}"
            ) from exc

        attestations.append(
            attestation
        )
        evidence_refs.append(
            str(
                value.get(
                    "evidence_ref",
                    "",
                )
            )
        )
        envelope_ids.append(
            str(
                value.get(
                    "envelope_id",
                    "",
                )
            )
        )

    return (
        attestations,
        evidence_refs,
        envelope_ids,
    )


def _registry_from_ledger(
    store: DurableEvidenceStore,
) -> tuple[
    PilotValidationRegistry,
    list[str],
    list[str],
]:
    registry = PilotValidationRegistry()

    (
        attestations,
        evidence_refs,
        envelope_ids,
    ) = _technical_attestations(
        store
    )

    try:
        for attestation in attestations:
            registry.record_attestation(
                attestation
            )
    except PilotValidationError as exc:
        raise ReleaseGateDerivationError(
            f"cannot reconstruct release-gate attestation registry: {exc}"
        ) from exc

    return (
        registry,
        evidence_refs,
        envelope_ids,
    )


def derive_release_gate_1(
    store: DurableEvidenceStore,
    *,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """
    Canonical Gate 1 derivation.

    Gate 1 remains dependent on the canonical Discovery Gate. Deferring the
    discovery target does not convert a PENDING Discovery Gate into PASS.
    """
    evaluated_at = (
        evaluated_at
        or datetime.now().astimezone().isoformat()
    )

    (
        registry,
        evidence_refs,
        envelope_ids,
    ) = _registry_from_ledger(
        store
    )

    discovery = derive_discovery_gate(
        store
    )

    discovery_gate = SimpleNamespace(
        **discovery[
            "gate"
        ]
    )

    try:
        result = registry.release_gate_1(
            discovery_gate=discovery_gate,
            evaluated_at=evaluated_at,
        )
    except PilotValidationError as exc:
        raise ReleaseGateDerivationError(
            f"Gate 1 derivation failed: {exc}"
        ) from exc

    return {
        "label": "release_gate_1",
        "gate": asdict(
            result
        ),
        "evaluated_at": evaluated_at,
        "technical_attestation_count": len(
            evidence_refs
        ),
        "technical_evidence_refs": evidence_refs,
        "technical_envelope_ids": envelope_ids,
        "discovery_gate": discovery[
            "gate"
        ],
        "fixture_evidence_excluded": True,
        "required_origin": "REAL_OPERATIONAL",
        "thresholds_waived": False,
    }


def derive_release_gate_2(
    store: DurableEvidenceStore,
    *,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """
    Canonical Gate 2 derivation from durable real technical attestations.
    """
    evaluated_at = (
        evaluated_at
        or datetime.now().astimezone().isoformat()
    )

    (
        registry,
        evidence_refs,
        envelope_ids,
    ) = _registry_from_ledger(
        store
    )

    try:
        result = registry.release_gate_2(
            evaluated_at=evaluated_at,
        )
    except PilotValidationError as exc:
        raise ReleaseGateDerivationError(
            f"Gate 2 derivation failed: {exc}"
        ) from exc

    return {
        "label": "release_gate_2",
        "gate": asdict(
            result
        ),
        "evaluated_at": evaluated_at,
        "technical_attestation_count": len(
            evidence_refs
        ),
        "technical_evidence_refs": evidence_refs,
        "technical_envelope_ids": envelope_ids,
        "fixture_evidence_excluded": True,
        "required_origin": "REAL_OPERATIONAL",
        "thresholds_waived": False,
    }


def _proof_input(
    derivation: dict[str, Any],
) -> dict[str, Any]:
    label = str(
        derivation.get(
            "label",
            "",
        )
    ).strip()

    if label not in {
        "release_gate_1",
        "release_gate_2",
    }:
        raise ReleaseGateDerivationError(
            "unsupported release-gate proof label"
        )

    gate = derivation.get(
        "gate",
        {},
    )

    if not isinstance(
        gate,
        dict,
    ):
        raise ReleaseGateDerivationError(
            "gate result must be an object"
        )

    state = str(
        gate.get(
            "state",
            "",
        )
    ).strip().upper()

    if state != "PASS":
        raise ReleaseGateDerivationError(
            f"{label} is not PASS; GATE_PROOF emission is prohibited"
        )

    digest = str(
        gate.get(
            "evidence_digest",
            "",
        )
    ).strip().lower()

    if len(
        digest
    ) != 64:
        raise ReleaseGateDerivationError(
            "canonical gate evidence_digest is invalid"
        )

    observed_at = str(
        derivation.get(
            "evaluated_at",
            "",
        )
    ).strip()

    return {
        "envelope_id": (
            f"gate-proof-{label}-{digest[:24]}"
        ),
        "evidence_type": "GATE_PROOF",
        "origin": "REAL_OPERATIONAL",
        "observed_at": observed_at,
        "evidence_ref": (
            f"evidence://phase7/gate-proof/{label}/{digest}"
        ),
        "source_system_ref": (
            "source://validation/release-gate-derivation"
        ),
        "payload": {
            "label": label,
            "state": "PASS",
            "evidence_digest": digest,
        },
    }


def emit_release_gate_proof(
    derivation: dict[str, Any],
    *,
    inbox: str | Path | None = None,
) -> dict[str, Any]:
    proof_input = _proof_input(
        derivation
    )

    try:
        envelope = envelope_from_input(
            proof_input
        )
    except EvidenceCollectionError as exc:
        raise ReleaseGateDerivationError(
            f"derived GATE_PROOF failed canonical validation: {exc}"
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
            raise ReleaseGateDerivationError(
                "proof target exists with different evaluated evidence"
            )

        return {
            "created": False,
            "path": str(
                target
            ),
            "label": envelope.payload[
                "label"
            ],
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
        "label": envelope.payload[
            "label"
        ],
        "state": "PASS",
    }
