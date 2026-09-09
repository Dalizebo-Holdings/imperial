from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


BRANCH_STATUSES = {
    "ACTIVE",
    "INACTIVE",
}

STAFF_STATUSES = {
    "ACTIVE",
    "INACTIVE",
}

POS_P0_PERMISSIONS = {
    "pos.branch.read": "Read assigned POS branch context.",
    "pos.product.read": "Search and read branch-scoped products.",
    "pos.cart.create": "Create POS carts.",
    "pos.cart.update": "Update POS carts.",
    "pos.checkout.execute": "Execute POS checkout.",
    "pos.payment.cash.record": "Record validated POS cash payment.",
    "pos.payment.card.record": "Initiate/record POS card payment.",
    "pos.receipt.issue": "Issue POS receipt metadata.",
    "pos.inventory.adjust": "Apply authorized POS inventory adjustment.",
    "pos.return.execute": "Execute POS return workflow.",
    "pos.summary.read": "Read branch-scoped daily summaries.",
}

SEARCH_MODES = {
    "TEXT",
    "SKU",
    "BARCODE",
}


class POSFoundationError(ValueError):
    pass


def _text(name: str, value: Any) -> str:
    if value is None:
        raise POSFoundationError(
            f"{name} must not be empty"
        )

    result = str(value).strip()

    if not result:
        raise POSFoundationError(
            f"{name} must not be empty"
        )

    return result


def _time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(
            timezone.utc
        )

    try:
        parsed = datetime.fromisoformat(
            value
        )
    except ValueError as exc:
        raise POSFoundationError(
            "timestamp must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise POSFoundationError(
            "timestamp must be timezone-aware"
        )

    return parsed


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise POSFoundationError(
            "value must be JSON-compatible"
        ) from exc


def _validate_pos_context(
    context: Any,
    *,
    branch_required: bool,
) -> None:
    if hasattr(
        context,
        "validate",
    ):
        context.validate()

    if (
        str(
            getattr(
                context,
                "product",
                "",
            )
        ).strip().upper()
        != "POS"
    ):
        raise POSFoundationError(
            "POS service requires product=POS"
        )

    if getattr(
        context,
        "store_id",
        None,
    ) is None:
        raise POSFoundationError(
            "POS service requires store context"
        )

    if (
        branch_required
        and getattr(
            context,
            "branch_id",
            None,
        ) is None
    ):
        raise POSFoundationError(
            "POS operational service requires branch context"
        )


@dataclass(frozen=True)
class CommerceEvidence:
    source: str
    entity_type: str
    entity_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    status: str | None = None

    def validate(self) -> None:
        if (
            str(
                self.source
            ).strip()
            != "kernel.commerce"
        ):
            raise POSFoundationError(
                "commerce evidence must come from kernel.commerce"
            )

        for name, value in {
            "entity_type": (
                self.entity_type
            ),
            "entity_id": (
                self.entity_id
            ),
            "organization_id": (
                self.organization_id
            ),
            "workspace_id": (
                self.workspace_id
            ),
            "project_id": (
                self.project_id
            ),
            "environment_id": (
                self.environment_id
            ),
        }.items():
            _text(
                name,
                value,
            )


def _assert_commerce_evidence(
    *,
    context: Any,
    evidence: CommerceEvidence,
    entity_type: str,
    entity_id: str,
    require_active: bool = False,
) -> None:
    evidence.validate()

    if (
        str(
            evidence.entity_type
        ).strip().upper()
        != entity_type
    ):
        raise POSFoundationError(
            "commerce evidence entity_type mismatch"
        )

    if (
        evidence.entity_id
        != entity_id
    ):
        raise POSFoundationError(
            "commerce evidence entity_id mismatch"
        )

    for name in [
        "organization_id",
        "workspace_id",
        "project_id",
        "environment_id",
    ]:
        if (
            getattr(
                evidence,
                name,
            )
            != getattr(
                context,
                name,
            )
        ):
            raise POSFoundationError(
                "commerce evidence tenant scope mismatch"
            )

    if (
        require_active
        and str(
            evidence.status or ""
        ).strip().upper()
        != "ACTIVE"
    ):
        raise POSFoundationError(
            f"{entity_type} must be ACTIVE"
        )


