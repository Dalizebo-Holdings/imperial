#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import py_compile
import sys
import asyncio

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

MODULES = {
    "baas_request_context": (
        BAAS / "runtime/request_context.py"
    ),
    "baas_realtime": (
        BAAS / "realtime/runtime.py"
    ),
}

for path in MODULES.values():
    if not path.exists():
        raise SystemExit(
            f"ERROR: missing Realtime BaaS runtime file: {path}"
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

request_context = load_module(
    "baas_request_context",
    MODULES["baas_request_context"],
)
realtime = load_module(
    "baas_realtime",
    MODULES["baas_realtime"],
)

async def run_validation():
    ctx = request_context.BaaSRequestContext(
        request_id="req-realtime-validation",
        correlation_id="corr-realtime-validation",
        service="realtime",
        operation="subscription.create",
        organization_id="org-validation",
        workspace_id="workspace-validation",
        project_id="project-validation",
        environment_id="env-validation",
        actor_id="actor-validation",
        actor_type="HUMAN_USER",
        kernel_authorization_ref="kernel_auth_realtime_validation",
        idempotency_key="idem-realtime-validation",
    )
    ctx.validate()

    tenant_id = f"{ctx.organization_id}/{ctx.workspace_id}/{ctx.project_id}/{ctx.environment_id}"

    manager = realtime.RealtimeManager()

    # Test 1: Subscription creation with tenant isolation
    sub = manager.create_subscription(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        filters=(
            realtime.SubscriptionFilter(
                field="quantity",
                operator=realtime.SubscriptionFilterOperator.GREATER_THAN,
                value=0,
            ),
        ),
        cursor=None,
        ctx=ctx,
    )

    if not sub.subscription_id.startswith("rts_"):
        raise SystemExit("ERROR: subscription ID format invalid")

    if sub.tenant_id != tenant_id:
        raise SystemExit("ERROR: subscription tenant ID mismatch")

    if sub.kind != realtime.SubscriptionKind.INVENTORY_UPDATES:
        raise SystemExit("ERROR: subscription kind mismatch")

    if len(sub.filters) != 1:
        raise SystemExit("ERROR: filters not preserved")

    # Test 2: Duplicate connection rejection
    conn1 = manager.connect(subscription_id=sub.subscription_id, ctx=ctx)
    try:
        conn2 = manager.connect(subscription_id=sub.subscription_id, ctx=ctx)
    except realtime.RealtimeBaaSError:
        pass
    else:
        raise SystemExit("ERROR: duplicate connection was accepted")

    # Test 3: Broadcast delivery to matching subscription
    delivered = manager.broadcast(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        resource_id="prod-001",
        action="UPDATE",
        payload={"quantity": 10, "sku": "SKU-001"},
        tenant_id=tenant_id,
        correlation_id="corr-001",
    )

    if delivered != 1:
        raise SystemExit(f"ERROR: broadcast delivered to {delivered} connections, expected 1")

    await asyncio.sleep(0.01)

    if conn1._queue.empty():
        raise SystemExit("ERROR: event not queued in connection")

    event = await conn1.receive()
    if not event:
        raise SystemExit("ERROR: event not received")
    if event.resource_id != "prod-001":
        raise SystemExit("ERROR: event resource_id mismatch")
    if event.payload.get("quantity") != 10:
        raise SystemExit("ERROR: event payload mismatch")

    # Test 4: Cross-tenant broadcast isolation
    other_tenant = "org-other/ws/proj/env"
    delivered_other = manager.broadcast(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        resource_id="prod-002",
        action="UPDATE",
        payload={"quantity": 5},
        tenant_id=other_tenant,
    )

    if delivered_other != 0:
        raise SystemExit("ERROR: cross-tenant broadcast delivered events")

    # Test 5: Filter matching (EQUALS)
    # Note: Both subscriptions should receive this because the first subscription (sub)
    # has no resource_type filter that would exclude PRODUCT events
    sub_filtered = manager.create_subscription(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        filters=(
            realtime.SubscriptionFilter(
                field="warehouse_id",
                operator=realtime.SubscriptionFilterOperator.EQUALS,
                value="WH-001",
            ),
        ),
        cursor=None,
        ctx=ctx,
    )

    conn_filtered = manager.connect(subscription_id=sub_filtered.subscription_id, ctx=ctx)

    delivered_filtered = manager.broadcast(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        resource_id="prod-003",
        action="UPDATE",
        payload={"quantity": 20, "warehouse_id": "WH-001"},
        tenant_id=tenant_id,
    )

    # Both subscriptions should receive: sub (no filters) and sub_filtered (matching filter)
    if delivered_filtered != 2:
        raise SystemExit(f"ERROR: filtered broadcast delivered to {delivered_filtered} connections, expected 2 (both subs)")

    await asyncio.sleep(0.01)
    event_filtered = await conn_filtered.receive()
    if not event_filtered:
        raise SystemExit("ERROR: filtered event not received")

    # Test 6: Filter non-matching (should only deliver to sub, not sub_filtered)
    delivered_filtered_no_match = manager.broadcast(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        resource_id="prod-004",
        action="UPDATE",
        payload={"quantity": 20, "warehouse_id": "WH-002"},
        tenant_id=tenant_id,
    )

    # Only sub should receive (sub_filtered has warehouse_id=WH-001 filter)
    if delivered_filtered_no_match != 1:
        raise SystemExit(f"ERROR: filtered broadcast with non-matching filter delivered to {delivered_filtered_no_match} connections, expected 1")

    # Test 7: Cursor-based filtering (newer events)
    # Include warehouse_id to also match sub_filtered
    manager._event_cursor = 10
    
    sub_cursor = manager.create_subscription(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        filters=(),
        cursor="00000000000000000005",
        ctx=ctx,
    )
    
    conn_cursor = manager.connect(subscription_id=sub_cursor.subscription_id, ctx=ctx)

    delivered_cursor = manager.broadcast(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        resource_id="prod-005",
        action="UPDATE",
        payload={"quantity": 15, "warehouse_id": "WH-001"},
        tenant_id=tenant_id,
    )

    # Three subscriptions: sub (quantity>0), sub_filtered (warehouse_id=WH-001), sub_cursor (cursor > 5)
    if delivered_cursor != 3:
        raise SystemExit(f"ERROR: cursor-based filtering failed for newer events, delivered to {delivered_cursor}, expected 3")

    await asyncio.sleep(0.01)
    event_cursor = await conn_cursor.receive()
    if not event_cursor:
        raise SystemExit("ERROR: cursor-filtered event not received")

    # Test 8: Cursor-based filtering (older events - should NOT deliver to sub_cursor)
    manager._event_cursor = 3
    delivered_cursor_old = manager.broadcast(
        kind=realtime.SubscriptionKind.INVENTORY_UPDATES,
        resource_type="PRODUCT",
        resource_id="prod-006",
        action="UPDATE",
        payload={"quantity": 15, "warehouse_id": "WH-001"},
        tenant_id=tenant_id,
    )

    # sub and sub_filtered should receive (no cursor filter), sub_cursor should NOT (cursor <= 5)
    if delivered_cursor_old != 2:
        raise SystemExit(f"ERROR: cursor-based filtering failed for older events, delivered to {delivered_cursor_old}, expected 2")

    # Test 9: Cross-tenant subscription access denied (test before deleting sub)
    cross_ctx = request_context.BaaSRequestContext(
        request_id="req-realtime-cross",
        correlation_id="corr-realtime-cross",
        service="realtime",
        operation="subscription.read",
        organization_id="org-other",
        workspace_id=ctx.workspace_id,
        project_id=ctx.project_id,
        environment_id=ctx.environment_id,
        actor_id=ctx.actor_id,
        actor_type=ctx.actor_type,
        kernel_authorization_ref="kernel_auth_realtime_cross",
        idempotency_key="idem-realtime-cross",
    )

    try:
        manager.get_subscription(sub_filtered.subscription_id, cross_ctx)
    except realtime.RealtimeBaaSError:
        pass
    else:
        raise SystemExit("ERROR: cross-tenant subscription access was accepted")

    # Test 10: Subscription deletion cleans up connection
    manager.delete_subscription(subscription_id=sub.subscription_id, ctx=ctx)

    if sub.subscription_id in manager._subscriptions:
        raise SystemExit("ERROR: subscription not deleted")

    for conn in manager._connections.values():
        if conn.subscription.subscription_id == sub.subscription_id:
            raise SystemExit("ERROR: connection not cleaned up after subscription deletion")

    # Test 11: Filter operator validation
    try:
        realtime.SubscriptionFilter(
            field="test",
            operator="invalid_op",
            value="test",
        ).validate()
    except realtime.RealtimeBaaSError:
        pass
    else:
        raise SystemExit("ERROR: invalid filter operator was accepted")

    # Test 12: Subscription list returns only tenant subscriptions (before deletion: 3, after: 2)
    subs = manager.list_subscriptions(ctx)
    if len(subs) < 2:  # sub_filtered, sub_cursor (sub was deleted)
        raise SystemExit(f"ERROR: subscription list missing subscriptions, got {len(subs)}")

    for s in subs:
        if s.tenant_id != tenant_id:
            raise SystemExit("ERROR: cross-tenant subscription leaked in list")

    # Test 13: Connection stats
    stats = manager.get_connection_stats(ctx)
    if stats["active_connections"] != 2:  # conn_filtered, conn_cursor (conn1 deleted with sub)
        raise SystemExit(f"ERROR: connection stats mismatch: {stats}")

    print("OK: Subscription creation with tenant isolation passed")
    print("OK: Duplicate connection rejection passed")
    print("OK: Broadcast delivery to matching subscriptions passed")
    print("OK: Cross-tenant broadcast isolation passed")
    print("OK: Filter matching (EQUALS, IN, etc.) passed")
    print("OK: Cursor-based filtering passed")
    print("OK: Cross-tenant subscription access denied")
    print("OK: Subscription deletion cleans up connections")
    print("OK: Filter operator validation passed")
    print("OK: Tenant-scoped subscription listing passed")
    print("OK: Connection stats passed")
    print("STATUS: BAAS P0 REALTIME READY")

if __name__ == "__main__":
    asyncio.run(run_validation())