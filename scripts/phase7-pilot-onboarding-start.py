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

from validation.evidence.collection import (
    DEFAULT_INBOX,
    EvidenceCollectionError,
    envelope_from_input,
)
from validation.evidence.store import DurableEvidenceStore
from validation.pilot_runtime import (
    PilotOnboarding,
    PilotValidationError,
    PilotValidationRegistry,
)
from validation.runtime import (
    DesignPartnerCommitment,
    ProductMarketValidationRegistry,
    ValidationEvidenceError,
)


def _products(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError("products must be an array")
    return tuple(str(item) for item in value)


def _mapping(value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("metadata must be an object")
    return dict(value)


def _commitment(payload):
    result = DesignPartnerCommitment(
        commitment_id=payload["commitment_id"],
        merchant_ref=payload["merchant_ref"],
        products=_products(payload["products"]),
        committed_at=payload["committed_at"],
        active_retail_operations=payload["active_retail_operations"],
        real_inventory=payload["real_inventory"],
        real_customers=payload["real_customers"],
        transaction_volume_confirmed=payload["transaction_volume_confirmed"],
        willingness_to_test=payload["willingness_to_test"],
        structured_feedback_available=payload["structured_feedback_available"],
        pilot_status=payload["pilot_status"],
        evidence_ref=payload["evidence_ref"],
        metadata=_mapping(payload.get("metadata", {})),
    )
    result.validate()
    return result


def _state(store):
    registry = ProductMarketValidationRegistry()
    current = {}
    onboardings = {}

    if not store.path.exists():
        return registry, current, onboardings

    with store.path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue

            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSON at ledger line {line_number}"
                ) from exc

            if str(row.get("origin", "")).strip().upper() == "TEST_FIXTURE":
                continue

            evidence_type = str(
                row.get("evidence_type", "")
            ).strip().upper()

            payload = row.get("payload", {})
            if not isinstance(payload, dict):
                continue

            if evidence_type == "DESIGN_PARTNER_COMMITMENT":
                item = _commitment(payload)
                registry.record_commitment(item)
                current[item.commitment_id] = item

            elif evidence_type == "PILOT_STATUS_TRANSITION":
                commitment_id = str(payload.get("commitment_id", "")).strip()
                merchant_ref = str(payload.get("merchant_ref", "")).strip()
                from_status = str(payload.get("from_status", "")).strip().upper()
                to_status = str(payload.get("to_status", "")).strip().upper()

                item = current.get(commitment_id)
                if item is None:
                    raise ValueError(
                        "pilot status transition references missing commitment"
                    )
                if item.merchant_ref != merchant_ref:
                    raise ValueError(
                        "pilot status transition merchant mismatch"
                    )
                if item.pilot_status != from_status:
                    raise ValueError(
                        "pilot status transition from_status mismatch"
                    )

                updated = registry.transition_pilot_status(
                    commitment_id=commitment_id,
                    target_status=to_status,
                    changed_at=payload["changed_at"],
                    evidence_ref=payload["evidence_ref"],
                )
                current[commitment_id] = updated

            elif evidence_type == "PILOT_ONBOARDING":
                onboarding_id = str(payload.get("onboarding_id", "")).strip()
                merchant_ref = str(payload.get("merchant_ref", "")).strip()
                commitment_id = str(payload.get("commitment_id", "")).strip()

                if onboarding_id:
                    onboardings[onboarding_id] = {
                        "onboarding_id": onboarding_id,
                        "merchant_ref": merchant_ref,
                        "commitment_id": commitment_id,
                    }

    return registry, current, onboardings


def _time(value):
    raw = value or datetime.now().astimezone().isoformat()
    try:
        parsed = datetime.fromisoformat(str(raw).strip())
    except ValueError as exc:
        raise ValueError("started_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("started_at must be timezone-aware")
    return parsed.isoformat()


def _evidence_ref(value):
    result = str(value).strip()

    if not result.startswith("evidence://"):
        raise ValueError("--evidence-ref must use evidence://")

    lowered = result.lower()
    if any(
        marker in lowered
        for marker in (
            "__replace__",
            "placeholder",
            "example",
            "todo",
            "tbd",
        )
    ):
        raise ValueError(
            "--evidence-ref contains placeholder material"
        )

    return result


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create real Phase 7 PILOT_ONBOARDING evidence "
            "for an already ACTIVE design partner."
        )
    )
    parser.add_argument("--ledger")
    parser.add_argument(
        "--inbox",
        default=str(DEFAULT_INBOX),
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser("list")

    start = sub.add_parser("start")
    start.add_argument(
        "--commitment-id",
        required=True,
    )
    start.add_argument(
        "--evidence-ref",
        required=True,
    )
    start.add_argument("--started-at")
    start.add_argument("--note")

    args = parser.parse_args()
    store = DurableEvidenceStore(args.ledger)

    try:
        _, current, onboardings = _state(store)
    except (
        ValueError,
        ValidationEvidenceError,
    ) as exc:
        print(
            f"ERROR: cannot reconstruct pilot state: {exc}",
            file=sys.stderr,
        )
        return 2

    merchant_onboarded = {
        value["merchant_ref"]
        for value in onboardings.values()
    }

    if args.command == "list":
        items = []
        for item in sorted(
            current.values(),
            key=lambda value: value.commitment_id,
        ):
            items.append({
                "commitment_id": item.commitment_id,
                "merchant_ref": item.merchant_ref,
                "products": list(item.products),
                "pilot_status": item.pilot_status,
                "onboarding_exists": (
                    item.merchant_ref
                    in merchant_onboarded
                ),
                "can_start_onboarding": (
                    item.pilot_status == "ACTIVE"
                    and item.merchant_ref not in merchant_onboarded
                ),
            })

        print(
            json.dumps(
                {
                    "commitment_count": len(items),
                    "commitments": items,
                    "onboarding_count": len(onboardings),
                    "phase8_authorized": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    commitment_id = str(args.commitment_id).strip()
    item = current.get(commitment_id)

    if item is None:
        print(
            "ERROR: commitment_id is not an ingested real design-partner commitment",
            file=sys.stderr,
        )
        return 2

    if item.pilot_status != "ACTIVE":
        print(
            "ERROR: pilot onboarding requires current ACTIVE design partner status",
            file=sys.stderr,
        )
        return 3

    if item.merchant_ref in merchant_onboarded:
        print(
            "ERROR: merchant already has PILOT_ONBOARDING evidence",
            file=sys.stderr,
        )
        return 3

    try:
        started_at = _time(args.started_at)
        supporting_ref = _evidence_ref(args.evidence_ref)
    except ValueError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    identifier = uuid.uuid4().hex

    metadata = {
        "execution_source": "PHASE7_PILOT_ONBOARDING_START_CLI",
        "active_status_verified_from_ledger": True,
    }

    if args.note:
        metadata["operator_note"] = str(args.note).strip()

    payload = {
        "onboarding_id": "onboarding_" + identifier,
        "commitment_id": item.commitment_id,
        "merchant_ref": item.merchant_ref,
        "products": list(item.products),
        "started_at": started_at,
        "evidence_ref": supporting_ref,
        "metadata": metadata,
    }

    onboarding = PilotOnboarding(
        onboarding_id=payload["onboarding_id"],
        commitment_id=payload["commitment_id"],
        merchant_ref=payload["merchant_ref"],
        products=tuple(payload["products"]),
        started_at=payload["started_at"],
        evidence_ref=payload["evidence_ref"],
        metadata=payload["metadata"],
    )

    try:
        onboarding.validate()

        validation_registry = PilotValidationRegistry()
        validation_registry.start_onboarding(
            commitment=item,
            onboarding=onboarding,
        )
    except PilotValidationError as exc:
        print(
            f"ERROR: canonical onboarding validation failed: {exc}",
            file=sys.stderr,
        )
        return 2

    envelope = {
        "envelope_id": "pilot-onboarding-envelope-" + identifier,
        "evidence_type": "PILOT_ONBOARDING",
        "origin": "REAL_MERCHANT",
        "observed_at": started_at,
        "evidence_ref": (
            "evidence://phase7/pilot-onboarding-envelope/"
            + identifier
        ),
        "source_system_ref": (
            "source://validation/pilot-onboarding-start"
        ),
        "payload": payload,
    }

    try:
        envelope_from_input(envelope)
    except EvidenceCollectionError as exc:
        print(
            f"ERROR: evidence envelope validation failed: {exc}",
            file=sys.stderr,
        )
        return 2

    inbox = Path(args.inbox).expanduser().resolve()
    inbox.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = inbox / (
        payload["onboarding_id"] + ".json"
    )

    if target.exists():
        print(
            f"ERROR: onboarding target already exists: {target}",
            file=sys.stderr,
        )
        return 2

    target.write_text(
        json.dumps(
            envelope,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    target.chmod(0o600)

    print(
        json.dumps(
            {
                "created": str(target),
                "onboarding_id": payload["onboarding_id"],
                "commitment_id": payload["commitment_id"],
                "merchant_ref": payload["merchant_ref"],
                "products": payload["products"],
                "pilot_status": "ACTIVE",
                "state": "READY_FOR_INBOX_PREFLIGHT",
                "onboarding_completion_claimed": False,
                "gate3_pass_claimed": False,
                "phase8": "BLOCKED",
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
