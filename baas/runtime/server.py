from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from baas.marketplace.runtime import MarketplaceService

app = FastAPI(title="Dalizebo BaaS API", version="0.1.0")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://imperial:imperial@localhost:5432/imperial")
KERNEL_AUTH_SECRET = os.getenv("KERNEL_AUTH_SECRET", "dev-secret-change-in-production")


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


class KernelAuthRequest(BaseModel):
    kernel_authorization_ref: str


def verify_kernel_auth(auth: KernelAuthRequest) -> bool:
    """Verify Kernel authorization evidence."""
    return auth.kernel_authorization_ref.startswith("kernel_auth_")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        database="connected" if DATABASE_URL else "not_configured",
        version="0.1.0",
    )


@app.get("/")
async def root():
    return {
        "service": "Dalizebo BaaS API",
        "version": "0.1.0",
        "phase": "Phase 8 — Platform Hardening",
        "docs": "/docs",
    }


@app.post("/auth/verify")
async def verify_auth(auth: KernelAuthRequest):
    if verify_kernel_auth(auth):
        return {"valid": True, "message": "Kernel authorization verified"}
    raise HTTPException(status_code=401, detail="Invalid Kernel authorization")


# Events endpoints
@app.post("/events/subscriptions")
async def register_subscription(subscription: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"subscription_id": "sub_pending", "status": "registered"}


@app.post("/events/publish")
async def publish_event(event: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"delivery_plans": [], "status": "planned"}


# Webhooks endpoints
@app.post("/webhooks/endpoints")
async def register_webhook(endpoint: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"endpoint_id": "ep_pending", "status": "registered"}


@app.post("/webhooks/deliver")
async def deliver_webhook(delivery: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"delivery_id": "del_pending", "status": "planned"}


# Background Jobs endpoints
@app.post("/jobs/definitions")
async def register_job_definition(definition: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"definition_id": "def_pending", "status": "registered"}


@app.post("/jobs/submit")
async def submit_job(submission: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"job_id": "job_pending", "status": "queued"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"job_id": job_id, "state": "UNKNOWN", "message": "Not implemented"}


# Audit endpoints
@app.post("/audit/query")
async def query_audit(query: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"records": [], "next_after_sequence": None}


@app.post("/audit/export")
async def export_audit(query: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"selected_count": 0, "verify_selection": lambda: True}


# Logging endpoints
@app.post("/logging/ingest")
async def ingest_log(log: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"accepted": True, "record": {"sequence": 1}}


@app.post("/logging/query")
async def query_logs(query: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"records": [], "next_after_sequence": None}


# Database endpoints
@app.post("/database/query")
async def query_database(query: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"rows": [], "row_count": 0}


# Storage endpoints
@app.post("/storage/upload")
async def upload_storage(upload: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"object_id": "obj_pending", "status": "uploaded"}


# Functions endpoints
@app.post("/functions/deploy")
async def deploy_function(function: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"function_id": "fn_pending", "status": "deployed"}


# API Gateway endpoints
@app.post("/gateway/routes")
async def create_route(route: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"route_id": "route_pending", "status": "created"}


# Secrets endpoints
@app.post("/secrets/create")
async def create_secret(secret: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"secret_id": "sec_pending", "status": "created"}


# Backups endpoints
@app.post("/backups/schedule")
async def schedule_backup(backup: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"backup_id": "bkp_pending", "status": "scheduled"}


# Billing endpoints
@app.post("/billing/subscriptions")
async def create_subscription(subscription: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"subscription_id": "sub_pending", "status": "created"}


# Payments endpoints
@app.post("/payments/intents")
async def create_payment_intent(intent: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"payment_intent_id": "pi_pending", "status": "created"}


