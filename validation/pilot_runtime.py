from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Any


PRODUCTS = {
    "COMMERCE",
    "POS",
}

ONBOARDING_STEP_ORDER = (
    "ORGANIZATION_CREATION",
    "STORE_SETUP",
    "BRANCH_SETUP",
    "STAFF",
    "PRODUCT_IMPORT",
    "INVENTORY_SETUP",
    "PAYMENT_SETUP",
    "TEST_SALE",
    "FIRST_LIVE_TRANSACTION",
)

EVENT_STATUSES = {
    "SUCCESS",
    "FAILED",
}

LAUNCH_CAP = {
    "organizations": 100,
    "pos_branches": 250,
    "monthly_orders": 10000,
}

GATE1_ATTESTATIONS = {
    "CORE_WORKFLOW_DEFINED",
    "KERNEL_BOUNDARIES_DOCUMENTED",
    "THREAT_MODEL_COMPLETED",
    "PAYMENT_ARCHITECTURE_DEFINED",
    "NO_UNRESOLVED_CRITICAL_REGULATORY_BLOCKER",
}

GATE2_ATTESTATIONS = {
    "END_TO_END_COMMERCE_FLOW",
    "END_TO_END_POS_FLOW",
    "TENANT_ISOLATION_TESTS",
    "PAYMENT_CONSISTENCY_TESTS",
    "INVENTORY_CONSISTENCY_TESTS",
    "MONITORING",
    "ROLLBACK_PROCEDURE",
    "BACKUP_RESTORE_TEST",
}

GATE3_ATTESTATIONS = {
    "SUPPORT_PROCESS",
    "RECOVERY_PROCEDURES",
    "NO_MATERIAL_TENANT_ISOLATION_DEFECT",
}

ALL_ATTESTATIONS = (
    GATE1_ATTESTATIONS
    | GATE2_ATTESTATIONS
    | GATE3_ATTESTATIONS
)

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


class PilotValidationError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise PilotValidationError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise PilotValidationError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            _text("timestamp", value)
        )
    except ValueError as exc:
        raise PilotValidationError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise PilotValidationError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _iso(value: str) -> str:
    return _time(value).isoformat()


