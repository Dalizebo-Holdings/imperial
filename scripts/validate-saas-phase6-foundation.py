#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
PATH = SAAS / "runtime/product_context.py"

if not PATH.exists():
    raise SystemExit(
        f"ERROR: missing Phase 6 runtime: {PATH}"
    )

py_compile.compile(
    str(PATH),
    doraise=True,
)

spec = importlib.util.spec_from_file_location(
    "saas_product_context",
    PATH,
)

if spec is None or spec.loader is None:
    raise SystemExit(
        "ERROR: unable to load Phase 6 runtime"
    )

runtime = importlib.util.module_from_spec(
    spec
)
sys.modules[
    "saas_product_context"
] = runtime
spec.loader.exec_module(
    runtime
)

router = runtime.CommercePOSFoundation()

commerce_context = runtime.ProductContext(
    product="COMMERCE",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="actor-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_phase6_validation",
    correlation_id="corr-commerce-validation",
)

store_create = runtime.ProductCommand(
    action="CREATE",
    entity_type="STORE",
    context=commerce_context,
    idempotency_key="store-create-validation",
    input_metadata={
        "name": "Validation Store",
        "currency": "ZAR",
    },
)

first = router.plan(
    store_create
)

if (
    first["plan"].authority
    != "kernel.commerce"
):
    raise SystemExit(
        "ERROR: Commerce STORE authority did not route to Kernel commerce"
    )

if (
    first["plan"].baas_service
    != "baas.database"
):
    raise SystemExit(
        "ERROR: Commerce STORE platform service route mismatch"
    )

duplicate = router.plan(
    store_create
)

if (
    duplicate["created"] is not False
    or duplicate["plan"].command_id
    != first["plan"].command_id
):
    raise SystemExit(
        "ERROR: product mutation idempotency failed"
    )

try:
    router.plan(
        runtime.ProductCommand(
            action="CREATE",
            entity_type="STORE",
            context=commerce_context,
            idempotency_key="store-create-validation",
            input_metadata={
                "name": "Different Store",
                "currency": "ZAR",
            },
        )
    )
except runtime.SaaSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: idempotency key accepted conflicting product command"
    )

try:
    router.plan(
        runtime.ProductCommand(
            action="CREATE",
            entity_type="ORDER",
            context=commerce_context,
            idempotency_key="order-no-store",
            input_metadata={},
        )
    )
except runtime.SaaSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: Commerce operational command without store context was accepted"
    )

pos_context = runtime.ProductContext(
    product="POS",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_validation",
    correlation_id="corr-pos-validation",
    store_id="store-validation",
    branch_id="branch-validation",
)

product_lookup = router.plan(
    runtime.ProductCommand(
        action="READ",
        entity_type="PRODUCT",
        entity_id="product-validation",
        context=pos_context,
        idempotency_key=None,
        input_metadata={
            "lookup": "SKU-001",
        },
    )
)

if (
    product_lookup["plan"].authority
    != "kernel.commerce"
):
    raise SystemExit(
        "ERROR: POS PRODUCT authority did not route to Kernel commerce"
    )

if (
    product_lookup["plan"].branch_id
    != "branch-validation"
):
    raise SystemExit(
        "ERROR: POS branch context was not preserved"
    )

try:
    router.plan(
        runtime.ProductCommand(
            action="READ",
            entity_type="PRODUCT",
            entity_id="product-validation",
            context=runtime.ProductContext(
                product="POS",
                organization_id="org-validation",
                workspace_id="workspace-validation",
                project_id="project-validation",
                environment_id="env-validation",
                actor_id="staff-validation",
                actor_type="HUMAN_USER",
                kernel_authorization_ref="kernel_auth_pos_validation",
                correlation_id="corr-pos-no-branch",
                store_id="store-validation",
            ),
            idempotency_key=None,
            input_metadata={},
        )
    )
except runtime.SaaSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: POS operational command without branch context was accepted"
    )

payment_plan = router.plan(
    runtime.ProductCommand(
        action="EXECUTE",
        entity_type="PAYMENT",
        entity_id="payment-validation",
        context=pos_context,
        idempotency_key="payment-validation",
        input_metadata={
            "amount_minor": 1000,
            "currency": "ZAR",
        },
    )
)

if (
    payment_plan["plan"].baas_service
    != "baas.payment_abstraction"
):
    raise SystemExit(
        "ERROR: Payment did not route through Payment Abstraction"
    )

try:
    router.plan(
        runtime.ProductCommand(
            action="EXECUTE",
            entity_type="PAYMENT",
            entity_id="payment-secret",
            context=pos_context,
            idempotency_key="payment-secret",
            input_metadata={
                "card_number": "4111111111111111"
            },
        )
    )
except runtime.SaaSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: secret/payment-authentication metadata was accepted"
    )

try:
    router.plan(
        runtime.ProductCommand(
            action="UPDATE",
            entity_type="PRODUCT",
            entity_id="product-validation",
            context=pos_context,
            idempotency_key=None,
            input_metadata={
                "name": "Changed"
            },
        )
    )
except runtime.SaaSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: mutable product command without idempotency was accepted"
    )

if set(
    runtime.AUTHORITY_ROUTES
) != runtime.SHARED_ENTITIES:
    raise SystemExit(
        "ERROR: not every shared entity has an authority route"
    )

status = (
    SAAS
    / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Commerce/POS product execution context",
    "- [x] Derived Kernel/BaaS authority routing",
    "- [x] Mutation idempotency",
    "- [x] No duplicate authoritative commerce models",
    "- [ ] Store setup",
    "Commerce P0 — Store + Catalogue.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: Phase 6 status missing: "
            + phrase
        )

print("OK: Commerce/POS execution context passed.")
print("OK: All shared SaaS entities have derived authority routes.")
print("OK: Commerce STORE commands route to Kernel commerce.")
print("OK: POS operational commands require branch context.")
print("OK: Payment commands route through Payment Abstraction.")
print("OK: Mutation idempotency and conflict detection passed.")
print("OK: Secret/payment-authentication metadata is rejected.")
print("OK: No direct product-selected database authority exists.")
print("STATUS: PHASE 6 COMMERCE + POS FOUNDATION READY")
