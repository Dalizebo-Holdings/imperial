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

from validation.evidence.collection import DEFAULT_INBOX, EvidenceCollectionError, envelope_from_input
from validation.evidence.store import DurableEvidenceStore
from validation.runtime import DesignPartnerCommitment, ProductMarketValidationRegistry, ValidationEvidenceError


def _products(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError('products must be an array')
    return tuple(str(item) for item in value)


def _mapping(value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError('metadata must be an object')
    return dict(value)


def _commitment(payload):
    required = {
        'commitment_id','merchant_ref','products','committed_at',
        'active_retail_operations','real_inventory','real_customers',
        'transaction_volume_confirmed','willingness_to_test',
        'structured_feedback_available','pilot_status','evidence_ref',
    }
    missing = required - set(payload)
    if missing:
        raise ValueError('DESIGN_PARTNER_COMMITMENT missing fields: ' + ', '.join(sorted(missing)))
    result = DesignPartnerCommitment(
        commitment_id=payload['commitment_id'], merchant_ref=payload['merchant_ref'],
        products=_products(payload['products']), committed_at=payload['committed_at'],
        active_retail_operations=payload['active_retail_operations'],
        real_inventory=payload['real_inventory'], real_customers=payload['real_customers'],
        transaction_volume_confirmed=payload['transaction_volume_confirmed'],
        willingness_to_test=payload['willingness_to_test'],
        structured_feedback_available=payload['structured_feedback_available'],
        pilot_status=payload['pilot_status'], evidence_ref=payload['evidence_ref'],
        metadata=_mapping(payload.get('metadata', {})),
    )
    result.validate()
    return result


def _transition(payload):
    required = {'transition_id','commitment_id','merchant_ref','from_status','to_status','changed_at','evidence_ref'}
    missing = required - set(payload)
    if missing:
        raise ValueError('PILOT_STATUS_TRANSITION missing fields: ' + ', '.join(sorted(missing)))
    return {
        'transition_id': str(payload['transition_id']).strip(),
        'commitment_id': str(payload['commitment_id']).strip(),
        'merchant_ref': str(payload['merchant_ref']).strip(),
        'from_status': str(payload['from_status']).strip().upper(),
        'to_status': str(payload['to_status']).strip().upper(),
        'changed_at': str(payload['changed_at']).strip(),
        'evidence_ref': str(payload['evidence_ref']).strip(),
    }


def _state(store):
    registry = ProductMarketValidationRegistry()
    current = {}
    transition_count = 0
    if not store.path.exists():
        return registry, current, transition_count
    with store.path.open('r', encoding='utf-8') as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f'invalid JSON at ledger line {line_number}') from exc
            if str(value.get('origin','')).strip().upper() == 'TEST_FIXTURE':
                continue
            evidence_type = str(value.get('evidence_type','')).strip().upper()
            payload = value.get('payload', {})
            if not isinstance(payload, dict):
                continue
            if evidence_type == 'DESIGN_PARTNER_COMMITMENT':
                item = _commitment(payload)
                registry.record_commitment(item)
                current[item.commitment_id] = item
            elif evidence_type == 'PILOT_STATUS_TRANSITION':
                tr = _transition(payload)
                before = current.get(tr['commitment_id'])
                if before is None:
                    raise ValueError('pilot status transition references missing commitment')
                if before.merchant_ref != tr['merchant_ref']:
                    raise ValueError('pilot status transition merchant_ref mismatch')
                if before.pilot_status != tr['from_status']:
                    raise ValueError('pilot status transition from_status does not match current status')
                updated = registry.transition_pilot_status(
                    commitment_id=tr['commitment_id'], target_status=tr['to_status'],
                    changed_at=tr['changed_at'], evidence_ref=tr['evidence_ref'])
                current[updated.commitment_id] = updated
                transition_count += 1
    return registry, current, transition_count


def _time(value):
    raw = value or datetime.now().astimezone().isoformat()
    try:
        parsed = datetime.fromisoformat(str(raw).strip())
    except ValueError as exc:
        raise ValueError('changed_at must be ISO-8601') from exc
    if parsed.tzinfo is None:
        raise ValueError('changed_at must be timezone-aware')
    return parsed.isoformat()


def _evidence_ref(value):
    result = str(value).strip()
    if not result.startswith('evidence://'):
        raise ValueError('--evidence-ref must use evidence://')
    lowered = result.lower()
    if any(marker in lowered for marker in ('__replace__','placeholder','example','todo','tbd')):
        raise ValueError('--evidence-ref contains placeholder material')
    return result


def main():
    parser = argparse.ArgumentParser(description='Record append-only Phase 7 pilot status transitions.')
    parser.add_argument('--ledger')
    parser.add_argument('--inbox', default=str(DEFAULT_INBOX))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    cmd = sub.add_parser('transition')
    cmd.add_argument('--commitment-id', required=True)
    cmd.add_argument('--target-status', required=True, choices=('ACTIVE','PAUSED','WITHDRAWN'))
    cmd.add_argument('--evidence-ref', required=True)
    cmd.add_argument('--changed-at')
    cmd.add_argument('--note')
    args = parser.parse_args()
    store = DurableEvidenceStore(args.ledger)
    try:
        registry, current, transition_count = _state(store)
    except (ValueError, ValidationEvidenceError) as exc:
        print(f'ERROR: cannot reconstruct pilot status state: {exc}', file=sys.stderr)
        return 2
    if args.command == 'list':
        items = [{'commitment_id': x.commitment_id, 'merchant_ref': x.merchant_ref,
                  'products': list(x.products), 'pilot_status': x.pilot_status}
                 for x in sorted(current.values(), key=lambda v: v.commitment_id)]
        print(json.dumps({'commitment_count': len(items), 'transition_count': transition_count,
                          'commitments': items}, indent=2, sort_keys=True))
        return 0
    commitment_id = str(args.commitment_id).strip()
    item = current.get(commitment_id)
    if item is None:
        print('ERROR: commitment_id is not an ingested real design-partner commitment', file=sys.stderr)
        return 2
    try:
        changed_at = _time(args.changed_at)
        supporting_ref = _evidence_ref(args.evidence_ref)
        updated = registry.transition_pilot_status(
            commitment_id=commitment_id, target_status=args.target_status,
            changed_at=changed_at, evidence_ref=supporting_ref)
    except (ValueError, ValidationEvidenceError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    identifier = uuid.uuid4().hex
    metadata = {'execution_source':'PHASE7_PILOT_STATUS_CLI'}
    if args.note:
        metadata['operator_note'] = str(args.note).strip()
    payload = {
        'transition_id':'pilot_transition_' + identifier,
        'commitment_id':item.commitment_id,
        'merchant_ref':item.merchant_ref,
        'from_status':item.pilot_status,
        'to_status':updated.pilot_status,
        'changed_at':changed_at,
        'evidence_ref':supporting_ref,
        'metadata':metadata,
    }
    envelope = {
        'envelope_id':'pilot-status-transition-envelope-' + identifier,
        'evidence_type':'PILOT_STATUS_TRANSITION', 'origin':'REAL_MERCHANT',
        'observed_at':changed_at,
        'evidence_ref':'evidence://phase7/pilot-status-transition-envelope/' + identifier,
        'source_system_ref':'source://validation/pilot-status', 'payload':payload,
    }
    try:
        envelope_from_input(envelope)
    except EvidenceCollectionError as exc:
        print(f'ERROR: evidence envelope validation failed: {exc}', file=sys.stderr)
        return 2
    inbox = Path(args.inbox).expanduser().resolve()
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{payload['transition_id']}.json"
    if target.exists():
        print(f'ERROR: transition target already exists: {target}', file=sys.stderr)
        return 2
    target.write_text(json.dumps(envelope, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    target.chmod(0o600)
    print(json.dumps({'created':str(target), 'transition_id':payload['transition_id'],
                      'commitment_id':payload['commitment_id'], 'merchant_ref':payload['merchant_ref'],
                      'from_status':payload['from_status'], 'to_status':payload['to_status'],
                      'state':'READY_FOR_INBOX_PREFLIGHT', 'discovery_gate_recompute_required':True,
                      'phase8':'BLOCKED'}, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
