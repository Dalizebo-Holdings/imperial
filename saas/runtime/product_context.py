from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


PRODUCTS = {
    "COMMERCE",
    "POS",
}

ACTIONS = {
    "CREATE",
    "READ",
    "UPDATE",
    "TRANSITION",
    "EXECUTE",
}

MUTATION_ACTIONS = {
    "CREATE",
    "UPDATE",
    "TRANSITION",
    "EXECUTE",
}

SHARED_ENTITIES = {
    "ORGANIZATION",
    "WORKSPACE",
    "USER",
    "ROLE",
    "STORE",
    "BRANCH",
    "PRODUCT",
    "PRODUCT_VARIANT",
    "INVENTORY_ITEM",
    "CUSTOMER",
    "CART",
    "ORDER",
    "ORDER_ITEM",
    "PAYMENT",
    "REFUND",
    "DISCOUNT",
    "AUDIT_EVENT",
}

AUTHORITY_ROUTES = {
    "ORGANIZATION": (
        "kernel.tenant",
        "baas.database",
    ),
    "WORKSPACE": (
        "kernel.tenant",
        "baas.database",
    ),
    "USER": (
        "kernel.identity",
        "baas.authentication",
    ),
    "ROLE": (
        "kernel.authorization",
        "baas.authentication",
    ),
    "STORE": (
        "kernel.commerce",
        "baas.database",
    ),
    "BRANCH": (
        "kernel.commerce",
        "baas.database",
    ),
    "PRODUCT": (
        "kernel.commerce",
        "baas.database",
    ),
    "PRODUCT_VARIANT": (
        "kernel.commerce",
        "baas.database",
    ),
    "INVENTORY_ITEM": (
        "kernel.commerce",
        "baas.database",
    ),
    "CUSTOMER": (
        "kernel.commerce",
        "baas.database",
    ),
    "CART": (
        "kernel.commerce",
        "baas.database",
    ),
    "ORDER": (
        "kernel.commerce",
        "baas.database",
    ),
    "ORDER_ITEM": (
        "kernel.commerce",
        "baas.database",
    ),
    "PAYMENT": (
        "kernel.commerce",
        "baas.payment_abstraction",
    ),
    "REFUND": (
        "kernel.commerce",
        "baas.payment_abstraction",
    ),
    "DISCOUNT": (
        "kernel.commerce",
        "baas.database",
    ),
    "AUDIT_EVENT": (
        "kernel.audit",
        "baas.audit",
    ),
}

COMMERCE_STORE_REQUIRED = {
    "BRANCH",
    "INVENTORY_ITEM",
    "CART",
    "ORDER",
    "ORDER_ITEM",
    "PAYMENT",
    "REFUND",
    "DISCOUNT",
}

POS_BRANCH_REQUIRED = {
    "PRODUCT",
    "PRODUCT_VARIANT",
    "INVENTORY_ITEM",
    "CUSTOMER",
    "CART",
    "ORDER",
    "ORDER_ITEM",
    "PAYMENT",
    "REFUND",
    "DISCOUNT",
    "AUDIT_EVENT",
}

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "secret",
    "secret_value",
    "client_secret",
    "private_key",
    "session_token",
    "webhook_secret",
    "provider_credentials",
    "card_number",
    "cardholder",
    "cvv",
    "cvc",
    "pan",
    "expiry",
}


class SaaSFoundationError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise SaaSFoundationError(
            f"{name} must not be empty"
        )

    result = str(value).strip()

    if not result:
        raise SaaSFoundationError(
            f"{name} must not be empty"
        )

    return result


def _contains_sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if (
                str(key).strip().lower()
                in SENSITIVE_KEYS
            ):
                return True

            if _contains_sensitive(item):
                return True

    elif isinstance(value, (list, tuple)):
        return any(
            _contains_sensitive(item)
            for item in value
        )

    return False


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise SaaSFoundationError(
            "command metadata must be JSON-compatible"
        ) from exc


