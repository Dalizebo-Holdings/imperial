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

from validation.evidence.collection import (  # noqa: E402
    DEFAULT_INBOX,
    EvidenceCollectionError,
    envelope_from_input,
)
from validation.evidence.store import (  # noqa: E402
    DurableEvidenceStore,
    EvidenceStoreError,
)

CRITERIA = (
    "active_retail_operations",
    "real_inventory",
    "real_customers",
    "transaction_volume_confirmed",
    "willingness_to_test",
    "structured_feedback_available",
)


def _read_ledger_rows(store: DurableEvidenceStore) -> list[dict]:
    if not store.path.exists():
        return []

    rows: list[dict] = []
    with store.path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise EvidenceStoreError(
                    f"invalid JSON at ledger line {line_number}"
                ) from exc
            if not isinstance(value, dict):
                raise EvidenceStoreError(
                    f"ledger line {line_number} is not an object"
                )
            rows.append(value)
    return rows


def _real_interviews(store: DurableEvidenceStore) -> list[dict]:
    result: list[dict] = []

    for value in _read_ledger_rows(store):
        if str(value.get("origin", "")).strip().upper() != "REAL_MERCHANT":
            continue
        if (
            str(value.get("evidence_type", "")).strip().upper()
            != "DISCOVERY_INTERVIEW"
        ):
            continue

        payload = value.get("payload", {})
        if not isinstance(payload, dict):
            continue

        merchant_ref = str(payload.get("merchant_ref", "")).strip()
        if not merchant_ref.startswith("merchant://"):
            continue

        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        item = {
            "merchant_ref": merchant_ref,
            "interview_id": str(payload.get("interview_id", "")),
            "merchant_segment": str(payload.get("merchant_segment", "")),
            "products": list(payload.get("products", [])),
            "core_problem_material": bool(
                payload.get("core_problem_material", False)
            ),
            "active_retail_operations": bool(
                metadata.get("active_retail_operations", False)
            ),
            "real_inventory": bool(metadata.get("real_inventory", False)),
            "real_customers": bool(metadata.get("real_customers", False)),
            "transaction_volume_confirmed": bool(
                metadata.get("transaction_volume_confirmed", False)
            ),
            "willingness_to_test": bool(
                payload.get("willingness_to_test", False)
            ),
            "structured_feedback_available": bool(
                payload.get("structured_feedback_available", False)
            ),
            "interview_evidence_ref": str(value.get("evidence_ref", "")),
        }

        missing = [
            criterion
            for criterion in CRITERIA
            if item[criterion] is not True
        ]
        item["eligible"] = not missing
        item["missing_criteria"] = missing
        result.append(item)

    result.sort(
        key=lambda item: (item["interview_id"], item["merchant_ref"])
    )
    return result


def _existing_commitment_merchants(
    store: DurableEvidenceStore,
) -> set[str]:
    merchants: set[str] = set()

    for value in _read_ledger_rows(store):
        if str(value.get("origin", "")).strip().upper() == "TEST_FIXTURE":
            continue
        if (
            str(value.get("evidence_type", "")).strip().upper()
            != "DESIGN_PARTNER_COMMITMENT"
        ):
            continue

        payload = value.get("payload", {})
        if not isinstance(payload, dict):
            continue

        merchant_ref = str(payload.get("merchant_ref", "")).strip()
        if merchant_ref:
            merchants.add(merchant_ref)

    return merchants


def _triage(store: DurableEvidenceStore) -> dict:
    committed = _existing_commitment_merchants(store)

    eligible: list[dict] = []
    discovery_only: list[dict] = []
    already_committed: list[dict] = []

    for item in _real_interviews(store):
        if item["merchant_ref"] in committed:
            already_committed.append(item)
        elif item["eligible"]:
            eligible.append(item)
        else:
            discovery_only.append(item)

    missing_frequency = {
        criterion: 0
        for criterion in CRITERIA
    }

    for item in discovery_only:
        for criterion in item["missing_criteria"]:
            missing_frequency[criterion] += 1

    recruitment_priority = [
        criterion
        for criterion, count in sorted(
            missing_frequency.items(),
            key=lambda pair: (-pair[1], pair[0]),
        )
        if count
    ]

    return {
        "eligible_count": len(eligible),
        "eligible": eligible,
        "discovery_only_count": len(discovery_only),
        "discovery_only": discovery_only,
        "already_committed_count": len(already_committed),
        "already_committed": already_committed,
        "recruitment_priority_missing_criteria": recruitment_priority,
        "discovery_target_deferred_not_waived": True,
    }


