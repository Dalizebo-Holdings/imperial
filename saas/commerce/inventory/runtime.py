from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


class CommerceInventoryError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise CommerceInventoryError(
            f"{name} must not be empty"
        )
    result = str(value).strip()
    if not result:
        raise CommerceInventoryError(
            f"{name} must not be empty"
        )
    return result


def _time(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CommerceInventoryError(
            "requested_at must be ISO-8601"
        ) from exc
    if parsed.tzinfo is None:
        raise CommerceInventoryError(
            "requested_at must be timezone-aware"
        )
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()

    if (
        str(getattr(context, "product", "")).strip().upper()
        != "COMMERCE"
    ):
        raise CommerceInventoryError(
            "Commerce Inventory requires product=COMMERCE"
        )


def _assert_evidence(
    *,
    context: Any,
    evidence: Any,
    entity_type: str,
    entity_id: str,
) -> None:
    if evidence is None:
        raise CommerceInventoryError(
            f"{entity_type} Kernel authority evidence is required"
        )

    if hasattr(evidence, "validate"):
        evidence.validate()

    if str(getattr(evidence, "source", "")).strip() != "kernel.commerce":
        raise CommerceInventoryError(
            "authority evidence must come from kernel.commerce"
        )

    if (
        str(getattr(evidence, "entity_type", "")).strip().upper()
        != entity_type
    ):
        raise CommerceInventoryError(
            "authority evidence entity_type mismatch"
        )

    if str(getattr(evidence, "entity_id", "")).strip() != str(entity_id).strip():
        raise CommerceInventoryError(
            "authority evidence entity_id mismatch"
        )

    for name in [
        "organization_id",
        "workspace_id",
        "project_id",
        "environment_id",
    ]:
        if getattr(evidence, name, None) != getattr(context, name, None):
            raise CommerceInventoryError(
                "authority evidence tenant scope mismatch"
            )


@dataclass(frozen=True)
class InventoryCreateRequest:
    inventory_item_id: str
    product_variant_id: str
    store_id: str
    branch_id: str | None
    quantity_on_hand: int
    quantity_reserved: int
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        for name, value in {
            "inventory_item_id": self.inventory_item_id,
            "product_variant_id": self.product_variant_id,
            "store_id": self.store_id,
            "idempotency_key": self.idempotency_key,
        }.items():
            _text(name, value)

        if self.branch_id is not None:
            _text("branch_id", self.branch_id)

        for name, value in {
            "quantity_on_hand": self.quantity_on_hand,
            "quantity_reserved": self.quantity_reserved,
        }.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
            ):
                raise CommerceInventoryError(
                    f"{name} must be an integer"
                )

        _time(self.requested_at)


@dataclass(frozen=True)
class InventoryAdjustmentRequest:
    inventory_item_id: str
    product_variant_id: str
    store_id: str
    branch_id: str | None
    expected_quantity_on_hand: int
    expected_quantity_reserved: int
    quantity_on_hand_delta: int
    quantity_reserved_delta: int
    reason: str
    source_ref: str
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        for name, value in {
            "inventory_item_id": self.inventory_item_id,
            "product_variant_id": self.product_variant_id,
            "store_id": self.store_id,
            "reason": self.reason,
            "source_ref": self.source_ref,
            "idempotency_key": self.idempotency_key,
        }.items():
            _text(name, value)

        if self.branch_id is not None:
            _text("branch_id", self.branch_id)

        for name, value in {
            "expected_quantity_on_hand": self.expected_quantity_on_hand,
            "expected_quantity_reserved": self.expected_quantity_reserved,
            "quantity_on_hand_delta": self.quantity_on_hand_delta,
            "quantity_reserved_delta": self.quantity_reserved_delta,
        }.items():
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
            ):
                raise CommerceInventoryError(
                    f"{name} must be an integer"
                )

        if (
            self.quantity_on_hand_delta == 0
            and self.quantity_reserved_delta == 0
        ):
            raise CommerceInventoryError(
                "inventory adjustment must change at least one quantity"
            )

        _time(self.requested_at)


