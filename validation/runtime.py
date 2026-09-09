from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
import json
from typing import Any


PRODUCTS = {
    "COMMERCE",
    "POS",
}

PILOT_STATUSES = {
    "CANDIDATE",
    "ACTIVE",
    "PAUSED",
    "WITHDRAWN",
}

SENSITIVE_FIELD_TERMS = {
    "email",
    "phone",
    "mobile",
    "address",
    "password",
    "secret",
    "token",
    "api_key",
    "card",
    "pan",
    "cvv",
    "cvc",
    "bank",
    "account_number",
}

LAUNCH_CAP = {
    "organizations": 100,
    "pos_branches": 250,
    "monthly_orders": 10000,
}

DISCOVERY_TARGET = {
    "interviews_min": 20,
    "interviews_target_max": 30,
    "commitments_min": 5,
    "commitments_target_max": 10,
    "active_pilots_min": 3,
    "problem_confirmation_rate_min": 0.80,
}


class ValidationEvidenceError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise ValidationEvidenceError(
            f"{name} must not be empty"
        )

    result = str(value).strip()

    if not result:
        raise ValidationEvidenceError(
            f"{name} must not be empty"
        )

    return result


def _time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(
            _text("timestamp", value)
        )
    except ValueError as exc:
        raise ValidationEvidenceError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise ValidationEvidenceError(
            "timestamp must be timezone-aware"
        )

    return parsed.isoformat()


def _merchant_ref(value: str) -> str:
    value = _text(
        "merchant_ref",
        value,
    )

    if not value.startswith(
        "merchant://"
    ):
        raise ValidationEvidenceError(
            "merchant_ref must use merchant://"
        )

    return value


def _evidence_ref(value: str) -> str:
    value = _text(
        "evidence_ref",
        value,
    )

    if not value.startswith(
        "evidence://"
    ):
        raise ValidationEvidenceError(
            "evidence_ref must use evidence://"
        )

    return value


def _products(values: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        raise ValidationEvidenceError(
            "at least one product is required"
        )

    normalized = tuple(
        sorted({
            str(value).strip().upper()
            for value in values
        })
    )

    unsupported = (
        set(normalized)
        - PRODUCTS
    )

    if unsupported:
        raise ValidationEvidenceError(
            "unsupported validation products: "
            + ", ".join(
                sorted(unsupported)
            )
        )

    return normalized


def _safe_mapping(
    value: dict[str, Any],
) -> None:
    def walk(item: Any) -> None:
        if isinstance(
            item,
            dict,
        ):
            for key, nested in item.items():
                normalized = str(
                    key
                ).strip().lower()

                if any(
                    term in normalized
                    for term in SENSITIVE_FIELD_TERMS
                ):
                    raise ValidationEvidenceError(
                        "validation metadata contains sensitive/direct-contact field"
                    )

                walk(
                    nested
                )

        elif isinstance(
            item,
            (
                list,
                tuple,
            ),
        ):
            for nested in item:
                walk(
                    nested
                )

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValidationEvidenceError(
            "metadata must be JSON-compatible"
        ) from exc

    if len(
        encoded
    ) > 8192:
        raise ValidationEvidenceError(
            "metadata exceeds 8192 bytes"
        )

    walk(
        value
    )


def _canonical(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


@dataclass(frozen=True)
class DiscoveryInterview:
    interview_id: str
    merchant_ref: str
    merchant_segment: str
    conducted_at: str
    products: tuple[str, ...]
    core_problem_material: bool
    willingness_to_test: bool
    structured_feedback_available: bool
    evidence_ref: str
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "interview_id",
            self.interview_id,
        )
        _merchant_ref(
            self.merchant_ref
        )
        _text(
            "merchant_segment",
            self.merchant_segment,
        )
        _time(
            self.conducted_at
        )
        _products(
            self.products
        )
        _evidence_ref(
            self.evidence_ref
        )

        for name, value in {
            "core_problem_material": (
                self.core_problem_material
            ),
            "willingness_to_test": (
                self.willingness_to_test
            ),
            "structured_feedback_available": (
                self.structured_feedback_available
            ),
        }.items():
            if not isinstance(
                value,
                bool,
            ):
                raise ValidationEvidenceError(
                    f"{name} must be boolean"
                )

        _safe_mapping(
            self.metadata
        )


@dataclass(frozen=True)
class DesignPartnerCommitment:
    commitment_id: str
    merchant_ref: str
    products: tuple[str, ...]
    committed_at: str
    active_retail_operations: bool
    real_inventory: bool
    real_customers: bool
    transaction_volume_confirmed: bool
    willingness_to_test: bool
    structured_feedback_available: bool
    pilot_status: str
    evidence_ref: str
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "commitment_id",
            self.commitment_id,
        )
        _merchant_ref(
            self.merchant_ref
        )
        _products(
            self.products
        )
        _time(
            self.committed_at
        )
        _evidence_ref(
            self.evidence_ref
        )

        checks = {
            "active_retail_operations": (
                self.active_retail_operations
            ),
            "real_inventory": (
                self.real_inventory
            ),
            "real_customers": (
                self.real_customers
            ),
            "transaction_volume_confirmed": (
                self.transaction_volume_confirmed
            ),
            "willingness_to_test": (
                self.willingness_to_test
            ),
            "structured_feedback_available": (
                self.structured_feedback_available
            ),
        }

        for name, value in checks.items():
            if not isinstance(
                value,
                bool,
            ):
                raise ValidationEvidenceError(
                    f"{name} must be boolean"
                )

            if value is not True:
                raise ValidationEvidenceError(
                    "design partner does not satisfy canonical selection criteria: "
                    + name
                )

        status = str(
            self.pilot_status
        ).strip().upper()

        if status not in PILOT_STATUSES:
            raise ValidationEvidenceError(
                "invalid pilot_status"
            )

        _safe_mapping(
            self.metadata
        )