def _merchant_ref(value: str) -> str:
    value = _text(
        "merchant_ref",
        value,
    )
    if not value.startswith(
        "merchant://"
    ):
        raise PilotValidationError(
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
        raise PilotValidationError(
            "evidence_ref must use evidence://"
        )
    return value


def _products(values: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        raise PilotValidationError(
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
        raise PilotValidationError(
            "unsupported products: "
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
                    raise PilotValidationError(
                        "metadata contains sensitive/direct-contact field"
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
        ).encode("utf-8")
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise PilotValidationError(
            "metadata must be JSON-compatible"
        ) from exc

    if len(encoded) > 8192:
        raise PilotValidationError(
            "metadata exceeds 8192 bytes"
        )

    walk(value)


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _nonnegative_int(
    name: str,
    value: Any,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise PilotValidationError(
            f"{name} must be an integer >= 0"
        )
    return value


def _ratio(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _required_steps(
    products: tuple[str, ...],
) -> tuple[str, ...]:
    products = _products(products)

    steps = [
        "ORGANIZATION_CREATION",
        "STORE_SETUP",
    ]

    if "POS" in products:
        steps.extend([
            "BRANCH_SETUP",
            "STAFF",
        ])

    steps.extend([
        "PRODUCT_IMPORT",
        "INVENTORY_SETUP",
        "PAYMENT_SETUP",
        "TEST_SALE",
        "FIRST_LIVE_TRANSACTION",
    ])

    return tuple(steps)


@dataclass(frozen=True)
class PilotOnboarding:
    onboarding_id: str
    commitment_id: str
    merchant_ref: str
    products: tuple[str, ...]
    started_at: str
    evidence_ref: str
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "onboarding_id",
            self.onboarding_id,
        )
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
        _iso(
            self.started_at
        )
        _evidence_ref(
            self.evidence_ref
        )
        _safe_mapping(
            self.metadata
        )


@dataclass(frozen=True)
class OnboardingEvent:
    event_id: str
    onboarding_id: str
    merchant_ref: str
    step: str
    status: str
    occurred_at: str
    evidence_ref: str
    failure_code: str | None = None
    training_required: bool = False
    support_intervention: bool = False
    metadata: dict[str, Any] | None = None

    def validate(self) -> None:
        for name, value in {
            "event_id": self.event_id,
            "onboarding_id": self.onboarding_id,
        }.items():
            _text(
                name,
                value,
            )

        _merchant_ref(
            self.merchant_ref
        )

        step = str(
            self.step
        ).strip().upper()

        if step not in ONBOARDING_STEP_ORDER:
            raise PilotValidationError(
                "invalid onboarding step"
            )

        status = str(
            self.status
        ).strip().upper()

        if status not in EVENT_STATUSES:
            raise PilotValidationError(
                "invalid onboarding event status"
            )

        _iso(
            self.occurred_at
        )
        _evidence_ref(
            self.evidence_ref
        )

        if (
            self.failure_code is not None
            and status != "FAILED"
        ):
            raise PilotValidationError(
                "failure_code is only valid for FAILED events"
            )

        if self.failure_code is not None:
            _text(
                "failure_code",
                self.failure_code,
            )

        for name, value in {
            "training_required": (
                self.training_required
            ),
            "support_intervention": (
                self.support_intervention
            ),
        }.items():
            if not isinstance(
                value,
                bool,
            ):
                raise PilotValidationError(
                    f"{name} must be boolean"
                )

        _safe_mapping(
            dict(
                self.metadata
                or {}
            )
        )


@dataclass(frozen=True)
class OnboardingSummary:
    onboarding_id: str
    merchant_ref: str
    products: tuple[str, ...]
    completed: bool
    required_steps: tuple[str, ...]
    successful_steps: tuple[str, ...]
    first_live_transaction_at: str | None
    setup_duration_seconds: int | None
    first_sale_within_24h: bool
    import_failure_count: int
    payment_setup_failure_count: int
    training_requirement_count: int
    support_intervention_count: int


@dataclass(frozen=True)
class PilotMetricSnapshot:
    snapshot_id: str
    period_start: str
    period_end: str
    evidence_ref: str

    weekly_active_merchants: int
    orders_total: int
    orders_correct_final_state: int

    pos_transactions: int
    commerce_transactions: int
    active_branches: int
    active_pos_locations: int

    checkout_attempts: int
    successful_checkouts: int

    payment_reconciliation_total: int
    payment_reconciliation_matches: int

    inventory_checks: int
    inventory_accurate_checks: int

    api_requests: int
    api_errors: int

    paying_merchants: int
    trial_merchants: int
    trial_to_paid_merchants: int
    mrr_minor: int

    logo_start_count: int
    logo_churned_count: int

    merchants_willing_to_continue: int
    merchants_willing_to_pay: int

    support_tickets: int
    engineering_interventions: int

    critical_cross_tenant_defects: int
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "snapshot_id",
            self.snapshot_id,
        )
        start = _time(
            self.period_start
        )
        end = _time(
            self.period_end
        )
        if start >= end:
            raise PilotValidationError(
                "metric period_start must be before period_end"
            )

        _evidence_ref(
            self.evidence_ref
        )
        _safe_mapping(
            self.metadata
        )

        counter_fields = {
            name: value
            for name, value in asdict(
                self
            ).items()
            if name not in {
                "snapshot_id",
                "period_start",
                "period_end",
                "evidence_ref",
                "metadata",
            }
        }

        for name, value in counter_fields.items():
            _nonnegative_int(
                name,
                value,
            )

        relationships = (
            (
                "orders_correct_final_state",
                self.orders_correct_final_state,
                "orders_total",
                self.orders_total,
            ),
            (
                "successful_checkouts",
                self.successful_checkouts,
                "checkout_attempts",
                self.checkout_attempts,
            ),
            (
                "payment_reconciliation_matches",
                self.payment_reconciliation_matches,
                "payment_reconciliation_total",
                self.payment_reconciliation_total,
            ),
            (
                "inventory_accurate_checks",
                self.inventory_accurate_checks,
                "inventory_checks",
                self.inventory_checks,
            ),
            (
                "api_errors",
                self.api_errors,
                "api_requests",
                self.api_requests,
            ),
            (
                "trial_to_paid_merchants",
                self.trial_to_paid_merchants,
                "trial_merchants",
                self.trial_merchants,
            ),
            (
                "logo_churned_count",
                self.logo_churned_count,
                "logo_start_count",
                self.logo_start_count,
            ),
        )

        for (
            numerator_name,
            numerator,
            denominator_name,
            denominator,
        ) in relationships:
            if numerator > denominator:
                raise PilotValidationError(
                    f"{numerator_name} may not exceed {denominator_name}"
                )


@dataclass(frozen=True)
class CapacitySnapshot:
    snapshot_id: str
    observed_at: str
    organizations: int
    pos_branches: int
    monthly_orders: int
    evidence_ref: str

    def validate(self) -> None:
        _text(
            "snapshot_id",
            self.snapshot_id,
        )
        _iso(
            self.observed_at
        )
        _evidence_ref(
            self.evidence_ref
        )
        for name, value in {
            "organizations": (
                self.organizations
            ),
            "pos_branches": (
                self.pos_branches
            ),
            "monthly_orders": (
                self.monthly_orders
            ),
        }.items():
            _nonnegative_int(
                name,
                value,
            )


@dataclass(frozen=True)
class TechnicalAttestation:
    attestation_id: str
    requirement: str
    satisfied: bool
    observed_at: str
    evidence_ref: str
    valid_until: str | None
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "attestation_id",
            self.attestation_id,
        )

        requirement = str(
            self.requirement
        ).strip().upper()

        if requirement not in ALL_ATTESTATIONS:
            raise PilotValidationError(
                "unsupported release-gate requirement"
            )

        if not isinstance(
            self.satisfied,
            bool,
        ):
            raise PilotValidationError(
                "satisfied must be boolean"
            )

        observed = _time(
            self.observed_at
        )
        _evidence_ref(
            self.evidence_ref
        )

        if self.valid_until is not None:
            valid_until = _time(
                self.valid_until
            )
            if valid_until < observed:
                raise PilotValidationError(
                    "valid_until precedes observed_at"
                )

        _safe_mapping(
            self.metadata
        )


@dataclass(frozen=True)
class GateResult:
    gate: str
    state: str
    checks: dict[str, bool]
    unmet: tuple[str, ...]
    evidence_digest: str


@dataclass(frozen=True)
class PilotExitResult:
    state: str
    completed_onboardings: int
    first_sale_within_24h_count: int
    rates: dict[str, float]
    checks: dict[str, bool]
    unmet: tuple[str, ...]
    evidence_digest: str
    gate: str = "PILOT_EXIT_GATE"


@dataclass(frozen=True)
class CapacityResult:
    state: str
    checks: dict[str, bool]
    exceeded: tuple[str, ...]
    evidence_digest: str
    gate: str = "CONTROLLED_CAPACITY_GATE"


class PilotValidationRegistry:
    def __init__(self) -> None:
        self._onboardings: dict[
            str,
            PilotOnboarding,
        ] = {}
        self._merchant_onboarding: dict[
            str,
            str,
        ] = {}
        self._events: dict[
            str,
            OnboardingEvent,
        ] = {}
        self._events_by_onboarding: dict[
            str,
            list[str],
        ] = {}
        self._metric_snapshots: dict[
            str,
            PilotMetricSnapshot,
        ] = {}
        self._capacity_snapshots: dict[
            str,
            CapacitySnapshot,
        ] = {}
        self._attestations: dict[
            str,
            TechnicalAttestation,
        ] = {}
        self._attestation_by_requirement: dict[
            str,
            str,
        ] = {}

    def start_onboarding(
        self,
        *,
        commitment: Any,
        onboarding: PilotOnboarding,
    ) -> dict[str, Any]:
        onboarding.validate()

        commitment_id = _text(
            "commitment.commitment_id",
            getattr(
                commitment,
                "commitment_id",
                None,
            ),
        )
        merchant_ref = _merchant_ref(
            getattr(
                commitment,
                "merchant_ref",
                "",
            )
        )
        commitment_products = set(
            _products(
                tuple(
                    getattr(
                        commitment,
                        "products",
                        (),
                    )
                )
            )
        )
        pilot_status = str(
            getattr(
                commitment,
                "pilot_status",
                "",
            )
        ).strip().upper()

        if pilot_status != "ACTIVE":
            raise PilotValidationError(
                "pilot onboarding requires ACTIVE design partner"
            )

        if (
            commitment_id
            != onboarding.commitment_id
        ):
            raise PilotValidationError(
                "onboarding commitment_id mismatch"
            )

        if (
            merchant_ref
            != onboarding.merchant_ref
        ):
            raise PilotValidationError(
                "onboarding merchant_ref mismatch"
            )

        if not set(
            onboarding.products
        ).issubset(
            commitment_products
        ):
            raise PilotValidationError(
                "onboarding products exceed committed products"
            )

        existing = self._onboardings.get(
            onboarding.onboarding_id
        )

        normalized = replace(
            onboarding,
            merchant_ref=_merchant_ref(
                onboarding.merchant_ref
            ),
            products=_products(
                onboarding.products
            ),
            started_at=_iso(
                onboarding.started_at
            ),
            evidence_ref=_evidence_ref(
                onboarding.evidence_ref
            ),
            metadata=dict(
                onboarding.metadata
            ),
        )

        if existing is not None:
            if existing != normalized:
                raise PilotValidationError(
                    "onboarding_id already exists with different evidence"
                )
            return {
                "created": False,
                "onboarding": existing,
            }

        merchant_existing = (
            self._merchant_onboarding.get(
                normalized.merchant_ref
            )
        )
        if merchant_existing is not None:
            raise PilotValidationError(
                "merchant already has a pilot onboarding"
            )

        self._onboardings[
            normalized.onboarding_id
        ] = normalized
        self._merchant_onboarding[
            normalized.merchant_ref
        ] = normalized.onboarding_id
        self._events_by_onboarding[
            normalized.onboarding_id
        ] = []

        return {
            "created": True,
            "onboarding": normalized,
        }

    def record_onboarding_event(
        self,
        event: OnboardingEvent,
    ) -> dict[str, Any]:
        event.validate()

        onboarding = self._onboardings.get(
            event.onboarding_id
        )
        if onboarding is None:
            raise PilotValidationError(
                "onboarding not found"
            )

        if (
            onboarding.merchant_ref
            != event.merchant_ref
        ):
            raise PilotValidationError(
                "onboarding event merchant mismatch"
            )

        occurred = _time(
            event.occurred_at
        )
        started = _time(
            onboarding.started_at
        )

        if occurred < started:
            raise PilotValidationError(
                "onboarding event predates onboarding start"
            )

        step = str(
            event.step
        ).strip().upper()
        status = str(
            event.status
        ).strip().upper()

        required = _required_steps(
            onboarding.products
        )
        if step not in required:
            raise PilotValidationError(
                "onboarding step is not applicable to pilot products"
            )

        successful_steps = {
            item.step
            for item in self._events_for(
                onboarding.onboarding_id
            )
            if item.status == "SUCCESS"
        }

        step_index = required.index(
            step
        )

        missing_prior = [
            prior
            for prior in required[
                :step_index
            ]
            if prior not in successful_steps
        ]

        if missing_prior:
            raise PilotValidationError(
                "onboarding event has incomplete prerequisite steps: "
                + ", ".join(
                    missing_prior
                )
            )

        existing = self._events.get(
            event.event_id
        )

        normalized = replace(
            event,
            merchant_ref=_merchant_ref(
                event.merchant_ref
            ),
            step=step,
            status=status,
            occurred_at=occurred.isoformat(),
            evidence_ref=_evidence_ref(
                event.evidence_ref
            ),
            metadata=dict(
                event.metadata
                or {}
            ),
        )

        if existing is not None:
            if existing != normalized:
                raise PilotValidationError(
                    "event_id already exists with different evidence"
                )
            return {
                "created": False,
                "event": existing,
            }

        if (
            status == "SUCCESS"
            and step in successful_steps
        ):
            raise PilotValidationError(
                "onboarding step already succeeded"
            )

        self._events[
            normalized.event_id
        ] = normalized
        self._events_by_onboarding[
            normalized.onboarding_id
        ].append(
            normalized.event_id
        )

        return {
            "created": True,
            "event": normalized,
        }

    def onboarding_summary(
        self,
        onboarding_id: str,
    ) -> OnboardingSummary:
        onboarding = self._onboardings.get(
            _text(
                "onboarding_id",
                onboarding_id,
            )
        )
        if onboarding is None:
            raise PilotValidationError(
                "onboarding not found"
            )

        events = self._events_for(
            onboarding.onboarding_id
        )
        required = _required_steps(
            onboarding.products
        )

        successful = {
            event.step: event
            for event in events
            if event.status == "SUCCESS"
        }

        completed = all(
            step in successful
            for step in required
        )

        first_sale_event = successful.get(
            "FIRST_LIVE_TRANSACTION"
        )

        setup_duration_seconds = None
        first_sale_within_24h = False
        first_sale_at = None

        if first_sale_event is not None:
            started = _time(
                onboarding.started_at
            )
            first_sale = _time(
                first_sale_event.occurred_at
            )
            delta = (
                first_sale
                - started
            )
            setup_duration_seconds = int(
                delta.total_seconds()
            )
            first_sale_within_24h = (
                delta
                <= timedelta(
                    hours=24
                )
            )
            first_sale_at = (
                first_sale.isoformat()
            )

        return OnboardingSummary(
            onboarding_id=(
                onboarding.onboarding_id
            ),
            merchant_ref=(
                onboarding.merchant_ref
            ),
            products=(
                onboarding.products
            ),
            completed=completed,
            required_steps=required,
            successful_steps=tuple(
                step
                for step in required
                if step in successful
            ),
            first_live_transaction_at=(
                first_sale_at
            ),
            setup_duration_seconds=(
                setup_duration_seconds
            ),
            first_sale_within_24h=(
                first_sale_within_24h
            ),
            import_failure_count=sum(
                1
                for event in events
                if (
                    event.step
                    == "PRODUCT_IMPORT"
                    and event.status
                    == "FAILED"
                )
            ),
            payment_setup_failure_count=sum(
                1
                for event in events
                if (
                    event.step
                    == "PAYMENT_SETUP"
                    and event.status
                    == "FAILED"
                )
            ),
            training_requirement_count=sum(
                1
                for event in events
                if event.training_required
            ),
            support_intervention_count=sum(
                1
                for event in events
                if event.support_intervention
            ),
        )

    def record_metric_snapshot(
        self,
        snapshot: PilotMetricSnapshot,
    ) -> dict[str, Any]:
        snapshot.validate()

        normalized = replace(
            snapshot,
            period_start=_time(
                snapshot.period_start
            ).isoformat(),
            period_end=_time(
                snapshot.period_end
            ).isoformat(),
            evidence_ref=_evidence_ref(
                snapshot.evidence_ref
            ),
            metadata=dict(
                snapshot.metadata
            ),
        )

        existing = self._metric_snapshots.get(
            normalized.snapshot_id
        )

        if existing is not None:
            if existing != normalized:
                raise PilotValidationError(
                    "snapshot_id already exists with different metrics"
                )
            return {
                "created": False,
                "snapshot": existing,
            }

        self._metric_snapshots[
            normalized.snapshot_id
        ] = normalized

        return {
            "created": True,
            "snapshot": normalized,
        }

    def record_capacity_snapshot(
        self,
        snapshot: CapacitySnapshot,
    ) -> dict[str, Any]:
        snapshot.validate()

        normalized = replace(
            snapshot,
            observed_at=_iso(
                snapshot.observed_at
            ),
            evidence_ref=_evidence_ref(
                snapshot.evidence_ref
            ),
        )

        existing = self._capacity_snapshots.get(
            normalized.snapshot_id
        )

        if existing is not None:
            if existing != normalized:
                raise PilotValidationError(
                    "capacity snapshot ID conflict"
                )
            return {
                "created": False,
                "snapshot": existing,
            }

        self._capacity_snapshots[
            normalized.snapshot_id
        ] = normalized

        return {
            "created": True,
            "snapshot": normalized,
        }

    def capacity_gate(
        self,
        snapshot_id: str,
    ) -> CapacityResult:
        snapshot = (
            self._capacity_snapshots.get(
                _text(
                    "snapshot_id",
                    snapshot_id,
                )
            )
        )
        if snapshot is None:
            raise PilotValidationError(
                "capacity snapshot not found"
            )

        checks = {
            "organizations_within_cap": (
                snapshot.organizations
                <= LAUNCH_CAP[
                    "organizations"
                ]
            ),
            "pos_branches_within_cap": (
                snapshot.pos_branches
                <= LAUNCH_CAP[
                    "pos_branches"
                ]
            ),
            "monthly_orders_within_cap": (
                snapshot.monthly_orders
                <= LAUNCH_CAP[
                    "monthly_orders"
                ]
            ),
        }

        exceeded = tuple(
            key
            for key, passed in checks.items()
            if not passed
        )

        digest = sha256(
            _canonical(
                asdict(
                    snapshot
                )
            ).encode(
                "utf-8"
            )
        ).hexdigest()

        return CapacityResult(
            state=(
                "PASS"
                if not exceeded
                else "VIOLATION"
            ),
            checks=checks,
            exceeded=exceeded,
            evidence_digest=digest,
        )

    def record_attestation(
        self,
        attestation: TechnicalAttestation,
    ) -> dict[str, Any]:
        attestation.validate()

        normalized = replace(
            attestation,
            requirement=str(
                attestation.requirement
            ).strip().upper(),
            observed_at=_iso(
                attestation.observed_at
            ),
            evidence_ref=_evidence_ref(
                attestation.evidence_ref
            ),
            valid_until=(
                None
                if attestation.valid_until
                is None
                else _iso(
                    attestation.valid_until
                )
            ),
            metadata=dict(
                attestation.metadata
            ),
        )

        existing = self._attestations.get(
            normalized.attestation_id
        )
        if existing is not None:
            if existing != normalized:
                raise PilotValidationError(
                    "attestation_id already exists with different evidence"
                )
            return {
                "created": False,
                "attestation": existing,
            }

        prior_id = (
            self._attestation_by_requirement.get(
                normalized.requirement
            )
        )

        if prior_id is not None:
            prior = self._attestations[
                prior_id
            ]
            if _time(
                normalized.observed_at
            ) <= _time(
                prior.observed_at
            ):
                raise PilotValidationError(
                    "new attestation must be newer than current requirement evidence"
                )

        self._attestations[
            normalized.attestation_id
        ] = normalized
        self._attestation_by_requirement[
            normalized.requirement
        ] = normalized.attestation_id

        return {
            "created": True,
            "attestation": normalized,
        }

    def pilot_exit_gate(
        self,
        snapshot_id: str,
    ) -> PilotExitResult:
        snapshot = (
            self._metric_snapshots.get(
                _text(
                    "snapshot_id",
                    snapshot_id,
                )
            )
        )
        if snapshot is None:
            raise PilotValidationError(
                "metric snapshot not found"
            )

        window = (
            _time(
                snapshot.period_end
            )
            - _time(
                snapshot.period_start
            )
        )

        summaries = tuple(
            self.onboarding_summary(
                onboarding_id
            )
            for onboarding_id
            in sorted(
                self._onboardings
            )
        )

        completed = tuple(
            summary
            for summary in summaries
            if summary.completed
        )

        completed_count = len(
            completed
        )

        within_24h = sum(
            1
            for summary in completed
            if summary.first_sale_within_24h
        )

        if (
            snapshot.weekly_active_merchants
            > completed_count
        ):
            raise PilotValidationError(
                "weekly_active_merchants exceeds completed onboardings"
            )

        if (
            snapshot.merchants_willing_to_continue
            > completed_count
            or snapshot.merchants_willing_to_pay
            > completed_count
            or snapshot.paying_merchants
            > completed_count
        ):
            raise PilotValidationError(
                "merchant commercial counters exceed completed onboardings"
            )

        rates = {
            "weekly_transact_rate": _ratio(
                snapshot.weekly_active_merchants,
                completed_count,
            ),
            "first_sale_within_24h_rate": _ratio(
                within_24h,
                completed_count,
            ),
            "correct_order_state_rate": _ratio(
                snapshot.orders_correct_final_state,
                snapshot.orders_total,
            ),
            "payment_reconciliation_rate": _ratio(
                snapshot.payment_reconciliation_matches,
                snapshot.payment_reconciliation_total,
            ),
            "inventory_accuracy_rate": _ratio(
                snapshot.inventory_accurate_checks,
                snapshot.inventory_checks,
            ),
            "checkout_success_rate": _ratio(
                snapshot.successful_checkouts,
                snapshot.checkout_attempts,
            ),
            "api_error_rate": _ratio(
                snapshot.api_errors,
                snapshot.api_requests,
            ),
            "trial_to_paid_rate": _ratio(
                snapshot.trial_to_paid_merchants,
                snapshot.trial_merchants,
            ),
            "logo_churn_rate": _ratio(
                snapshot.logo_churned_count,
                snapshot.logo_start_count,
            ),
        }

        checks = {
            "measurement_window_at_least_7_days": (
                window
                >= timedelta(
                    days=7
                )
            ),
            "onboarded_merchants_min_5": (
                completed_count >= 5
            ),
            "weekly_transact_rate_70pct": (
                rates[
                    "weekly_transact_rate"
                ]
                >= 0.70
            ),
            "first_sale_within_24h_80pct": (
                rates[
                    "first_sale_within_24h_rate"
                ]
                >= 0.80
            ),
            "correct_order_state_90pct": (
                rates[
                    "correct_order_state_rate"
                ]
                >= 0.90
            ),
            "payment_reconciliation_99_5pct": (
                rates[
                    "payment_reconciliation_rate"
                ]
                >= 0.995
            ),
            "inventory_accuracy_98pct": (
                rates[
                    "inventory_accuracy_rate"
                ]
                >= 0.98
            ),
            "want_to_continue_min_3": (
                snapshot.merchants_willing_to_continue
                >= 3
            ),
            "willing_to_pay_min_2": (
                snapshot.merchants_willing_to_pay
                >= 2
            ),
            "no_critical_cross_tenant_exposure": (
                snapshot.critical_cross_tenant_defects
                == 0
            ),
        }

        unmet = tuple(
            key
            for key, passed in checks.items()
            if not passed
        )

        material = {
            "snapshot": asdict(
                snapshot
            ),
            "onboarding_summaries": [
                asdict(
                    summary
                )
                for summary in completed
            ],
        }

        return PilotExitResult(
            state=(
                "PASS"
                if not unmet
                else "PENDING"
            ),
            completed_onboardings=(
                completed_count
            ),
            first_sale_within_24h_count=(
                within_24h
            ),
            rates=rates,
            checks=checks,
            unmet=unmet,
            evidence_digest=sha256(
                _canonical(
                    material
                ).encode(
                    "utf-8"
                )
            ).hexdigest(),
        )

    def release_gate_1(
        self,
        *,
        discovery_gate: Any,
        evaluated_at: str,
    ) -> GateResult:
        checks = {
            "problem_validation": (
                str(
                    getattr(
                        discovery_gate,
                        "state",
                        "",
                    )
                ).strip().upper()
                == "PASS"
                and float(
                    getattr(
                        discovery_gate,
                        "material_problem_rate",
                        0.0,
                    )
                )
                >= 0.80
            ),
            "design_partners": (
                int(
                    getattr(
                        discovery_gate,
                        "commitment_count",
                        0,
                    )
                )
                >= 5
            ),
        }

        checks.update(
            self._attestation_checks(
                GATE1_ATTESTATIONS,
                evaluated_at=evaluated_at,
            )
        )

        return self._gate_result(
            "GATE_1_DISCOVERY_TO_ALPHA",
            checks,
        )

    def release_gate_2(
        self,
        *,
        evaluated_at: str,
    ) -> GateResult:
        checks = self._attestation_checks(
            GATE2_ATTESTATIONS,
            evaluated_at=evaluated_at,
        )

        return self._gate_result(
            "GATE_2_ALPHA_TO_PILOT",
            checks,
        )

    def release_gate_3(
        self,
        *,
        snapshot_id: str,
        capacity_snapshot_id: str,
        evaluated_at: str,
    ) -> GateResult:
        pilot = self.pilot_exit_gate(
            snapshot_id
        )
        capacity = self.capacity_gate(
            capacity_snapshot_id
        )
        snapshot = self._metric_snapshots[
            snapshot_id
        ]

        checks = {
            "real_transactions": (
                snapshot.orders_total > 0
            ),
            "stable_reconciliation": (
                pilot.rates[
                    "payment_reconciliation_rate"
                ]
                >= 0.995
            ),
            "repeatable_onboarding": (
                pilot.completed_onboardings >= 5
                and pilot.rates[
                    "first_sale_within_24h_rate"
                ]
                >= 0.80
            ),
            "willing_to_pay_min_2": (
                snapshot.merchants_willing_to_pay
                >= 2
            ),
            "no_critical_cross_tenant_metric": (
                snapshot.critical_cross_tenant_defects
                == 0
            ),
            "controlled_capacity": (
                capacity.state
                == "PASS"
            ),
        }

        checks.update(
            self._attestation_checks(
                GATE3_ATTESTATIONS,
                evaluated_at=evaluated_at,
            )
        )

        return self._gate_result(
            "GATE_3_PILOT_TO_PUBLIC_MVP",
            checks,
        )

    def _events_for(
        self,
        onboarding_id: str,
    ) -> tuple[
        OnboardingEvent,
        ...
    ]:
        return tuple(
            self._events[
                event_id
            ]
            for event_id
            in self._events_by_onboarding.get(
                onboarding_id,
                []
            )
        )

    def _attestation_checks(
        self,
        requirements: set[str],
        *,
        evaluated_at: str,
    ) -> dict[str, bool]:
        as_of = _time(
            evaluated_at
        )
        checks: dict[
            str,
            bool,
        ] = {}

        for requirement in sorted(
            requirements
        ):
            attestation_id = (
                self._attestation_by_requirement.get(
                    requirement
                )
            )
            if attestation_id is None:
                checks[
                    requirement.lower()
                ] = False
                continue

            attestation = self._attestations[
                attestation_id
            ]
            valid = (
                attestation.satisfied
                is True
            )

            if (
                attestation.valid_until
                is not None
                and _time(
                    attestation.valid_until
                )
                < as_of
            ):
                valid = False

            checks[
                requirement.lower()
            ] = valid

        return checks

    @staticmethod
    def _gate_result(
        gate: str,
        checks: dict[str, bool],
    ) -> GateResult:
        unmet = tuple(
            key
            for key, passed in checks.items()
            if not passed
        )
        digest = sha256(
            _canonical(
                checks
            ).encode(
                "utf-8"
            )
        ).hexdigest()

        return GateResult(
            gate=gate,
            state=(
                "PASS"
                if not unmet
                else "PENDING"
            ),
            checks=checks,
            unmet=unmet,
            evidence_digest=digest,
        )