def _select(candidates: list[dict]) -> dict:
    if not candidates:
        raise SystemExit(
            "ERROR: no design-partner-eligible interviewed merchants found; "
            "review `list` and recruit against missing criteria"
        )

    print("Eligible interviewed merchants:")
    for index, item in enumerate(candidates, start=1):
        print(
            f"{index}. {item['merchant_segment']} | "
            f"{item['merchant_ref']} | "
            f"material={str(item['core_problem_material']).lower()}"
        )

    while True:
        raw = input("Select merchant number: ").strip()
        try:
            selected = int(raw)
        except ValueError:
            print("Enter a valid number.")
            continue

        if 1 <= selected <= len(candidates):
            return candidates[selected - 1]
        print("Selection is out of range.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Triage real Phase 7 discovery interviews and create "
            "design-partner commitments only for canonically eligible merchants."
        )
    )
    parser.add_argument("--ledger", help="override durable evidence ledger path")
    parser.add_argument(
        "--inbox",
        default=str(DEFAULT_INBOX),
        help="active evidence inbox",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("create")

    args = parser.parse_args()
    store = DurableEvidenceStore(args.ledger)

    try:
        triage = _triage(store)
    except EvidenceStoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.command == "list":
        print(json.dumps(triage, indent=2, sort_keys=True))
        return 0

    merchant = _select(triage["eligible"])

    failed = [
        criterion
        for criterion in CRITERIA
        if merchant[criterion] is not True
    ]
    if failed:
        print(
            "ERROR: merchant eligibility changed or is invalid: "
            + ", ".join(failed),
            file=sys.stderr,
        )
        return 3

    now = datetime.now().astimezone()
    commitment_uuid = uuid.uuid4().hex
    commitment_id = "commitment_" + commitment_uuid

    payload = {
        "commitment_id": commitment_id,
        "merchant_ref": merchant["merchant_ref"],
        "products": list(merchant["products"]),
        "committed_at": now.isoformat(),
        "active_retail_operations": True,
        "real_inventory": True,
        "real_customers": True,
        "transaction_volume_confirmed": True,
        "willingness_to_test": True,
        "structured_feedback_available": True,
        "pilot_status": "CANDIDATE",
        "evidence_ref": (
            "evidence://phase7/design-partner/" + commitment_uuid
        ),
        "metadata": {
            "linked_interview_id": merchant["interview_id"],
            "linked_interview_evidence_ref": merchant[
                "interview_evidence_ref"
            ],
            "eligibility_source": "INGESTED_DISCOVERY_INTERVIEW",
            "discovery_target_deferred_not_waived": True,
        },
    }

    envelope = {
        "envelope_id": (
            "design-partner-envelope-" + commitment_uuid
        ),
        "evidence_type": "DESIGN_PARTNER_COMMITMENT",
        "origin": "REAL_MERCHANT",
        "observed_at": now.isoformat(),
        "evidence_ref": (
            "evidence://phase7/design-partner-envelope/" + commitment_uuid
        ),
        "source_system_ref": (
            "source://validation/design-partner-eligibility-triage"
        ),
        "payload": payload,
    }

    try:
        envelope_from_input(envelope)
    except EvidenceCollectionError as exc:
        print(
            f"ERROR: generated commitment evidence is invalid: {exc}",
            file=sys.stderr,
        )
        return 2

    inbox = Path(args.inbox).expanduser().resolve()
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{commitment_id}.json"

    if target.exists():
        print(
            f"ERROR: evidence record already exists: {target}",
            file=sys.stderr,
        )
        return 2

    target.write_text(
        json.dumps(envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    target.chmod(0o600)

    print(
        json.dumps(
            {
                "created": str(target),
                "merchant_ref": merchant["merchant_ref"],
                "commitment_id": commitment_id,
                "pilot_status": "CANDIDATE",
                "state": "READY_FOR_INBOX_PREFLIGHT",
                "discovery_gate": "STILL_PENDING",
                "phase8": "BLOCKED",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
