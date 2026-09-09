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

from validation.decision.runtime import (  # noqa: E402
    GateProof,
    PMFDecisionEngine,
    PublicMVP90DaySnapshot,
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


def _snapshot(
    value: dict,
) -> PublicMVP90DaySnapshot:
    allowed = {
        "snapshot_id",
        "period_start",
        "period_end",
        "activated_organizations",
        "monthly_transacting_organizations",
        "active_three_consecutive_months",
        "logo_start_count",
        "logo_churned_count",
        "first_transaction_eligible_organizations",
        "first_transaction_within_24h",
        "weekly_usage_eligible_organizations",
        "weekly_active_organizations",
        "payment_reconciliation_total",
        "payment_reconciliation_matches",
        "uptime_total_minutes",
        "uptime_available_minutes",
        "p95_core_api_latency_ms",
        "checkout_api_p95_ms",
        "paying_customers",
        "customer_references",
        "critical_tenant_isolation_defects",
        "backup_restore_test_passed",
        "evidence_refs",
    }

    missing = allowed - set(
        value
    )
    if missing:
        raise SystemExit(
            "ERROR: Public MVP snapshot missing fields: "
            + ", ".join(
                sorted(missing)
            )
        )

    extra = set(
        value
    ) - allowed
    if extra:
        raise SystemExit(
            "ERROR: Public MVP snapshot unsupported fields: "
            + ", ".join(
                sorted(extra)
            )
        )

    normalized = dict(
        value
    )
    normalized[
        "evidence_refs"
    ] = tuple(
        normalized[
            "evidence_refs"
        ]
    )

    return PublicMVP90DaySnapshot(
        **normalized
    )


def _proofs(
    value: dict,
) -> tuple[GateProof, ...]:
    raw = value.get(
        "proofs"
    )
    if not isinstance(
        raw,
        list,
    ):
        raise SystemExit(
            "ERROR: proof manifest requires a proofs array"
        )

    proofs = []
    allowed = {
        "label",
        "state",
        "evidence_digest",
        "evidence_ref",
    }

    for index, item in enumerate(
        raw
    ):
        if not isinstance(
            item,
            dict,
        ):
            raise SystemExit(
                f"ERROR: proof[{index}] must be an object"
            )

        missing = allowed - set(
            item
        )
        extra = set(
            item
        ) - allowed

        if missing:
            raise SystemExit(
                f"ERROR: proof[{index}] missing: "
                + ", ".join(
                    sorted(missing)
                )
            )
        if extra:
            raise SystemExit(
                f"ERROR: proof[{index}] unsupported: "
                + ", ".join(
                    sorted(extra)
                )
            )

        proofs.append(
            GateProof(
                **item
            )
        )

    return tuple(
        proofs
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Phase 7 PMF evidence and closure state"
        )
    )
    parser.add_argument(
        "proof_manifest",
        nargs="?",
    )
    parser.add_argument(
        "--ledger",
    )
    parser.add_argument(
        "--public-mvp-snapshot",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
    )

    args = parser.parse_args()
    engine = PMFDecisionEngine()

    if args.public_mvp_snapshot:
        value = _read_json(
            args.public_mvp_snapshot
        )
        snapshot = _snapshot(
            value
        )
        result = engine.public_mvp_gate(
            snapshot
        )

        print(
            json.dumps(
                asdict(
                    result
                ),
                indent=2,
                sort_keys=True,
            )
        )

        if args.proof_manifest is None:
            return (
                0
                if result.state == "PASS"
                else 3
            )

    if args.proof_manifest is None:
        parser.error(
            "proof_manifest is required unless only --public-mvp-snapshot is used"
        )

    manifest = _read_json(
        args.proof_manifest
    )
    proofs = _proofs(
        manifest
    )

    store = DurableEvidenceStore(
        args.ledger
    )

    try:
        ledger = store.load()
    except EvidenceStoreError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    result = engine.phase7_decision(
        ledger=ledger,
        proofs=proofs,
    )

    print(
        json.dumps(
            asdict(
                result
            ),
            indent=2,
            sort_keys=True,
        )
    )

    if (
        args.require_complete
        and result.state
        != "PHASE7_COMPLETE"
    ):
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