def _validate_metadata(
    value: dict[str, Any],
) -> None:
    encoded = _canonical(
        value
    ).encode("utf-8")

    if len(encoded) > 16384:
        raise SaaSFoundationError(
            "command metadata exceeds 16384 bytes"
        )

    if _contains_sensitive(
        value
    ):
        raise SaaSFoundationError(
            "command metadata contains secret-bearing fields"
        )


@dataclass(frozen=True)
class ProductContext:
    product: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    actor_id: str
    actor_type: str
    kernel_authorization_ref: str
    correlation_id: str
    store_id: str | None = None
    branch_id: str | None = None

    def validate(self) -> None:
        product = str(
            self.product
        ).strip().upper()

        if product not in PRODUCTS:
            raise SaaSFoundationError(
                f"unsupported product: {product}"
            )

        for name, value in {
            "organization_id": (
                self.organization_id
            ),
            "workspace_id": (
                self.workspace_id
            ),
            "project_id": (
                self.project_id
            ),
            "environment_id": (
                self.environment_id
            ),
            "actor_id": (
                self.actor_id
            ),
            "actor_type": (
                self.actor_type
            ),
            "kernel_authorization_ref": (
                self.kernel_authorization_ref
            ),
            "correlation_id": (
                self.correlation_id
            ),
        }.items():
            _text(
                name,
                value,
            )

        if not str(
            self.kernel_authorization_ref
        ).startswith(
            "kernel_auth_"
        ):
            raise SaaSFoundationError(
                "product operations require Kernel authorization evidence"
            )

        if self.store_id is not None:
            _text(
                "store_id",
                self.store_id,
            )

        if self.branch_id is not None:
            _text(
                "branch_id",
                self.branch_id,
            )

        if (
            self.branch_id is not None
            and self.store_id is None
        ):
            raise SaaSFoundationError(
                "branch context requires store context"
            )


@dataclass(frozen=True)
class SharedEntityRef:
    entity_type: str
    entity_id: str

    def validate(self) -> None:
        entity = str(
            self.entity_type
        ).strip().upper()

        if entity not in SHARED_ENTITIES:
            raise SaaSFoundationError(
                f"unsupported shared entity: {entity}"
            )

        _text(
            "entity_id",
            self.entity_id,
        )


@dataclass(frozen=True)
class ProductCommand:
    action: str
    entity_type: str
    context: ProductContext
    idempotency_key: str | None
    input_metadata: dict[str, Any]
    entity_id: str | None = None

    def validate(self) -> None:
        self.context.validate()

        action = str(
            self.action
        ).strip().upper()

        if action not in ACTIONS:
            raise SaaSFoundationError(
                f"unsupported command action: {action}"
            )

        entity = str(
            self.entity_type
        ).strip().upper()

        if entity not in SHARED_ENTITIES:
            raise SaaSFoundationError(
                f"unsupported shared entity: {entity}"
            )

        if (
            action != "CREATE"
            and self.entity_id is None
        ):
            raise SaaSFoundationError(
                "existing-entity command requires entity_id"
            )

        if self.entity_id is not None:
            _text(
                "entity_id",
                self.entity_id,
            )

        if action in MUTATION_ACTIONS:
            _text(
                "idempotency_key",
                self.idempotency_key,
            )

        _validate_metadata(
            self.input_metadata
        )

        product = str(
            self.context.product
        ).strip().upper()

        if (
            product == "COMMERCE"
            and entity in COMMERCE_STORE_REQUIRED
            and self.context.store_id is None
        ):
            raise SaaSFoundationError(
                f"Commerce {entity} command requires store context"
            )

        if (
            product == "POS"
            and entity in POS_BRANCH_REQUIRED
            and self.context.branch_id is None
        ):
            raise SaaSFoundationError(
                f"POS {entity} command requires branch context"
            )


@dataclass(frozen=True)
class PlatformCommandPlan:
    command_id: str
    product: str
    action: str
    entity_type: str
    entity_id: str | None
    authority: str
    baas_service: str
    tenant_context: dict[str, str]
    store_id: str | None
    branch_id: str | None
    actor_id: str
    actor_type: str
    correlation_id: str
    idempotency_key: str | None
    kernel_authorization_ref: str
    input_metadata: dict[str, Any]
    audit_event: dict[str, Any]
    state: str = (
        "READY_FOR_PLATFORM_CONTRACT_ADAPTER"
    )


