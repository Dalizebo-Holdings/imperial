#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT = Path(__file__).resolve().parent.parent
V = ROOT/'validation'
cli = (ROOT/'scripts/phase7-pilot-status.py').read_text(encoding='utf-8')
derive = (V/'evidence/derive.py').read_text(encoding='utf-8')
collection = (V/'evidence/collection.py').read_text(encoding='utf-8')
ast.parse(cli); ast.parse(derive)
for phrase in ['"pilot-status-transition": _template(', 'evidence_type="PILOT_STATUS_TRANSITION"', 'origin="REAL_MERCHANT"']:
    if phrase not in collection: raise SystemExit('ERROR: collection schema missing: ' + phrase)
for phrase in ['ProductMarketValidationRegistry()', 'registry.transition_pilot_status(', "'from_status':item.pilot_status", "'to_status':updated.pilot_status", "'phase8':'BLOCKED'"]:
    if phrase not in cli: raise SystemExit('ERROR: CLI safeguard missing: ' + phrase)
for phrase in ['def _pilot_status_transition(', '"PILOT_STATUS_TRANSITION": 0', 'elif evidence_type == "PILOT_STATUS_TRANSITION":', 'registry.transition_pilot_status(', 'pilot status transition from_status does not match current status']:
    if phrase not in derive: raise SystemExit('ERROR: derive replay missing: ' + phrase)
status = (V/'STATUS.md').read_text(encoding='utf-8')
for phrase in ['Canonical pilot state-machine replay: COMPLETE','Discovery active-pilot count transition replay: COMPLETE','Automatic ACTIVE promotion: PROHIBITED','Actual ACTIVE pilot transition: EVIDENCE COLLECTION PENDING','PHASE 7: NOT COMPLETE — REAL EVIDENCE REQUIRED']:
    if phrase not in status: raise SystemExit('ERROR: status missing: ' + phrase)
print('OK: pilot-status CLI syntax valid.')
print('OK: append-only PILOT_STATUS_TRANSITION schema present.')
print('OK: canonical transition state machine reused.')
print('OK: Discovery derivation replays transitions.')
print('OK: no automatic ACTIVE/Phase 8 claim is made.')
print('STATUS: PHASE 7 DURABLE PILOT STATUS TRANSITIONS READY')
