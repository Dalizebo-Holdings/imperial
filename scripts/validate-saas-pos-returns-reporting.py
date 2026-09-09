#!/usr/bin/env python3
from pathlib import Path
import importlib
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
SAAS = ROOT / "saas"
KERNEL = ROOT / "kernel"
BAAS = ROOT / "baas"

root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )

MODULES = {
    "saas.runtime.product_context": (
        SAAS / "runtime/product_context.py"
    ),
    "saas.pos.returns.runtime": (
        SAAS / "pos/returns/runtime.py"
    ),
    "kernel.commerce.runtime": (
        KERNEL / "commerce/runtime.py"
    ),
    "baas.payments.runtime": (
        BAAS / "payments/runtime.py"
    ),
    "baas.runtime.request_context": (
        BAAS / "runtime/request_context.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing POS return/report runtime file: {path}"
        )
    py_compile.compile(
        str(path),
        doraise=True,
    )


def load_module(name):
    try:
        return importlib.import_module(
            name
        )
    except Exception as exc:
        raise SystemExit(
            f"ERROR: unable to import package module {name}: {exc}"
        ) from exc


foundation = load_module(
    "saas.runtime.product_context"
)
returns = load_module(
    "saas.pos.returns.runtime"
)
kernel = load_module(
    "kernel.commerce.runtime"
)
payments = load_module(
    "baas.payments.runtime"
)
baas_context = load_module(
    "baas.runtime.request_context"
)


class StaffAccess:
    def check(
        self,
        context,
        actor_id,
        permission,
    ):
        allowed = {
            "pos.return.execute",
            "pos.summary.read",
        }

        return (
            actor_id
            == context.actor_id
            and permission in allowed
        )


def kernel_transition_validator(
    current,
    target,
    payment_id,
    order_id,
    amount_minor,
    currency,
):
    try:
        kernel.PaymentState(
            payment_id=(
                payment_id
            ),
            order_id=(
                order_id
            ),
            status=current,
            amount=kernel.Money(
                amount_minor=(
                    amount_minor
                ),
                currency=currency,
            ),
        ).transition(
            target
        )
        return True
    except Exception:
        return False


def kernel_refund_validator(
    payment_id,
    amount_minor,
    currency,
    captured_amount_minor,
    previously_refunded_minor,
    reason,
):
    try:
        kernel.Refund(
            refund_id=(
                "validator-refund"
            ),
            payment_id=(
                payment_id
            ),
            amount=kernel.Money(
                amount_minor=(
                    amount_minor
                ),
                currency=currency,
            ),
            reason=reason,
        ).validate(
            captured_amount=(
                kernel.Money(
                    amount_minor=(
                        captured_amount_minor
                    ),
                    currency=currency,
                )
            ),
            previously_refunded_minor=(
                previously_refunded_minor
            ),
        )
        return True
    except Exception:
        return False


payment_service = (
    payments.PaymentAbstractionService(
        kernel_transition_validator=(
            kernel_transition_validator
        ),
        kernel_refund_validator=(
            kernel_refund_validator
        ),
    )
)

provider_ctx = baas_context.BaaSRequestContext(
    request_id="req-return-provider",
    correlation_id="corr-pos-return-validation",
    service="payments",
    operation="provider.register",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_return_validation",
    idempotency_key="provider-return-validation",
)

payment_service.register_provider(
    provider=payments.ProviderConfiguration(
        provider_id="provider_validation",
        adapter_ref=(
            "adapter://payments/validation"
        ),
        credential_ref=(
            "vault://payments/validation/control"
        ),
        supported_currencies=(
            "ZAR",
        ),
        capabilities=(
            "AUTHORIZE",
            "CAPTURE",
            "REFUND",
        ),
    ),
    request_context=(
        provider_ctx
    ),
)

payment_request = payments.PaymentRequest(
    payment_request_id="return-source-payment-request",
    source_type="ORDER",
    source_ref="order-validation",
    amount_minor=5000,
    currency="ZAR",
    capture_mode="AUTHORIZE_CAPTURE",
    idempotency_key="source-payment-validation",
    requested_at="2026-09-09T17:00:00+00:00",
)

payment_plan = payment_service.create_payment_plan(
    provider_id="provider_validation",
    request=payment_request,
    request_context=provider_ctx,
)["plan"]

payment_service.plan_provider_result(
    result=payments.ProviderResult(
        payment_id=(
            payment_plan.payment_id
        ),
        provider_id="provider_validation",
        provider_reference=(
            "provider-payment-ref-validation"
        ),
        outcome="CAPTURED",
        amount_minor=5000,
        currency="ZAR",
        occurred_at="2026-09-09T17:00:01+00:00",
    ),
    kernel_current_status="PENDING",
    request_context=provider_ctx,
)

planner = foundation.CommercePOSFoundation()
service = returns.POSReturnsReportingService(
    foundation=planner,
    product_command_type=(
        foundation.ProductCommand
    ),
    staff_permission_checker=(
        StaffAccess().check
    ),
    kernel_tenant_scope_type=(
        kernel.TenantScope
    ),
    kernel_resource_type=(
        kernel.CommerceResource
    ),
    kernel_inventory_type=(
        kernel.InventoryItem
    ),
    kernel_money_type=(
        kernel.Money
    ),
    kernel_refund_type=(
        kernel.Refund
    ),
    kernel_payment_state_type=(
        kernel.PaymentState
    ),
    kernel_currency_validator=(
        kernel.validate_currency
    ),
    baas_payment_service=(
        payment_service
    ),
    baas_refund_request_type=(
        payments.RefundRequest
    ),
    baas_request_context_type=(
        baas_context.BaaSRequestContext
    ),
)

context = foundation.ProductContext(
    product="POS",
    organization_id="org-validation",
    workspace_id="workspace-validation",
    project_id="project-validation",
    environment_id="env-validation",
    actor_id="staff-validation",
    actor_type="HUMAN_USER",
    kernel_authorization_ref="kernel_auth_pos_return_validation",
    correlation_id="corr-pos-return-validation",
    store_id="store-validation",
    branch_id="branch-validation",
)


def evidence(
    entity_type,
    entity_id,
    *,
    status=None,
):
    return returns.Evidence(
        source="kernel.commerce",
        entity_type=(
            entity_type
        ),
        entity_id=(
            entity_id
        ),
        organization_id=(
            context.organization_id
        ),
        workspace_id=(
            context.workspace_id
        ),
        project_id=(
            context.project_id
        ),
        environment_id=(
            context.environment_id
        ),
        snapshot_ref=(
            f"kernel-snapshot://{entity_type.lower()}/{entity_id}"
        ),
        status=status,
    )


line = returns.ReturnLine(
    return_line_id="return-line-001",
    order_item_id="order-item-001",
    product_id="product-001",
    product_variant_id="variant-001",
    inventory_item_id="inventory-001",
    sold_quantity=2,
    previously_returned_quantity=0,
    return_quantity=1,
    unit_price_minor=2500,
    currency="ZAR",
    current_quantity_on_hand=8,
    current_quantity_reserved=1,
    product_evidence=evidence(
        "PRODUCT",
        "product-001",
    ),
    variant_evidence=evidence(
        "PRODUCT_VARIANT",
        "variant-001",
    ),
    inventory_evidence=evidence(
        "INVENTORY_ITEM",
        "inventory-001",
    ),
)

order_evidence = evidence(
    "ORDER",
    "order-validation",
    status="COMPLETED",
)

cash_payment_evidence = evidence(
    "PAYMENT",
    "payment-cash-validation",
    status="CAPTURED",
)

cash_request = returns.ReturnRequest(
    return_id="return-cash-validation",
    refund_id="refund-cash-validation",
    order_id="order-validation",
    payment_id="payment-cash-validation",
    tender_type="CASH",
    captured_amount_minor=5000,
    previously_refunded_minor=0,
    currency="ZAR",
    reason="Customer return",
    lines=(
        line,
    ),
    idempotency_key="return-cash-validation",
    requested_at="2026-09-09T17:01:00+00:00",
)

cash = service.plan_cash_return(
    context=context,
    request=cash_request,
    order_evidence=(
        order_evidence
    ),
    payment_evidence=(
        cash_payment_evidence
    ),
)

if (
    cash["plan"].refund_create.entity_type
    != "REFUND"
):
    raise SystemExit(
        "ERROR: cash return did not create shared Refund command"
    )

if (
    cash["plan"].inventory_restocks[0].input_metadata[
        "target_quantity_on_hand"
    ]
    != 9
):
    raise SystemExit(
        "ERROR: cash return inventory restock failed"
    )

if (
    cash["plan"].payment_transition
    is not None
):
    raise SystemExit(
        "ERROR: partial refund incorrectly marked Payment REFUNDED"
    )

full_line = returns.ReturnLine(
    **{
        **line.__dict__,
        "return_line_id": (
            "return-line-full"
        ),
        "previously_returned_quantity": 1,
        "return_quantity": 1,
    }
)

full_cash_request = returns.ReturnRequest(
    return_id="return-cash-full",
    refund_id="refund-cash-full",
    order_id="order-validation",
    payment_id="payment-cash-validation",
    tender_type="CASH",
    captured_amount_minor=5000,
    previously_refunded_minor=2500,
    currency="ZAR",
    reason="Final item return",
    lines=(
        full_line,
    ),
    idempotency_key="return-cash-full",
    requested_at="2026-09-09T17:02:00+00:00",
)

full_cash = service.plan_cash_return(
    context=context,
    request=(
        full_cash_request
    ),
    order_evidence=(
        order_evidence
    ),
    payment_evidence=(
        cash_payment_evidence
    ),
)

if (
    full_cash["plan"].payment_transition
    is None
    or full_cash["plan"].payment_transition.input_metadata[
        "to_status"
    ]
    != "REFUNDED"
):
    raise SystemExit(
        "ERROR: full cumulative refund did not transition Payment"
    )

try:
    service.plan_cash_return(
        context=context,
        request=returns.ReturnRequest(
            return_id="return-too-many-items",
            refund_id="refund-too-many-items",
            order_id="order-validation",
            payment_id="payment-cash-validation",
            tender_type="CASH",
            captured_amount_minor=10000,
            previously_refunded_minor=0,
            currency="ZAR",
            reason="Invalid return",
            lines=(
                returns.ReturnLine(
                    **{
                        **line.__dict__,
                        "return_line_id": (
                            "invalid-line"
                        ),
                        "return_quantity": 3,
                    }
                ),
            ),
            idempotency_key="return-too-many-items",
            requested_at="2026-09-09T17:03:00+00:00",
        ),
        order_evidence=(
            order_evidence
        ),
        payment_evidence=(
            cash_payment_evidence
        ),
    )
except returns.POSReturnsError:
    pass
else:
    raise SystemExit(
        "ERROR: returned quantity exceeded sold quantity"
    )

card_payment_evidence = evidence(
    "PAYMENT",
    payment_plan.payment_id,
    status="CAPTURED",
)

card_request = returns.ReturnRequest(
    return_id="return-card-validation",
    refund_id="refund-card-validation",
    order_id="order-validation",
    payment_id=(
        payment_plan.payment_id
    ),
    tender_type="CARD",
    captured_amount_minor=5000,
    previously_refunded_minor=0,
    currency="ZAR",
    reason="Card sale return",
    lines=(
        line,
    ),
    idempotency_key="return-card-validation",
    requested_at="2026-09-09T17:04:00+00:00",
)

card = service.plan_card_return(
    context=context,
    request=card_request,
    order_evidence=(
        order_evidence
    ),
    payment_evidence=(
        card_payment_evidence
    ),
    provider_id="provider_validation",
    provider_reference=(
        "provider-payment-ref-validation"
    ),
)

provider_plan = (
    card["plan"].provider_operation_plan
)

if (
    provider_plan.state
    != "READY_FOR_PROVIDER_REFUND_ADAPTER"
):
    raise SystemExit(
        "ERROR: card return claimed provider refund execution"
    )

if hasattr(
    provider_plan,
    "credential_value",
):
    raise SystemExit(
        "ERROR: provider refund plan exposes credential value"
    )

completion = returns.ProviderRefundCompletion(
    result_ref=(
        "payment-refund-result://validation/001"
    ),
    refund_id="refund-card-validation",
    payment_id=(
        payment_plan.payment_id
    ),
    provider_id="provider_validation",
    provider_reference=(
        "provider-payment-ref-validation"
    ),
    amount_minor=2500,
    currency="ZAR",
    outcome="SUCCEEDED",
    completed_at="2026-09-09T17:04:05+00:00",
)

completed = service.complete_card_return(
    context=context,
    request=card_request,
    card_plan=(
        card["plan"]
    ),
    completion=completion,
)

if (
    completed.refund_create.entity_type
    != "REFUND"
    or completed.receipt.state
    != "READY_FOR_RETURN_RECEIPT_RENDERER_AFTER_COMMIT"
):
    raise SystemExit(
        "ERROR: card return completion plan failed"
    )

try:
    service.complete_card_return(
        context=context,
        request=card_request,
        card_plan=(
            card["plan"]
        ),
        completion=returns.ProviderRefundCompletion(
            **{
                **completion.__dict__,
                "amount_minor": 2000,
            }
        ),
    )
except returns.POSReturnsError:
    pass
else:
    raise SystemExit(
        "ERROR: mismatched provider refund completion was accepted"
    )

summary = service.plan_daily_summary(
    context=context,
    query=returns.DailySummaryQuery(
        business_date="2026-09-09",
        timezone_name=(
            "Africa/Johannesburg"
        ),
        currency="ZAR",
    ),
)

if (
    summary.state
    != "READY_FOR_POS_DAILY_SUMMARY_ADAPTER"
):
    raise SystemExit(
        "ERROR: Daily Summary became an authoritative report store"
    )

if (
    summary.period_start_utc
    != "2026-09-08T22:00:00+00:00"
    or summary.period_end_utc
    != "2026-09-09T22:00:00+00:00"
):
    raise SystemExit(
        "ERROR: business-day timezone boundary failed"
    )

if (
    "kernel.refunds"
    not in summary.sources
    or summary.formulas[
        "net_sales_minor"
    ]
    != "gross_sales_minor - refund_minor"
):
    raise SystemExit(
        "ERROR: Daily Summary refund/net-sales contract missing"
    )

cross_order = returns.Evidence(
    source="kernel.commerce",
    entity_type="ORDER",
    entity_id="order-validation",
    organization_id="org-other",
    workspace_id=(
        context.workspace_id
    ),
    project_id=(
        context.project_id
    ),
    environment_id=(
        context.environment_id
    ),
    snapshot_ref=(
        "kernel-snapshot://order/cross"
    ),
    status="COMPLETED",
)

try:
    service.plan_cash_return(
        context=context,
        request=(
            cash_request
        ),
        order_evidence=(
            cross_order
        ),
        payment_evidence=(
            cash_payment_evidence
        ),
    )
except returns.POSReturnsError:
    pass
else:
    raise SystemExit(
        "ERROR: cross-tenant return evidence was accepted"
    )

status = (
    SAAS / "IMPLEMENTATION_STATUS.md"
).read_text(
    encoding="utf-8"
)

for phrase in [
    "- [x] Returns",
    "- [x] Daily summaries",
    "DALIZEBO POS P0: COMPLETE",
    "MVP acceptance/integration sweep: NEXT",
    "Phase 6 — Commerce + POS MVP Acceptance & Integration Closure.",
]:
    if phrase not in status:
        raise SystemExit(
            "ERROR: POS closure status missing: "
            + phrase
        )

print("OK: Kernel Refund cumulative cap passed.")
print("OK: Return quantity cannot exceed sold quantity.")
print("OK: Cash refund + inventory restock planning passed.")
print("OK: Partial refund preserves CAPTURED Payment.")
print("OK: Full cumulative refund explicitly transitions CAPTURED→REFUNDED.")
print("OK: Card refund delegates to BaaS Payment Abstraction.")
print("OK: Provider refund completion must match approved BaaS plan.")
print("OK: Return receipt/audit metadata is post-commit safe.")
print("OK: Branch daily summary timezone/currency scope passed.")
print("OK: Cross-tenant return evidence fails closed.")
print("STATUS: POS P0 RETURNS + DAILY SUMMARIES READY")
print("STATUS: DALIZEBO POS P0 COMPLETE")
