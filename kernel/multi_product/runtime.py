from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union


class MultiProductPrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise MultiProductPrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_sku(sku: str) -> str:
    # SKU should be alphanumeric with hyphens and underscores allowed
    value = str(sku).strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]*[A-Z0-9]", value):
        raise MultiProductPrimitiveError(
            "SKU must be alphanumeric, can contain hyphens and underscores, but not start or end with them"
        )
    return value


@dataclass(frozen=True)
class TenantScope:
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        for name, value in {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "environment_id": self.environment_id,
        }.items():
            _require_text(name, value)


@dataclass(frozen=True)
class MultiProductResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in MULTI_PRODUCT_ENTITY_TYPES:
            raise MultiProductPrimitiveError(
                f"unsupported entity_type: {self.entity_type}"
            )

        self.tenant.validate()

        for name, value in {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }.items():
            try:
                datetime.fromisoformat(value)
            except ValueError as exc:
                raise MultiProductPrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Multi-Product Platform
MULTI_PRODUCT_ENTITY_TYPES = {
    "PRODUCT",
    "VARIANT",
    "INVENTORY_ITEM",
    "CATALOG",
    "CATEGORY",
}


@dataclass(frozen=True)
class Product:
    resource: MultiProductResource
    name: str
    description: str
    sku: str
    status: str  # e.g., "ACTIVE", "INACTIVE", "ARCHIVED"
    attributes: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "PRODUCT":
            raise MultiProductPrimitiveError(
                "resource entity_type must be PRODUCT"
            )
        _require_text("name", self.name)
        _require_text("description", self.description)
        _require_text("sku", self.sku)
        validate_sku(self.sku)
        _require_text("status", self.status)
        if not isinstance(self.attributes, dict):
            raise MultiProductPrimitiveError(
                "attributes must be a dict"
            )


@dataclass(frozen=True)
class Variant:
    resource: MultiProductResource
    product_id: str
    name: str
    sku: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str  # e.g., "ACTIVE", "INACTIVE", "ARCHIVED"

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "VARIANT":
            raise MultiProductPrimitiveError(
                "resource entity_type must be VARIANT"
            )
        _require_text("product_id", self.product_id)
        _require_text("name", self.name)
        _require_text("sku", self.sku)
        validate_sku(self.sku)
        if not isinstance(self.attributes, dict):
            raise MultiProductPrimitiveError(
                "attributes must be a dict"
            )
        _require_text("status", self.status)


@dataclass(frozen=True)
class InventoryItem:
    resource: MultiProductResource
    variant_id: str
    sku: str
    quantity: int
    status: str  # e.g., "IN_STOCK", "OUT_OF_STOCK", "LOW_STOCK"
    location: str  # e.g., "WAREHOUSE_A", "STORE_1"

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "INVENTORY_ITEM":
            raise MultiProductPrimitiveError(
                "resource entity_type must be INVENTORY_ITEM"
            )
        _require_text("variant_id", self.variant_id)
        _require_text("sku", self.sku)
        validate_sku(self.sku)
        if not isinstance(self.quantity, int) or self.quantity < 0:
            raise MultiProductPrimitiveError(
                "quantity must be a non-negative integer"
            )
        _require_text("status", self.status)
        _require_text("location", self.location)


@dataclass(frozen=True)
class Catalog:
    resource: MultiProductResource
    name: str
    description: str
    status: str  # e.g., "ACTIVE", "INACTIVE", "ARCHIVED"
    items: List[str] = field(default_factory=list)  # list of product IDs

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "CATALOG":
            raise MultiProductPrimitiveError(
                "resource entity_type must be CATALOG"
            )
        _require_text("name", self.name)
        _require_text("description", self.description)
        _require_text("status", self.status)
        if not isinstance(self.items, list):
            raise MultiProductPrimitiveError(
                "items must be a list"
            )
        for item in self.items:
            if not isinstance(item, str):
                raise MultiProductPrimitiveError(
                    "each item must be a string"
                )
            _require_text("item", item)


@dataclass(frozen=True)
class Category:
    resource: MultiProductResource
    name: str
    description: str
    parent_id: Optional[str] = None
    status: str  # e.g., "ACTIVE", "INACTIVE", "ARCHIVED"

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "CATEGORY":
            raise MultiProductPrimitiveError(
                "resource entity_type must be CATEGORY"
            )
        _require_text("name", self.name)
        _require_text("description", self.description)
        if self.parent_id is not None:
            _require_text("parent_id", self.parent_id)
        _require_text("status", self.status)