@dataclass(frozen=True)
class BranchSetupRequest:
    branch_id: str
    store_id: str
    name: str
    status: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        for name, value in {
            "branch_id": (
                self.branch_id
            ),
            "store_id": (
                self.store_id
            ),
            "name": self.name,
            "idempotency_key": (
                self.idempotency_key
            ),
        }.items():
            _text(
                name,
                value,
            )

        status = str(
            self.status
        ).strip().upper()

        if status not in BRANCH_STATUSES:
            raise POSFoundationError(
                "invalid Branch status"
            )

        _time(
            self.requested_at
        )


@dataclass(frozen=True)
class RoleRegistrationRequest:
    role_id: str
    permissions: frozenset[str]

    def validate(self) -> None:
        _text(
            "role_id",
            self.role_id,
        )

        if not self.permissions:
            raise POSFoundationError(
                "POS role permissions must not be empty"
            )

        unsupported = (
            set(
                self.permissions
            )
            - set(
                POS_P0_PERMISSIONS
            )
        )

        if unsupported:
            raise POSFoundationError(
                "POS role requested unsupported permissions: "
                + ", ".join(
                    sorted(
                        unsupported
                    )
                )
            )


@dataclass(frozen=True)
class RoleRegistrationResult:
    role_id: str
    permissions: tuple[str, ...]
    created: bool
    authority: str = "kernel.authorization"


@dataclass(frozen=True)
class StaffAssignment:
    assignment_id: str
    actor_id: str
    identity_ref: str
    role_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str
    store_id: str
    branch_id: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ProductSearchQuery:
    mode: str
    value: str
    available_only: bool = True
    limit: int = 25

    def validate(
        self,
        *,
        barcode_validator: Any,
    ) -> str:
        mode = str(
            self.mode
        ).strip().upper()

        if mode not in SEARCH_MODES:
            raise POSFoundationError(
                "unsupported POS product search mode"
            )

        value = _text(
            "search value",
            self.value,
        )

        if mode == "TEXT":
            if not 2 <= len(
                value
            ) <= 128:
                raise POSFoundationError(
                    "TEXT search value must be 2..128 characters"
                )

        elif mode == "SKU":
            if len(
                value
            ) > 128:
                raise POSFoundationError(
                    "SKU exceeds 128 characters"
                )

        else:
            try:
                value = barcode_validator(
                    value
                )
            except Exception as exc:
                raise POSFoundationError(
                    "invalid canonical barcode"
                ) from exc

        if (
            not isinstance(
                self.available_only,
                bool,
            )
        ):
            raise POSFoundationError(
                "available_only must be boolean"
            )

        if (
            not isinstance(
                self.limit,
                int,
            )
            or isinstance(
                self.limit,
                bool,
            )
            or not 1 <= self.limit <= 100
        ):
            raise POSFoundationError(
                "search limit must be 1..100"
            )

        return value


@dataclass(frozen=True)
class ProductSearchReadPlan:
    query_id: str
    mode: str
    value: str
    tenant_context: dict[str, str]
    store_id: str
    branch_id: str
    sources: tuple[str, ...]
    filters: dict[str, Any]
    limit: int
    correlation_id: str
    state: str = (
        "READY_FOR_POS_PRODUCT_SEARCH_ADAPTER"
    )


