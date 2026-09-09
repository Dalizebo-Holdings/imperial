from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Final, Protocol, override
from urllib.parse import urlsplit

from baas.webhooks.runtime import WebhooksBaaSError, validate_webhook_url

HTTPS_DEFAULT_PORT: Final = 443


@dataclass(frozen=True, slots=True)
class WebhookNetworkPolicyError(Exception):
    field: str
    reason: str

    @override
    def __str__(self) -> str:
        return f"{self.field}: {self.reason}"


class WebhookDNSResolver(Protocol):
    def resolve(self, *, hostname: str, port: int) -> tuple[str, ...]: ...


@dataclass(frozen=True, slots=True)
class ResolvedWebhookTarget:
    url: str
    hostname: str
    port: int
    addresses: tuple[str, ...]


def _public_address(raw_address: str) -> str:
    try:
        address = ip_address(raw_address)
    except ValueError as error:
        raise WebhookNetworkPolicyError(
            field="resolved_address",
            reason="must be a valid IP address",
        ) from error
    if not address.is_global or address.is_multicast:
        raise WebhookNetworkPolicyError(
            field="resolved_address",
            reason="must be globally routable",
        )
    return str(address)


@dataclass(frozen=True, slots=True)
class OutboundWebhookNetworkPolicy:
    def resolve_for_connection(
        self,
        *,
        url: str,
        resolver: WebhookDNSResolver,
    ) -> ResolvedWebhookTarget:
        try:
            validated_url = validate_webhook_url(url)
        except WebhooksBaaSError as error:
            raise WebhookNetworkPolicyError(
                field="url",
                reason=str(error),
            ) from error

        parsed = urlsplit(validated_url)
        hostname = parsed.hostname
        if hostname is None:
            raise WebhookNetworkPolicyError(
                field="hostname",
                reason="is required",
            )
        try:
            port = parsed.port or HTTPS_DEFAULT_PORT
        except ValueError as error:
            raise WebhookNetworkPolicyError(
                field="port",
                reason="must be within 1..65535",
            ) from error

        try:
            literal_address = ip_address(hostname)
        except ValueError:
            resolved = resolver.resolve(hostname=hostname, port=port)
        else:
            resolved = (str(literal_address),)

        if not resolved:
            raise WebhookNetworkPolicyError(
                field="resolved_addresses",
                reason="must not be empty",
            )

        addresses = tuple(
            dict.fromkeys(_public_address(address) for address in resolved)
        )
        return ResolvedWebhookTarget(
            url=validated_url,
            hostname=hostname,
            port=port,
            addresses=addresses,
        )

    def authorize_connected_peer(
        self,
        *,
        target: ResolvedWebhookTarget,
        peer_address: str,
    ) -> None:
        peer = _public_address(peer_address)
        if peer not in target.addresses:
            raise WebhookNetworkPolicyError(
                field="peer_address",
                reason="does not match the authorized DNS resolution",
            )
