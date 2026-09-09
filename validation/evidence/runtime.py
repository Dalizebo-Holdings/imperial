from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
import json
from typing import Any


ORIGINS = {
    "REAL_MERCHANT",
    "REAL_OPERATIONAL",
    "REAL_COMMERCIAL",
    "REAL_RELIABILITY",
    "TEST_FIXTURE",
}

SENSITIVE_TERMS = {
    "email",
    "phone",
    "mobile",
    "address",
    "password",
    "secret",
    "token",
    "api_key",
    "card",
    "pan",
    "cvv",
    "cvc",
    "bank",
    "account_number",
}


class EvidenceIngestionError(ValueError):
    pass


def _text(name: str, value: Any, *, max_length: int = 512) -> str:
    if value is None:
        raise EvidenceIngestionError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise EvidenceIngestionError(f"{name} must not be empty")
    if len(result) > max_length:
        raise EvidenceIngestionError(
            f"{name} exceeds {max_length} characters"
        )
    return result


def _time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(
            _text("observed_at", value, max_length=128)
        )
    except ValueError as exc:
        raise EvidenceIngestionError(
            "observed_at must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise EvidenceIngestionError(
            "observed_at must be timezone-aware"
        )

    return parsed.isoformat()


def _evidence_ref(value: str) -> str:
    result = _text("evidence_ref", value)
    if not result.startswith("evidence://"):
        raise EvidenceIngestionError(
            "evidence_ref must use evidence://"
        )
    return result


def _source_ref(value: str) -> str:
    result = _text("source_system_ref", value)
    if not result.startswith("source://"):
        raise EvidenceIngestionError(
            "source_system_ref must use source://"
        )
    return result


