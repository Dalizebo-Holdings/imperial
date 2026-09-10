from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

from kernel.multi_product.runtime import (
    Product,
    Variant,
    InventoryItem,
    Catalog,
    Category,
    MultiProductPrimitiveError,
    MultiProductResource,
    TenantScope,
)


class MultiProductSError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise MultiProductSError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise MultiProductSError(f"{name} must not be empty")
    return result


def _time(value: str | None = None) -> str:
    from datetime import datetime, timezone
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise MultiProductSError("requested_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise MultiProductSError("requested_at must be timezone-aware")
    return parsed.isoformat()


def _validate_context(context: Any) -> None:
    if hasattr(context, "validate"):
        context.validate()


@dataclass(frozen=True)
class ProductCreateRequest:
    product_id: str
    name: str
    description: str
    sku: str
    status: str
    attributes: dict[str, Any] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("product_id", self.product_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("description", self.description)
        _text("sku", self.sku)
        _text("status", self.status)

        attributes = self.attributes or {}
        if not isinstance(attributes, dict):
            raise MultiProductSError("attributes must be a dict")

        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "sku": self.sku,
            "status": self.status,
            "attributes": attributes,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class VariantCreateRequest:
    variant_id: str
    product_id: str
    name: str
    sku: str
    attributes: dict[str, Any] | None = None
    status: str
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("variant_id", self.variant_id)
        _text("idempotency_key", self.idempotency_key)
        _text("product_id", self.product_id)
        _text("name", self.name)
        _text("sku", self.sku)
        _text("status", self.status)

        attributes = self.attributes or {}
        if not isinstance(attributes, dict):
            raise MultiProductSError("attributes must be a dict")

        return {
            "variant_id": self.variant_id,
            "product_id": self.product_id,
            "name": self.name,
            "sku": self.sku,
            "attributes": attributes,
            "status": self.status,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class InventoryItemCreateRequest:
    inventory_item_id: str
    variant_id: str
    sku: str
    quantity: int
    status: str
    location: str
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("inventory_item_id", self.inventory_item_id)
        _text("idempotency_key", self.idempotency_key)
        _text("variant_id", self.variant_id)
        _text("sku", self.sku)
        _text("quantity", self.quantity)
        _text("status", self.status)
        _text("location", self.location)

        return {
            "inventory_item_id": self.inventory_item_id,
            "variant_id": self.variant_id,
            "sku": self.sku,
            "quantity": self.quantity,
            "status": self.status,
            "location": self.location,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class CatalogCreateRequest:
    catalog_id: str
    name: str
    description: str
    status: str
    items: list[str] | None = None
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("catalog_id", self.catalog_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("description", self.description)
        _text("status", self.status)

        items = self.items or []
        if not isinstance(items, list):
            raise MultiProductSError("items must be a list")
        for item in items:
            if not isinstance(item, str):
                raise MultiProductSError("each item must be a string")
            _text("item", item)

        return {
            "catalog_id": self.catalog_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "items": items,
            "requested_at": _time(self.requested_at),
        }


@dataclass(frozen=True)
class CategoryCreateRequest:
    category_id: str
    name: str
    description: str
    parent_id: str | None = None
    status: str
    idempotency_key: str
    requested_at: str

    def normalized(self) -> dict[str, Any]:
        _text("category_id", self.category_id)
        _text("idempotency_key", self.idempotency_key)
        _text("name", self.name)
        _text("description", self.description)
        if self.parent_id is not None:
            _text("parent_id", self.parent_id)
        _text("status", self.status)

        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "status": self.status,
            "requested_at": _time(self.requested_at),
        }


class MultiProductService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
    ) -> None:
        self._foundation = foundation
        self._product_command_type = product_command_type

    def plan_create_product(
        self,
        *,
        context: Any,
        request: ProductCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PRODUCT",
                entity_id=request.product_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "MULTI_PRODUCT_PRODUCT",
                },
            )
        )

    def plan_create_variant(
        self,
        *,
        context: Any,
        request: VariantCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="VARIANT",
                entity_id=request.variant_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "MULTI_PRODUCT_VARIANT",
                },
            )
        )

    def plan_create_inventory_item(
        self,
        *,
        context: Any,
        request: InventoryItemCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="INVENTORY_ITEM",
                entity_id=request.inventory_item_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "MULTI_PRODUCT_INVENTORY_ITEM",
                },
            )
        )

    def plan_create_catalog(
        self,
        *,
        context: Any,
        request: CatalogCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="CATALOG",
                entity_id=request.catalog_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "MULTI_PRODUCT_CATALOG",
                },
            )
        )

    def plan_create_category(
        self,
        *,
        context: Any,
        request: CategoryCreateRequest,
    ) -> dict[str, Any]:
        _validate_context(context)
        normalized = request.normalized()
        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="CATEGORY",
                entity_id=request.category_id,
                context=context,
                idempotency_key=request.idempotency_key,
                input_metadata={
                    **normalized,
                    "data_classification": "MULTI_PRODUCT_CATEGORY",
                },
            )
        )