class CommerceInventoryService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        kernel_tenant_scope_type: Any,
        kernel_resource_type: Any,
        kernel_inventory_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type
        self._kernel_tenant_scope_type = kernel_tenant_scope_type
        self._kernel_resource_type = kernel_resource_type
        self._kernel_inventory_type = kernel_inventory_type

    def _validate_kernel_inventory(
        self,
        *,
        context: Any,
        inventory_item_id: str,
        product_variant_id: str,
        store_id: str,
        branch_id: str | None,
        quantity_on_hand: int,
        quantity_reserved: int,
        timestamp: str,
    ) -> None:
        tenant = self._kernel_tenant_scope_type(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            environment_id=context.environment_id,
        )
        tenant.validate()

        resource = self._kernel_resource_type(
            id=inventory_item_id,
            entity_type="INVENTORY_ITEM",
            tenant=tenant,
            created_at=timestamp,
            updated_at=timestamp,
        )

        item = self._kernel_inventory_type(
            resource=resource,
            product_variant_id=product_variant_id,
            store_id=store_id,
            branch_id=branch_id,
            quantity_on_hand=quantity_on_hand,
            quantity_reserved=quantity_reserved,
        )

        try:
            item.validate()
        except Exception as exc:
            raise CommerceInventoryError(
                "Kernel InventoryItem validation failed"
            ) from exc

    def plan_create(
        self,
        *,
        context: Any,
        request: InventoryCreateRequest,
        variant_evidence: Any,
        store_evidence: Any,
        branch_evidence: Any | None = None,
    ) -> dict[str, Any]:
        _validate_context(context)
        request.validate_basic()

        if context.store_id is None or context.store_id != request.store_id:
            raise CommerceInventoryError(
                "Commerce inventory context store_id mismatch"
            )

        if context.branch_id != request.branch_id:
            raise CommerceInventoryError(
                "Commerce inventory context branch_id mismatch"
            )

        _assert_evidence(
            context=context,
            evidence=variant_evidence,
            entity_type="PRODUCT_VARIANT",
            entity_id=request.product_variant_id,
        )
        _assert_evidence(
            context=context,
            evidence=store_evidence,
            entity_type="STORE",
            entity_id=request.store_id,
        )

        if request.branch_id is not None:
            _assert_evidence(
                context=context,
                evidence=branch_evidence,
                entity_type="BRANCH",
                entity_id=request.branch_id,
            )

        timestamp = _time(request.requested_at)

        self._validate_kernel_inventory(
            context=context,
            inventory_item_id=request.inventory_item_id,
            product_variant_id=request.product_variant_id,
            store_id=request.store_id,
            branch_id=request.branch_id,
            quantity_on_hand=request.quantity_on_hand,
            quantity_reserved=request.quantity_reserved,
            timestamp=timestamp,
        )

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="INVENTORY_ITEM",
                entity_id=request.inventory_item_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    "product_variant_id": request.product_variant_id,
                    "store_id": request.store_id,
                    "branch_id": request.branch_id,
                    "quantity_on_hand": request.quantity_on_hand,
                    "quantity_reserved": request.quantity_reserved,
                    "requested_at": timestamp,
                },
            )
        )

    def plan_adjustment(
        self,
        *,
        context: Any,
        request: InventoryAdjustmentRequest,
        inventory_evidence: Any,
        variant_evidence: Any,
        store_evidence: Any,
        branch_evidence: Any | None = None,
    ) -> dict[str, Any]:
        _validate_context(context)
        request.validate_basic()

        if context.store_id is None or context.store_id != request.store_id:
            raise CommerceInventoryError(
                "Commerce inventory context store_id mismatch"
            )

        if context.branch_id != request.branch_id:
            raise CommerceInventoryError(
                "Commerce inventory context branch_id mismatch"
            )

        _assert_evidence(
            context=context,
            evidence=inventory_evidence,
            entity_type="INVENTORY_ITEM",
            entity_id=request.inventory_item_id,
        )
        _assert_evidence(
            context=context,
            evidence=variant_evidence,
            entity_type="PRODUCT_VARIANT",
            entity_id=request.product_variant_id,
        )
        _assert_evidence(
            context=context,
            evidence=store_evidence,
            entity_type="STORE",
            entity_id=request.store_id,
        )

        if request.branch_id is not None:
            _assert_evidence(
                context=context,
                evidence=branch_evidence,
                entity_type="BRANCH",
                entity_id=request.branch_id,
            )

        target_on_hand = (
            request.expected_quantity_on_hand
            + request.quantity_on_hand_delta
        )
        target_reserved = (
            request.expected_quantity_reserved
            + request.quantity_reserved_delta
        )

        timestamp = _time(request.requested_at)

        self._validate_kernel_inventory(
            context=context,
            inventory_item_id=request.inventory_item_id,
            product_variant_id=request.product_variant_id,
            store_id=request.store_id,
            branch_id=request.branch_id,
            quantity_on_hand=target_on_hand,
            quantity_reserved=target_reserved,
            timestamp=timestamp,
        )

        return self._foundation.plan(
            self._product_command_type(
                action="UPDATE",
                entity_type="INVENTORY_ITEM",
                entity_id=request.inventory_item_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    "product_variant_id": request.product_variant_id,
                    "store_id": request.store_id,
                    "branch_id": request.branch_id,
                    "expected_quantity_on_hand": (
                        request.expected_quantity_on_hand
                    ),
                    "expected_quantity_reserved": (
                        request.expected_quantity_reserved
                    ),
                    "quantity_on_hand_delta": request.quantity_on_hand_delta,
                    "quantity_reserved_delta": request.quantity_reserved_delta,
                    "target_quantity_on_hand": target_on_hand,
                    "target_quantity_reserved": target_reserved,
                    "reason": request.reason,
                    "source_ref": request.source_ref,
                    "requested_at": timestamp,
                    "persistence_requirement": (
                        "ATOMIC_COMPARE_EXPECTED_AND_UPDATE"
                    ),
                },
            )
        )
