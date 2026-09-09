#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.evidence.release_gate_derive import (  # noqa: E402
    ReleaseGateDerivationError,
    derive_release_gate_1,
    derive_release_gate_2,
)
from validation.evidence.store import DurableEvidenceStore  # noqa: E402
from validation.pilot_runtime import (  # noqa: E402
    GATE1_ATTESTATIONS,
    GATE2_ATTESTATIONS,
)


def _gate_report(
    *,
    number: int,
    derivation: dict,
) -> dict:
    gate = dict(
        derivation.get(
            "gate",
            {},
        )
    )

    checks = dict(
        gate.get(
            "checks",
            {},
        )
    )

    unmet = list(
        gate.get(
            "unmet",
            [],
        )
    )

    requirements = (
        sorted(
            GATE1_ATTESTATIONS
        )
        if number == 1
        else sorted(
            GATE2_ATTESTATIONS
        )
    )

    requirement_state = {}

    for requirement in requirements:
        passed = bool(
            checks.get(
                requirement,
                False,
            )
        )

        requirement_state[
            requirement
        ] = (
            "SATISFIED"
            if passed
            else "MISSING_FAILED_OR_EXPIRED"
        )

    state = str(
        gate.get(
            "state",
            "PENDING",
        )
    ).strip().upper()

    report = {
        "gate": number,
        "label": derivation.get(
            "label"
        ),
        "state": state,
        "evidence_digest": gate.get(
            "evidence_digest"
        ),
        "unmet": unmet,
        "technical_attestation_count": derivation.get(
            "technical_attestation_count",
            0,
        ),
        "required_attestations": requirements,
        "requirement_state": requirement_state,
        "proof_emission_allowed": (
            state == "PASS"
        ),
        "thresholds_waived": False,
        "fixture_evidence_excluded": True,
    }

    if number == 1:
        discovery = dict(
            derivation.get(
                "discovery_gate",
                {},
            )
        )

        discovery_state = str(
            discovery.get(
                "state",
                "PENDING",
            )
        ).strip().upper()

        report[
            "discovery_dependency"
        ] = {
            "state": discovery_state,
            "satisfied": (
                discovery_state
                == "PASS"
            ),
            "unmet": list(
                discovery.get(
                    "unmet",
                    [],
                )
            ),
        }

    pending_requirements = [
        requirement
        for requirement, status in requirement_state.items()
        if status
        != "SATISFIED"
    ]

    if number == 1 and not report[
        "discovery_dependency"
    ][
        "satisfied"
    ]:
        next_action = (
            "Discovery remains a canonical Gate 1 blocker. "
            "Continue real Discovery/design-partner evidence collection "
            "when practical; technical attestations may still be collected in parallel."
        )
    elif pending_requirements:
        next_action = (
            "Collect real supporting evidence and record one of the pending "
            "technical attestations with phase7-technical-attestation.py."
        )
    elif state != "PASS":
        next_action = (
            "Canonical evaluator still reports PENDING; inspect `unmet` "
            "before attempting proof emission."
        )
    else:
        next_action = (
            "Gate is PASS. PASS-only proof emission is now allowed."
        )

    report[
        "next_action"
    ] = next_action
    report[
        "pending_attestations"
    ] = pending_requirements

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Show canonical Phase 7 Release Gate 1/2 evidence readiness."
        )
    )

    parser.add_argument(
        "--ledger",
        help="override durable evidence ledger path",
    )
    parser.add_argument(
        "--gate",
        choices=(
            "1",
            "2",
            "all",
        ),
        default="all",
    )
    parser.add_argument(
        "--evaluated-at",
        help="timezone-aware ISO timestamp; defaults to current local time",
    )

    args = parser.parse_args()
    store = DurableEvidenceStore(
        args.ledger
    )

    reports = []

    try:
        if args.gate in {
            "1",
            "all",
        }:
            reports.append(
                _gate_report(
                    number=1,
                    derivation=derive_release_gate_1(
                        store,
                        evaluated_at=args.evaluated_at,
                    ),
                )
            )

        if args.gate in {
            "2",
            "all",
        }:
            reports.append(
                _gate_report(
                    number=2,
                    derivation=derive_release_gate_2(
                        store,
                        evaluated_at=args.evaluated_at,
                    ),
                )
            )

    except ReleaseGateDerivationError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    result = {
        "phase": 7,
        "release_gate_readiness": reports,
        "evidence_generated": False,
        "proof_generated": False,
        "phase8_authorized": False,
    }

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return (
        0
        if all(
            item[
                "state"
            ]
            == "PASS"
            for item in reports
        )
        else 3
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
