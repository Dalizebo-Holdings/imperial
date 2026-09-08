#!/usr/bin/env python3
from pathlib import Path
from dataclasses import dataclass
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"

MODULES = {
    "saas_product_context": SAAS / "runtime/product_context.py",
    "commerce_inventory": SAAS / "commerce/inventory/runtime.py",
    "commerce_customers": SAAS / "commerce/customers/runtime.py",
    "kernel_commerce": KERNEL / "commerce/runtime.py",
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(f"ERROR: missing runtime file: {path}")
    py_compile.compile(str(path), doraise=True)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"ERROR: unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


foundation = load_module(
    "saas_product_context",
    MODULES["saas_product_context"],
)
inventory = load_module(
    "commerce_inventory",
    MODULES["commerce_inventory"],
)
customers = load_module(
    "commerce_customers",
    MODULES["commerce_customers"],
)
kernel = load_module(
    "kernel_commerce",
    MODULES["kernel_commerce"],
)


@dataclass(frozen=True)
class Evidence:
    source: str
    entity_type: str
    entity_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self):
        if self.source != "kernel.commerce":
            raise ValueError("bad source")


planner = foundation.CommercePOSFoundation()

context = foundation.ProductContext(
    product="COMMERCE",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_inventory_customer_validation",
    correlation_id="corr-inventory-customer-validation",
    store_id="store-validation",
    branch_id=None,
)

inventory_service = inventory.CommerceInventoryService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    kernel_tenant_scope_type=kernel.TenantScope,
    kernel_resource_type=kernel.CommerceResource,
    kernel_inventory_type=kernel.InventoryItem,
)

