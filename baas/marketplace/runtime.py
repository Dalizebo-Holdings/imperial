from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from kernel.marketplace.runtime import (
    Listing, Transaction, Vendor, Product, Money, TenantScope, MarketplacePrimitiveError
)
import uuid
from datetime import datetime, timezone

# In-memory storage (replace with DB later)
_listings: Dict[str, Listing] = {}
_vendors: Dict[str, Vendor] = {}
_products: Dict[str, Product] = {}
_transactions: Dict[str, Transaction] = {}

class MarketplaceServiceError(ValueError):
    pass

def _text(name: str, value: Any) -> str:
    if value is None:
        raise MarketplaceServiceError(f"{name} must not be empty")
    result = str(value).strip()
    if not result:
        raise MarketplaceServiceError(f"{name} must not be empty")
    return result

def _get_dummy_tenant() -> TenantScope:
    """Returns a dummy tenant scope for development purposes."""
    return TenantScope(
        organization_id="test-org",
        workspace_id="test-workspace",
        project_id="test-project",
        environment_id="test-env"
    )

class MarketplaceService:
    def __init__(self):
        pass

    def create_listing(self, *, tenant: Optional[TenantScope] = None, title: str, description: str,
                       price_amount_minor: int, price_currency: str, vendor_id: str,
                       product_id: Optional[str] = None) -> Listing:
        tenant = tenant or _get_dummy_tenant()
        _text("title", title)
        _text("description", description)
        _text("vendor_id", vendor_id)
        if product_id is not None:
            _text("product_id", product_id)

        listing_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        listing = Listing(
            resource=kernel.marketplace.runtime.MarketplaceResource(
                id=listing_id,
                entity_type="LISTING",
                tenant=tenant,
                created_at=now,
                updated_at=now,
            ),
            title=title,
            description=description,
            price=Money(amount_minor=price_amount_minor, currency=price_currency),
            vendor_id=vendor_id,
            product_id=product_id,
            is_active=True,
            is_featured=False,
        )
        listing.validate()
        _listings[listing_id] = listing
        # TODO: Emit LISTING_CREATED event to outbox
        return listing

    def get_listings(self, *, tenant: Optional[TenantScope] = None, active_only: bool = True) -> List[Listing]:
        tenant = tenant or _get_dummy_tenant()
        listings = list(_listings.values())
        if active_only:
            listings = [l for l in listings if l.is_active]
        # TODO: Filter by tenant
        return listings

    def get_listing(self, *, listing_id: str) -> Optional[Listing]:
        return _listings.get(listing_id)

    def update_listing(self, *, listing_id: str, title: Optional[str] = None,
                       description: Optional[str] = None, price_amount_minor: Optional[int] = None,
                       price_currency: Optional[str] = None, is_active: Optional[bool] = None,
                       is_featured: Optional[bool] = None) -> Listing:
        listing = _listings.get(listing_id)
        if not listing:
            raise MarketplaceServiceError(f"Listing {listing_id} not found")
        update_dict = {}
        if title is not None:
            _text("title", title)
            update_dict["title"] = title
        if description is not None:
            _text("description", description)
            update_dict["description"] = description
        if price_amount_minor is not None and price_currency is not None:
            new_price = Money(amount_minor=price_amount_minor, currency=price_currency)
            new_price.validate()
            update_dict["price"] = new_price
        elif price_amount_minor is not None or price_currency is not None:
            raise MarketplaceServiceError("Both price_amount_minor and price_currency must be provided together")
        if is_active is not None:
            update_dict["is_active"] = is_active
        if is_featured is not None:
            update_dict["is_featured"] = is_featured

        if not update_dict:
            return listing

        # Create a new listing with updated fields
        listing = Listing(
            resource=listing.resource,
            title=update_dict.get("title", listing.title),
            description=update_dict.get("description", listing.description),
            price=update_dict.get("price", listing.price),
            vendor_id=listing.vendor_id,
            product_id=listing.product_id,
            is_active=update_dict.get("is_active", listing.is_active),
            is_featured=update_dict.get("is_featured", listing.is_featured),
        )
        listing.validate()
        _listings[listing_id] = listing
        return listing

    def delete_listing(self, *, listing_id: str) -> None:
        if listing_id not in _listings:
            raise MarketplaceServiceError(f"Listing {listing_id} not found")
        del _listings[listing_id]

    # Vendor methods
    def create_vendor(self, *, tenant: Optional[TenantScope] = None, name: str, description: Optional[str],
                      contact_email: str) -> Vendor:
        tenant = tenant or _get_dummy_tenant()
        _text("name", name)
        _text("contact_email", contact_email)
        vendor_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        vendor = Vendor(
            resource=kernel.marketplace.runtime.MarketplaceResource(
                id=vendor_id,
                entity_type="VENDOR",
                tenant=tenant,
                created_at=now,
                updated_at=now,
            ),
            name=name,
            description=description,
            contact_email=contact_email,
            is_active=True,
            is_verified=False,
        )
        vendor.validate()
        _vendors[vendor_id] = vendor
        return vendor

    def get_vendors(self, *, tenant: Optional[TenantScope] = None, active_only: bool = True) -> List[Vendor]:
        tenant = tenant or _get_dummy_tenant()
        vendors = list(_vendors.values())
        if active_only:
            vendors = [v for v in vendors if v.is_active]
        # TODO: Filter by tenant
        return vendors

    def get_vendor(self, *, vendor_id: str) -> Optional[Vendor]:
        return _vendors.get(vendor_id)

    # Product methods
    def create_product(self, *, tenant: Optional[TenantScope] = None, name: str, description: str,
                       sku: str) -> Product:
        tenant = tenant or _get_dummy_tenant()
        _text("name", name)
        _text("description", description)
        _text("sku", sku)
        product_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        product = Product(
            resource=kernel.marketplace.runtime.MarketplaceResource(
                id=product_id,
                entity_type="PRODUCT",
                tenant=tenant,
                created_at=now,
                updated_at=now,
            ),
            name=name,
            description=description,
            sku=sku,
            is_active=True,
        )
        product.validate()
        _products[product_id] = product
        return product

    def get_products(self, *, tenant: Optional[TenantScope] = None, active_only: bool = True) -> List[Product]:
        tenant = tenant or _get_dummy_tenant()
        products = list(_products.values())
        if active_only:
            products = [p for p in products if p.is_active]
        # TODO: Filter by tenant
        return products

    def get_product(self, *, product_id: str) -> Optional[Product]:
        return _products.get(product_id)

    # Transaction methods
    def create_transaction(self, *, tenant: Optional[TenantScope] = None, listing_id: str,
                           buyer_tenant_id: str, seller_tenant_id: str,
                           amount_minor: int, currency: str) -> Transaction:
        tenant = tenant or _get_dummy_tenant()
        _text("listing_id", listing_id)
        _text("buyer_tenant_id", buyer_tenant_id)
        _text("seller_tenant_id", seller_tenant_id)
        listing = _listings.get(listing_id)
        if not listing:
            raise MarketplaceServiceError(f"Listing {listing_id} not found")
        if not listing.is_active:
            raise MarketplaceServiceError(f"Listing {listing_id} is not active")
        # TODO: Validate that seller_tenant_id matches the vendor's tenant? We'll skip for now.
        transaction_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        transaction = Transaction(
            resource=kernel.marketplace.runtime.MarketplaceResource(
                id=transaction_id,
                entity_type="TRANSACTION",
                tenant=tenant,
                created_at=now,
                updated_at=now,
            ),
            listing_id=listing_id,
            buyer_tenant_id=buyer_tenant_id,
            seller_tenant_id=seller_tenant_id,
            amount=Money(amount_minor=amount_minor, currency=currency),
            status="PENDING",
            initiated_at=now,
            completed_at=None,
            refunded_at=None,
        )
        transaction.validate()
        _transactions[transaction_id] = transaction
        return transaction

    def get_transactions(self, *, tenant: Optional[TenantScope] = None) -> List[Transaction]:
        tenant = tenant or _get_dummy_tenant()
        # TODO: Filter by tenant
        return list(_transactions.values())

    def get_transaction(self, *, transaction_id: str) -> Optional[Transaction]:
        return _transactions.get(transaction_id)

    def update_transaction_status(self, *, transaction_id: str, status: str,
                                  completed_at: Optional[str] = None,
                                  refunded_at: Optional[str] = None) -> Transaction:
        transaction = _transactions.get(transaction_id)
        if not transaction:
            raise MarketplaceServiceError(f"Transaction {transaction_id} not found")
        _text("status", status)
        # Validate status transition? We'll skip for now.
        updated = Transaction(
            resource=transaction.resource,
            listing_id=transaction.listing_id,
            buyer_tenant_id=transaction.buyer_tenant_id,
            seller_tenant_id=transaction.seller_tenant_id,
            amount=transaction.amount,
            status=status,
            initiated_at=transaction.initiated_at,
            completed_at=completed_at,
            refunded_at=refunded_at,
        )
        updated.validate()
        _transactions[transaction_id] = updated
        return updated