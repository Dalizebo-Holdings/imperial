#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

from validation.evidence.runtime import (  # noqa: E402
    EvidenceEnvelope,
    payload_sha256,
)
from validation.evidence.store import (  # noqa: E402
    DurableEvidenceStore,
    EvidenceStoreError,
)


def _read_json(
    path: str,
) -> dict:
    source = Path(
        path
    ).expanduser().resolve()

    try:
        value = json.loads(
            source.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise SystemExit(
            f"ERROR: input file not found: {source}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"ERROR: invalid JSON in {source}: {exc}"
        ) from exc

    if not isinstance(
        value,
        dict,
    ):
        raise SystemExit(
            "ERROR: input must be a JSON object"
        )

    return value


def _envelope_from_input(
    value: dict,
) -> EvidenceEnvelope:
    required = {
        "envelope_id",
        "evidence_type",
        "origin",
        "observed_at",
        "evidence_ref",
        "source_system_ref",
        "payload",
    }

    missing = required - set(
        value
    )
    if missing:
        raise SystemExit(
            "ERROR: input missing fields: "
            + ", ".join(
                sorted(missing)
            )
        )

    allowed = (
        required
        | {
            "content_sha256",
        }
    )
    extra = set(
        value
    ) - allowed
    if extra:
        raise SystemExit(
            "ERROR: unsupported input fields: "
            + ", ".join(
                sorted(extra)
            )
        )

    payload = value[
        "payload"
    ]
    if not isinstance(
        payload,
        dict,
    ):
        raise SystemExit(
            "ERROR: payload must be a JSON object"
        )

    calculated = payload_sha256(
        payload
    )

    supplied = value.get(
        "content_sha256"
    )
    if (
        supplied is not None
        and str(
            supplied
        ).strip().lower()
        != calculated
    ):
        raise SystemExit(
            "ERROR: supplied content_sha256 does not match canonical payload"
        )

    return EvidenceEnvelope(
        envelope_id=value["envelope_id"],
        evidence_type=value["evidence_type"],
        origin=value["origin"],
        observed_at=value["observed_at"],
        evidence_ref=value["evidence_ref"],
        source_system_ref=value["source_system_ref"],
        payload=dict(
            payload
        ),
        content_sha256=calculated,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Durable Phase 7 validation evidence operations"
        )
    )
    parser.add_argument(
        "--ledger",
        help=(
            "ledger path; defaults to DALIZEBO_VALIDATION_LEDGER "
            "or ~/.local/share/dalizebo/imperial/validation/evidence-ledger.jsonl"
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "init",
    )

    ingest = sub.add_parser(
        "ingest",
    )
    ingest.add_argument(
        "input_json",
    )

    sub.add_parser(
        "verify",
    )
    sub.add_parser(
        "status",
    )

    export = sub.add_parser(
        "export",
    )
    export.add_argument(
        "target",
    )

    args = parser.parse_args()
    store = DurableEvidenceStore(
        args.ledger
    )

    try:
        if args.command == "init":
            path = store.initialize()
            print(
                f"OK: evidence ledger initialized: {path}"
            )
            return 0

        if args.command == "ingest":
            value = _read_json(
                args.input_json
            )
            envelope = _envelope_from_input(
                value
            )
            result = store.append(
                envelope
            )
            entry = result[
                "entry"
            ]
            print(
                "CREATED"
                if result["created"]
                else "REPLAY"
            )
            print(
                f"sequence={entry.sequence}"
            )
            print(
                f"evidence_ref={entry.envelope.evidence_ref}"
            )
            print(
                f"decision_eligible={str(entry.decision_eligible).lower()}"
            )
            print(
                f"chain_digest={entry.chain_digest}"
            )
            return 0

        if args.command == "verify":
            ledger = store.load()
            if not ledger.verify_chain():
                print(
                    "ERROR: evidence ledger chain invalid",
                    file=sys.stderr,
                )
                return 2

            print(
                "STATUS: PHASE 7 EVIDENCE LEDGER VERIFIED"
            )
            print(
                f"count={ledger.count}"
            )
            print(
                f"head_digest={ledger.head_digest}"
            )
            return 0

        if args.command == "status":
            print(
                json.dumps(
                    store.summary(),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "export":
            target = store.export_verified(
                args.target
            )
            print(
                f"OK: verified ledger exported: {target}"
            )
            return 0

    except EvidenceStoreError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
