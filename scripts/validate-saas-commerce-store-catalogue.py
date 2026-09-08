#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"

MODULES = {
    "saas_product_context": (
        SAAS / "runtime/product_context.py"
    ),
    "commerce_store_catalogue": (
        SAAS / "commerce/catalogue/runtime.py"
    ),
    "kernel_commerce": (
        KERNEL / "commerce/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Store/Catalogue runtime file: {path}"
        )
    py_compile.compile(
        str(path),
        doraise=True,
    )


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )
    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERROR: unable to load module: {path}"
        )
    module = importlib.util.module_from_spec(
        spec
    )
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


foundation = load_module(
    "saas_product_context",
    MODULES["saas_product_context"],
)
commerce = load_module(
    "commerce_store_catalogue",
    MODULES["commerce_store_catalogue"],
)
kernel = load_module(
    "kernel_commerce",
    MODULES["kernel_commerce"],
)

planner = foundation.CommercePOSFoundation()

service = commerce.CommerceStoreCatalogueService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    kernel_tenant_scope_type=kernel.TenantScope,
    kernel_resource_type=kernel.CommerceResource,
    kernel_variant_type=kernel.ProductVariant,
    kernel_money_type=kernel.Money,
)

context = foundation.ProductContext(
    product="COMMERCE",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_commerce_catalogue_validation",
    correlation_id="corr-commerce-catalogue-validation",
)

store_request = commerce.StoreSetupRequest(
    store_id="store-validation",
    name="Validation Store",
    status="ACTIVE",
    idempotency_key="store-validation-create",
    requested_at="2026-09-09T10:00:00+00:00",
)

store_plan = service.plan_store_setup(
    context=context,
    request=store_request,
)

if store_plan["plan"].authority != "kernel.commerce":
    raise SystemExit(
        "ERROR: Store setup did not route to Kernel commerce"
    )

if store_plan["plan"].entity_id != "store-validation":
    raise SystemExit(
        "ERROR: shared Store ID was not preserved"
    )

store_duplicate = service.plan_store_setup(
    context=context,
    request=store_request,
)

if (
    store_duplicate["created"] is not False
    or store_duplicate["plan"].command_id
    != store_plan["plan"].command_id
):
    raise SystemExit(
        "ERROR: Store setup idempotency failed"
    )

