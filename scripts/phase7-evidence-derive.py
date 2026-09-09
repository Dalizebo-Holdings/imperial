#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.evidence.derive import (
    EvidenceDerivationError,
    derive_discovery_gate,
    emit_discovery_gate_proof,
)
from validation.evidence.store import (
    DurableEvidenceStore,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive canonical Phase 7 gates from the durable real-evidence ledger."
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

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    discovery = sub.add_parser(
        "discovery",
        help="derive the canonical discovery/design-partner gate",
    )
    discovery.add_argument(
        "--emit-proof",
        action="store_true",
        help=(
            "write a discovery GATE_PROOF to the evidence inbox; "
            "prohibited unless the canonical gate is PASS"
        ),
    )

    args = parser.parse_args()

    store = DurableEvidenceStore(
        args.ledger
    )

    try:
        if args.command == "discovery":
            derivation = derive_discovery_gate(
                store
            )

            result = {
                "derivation": derivation,
                "proof": None,
            }

            if args.emit_proof:
                result[
                    "proof"
                ] = emit_discovery_gate_proof(
                    derivation=derivation,
                    inbox=args.inbox,
                )

            print(
                json.dumps(
                    result,
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

    except EvidenceDerivationError as exc:
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
