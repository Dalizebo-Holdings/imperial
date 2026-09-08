from __future__ import annotations

from dataclasses import replace

try:
    from .connector_model import ConnectorDefinition
except ImportError:
    from connector_model import ConnectorDefinition


class ConnectorRegistryError(ValueError):
    pass


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[tuple[str, str], ConnectorDefinition] = {}

    def register(
        self,
        connector: ConnectorDefinition,
        *,
        replace_existing: bool = False,
    ) -> None:
        connector.validate()
        key = (connector.connector_id, connector.version)

        if key in self._connectors and not replace_existing:
            raise ConnectorRegistryError(
                f"connector already registered: {connector.connector_id}@{connector.version}"
            )

        self._connectors[key] = replace(connector)

    def get(
        self,
        connector_id: str,
        version: str,
    ) -> ConnectorDefinition:
        key = (str(connector_id).strip(), str(version).strip())
        connector = self._connectors.get(key)

        if connector is None:
            raise ConnectorRegistryError(
                f"unknown connector: {key[0]}@{key[1]}"
            )

        return replace(connector)

    def resolve_compatible(
        self,
        connector_id: str,
        requested_version: str,
    ) -> ConnectorDefinition:
        connector_id = str(connector_id).strip()
        requested_version = str(requested_version).strip()

        exact = self._connectors.get(
            (connector_id, requested_version)
        )

        if exact is not None:
            return replace(exact)

        candidates = [
            connector
            for (cid, _), connector in self._connectors.items()
            if cid == connector_id
            and requested_version in connector.compatible_versions
        ]

        if not candidates:
            raise ConnectorRegistryError(
                f"no compatible connector for {connector_id}@{requested_version}"
            )

        candidates.sort(key=lambda item: item.version)
        return replace(candidates[-1])

    def disable(
        self,
        connector_id: str,
        version: str,
    ) -> None:
        connector = self.get(connector_id, version)
        connector.enabled = False
        self._connectors[(connector_id, version)] = connector

    def enable(
        self,
        connector_id: str,
        version: str,
    ) -> None:
        connector = self.get(connector_id, version)
        connector.enabled = True
        self._connectors[(connector_id, version)] = connector

    def list_connectors(self) -> list[ConnectorDefinition]:
        return [
            replace(connector)
            for connector in sorted(
                self._connectors.values(),
                key=lambda item: (item.connector_id, item.version),
            )
        ]
