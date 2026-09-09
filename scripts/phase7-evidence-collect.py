#!/usr/bin/env python3
from __future__ import annotations

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

from validation.evidence.collection import (  # noqa: E402
    EvidenceCollectionError,
    create_record,
    ingest_inbox,
    initialize_inbox,
    preflight_inbox,
    progress,
    templates,
    workspace_status,
)
from validation.evidence.store import (  # noqa: E402
    DurableEvidenceStore,
    EvidenceStoreError,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 7 real-evidence inbox and batch ingestion"
        )
    )
    parser.add_argument(
        "--ledger",
        help="override durable evidence ledger path",
    )
    parser.add_argument(
        "--inbox",
        help="override private evidence inbox path",
    )
    parser.add_argument(
        "--template-library",
        help="override private evidence template-library path",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "init-inbox",
    )

    new_record = sub.add_parser(
        "new",
    )
    new_record.add_argument(
        "type",
        choices=sorted(
            templates()
        ),
    )
    new_record.add_argument(
        "name",
        help="simple output file name, with or without .json",
    )

    sub.add_parser(
        "workspace",
    )

    template = sub.add_parser(
        "template",
    )
    template.add_argument(
        "type",
        choices=sorted(
            templates()
        ),
    )

    sub.add_parser(
        "validate-inbox",
    )
    sub.add_parser(
        "ingest-inbox",
    )
    sub.add_parser(
        "progress",
    )

    args = parser.parse_args()
    store = DurableEvidenceStore(
        args.ledger
    )

    try:
        if args.command == "init-inbox":
            result = initialize_inbox(
                args.inbox,
                template_library=args.template_library,
            )
            print(
                json.dumps(
                    result,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "new":
            target = create_record(
                template_type=args.type,
                record_name=args.name,
                inbox=args.inbox,
                template_library=args.template_library,
            )
            print(
                json.dumps(
                    {
                        "created": str(
                            target
                        ),
                        "state": "PLACEHOLDERS_REQUIRE_REAL_EVIDENCE",
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "workspace":
            print(
                json.dumps(
                    workspace_status(
                        inbox=args.inbox,
                        template_library=args.template_library,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "template":
            print(
                json.dumps(
                    templates()[
                        args.type
                    ],
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "validate-inbox":
            result = preflight_inbox(
                store=store,
                inbox=args.inbox,
            )

            output = dict(
                result
            )
            output.pop(
                "envelopes",
                None,
            )

            print(
                json.dumps(
                    output,
                    indent=2,
                    sort_keys=True,
                )
            )
            return (
                0
                if result["valid"]
                else 2
            )

        if args.command == "ingest-inbox":
            result = ingest_inbox(
                store=store,
                inbox=args.inbox,
            )
            print(
                json.dumps(
                    result,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "progress":
            print(
                json.dumps(
                    progress(
                        store
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

    except (
        EvidenceCollectionError,
        EvidenceStoreError,
    ) as exc:
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
