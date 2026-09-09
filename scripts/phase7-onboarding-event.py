#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.evidence.collection import DEFAULT_INBOX, EvidenceCollectionError, envelope_from_input
from validation.evidence.store import DurableEvidenceStore
from validation.pilot_runtime import EVENT_STATUSES, ONBOARDING_STEP_ORDER, OnboardingEvent, PilotValidationError


def _onboardings(store):
    if not store.path.exists():
        return []
    result = []
    with store.path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            value = json.loads(raw)
            if str(value.get("origin", "")).strip().upper() != "REAL_MERCHANT":
                continue
            if str(value.get("evidence_type", "")).strip().upper() != "PILOT_ONBOARDING":
                continue
            payload = value.get("payload", {})
            if not isinstance(payload, dict):
                continue
            onboarding_id = str(payload.get("onboarding_id", "")).strip()
            merchant_ref = str(payload.get("merchant_ref", "")).strip()
            if onboarding_id and merchant_ref.startswith("merchant://"):
                result.append({
                    "onboarding_id": onboarding_id,
                    "commitment_id": str(payload.get("commitment_id", "")),
                    "merchant_ref": merchant_ref,
                    "products": list(payload.get("products", [])),
                    "started_at": str(payload.get("started_at", "")),
                    "onboarding_evidence_ref": str(value.get("evidence_ref", "")),
                })
    result.sort(key=lambda item: item["onboarding_id"])
    return result


def _select(items, onboarding_id):
    matches = [item for item in items if item["onboarding_id"] == onboarding_id]
    if not matches:
        raise ValueError("onboarding_id is not an ingested REAL_MERCHANT PILOT_ONBOARDING")
    if len(matches) != 1:
        raise ValueError("duplicate onboarding_id found in durable evidence")
    return matches[0]


def _time(value):
    raw = value or datetime.now().astimezone().isoformat()
    parsed = datetime.fromisoformat(str(raw).strip())
    if parsed.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware")
    return parsed.isoformat()


def _bool(value, name):
    raw = str(value).strip().lower()
    if raw in {"yes", "y", "true", "1"}:
        return True
    if raw in {"no", "n", "false", "0"}:
        return False
    raise ValueError(f"{name} must be yes or no")


def _evidence_ref(value):
    result = str(value).strip()
    if not result.startswith("evidence://"):
        raise ValueError("--evidence-ref must use evidence://")
    lower = result.lower()
    if any(marker in lower for marker in ("__replace__", "placeholder", "example", "todo", "tbd")):
        raise ValueError("--evidence-ref contains placeholder material")
    return result


def main():
    parser = argparse.ArgumentParser(description="Record real Phase 7 pilot onboarding events.")
    parser.add_argument("--ledger")
    parser.add_argument("--inbox", default=str(DEFAULT_INBOX))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")

    record = sub.add_parser("record")
    record.add_argument("--onboarding-id", required=True)
    record.add_argument("--step", required=True, choices=tuple(ONBOARDING_STEP_ORDER))
    record.add_argument("--status", required=True, choices=tuple(sorted(EVENT_STATUSES)))
    record.add_argument("--evidence-ref", required=True)
    record.add_argument("--occurred-at")
    record.add_argument("--failure-code")
    record.add_argument("--training-required", default="no")
    record.add_argument("--support-intervention", default="no")
    record.add_argument("--note")

    args = parser.parse_args()
    store = DurableEvidenceStore(args.ledger)
    onboardings = _onboardings(store)

    if args.command == "list":
        print(json.dumps({"count": len(onboardings), "onboardings": onboardings}, indent=2, sort_keys=True))
        return 0

    try:
        onboarding = _select(onboardings, str(args.onboarding_id).strip())
        occurred_at = _time(args.occurred_at)
        evidence_ref = _evidence_ref(args.evidence_ref)
        training_required = _bool(args.training_required, "--training-required")
        support_intervention = _bool(args.support_intervention, "--support-intervention")
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    status = str(args.status).strip().upper()
    failure_code = str(args.failure_code).strip() if args.failure_code is not None else None

    if status == "FAILED" and not failure_code:
        print("ERROR: --failure-code is required for FAILED events", file=sys.stderr)
        return 2
    if status == "SUCCESS" and failure_code is not None:
        print("ERROR: --failure-code is only valid for FAILED events", file=sys.stderr)
        return 2

    identifier = uuid.uuid4().hex
    metadata = {
        "linked_onboarding_evidence_ref": onboarding["onboarding_evidence_ref"],
        "evidence_source": "PHASE7_ONBOARDING_EVENT_CLI",
    }
    if args.note:
        metadata["operator_note"] = str(args.note).strip()

    payload = {
        "event_id": "onboarding_event_" + identifier,
        "onboarding_id": onboarding["onboarding_id"],
        "merchant_ref": onboarding["merchant_ref"],
        "step": str(args.step).strip().upper(),
        "status": status,
        "occurred_at": occurred_at,
        "evidence_ref": evidence_ref,
        "failure_code": failure_code,
        "training_required": training_required,
        "support_intervention": support_intervention,
        "metadata": metadata,
    }

    try:
        OnboardingEvent(**payload).validate()
    except PilotValidationError as exc:
        print(f"ERROR: canonical onboarding-event validation failed: {exc}", file=sys.stderr)
        return 2

    envelope = {
        "envelope_id": "pilot-onboarding-event-envelope-" + identifier,
        "evidence_type": "PILOT_ONBOARDING_EVENT",
        "origin": "REAL_MERCHANT",
        "observed_at": occurred_at,
        "evidence_ref": "evidence://phase7/pilot-onboarding-event-envelope/" + identifier,
        "source_system_ref": "source://validation/pilot-onboarding-events",
        "payload": payload,
    }

    try:
        envelope_from_input(envelope)
    except EvidenceCollectionError as exc:
        print(f"ERROR: evidence envelope validation failed: {exc}", file=sys.stderr)
        return 2

    inbox = Path(args.inbox).expanduser().resolve()
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{payload['event_id']}.json"
    if target.exists():
        print(f"ERROR: event target already exists: {target}", file=sys.stderr)
        return 2

    target.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target.chmod(0o600)

    print(json.dumps({
        "created": str(target),
        "event_id": payload["event_id"],
        "onboarding_id": payload["onboarding_id"],
        "merchant_ref": payload["merchant_ref"],
        "step": payload["step"],
        "status": payload["status"],
        "state": "READY_FOR_INBOX_PREFLIGHT",
        "onboarding_completion_claimed": False,
        "gate3_pass_claimed": False,
        "phase8": "BLOCKED",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
