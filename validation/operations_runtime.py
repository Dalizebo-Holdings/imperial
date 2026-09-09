from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from hashlib import sha256
import json
import re
from typing import Any


FEEDBACK_CATEGORIES = {
    "ONBOARDING",
    "COMMERCE",
    "POS",
    "INVENTORY",
    "PAYMENTS",
    "REPORTING",
    "PERFORMANCE",
    "RELIABILITY",
    "SUPPORT",
    "PRICING",
}

SEVERITIES = {
    "P0",
    "P1",
    "P2",
    "P3",
}

PRODUCT_DECISIONS = {
    "PENDING",
    "INVESTIGATE",
    "PLANNED",
    "DECLINED",
    "DELIVERED",
}

SUPPORT_STATES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
}

INCIDENT_STATES = {
    "OPEN",
    "MITIGATED",
    "RESOLVED",
}

PRODUCTS = {
    "COMMERCE",
    "POS",
    "PLATFORM",
}

SENSITIVE_KEY_TERMS = {
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

SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    re.compile(r"(?i)\b(?:password|secret|api[_ -]?key|bearer token)\s*[:=]"),
)


class OperationalEvidenceError(ValueError):
    pass


def _text(
    name: str,
    value: Any,
    *,
    max_length: int = 2048,
) -> str:
    if value is None:
        raise OperationalEvidenceError(
            f"{name} must not be empty"
        )

    result = str(value).strip()

    if not result:
        raise OperationalEvidenceError(
            f"{name} must not be empty"
        )

    if len(result) > max_length:
        raise OperationalEvidenceError(
            f"{name} exceeds {max_length} characters"
        )

    for pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern.search(result):
            raise OperationalEvidenceError(
                f"{name} appears to contain sensitive credential/payment material"
            )

    return result


def _optional_text(
    name: str,
    value: str | None,
    *,
    max_length: int = 2048,
) -> str | None:
    if value is None:
        return None
    return _text(
        name,
        value,
        max_length=max_length,
    )


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            _text(
                "timestamp",
                value,
                max_length=128,
            )
        )
    except ValueError as exc:
        raise OperationalEvidenceError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise OperationalEvidenceError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _iso(value: str) -> str:
    return _time(value).isoformat()


def _merchant_ref(value: str) -> str:
    result = _text(
        "merchant_ref",
        value,
        max_length=256,
    )
    if not result.startswith(
        "merchant://"
    ):
        raise OperationalEvidenceError(
            "merchant_ref must use merchant://"
        )
    return result


def _org_ref(value: str) -> str:
    result = _text(
        "organization_ref",
        value,
        max_length=256,
    )
    if not result.startswith(
        "organization://"
    ):
        raise OperationalEvidenceError(
            "organization reference must use organization://"
        )
    return result


def _owner_ref(value: str) -> str:
    result = _text(
        "owner_ref",
        value,
        max_length=256,
    )
    if not (
        result.startswith(
            "user://"
        )
        or result.startswith(
            "service://"
        )
    ):
        raise OperationalEvidenceError(
            "owner_ref must use user:// or service://"
        )
    return result