variant_evidence = Evidence(
    source="kernel.commerce",
    entity_type="PRODUCT_VARIANT",
    entity_id="variant-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

store_evidence = Evidence(
    source="kernel.commerce",
    entity_type="STORE",
    entity_id="store-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

create = inventory_service.plan_create(
    context=context,
    request=inventory.InventoryCreateRequest(
        inventory_item_id="inventory-validation",
        product_variant_id="variant-validation",
        store_id="store-validation",
        branch_id=None,
        quantity_on_hand=100,
        quantity_reserved=10,
        idempotency_key="inventory-validation-create",
        requested_at="2026-09-09T12:00:00+00:00",
    ),
    variant_evidence=variant_evidence,
    store_evidence=store_evidence,
)

if create["plan"].entity_type != "INVENTORY_ITEM":
    raise SystemExit("ERROR: inventory create entity mismatch")

if create["plan"].input_metadata["quantity_reserved"] != 10:
    raise SystemExit("ERROR: inventory reserved quantity lost")

inventory_evidence = Evidence(
    source="kernel.commerce",
    entity_type="INVENTORY_ITEM",
    entity_id="inventory-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

adjust = inventory_service.plan_adjustment(
    context=context,
    request=inventory.InventoryAdjustmentRequest(
        inventory_item_id="inventory-validation",
        product_variant_id="variant-validation",
        store_id="store-validation",
        branch_id=None,
        expected_quantity_on_hand=100,
        expected_quantity_reserved=10,
        quantity_on_hand_delta=-5,
        quantity_reserved_delta=5,
        reason="Manual stock reconciliation",
        source_ref="commerce://inventory/reconciliation/001",
        idempotency_key="inventory-validation-adjust-1",
        requested_at="2026-09-09T12:01:00+00:00",
    ),
    inventory_evidence=inventory_evidence,
    variant_evidence=variant_evidence,
    store_evidence=store_evidence,
)

if (
    adjust["plan"].input_metadata["target_quantity_on_hand"] != 95
    or adjust["plan"].input_metadata["target_quantity_reserved"] != 15
):
    raise SystemExit("ERROR: inventory target quantity calculation failed")

if (
    adjust["plan"].input_metadata["persistence_requirement"]
    != "ATOMIC_COMPARE_EXPECTED_AND_UPDATE"
):
    raise SystemExit("ERROR: expected-value persistence requirement missing")

try:
    inventory_service.plan_adjustment(
        context=context,
        request=inventory.InventoryAdjustmentRequest(
            inventory_item_id="inventory-validation",
            product_variant_id="variant-validation",
            store_id="store-validation",
            branch_id=None,
            expected_quantity_on_hand=20,
            expected_quantity_reserved=15,
            quantity_on_hand_delta=-10,
            quantity_reserved_delta=0,
            reason="Invalid shrink",
            source_ref="commerce://inventory/invalid",
            idempotency_key="inventory-invalid-reserved",
            requested_at="2026-09-09T12:02:00+00:00",
        ),
        inventory_evidence=inventory_evidence,
        variant_evidence=variant_evidence,
        store_evidence=store_evidence,
    )
except inventory.CommerceInventoryError:
    pass
else:
    raise SystemExit(
        "ERROR: inventory adjustment allowed reserved > on-hand"
    )

cross_variant = Evidence(
    source="kernel.commerce",
    entity_type="PRODUCT_VARIANT",
    entity_id="variant-validation",
    organization_id="org-other",
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

try:
    inventory_service.plan_create(
        context=context,
        request=inventory.InventoryCreateRequest(
            inventory_item_id="inventory-cross",
            product_variant_id="variant-validation",
            store_id="store-validation",
            branch_id=None,
            quantity_on_hand=10,
            quantity_reserved=0,
            idempotency_key="inventory-cross-create",
            requested_at="2026-09-09T12:03:00+00:00",
        ),
        variant_evidence=cross_variant,
        store_evidence=store_evidence,
    )
except inventory.CommerceInventoryError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant inventory parent evidence was accepted"
    )

customer_service = customers.CommerceCustomersService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
)

customer = customer_service.plan_create(
    context=context,
    request=customers.CustomerCreateRequest(
        customer_id="customer-validation",
        display_name="Validation Customer",
        external_identity_ref="identity://customer-validation",
        email="Customer@Example.COM",
        phone="+27 11 555 0100",
        pii_policy_ref="pii-policy://customer-contact/v1",
        retention_policy_ref="retention-policy://customer-contact/v1",
        idempotency_key="customer-validation-create",
        requested_at="2026-09-09T12:04:00+00:00",
    ),
)

if (
    customer["plan"].input_metadata["email"]
    != "customer@example.com"
):
    raise SystemExit("ERROR: customer email normalization failed")

if (
    customer["plan"].input_metadata["data_classification"]
    != "PERSONAL_DATA"
):
    raise SystemExit("ERROR: customer contact PII classification missing")

if (
    customer["plan"].input_metadata["audit_logging_policy"]
    != "DO_NOT_LOG_CONTACT_VALUES"
):
    raise SystemExit("ERROR: customer contact audit suppression directive missing")

if "email" in str(customer["plan"].audit_event).lower():
    raise SystemExit("ERROR: customer email leaked into product audit event")

try:
    customer_service.plan_create(
        context=context,
        request=customers.CustomerCreateRequest(
            customer_id="customer-no-policy",
            display_name="No Policy",
            external_identity_ref=None,
            email="no-policy@example.com",
            phone=None,
            pii_policy_ref=None,
            retention_policy_ref=None,
            idempotency_key="customer-no-policy-create",
            requested_at="2026-09-09T12:05:00+00:00",
        ),
    )
except customers.CommerceCustomersError:
    pass
else:
    raise SystemExit(
        "ERROR: contact PII was accepted without policy references"
    )

customer_evidence = Evidence(
    source="kernel.commerce",
    entity_type="CUSTOMER",
    entity_id="customer-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

updated = customer_service.plan_update(
    context=context,
    customer_evidence=customer_evidence,
    request=customers.CustomerUpdateRequest(
        customer_id="customer-validation",
        display_name="Validation Customer Updated",
        external_identity_ref="identity://customer-validation",
        email=None,
        phone=None,
        pii_policy_ref=None,
        retention_policy_ref=None,
        idempotency_key="customer-validation-update",
        requested_at="2026-09-09T12:06:00+00:00",
    ),
)

if updated["plan"].action != "UPDATE":
    raise SystemExit("ERROR: customer update action mismatch")

cross_customer = Evidence(
    source="kernel.commerce",
    entity_type="CUSTOMER",
    entity_id="customer-validation",
    organization_id="org-other",
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
)

try:
    customer_service.plan_update(
        context=context,
        customer_evidence=cross_customer,
        request=customers.CustomerUpdateRequest(
            customer_id="customer-validation",
            display_name="Cross Tenant",
            external_identity_ref=None,
            email=None,
            phone=None,
            pii_policy_ref=None,
            retention_policy_ref=None,
            idempotency_key="customer-cross-update",
            requested_at="2026-09-09T12:07:00+00:00",
        ),
    )
except customers.CommerceCustomersError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant Customer evidence was accepted"
    )

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(encoding="utf-8")

for phrase in [
    "- [x] Inventory",
    "- [x] Customers",
    "- [x] Optimistic expected-quantity persistence requirement",
    "- [x] PII policy reference requirement",
    "- [ ] Cart",
    "Commerce P0 — Cart + Checkout + Orders.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Inventory/Customers status missing: " + phrase
        )

print("OK: Kernel InventoryItem authority and invariants passed.")
print("OK: Explicit expected-value inventory adjustment passed.")
print("OK: Reserved stock cannot exceed on-hand stock.")
print("OK: Cross-tenant inventory evidence fails closed.")
print("OK: Customer create/update remains Kernel-authoritative.")
print("OK: Customer contact PII requires policy + retention references.")
print("OK: Customer contact values do not enter product audit metadata.")
print("OK: Cross-tenant Customer evidence fails closed.")
print("STATUS: COMMERCE P0 INVENTORY + CUSTOMERS READY")
