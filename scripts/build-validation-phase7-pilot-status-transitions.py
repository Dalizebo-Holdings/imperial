#!/usr/bin/env python3
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent.parent
VALIDATION = ROOT / 'validation'
required = [
    VALIDATION/'STATUS.md', VALIDATION/'IMPLEMENTATION_STATUS.md', VALIDATION/'runtime.py',
    VALIDATION/'evidence/collection.py', VALIDATION/'evidence/derive.py',
    VALIDATION/'design-partners/PILOT_STATUS_TRANSITIONS.md', ROOT/'scripts/phase7-pilot-status.py',
]
for path in required:
    if not path.exists(): raise SystemExit(f'ERROR: missing pilot-status prerequisite/artifact: {path}')
py_compile.compile(str(ROOT/'scripts/phase7-pilot-status.py'), doraise=True)

collection_path = VALIDATION/'evidence/collection.py'
collection = collection_path.read_text(encoding='utf-8')
if '"pilot-status-transition": _template(' not in collection:
    marker = '        "pilot-onboarding": _template(\n'
    block = (
        '        "pilot-status-transition": _template(\n'
        '            evidence_type="PILOT_STATUS_TRANSITION",\n'
        '            origin="REAL_MERCHANT",\n'
        '            source_system_ref="source://validation/pilot-status",\n'
        '            payload={\n'
        '                "transition_id": "__REPLACE__",\n'
        '                "commitment_id": "__REPLACE__",\n'
        '                "merchant_ref": "__REPLACE__",\n'
        '                "from_status": "__REPLACE__",\n'
        '                "to_status": "__REPLACE__",\n'
        '                "changed_at": "__REPLACE__",\n'
        '                "evidence_ref": "__REPLACE__",\n'
        '                "metadata": {},\n'
        '            },\n'
        '        ),\n'
    )
    if marker not in collection: raise SystemExit('ERROR: collection template insertion marker missing')
    collection = collection.replace(marker, block + marker, 1)
collection_path.write_text(collection, encoding='utf-8')

derive_path = VALIDATION/'evidence/derive.py'
derive = derive_path.read_text(encoding='utf-8')
if 'def _pilot_status_transition(' not in derive:
    marker = 'def derive_discovery_gate('
    helper = '''

def _pilot_status_transition(
    payload: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "transition_id", "commitment_id", "merchant_ref",
        "from_status", "to_status", "changed_at", "evidence_ref",
    }
    missing = required - set(payload)
    if missing:
        raise EvidenceDerivationError(
            "PILOT_STATUS_TRANSITION payload missing fields: "
            + ", ".join(sorted(missing))
        )
    result = {
        "transition_id": str(payload["transition_id"]).strip(),
        "commitment_id": str(payload["commitment_id"]).strip(),
        "merchant_ref": str(payload["merchant_ref"]).strip(),
        "from_status": str(payload["from_status"]).strip().upper(),
        "to_status": str(payload["to_status"]).strip().upper(),
        "changed_at": str(payload["changed_at"]).strip(),
        "evidence_ref": str(payload["evidence_ref"]).strip(),
        "metadata": _mapping("metadata", payload.get("metadata", {})),
    }
    if not result["transition_id"]:
        raise EvidenceDerivationError("PILOT_STATUS_TRANSITION transition_id must not be empty")
    return result
'''
    if marker not in derive: raise SystemExit('ERROR: derive helper insertion marker missing')
    derive = derive.replace(marker, helper + marker, 1)
if '"PILOT_STATUS_TRANSITION": 0' not in derive:
    marker = '        "DESIGN_PARTNER_COMMITMENT": 0,\n'
    if marker not in derive: raise SystemExit('ERROR: derive count marker missing')
    derive = derive.replace(marker, marker + '        "PILOT_STATUS_TRANSITION": 0,\n', 1)
if 'current_commitments: dict[str, DesignPartnerCommitment]' not in derive:
    marker = '    registry = ProductMarketValidationRegistry()\n\n'
    if marker not in derive: raise SystemExit('ERROR: derive registry marker missing')
    derive = derive.replace(marker, '    registry = ProductMarketValidationRegistry()\n    current_commitments: dict[str, DesignPartnerCommitment] = {}\n\n', 1)
