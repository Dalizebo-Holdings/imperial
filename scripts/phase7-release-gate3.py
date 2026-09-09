#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.evidence.gate3_derive import (  # noqa: E402
    Gate3DerivationError,
    derive_release_gate_3,
    emit_release_gate_3_proof,
    reconstruct_gate3_registry,
)
from validation.evidence.store import DurableEvidenceStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive canonical Phase 7 Release Gate 3 "
            "from durable real pilot evidence."
        )
    )
    parser.add_argument("--ledger")
    parser.add_argument("--inbox")

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "sources",
        help="list available real metric/capacity sources",
    )

    derive = sub.add_parser(
        "derive",
        help="derive canonical Gate 3 from explicit real snapshots",
    )
    derive.add_argument(
        "--snapshot-id",
        required=True,
    )
    derive.add_argument(
        "--capacity-snapshot-id",
        required=True,
    )
    derive.add_argument(
        "--evaluated-at",
    )
    derive.add_argument(
        "--emit-proof",
        action="store_true",
    )

    args = parser.parse_args()
    store = DurableEvidenceStore(
        args.ledger
    )

    try:
        if args.command == "sources":
            state = reconstruct_gate3_registry(
                store
            )
            result = {
                "metric_snapshot_ids": state[
                    "metric_snapshot_ids"
                ],
                "capacity_snapshot_ids": state[
                    "capacity_snapshot_ids"
                ],
                "current_commitments": state[
                    "current_commitments"
                ],
                "source_counts": state[
                    "source_counts"
                ],
                "fixture_evidence_excluded": True,
                "thresholds_waived": False,
                "phase8_authorized": False,
            }
            print(
                json.dumps(
                    result,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        derivation = derive_release_gate_3(
            store,
            snapshot_id=args.snapshot_id,
            capacity_snapshot_id=(
                args.capacity_snapshot_id
            ),
            evaluated_at=args.evaluated_at,
        )

        proof = None
        if args.emit_proof:
            proof = emit_release_gate_3_proof(
                derivation,
                inbox=args.inbox,
            )

        print(
            json.dumps(
                {
                    "derivation": derivation,
                    "proof": proof,
                    "phase8_authorized": False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        return (
            0
            if derivation["gate"]["state"] == "PASS"
            else 3
        )

    except Gate3DerivationError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
