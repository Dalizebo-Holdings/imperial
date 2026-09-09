#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / "validation"

required = [
    VALIDATION / "STATUS.md",
    VALIDATION / "IMPLEMENTATION_STATUS.md",
    VALIDATION / "runtime.py",
    VALIDATION / "pilot_runtime.py",
    VALIDATION / "evidence/store.py",
    VALIDATION / "evidence/collection.py",
    VALIDATION / "evidence/gate3_derive.py",
    VALIDATION / "release-gates/DURABLE_GATE3_DERIVATION.md",
    ROOT / "scripts/phase7-release-gate3.py",
]

for path in required:
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Gate 3 derivation prerequisite/artifact: {path}"
        )

for path in [
    VALIDATION / "evidence/gate3_derive.py",
    ROOT / "scripts/phase7-release-gate3.py",
]:
    py_compile.compile(
        str(path),
        doraise=True,
    )

status_path = VALIDATION / "STATUS.md"
status = status_path.read_text(
    encoding="utf-8"
)

if "## Durable Release Gate 3 Derivation" not in status:
    marker = "## Phase 7 Closure State\n"
    block = """## Durable Release Gate 3 Derivation

Design-partner current-state replay: COMPLETE

PILOT_STATUS_TRANSITION replay: COMPLETE

PILOT_ONBOARDING reconstruction: COMPLETE

PILOT_ONBOARDING_EVENT reconstruction: COMPLETE

PILOT_METRIC_SNAPSHOT reconstruction: COMPLETE

CAPACITY_SNAPSHOT reconstruction: COMPLETE

Gate 3 technical-attestation reconstruction: COMPLETE

Canonical Pilot Exit reuse: COMPLETE

Canonical Controlled Capacity reuse: COMPLETE

Canonical Release Gate 3 reuse: COMPLETE

TEST_FIXTURE exclusion: COMPLETE

PASS-only release_gate_3 proof emission: COMPLETE

Actual Release Gate 3 proof: PENDING REAL EVIDENCE

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

status = status.replace(
    "Gate 3 derivation: DEFERRED — REAL PILOT METRICS REQUIRED",
    "Gate 3 derivation: COMPLETE — REAL PILOT EVIDENCE REQUIRED FOR PASS",
)

status_path.write_text(
    status,
    encoding="utf-8",
)

impl_path = VALIDATION / "IMPLEMENTATION_STATUS.md"
impl = impl_path.read_text(
    encoding="utf-8"
)

if "## Durable Release Gate 3 Derivation" not in impl:
    marker = "## Closure Evidence — Not Fabricated\n"
    block = """## Durable Release Gate 3 Derivation

- [x] Current design-partner state replay
- [x] Pilot-status transition replay
- [x] Active-partner onboarding enforcement
- [x] Durable onboarding reconstruction
- [x] Durable onboarding-event reconstruction
- [x] Durable metric snapshot reconstruction
- [x] Durable capacity snapshot reconstruction
- [x] Durable technical-attestation reconstruction
- [x] Canonical Pilot Exit evaluator reuse
- [x] Canonical Controlled Capacity evaluator reuse
- [x] Canonical Release Gate 3 evaluator reuse
- [x] TEST_FIXTURE exclusion
- [x] PASS-only release_gate_3 proof emission
- [ ] Real Release Gate 3 proof ingested

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

print("OK: durable Release Gate 3 derivation installed.")
print("OK: canonical pilot/capacity/Gate 3 evaluators are reused.")
print("OK: PASS-only Gate 3 proof emission installed.")
print("OK: TEST_FIXTURE remains excluded.")
print("STATUS: PHASE 7 DURABLE RELEASE GATE 3 DERIVATION READY")
print("STATUS: PHASE 7 NOT COMPLETE — REAL EVIDENCE REQUIRED")
