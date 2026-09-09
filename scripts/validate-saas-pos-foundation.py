#!/usr/bin/env python3
from pathlib import Path
import importlib
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"
BAAS = ROOT / "baas"

# The validator executes from scripts/, but Kernel modules use package-relative
# imports (for example kernel.authorization.runtime -> ..identity.context).
# Add the repository root to sys.path and import by dotted package name so
# Python preserves the package context required by those relative imports.
root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(0, root_text)

MODULES = {
    "saas.runtime.product_context": (
        SAAS / "runtime/product_context.py"
    ),
    "saas.pos.foundation.runtime": (
        SAAS / "pos/foundation/runtime.py"
    ),
    "kernel.authorization.runtime": (
        KERNEL / "authorization/runtime.py"
    ),
    "kernel.commerce.variant_identifiers": (
        KERNEL / "commerce/variant_identifiers.py"
    ),
    "baas.auth.runtime": (
        BAAS / "auth/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing POS foundation runtime file: {path}"
        )
    py_compile.compile(
        str(path),
        doraise=True,
    )


def load_module(module_name):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        raise SystemExit(
            f"ERROR: unable to import package module {module_name}: {exc}"
        ) from exc


foundation = load_module(
    "saas.runtime.product_context"
)
pos = load_module(
    "saas.pos.foundation.runtime"
)
authorization = load_module(
    "kernel.authorization.runtime"
)
identifiers = load_module(
    "kernel.commerce.variant_identifiers"
)
auth = load_module(
    "baas.auth.runtime"
)

auth_registry = auth.AuthenticationRegistry()

identity = auth.IdentityRecord(
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    organization_id="org-validation",
    identity_ref="identity://staff-validation",
    enabled=True,
    metadata={"display_name": "Validation Cashier"},
)
auth_registry.register_identity(identity)

permission_registry = (
    authorization.PermissionRegistry()
)
role_registry = (
    authorization.RoleRegistry()
)

planner = foundation.CommercePOSFoundation()

service = pos.POSFoundationService(
    foundation=planner,
    product_command_type=foundation.ProductCommand,
    auth_registry=auth_registry,
    permission_registry=permission_registry,
    role_registry=role_registry,
    permission_definition_type=(
        authorization.PermissionDefinition
    ),
    role_definition_type=(
        authorization.RoleDefinition
    ),
    barcode_validator=(
        identifiers.validate_barcode
    ),
)

setup_context = foundation.ProductContext(
    product="POS",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="owner-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_setup_validation",
    correlation_id="corr-pos-setup-validation",
    store_id="store-validation",
    branch_id=None,
)

store_evidence = pos.CommerceEvidence(
    source="kernel.commerce",
    entity_type="STORE",
    entity_id="store-validation",
    organization_id=setup_context.organization_id,
    workspace_id=setup_context.workspace_id,
    project_id=setup_context.project_id,
    environment_id=setup_context.environment_id,
    status="ACTIVE",
)

branch = service.plan_branch_create(
    context=setup_context,
    request=pos.BranchSetupRequest(
        branch_id="branch-validation",
        store_id="store-validation",
        name="Validation Branch",
        status="ACTIVE",
        idempotency_key="branch-validation-create",
        requested_at="2026-09-09T15:00:00+00:00",
    ),
    store_evidence=store_evidence,
)

if (
    branch["plan"].entity_type
    != "BRANCH"
    or branch["plan"].authority
    != "kernel.commerce"
):
    raise SystemExit(
        "ERROR: Branch did not route to Kernel commerce"
    )

branch_duplicate = service.plan_branch_create(
    context=setup_context,
    request=pos.BranchSetupRequest(
        branch_id="branch-validation",
        store_id="store-validation",
        name="Validation Branch",
        status="ACTIVE",
        idempotency_key="branch-validation-create",
        requested_at="2026-09-09T15:00:00+00:00",
    ),
    store_evidence=store_evidence,
)

if (
    branch_duplicate["created"] is not False
    or branch_duplicate["plan"].command_id
    != branch["plan"].command_id
):
    raise SystemExit(
        "ERROR: Branch creation idempotency failed"
    )

context = foundation.ProductContext(
    product="POS",
    organization_id=setup_context.organization_id,
    workspace_id=setup_context.workspace_id,
    project_id=setup_context.project_id,
    environment_id=setup_context.environment_id,
    actor_id="owner-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_operations_validation",
    correlation_id="corr-pos-operations-validation",
    store_id="store-validation",
    branch_id="branch-validation",
)

branch_evidence = pos.CommerceEvidence(
    source="kernel.commerce",
    entity_type="BRANCH",
    entity_id="branch-validation",
    organization_id=context.organization_id,
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
    status="ACTIVE",
)

role_result = service.register_role(
    context=context,
    request=pos.RoleRegistrationRequest(
        role_id="pos.cashier",
        permissions=frozenset({
            "pos.branch.read",
            "pos.product.read",
            "pos.cart.create",
            "pos.cart.update",
            "pos.checkout.execute",
            "pos.payment.cash.record",
            "pos.payment.card.record",
            "pos.receipt.issue",
        }),
    ),
)

if role_result.authority != "kernel.authorization":
    raise SystemExit(
        "ERROR: POS Role did not remain Kernel-authoritative"
    )

again = service.register_role(
    context=context,
    request=pos.RoleRegistrationRequest(
        role_id="pos.cashier",
        permissions=frozenset({
            "pos.branch.read",
            "pos.product.read",
            "pos.cart.create",
            "pos.cart.update",
            "pos.checkout.execute",
            "pos.payment.cash.record",
            "pos.payment.card.record",
            "pos.receipt.issue",
        }),
    ),
)

if again.created is not False:
    raise SystemExit(
        "ERROR: identical Kernel Role registration was not idempotent"
    )

try:
    service.register_role(
        context=context,
        request=pos.RoleRegistrationRequest(
            role_id="pos.bad-role",
            permissions=frozenset({
                "kernel.cross_tenant",
            }),
        ),
    )
except pos.POSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: POS Role accepted unsupported privileged permission"
    )