class CommercePOSFoundation:
    def __init__(self) -> None:
        self._idempotency: dict[
            tuple[str, str, str, str],
            tuple[str, str],
        ] = {}

    def plan(
        self,
        command: ProductCommand,
    ) -> dict[str, Any]:
        command.validate()

        action = str(
            command.action
        ).strip().upper()

        product = str(
            command.context.product
        ).strip().upper()

        entity = str(
            command.entity_type
        ).strip().upper()

        authority, baas_service = (
            AUTHORITY_ROUTES[
                entity
            ]
        )

        material = {
            "product": product,
            "action": action,
            "entity_type": entity,
            "entity_id": (
                command.entity_id
            ),
            "organization_id": (
                command.context.organization_id
            ),
            "workspace_id": (
                command.context.workspace_id
            ),
            "project_id": (
                command.context.project_id
            ),
            "environment_id": (
                command.context.environment_id
            ),
            "store_id": (
                command.context.store_id
            ),
            "branch_id": (
                command.context.branch_id
            ),
            "input_metadata": (
                command.input_metadata
            ),
        }

        command_hash = sha256(
            _canonical(
                material
            ).encode("utf-8")
        ).hexdigest()

        created = True

        if action in MUTATION_ACTIONS:
            idem_scope = (
                command.context.organization_id,
                command.context.environment_id,
                product,
                str(
                    command.idempotency_key
                ),
            )

            existing = (
                self._idempotency.get(
                    idem_scope
                )
            )

            if existing is not None:
                existing_hash, command_id = (
                    existing
                )

                if (
                    existing_hash
                    != command_hash
                ):
                    raise SaaSFoundationError(
                        "idempotency key reused with different product command"
                    )

                created = False
            else:
                command_id = (
                    "saas_cmd_"
                    + sha256(
                        _canonical(
                            {
                                "idempotency_scope": (
                                    idem_scope
                                ),
                                "command_hash": (
                                    command_hash
                                ),
                            }
                        ).encode(
                            "utf-8"
                        )
                    ).hexdigest()[:24]
                )

                self._idempotency[
                    idem_scope
                ] = (
                    command_hash,
                    command_id,
                )
        else:
            command_id = (
                "saas_read_"
                + sha256(
                    _canonical(
                        {
                            "material": (
                                material
                            ),
                            "correlation_id": (
                                command.context.correlation_id
                            ),
                        }
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()[:24]
            )

        plan = PlatformCommandPlan(
            command_id=command_id,
            product=product,
            action=action,
            entity_type=entity,
            entity_id=(
                command.entity_id
            ),
            authority=authority,
            baas_service=(
                baas_service
            ),
            tenant_context={
                "organization_id": (
                    command.context.organization_id
                ),
                "workspace_id": (
                    command.context.workspace_id
                ),
                "project_id": (
                    command.context.project_id
                ),
                "environment_id": (
                    command.context.environment_id
                ),
            },
            store_id=(
                command.context.store_id
            ),
            branch_id=(
                command.context.branch_id
            ),
            actor_id=(
                command.context.actor_id
            ),
            actor_type=(
                command.context.actor_type
            ),
            correlation_id=(
                command.context.correlation_id
            ),
            idempotency_key=(
                command.idempotency_key
            ),
            kernel_authorization_ref=(
                command.context.kernel_authorization_ref
            ),
            input_metadata=dict(
                command.input_metadata
            ),
            audit_event={
                "event_type": (
                    "saas.product_command.planned"
                ),
                "command_id": (
                    command_id
                ),
                "product": product,
                "action": action,
                "entity_type": (
                    entity
                ),
                "entity_id": (
                    command.entity_id
                ),
                "authority": (
                    authority
                ),
                "baas_service": (
                    baas_service
                ),
                "organization_id": (
                    command.context.organization_id
                ),
                "store_id": (
                    command.context.store_id
                ),
                "branch_id": (
                    command.context.branch_id
                ),
                "correlation_id": (
                    command.context.correlation_id
                ),
            },
        )

        return {
            "created": created,
            "plan": plan,
        }