class POSFoundationService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        auth_registry: Any,
        permission_registry: Any,
        role_registry: Any,
        permission_definition_type: Any,
        role_definition_type: Any,
        barcode_validator: Any,
    ) -> None:
        self._foundation = (
            foundation
        )
        self._product_command_type = (
            product_command_type
        )
        self._auth_registry = (
            auth_registry
        )
        self._permission_registry = (
            permission_registry
        )
        self._role_registry = (
            role_registry
        )
        self._permission_definition_type = (
            permission_definition_type
        )
        self._role_definition_type = (
            role_definition_type
        )
        self._barcode_validator = (
            barcode_validator
        )

        self._staff_assignments: dict[
            str,
            StaffAssignment,
        ] = {}

        self._staff_scope_index: dict[
            tuple[str, str, str],
            str,
        ] = {}

    def plan_branch_create(
        self,
        *,
        context: Any,
        request: BranchSetupRequest,
        store_evidence: CommerceEvidence,
    ) -> dict[str, Any]:
        _validate_pos_context(
            context,
            branch_required=False,
        )
        request.validate()

        if (
            context.store_id
            != request.store_id
        ):
            raise POSFoundationError(
                "Branch store_id must match POS context"
            )

        _assert_commerce_evidence(
            context=context,
            evidence=store_evidence,
            entity_type="STORE",
            entity_id=request.store_id,
            require_active=True,
        )

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="BRANCH",
                entity_id=(
                    request.branch_id
                ),
                context=context,
                idempotency_key=(
                    request.idempotency_key
                ),
                input_metadata={
                    "store_id": (
                        request.store_id
                    ),
                    "name": (
                        request.name
                    ),
                    "status": (
                        str(
                            request.status
                        ).strip().upper()
                    ),
                    "requested_at": (
                        _time(
                            request.requested_at
                        ).isoformat()
                    ),
                },
            )
        )

    def plan_branch_status(
        self,
        *,
        context: Any,
        branch_evidence: CommerceEvidence,
        current_status: str,
        target_status: str,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        _validate_pos_context(
            context,
            branch_required=True,
        )

        _assert_commerce_evidence(
            context=context,
            evidence=branch_evidence,
            entity_type="BRANCH",
            entity_id=context.branch_id,
        )

        current = str(
            current_status
        ).strip().upper()
        target = str(
            target_status
        ).strip().upper()

        if (
            current not in BRANCH_STATUSES
            or target not in BRANCH_STATUSES
            or current == target
        ):
            raise POSFoundationError(
                "Branch status must transition ACTIVE↔INACTIVE"
            )

        return self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="BRANCH",
                entity_id=(
                    context.branch_id
                ),
                context=context,
                idempotency_key=(
                    _text(
                        "idempotency_key",
                        idempotency_key,
                    )
                ),
                input_metadata={
                    "from_status": current,
                    "to_status": target,
                    "requested_at": (
                        _time(
                            requested_at
                        ).isoformat()
                    ),
                },
            )
        )

    def register_role(
        self,
        *,
        context: Any,
        request: RoleRegistrationRequest,
    ) -> RoleRegistrationResult:
        _validate_pos_context(
            context,
            branch_required=True,
        )
        request.validate()

        for permission_id in sorted(
            request.permissions
        ):
            try:
                existing_permission = (
                    self._permission_registry.require(
                        permission_id
                    )
                )
                if (
                    existing_permission.permission_id
                    != permission_id
                ):
                    raise POSFoundationError(
                        "Kernel permission registry mismatch"
                    )
            except Exception:
                definition = (
                    self._permission_definition_type(
                        permission_id=(
                            permission_id
                        ),
                        description=(
                            POS_P0_PERMISSIONS[
                                permission_id
                            ]
                        ),
                        sensitive=(
                            permission_id
                            in {
                                "pos.checkout.execute",
                                "pos.payment.cash.record",
                                "pos.payment.card.record",
                                "pos.inventory.adjust",
                                "pos.return.execute",
                            }
                        ),
                    )
                )
                try:
                    self._permission_registry.register(
                        definition
                    )
                except Exception as exc:
                    raise POSFoundationError(
                        "Kernel permission registration failed"
                    ) from exc

        role = self._role_definition_type(
            role_id=request.role_id,
            permissions=frozenset(
                request.permissions
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
        )

        try:
            role.validate()
        except Exception as exc:
            raise POSFoundationError(
                "Kernel RoleDefinition validation failed"
            ) from exc

        try:
            existing = self._role_registry.get(
                request.role_id
            )
        except Exception:
            existing = None

        if existing is not None:
            if existing != role:
                raise POSFoundationError(
                    "Kernel role_id already exists with different definition"
                )
            created = False
        else:
            try:
                self._role_registry.register(
                    role
                )
            except Exception as exc:
                raise POSFoundationError(
                    "Kernel Role registration failed"
                ) from exc
            created = True

        return RoleRegistrationResult(
            role_id=request.role_id,
            permissions=tuple(
                sorted(
                    request.permissions
                )
            ),
            created=created,
        )

    def assign_staff(
        self,
        *,
        context: Any,
        actor_id: str,
        role_id: str,
        branch_evidence: CommerceEvidence,
        assigned_at: str | None = None,
    ) -> dict[str, Any]:
        _validate_pos_context(
            context,
            branch_required=True,
        )

        _assert_commerce_evidence(
            context=context,
            evidence=branch_evidence,
            entity_type="BRANCH",
            entity_id=context.branch_id,
            require_active=True,
        )

        try:
            identity = self._auth_registry.get_identity(
                _text(
                    "actor_id",
                    actor_id,
                )
            )
            identity.validate()
        except Exception as exc:
            raise POSFoundationError(
                "POS staff requires existing BaaS identity"
            ) from exc

        if (
            identity.actor_type
            != "HUMAN_USER"
        ):
            raise POSFoundationError(
                "POS staff identity must be HUMAN_USER"
            )

        if not identity.enabled:
            raise POSFoundationError(
                "POS staff identity is disabled"
            )

        if (
            identity.organization_id
            != context.organization_id
        ):
            raise POSFoundationError(
                "POS staff identity organization mismatch"
            )

        try:
            role = self._role_registry.get(
                _text(
                    "role_id",
                    role_id,
                )
            )
            role.validate()
        except Exception as exc:
            raise POSFoundationError(
                "POS staff requires existing Kernel role"
            ) from exc

        if (
            role.organization_id
            != context.organization_id
            or role.workspace_id
            != context.workspace_id
            or role.project_id
            != context.project_id
            or role.environment_id
            != context.environment_id
        ):
            raise POSFoundationError(
                "POS staff role tenant scope mismatch"
            )

        now = _time(
            assigned_at
        ).isoformat()

        scope = (
            identity.actor_id,
            context.store_id,
            context.branch_id,
        )

        existing_assignment_id = (
            self._staff_scope_index.get(
                scope
            )
        )

        if (
            existing_assignment_id
            is not None
        ):
            existing = self._staff_assignments[
                existing_assignment_id
            ]

            if (
                existing.role_id
                == role.role_id
                and existing.status
                == "ACTIVE"
            ):
                return {
                    "created": False,
                    "assignment": existing,
                }

            raise POSFoundationError(
                "staff already has a different branch assignment; use change_staff_role"
            )

        assignment_id = (
            "pos_staff_"
            + sha256(
                _canonical(
                    {
                        "actor_id": (
                            identity.actor_id
                        ),
                        "store_id": (
                            context.store_id
                        ),
                        "branch_id": (
                            context.branch_id
                        ),
                        "role_id": (
                            role.role_id
                        ),
                    }
                ).encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        assignment = StaffAssignment(
            assignment_id=(
                assignment_id
            ),
            actor_id=(
                identity.actor_id
            ),
            identity_ref=(
                identity.identity_ref
            ),
            role_id=(
                role.role_id
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
            store_id=(
                context.store_id
            ),
            branch_id=(
                context.branch_id
            ),
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )

        self._staff_assignments[
            assignment.assignment_id
        ] = assignment
        self._staff_scope_index[
            scope
        ] = assignment.assignment_id

        return {
            "created": True,
            "assignment": assignment,
        }

    def change_staff_role(
        self,
        *,
        context: Any,
        assignment_id: str,
        target_role_id: str,
        changed_at: str | None = None,
    ) -> StaffAssignment:
        _validate_pos_context(
            context,
            branch_required=True,
        )

        assignment = self._require_assignment(
            context=context,
            assignment_id=assignment_id,
        )

        try:
            role = self._role_registry.get(
                _text(
                    "target_role_id",
                    target_role_id,
                )
            )
            role.validate()
        except Exception as exc:
            raise POSFoundationError(
                "target Kernel role not found"
            ) from exc

        if (
            role.organization_id
            != context.organization_id
            or role.workspace_id
            != context.workspace_id
            or role.project_id
            != context.project_id
            or role.environment_id
            != context.environment_id
        ):
            raise POSFoundationError(
                "target role tenant scope mismatch"
            )

        updated = replace(
            assignment,
            role_id=role.role_id,
            updated_at=(
                _time(
                    changed_at
                ).isoformat()
            ),
        )

        self._staff_assignments[
            assignment.assignment_id
        ] = updated

        return updated

    def deactivate_staff(
        self,
        *,
        context: Any,
        assignment_id: str,
        deactivated_at: str | None = None,
    ) -> StaffAssignment:
        _validate_pos_context(
            context,
            branch_required=True,
        )

        assignment = self._require_assignment(
            context=context,
            assignment_id=assignment_id,
        )

        if (
            assignment.status
            != "ACTIVE"
        ):
            raise POSFoundationError(
                "staff assignment is already inactive"
            )

        updated = replace(
            assignment,
            status="INACTIVE",
            updated_at=(
                _time(
                    deactivated_at
                ).isoformat()
            ),
        )

        self._staff_assignments[
            assignment.assignment_id
        ] = updated

        return updated

    def staff_context(
        self,
        *,
        context: Any,
        actor_id: str,
    ) -> StaffAssignment:
        _validate_pos_context(
            context,
            branch_required=True,
        )

        scope = (
            actor_id,
            context.store_id,
            context.branch_id,
        )

        assignment_id = (
            self._staff_scope_index.get(
                scope
            )
        )

        if assignment_id is None:
            raise POSFoundationError(
                "actor has no POS staff assignment for branch"
            )

        assignment = self._staff_assignments[
            assignment_id
        ]

        if assignment.status != "ACTIVE":
            raise POSFoundationError(
                "POS staff assignment is inactive"
            )

        identity = self._auth_registry.get_identity(
            assignment.actor_id
        )

        if not identity.enabled:
            raise POSFoundationError(
                "POS staff BaaS identity is disabled"
            )

        return assignment

    def plan_product_search(
        self,
        *,
        context: Any,
        branch_evidence: CommerceEvidence,
        query: ProductSearchQuery,
    ) -> ProductSearchReadPlan:
        _validate_pos_context(
            context,
            branch_required=True,
        )

        _assert_commerce_evidence(
            context=context,
            evidence=branch_evidence,
            entity_type="BRANCH",
            entity_id=context.branch_id,
            require_active=True,
        )

        value = query.validate(
            barcode_validator=(
                self._barcode_validator
            )
        )
        mode = str(
            query.mode
        ).strip().upper()

        material = {
            "organization_id": (
                context.organization_id
            ),
            "workspace_id": (
                context.workspace_id
            ),
            "project_id": (
                context.project_id
            ),
            "environment_id": (
                context.environment_id
            ),
            "store_id": (
                context.store_id
            ),
            "branch_id": (
                context.branch_id
            ),
            "mode": mode,
            "value": value,
            "available_only": (
                query.available_only
            ),
            "limit": query.limit,
        }

        filters: dict[str, Any] = {
            "organization_id": (
                context.organization_id
            ),
            "workspace_id": (
                context.workspace_id
            ),
            "project_id": (
                context.project_id
            ),
            "environment_id": (
                context.environment_id
            ),
            "store_id": (
                context.store_id
            ),
            "branch_id": (
                context.branch_id
            ),
            "product_status": "ACTIVE",
            "variant_active": True,
            "available_only": (
                query.available_only
            ),
        }

        if mode == "TEXT":
            filters[
                "product_text_query"
            ] = value
        elif mode == "SKU":
            filters[
                "sku_exact"
            ] = value
        else:
            filters[
                "barcode_exact"
            ] = value

        return ProductSearchReadPlan(
            query_id=(
                "pos_product_search_"
                + sha256(
                    _canonical(
                        material
                    ).encode(
                        "utf-8"
                    )
                ).hexdigest()[:24]
            ),
            mode=mode,
            value=value,
            tenant_context={
                "organization_id": (
                    context.organization_id
                ),
                "workspace_id": (
                    context.workspace_id
                ),
                "project_id": (
                    context.project_id
                ),
                "environment_id": (
                    context.environment_id
                ),
            },
            store_id=(
                context.store_id
            ),
            branch_id=(
                context.branch_id
            ),
            sources=(
                "kernel.products",
                "kernel.product_variants",
                "kernel.inventory_items",
            ),
            filters=filters,
            limit=query.limit,
            correlation_id=(
                context.correlation_id
            ),
        )

    def _require_assignment(
        self,
        *,
        context: Any,
        assignment_id: str,
    ) -> StaffAssignment:
        assignment = (
            self._staff_assignments.get(
                _text(
                    "assignment_id",
                    assignment_id,
                )
            )
        )

        if assignment is None:
            raise POSFoundationError(
                "POS staff assignment not found"
            )

        if (
            assignment.organization_id
            != context.organization_id
            or assignment.workspace_id
            != context.workspace_id
            or assignment.project_id
            != context.project_id
            or assignment.environment_id
            != context.environment_id
            or assignment.store_id
            != context.store_id
            or assignment.branch_id
            != context.branch_id
        ):
            raise POSFoundationError(
                "cross-scope POS staff assignment access denied"
            )

        return assignment