def _evidence_ref(value: str) -> str:
    result = _text(
        "evidence_ref",
        value,
        max_length=512,
    )
    if not result.startswith(
        "evidence://"
    ):
        raise OperationalEvidenceError(
            "evidence_ref must use evidence://"
        )
    return result


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
                    for term in SENSITIVE_KEY_TERMS
                ):
                    raise OperationalEvidenceError(
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

        elif isinstance(
            item,
            str,
        ):
            _text(
                "metadata text",
                item,
                max_length=2048,
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
        raise OperationalEvidenceError(
            "metadata must be JSON-compatible"
        ) from exc

    if len(
        encoded
    ) > 8192:
        raise OperationalEvidenceError(
            "metadata exceeds 8192 bytes"
        )

    walk(
        value
    )


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _digest(value: Any) -> str:
    return sha256(
        _canonical(
            value
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def _business_day_deadline(
    opened_at: datetime,
) -> datetime:
    deadline = opened_at

    while True:
        deadline = (
            deadline
            + timedelta(
                days=1
            )
        )
        if deadline.weekday() < 5:
            return deadline


@dataclass(frozen=True)
class MerchantFeedback:
    feedback_id: str
    merchant_ref: str
    category: str
    problem: str
    frequency: int
    severity: str
    business_impact: str
    requested_outcome: str
    existing_workaround: str
    product_decision: str
    recorded_at: str
    evidence_ref: str
    metadata: dict[str, Any]

    def validate(self) -> None:
        _text(
            "feedback_id",
            self.feedback_id,
            max_length=128,
        )
        _merchant_ref(
            self.merchant_ref
        )

        if (
            str(
                self.category
            ).strip().upper()
            not in FEEDBACK_CATEGORIES
        ):
            raise OperationalEvidenceError(
                "unsupported feedback category"
            )

        _text(
            "problem",
            self.problem,
        )

        if (
            not isinstance(
                self.frequency,
                int,
            )
            or isinstance(
                self.frequency,
                bool,
            )
            or self.frequency <= 0
        ):
            raise OperationalEvidenceError(
                "feedback frequency must be an integer > 0"
            )

        if (
            str(
                self.severity
            ).strip().upper()
            not in SEVERITIES
        ):
            raise OperationalEvidenceError(
                "feedback severity must be P0/P1/P2/P3"
            )

        for name, value in {
            "business_impact": (
                self.business_impact
            ),
            "requested_outcome": (
                self.requested_outcome
            ),
            "existing_workaround": (
                self.existing_workaround
            ),
        }.items():
            _text(
                name,
                value,
            )

        if (
            str(
                self.product_decision
            ).strip().upper()
            not in PRODUCT_DECISIONS
        ):
            raise OperationalEvidenceError(
                "invalid product decision"
            )

        _iso(
            self.recorded_at
        )
        _evidence_ref(
            self.evidence_ref
        )
        _safe_mapping(
            self.metadata
        )


@dataclass(frozen=True)
class SupportTicket:
    ticket_id: str
    merchant_ref: str
    organization_id: str
    severity: str
    product: str
    environment_id: str
    description: str
    correlation_id: str
    owner_ref: str
    opened_at: str
    evidence_ref: str
    state: str = "OPEN"
    first_response_at: str | None = None
    first_response_evidence_ref: str | None = None
    resolution: str | None = None
    resolved_at: str | None = None
    resolution_evidence_ref: str | None = None
    metadata: dict[str, Any] | None = None

    def validate(self) -> None:
        _text(
            "ticket_id",
            self.ticket_id,
            max_length=128,
        )
        _merchant_ref(
            self.merchant_ref
        )
        _text(
            "organization_id",
            self.organization_id,
            max_length=256,
        )

        if (
            str(
                self.severity
            ).strip().upper()
            not in SEVERITIES
        ):
            raise OperationalEvidenceError(
                "support severity must be P0/P1/P2/P3"
            )

        if (
            str(
                self.product
            ).strip().upper()
            not in PRODUCTS
        ):
            raise OperationalEvidenceError(
                "support product must be COMMERCE/POS/PLATFORM"
            )

        _text(
            "environment_id",
            self.environment_id,
            max_length=256,
        )
        _text(
            "description",
            self.description,
        )
        _text(
            "correlation_id",
            self.correlation_id,
            max_length=256,
        )
        _owner_ref(
            self.owner_ref
        )
        _iso(
            self.opened_at
        )
        _evidence_ref(
            self.evidence_ref
        )

        state = str(
            self.state
        ).strip().upper()

        if state not in SUPPORT_STATES:
            raise OperationalEvidenceError(
                "invalid support ticket state"
            )

        if (
            self.first_response_at
            is None
        ) != (
            self.first_response_evidence_ref
            is None
        ):
            raise OperationalEvidenceError(
                "first response timestamp/evidence must be set together"
            )

        if self.first_response_at is not None:
            if _time(
                self.first_response_at
            ) < _time(
                self.opened_at
            ):
                raise OperationalEvidenceError(
                    "first response predates ticket"
                )
            _evidence_ref(
                self.first_response_evidence_ref
                or ""
            )

        if state == "RESOLVED":
            _text(
                "resolution",
                self.resolution,
            )
            if self.resolved_at is None:
                raise OperationalEvidenceError(
                    "resolved ticket requires resolved_at"
                )
            if _time(
                self.resolved_at
            ) < _time(
                self.opened_at
            ):
                raise OperationalEvidenceError(
                    "ticket resolution predates opening"
                )
            _evidence_ref(
                self.resolution_evidence_ref
                or ""
            )

        _safe_mapping(
            dict(
                self.metadata
                or {}
            )
        )


@dataclass(frozen=True)
class ProductionIncident:
    incident_id: str
    severity: str
    start_time: str
    detection_source: str
    owner_ref: str
    affected_tenants: tuple[str, ...]
    affected_services: tuple[str, ...]
    customer_impact: str
    tenant_isolation_impact: bool
    material_tenant_isolation_defect: bool
    creation_evidence_ref: str
    state: str = "OPEN"
    root_cause: str | None = None
    resolution: str | None = None
    recovery_validation: str | None = None
    corrective_actions: tuple[str, ...] = ()
    resolved_at: str | None = None
    resolution_evidence_ref: str | None = None
    metadata: dict[str, Any] | None = None

    def validate(self) -> None:
        _text(
            "incident_id",
            self.incident_id,
            max_length=128,
        )

        severity = str(
            self.severity
        ).strip().upper()

        if severity not in SEVERITIES:
            raise OperationalEvidenceError(
                "incident severity must be P0/P1/P2/P3"
            )

        _iso(
            self.start_time
        )
        _text(
            "detection_source",
            self.detection_source,
        )

        # Critical ownership is always mandatory.
        _owner_ref(
            self.owner_ref
        )

        if not self.affected_tenants:
            raise OperationalEvidenceError(
                "incident requires affected tenants"
            )

        for tenant in self.affected_tenants:
            _org_ref(
                tenant
            )

        if not self.affected_services:
            raise OperationalEvidenceError(
                "incident requires affected services"
            )

        for service in self.affected_services:
            _text(
                "affected_service",
                service,
                max_length=128,
            )

        _text(
            "customer_impact",
            self.customer_impact,
        )
        _evidence_ref(
            self.creation_evidence_ref
        )

        for name, value in {
            "tenant_isolation_impact": (
                self.tenant_isolation_impact
            ),
            "material_tenant_isolation_defect": (
                self.material_tenant_isolation_defect
            ),
        }.items():
            if not isinstance(
                value,
                bool,
            ):
                raise OperationalEvidenceError(
                    f"{name} must be boolean"
                )

        if (
            self.material_tenant_isolation_defect
            and not self.tenant_isolation_impact
        ):
            raise OperationalEvidenceError(
                "material tenant-isolation defect requires isolation impact"
            )

        state = str(
            self.state
        ).strip().upper()

        if state not in INCIDENT_STATES:
            raise OperationalEvidenceError(
                "invalid incident state"
            )

        if state == "RESOLVED":
            for name, value in {
                "root_cause": (
                    self.root_cause
                ),
                "resolution": (
                    self.resolution
                ),
                "recovery_validation": (
                    self.recovery_validation
                ),
            }.items():
                _text(
                    name,
                    value,
                )

            if not self.corrective_actions:
                raise OperationalEvidenceError(
                    "resolved incident requires corrective actions"
                )

            for action in self.corrective_actions:
                _text(
                    "corrective_action",
                    action,
                )

            if self.resolved_at is None:
                raise OperationalEvidenceError(
                    "resolved incident requires resolved_at"
                )

            if _time(
                self.resolved_at
            ) < _time(
                self.start_time
            ):
                raise OperationalEvidenceError(
                    "incident resolution predates start"
                )

            _evidence_ref(
                self.resolution_evidence_ref
                or ""
            )

        _safe_mapping(
            dict(
                self.metadata
                or {}
            )
        )


@dataclass(frozen=True)
class SupportSummary:
    ticket_count: int
    open_count: int
    resolved_count: int
    p0_count: int
    p1_count: int
    p1_responded_count: int
    p1_within_one_business_day_count: int
    p1_response_compliance_rate: float
    evidence_digest: str


@dataclass(frozen=True)
class IncidentSummary:
    incident_count: int
    open_p0_count: int
    resolved_count: int
    tenant_isolation_incident_count: int
    unresolved_material_tenant_isolation_defect_count: int
    recovery_validated_count: int
    evidence_digest: str


@dataclass(frozen=True)
class OperationalReadinessSummary:
    support: SupportSummary
    incidents: IncidentSummary
    support_process_evidence_available: bool
    recovery_evidence_available: bool
    no_unresolved_material_tenant_isolation_defect: bool
    evidence_digest: str
    state: str


class Phase7OperationalEvidenceRegistry:
    def __init__(self) -> None:
        self._feedback: dict[
            str,
            MerchantFeedback,
        ] = {}
        self._tickets: dict[
            str,
            SupportTicket,
        ] = {}
        self._incidents: dict[
            str,
            ProductionIncident,
        ] = {}

    def record_feedback(
        self,
        feedback: MerchantFeedback,
    ) -> dict[str, Any]:
        feedback.validate()

        normalized = replace(
            feedback,
            merchant_ref=_merchant_ref(
                feedback.merchant_ref
            ),
            category=str(
                feedback.category
            ).strip().upper(),
            severity=str(
                feedback.severity
            ).strip().upper(),
            product_decision=str(
                feedback.product_decision
            ).strip().upper(),
            recorded_at=_iso(
                feedback.recorded_at
            ),
            evidence_ref=_evidence_ref(
                feedback.evidence_ref
            ),
            metadata=dict(
                feedback.metadata
            ),
        )

        existing = self._feedback.get(
            normalized.feedback_id
        )

        if existing is not None:
            if existing != normalized:
                raise OperationalEvidenceError(
                    "feedback_id already exists with different evidence"
                )
            return {
                "created": False,
                "feedback": existing,
            }

        self._feedback[
            normalized.feedback_id
        ] = normalized

        return {
            "created": True,
            "feedback": normalized,
        }

    def decide_feedback(
        self,
        *,
        feedback_id: str,
        decision: str,
        decided_at: str,
        evidence_ref: str,
    ) -> MerchantFeedback:
        existing = self._feedback.get(
            _text(
                "feedback_id",
                feedback_id,
                max_length=128,
            )
        )

        if existing is None:
            raise OperationalEvidenceError(
                "feedback not found"
            )

        target = str(
            decision
        ).strip().upper()

        if target not in PRODUCT_DECISIONS:
            raise OperationalEvidenceError(
                "invalid feedback decision"
            )

        metadata = dict(
            existing.metadata
        )
        metadata[
            "decision_change"
        ] = {
            "from": (
                existing.product_decision
            ),
            "to": target,
            "decided_at": _iso(
                decided_at
            ),
            "evidence_ref": _evidence_ref(
                evidence_ref
            ),
        }

        updated = replace(
            existing,
            product_decision=target,
            metadata=metadata,
        )
        updated.validate()

        self._feedback[
            existing.feedback_id
        ] = updated

        return updated

    def open_ticket(
        self,
        ticket: SupportTicket,
    ) -> dict[str, Any]:
        ticket.validate()

        if (
            str(
                ticket.state
            ).strip().upper()
            != "OPEN"
        ):
            raise OperationalEvidenceError(
                "new support ticket must start OPEN"
            )

        normalized = replace(
            ticket,
            merchant_ref=_merchant_ref(
                ticket.merchant_ref
            ),
            severity=str(
                ticket.severity
            ).strip().upper(),
            product=str(
                ticket.product
            ).strip().upper(),
            owner_ref=_owner_ref(
                ticket.owner_ref
            ),
            opened_at=_iso(
                ticket.opened_at
            ),
            evidence_ref=_evidence_ref(
                ticket.evidence_ref
            ),
            state="OPEN",
            metadata=dict(
                ticket.metadata
                or {}
            ),
        )

        existing = self._tickets.get(
            normalized.ticket_id
        )

        if existing is not None:
            if existing != normalized:
                raise OperationalEvidenceError(
                    "ticket_id already exists with different evidence"
                )
            return {
                "created": False,
                "ticket": existing,
            }

        self._tickets[
            normalized.ticket_id
        ] = normalized

        return {
            "created": True,
            "ticket": normalized,
        }

    def record_first_response(
        self,
        *,
        ticket_id: str,
        responded_at: str,
        evidence_ref: str,
    ) -> SupportTicket:
        ticket = self._require_ticket(
            ticket_id
        )

        if ticket.first_response_at is not None:
            raise OperationalEvidenceError(
                "first response already recorded"
            )

        response_time = _iso(
            responded_at
        )

        if _time(
            response_time
        ) < _time(
            ticket.opened_at
        ):
            raise OperationalEvidenceError(
                "first response predates ticket"
            )

        updated = replace(
            ticket,
            first_response_at=response_time,
            first_response_evidence_ref=_evidence_ref(
                evidence_ref
            ),
            state=(
                "IN_PROGRESS"
                if ticket.state == "OPEN"
                else ticket.state
            ),
        )
        updated.validate()

        self._tickets[
            ticket.ticket_id
        ] = updated

        return updated

    def resolve_ticket(
        self,
        *,
        ticket_id: str,
        resolution: str,
        resolved_at: str,
        evidence_ref: str,
    ) -> SupportTicket:
        ticket = self._require_ticket(
            ticket_id
        )

        if ticket.state == "RESOLVED":
            raise OperationalEvidenceError(
                "support ticket already resolved"
            )

        resolved_time = _iso(
            resolved_at
        )

        if _time(
            resolved_time
        ) < _time(
            ticket.opened_at
        ):
            raise OperationalEvidenceError(
                "ticket resolution predates opening"
            )

        updated = replace(
            ticket,
            state="RESOLVED",
            resolution=_text(
                "resolution",
                resolution,
            ),
            resolved_at=resolved_time,
            resolution_evidence_ref=_evidence_ref(
                evidence_ref
            ),
        )
        updated.validate()

        self._tickets[
            ticket.ticket_id
        ] = updated

        return updated

    def create_incident(
        self,
        incident: ProductionIncident,
    ) -> dict[str, Any]:
        incident.validate()

        if (
            str(
                incident.state
            ).strip().upper()
            != "OPEN"
        ):
            raise OperationalEvidenceError(
                "new production incident must start OPEN"
            )

        normalized = replace(
            incident,
            severity=str(
                incident.severity
            ).strip().upper(),
            start_time=_iso(
                incident.start_time
            ),
            owner_ref=_owner_ref(
                incident.owner_ref
            ),
            affected_tenants=tuple(
                sorted({
                    _org_ref(
                        item
                    )
                    for item in incident.affected_tenants
                })
            ),
            affected_services=tuple(
                sorted({
                    _text(
                        "affected_service",
                        item,
                        max_length=128,
                    )
                    for item in incident.affected_services
                })
            ),
            creation_evidence_ref=_evidence_ref(
                incident.creation_evidence_ref
            ),
            state="OPEN",
            metadata=dict(
                incident.metadata
                or {}
            ),
        )

        existing = self._incidents.get(
            normalized.incident_id
        )

        if existing is not None:
            if existing != normalized:
                raise OperationalEvidenceError(
                    "incident_id already exists with different evidence"
                )
            return {
                "created": False,
                "incident": existing,
            }

        self._incidents[
            normalized.incident_id
        ] = normalized

        return {
            "created": True,
            "incident": normalized,
        }

    def mitigate_incident(
        self,
        *,
        incident_id: str,
        mitigation: str,
        mitigated_at: str,
        evidence_ref: str,
    ) -> ProductionIncident:
        incident = self._require_incident(
            incident_id
        )

        if incident.state != "OPEN":
            raise OperationalEvidenceError(
                "only OPEN incident may be mitigated"
            )

        metadata = dict(
            incident.metadata
            or {}
        )
        metadata[
            "mitigation"
        ] = {
            "description": _text(
                "mitigation",
                mitigation,
            ),
            "mitigated_at": _iso(
                mitigated_at
            ),
            "evidence_ref": _evidence_ref(
                evidence_ref
            ),
        }

        updated = replace(
            incident,
            state="MITIGATED",
            metadata=metadata,
        )
        updated.validate()

        self._incidents[
            incident.incident_id
        ] = updated

        return updated

    def resolve_incident(
        self,
        *,
        incident_id: str,
        root_cause: str,
        resolution: str,
        recovery_validation: str,
        corrective_actions: tuple[str, ...],
        resolved_at: str,
        evidence_ref: str,
    ) -> ProductionIncident:
        incident = self._require_incident(
            incident_id
        )

        if incident.state == "RESOLVED":
            raise OperationalEvidenceError(
                "incident already resolved"
            )

        updated = replace(
            incident,
            state="RESOLVED",
            root_cause=_text(
                "root_cause",
                root_cause,
            ),
            resolution=_text(
                "resolution",
                resolution,
            ),
            recovery_validation=_text(
                "recovery_validation",
                recovery_validation,
            ),
            corrective_actions=tuple(
                _text(
                    "corrective_action",
                    action,
                )
                for action in corrective_actions
            ),
            resolved_at=_iso(
                resolved_at
            ),
            resolution_evidence_ref=_evidence_ref(
                evidence_ref
            ),
        )
        updated.validate()

        self._incidents[
            incident.incident_id
        ] = updated

        return updated

    def support_summary(
        self,
    ) -> SupportSummary:
        tickets = tuple(
            self._tickets.values()
        )
        p1 = tuple(
            ticket
            for ticket in tickets
            if ticket.severity
            == "P1"
        )

        responded = tuple(
            ticket
            for ticket in p1
            if ticket.first_response_at
            is not None
        )

        compliant = sum(
            1
            for ticket in responded
            if _time(
                ticket.first_response_at
                or ticket.opened_at
            )
            <= _business_day_deadline(
                _time(
                    ticket.opened_at
                )
            )
        )

        return SupportSummary(
            ticket_count=len(
                tickets
            ),
            open_count=sum(
                1
                for ticket in tickets
                if ticket.state
                != "RESOLVED"
            ),
            resolved_count=sum(
                1
                for ticket in tickets
                if ticket.state
                == "RESOLVED"
            ),
            p0_count=sum(
                1
                for ticket in tickets
                if ticket.severity
                == "P0"
            ),
            p1_count=len(
                p1
            ),
            p1_responded_count=len(
                responded
            ),
            p1_within_one_business_day_count=(
                compliant
            ),
            p1_response_compliance_rate=(
                compliant
                / len(p1)
                if p1
                else 0.0
            ),
            evidence_digest=_digest([
                asdict(
                    ticket
                )
                for ticket in sorted(
                    tickets,
                    key=lambda item: (
                        item.ticket_id
                    ),
                )
            ]),
        )

    def incident_summary(
        self,
    ) -> IncidentSummary:
        incidents = tuple(
            self._incidents.values()
        )

        return IncidentSummary(
            incident_count=len(
                incidents
            ),
            open_p0_count=sum(
                1
                for incident in incidents
                if (
                    incident.severity
                    == "P0"
                    and incident.state
                    != "RESOLVED"
                )
            ),
            resolved_count=sum(
                1
                for incident in incidents
                if incident.state
                == "RESOLVED"
            ),
            tenant_isolation_incident_count=sum(
                1
                for incident in incidents
                if incident.tenant_isolation_impact
            ),
            unresolved_material_tenant_isolation_defect_count=sum(
                1
                for incident in incidents
                if (
                    incident.material_tenant_isolation_defect
                    and incident.state
                    != "RESOLVED"
                )
            ),
            recovery_validated_count=sum(
                1
                for incident in incidents
                if (
                    incident.state
                    == "RESOLVED"
                    and incident.recovery_validation
                    is not None
                )
            ),
            evidence_digest=_digest([
                asdict(
                    incident
                )
                for incident in sorted(
                    incidents,
                    key=lambda item: (
                        item.incident_id
                    ),
                )
            ]),
        )

    def operational_readiness(
        self,
    ) -> OperationalReadinessSummary:
        support = self.support_summary()
        incidents = self.incident_summary()

        support_evidence = (
            support.ticket_count > 0
        )
        recovery_evidence = (
            incidents.recovery_validated_count
            > 0
        )
        isolation_safe = (
            incidents.unresolved_material_tenant_isolation_defect_count
            == 0
        )

        state = (
            "EVIDENCE_AVAILABLE"
            if (
                support_evidence
                and recovery_evidence
                and isolation_safe
            )
            else "PENDING"
        )

        digest = _digest({
            "support": asdict(
                support
            ),
            "incidents": asdict(
                incidents
            ),
            "support_process_evidence_available": (
                support_evidence
            ),
            "recovery_evidence_available": (
                recovery_evidence
            ),
            "no_unresolved_material_tenant_isolation_defect": (
                isolation_safe
            ),
        })

        return OperationalReadinessSummary(
            support=support,
            incidents=incidents,
            support_process_evidence_available=(
                support_evidence
            ),
            recovery_evidence_available=(
                recovery_evidence
            ),
            no_unresolved_material_tenant_isolation_defect=(
                isolation_safe
            ),
            evidence_digest=digest,
            state=state,
        )

    def _require_ticket(
        self,
        ticket_id: str,
    ) -> SupportTicket:
        ticket = self._tickets.get(
            _text(
                "ticket_id",
                ticket_id,
                max_length=128,
            )
        )
        if ticket is None:
            raise OperationalEvidenceError(
                "support ticket not found"
            )
        return ticket

    def _require_incident(
        self,
        incident_id: str,
    ) -> ProductionIncident:
        incident = self._incidents.get(
            _text(
                "incident_id",
                incident_id,
                max_length=128,
            )
        )
        if incident is None:
            raise OperationalEvidenceError(
                "production incident not found"
            )
        return incident
