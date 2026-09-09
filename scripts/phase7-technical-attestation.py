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
    sys.path.insert(
        0,
        str(ROOT),
    )

from validation.evidence.collection import (  # noqa: E402
    DEFAULT_INBOX,
    EvidenceCollectionError,
    envelope_from_input,
)
from validation.pilot_runtime import (  # noqa: E402
    GATE1_ATTESTATIONS,
    GATE2_ATTESTATIONS,
    PilotValidationError,
    TechnicalAttestation,
)


REQUIREMENT_GATE = {
    requirement: 1
    for requirement in GATE1_ATTESTATIONS
}
REQUIREMENT_GATE.update({
    requirement: 2
    for requirement in GATE2_ATTESTATIONS
})


def _time(
    name: str,
    value: str,
) -> str:
    try:
        parsed = datetime.fromisoformat(
            str(
                value
            ).strip()
        )
    except ValueError as exc:
        raise ValueError(
            f"{name} must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
            f"{name} must be timezone-aware"
        )

    return parsed.isoformat()


def _satisfied(
    value: str,
) -> bool:
    normalized = str(
        value
    ).strip().lower()

    if normalized in {
        "yes",
        "y",
        "true",
        "1",
    }:
        return True

    if normalized in {
        "no",
        "n",
        "false",
        "0",
    }:
        return False

    raise ValueError(
        "--satisfied must be yes or no"
    )


def _evidence_ref(
    value: str,
) -> str:
    result = str(
        value
    ).strip()

    if not result.startswith(
        "evidence://"
    ):
        raise ValueError(
            "--evidence-ref must use evidence://"
        )

    lowered = result.lower()

    for placeholder in (
        "__replace__",
        "placeholder",
        "example",
        "todo",
        "tbd",
    ):
        if placeholder in lowered:
            raise ValueError(
                "--evidence-ref contains placeholder material"
            )

    if len(
        result
    ) <= len(
        "evidence://"
    ):
        raise ValueError(
            "--evidence-ref must identify real supporting evidence"
        )

    return result


