from __future__ import annotations

from pathlib import Path
import csv

ALLOWED_PILLARS_DECISIONS = {
    "ALLOW": "APPROVED_FOR_AUTHORIZATION",
    "DENY": "POLICY_DENIED",
    "REQUIRE_APPROVAL": "REQUIRES_APPROVAL",
    "REQUIRE_CONTEXT": "REQUIRES_CONTEXT",
}


class PolicyAdapterError(ValueError):
    pass


def load_policy_profiles(path: str | Path) -> dict[str, dict[str, str]]:
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {row["canonical_id"]: row for row in rows}


def build_policy_request(
    profiles: dict[str, dict[str, str]],
    *,
    capability_id: str,
    decision_request_id: str,
    actor_id: str,
    organization_id: str,
    correlation_id: str,
    requested_operation: str,
    environment: str,
) -> dict:
    cid = capability_id.removeprefix("OS-").zfill(3)
    profile = profiles.get(cid)

    if profile is None:
        raise PolicyAdapterError(f"Unknown canonical capability: OS-{cid}")

    required = {
        "decision_request_id": decision_request_id,
        "actor_id": actor_id,
        "organization_id": organization_id,
        "correlation_id": correlation_id,
        "requested_operation": requested_operation,
        "environment": environment,
    }

    missing = [key for key, value in required.items() if not str(value).strip()]
    if missing:
        raise PolicyAdapterError(
            "Missing policy context: " + ", ".join(missing)
        )

    return {
        "policy_route": "PILLARS_OS",
        "decision_request_id": decision_request_id,
        "capability_id": f"OS-{cid}",
        "capability_name": profile["name"],
        "actor_id": actor_id,
        "organization_id": organization_id,
        "correlation_id": correlation_id,
        "requested_operation": requested_operation,
        "environment": environment,
        "security_level": profile["security_level"],
        "execution_eligibility": profile["execution_eligibility"],
        "approval_mode": profile["approval_mode"],
        "required_controls": [
            item
            for item in profile["required_controls"].split(";")
            if item
        ],
        "status": "PILLARS_OS_EVALUATION_REQUIRED",
    }


def apply_pillars_decision(
    *,
    policy_request: dict,
    pillars_decision: str,
) -> dict:
    decision = pillars_decision.strip().upper()
    outcome = ALLOWED_PILLARS_DECISIONS.get(decision, "SAFE_FAILURE")

    if (
        policy_request["execution_eligibility"] == "RESEARCH_ONLY"
        and outcome == "APPROVED_FOR_AUTHORIZATION"
    ):
        outcome = "REQUIRES_APPROVAL"

    return {
        "capability_id": policy_request["capability_id"],
        "decision_request_id": policy_request["decision_request_id"],
        "correlation_id": policy_request["correlation_id"],
        "pillars_decision": decision,
        "outcome": outcome,
    }