def _safe_payload(value: dict[str, Any]) -> None:
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                normalized = str(key).strip().lower()
                if any(term in normalized for term in SENSITIVE_TERMS):
                    raise EvidenceIngestionError(
                        "evidence payload contains sensitive/direct-contact field"
                    )
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EvidenceIngestionError(
            "evidence payload must be JSON-compatible"
        ) from exc

    if len(encoded) > 65536:
        raise EvidenceIngestionError(
            "evidence payload exceeds 65536 bytes"
        )

    walk(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def payload_sha256(payload: dict[str, Any]) -> str:
    _safe_payload(payload)
    return sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class EvidenceEnvelope:
    envelope_id: str
    evidence_type: str
    origin: str
    observed_at: str
    evidence_ref: str
    source_system_ref: str
    payload: dict[str, Any]
    content_sha256: str

    def validate(self) -> None:
        _text("envelope_id", self.envelope_id, max_length=128)
        _text("evidence_type", self.evidence_type, max_length=128)

        origin = str(self.origin).strip().upper()
        if origin not in ORIGINS:
            raise EvidenceIngestionError("unsupported evidence origin")

        _time(self.observed_at)
        evidence_ref = _evidence_ref(self.evidence_ref)
        _source_ref(self.source_system_ref)
        _safe_payload(self.payload)

        expected = payload_sha256(self.payload)

        digest = _text(
            "content_sha256",
            self.content_sha256,
            max_length=64,
        ).lower()

        if len(digest) != 64 or any(
            char not in "0123456789abcdef"
            for char in digest
        ):
            raise EvidenceIngestionError(
                "content_sha256 must be 64 lowercase hex characters"
            )

        if digest != expected:
            raise EvidenceIngestionError(
                "evidence payload SHA-256 mismatch"
            )

        if (
            origin != "TEST_FIXTURE"
            and (
                "/test/" in evidence_ref.lower()
                or evidence_ref.lower().startswith("evidence://test")
            )
        ):
            raise EvidenceIngestionError(
                "REAL evidence origin may not use an obvious test evidence_ref"
            )


@dataclass(frozen=True)
class EvidenceLedgerEntry:
    sequence: int
    envelope: EvidenceEnvelope
    previous_chain_digest: str
    chain_digest: str
    decision_eligible: bool


class EvidenceLedger:
    def __init__(self) -> None:
        self._entries: list[EvidenceLedgerEntry] = []
        self._by_id: dict[str, EvidenceLedgerEntry] = {}
        self._by_ref: dict[str, EvidenceLedgerEntry] = {}

    def ingest(
        self,
        envelope: EvidenceEnvelope,
    ) -> dict[str, Any]:
        envelope.validate()

        normalized = replace(
            envelope,
            origin=str(envelope.origin).strip().upper(),
            observed_at=_time(envelope.observed_at),
            evidence_ref=_evidence_ref(envelope.evidence_ref),
            source_system_ref=_source_ref(envelope.source_system_ref),
            payload=dict(envelope.payload),
            content_sha256=envelope.content_sha256.lower(),
        )

        existing = self._by_id.get(normalized.envelope_id)
        if existing is not None:
            if existing.envelope != normalized:
                raise EvidenceIngestionError(
                    "envelope_id already exists with different evidence"
                )
            return {
                "created": False,
                "entry": existing,
            }

        existing_ref = self._by_ref.get(normalized.evidence_ref)
        if existing_ref is not None:
            if existing_ref.envelope != normalized:
                raise EvidenceIngestionError(
                    "evidence_ref already bound to different evidence"
                )
            return {
                "created": False,
                "entry": existing_ref,
            }

        previous = (
            self._entries[-1].chain_digest
            if self._entries
            else "0" * 64
        )

        material = {
            "previous_chain_digest": previous,
            "envelope": asdict(normalized),
        }

        chain_digest = sha256(
            canonical_json(material).encode("utf-8")
        ).hexdigest()

        entry = EvidenceLedgerEntry(
            sequence=len(self._entries) + 1,
            envelope=normalized,
            previous_chain_digest=previous,
            chain_digest=chain_digest,
            decision_eligible=(
                normalized.origin != "TEST_FIXTURE"
            ),
        )

        self._entries.append(entry)
        self._by_id[normalized.envelope_id] = entry
        self._by_ref[normalized.evidence_ref] = entry

        return {
            "created": True,
            "entry": entry,
        }

    def require_decision_evidence(
        self,
        evidence_ref: str,
    ) -> EvidenceLedgerEntry:
        ref = _evidence_ref(evidence_ref)
        entry = self._by_ref.get(ref)

        if entry is None:
            raise EvidenceIngestionError(
                "decision evidence_ref is not present in the evidence ledger"
            )

        if not entry.decision_eligible:
            raise EvidenceIngestionError(
                "TEST_FIXTURE evidence is not decision-eligible"
            )

        return entry

    def require_digest_binding(
        self,
        *,
        evidence_ref: str,
        evidence_digest: str,
    ) -> EvidenceLedgerEntry:
        entry = self.require_decision_evidence(
            evidence_ref
        )

        expected = _text(
            "evidence_digest",
            evidence_digest,
            max_length=64,
        ).lower()

        bound = str(
            entry.envelope.payload.get(
                "evidence_digest",
                ""
            )
        ).strip().lower()

        if bound != expected:
            raise EvidenceIngestionError(
                "evidence_ref is not bound to the supplied evidence_digest"
            )

        return entry

    def verify_chain(self) -> bool:
        previous = "0" * 64

        for index, entry in enumerate(
            self._entries,
            start=1,
        ):
            if (
                entry.sequence != index
                or entry.previous_chain_digest
                != previous
            ):
                return False

            material = {
                "previous_chain_digest": previous,
                "envelope": asdict(
                    entry.envelope
                ),
            }

            expected = sha256(
                canonical_json(
                    material
                ).encode(
                    "utf-8"
                )
            ).hexdigest()

            if entry.chain_digest != expected:
                return False

            previous = entry.chain_digest

        return True

    @property
    def head_digest(self) -> str:
        return (
            self._entries[-1].chain_digest
            if self._entries
            else "0" * 64
        )

    @property
    def count(self) -> int:
        return len(self._entries)
