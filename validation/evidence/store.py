from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import fcntl
import json
import os
import tempfile
from typing import Any

from .runtime import (
    EvidenceEnvelope,
    EvidenceIngestionError,
    EvidenceLedger,
    canonical_json,
)


DEFAULT_LEDGER_ENV = "DALIZEBO_VALIDATION_LEDGER"
DEFAULT_LEDGER_PATH = (
    Path.home()
    / ".local"
    / "share"
    / "dalizebo"
    / "imperial"
    / "validation"
    / "evidence-ledger.jsonl"
)


class EvidenceStoreError(ValueError):
    pass


def resolve_ledger_path(
    value: str | Path | None = None,
) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve()

    configured = os.environ.get(
        DEFAULT_LEDGER_ENV
    )
    if configured:
        return Path(
            configured
        ).expanduser().resolve()

    return DEFAULT_LEDGER_PATH


def envelope_from_mapping(
    value: dict[str, Any],
) -> EvidenceEnvelope:
    required = {
        "envelope_id",
        "evidence_type",
        "origin",
        "observed_at",
        "evidence_ref",
        "source_system_ref",
        "payload",
        "content_sha256",
    }

    missing = required - set(value)
    if missing:
        raise EvidenceStoreError(
            "evidence envelope missing fields: "
            + ", ".join(
                sorted(missing)
            )
        )

    extra = set(value) - required
    if extra:
        raise EvidenceStoreError(
            "evidence envelope contains unsupported fields: "
            + ", ".join(
                sorted(extra)
            )
        )

    payload = value["payload"]
    if not isinstance(
        payload,
        dict,
    ):
        raise EvidenceStoreError(
            "evidence payload must be a JSON object"
        )

    envelope = EvidenceEnvelope(
        envelope_id=value["envelope_id"],
        evidence_type=value["evidence_type"],
        origin=value["origin"],
        observed_at=value["observed_at"],
        evidence_ref=value["evidence_ref"],
        source_system_ref=value["source_system_ref"],
        payload=dict(payload),
        content_sha256=value["content_sha256"],
    )
    envelope.validate()
    return envelope


def envelope_to_mapping(
    envelope: EvidenceEnvelope,
) -> dict[str, Any]:
    return asdict(
        envelope
    )


class DurableEvidenceStore:
    """
    Durable append-only wrapper around EvidenceLedger.

    The runtime ledger remains the source of validation/decision semantics.
    This store persists canonical EvidenceEnvelope records as JSONL, rebuilds
    and verifies the chain on every open, and rewrites atomically only for
    maintenance/export operations.
    """

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:
        self.path = resolve_ledger_path(
            path
        )
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.lock_path = self.path.with_suffix(
            self.path.suffix
            + ".lock"
        )

    def initialize(self) -> Path:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.path.touch(
            exist_ok=True,
        )
        os.chmod(
            self.path,
            0o600,
        )
        self.lock_path.touch(
            exist_ok=True,
        )
        os.chmod(
            self.lock_path,
            0o600,
        )

        ledger = self.load()
        if not ledger.verify_chain():
            raise EvidenceStoreError(
                "evidence ledger failed verification during initialization"
            )
        return self.path

    def load(self) -> EvidenceLedger:
        ledger = EvidenceLedger()

        if not self.path.exists():
            return ledger

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line_number, raw in enumerate(
                handle,
                start=1,
            ):
                raw = raw.strip()
                if not raw:
                    continue

                try:
                    value = json.loads(
                        raw
                    )
                except json.JSONDecodeError as exc:
                    raise EvidenceStoreError(
                        f"invalid JSON at ledger line {line_number}"
                    ) from exc

                if not isinstance(
                    value,
                    dict,
                ):
                    raise EvidenceStoreError(
                        f"ledger line {line_number} must be a JSON object"
                    )

                try:
                    envelope = envelope_from_mapping(
                        value
                    )
                    result = ledger.ingest(
                        envelope
                    )
                except (
                    EvidenceStoreError,
                    EvidenceIngestionError,
                ) as exc:
                    raise EvidenceStoreError(
                        f"invalid evidence at ledger line {line_number}: {exc}"
                    ) from exc

                if result["created"] is not True:
                    raise EvidenceStoreError(
                        f"duplicate evidence at ledger line {line_number}"
                    )

        if not ledger.verify_chain():
            raise EvidenceStoreError(
                "reconstructed evidence ledger chain verification failed"
            )

        return ledger

    def append(
        self,
        envelope: EvidenceEnvelope,
    ) -> dict[str, Any]:
        envelope.validate()
        self.initialize()

        with self.lock_path.open(
            "r+",
            encoding="utf-8",
        ) as lock:
            fcntl.flock(
                lock.fileno(),
                fcntl.LOCK_EX,
            )
            try:
                ledger = self.load()
                result = ledger.ingest(
                    envelope
                )

                if result["created"] is False:
                    return {
                        "created": False,
                        "entry": result["entry"],
                        "path": self.path,
                    }

                record = (
                    canonical_json(
                        envelope_to_mapping(
                            result["entry"].envelope
                        )
                    )
                    + "\n"
                )

                with self.path.open(
                    "a",
                    encoding="utf-8",
                ) as handle:
                    handle.write(
                        record
                    )
                    handle.flush()
                    os.fsync(
                        handle.fileno()
                    )

                rebuilt = self.load()
                if not rebuilt.verify_chain():
                    raise EvidenceStoreError(
                        "evidence ledger verification failed after append"
                    )

                return {
                    "created": True,
                    "entry": result["entry"],
                    "path": self.path,
                }
            finally:
                fcntl.flock(
                    lock.fileno(),
                    fcntl.LOCK_UN,
                )

    def summary(self) -> dict[str, Any]:
        ledger = self.load()

        decision_eligible = 0
        fixture = 0

        if self.path.exists():
            with self.path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    value = json.loads(
                        raw
                    )
                    if (
                        str(
                            value.get(
                                "origin",
                                "",
                            )
                        ).strip().upper()
                        == "TEST_FIXTURE"
                    ):
                        fixture += 1
                    else:
                        decision_eligible += 1

        return {
            "path": str(
                self.path
            ),
            "count": ledger.count,
            "decision_eligible_count": (
                decision_eligible
            ),
            "fixture_count": fixture,
            "head_digest": ledger.head_digest,
            "chain_valid": ledger.verify_chain(),
        }

    def export_verified(
        self,
        target: str | Path,
    ) -> Path:
        ledger = self.load()
        if not ledger.verify_chain():
            raise EvidenceStoreError(
                "cannot export an invalid ledger"
            )

        target_path = Path(
            target
        ).expanduser().resolve()
        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        content = (
            self.path.read_text(
                encoding="utf-8"
            )
            if self.path.exists()
            else ""
        )

        fd, temp_name = tempfile.mkstemp(
            prefix=target_path.name + ".",
            dir=str(
                target_path.parent
            ),
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    content
                )
                handle.flush()
                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temp_name,
                target_path,
            )
            os.chmod(
                target_path,
                0o600,
            )
        finally:
            if os.path.exists(
                temp_name
            ):
                os.unlink(
                    temp_name
                )

        return target_path
