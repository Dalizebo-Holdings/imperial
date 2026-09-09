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
from validation.evidence.store import (
    DurableEvidenceStore,
    EvidenceStoreError,
)


def _read_rows(store: DurableEvidenceStore):
    if not store.path.exists():
        return []

    rows = []
    with store.path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSON at ledger line {line_number}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"ledger line {line_number} must be an object"
                )
            value["_ledger_line"] = line_number
            rows.append(value)
    return rows


def _verified_rows(store: DurableEvidenceStore):
    try:
        ledger = store.load()
    except EvidenceStoreError as exc:
        raise ValueError(str(exc)) from exc

    if not ledger.verify_chain():
        raise ValueError("evidence ledger chain verification failed")

    return _read_rows(store)


def _existing_void_targets(rows):
    targets = set()
    for row in rows:
        if (
            str(row.get("evidence_type", "")).strip().upper()
            != "EVIDENCE_VOID"
        ):
            continue
        payload = row.get("payload", {})
        if isinstance(payload, dict):
            target = str(
                payload.get("target_envelope_id", "")
            ).strip()
            if target:
                targets.add(target)
    return targets


def _target_by_event_id(rows, event_id):
    matches = []
    for row in rows:
        if (
            str(row.get("origin", "")).strip().upper()
            == "TEST_FIXTURE"
        ):
            continue
        if (
            str(row.get("evidence_type", "")).strip().upper()
            != "PILOT_ONBOARDING_EVENT"
        ):
            continue
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if str(payload.get("event_id", "")).strip() == event_id:
            matches.append(row)

    if not matches:
        raise ValueError(
            "event_id is not an ingested real PILOT_ONBOARDING_EVENT"
        )
    if len(matches) != 1:
        raise ValueError(
            "event_id is not unique in durable evidence"
        )
    return matches[0]


def _evidence_ref(value):
    result = str(value).strip()
    if not result.startswith("evidence://"):
        raise ValueError("--evidence-ref must use evidence://")
    lower = result.lower()
    if any(
        marker in lower
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


def _reason(value):
    result = " ".join(str(value).split())
    if len(result) < 12:
        raise ValueError(
            "--reason must clearly explain the correction"
        )
    if len(result) > 1000:
        raise ValueError("--reason exceeds 1000 characters")
    return result


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Append an EVIDENCE_VOID for an erroneous real "
            "PILOT_ONBOARDING_EVENT."
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

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--event-id", required=True)

    void = sub.add_parser("void")
    void.add_argument("--event-id", required=True)
    void.add_argument("--reason", required=True)
    void.add_argument("--evidence-ref", required=True)
    void.add_argument("--voided-at")

    args = parser.parse_args()
    store = DurableEvidenceStore(args.ledger)

    try:
        rows = _verified_rows(store)
        event_id = str(args.event_id).strip()
        target = _target_by_event_id(rows, event_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    target_payload = target.get("payload", {})
    target_envelope_id = str(
        target.get("envelope_id", "")
    ).strip()
    target_digest = str(
        target.get("content_sha256", "")
    ).strip().lower()

    if not target_envelope_id:
        print(
            "ERROR: target envelope_id is missing",
            file=sys.stderr,
        )
        return 2

    if len(target_digest) != 64:
        print(
            "ERROR: target content_sha256 is missing/invalid",
            file=sys.stderr,
        )
        return 2

    already_voided = (
        target_envelope_id
        in _existing_void_targets(rows)
    )

    summary = {
        "event_id": event_id,
        "ledger_line": target.get("_ledger_line"),
        "onboarding_id": target_payload.get("onboarding_id"),
        "step": target_payload.get("step"),
        "status": target_payload.get("status"),
        "occurred_at": target_payload.get("occurred_at"),
        "target_envelope_id": target_envelope_id,
        "target_content_sha256": target_digest,
        "already_voided": already_voided,
        "ledger_mutation_required": False,
        "phase8_authorized": False,
    }

    if args.command == "inspect":
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if already_voided:
        print(
            "ERROR: target envelope already has EVIDENCE_VOID",
            file=sys.stderr,
        )
        return 3

    try:
        reason = _reason(args.reason)
        evidence_ref = _evidence_ref(args.evidence_ref)

        raw_time = (
            args.voided_at
            or datetime.now().astimezone().isoformat()
        )
        parsed_time = datetime.fromisoformat(
            str(raw_time).strip()
        )
        if parsed_time.tzinfo is None:
            raise ValueError(
                "--voided-at must be timezone-aware"
            )
        voided_at = parsed_time.isoformat()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    identifier = uuid.uuid4().hex
    payload = {
        "void_id": "evidence_void_" + identifier,
        "target_envelope_id": target_envelope_id,
        "target_evidence_type": "PILOT_ONBOARDING_EVENT",
        "target_event_id": event_id,
        "target_content_sha256": target_digest,
        "reason": reason,
        "voided_at": voided_at,
        "evidence_ref": evidence_ref,
        "metadata": {
            "correction_mode": "APPEND_ONLY_VOID",
            "original_ledger_line": target.get("_ledger_line"),
        },
    }

    envelope = {
        "envelope_id": "evidence-void-envelope-" + identifier,
        "evidence_type": "EVIDENCE_VOID",
        "origin": "REAL_OPERATIONAL",
        "observed_at": voided_at,
        "evidence_ref": (
            "evidence://phase7/evidence-void-envelope/"
            + identifier
        ),
        "source_system_ref": (
            "source://validation/evidence-void"
        ),
        "payload": payload,
    }

    try:
        envelope_from_input(envelope)
    except EvidenceCollectionError as exc:
        print(
            f"ERROR: generated EVIDENCE_VOID is invalid: {exc}",
            file=sys.stderr,
        )
        return 2

    inbox = Path(args.inbox).expanduser().resolve()
    inbox.mkdir(parents=True, exist_ok=True)

    target_file = inbox / (
        payload["void_id"] + ".json"
    )
    if target_file.exists():
        print(
            f"ERROR: void file already exists: {target_file}",
            file=sys.stderr,
        )
        return 2

    target_file.write_text(
        json.dumps(
            envelope,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    target_file.chmod(0o600)

    print(
        json.dumps(
            {
                **summary,
                "created": str(target_file),
                "void_id": payload["void_id"],
                "state": "READY_FOR_INBOX_PREFLIGHT",
                "gate_pass_claimed": False,
                "phase8": "BLOCKED",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
