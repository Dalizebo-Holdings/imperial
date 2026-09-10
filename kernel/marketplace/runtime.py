from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Union


class MarketplacePrimitiveError(ValueError):
    pass


def _require_text(name: str, value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise MarketplacePrimitiveError(
            f"{name} must not be empty"
        )
    return normalized


def validate_currency(currency: str) -> str:
    value = str(currency).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", value):
        raise MarketplacePrimitiveError(
            "currency must be three uppercase letters"
        )
    return value


# Reuse Money from AI module if available, otherwise define a simple one.
# We'll define it here for now to avoid circular dependencies, but note that AI module has a similar one.
# In a real project, we might have a common types module.
@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def validate(self, *, allow_negative: bool = False) -> None:
        if not isinstance(self.amount_minor, int):
            raise MarketplacePrimitiveError(
                "amount_minor must be an integer"
            )
        if not allow_negative and self.amount_minor < 0:
            raise MarketplacePrimitiveError(
                "amount_minor must be >= 0"
            )
        validate_currency(self.currency)


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
class MarketplaceResource:
    id: str
    entity_type: str
    tenant: TenantScope
    created_at: str
    updated_at: str

    def validate(self) -> None:
        _require_text("id", self.id)

        if self.entity_type not in MARKETPLACE_ENTITY_TYPES:
            raise MarketplacePrimitiveError(
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
                raise MarketplacePrimitiveError(
                    f"{name} must be ISO-8601"
                ) from exc


# Entity types for Marketplace
MARKETPLACE_ENTITY_TYPES = {
    "LISTING",
    "TRANSACTION",
    "VENDOR",
    "PRODUCT",
}


@dataclass(frozen=True)
class Listing:
    resource: MarketplaceResource
    title: str
    description: str
    price: Money
    vendor_id: str  # Reference to Vendor
    product_id: str | None = None  # Optional reference to Product (if products are separate)
    is_active: bool = True
    is_featured: bool = False

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "LISTING":
            raise MarketplacePrimitiveError(
                "resource entity_type must be LISTING"
            )
        _require_text("title", self.title)
        _require_text("description", self.description)
        self.price.validate()
        _require_text("vendor_id", self.vendor_id)
        if self.product_id is not None:
            _require_text("product_id", self.product_id)
        if not isinstance(self.is_active, bool):
            raise MarketplacePrimitiveError(
                "is_active must be a boolean"
            )
        if not isinstance(self.is_featured, bool):
            raise MarketplacePrimitiveError(
                "is_featured must be a boolean"
            )


@dataclass(frozen=True)
class Transaction:
    resource: MarketplaceResource
    listing_id: str
    buyer_tenant_id: str  # Tenant organization ID of the buyer
    seller_tenant_id: str  # Tenant organization ID of the seller (should match vendor's tenant)
    amount: Money
    status: str  # e.g., "PENDING", "COMPLETED", "CANCELLED", "REFUNDED"
    initiated_at: str
    completed_at: str | None = None
    refunded_at: str | None = None

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "TRANSACTION":
            raise MarketplacePrimitiveError(
                "resource entity_type must be TRANSACTION"
            )
        _require_text("listing_id", self.listing_id)
        _require_text("buyer_tenant_id", self.buyer_tenant_id)
        _require_text("seller_tenant_id", self.seller_tenant_id)
        self.amount.validate(allow_negative=False)  # Transaction amount should be positive
        _require_text("status", self.status)
        try:
            datetime.fromisoformat(self.initiated_at)
        except ValueError as exc:
            raise MarketplacePrimitiveError(
                "initiated_at must be ISO-8601"
            ) from exc
        if self.completed_at is not None:
            try:
                datetime.fromisoformat(self.completed_at)
            except ValueError as exc:
                raise MarketplacePrimitiveError(
                    "completed_at must be ISO-8601"
                ) from exc
        if self.refunded_at is not None:
            try:
                datetime.fromisoformat(self.refunded_at)
            except ValueError as exc:
                raise MarketplacePrimitiveError(
                    "refunded_at must be ISO-8601"
                ) from exc


@dataclass(frozen=True)
class Vendor:
    resource: MarketplaceResource
    name: str
    description: str | None = None
    contact_email: str
    is_active: bool = True
    is_verified: bool = False

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "VENDOR":
            raise MarketplacePrimitiveError(
                "resource entity_type must be VENDOR"
            )
        _require_text("name", self.name)
        if self.description is not None:
            _require_text("description", self.description)
        _require_text("contact_email", self.contact_email)
        # Simple email validation
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", self.contact_email):
            raise MarketplacePrimitiveError(
                "contact_email must be a valid email address"
            )
        if not isinstance(self.is_active, bool):
            raise MarketplacePrimitiveError(
                "is_active must be a boolean"
            )
        if not isinstance(self.is_verified, bool):
            raise MarketplacePrimitiveError(
                "is_verified must be a boolean"
            )


@dataclass(frozen=True)
class Product:
    resource: MarketplaceResource
    name: str
    description: str
    sku: str  # Stock Keeping Unit
    is_active: bool = True

    def validate(self) -> None:
        self.resource.validate()
        if self.resource.entity_type != "PRODUCT":
            raise MarketplacePrimitiveError(
                "resource entity_type must be PRODUCT"
            )
        _require_text("name", self.name)
        _require_text("description", self.description)
        _require_text("sku", self.sku)
        if not isinstance(self.is_active, bool):
            raise MarketplacePrimitiveError(
                "is_active must be a boolean"
            )