store_evidence = commerce.AuthorityEvidence(
    source="kernel.commerce",
    entity_type="STORE",
    entity_id="store-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

store_transition = service.plan_store_status(
    context=context,
    store_evidence=store_evidence,
    current_status="ACTIVE",
    target_status="INACTIVE",
    idempotency_key="store-validation-disable",
    requested_at="2026-09-09T10:01:00+00:00",
)

if (
    store_transition["plan"].input_metadata["to_status"]
    != "INACTIVE"
):
    raise SystemExit(
        "ERROR: Store lifecycle transition was not preserved"
    )

product_request = commerce.ProductCreateRequest(
    product_id="product-validation",
    name="Validation Product",
    description="Test product",
    status="DRAFT",
    idempotency_key="product-validation-create",
    requested_at="2026-09-09T10:02:00+00:00",
)

product_plan = service.plan_product_create(
    context=context,
    request=product_request,
)

if product_plan["plan"].entity_type != "PRODUCT":
    raise SystemExit(
        "ERROR: Product create command has wrong entity type"
    )

product_evidence = commerce.AuthorityEvidence(
    source="kernel.commerce",
    entity_type="PRODUCT",
    entity_id="product-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

activate = service.plan_product_status(
    context=context,
    product_evidence=product_evidence,
    current_status="DRAFT",
    target_status="ACTIVE",
    idempotency_key="product-validation-activate",
    requested_at="2026-09-09T10:03:00+00:00",
)

if activate["plan"].input_metadata["to_status"] != "ACTIVE":
    raise SystemExit(
        "ERROR: Product activation transition failed"
    )

try:
    service.plan_product_status(
        context=context,
        product_evidence=product_evidence,
        current_status="ACTIVE",
        target_status="DRAFT",
        idempotency_key="product-validation-illegal",
        requested_at="2026-09-09T10:04:00+00:00",
    )
except commerce.CommerceStoreCatalogueError:
    pass
else:
    raise SystemExit(
        "ERROR: illegal Product lifecycle transition was accepted"
    )

variant_request = commerce.ProductVariantCreateRequest(
    variant_id="variant-validation",
    product_id="product-validation",
    sku="SKU-VALIDATION-001",
    price_minor=12999,
    currency="ZAR",
    active=True,
    idempotency_key="variant-validation-create",
    requested_at="2026-09-09T10:05:00+00:00",
)

variant_plan = service.plan_variant_create(
    context=context,
    product_evidence=product_evidence,
    request=variant_request,
)

if (
    variant_plan["plan"].input_metadata["price_minor"]
    != 12999
):
    raise SystemExit(
        "ERROR: Variant integer minor-unit price was not preserved"
    )

if (
    variant_plan["plan"].input_metadata["currency"]
    != "ZAR"
):
    raise SystemExit(
        "ERROR: Variant currency normalization failed"
    )

variant_evidence = commerce.AuthorityEvidence(
    source="kernel.commerce",
    entity_type="PRODUCT_VARIANT",
    entity_id="variant-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

price_update = service.plan_variant_price_update(
    context=context,
    variant_evidence=variant_evidence,
    product_evidence=product_evidence,
    request=commerce.VariantPriceUpdateRequest(
        variant_id="variant-validation",
        product_id="product-validation",
        sku="SKU-VALIDATION-001",
        price_minor=14999,
        currency="ZAR",
        active=True,
        idempotency_key="variant-validation-price-14999",
        requested_at="2026-09-09T10:06:00+00:00",
    ),
)

if (
    price_update["plan"].action != "UPDATE"
    or price_update["plan"].input_metadata["price_minor"]
    != 14999
):
    raise SystemExit(
        "ERROR: Variant pricing update plan failed"
    )

try:
    service.plan_variant_create(
        context=context,
        product_evidence=product_evidence,
        request=commerce.ProductVariantCreateRequest(
            variant_id="variant-float",
            product_id="product-validation",
            sku="SKU-FLOAT",
            price_minor=129.99,
            currency="ZAR",
            active=True,
            idempotency_key="variant-float-create",
            requested_at="2026-09-09T10:07:00+00:00",
        ),
    )
except commerce.CommerceStoreCatalogueError:
    pass
else:
    raise SystemExit(
        "ERROR: floating-point Variant price was accepted"
    )

try:
    service.plan_variant_create(
        context=context,
        product_evidence=product_evidence,
        request=commerce.ProductVariantCreateRequest(
            variant_id="variant-currency",
            product_id="product-validation",
            sku="SKU-CURRENCY",
            price_minor=1000,
            currency="ZA",
            active=True,
            idempotency_key="variant-currency-create",
            requested_at="2026-09-09T10:08:00+00:00",
        ),
    )
except commerce.CommerceStoreCatalogueError:
    pass
else:
    raise SystemExit(
        "ERROR: invalid Variant currency was accepted"
    )

cross_evidence = commerce.AuthorityEvidence(
    source="kernel.commerce",
    entity_type="PRODUCT",
    entity_id="product-validation",
    organization_id="org-other",
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

try:
    service.plan_variant_create(
        context=context,
        product_evidence=cross_evidence,
        request=commerce.ProductVariantCreateRequest(
            variant_id="variant-cross",
            product_id="product-validation",
            sku="SKU-CROSS",
            price_minor=1000,
            currency="ZAR",
            active=True,
            idempotency_key="variant-cross-create",
            requested_at="2026-09-09T10:09:00+00:00",
        ),
    )
except commerce.CommerceStoreCatalogueError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant Product evidence was accepted"
    )

pos_context = foundation.ProductContext(
    product="POS",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_catalogue_validation",
    correlation_id="corr-pos-catalogue-validation",
    store_id="store-validation",
    branch_id="branch-validation",
)

try:
    service.plan_product_create(
        context=pos_context,
        request=product_request,
    )
except commerce.CommerceStoreCatalogueError:
    pass
else:
    raise SystemExit(
        "ERROR: POS context was accepted by Commerce Store/Catalogue service"
    )

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Store setup",
    "- [x] Product catalogue",
    "- [x] Variants",
    "- [x] Pricing",
    "- [x] Cross-tenant authority evidence rejection",
    "- [ ] Inventory",
    "Commerce P0 — Inventory + Customers.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Store/Catalogue status missing: "
            + phrase
        )

print("OK: Store setup routes to Kernel commerce authority.")
print("OK: Store lifecycle and idempotency passed.")
print("OK: Product lifecycle passed.")
print("OK: Product Variant uses Kernel runtime validation.")
print("OK: Integer minor-unit Variant pricing passed.")
print("OK: Variant price update planning passed.")
print("OK: Cross-tenant parent authority evidence fails closed.")
print("OK: Commerce service rejects POS product context.")
print("STATUS: COMMERCE P0 STORE + CATALOGUE READY")
