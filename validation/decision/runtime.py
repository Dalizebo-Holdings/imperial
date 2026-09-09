from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Any


class PMFDecisionError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise PMFDecisionError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise PMFDecisionError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            _text("timestamp", value)
        )
    except ValueError as exc:
        raise PMFDecisionError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise PMFDecisionError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _nonnegative_int(
    name: str,
    value: Any,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise PMFDecisionError(
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


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


@dataclass(frozen=True)
class PublicMVP90DaySnapshot:
    snapshot_id: str
    period_start: str
    period_end: str

    activated_organizations: int
    monthly_transacting_organizations: int
    active_three_consecutive_months: int

    logo_start_count: int
    logo_churned_count: int

    first_transaction_eligible_organizations: int
    first_transaction_within_24h: int

    weekly_usage_eligible_organizations: int
    weekly_active_organizations: int

    payment_reconciliation_total: int
    payment_reconciliation_matches: int

    uptime_total_minutes: int
    uptime_available_minutes: int

    p95_core_api_latency_ms: int
    checkout_api_p95_ms: int

    paying_customers: int
    customer_references: int

    critical_tenant_isolation_defects: int
    backup_restore_test_passed: bool

    evidence_refs: tuple[str, ...]

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
            raise PMFDecisionError(
                "period_start must be before period_end"
            )

        if (
            end - start
            < timedelta(
                days=90
            )
        ):
            raise PMFDecisionError(
                "Public MVP evidence window must span at least 90 days"
            )

        fields = {
            name: value
            for name, value in asdict(
                self
            ).items()
            if name not in {
                "snapshot_id",
                "period_start",
                "period_end",
                "backup_restore_test_passed",
                "evidence_refs",
            }
        }

        for name, value in fields.items():
            _nonnegative_int(
                name,
                value,
            )

        relationships = (
            (
                "logo_churned_count",
                self.logo_churned_count,
                "logo_start_count",
                self.logo_start_count,
            ),
            (
                "first_transaction_within_24h",
                self.first_transaction_within_24h,
                "first_transaction_eligible_organizations",
                self.first_transaction_eligible_organizations,
            ),
            (
                "weekly_active_organizations",
                self.weekly_active_organizations,
                "weekly_usage_eligible_organizations",
                self.weekly_usage_eligible_organizations,
            ),
            (
                "payment_reconciliation_matches",
                self.payment_reconciliation_matches,
                "payment_reconciliation_total",
                self.payment_reconciliation_total,
            ),
            (
                "uptime_available_minutes",
                self.uptime_available_minutes,
                "uptime_total_minutes",
                self.uptime_total_minutes,
            ),
        )

        for (
            numerator_name,
            numerator,
            denominator_name,
            denominator,
        ) in relationships:
            if numerator > denominator:
                raise PMFDecisionError(
                    f"{numerator_name} may not exceed {denominator_name}"
                )

        if not isinstance(
            self.backup_restore_test_passed,
            bool,
        ):
            raise PMFDecisionError(
                "backup_restore_test_passed must be boolean"
            )

        if not self.evidence_refs:
            raise PMFDecisionError(
                "Public MVP snapshot requires evidence_refs"
            )


@dataclass(frozen=True)
class PublicMVPGateResult:
    state: str
    checks: dict[str, bool]
    rates: dict[str, float]
    unmet: tuple[str, ...]
    evidence_digest: str
    gate: str = "PUBLIC_MVP_FIRST_90_DAY_GATE"


@dataclass(frozen=True)
class GateProof:
    label: str
    state: str
    evidence_digest: str
    evidence_ref: str


@dataclass(frozen=True)
class Phase7DecisionResult:
    state: str
    checks: dict[str, bool]
    unmet: tuple[str, ...]
    evidence_digest: str
    ledger_head_digest: str
    next_phase: str | None
    gate: str = "PHASE_7_PMF_CLOSURE_GATE"


class PMFDecisionEngine:
    REQUIRED_PROOFS = {
        "discovery": "PASS",
        "pilot_exit": "PASS",
        "release_gate_1": "PASS",
        "release_gate_2": "PASS",
        "release_gate_3": "PASS",
        "operational_readiness": "EVIDENCE_AVAILABLE",
        "public_mvp_90d": "PASS",
    }

    @staticmethod
    def public_mvp_gate(
        snapshot: PublicMVP90DaySnapshot,
    ) -> PublicMVPGateResult:
        snapshot.validate()

        rates = {
            "monthly_logo_churn": _ratio(
                snapshot.logo_churned_count,
                snapshot.logo_start_count,
            ),
            "first_transaction_within_24h": _ratio(
                snapshot.first_transaction_within_24h,
                snapshot.first_transaction_eligible_organizations,
            ),
            "weekly_active_usage": _ratio(
                snapshot.weekly_active_organizations,
                snapshot.weekly_usage_eligible_organizations,
            ),
            "payment_reconciliation": _ratio(
                snapshot.payment_reconciliation_matches,
                snapshot.payment_reconciliation_total,
            ),
            "uptime": _ratio(
                snapshot.uptime_available_minutes,
                snapshot.uptime_total_minutes,
            ),
        }

        checks = {
            "activated_organizations_min_50": (
                snapshot.activated_organizations >= 50
            ),
            "monthly_transacting_organizations_min_30": (
                snapshot.monthly_transacting_organizations >= 30
            ),
            "active_three_consecutive_months_min_20": (
                snapshot.active_three_consecutive_months >= 20
            ),
            "monthly_logo_churn_lt_5pct": (
                snapshot.logo_start_count > 0
                and rates["monthly_logo_churn"] < 0.05
            ),
            "first_transaction_within_24h_30pct": (
                snapshot.first_transaction_eligible_organizations > 0
                and rates["first_transaction_within_24h"] >= 0.30
            ),
            "weekly_active_usage_60pct": (
                snapshot.weekly_usage_eligible_organizations > 0
                and rates["weekly_active_usage"] >= 0.60
            ),
            "payment_reconciliation_99_5pct": (
                snapshot.payment_reconciliation_total > 0
                and rates["payment_reconciliation"] >= 0.995
            ),
            "uptime_99_5pct": (
                snapshot.uptime_total_minutes > 0
                and rates["uptime"] >= 0.995
            ),
            "p95_core_api_latency_lt_500ms": (
                snapshot.p95_core_api_latency_ms < 500
            ),
            "checkout_api_p95_lt_1500ms": (
                snapshot.checkout_api_p95_ms < 1500
            ),
            "paying_customers_min_10": (
                snapshot.paying_customers >= 10
            ),
            "customer_references_min_3": (
                snapshot.customer_references >= 3
            ),
            "no_critical_tenant_isolation_defect": (
                snapshot.critical_tenant_isolation_defects == 0
            ),
            "successful_backup_restore_test": (
                snapshot.backup_restore_test_passed is True
            ),
        }

        unmet = tuple(
            key
            for key, passed in checks.items()
            if not passed
        )

        digest = sha256(
            _canonical({
                "snapshot": asdict(snapshot),
                "rates": rates,
                "checks": checks,
            }).encode("utf-8")
        ).hexdigest()

        return PublicMVPGateResult(
            state=(
                "PASS"
                if not unmet
                else "PENDING"
            ),
            checks=checks,
            rates=rates,
            unmet=unmet,
            evidence_digest=digest,
        )

    def phase7_decision(
        self,
        *,
        ledger: Any,
        proofs: tuple[GateProof, ...],
    ) -> Phase7DecisionResult:
        if not ledger.verify_chain():
            raise PMFDecisionError(
                "evidence ledger chain verification failed"
            )

        proof_map = {
            proof.label: proof
            for proof in proofs
        }

        if len(proof_map) != len(proofs):
            raise PMFDecisionError(
                "duplicate Phase 7 proof label"
            )

        checks: dict[str, bool] = {}

        for label, required_state in self.REQUIRED_PROOFS.items():
            proof = proof_map.get(label)

            if proof is None:
                checks[label] = False
                continue

            state_ok = (
                str(proof.state).strip().upper()
                == required_state
            )

            binding_ok = False

            try:
                ledger.require_digest_binding(
                    evidence_ref=proof.evidence_ref,
                    evidence_digest=proof.evidence_digest,
                )
                binding_ok = True
            except Exception:
                binding_ok = False

            checks[label] = (
                state_ok
                and binding_ok
            )

        unmet = tuple(
            label
            for label, passed in checks.items()
            if not passed
        )

        material = {
            "checks": checks,
            "proofs": [
                asdict(proof)
                for proof in sorted(
                    proofs,
                    key=lambda item: item.label,
                )
            ],
            "ledger_head_digest": ledger.head_digest,
        }

        digest = sha256(
            _canonical(material).encode("utf-8")
        ).hexdigest()

        complete = not unmet

        return Phase7DecisionResult(
            state=(
                "PHASE7_COMPLETE"
                if complete
                else "CONTINUE_VALIDATION"
            ),
            checks=checks,
            unmet=unmet,
            evidence_digest=digest,
            ledger_head_digest=ledger.head_digest,
            next_phase=(
                "Phase 8 — Platform Hardening"
                if complete
                else None
            ),
        )