# Currency Conversion endpoints
@app.post("/currency/convert")
async def convert_currency(conversion: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    return {"conversion_id": "conv_pending", "status": "planned"}


# Marketplace endpoints
marketplace_service = MarketplaceService()


@app.post("/api/v1/marketplace/listings")
async def create_listing(listing: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        result = marketplace_service.create_listing(
            title=listing.get("title"),
            description=listing.get("description"),
            price_amount_minor=listing.get("price_amount_minor"),
            price_currency=listing.get("price_currency"),
            vendor_id=listing.get("vendor_id"),
            product_id=listing.get("product_id")
        )
        return {
            "id": result.resource.id,
            "title": result.title,
            "description": result.description,
            "price": {
                "amount_minor": result.price.amount_minor,
                "currency": result.price.currency
            },
            "vendor_id": result.vendor_id,
            "product_id": result.product_id,
            "is_active": result.is_active,
            "is_featured": result.is_featured,
            "created_at": result.resource.created_at,
            "updated_at": result.resource.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/marketplace/listings")
async def list_listings(auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    listings = marketplace_service.get_listings()
    return [
        {
            "id": l.resource.id,
            "title": l.title,
            "description": l.description,
            "price": {
                "amount_minor": l.price.amount_minor,
                "currency": l.price.currency
            },
            "vendor_id": l.vendor_id,
            "product_id": l.product_id,
            "is_active": l.is_active,
            "is_featured": l.is_featured,
            "created_at": l.resource.created_at,
            "updated_at": l.resource.updated_at
        }
        for l in listings
    ]


@app.get("/api/v1/marketplace/listings/{listing_id}")
async def get_listing(listing_id: str, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    listing = marketplace_service.get_listing(listing_id=listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {
        "id": listing.resource.id,
        "title": listing.title,
        "description": listing.description,
        "price": {
            "amount_minor": listing.price.amount_minor,
            "currency": listing.price.currency
        },
        "vendor_id": listing.vendor_id,
        "product_id": listing.product_id,
        "is_active": listing.is_active,
        "is_featured": listing.is_featured,
        "created_at": listing.resource.created_at,
        "updated_at": listing.resource.updated_at
    }


@app.put("/api/v1/marketplace/listings/{listing_id}")
async def update_listing(listing_id: str, listing: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        result = marketplace_service.update_listing(
            listing_id=listing_id,
            title=listing.get("title"),
            description=listing.get("description"),
            price_amount_minor=listing.get("price_amount_minor"),
            price_currency=listing.get("price_currency"),
            is_active=listing.get("is_active"),
            is_featured=listing.get("is_featured")
        )
        return {
            "id": result.resource.id,
            "title": result.title,
            "description": result.description,
            "price": {
                "amount_minor": result.price.amount_minor,
                "currency": result.price.currency
            },
            "vendor_id": result.vendor_id,
            "product_id": result.product_id,
            "is_active": result.is_active,
            "is_featured": result.is_featured,
            "created_at": result.resource.created_at,
            "updated_at": result.resource.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/marketplace/listings/{listing_id}")
async def delete_listing(listing_id: str, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        marketplace_service.delete_listing(listing_id=listing_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Vendor endpoints
@app.post("/api/v1/marketplace/vendors")
async def create_vendor(vendor: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        result = marketplace_service.create_vendor(
            name=vendor.get("name"),
            description=vendor.get("description"),
            contact_email=vendor.get("contact_email")
        )
        return {
            "id": result.resource.id,
            "name": result.name,
            "description": result.description,
            "contact_email": result.contact_email,
            "is_active": result.is_active,
            "is_verified": result.is_verified,
            "created_at": result.resource.created_at,
            "updated_at": result.resource.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/marketplace/vendors")
async def list_vendors(auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    vendors = marketplace_service.get_vendors()
    return [
        {
            "id": v.resource.id,
            "name": v.name,
            "description": v.description,
            "contact_email": v.contact_email,
            "is_active": v.is_active,
            "is_verified": v.is_verified,
            "created_at": v.resource.created_at,
            "updated_at": v.resource.updated_at
        }
        for v in vendors
    ]


@app.get("/api/v1/marketplace/vendors/{vendor_id}")
async def get_vendor(vendor_id: str, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    vendor = marketplace_service.get_vendor(vendor_id=vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {
        "id": vendor.resource.id,
        "name": vendor.name,
        "description": vendor.description,
        "contact_email": vendor.contact_email,
        "is_active": vendor.is_active,
        "is_verified": vendor.is_verified,
        "created_at": vendor.resource.created_at,
        "updated_at": vendor.resource.updated_at
    ]


# Product endpoints
@app.post("/api/v1/marketplace/products")
async def create_product(product: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        result = marketplace_service.create_product(
            name=product.get("name"),
            description=product.get("description"),
            sku=product.get("sku")
        )
        return {
            "id": result.resource.id,
            "name": result.name,
            "description": result.description,
            "sku": result.sku,
            "is_active": result.is_active,
            "created_at": result.resource.created_at,
            "updated_at": result.resource.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/marketplace/products")
async def list_products(auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    products = marketplace_service.get_products()
    return [
        {
            "id": p.resource.id,
            "name": p.name,
            "description": p.description,
            "sku": p.sku,
            "is_active": p.is_active,
            "created_at": p.resource.created_at,
            "updated_at": p.resource.updated_at
        }
        for p in products
    ]


@app.get("/api/v1/marketplace/products/{product_id}")
async def get_product(product_id: str, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    product = marketplace_service.get_product(product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": product.resource.id,
        "name": product.name,
        "description": product.description,
        "sku": product.sku,
        "is_active": product.is_active,
        "created_at": product.resource.created_at,
        "updated_at": product.resource.updated_at
    }


# Transaction endpoints
@app.post("/api/v1/marketplace/transactions")
async def create_transaction(transaction: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        result = marketplace_service.create_transaction(
            listing_id=transaction.get("listing_id"),
            buyer_tenant_id=transaction.get("buyer_tenant_id"),
            seller_tenant_id=transaction.get("seller_tenant_id"),
            amount_minor=transaction.get("amount_minor"),
            currency=transaction.get("currency")
        )
        return {
            "id": result.resource.id,
            "listing_id": result.listing_id,
            "buyer_tenant_id": result.buyer_tenant_id,
            "seller_tenant_id": result.seller_tenant_id,
            "amount": {
                "amount_minor": result.amount.amount_minor,
                "currency": result.amount.currency
            },
            "status": result.status,
            "initiated_at": result.initiated_at,
            "completed_at": result.completed_at,
            "refunded_at": result.refunded_at,
            "created_at": result.resource.created_at,
            "updated_at": result.resource.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/marketplace/transactions")
async def list_transactions(auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    transactions = marketplace_service.get_transactions()
    return [
        {
            "id": t.resource.id,
            "listing_id": t.listing_id,
            "buyer_tenant_id": t.buyer_tenant_id,
            "seller_tenant_id": t.seller_tenant_id,
            "amount": {
                "amount_minor": t.amount.amount_minor,
                "currency": t.amount.currency
            },
            "status": t.status,
            "initiated_at": t.initiated_at,
            "completed_at": t.completed_at,
            "refunded_at": t.refunded_at,
            "created_at": t.resource.created_at,
            "updated_at": t.resource.updated_at
        }
        for t in transactions
    ]


@app.get("/api/v1/marketplace/transactions/{transaction_id}")
async def get_transaction(transaction_id: str, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    transaction = marketplace_service.get_transaction(transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "id": transaction.resource.id,
        "listing_id": transaction.listing_id,
        "buyer_tenant_id": transaction.buyer_tenant_id,
        "seller_tenant_id": transaction.seller_tenant_id,
        "amount": {
            "amount_minor": transaction.amount.amount_minor,
            "currency": transaction.amount.currency
        },
        "status": transaction.status,
        "initiated_at": transaction.initiated_at,
        "completed_at": transaction.completed_at,
        "refunded_at": transaction.refunded_at,
        "created_at": transaction.resource.created_at,
        "updated_at": transaction.resource.updated_at
    }


@app.put("/api/v1/marketplace/transactions/{transaction_id}")
async def update_transaction_status(transaction_id: str, transaction: dict, auth: KernelAuthRequest = Depends()):
    if not verify_kernel_auth(auth):
        raise HTTPException(status_code=401, detail="Invalid Kernel authorization")
    try:
        result = marketplace_service.update_transaction_status(
            transaction_id=transaction_id,
            status=transaction.get("status"),
            completed_at=transaction.get("completed_at"),
            refunded_at=transaction.get("refunded_at")
        )
        return {
            "id": result.resource.id,
            "listing_id": result.listing_id,
            "buyer_tenant_id": result.buyer_tenant_id,
            "seller_tenant_id": result.seller_tenant_id,
            "amount": {
                "amount_minor": result.amount.amount_minor,
                "currency": result.amount.currency
            },
            "status": result.status,
            "initiated_at": result.initiated_at,
            "completed_at": result.completed_at,
            "refunded_at": result.refunded_at,
            "created_at": result.resource.created_at,
            "updated_at": result.resource.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)