def _requirements(
    gate: str,
) -> dict:
    if gate == "1":
        requirements = sorted(
            GATE1_ATTESTATIONS
        )
    elif gate == "2":
        requirements = sorted(
            GATE2_ATTESTATIONS
        )
    else:
        requirements = sorted(
            REQUIREMENT_GATE
        )

    return {
        "gate": (
            gate
            if gate in {
                "1",
                "2",
            }
            else "all"
        ),
        "requirements": [
            {
                "requirement": requirement,
                "gate": REQUIREMENT_GATE[
                    requirement
                ],
            }
            for requirement in requirements
        ],
        "count": len(
            requirements
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record real Phase 7 Release Gate 1/2 technical attestations."
        )
    )

    parser.add_argument(
        "--inbox",
        default=str(
            DEFAULT_INBOX
        ),
        help="active private evidence inbox",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    requirements = sub.add_parser(
        "requirements",
        help="list canonical Gate 1/2 technical-attestation requirements",
    )
    requirements.add_argument(
        "--gate",
        choices=(
            "1",
            "2",
            "all",
        ),
        default="all",
    )

    record = sub.add_parser(
        "record",
        help="record one real operational technical attestation",
    )
    record.add_argument(
        "requirement",
        help="canonical requirement name",
    )
    record.add_argument(
        "--satisfied",
        required=True,
        help="yes or no",
    )
    record.add_argument(
        "--evidence-ref",
        required=True,
        help="real supporting evidence:// reference",
    )
    record.add_argument(
        "--observed-at",
        help="timezone-aware ISO-8601; defaults to current local time",
    )
    record.add_argument(
        "--valid-until",
        help="optional timezone-aware ISO-8601 expiry",
    )
    record.add_argument(
        "--note",
        help="optional non-sensitive operator note",
    )

    args = parser.parse_args()

    if args.command == "requirements":
        print(
            json.dumps(
                _requirements(
                    args.gate
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    requirement = str(
        args.requirement
    ).strip().upper()

    if requirement not in REQUIREMENT_GATE:
        print(
            "ERROR: unsupported Gate 1/2 requirement. Run `requirements`.",
            file=sys.stderr,
        )
        return 2

    try:
        satisfied = _satisfied(
            args.satisfied
        )
        supporting_ref = _evidence_ref(
            args.evidence_ref
        )

        observed_at = _time(
            "observed_at",
            (
                args.observed_at
                or datetime.now().astimezone().isoformat()
            ),
        )

        valid_until = (
            _time(
                "valid_until",
                args.valid_until,
            )
            if args.valid_until
            else None
        )

        if (
            valid_until is not None
            and datetime.fromisoformat(
                valid_until
            )
            < datetime.fromisoformat(
                observed_at
            )
        ):
            raise ValueError(
                "valid_until precedes observed_at"
            )
    except ValueError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    identifier = uuid.uuid4().hex

    metadata = {
        "gate": REQUIREMENT_GATE[
            requirement
        ],
        "execution_source": (
            "PHASE7_TECHNICAL_ATTESTATION_CLI"
        ),
    }

    if args.note:
        metadata[
            "operator_note"
        ] = str(
            args.note
        ).strip()

    payload = {
        "attestation_id": (
            "attestation_"
            + identifier
        ),
        "requirement": requirement,
        "satisfied": satisfied,
        "observed_at": observed_at,
        "evidence_ref": supporting_ref,
        "valid_until": valid_until,
        "metadata": metadata,
    }

    try:
        TechnicalAttestation(
            attestation_id=payload[
                "attestation_id"
            ],
            requirement=payload[
                "requirement"
            ],
            satisfied=payload[
                "satisfied"
            ],
            observed_at=payload[
                "observed_at"
            ],
            evidence_ref=payload[
                "evidence_ref"
            ],
            valid_until=payload[
                "valid_until"
            ],
            metadata=payload[
                "metadata"
            ],
        ).validate()
    except PilotValidationError as exc:
        print(
            f"ERROR: canonical attestation validation failed: {exc}",
            file=sys.stderr,
        )
        return 2

    envelope = {
        "envelope_id": (
            "technical-attestation-envelope-"
            + identifier
        ),
        "evidence_type": (
            "TECHNICAL_ATTESTATION"
        ),
        "origin": (
            "REAL_OPERATIONAL"
        ),
        "observed_at": observed_at,
        "evidence_ref": (
            "evidence://phase7/technical-attestation-envelope/"
            + identifier
        ),
        "source_system_ref": (
            "source://validation/release-gates"
        ),
        "payload": payload,
    }

    try:
        envelope_from_input(
            envelope
        )
    except EvidenceCollectionError as exc:
        print(
            f"ERROR: evidence envelope validation failed: {exc}",
            file=sys.stderr,
        )
        return 2

    inbox = Path(
        args.inbox
    ).expanduser().resolve()

    inbox.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = (
        inbox
        / (
            payload[
                "attestation_id"
            ]
            + ".json"
        )
    )

    if target.exists():
        print(
            f"ERROR: attestation target already exists: {target}",
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
    target.chmod(
        0o600
    )

    print(
        json.dumps(
            {
                "created": str(
                    target
                ),
                "attestation_id": payload[
                    "attestation_id"
                ],
                "requirement": requirement,
                "gate": REQUIREMENT_GATE[
                    requirement
                ],
                "satisfied": satisfied,
                "supporting_evidence_ref": (
                    supporting_ref
                ),
                "valid_until": valid_until,
                "origin": "REAL_OPERATIONAL",
                "state": (
                    "READY_FOR_INBOX_PREFLIGHT"
                ),
                "gate_pass_claimed": False,
                "phase8": "BLOCKED",
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