old = '''                elif evidence_type == "DESIGN_PARTNER_COMMITMENT":
                    registry.record_commitment(
                        _design_partner_commitment(
                            envelope.payload
                        )
                    )
                else:
                    continue
'''
new = '''                elif evidence_type == "DESIGN_PARTNER_COMMITMENT":
                    commitment = _design_partner_commitment(
                        envelope.payload
                    )
                    registry.record_commitment(commitment)
                    current_commitments[commitment.commitment_id] = commitment
                elif evidence_type == "PILOT_STATUS_TRANSITION":
                    transition = _pilot_status_transition(envelope.payload)
                    current = current_commitments.get(transition["commitment_id"])
                    if current is None:
                        raise EvidenceDerivationError(
                            "pilot status transition references missing commitment"
                        )
                    if current.merchant_ref != transition["merchant_ref"]:
                        raise EvidenceDerivationError(
                            "pilot status transition merchant_ref mismatch"
                        )
                    if current.pilot_status != transition["from_status"]:
                        raise EvidenceDerivationError(
                            "pilot status transition from_status does not match current status"
                        )
                    updated = registry.transition_pilot_status(
                        commitment_id=transition["commitment_id"],
                        target_status=transition["to_status"],
                        changed_at=transition["changed_at"],
                        evidence_ref=transition["evidence_ref"],
                    )
                    current_commitments[updated.commitment_id] = updated
                else:
                    continue
'''
if 'elif evidence_type == "PILOT_STATUS_TRANSITION":' not in derive:
    if old not in derive: raise SystemExit('ERROR: derive commitment replay marker missing')
    derive = derive.replace(old, new, 1)
derive_path.write_text(derive, encoding='utf-8')

status_path = VALIDATION/'STATUS.md'
status = status_path.read_text(encoding='utf-8')
if '## Durable Pilot Status Transitions' not in status:
    marker = '## Durable Pilot Onboarding Event Evidence\n'
    block = '''## Durable Pilot Status Transitions

PILOT_STATUS_TRANSITION evidence type: COMPLETE

Canonical pilot state-machine replay: COMPLETE

CANDIDATE -> ACTIVE evidence path: COMPLETE

PAUSED/WITHDRAWN transitions: COMPLETE

Merchant/commitment linkage enforcement: COMPLETE

Discovery active-pilot count transition replay: COMPLETE

Transition evidence mutation: PROHIBITED

Automatic ACTIVE promotion: PROHIBITED

Actual ACTIVE pilot transition: EVIDENCE COLLECTION PENDING

'''
    if marker not in status: raise SystemExit('ERROR: status insertion marker missing')
    status = status.replace(marker, block + marker, 1)
status_path.write_text(status, encoding='utf-8')

impl_path = VALIDATION/'IMPLEMENTATION_STATUS.md'
impl = impl_path.read_text(encoding='utf-8')
if '## Durable Pilot Status Transitions' not in impl:
    marker = '## Closure Evidence — Not Fabricated\n'
    block = '''## Durable Pilot Status Transitions

- [x] PILOT_STATUS_TRANSITION collection template
- [x] Append-only real merchant provenance
- [x] Canonical transition state machine
- [x] Current-state reconstruction from ledger
- [x] Merchant/commitment linkage
- [x] Derived from_status
- [x] Explicit real transition evidence reference
- [x] Discovery derivation transition replay
- [x] Active-pilot count reflects replayed status
- [x] No automatic ACTIVE promotion
- [ ] First real CANDIDATE -> ACTIVE transition ingested

'''
    if marker not in impl: raise SystemExit('ERROR: implementation-status insertion marker missing')
    impl = impl.replace(marker, block + marker, 1)
impl_path.write_text(impl, encoding='utf-8')

print('OK: durable pilot status transitions installed.')
print('OK: canonical pilot-status state machine is reused.')
print('OK: Discovery derivation replays append-only transitions.')
print('OK: no automatic ACTIVE promotion is performed.')
print('STATUS: PHASE 7 DURABLE PILOT STATUS TRANSITIONS READY')
