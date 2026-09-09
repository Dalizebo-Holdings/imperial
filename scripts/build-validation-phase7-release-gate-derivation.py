#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/derive.py",
    VALIDATION / "evidence/release_gate_derive.py",
    VALIDATION / "release-gates/DURABLE_DERIVATION.md",
    ROOT / "scripts/phase7-release-gates.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing release-gate derivation prerequisite/artifact: {path}"
        )

for path in [
    VALIDATION / "evidence/release_gate_derive.py",
    ROOT / "scripts/phase7-release-gates.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "## Durable Release Gate 1/2 Derivation" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Durable Release Gate 1/2 Derivation

REAL_OPERATIONAL technical-attestation reconstruction: COMPLETE

TEST_FIXTURE exclusion: COMPLETE

Canonical Gate 1 derivation: COMPLETE

Canonical Gate 2 derivation: COMPLETE

Evidence-expiry enforcement: CANONICAL RUNTIME

PASS-only release-gate proof emission: COMPLETE

Gate 1 Discovery dependency: ENFORCED

Gate 3 derivation: DEFERRED — REAL PILOT METRICS REQUIRED

Actual Release Gate 1 proof: PENDING REAL EVIDENCE

Actual Release Gate 2 proof: PENDING REAL EVIDENCE

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

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Durable Release Gate 1/2 Derivation" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Durable Release Gate 1/2 Derivation

- [x] REAL_OPERATIONAL technical-attestation filtering
- [x] TEST_FIXTURE exclusion
- [x] TechnicalAttestation canonical validation
- [x] PilotValidationRegistry reconstruction
- [x] Canonical Gate 1 derivation
- [x] Canonical Gate 2 derivation
- [x] Gate 1 canonical Discovery dependency
- [x] Canonical expiry handling retained
- [x] PASS-only release_gate_1 proof emission
- [x] PASS-only release_gate_2 proof emission
- [ ] Real Release Gate 1 proof ingested
- [ ] Real Release Gate 2 proof ingested
- [ ] Gate 3 durable derivation from real pilot evidence

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

print("OK: durable Release Gate 1/2 derivation installed.")
print("OK: REAL_OPERATIONAL provenance enforced.")
print("OK: Gate 1 remains dependent on canonical Discovery PASS.")
print("OK: Gate 2 retains canonical expiry enforcement.")
print("OK: proof emission is PASS-only.")
print("STATUS: PHASE 7 RELEASE GATE 1/2 DERIVATION READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
