from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


STORE_STATUSES = {
    "ACTIVE",
    "INACTIVE",
}

PRODUCT_STATUSES = {
    "DRAFT",
    "ACTIVE",
    "ARCHIVED",
}

PRODUCT_TRANSITIONS = {
    "DRAFT": {
        "ACTIVE",
        "ARCHIVED",
    },
    "ACTIVE": {
        "ARCHIVED",
    },
    "ARCHIVED": set(),
}


class CommerceStoreCatalogueError(
    ValueError
):
    pass


def _text(
    name: str,
    value: Any,
) -> str:
    if value is None:
        raise CommerceStoreCatalogueError(
            f"{name} must not be empty"
        )

    result = str(
        value
    ).strip()

    if not result:
        raise CommerceStoreCatalogueError(
            f"{name} must not be empty"
        )

    return result


def _time(
    value: str | None = None,
) -> str:
    if value is None:
        return datetime.now(
            timezone.utc
        ).isoformat()

    try:
        parsed = datetime.fromisoformat(
            value
        )
    except ValueError as exc:
        raise CommerceStoreCatalogueError(
            "requested_at must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise CommerceStoreCatalogueError(
            "requested_at must be timezone-aware"
        )

    return parsed.isoformat()


@dataclass(frozen=True)
class AuthorityEvidence:
    source: str
    entity_type: str
    entity_id: str
    organization_id: str
    workspace_id: str
    project_id: str
    environment_id: str

    def validate(self) -> None:
        if (
            str(
                self.source
            ).strip()
            != "kernel.commerce"
        ):
            raise CommerceStoreCatalogueError(
                "authority evidence must come from kernel.commerce"
            )

        entity_type = str(
            self.entity_type
        ).strip().upper()

        if entity_type not in {
            "STORE",
            "PRODUCT",
            "PRODUCT_VARIANT",
        }:
            raise CommerceStoreCatalogueError(
                "unsupported authority evidence entity_type"
            )

        for name, value in {
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


@dataclass(frozen=True)
class StoreSetupRequest:
    store_id: str
    name: str
    status: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        _text(
            "store_id",
            self.store_id,
        )
        _text(
            "name",
            self.name,
        )
        _text(
            "idempotency_key",
            self.idempotency_key,
        )

        if (
            str(
                self.status
            ).strip().upper()
            not in STORE_STATUSES
        ):
            raise CommerceStoreCatalogueError(
                "invalid Store status"
            )

        _time(
            self.requested_at
        )


@dataclass(frozen=True)
class ProductCreateRequest:
    product_id: str
    name: str
    description: str | None
    status: str
    idempotency_key: str
    requested_at: str

    def validate(self) -> None:
        _text(
            "product_id",
            self.product_id,
        )
        _text(
            "name",
            self.name,
        )
        _text(
            "idempotency_key",
            self.idempotency_key,
        )

        if (
            str(
                self.status
            ).strip().upper()
            not in PRODUCT_STATUSES
        ):
            raise CommerceStoreCatalogueError(
                "invalid Product status"
            )

        if self.description is not None:
            description = str(
                self.description
            )

            if len(
                description
            ) > 10000:
                raise CommerceStoreCatalogueError(
                    "description exceeds 10000 characters"
                )

        _time(
            self.requested_at
        )


@dataclass(frozen=True)
class ProductVariantCreateRequest:
    variant_id: str
    product_id: str
    sku: str
    price_minor: int
    currency: str
    active: bool
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        for name, value in {
            "variant_id": (
                self.variant_id
            ),
            "product_id": (
                self.product_id
            ),
            "sku": self.sku,
            "idempotency_key": (
                self.idempotency_key
            ),
        }.items():
            _text(
                name,
                value,
            )

        if (
            not isinstance(
                self.price_minor,
                int,
            )
            or isinstance(
                self.price_minor,
                bool,
            )
            or self.price_minor < 0
        ):
            raise CommerceStoreCatalogueError(
                "price_minor must be an integer >= 0"
            )

        if not isinstance(
            self.active,
            bool,
        ):
            raise CommerceStoreCatalogueError(
                "active must be boolean"
            )

        _time(
            self.requested_at
        )


@dataclass(frozen=True)
class VariantPriceUpdateRequest:
    variant_id: str
    product_id: str
    sku: str
    price_minor: int
    currency: str
    active: bool
    idempotency_key: str
    requested_at: str

    def validate_basic(self) -> None:
        ProductVariantCreateRequest(
            variant_id=(
                self.variant_id
            ),
            product_id=(
                self.product_id
            ),
            sku=self.sku,
            price_minor=(
                self.price_minor
            ),
            currency=(
                self.currency
            ),
            active=(
                self.active
            ),
            idempotency_key=(
                self.idempotency_key
            ),
            requested_at=(
                self.requested_at
            ),
        ).validate_basic()


class CommerceStoreCatalogueService:
    def __init__(
        self,
        *,
        foundation: Any,
        product_command_type: Any,
        kernel_tenant_scope_type: Any,
        kernel_resource_type: Any,
        kernel_variant_type: Any,
        kernel_money_type: Any,
    ) -> None:
        for name, value in {
            "foundation": (
                foundation
            ),
            "product_command_type": (
                product_command_type
            ),
            "kernel_tenant_scope_type": (
                kernel_tenant_scope_type
            ),
            "kernel_resource_type": (
                kernel_resource_type
            ),
            "kernel_variant_type": (
                kernel_variant_type
            ),
            "kernel_money_type": (
                kernel_money_type
            ),
        }.items():
            if value is None:
                raise CommerceStoreCatalogueError(
                    f"{name} is required"
                )

        self._foundation = (
            foundation
        )
        self._product_command_type = (
            product_command_type
        )
        self._kernel_tenant_scope_type = (
            kernel_tenant_scope_type
        )
        self._kernel_resource_type = (
            kernel_resource_type
        )
        self._kernel_variant_type = (
            kernel_variant_type
        )
        self._kernel_money_type = (
            kernel_money_type
        )

    @staticmethod
    def _validate_context(
        context: Any,
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
            != "COMMERCE"
        ):
            raise CommerceStoreCatalogueError(
                "Commerce Store/Catalogue requires product=COMMERCE"
            )

    @staticmethod
    def _assert_evidence(
        *,
        context: Any,
        evidence: AuthorityEvidence,
        entity_type: str,
        entity_id: str,
    ) -> None:
        evidence.validate()

        if (
            str(
                evidence.entity_type
            ).strip().upper()
            != entity_type
        ):
            raise CommerceStoreCatalogueError(
                "authority evidence entity_type mismatch"
            )

        if (
            evidence.entity_id
            != entity_id
        ):
            raise CommerceStoreCatalogueError(
                "authority evidence entity_id mismatch"
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
                raise CommerceStoreCatalogueError(
                    "authority evidence tenant scope mismatch"
                )

    def _kernel_tenant(
        self,
        context: Any,
    ) -> Any:
        tenant = (
            self._kernel_tenant_scope_type(
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
        )
        tenant.validate()
        return tenant

    def plan_store_setup(
        self,
        *,
        context: Any,
        request: StoreSetupRequest,
    ) -> dict[str, Any]:
        self._validate_context(
            context
        )
        request.validate()

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="STORE",
                entity_id=(
                    request.store_id
                ),
                context=context,
                idempotency_key=(
                    request.idempotency_key
                ),
                input_metadata={
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
                        )
                    ),
                },
            )
        )

    def plan_store_status(
        self,
        *,
        context: Any,
        store_evidence: AuthorityEvidence,
        current_status: str,
        target_status: str,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        self._validate_context(
            context
        )

        self._assert_evidence(
            context=context,
            evidence=(
                store_evidence
            ),
            entity_type="STORE",
            entity_id=(
                store_evidence.entity_id
            ),
        )

        current = str(
            current_status
        ).strip().upper()
        target = str(
            target_status
        ).strip().upper()

        if (
            current not in STORE_STATUSES
            or target not in STORE_STATUSES
            or current == target
        ):
            raise CommerceStoreCatalogueError(
                "Store status change must move between ACTIVE and INACTIVE"
            )

        return self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="STORE",
                entity_id=(
                    store_evidence.entity_id
                ),
                context=context,
                idempotency_key=(
                    _text(
                        "idempotency_key",
                        idempotency_key,
                    )
                ),
                input_metadata={
                    "from_status": (
                        current
                    ),
                    "to_status": (
                        target
                    ),
                    "requested_at": (
                        _time(
                            requested_at
                        )
                    ),
                },
            )
        )

    def plan_product_create(
        self,
        *,
        context: Any,
        request: ProductCreateRequest,
    ) -> dict[str, Any]:
        self._validate_context(
            context
        )
        request.validate()

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type="PRODUCT",
                entity_id=(
                    request.product_id
                ),
                context=context,
                idempotency_key=(
                    request.idempotency_key
                ),
                input_metadata={
                    "name": (
                        request.name
                    ),
                    "description": (
                        request.description
                    ),
                    "status": (
                        str(
                            request.status
                        ).strip().upper()
                    ),
                    "requested_at": (
                        _time(
                            request.requested_at
                        )
                    ),
                },
            )
        )

    def plan_product_status(
        self,
        *,
        context: Any,
        product_evidence: AuthorityEvidence,
        current_status: str,
        target_status: str,
        idempotency_key: str,
        requested_at: str,
    ) -> dict[str, Any]:
        self._validate_context(
            context
        )

        self._assert_evidence(
            context=context,
            evidence=(
                product_evidence
            ),
            entity_type="PRODUCT",
            entity_id=(
                product_evidence.entity_id
            ),
        )

        current = str(
            current_status
        ).strip().upper()
        target = str(
            target_status
        ).strip().upper()

        if (
            current not in PRODUCT_STATUSES
            or target not in PRODUCT_STATUSES
        ):
            raise CommerceStoreCatalogueError(
                "invalid Product lifecycle status"
            )

        if (
            target
            not in PRODUCT_TRANSITIONS[
                current
            ]
        ):
            raise CommerceStoreCatalogueError(
                f"illegal Product transition: {current} -> {target}"
            )

        return self._foundation.plan(
            self._product_command_type(
                action="TRANSITION",
                entity_type="PRODUCT",
                entity_id=(
                    product_evidence.entity_id
                ),
                context=context,
                idempotency_key=(
                    _text(
                        "idempotency_key",
                        idempotency_key,
                    )
                ),
                input_metadata={
                    "from_status": (
                        current
                    ),
                    "to_status": (
                        target
                    ),
                    "requested_at": (
                        _time(
                            requested_at
                        )
                    ),
                },
            )
        )

    def _validate_kernel_variant(
        self,
        *,
        context: Any,
        variant_id: str,
        product_id: str,
        sku: str,
        price_minor: int,
        currency: str,
        active: bool,
        timestamp: str,
    ) -> None:
        tenant = self._kernel_tenant(
            context
        )

        resource = (
            self._kernel_resource_type(
                id=variant_id,
                entity_type=(
                    "PRODUCT_VARIANT"
                ),
                tenant=tenant,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

        money = (
            self._kernel_money_type(
                amount_minor=(
                    price_minor
                ),
                currency=(
                    str(
                        currency
                    ).strip().upper()
                ),
            )
        )

        variant = (
            self._kernel_variant_type(
                resource=resource,
                product_id=(
                    product_id
                ),
                sku=sku,
                price=money,
                active=active,
            )
        )

        try:
            variant.validate()
        except Exception as exc:
            raise CommerceStoreCatalogueError(
                "Kernel ProductVariant validation failed"
            ) from exc

    def plan_variant_create(
        self,
        *,
        context: Any,
        product_evidence: AuthorityEvidence,
        request: ProductVariantCreateRequest,
    ) -> dict[str, Any]:
        self._validate_context(
            context
        )
        request.validate_basic()

        self._assert_evidence(
            context=context,
            evidence=(
                product_evidence
            ),
            entity_type="PRODUCT",
            entity_id=(
                request.product_id
            ),
        )

        timestamp = _time(
            request.requested_at
        )

        self._validate_kernel_variant(
            context=context,
            variant_id=(
                request.variant_id
            ),
            product_id=(
                request.product_id
            ),
            sku=request.sku,
            price_minor=(
                request.price_minor
            ),
            currency=(
                request.currency
            ),
            active=(
                request.active
            ),
            timestamp=timestamp,
        )

        return self._foundation.plan(
            self._product_command_type(
                action="CREATE",
                entity_type=(
                    "PRODUCT_VARIANT"
                ),
                entity_id=(
                    request.variant_id
                ),
                context=context,
                idempotency_key=(
                    request.idempotency_key
                ),
                input_metadata={
                    "product_id": (
                        request.product_id
                    ),
                    "sku": (
                        request.sku
                    ),
                    "price_minor": (
                        request.price_minor
                    ),
                    "currency": (
                        str(
                            request.currency
                        ).strip().upper()
                    ),
                    "active": (
                        request.active
                    ),
                    "requested_at": (
                        timestamp
                    ),
                },
            )
        )

    def plan_variant_price_update(
        self,
        *,
        context: Any,
        variant_evidence: AuthorityEvidence,
        product_evidence: AuthorityEvidence,
        request: VariantPriceUpdateRequest,
    ) -> dict[str, Any]:
        self._validate_context(
            context
        )
        request.validate_basic()

        self._assert_evidence(
            context=context,
            evidence=(
                variant_evidence
            ),
            entity_type=(
                "PRODUCT_VARIANT"
            ),
            entity_id=(
                request.variant_id
            ),
        )

        self._assert_evidence(
            context=context,
            evidence=(
                product_evidence
            ),
            entity_type="PRODUCT",
            entity_id=(
                request.product_id
            ),
        )

        timestamp = _time(
            request.requested_at
        )

        self._validate_kernel_variant(
            context=context,
            variant_id=(
                request.variant_id
            ),
            product_id=(
                request.product_id
            ),
            sku=request.sku,
            price_minor=(
                request.price_minor
            ),
            currency=(
                request.currency
            ),
            active=(
                request.active
            ),
            timestamp=timestamp,
        )

        return self._foundation.plan(
            self._product_command_type(
                action="UPDATE",
                entity_type=(
                    "PRODUCT_VARIANT"
                ),
                entity_id=(
                    request.variant_id
                ),
                context=context,
                idempotency_key=(
                    request.idempotency_key
                ),
                input_metadata={
                    "product_id": (
                        request.product_id
                    ),
                    "sku": (
                        request.sku
                    ),
                    "price_minor": (
                        request.price_minor
                    ),
                    "currency": (
                        str(
                            request.currency
                        ).strip().upper()
                    ),
                    "active": (
                        request.active
                    ),
                    "requested_at": (
                        timestamp
                    ),
                },
            )
        )