assignment_result = service.assign_staff(
    context=context,
    actor_id="staff-validation",
    role_id="pos.cashier",
    branch_evidence=branch_evidence,
    assigned_at="2026-09-09T15:01:00+00:00",
)

assignment = assignment_result["assignment"]

if (
    assignment.actor_id
    != "staff-validation"
    or assignment.role_id
    != "pos.cashier"
    or assignment.branch_id
    != "branch-validation"
):
    raise SystemExit(
        "ERROR: Staff assignment did not preserve identity/role/branch"
    )

staff_context = service.staff_context(
    context=context,
    actor_id="staff-validation",
)

if (
    staff_context.assignment_id
    != assignment.assignment_id
):
    raise SystemExit(
        "ERROR: POS staff context resolution failed"
    )

search_text = service.plan_product_search(
    context=context,
    branch_evidence=branch_evidence,
    query=pos.ProductSearchQuery(
        mode="TEXT",
        value="validation product",
        available_only=True,
        limit=25,
    ),
)

if (
    search_text.state
    != "READY_FOR_POS_PRODUCT_SEARCH_ADAPTER"
):
    raise SystemExit(
        "ERROR: Product search claimed authoritative search state"
    )

if (
    search_text.filters["branch_id"]
    != "branch-validation"
    or search_text.filters["product_status"]
    != "ACTIVE"
):
    raise SystemExit(
        "ERROR: Product search branch/status scope missing"
    )

sku = service.plan_product_search(
    context=context,
    branch_evidence=branch_evidence,
    query=pos.ProductSearchQuery(
        mode="SKU",
        value="SKU-VALIDATION-001",
        available_only=True,
        limit=1,
    ),
)

if (
    sku.filters.get("sku_exact")
    != "SKU-VALIDATION-001"
):
    raise SystemExit(
        "ERROR: exact SKU lookup filter missing"
    )

barcode = service.plan_product_search(
    context=context,
    branch_evidence=branch_evidence,
    query=pos.ProductSearchQuery(
        mode="BARCODE",
        value="6001234567890",
        available_only=True,
        limit=1,
    ),
)

if (
    barcode.filters.get("barcode_exact")
    != "6001234567890"
):
    raise SystemExit(
        "ERROR: exact barcode lookup filter missing"
    )

try:
    service.plan_product_search(
        context=context,
        branch_evidence=branch_evidence,
        query=pos.ProductSearchQuery(
            mode="BARCODE",
            value="bad barcode with spaces",
            available_only=True,
            limit=1,
        ),
    )
except pos.POSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: unsafe barcode was accepted"
    )

cross_branch = pos.CommerceEvidence(
    source="kernel.commerce",
    entity_type="BRANCH",
    entity_id="branch-validation",
    organization_id="org-other",
    workspace_id=context.workspace_id,
    project_id=context.project_id,
    environment_id=context.environment_id,
    status="ACTIVE",
)

try:
    service.plan_product_search(
        context=context,
        branch_evidence=cross_branch,
        query=pos.ProductSearchQuery(
            mode="SKU",
            value="SKU-VALIDATION-001",
            limit=1,
        ),
    )
except pos.POSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant Branch search evidence was accepted"
    )

disabled_identity = auth.IdentityRecord(
    actor_id="disabled-staff",
    actor_type="HUMAN_USER",
    organization_id=context.organization_id,
    identity_ref="identity://disabled-staff",
    enabled=False,
)
auth_registry.register_identity(
    disabled_identity
)

try:
    service.assign_staff(
        context=context,
        actor_id="disabled-staff",
        role_id="pos.cashier",
        branch_evidence=branch_evidence,
    )
except pos.POSFoundationError:
    pass
else:
    raise SystemExit(
        "ERROR: disabled BaaS identity was accepted as POS staff"
    )

migration = (
    KERNEL
    / "migrations/sql/0003_kernel_product_variant_barcode.sql"
).read_text(
    encoding="utf-8"
)

for marker in [
    "ADD COLUMN IF NOT EXISTS barcode text",
    "uq_product_variants_org_barcode",
    "WHERE barcode IS NOT NULL",
]:
    if marker not in migration:
        raise SystemExit(
            "ERROR: barcode migration missing: "
            + marker
        )

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Branches",
    "- [x] Staff",
    "- [x] Roles",
    "- [x] Product search",
    "- [x] Barcode and SKU lookup",
    "- [x] Cart",
    "- [x] Checkout",
    "DALIZEBO POS P0: COMPLETE",
    "PHASE 6: COMPLETE",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: POS foundation status missing: "
            + phrase
        )

print("OK: Branch creation/lifecycle remains Kernel-authoritative.")
print("OK: POS roles use Kernel Permission/Role registries.")
print("OK: Staff references existing BaaS HUMAN_USER identity.")
print("OK: Branch-scoped staff assignment/control passed.")
print("OK: Product search is exact-tenant/store/branch scoped.")
print("OK: Exact SKU lookup passed.")
print("OK: Canonical shared Variant barcode lookup passed.")
print("OK: Cross-tenant Branch evidence fails closed.")
print("STATUS: POS P0 BRANCHES + STAFF + ROLES + PRODUCT SEARCH READY")
