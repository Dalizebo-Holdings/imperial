from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json


class ExecutionPlannerError(ValueError):
    pass


def _stable_digest(payload: dict) -> str:
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def build_execution_plan(
    *,
    decision_request: dict,
    rule_evaluation: dict,
    dependency_resolution: dict,
    policy_results: list[dict],
    registry_version: str = "phase3-capability-registry-v1",
    policy_version: str = "pillars-os-v1",
    created_at: str | None = None,
) -> dict:
    required_request_fields = [
        "decision_request_id",
        "organization_id",
        "actor_id",
        "requested_capabilities",
        "constraints",
        "idempotency_key",
        "correlation_id",
    ]

    missing = [
        field
        for field in required_request_fields
        if field not in decision_request
    ]

    if missing:
        raise ExecutionPlannerError(
            "Missing decision request fields: " + ", ".join(missing)
        )

    if not str(decision_request["correlation_id"]).strip():
        raise ExecutionPlannerError("correlation_id must not be empty")

    dependency_order = list(
        dependency_resolution.get(
            "ordered_canonical_capabilities",
            [],
        )
    )

    outcome = rule_evaluation["outcome"]

    ready = outcome == "APPROVED_FOR_AUTHORIZATION"
    step_state = (
        "READY_FOR_KERNEL_AUTHORIZATION"
        if ready
        else "BLOCKED"
    )

    execution_steps = [
        {
            "sequence": index,
            "capability_id": capability_id,
            "state": step_state,
        }
        for index, capability_id in enumerate(
            dependency_order,
            start=1,
        )
    ]

    integrations = dependency_resolution.get(
        "external_prerequisites",
        {},
    )
    platform_prerequisites = dependency_resolution.get(
        "platform_prerequisites",
        {},
    )

    material = {
        "decision_request_id": decision_request["decision_request_id"],
        "organization_id": decision_request["organization_id"],
        "actor_id": decision_request["actor_id"],
        "requested_capabilities": decision_request["requested_capabilities"],
        "constraints": decision_request["constraints"],
        "idempotency_key": decision_request["idempotency_key"],
        "correlation_id": decision_request["correlation_id"],
        "policy_results": policy_results,
        "dependency_order": dependency_order,
        "rule_evaluation": rule_evaluation,
        "registry_version": registry_version,
        "policy_version": policy_version,
    }

    digest = _stable_digest(material)
    decision_id = f"decision_{digest[:24]}"

    timestamp = created_at or datetime.now(timezone.utc).isoformat()

    audit_event = {
        "event_type": "algorithm_os.decision_planned",
        "decision_id": decision_id,
        "decision_request_id": decision_request["decision_request_id"],
        "correlation_id": decision_request["correlation_id"],
        "actor_id": decision_request["actor_id"],
        "organization_id": decision_request["organization_id"],
        "registry_version": registry_version,
        "policy_version": policy_version,
        "risk_class": rule_evaluation["risk_class"],
        "outcome": outcome,
    }

    return {
        "decision_id": decision_id,
        "decision_request_id": decision_request["decision_request_id"],
        "correlation_id": decision_request["correlation_id"],
        "policy_result": outcome,
        "selected_capabilities": list(
            decision_request["requested_capabilities"]
        ),
        "dependency_order": dependency_order,
        "execution_steps": execution_steps,
        "required_approvals": list(
            rule_evaluation.get("required_approvals", [])
        ),
        "required_loop_jobs": [],
        "required_integrations": integrations,
        "platform_prerequisites": platform_prerequisites,
        "risk_class": rule_evaluation["risk_class"],
        "audit_event": audit_event,
        "kernel_authorization": "REQUIRED",
        "created_at": timestamp,
    }
