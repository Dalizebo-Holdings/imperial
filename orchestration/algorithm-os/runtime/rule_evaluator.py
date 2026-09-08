from __future__ import annotations

SECURITY_ORDER = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}

ALLOWED_OUTCOMES = {
    "APPROVED_FOR_AUTHORIZATION",
    "REQUIRES_APPROVAL",
    "REQUIRES_CONTEXT",
    "POLICY_DENIED",
    "CAPABILITY_UNAVAILABLE",
    "DEPENDENCY_UNRESOLVED",
    "SAFE_FAILURE",
}


class RuleEvaluationError(ValueError):
    pass


def _canonical_id(value: str) -> str:
    raw = value.removeprefix("OS-").strip()
    if not raw.isdigit():
        raise RuleEvaluationError(f"Invalid capability ID: {value}")
    number = int(raw)
    if number < 1 or number > 269:
        raise RuleEvaluationError(f"Capability outside canonical range: {value}")
    return f"{number:03d}"


def risk_class_for(
    capability_ids: list[str],
    policy_profiles: dict[str, dict[str, str]],
) -> str:
    highest = "LOW"

    for capability_id in capability_ids:
        cid = _canonical_id(capability_id)
        profile = policy_profiles.get(cid)
        if profile is None:
            raise RuleEvaluationError(
                f"Missing policy profile for OS-{cid}"
            )

        security = profile["security_level"].strip().upper()
        if security not in SECURITY_ORDER:
            raise RuleEvaluationError(
                f"Invalid security level for OS-{cid}: {security}"
            )

        if SECURITY_ORDER[security] > SECURITY_ORDER[highest]:
            highest = security

    return highest


def evaluate(
    *,
    requested_capabilities: list[str],
    policy_results: list[dict],
    dependency_resolution: dict,
    policy_profiles: dict[str, dict[str, str]],
    constraints: dict | None = None,
) -> dict:
    constraints = constraints or {}

    if not requested_capabilities:
        return {
            "outcome": "SAFE_FAILURE",
            "risk_class": "LOW",
            "required_approvals": [],
            "reasons": ["empty_request"],
        }

    try:
        requested_ids = [
            _canonical_id(item)
            for item in requested_capabilities
        ]
    except RuleEvaluationError as exc:
        return {
            "outcome": "SAFE_FAILURE",
            "risk_class": "LOW",
            "required_approvals": [],
            "reasons": [str(exc)],
        }

    policy_by_capability = {}

    for result in policy_results:
        capability_id = str(result.get("capability_id", ""))
        try:
            cid = _canonical_id(capability_id)
        except RuleEvaluationError:
            return {
                "outcome": "SAFE_FAILURE",
                "risk_class": "LOW",
                "required_approvals": [],
                "reasons": ["malformed_policy_result"],
            }

        outcome = str(result.get("outcome", "")).strip().upper()
        if outcome not in ALLOWED_OUTCOMES:
            return {
                "outcome": "SAFE_FAILURE",
                "risk_class": "LOW",
                "required_approvals": [],
                "reasons": ["malformed_policy_outcome"],
            }

        policy_by_capability[cid] = outcome

    missing_policy = [
        cid
        for cid in requested_ids
        if cid not in policy_by_capability
    ]

    if missing_policy:
        return {
            "outcome": "REQUIRES_CONTEXT",
            "risk_class": risk_class_for(
                requested_capabilities,
                policy_profiles,
            ),
            "required_approvals": [],
            "reasons": [
                "missing_policy_results:"
                + ",".join(f"OS-{cid}" for cid in missing_policy)
            ],
        }

    outcomes = set(policy_by_capability.values())

    if "SAFE_FAILURE" in outcomes:
        final_outcome = "SAFE_FAILURE"
        reasons = ["policy_safe_failure"]
    elif "POLICY_DENIED" in outcomes:
        final_outcome = "POLICY_DENIED"
        reasons = ["pillars_policy_denied"]
    elif "REQUIRES_CONTEXT" in outcomes:
        final_outcome = "REQUIRES_CONTEXT"
        reasons = ["policy_requires_context"]
    elif dependency_resolution.get("cycles"):
        final_outcome = "DEPENDENCY_UNRESOLVED"
        reasons = ["dependency_cycle"]
    elif "CAPABILITY_UNAVAILABLE" in outcomes:
        final_outcome = "CAPABILITY_UNAVAILABLE"
        reasons = ["capability_unavailable"]
    elif "REQUIRES_APPROVAL" in outcomes:
        final_outcome = "REQUIRES_APPROVAL"
        reasons = ["policy_requires_approval"]
    else:
        final_outcome = "APPROVED_FOR_AUTHORIZATION"
        reasons = ["deterministic_rules_satisfied"]

    required_approvals = []

    for capability_id in dependency_resolution.get(
        "ordered_canonical_capabilities",
        requested_capabilities,
    ):
        cid = _canonical_id(capability_id)
        profile = policy_profiles.get(cid)

        if profile is None:
            continue

        approval_mode = profile["approval_mode"].strip().upper()
        eligibility = profile["execution_eligibility"].strip().upper()

        if (
            approval_mode == "EXPLICIT_APPROVAL_REQUIRED"
            or eligibility == "RESEARCH_ONLY"
        ):
            ref = f"OS-{cid}"
            if ref not in required_approvals:
                required_approvals.append(ref)

    if (
        final_outcome == "APPROVED_FOR_AUTHORIZATION"
        and required_approvals
    ):
        final_outcome = "REQUIRES_APPROVAL"
        reasons = ["explicit_approval_required"]

    if constraints.get("require_human_approval") is True:
        if final_outcome == "APPROVED_FOR_AUTHORIZATION":
            final_outcome = "REQUIRES_APPROVAL"
            reasons = ["request_constraint_requires_human_approval"]

    planned = dependency_resolution.get(
        "ordered_canonical_capabilities",
        requested_capabilities,
    )

    return {
        "outcome": final_outcome,
        "risk_class": risk_class_for(planned, policy_profiles),
        "required_approvals": required_approvals,
        "reasons": reasons,
    }
