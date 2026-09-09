#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "runtime.py",
    VALIDATION / "evidence/runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/derive.py",
    VALIDATION / "evidence/DISCOVERY_GATE_DERIVATION.md",
    ROOT / "scripts/phase7-evidence-derive.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing evidence-derivation prerequisite/artifact: {path}"
        )

for path in [
    VALIDATION / "evidence/derive.py",
    ROOT / "scripts/phase7-evidence-derive.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

derive_source = (
    VALIDATION
    / "evidence/derive.py"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "ProductMarketValidationRegistry",
    "registry.discovery_gate()",
    '== "TEST_FIXTURE"',
    "thresholds_waived",
    "GATE_PROOF emission is prohibited",
    '"label": "discovery"',
    '"state": "PASS"',
    "source_ledger_head_digest",
    "source_evidence_refs",
]:
    if phrase not in derive_source:
        raise SystemExit(
            "ERROR: evidence-derivation safeguard missing: "
            + phrase
        )

status_path = (
    VALIDATION
    / "STATUS.md"
)
status = status_path.read_text(
    encoding="utf-8"
)

if "## Durable Discovery Gate Derivation" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Durable Discovery Gate Derivation

Durable ledger -> canonical Discovery registry reconstruction: COMPLETE

Decision-eligible evidence filtering: COMPLETE

TEST_FIXTURE exclusion: COMPLETE

Discovery/design-partner payload validation: COMPLETE

Canonical Discovery Gate derivation: COMPLETE

PASS-only discovery GATE_PROOF emission: COMPLETE

Evidence-digest + ledger-head + source-reference binding: COMPLETE

Discovery threshold waiver: PROHIBITED

Actual discovery GATE_PROOF: PENDING REAL EVIDENCE

"""
    if marker not in status:
        raise SystemExit(
            "ERROR: status insertion marker missing"
        )
    status = status.replace(
        marker,
        block + marker,
        1,
    )

old_next = (
    "Continue merchant discovery when practical. In parallel, eligible interviewed "
    "merchants may enter the design-partner candidate flow with "
    "`scripts/phase7-design-partner.py`; the Discovery target remains deferred, "
    "not waived."
)

new_next = (
    "Continue validation in parallel. Use `scripts/phase7-evidence-derive.py discovery` "
    "to inspect the durable real-evidence Discovery Gate. A discovery GATE_PROOF "
    "may be emitted only when the canonical gate returns PASS; the target remains "
    "deferred, not waived."
)

if old_next in status:
    status = status.replace(
        old_next,
        new_next,
        1,
    )

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = (
    VALIDATION
    / "IMPLEMENTATION_STATUS.md"
)
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Durable Discovery Gate Derivation" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Durable Discovery Gate Derivation

- [x] Durable evidence reconstruction
- [x] Decision-eligible-only filtering
- [x] TEST_FIXTURE exclusion
- [x] DiscoveryInterview canonical payload validation
- [x] DesignPartnerCommitment canonical payload validation
- [x] Existing ProductMarketValidationRegistry reuse
- [x] Canonical discovery_gate computation
- [x] PASS-only GATE_PROOF emission
- [x] Evidence digest binding
- [x] Ledger head binding
- [x] Source evidence reference binding
- [x] Deferred target cannot be waived
- [ ] Real discovery GATE_PROOF ingested

"""
    if marker not in impl:
        raise SystemExit(
            "ERROR: implementation-status insertion marker missing"
        )
    impl = impl.replace(
        marker,
        block + marker,
        1,
    )

impl_path.write_text(
    impl,
    encoding="utf-8",
)

print("OK: durable evidence -> canonical Discovery Gate derivation installed.")
print("OK: TEST_FIXTURE evidence is excluded.")
print("OK: Discovery thresholds remain authoritative.")
print("OK: GATE_PROOF emission is PASS-only.")
print("STATUS: PHASE 7 DISCOVERY GATE DERIVATION READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE STILL REQUIRED")
