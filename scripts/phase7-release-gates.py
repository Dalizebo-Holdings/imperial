#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

from validation.evidence.release_gate_derive import (  # noqa: E402
    ReleaseGateDerivationError,
    derive_release_gate_1,
    derive_release_gate_2,
    emit_release_gate_proof,
)
from validation.evidence.store import DurableEvidenceStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive canonical Phase 7 Release Gates 1/2 "
            "from durable real operational evidence."
        )
    )

    parser.add_argument(
        "--ledger",
        help="override durable evidence ledger path",
    )
    parser.add_argument(
        "--inbox",
        help="override active evidence inbox for proof emission",
    )
    parser.add_argument(
        "--evaluated-at",
        help="timezone-aware ISO timestamp; defaults to current local time",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for name in (
        "gate1",
        "gate2",
    ):
        command = sub.add_parser(
            name
        )
        command.add_argument(
            "--emit-proof",
            action="store_true",
            help="emit PASS-only canonical GATE_PROOF",
        )

    args = parser.parse_args()
    store = DurableEvidenceStore(
        args.ledger
    )

    try:
        if args.command == "gate1":
            derivation = derive_release_gate_1(
                store,
                evaluated_at=args.evaluated_at,
            )
        elif args.command == "gate2":
            derivation = derive_release_gate_2(
                store,
                evaluated_at=args.evaluated_at,
            )
        else:
            return 2

        proof = None

        if args.emit_proof:
            proof = emit_release_gate_proof(
                derivation,
                inbox=args.inbox,
            )

        print(
            json.dumps(
                {
                    "derivation": derivation,
                    "proof": proof,
                },
                indent=2,
                sort_keys=True,
            )
        )

        state = str(
            derivation[
                "gate"
            ].get(
                "state",
                "",
            )
        ).strip().upper()

        return (
            0
            if state == "PASS"
            else 3
        )

    except ReleaseGateDerivationError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