@dataclass(frozen=True)
class DiscoveryGateResult:
    state: str
    interview_count: int
    material_problem_count: int
    material_problem_rate: float
    commitment_count: int
    active_pilot_count: int
    checks: dict[str, bool]
    unmet: tuple[str, ...]
    evidence_digest: str
    gate: str = (
        "DISCOVERY_DESIGN_PARTNER_GATE"
    )


class ProductMarketValidationRegistry:
    def __init__(self) -> None:
        self._interviews: dict[
            str,
            DiscoveryInterview,
        ] = {}

        self._commitments: dict[
            str,
            DesignPartnerCommitment,
        ] = {}

        self._merchant_commitment: dict[
            str,
            str,
        ] = {}

    def record_interview(
        self,
        interview: DiscoveryInterview,
    ) -> dict[str, Any]:
        interview.validate()

        normalized = replace(
            interview,
            merchant_ref=_merchant_ref(
                interview.merchant_ref
            ),
            conducted_at=_time(
                interview.conducted_at
            ),
            products=_products(
                interview.products
            ),
            evidence_ref=_evidence_ref(
                interview.evidence_ref
            ),
            metadata=dict(
                interview.metadata
            ),
        )

        existing = self._interviews.get(
            normalized.interview_id
        )

        if existing is not None:
            if existing != normalized:
                raise ValidationEvidenceError(
                    "interview_id already exists with different evidence"
                )

            return {
                "created": False,
                "interview": existing,
            }

        self._interviews[
            normalized.interview_id
        ] = normalized

        return {
            "created": True,
            "interview": normalized,
        }

    def record_commitment(
        self,
        commitment: DesignPartnerCommitment,
    ) -> dict[str, Any]:
        commitment.validate()

        normalized = replace(
            commitment,
            merchant_ref=_merchant_ref(
                commitment.merchant_ref
            ),
            products=_products(
                commitment.products
            ),
            committed_at=_time(
                commitment.committed_at
            ),
            pilot_status=str(
                commitment.pilot_status
            ).strip().upper(),
            evidence_ref=_evidence_ref(
                commitment.evidence_ref
            ),
            metadata=dict(
                commitment.metadata
            ),
        )

        existing = self._commitments.get(
            normalized.commitment_id
        )

        if existing is not None:
            if existing != normalized:
                raise ValidationEvidenceError(
                    "commitment_id already exists with different evidence"
                )

            return {
                "created": False,
                "commitment": existing,
            }

        merchant_existing_id = (
            self._merchant_commitment.get(
                normalized.merchant_ref
            )
        )

        if merchant_existing_id is not None:
            raise ValidationEvidenceError(
                "merchant already has a design partner commitment"
            )

        self._commitments[
            normalized.commitment_id
        ] = normalized

        self._merchant_commitment[
            normalized.merchant_ref
        ] = normalized.commitment_id

        return {
            "created": True,
            "commitment": normalized,
        }

    def transition_pilot_status(
        self,
        *,
        commitment_id: str,
        target_status: str,
        changed_at: str,
        evidence_ref: str,
    ) -> DesignPartnerCommitment:
        commitment = (
            self._commitments.get(
                _text(
                    "commitment_id",
                    commitment_id,
                )
            )
        )

        if commitment is None:
            raise ValidationEvidenceError(
                "design partner commitment not found"
            )

        target = str(
            target_status
        ).strip().upper()

        if target not in PILOT_STATUSES:
            raise ValidationEvidenceError(
                "invalid target pilot status"
            )

        if (
            commitment.pilot_status
            == "WITHDRAWN"
        ):
            raise ValidationEvidenceError(
                "WITHDRAWN pilot status is terminal"
            )

        allowed = {
            "CANDIDATE": {
                "ACTIVE",
                "WITHDRAWN",
            },
            "ACTIVE": {
                "PAUSED",
                "WITHDRAWN",
            },
            "PAUSED": {
                "ACTIVE",
                "WITHDRAWN",
            },
        }

        if target not in allowed[
            commitment.pilot_status
        ]:
            raise ValidationEvidenceError(
                "invalid pilot status transition"
            )

        updated_metadata = dict(
            commitment.metadata
        )

        updated_metadata[
            "pilot_status_change"
        ] = {
            "changed_at": _time(
                changed_at
            ),
            "evidence_ref": _evidence_ref(
                evidence_ref
            ),
            "from_status": (
                commitment.pilot_status
            ),
            "to_status": target,
        }

        updated = replace(
            commitment,
            pilot_status=target,
            metadata=updated_metadata,
        )

        self._commitments[
            commitment.commitment_id
        ] = updated

        return updated

    def discovery_gate(
        self,
    ) -> DiscoveryGateResult:
        interviews = tuple(
            self._interviews.values()
        )
        commitments = tuple(
            self._commitments.values()
        )

        interview_count = len(
            interviews
        )

        material_count = sum(
            1
            for interview in interviews
            if interview.core_problem_material
        )

        material_rate = (
            material_count
            / interview_count
            if interview_count
            else 0.0
        )

        active_pilots = sum(
            1
            for commitment in commitments
            if commitment.pilot_status
            == "ACTIVE"
        )

        checks = {
            "interviews_min_20": (
                interview_count
                >= DISCOVERY_TARGET[
                    "interviews_min"
                ]
            ),
            "problem_confirmation_rate_80pct": (
                material_rate
                >= DISCOVERY_TARGET[
                    "problem_confirmation_rate_min"
                ]
            ),
            "commitments_min_5": (
                len(
                    commitments
                )
                >= DISCOVERY_TARGET[
                    "commitments_min"
                ]
            ),
            "active_pilots_min_3": (
                active_pilots
                >= DISCOVERY_TARGET[
                    "active_pilots_min"
                ]
            ),
        }

        unmet = tuple(
            key
            for key, passed in checks.items()
            if not passed
        )

        evidence_material = {
            "interviews": [
                asdict(
                    interview
                )
                for interview in sorted(
                    interviews,
                    key=lambda item: (
                        item.interview_id
                    ),
                )
            ],
            "commitments": [
                asdict(
                    commitment
                )
                for commitment in sorted(
                    commitments,
                    key=lambda item: (
                        item.commitment_id
                    ),
                )
            ],
        }

        digest = sha256(
            _canonical(
                evidence_material
            ).encode(
                "utf-8"
            )
        ).hexdigest()

        return DiscoveryGateResult(
            state=(
                "PASS"
                if not unmet
                else "PENDING"
            ),
            interview_count=(
                interview_count
            ),
            material_problem_count=(
                material_count
            ),
            material_problem_rate=(
                material_rate
            ),
            commitment_count=(
                len(
                    commitments
                )
            ),
            active_pilot_count=(
                active_pilots
            ),
            checks=checks,
            unmet=unmet,
            evidence_digest=(
                digest
            ),
        )

    @property
    def launch_cap(
        self,
    ) -> dict[str, int]:
        return dict(
            LAUNCH_CAP
        )
