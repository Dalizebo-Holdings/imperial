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


def yes_no(prompt: str) -> bool:
    while True:
        raw = input(
            f"{prompt} [y/n]: "
        ).strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Enter y or n.")


def text(prompt: str) -> str:
    while True:
        value = input(
            f"{prompt}: "
        ).strip()
        if value:
            return value
        print("A non-empty answer is required.")


def products_prompt() -> tuple[str, ...]:
    while True:
        raw = input(
            "Products relevant to merchant [commerce/pos/both]: "
        ).strip().lower()

        if raw == "commerce":
            return ("COMMERCE",)
        if raw == "pos":
            return ("POS",)
        if raw == "both":
            return ("COMMERCE", "POS")

        print("Enter commerce, pos, or both.")


def safe_notes(value: str) -> str:
    lowered = value.lower()

    prohibited_markers = (
        "password:",
        "secret:",
        "api_key:",
        "api key:",
        "cvv:",
        "cvc:",
        "card number:",
        "bank account:",
    )

    if any(
        marker in lowered
        for marker in prohibited_markers
    ):
        raise SystemExit(
            "ERROR: notes appear to contain credential/payment-sensitive material"
        )

    if len(value) > 2000:
        raise SystemExit(
            "ERROR: notes exceed 2000 characters"
        )

    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Conduct a real Phase 7 merchant discovery interview "
            "and create a ready evidence record."
        )
    )
    parser.add_argument(
        "--inbox",
        default=str(DEFAULT_INBOX),
        help="active evidence inbox",
    )
    parser.add_argument(
        "--segment",
        help="merchant segment; prompted when omitted",
    )
    parser.add_argument(
        "--products",
        choices=("commerce", "pos", "both"),
        help="product scope; prompted when omitted",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show resulting envelope without writing it",
    )

    args = parser.parse_args()

    print("Phase 7 Merchant Discovery Interview")
    print("Do not collect passwords, card data, bank details or customer PII.")
    print()

    segment = (
        args.segment.strip()
        if args.segment
        else text("Merchant segment")
    )

    if args.products == "commerce":
        products = ("COMMERCE",)
    elif args.products == "pos":
        products = ("POS",)
    elif args.products == "both":
        products = ("COMMERCE", "POS")
    else:
        products = products_prompt()

    print()
    active_retail = yes_no(
        "Does the merchant have active retail/business operations?"
    )
    real_inventory = yes_no(
        "Does the merchant manage real inventory/stock?"
    )
    real_customers = yes_no(
        "Does the merchant serve real paying customers?"
    )
    transaction_volume = yes_no(
        "Does the merchant have recurring transaction volume?"
    )

    print()
    primary_problem = safe_notes(
        text(
            "What current problem causes the most time/money/sales/inventory/payment/customer impact?"
        )
    )
    problem_frequency = safe_notes(
        text(
            "How often does this problem occur?"
        )
    )
    business_impact = safe_notes(
        text(
            "What is the business impact?"
        )
    )
    workaround = safe_notes(
        text(
            "What workaround does the merchant use today?"
        )
    )

    print()
    material = yes_no(
        "Did the merchant describe this as a material current business problem?"
    )
    willing = yes_no(
        "Did the merchant explicitly agree they would test Commerce/POS?"
    )
    feedback = yes_no(
        "Did the merchant explicitly agree to provide structured pilot feedback?"
    )

    extra_notes = input(
        "Optional non-sensitive interview notes: "
    ).strip()
    extra_notes = safe_notes(
        extra_notes
    )

    now = datetime.now().astimezone()
    interview_uuid = uuid.uuid4().hex
    interview_id = (
        "interview_"
        + interview_uuid
    )
    merchant_ref = (
        "merchant://phase7/"
        + uuid.uuid4().hex
    )
    domain_evidence_ref = (
        "evidence://phase7/discovery/"
        + interview_uuid
    )
    envelope_evidence_ref = (
        "evidence://phase7/discovery-envelope/"
        + interview_uuid
    )

    payload = {
        "interview_id": interview_id,
        "merchant_ref": merchant_ref,
        "merchant_segment": segment,
        "conducted_at": now.isoformat(),
        "products": list(products),
        "core_problem_material": material,
        "willingness_to_test": willing,
        "structured_feedback_available": feedback,
        "evidence_ref": domain_evidence_ref,
        "metadata": {
            "active_retail_operations": active_retail,
            "real_inventory": real_inventory,
            "real_customers": real_customers,
            "transaction_volume_confirmed": transaction_volume,
            "primary_problem": primary_problem,
            "problem_frequency": problem_frequency,
            "business_impact": business_impact,
            "existing_workaround": workaround,
            "interviewer_notes": extra_notes,
        },
    }

    envelope = {
        "envelope_id": (
            "discovery-envelope-"
            + interview_uuid
        ),
        "evidence_type": "DISCOVERY_INTERVIEW",
        "origin": "REAL_MERCHANT",
        "observed_at": now.isoformat(),
        "evidence_ref": envelope_evidence_ref,
        "source_system_ref": (
            "source://validation/live-discovery-interview"
        ),
        "payload": payload,
    }

    # Reuse the canonical collection validator before writing.
    try:
        envelope_from_input(
            envelope
        )
    except EvidenceCollectionError as exc:
        print(
            f"ERROR: generated interview evidence is invalid: {exc}",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        print(
            json.dumps(
                envelope,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    inbox = Path(
        args.inbox
    ).expanduser().resolve()
    inbox.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = (
        inbox
        / f"{interview_id}.json"
    )

    if target.exists():
        print(
            f"ERROR: evidence record already exists: {target}",
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
                "interview_id": interview_id,
                "merchant_ref": merchant_ref,
                "core_problem_material": material,
                "willingness_to_test": willing,
                "structured_feedback_available": feedback,
                "state": (
                    "READY_FOR_INBOX_PREFLIGHT"
                ),
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
