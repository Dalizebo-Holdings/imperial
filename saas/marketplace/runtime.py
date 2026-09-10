from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kernel.marketplace.runtime import (
    Listing,
    Transaction,
    Vendor,
    Product,
    Money,
    TenantScope,
    MarketplaceResource,
    MarketplacePrimitiveError,
    MARKETPLACE_ENTITY_TYPES,
)


class MarketplaceServiceError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise MarketplaceServiceError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise MarketplaceServiceError(f"{name} must not be empty")
    return result


# In a real system, these would interact with a database or storage layer.
# For now, we'll define the service functions that validate and return the primitives.

def create_listing(
    *,
    id: str,
    title: str,
    description: str,
    price_amount_minor: int,
    price_currency: str,
    vendor_id: str,
    tenant: TenantScope,
    product_id: Optional[str] = None,
    is_active: bool = True,
    is_featured: bool = False,
    created_at: str,
    updated_at: str,
) -> Listing:
    """
    Create a new Listing primitive.
    This function validates the input and returns a Listing instance.
    """
    resource = MarketplaceResource(
        id=id,
        entity_type="LISTING",
        tenant=tenant,
        created_at=created_at,
        updated_at=updated_at,
    )
    resource.validate()

    price = Money(amount_minor=price_amount_minor, currency=price_currency)
    price.validate()

    listing = Listing(
        resource=resource,
        title=_text("title", title),
        description=_text("description", description),
        price=price,
        vendor_id=_text("vendor_id", vendor_id),
        product_id=product_id,  # can be None
        is_active=is_active,
        is_featured=is_featured,
    )
    listing.validate()
    return listing


def create_transaction(
    *,
    id: str,
    listing_id: str,
    buyer_tenant_id: str,
    seller_tenant_id: str,
    amount_amount_minor: int,
    amount_currency: str,
    status: str,
    initiated_at: str,
    tenant: TenantScope,
    completed_at: Optional[str] = None,
    refunded_at: Optional[str] = None,
    updated_at: str,
) -> Transaction:
    """
    Create a new Transaction primitive.
    """
    resource = MarketplaceResource(
        id=id,
        entity_type="TRANSACTION",
        tenant=tenant,
        created_at=initiated_at,  # For transaction, created_at is the initiated_at
        updated_at=updated_at,
    )
    resource.validate()

    amount = Money(amount_minor=amount_amount_minor, currency=amount_currency)
    amount.validate(allow_negative=False)

    transaction = Transaction(
        resource=resource,
        listing_id=_text("listing_id", listing_id),
        buyer_tenant_id=_text("buyer_tenant_id", buyer_tenant_id),
        seller_tenant_id=_text("seller_tenant_id", seller_tenant_id),
        amount=amount,
        status=_text("status", status),
        initiated_at=initiated_at,
        completed_at=completed_at,
        refunded_at=refunded_at,
    )
    transaction.validate()
    return transaction


def create_vendor(
    *,
    id: str,
    name: str,
    description: Optional[str],
    contact_email: str,
    tenant: TenantScope,
    is_active: bool = True,
    is_verified: bool = False,
    created_at: str,
    updated_at: str,
) -> Vendor:
    """
    Create a new Vendor primitive.
    """
    resource = MarketplaceResource(
        id=id,
        entity_type="VENDOR",
        tenant=tenant,
        created_at=created_at,
        updated_at=updated_at,
    )
    resource.validate()

    vendor = Vendor(
        resource=resource,
        name=_text("name", name),
        description=description,  # can be None
        contact_email=_text("contact_email", contact_email),
        is_active=is_active,
        is_verified=is_verified,
    )
    vendor.validate()
    return vendor


def create_product(
    *,
    id: str,
    name: str,
    description: str,
    sku: str,
    tenant: TenantScope,
    is_active: bool = True,
    created_at: str,
    updated_at: str,
) -> Product:
    """
    Create a new Product primitive.
    """
    resource = MarketplaceResource(
        id=id,
        entity_type="PRODUCT",
        tenant=tenant,
        created_at=created_at,
        updated_at=updated_at,
    )
    resource.validate()

    product = Product(
        resource=resource,
        name=_text("name", name),
        description=_text("description", description),
        sku=_text("sku", sku),
        is_active=is_active,
    )
    product.validate()
    return product


# Additional service functions could include:
# - update_listing, update_transaction, etc.
# - search_listings, get_vendor_by_id, etc.
# For now, we have the creation functions.

