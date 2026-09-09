#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
# ─── How to run ───
# uv run scripts/validate-phase8-webhook-network-policy.py
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baas.webhooks.network_policy import (
    OutboundWebhookNetworkPolicy,
    WebhookNetworkPolicyError,
)


@dataclass(frozen=True, slots=True)
class StaticResolver:
    addresses: tuple[str, ...]

    def resolve(self, *, hostname: str, port: int) -> tuple[str, ...]:
        if hostname != "hooks.example.com" or port != 443:
            raise AssertionError("unexpected DNS resolution target")
        return self.addresses


policy = OutboundWebhookNetworkPolicy()
target = policy.resolve_for_connection(
    url="https://hooks.example.com/events",
    resolver=StaticResolver(("1.1.1.1", "2606:4700:4700::1111")),
)

if target.hostname != "hooks.example.com" or target.port != 443:
    raise SystemExit("ERROR: webhook connection target was not normalized")
if target.addresses != ("1.1.1.1", "2606:4700:4700::1111"):
    raise SystemExit("ERROR: public DNS addresses were not preserved")

policy.authorize_connected_peer(target=target, peer_address="1.1.1.1")

rebound_peer_rejected = False
try:
    policy.authorize_connected_peer(target=target, peer_address="10.0.0.8")
except WebhookNetworkPolicyError:
    rebound_peer_rejected = True
if not rebound_peer_rejected:
    raise SystemExit("ERROR: DNS-rebound webhook peer was accepted")

mixed_resolution_rejected = False
try:
    _ = policy.resolve_for_connection(
        url="https://hooks.example.com/events",
        resolver=StaticResolver(("1.1.1.1", "127.0.0.1")),
    )
except WebhookNetworkPolicyError:
    mixed_resolution_rejected = True
if not mixed_resolution_rejected:
    raise SystemExit("ERROR: mixed public/private DNS resolution was accepted")

multicast_resolution_rejected = False
try:
    _ = policy.resolve_for_connection(
        url="https://hooks.example.com/events",
        resolver=StaticResolver(("224.0.0.1",)),
    )
except WebhookNetworkPolicyError:
    multicast_resolution_rejected = True
if not multicast_resolution_rejected:
    raise SystemExit("ERROR: multicast DNS resolution was accepted")

empty_resolution_rejected = False
try:
    _ = policy.resolve_for_connection(
        url="https://hooks.example.com/events",
        resolver=StaticResolver(()),
    )
except WebhookNetworkPolicyError:
    empty_resolution_rejected = True
if not empty_resolution_rejected:
    raise SystemExit("ERROR: empty DNS resolution was accepted")

invalid_resolution_rejected = False
try:
    _ = policy.resolve_for_connection(
        url="https://hooks.example.com/events",
        resolver=StaticResolver(("not-an-ip",)),
    )
except WebhookNetworkPolicyError:
    invalid_resolution_rejected = True
if not invalid_resolution_rejected:
    raise SystemExit("ERROR: malformed DNS response was accepted")

literal = policy.resolve_for_connection(
    url="https://1.1.1.1/events",
    resolver=StaticResolver(()),
)
if literal.addresses != ("1.1.1.1",):
    raise SystemExit("ERROR: public IP literal was not pinned")
policy.authorize_connected_peer(target=literal, peer_address="1.1.1.1")

print("OK: webhook DNS resolution allows only public addresses")
print("OK: mixed and empty DNS results fail closed")
print("OK: connected peers are pinned to the authorized resolution")
print("OK: public HTTPS IP literals remain supported")
print("STATUS: PHASE 8 WEBHOOK NETWORK POLICY READY")
