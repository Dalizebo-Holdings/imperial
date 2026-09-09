#!/usr/bin/env python3
from pathlib import Path
import importlib
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"
SAAS = ROOT / "saas"

root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "feedback/README.md",
    VALIDATION / "support/README.md",
    VALIDATION / "incidents/README.md",
    VALIDATION / "feedback/FEEDBACK_CONTRACT.md",
    VALIDATION / "support/SUPPORT_CONTRACT.md",
    VALIDATION / "incidents/INCIDENT_CONTRACT.md",
    VALIDATION / "operations_runtime.py",
    VALIDATION / "pilot_runtime.py",
    SAAS / "STATUS.md",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Phase 7 operational evidence file: {path}"
        )

for path in [
    VALIDATION / "operations_runtime.py",
    VALIDATION / "pilot_runtime.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

try:
    ops = importlib.import_module(
        "validation.operations_runtime"
    )
except Exception as exc:
    raise SystemExit(
        f"ERROR: unable to import validation.operations_runtime: {exc}"
    ) from exc

feedback_doc = (
    VALIDATION / "feedback/README.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Onboarding",
    "Commerce",
    "POS",
    "Inventory",
    "Payments",
    "Reporting",
    "Performance",
    "Reliability",
    "Support",
    "Pricing",
    "Merchant",
    "Problem",
    "Frequency",
    "Severity",
    "Business impact",
    "Requested outcome",
    "Existing workaround",
    "Product decision",
]:
    if phrase not in feedback_doc:
        raise SystemExit(
            "ERROR: canonical feedback field/category missing: "
            + phrase
        )

support_doc = (
    VALIDATION / "support/README.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "P0",
    "P1",
    "P2",
    "P3",
    "P1 first response within one business day.",
    "Organization ID",
    "Correlation ID",
    "Owner",
    "Resolution",
]:
    if phrase not in support_doc:
        raise SystemExit(
            "ERROR: canonical support requirement missing: "
            + phrase
        )

incident_doc = (
    VALIDATION / "incidents/README.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "Incident ID",
    "Severity",
    "Start time",
    "Detection source",
    "Owner",
    "Affected tenants",
    "Affected services",
    "Customer impact",
    "Root cause",
    "Resolution",
    "Recovery validation",
    "Corrective actions",
    "No critical incident may remain without an assigned owner.",
]:
    if phrase not in incident_doc:
        raise SystemExit(
            "ERROR: canonical incident requirement missing: "
            + phrase
        )

registry = (
    ops.Phase7OperationalEvidenceRegistry()
)

feedback = ops.MerchantFeedback(
    feedback_id="feedback-test-001",
    merchant_ref="merchant://test/001",
    category="POS",
    problem="Barcode lookup needs fewer operator steps.",
    frequency=3,
    severity="P2",
    business_impact="Checkout takes longer during busy periods.",
    requested_outcome="Faster product lookup workflow.",
    existing_workaround="Cashier uses exact SKU lookup.",
    product_decision="PENDING",
    recorded_at="2026-09-09T09:00:00+02:00",
    evidence_ref="evidence://test/feedback/001",
    metadata={
        "fixture": True,
    },
)

created_feedback = registry.record_feedback(
    feedback
)

if created_feedback["created"] is not True:
    raise SystemExit(
        "ERROR: feedback fixture was not created"
    )

if registry.record_feedback(
    feedback
)["created"] is not False:
    raise SystemExit(
        "ERROR: feedback idempotency failed"
    )

decided = registry.decide_feedback(
    feedback_id=feedback.feedback_id,
    decision="INVESTIGATE",
    decided_at="2026-09-09T10:00:00+02:00",
    evidence_ref="evidence://test/feedback/decision/001",
)

if (
    decided.product_decision
    != "INVESTIGATE"
):
    raise SystemExit(
        "ERROR: feedback decision update failed"
    )

p1_ticket = ops.SupportTicket(
    ticket_id="ticket-p1-test",
    merchant_ref="merchant://test/001",
    organization_id="org-test-001",
    severity="P1",
    product="POS",
    environment_id="env-production",
    description="Checkout workflow is unavailable.",
    correlation_id="corr-support-test-001",
    owner_ref="user://support-owner/001",
    opened_at="2026-09-11T15:00:00+02:00",
    evidence_ref="evidence://test/support/open/001",
    metadata={
        "fixture": True,
    },
)

registry.open_ticket(
    p1_ticket
)

# Friday -> Monday same local time is one business-day deadline.
responded = registry.record_first_response(
    ticket_id=p1_ticket.ticket_id,
    responded_at="2026-09-14T14:00:00+02:00",
    evidence_ref="evidence://test/support/response/001",
)

if (
    responded.state
    != "IN_PROGRESS"
):
    raise SystemExit(
        "ERROR: support first response did not advance ticket"
    )

registry.resolve_ticket(
    ticket_id=p1_ticket.ticket_id,
    resolution="Checkout service restored and merchant confirmed recovery.",
    resolved_at="2026-09-14T16:00:00+02:00",
    evidence_ref="evidence://test/support/resolve/001",
)

late_ticket = ops.SupportTicket(
    ticket_id="ticket-p1-late",
    merchant_ref="merchant://test/002",
    organization_id="org-test-002",
    severity="P1",
    product="COMMERCE",
    environment_id="env-production",
    description="Order placement workflow is unavailable.",
    correlation_id="corr-support-test-002",
    owner_ref="user://support-owner/002",
    opened_at="2026-09-07T09:00:00+02:00",
    evidence_ref="evidence://test/support/open/002",
    metadata={},
)

registry.open_ticket(
    late_ticket
)

registry.record_first_response(
    ticket_id=late_ticket.ticket_id,
    responded_at="2026-09-09T09:01:00+02:00",
    evidence_ref="evidence://test/support/response/002",
)

summary = registry.support_summary()

if (
    summary.p1_count != 2
    or summary.p1_responded_count != 2
    or summary.p1_within_one_business_day_count != 1
    or abs(
        summary.p1_response_compliance_rate
        - 0.5
    ) > 1e-12
):
    raise SystemExit(
        "ERROR: P1 response SLA calculation failed"
    )

incident = ops.ProductionIncident(
    incident_id="incident-test-001",
    severity="P0",
    start_time="2026-09-09T11:00:00+02:00",
    detection_source="monitoring",
    owner_ref="user://incident-owner/001",
    affected_tenants=(
        "organization://test/001",
    ),
    affected_services=(
        "api-gateway",
        "commerce",
    ),
    customer_impact="Pilot checkout requests failed.",
    tenant_isolation_impact=False,
    material_tenant_isolation_defect=False,
    creation_evidence_ref="evidence://test/incident/open/001",
    metadata={
        "fixture": True,
    },
)

registry.create_incident(
    incident
)

registry.mitigate_incident(
    incident_id=incident.incident_id,
    mitigation="Traffic routed to healthy service instances.",
    mitigated_at="2026-09-09T11:15:00+02:00",
    evidence_ref="evidence://test/incident/mitigation/001",
)

resolved = registry.resolve_incident(
    incident_id=incident.incident_id,
    root_cause="A failed deployment left unhealthy service instances active.",
    resolution="Deployment was rolled back and healthy capacity restored.",
    recovery_validation="Synthetic checkout and pilot health probes passed.",
    corrective_actions=(
        "Add automated unhealthy-instance removal.",
        "Require rollback verification in deployment gate.",
    ),
    resolved_at="2026-09-09T12:00:00+02:00",
    evidence_ref="evidence://test/incident/resolve/001",
)

if (
    resolved.state
    != "RESOLVED"
):
    raise SystemExit(
        "ERROR: incident resolution lifecycle failed"
    )

incident_summary = registry.incident_summary()

if (
    incident_summary.incident_count != 1
    or incident_summary.open_p0_count != 0
    or incident_summary.recovery_validated_count != 1
):
    raise SystemExit(
        "ERROR: incident summary failed"
    )

ready = registry.operational_readiness()

if (
    ready.state
    != "EVIDENCE_AVAILABLE"
    or not ready.support_process_evidence_available
    or not ready.recovery_evidence_available
    or not ready.no_unresolved_material_tenant_isolation_defect
):
    raise SystemExit(
        "ERROR: operational evidence readiness calculation failed"
    )

isolation_incident = ops.ProductionIncident(
    incident_id="incident-isolation-test",
    severity="P0",
    start_time="2026-09-09T13:00:00+02:00",
    detection_source="tenant-isolation-test",
    owner_ref="user://incident-owner/002",
    affected_tenants=(
        "organization://test/001",
        "organization://test/002",
    ),
    affected_services=(
        "database",
    ),
    customer_impact="Test fixture detected material cross-tenant exposure.",
    tenant_isolation_impact=True,
    material_tenant_isolation_defect=True,
    creation_evidence_ref="evidence://test/incident/isolation/open",
    metadata={
        "fixture": True,
    },
)

registry.create_incident(
    isolation_incident
)

blocked = registry.operational_readiness()

if (
    blocked.state
    != "PENDING"
    or blocked.no_unresolved_material_tenant_isolation_defect
):
    raise SystemExit(
        "ERROR: unresolved material tenant-isolation defect did not block readiness"
    )

registry.resolve_incident(
    incident_id=isolation_incident.incident_id,
    root_cause="Test fixture authorization filter regression.",
    resolution="Tenant filter was restored.",
    recovery_validation="Cross-tenant regression suite passed.",
    corrective_actions=(
        "Add mandatory isolation regression gate.",
    ),
    resolved_at="2026-09-09T14:00:00+02:00",
    evidence_ref="evidence://test/incident/isolation/resolve",
)

if (
    registry.operational_readiness().state
    != "EVIDENCE_AVAILABLE"
):
    raise SystemExit(
        "ERROR: resolved isolation incident remained a blocker"
    )

# P0 incident without owner must fail.
try:
    registry.create_incident(
        ops.ProductionIncident(
            **{
                **incident.__dict__,
                "incident_id": "incident-no-owner",
                "owner_ref": "",
            }
        )
    )
except ops.OperationalEvidenceError:
    pass
else:
    raise SystemExit(
        "ERROR: critical incident without owner was accepted"
    )

# Sensitive metadata must fail.
try:
    registry.record_feedback(
        ops.MerchantFeedback(
            **{
                **feedback.__dict__,
                "feedback_id": "feedback-sensitive",
                "metadata": {
                    "api_key": "must-not-be-here",
                },
            }
        )
    )
except ops.OperationalEvidenceError:
    pass
else:
    raise SystemExit(
        "ERROR: sensitive feedback metadata was accepted"
    )

status = (
    VALIDATION / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "## Feedback + Support + Incidents",
    "- [x] P1 <=1 business-day calculation",
    "- [x] Critical incident owner enforcement",
    "- [x] Material tenant-isolation defect tracking",
    "- [ ] Actual P1 response SLA measured",
    "- [ ] Operational evidence attached to release gates",
    "Phase 7 evidence ingestion + PMF decision/closure gate.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 7 operational status missing or overclaims evidence: "
            + phrase
        )

print("OK: Canonical feedback classification evidence passed.")
print("OK: Feedback decision changes are explicit/idempotent.")
print("OK: P0–P3 support evidence lifecycle passed.")
print("OK: P1 <=1 business-day response calculation passed.")
print("OK: Production incident ownership/recovery lifecycle passed.")
print("OK: Unresolved material tenant-isolation defects block readiness.")
print("OK: Recovery evidence restores operational readiness after resolution.")
print("OK: Sensitive credential/payment metadata is rejected.")
print("STATUS: PHASE 7 FEEDBACK + SUPPORT + INCIDENTS READY")
