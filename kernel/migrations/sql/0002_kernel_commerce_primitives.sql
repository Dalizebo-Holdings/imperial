-- Dalizebo Kernel P0 shared commerce primitives.
-- Authoritative models shared by Commerce and POS.

CREATE TABLE IF NOT EXISTS kernel.stores (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    name text NOT NULL,
    status text NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stores_tenant
    ON kernel.stores (
        organization_id,
        workspace_id,
        project_id,
        environment_id
    );

CREATE TABLE IF NOT EXISTS kernel.branches (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    store_id text NOT NULL
        REFERENCES kernel.stores(id) ON DELETE RESTRICT,
    name text NOT NULL,
    status text NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_branches_store
    ON kernel.branches (organization_id, store_id);

CREATE TABLE IF NOT EXISTS kernel.products (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    name text NOT NULL,
    description text,
    status text NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_tenant
    ON kernel.products (organization_id, status);

CREATE TABLE IF NOT EXISTS kernel.product_variants (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    product_id text NOT NULL
        REFERENCES kernel.products(id) ON DELETE RESTRICT,
    sku text NOT NULL,
    price_minor bigint NOT NULL CHECK (price_minor >= 0),
    currency char(3) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, sku)
);

CREATE INDEX IF NOT EXISTS idx_variants_product
    ON kernel.product_variants (organization_id, product_id);

CREATE TABLE IF NOT EXISTS kernel.inventory_items (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    product_variant_id text NOT NULL
        REFERENCES kernel.product_variants(id) ON DELETE RESTRICT,
    store_id text NOT NULL
        REFERENCES kernel.stores(id) ON DELETE RESTRICT,
    branch_id text
        REFERENCES kernel.branches(id) ON DELETE RESTRICT,
    quantity_on_hand bigint NOT NULL DEFAULT 0
        CHECK (quantity_on_hand >= 0),
    quantity_reserved bigint NOT NULL DEFAULT 0
        CHECK (
            quantity_reserved >= 0
            AND quantity_reserved <= quantity_on_hand
        ),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (
        organization_id,
        product_variant_id,
        store_id,
        branch_id
    )
);

CREATE INDEX IF NOT EXISTS idx_inventory_variant
    ON kernel.inventory_items (
        organization_id,
        product_variant_id
    );

CREATE TABLE IF NOT EXISTS kernel.customers (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    external_identity_ref text,
    display_name text,
    email text,
    phone text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_customers_tenant
    ON kernel.customers (organization_id);

CREATE TABLE IF NOT EXISTS kernel.carts (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    store_id text NOT NULL
        REFERENCES kernel.stores(id) ON DELETE RESTRICT,
    customer_id text
        REFERENCES kernel.customers(id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'CONVERTED', 'ABANDONED')),
    currency char(3) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS kernel.orders (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    store_id text NOT NULL
        REFERENCES kernel.stores(id) ON DELETE RESTRICT,
    branch_id text
        REFERENCES kernel.branches(id) ON DELETE RESTRICT,
    customer_id text
        REFERENCES kernel.customers(id) ON DELETE SET NULL,
    cart_id text
        REFERENCES kernel.carts(id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'DRAFT'
        CHECK (
            status IN (
                'DRAFT',
                'PLACED',
                'CONFIRMED',
                'COMPLETED',
                'CANCELLED'
            )
        ),
    currency char(3) NOT NULL,
    subtotal_minor bigint NOT NULL CHECK (subtotal_minor >= 0),
    discount_minor bigint NOT NULL DEFAULT 0
        CHECK (discount_minor >= 0),
    tax_minor bigint NOT NULL DEFAULT 0 CHECK (tax_minor >= 0),
    total_minor bigint NOT NULL CHECK (total_minor >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_tenant_status
    ON kernel.orders (organization_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS kernel.order_items (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    order_id text NOT NULL
        REFERENCES kernel.orders(id) ON DELETE CASCADE,
    product_id text NOT NULL
        REFERENCES kernel.products(id) ON DELETE RESTRICT,
    product_variant_id text NOT NULL
        REFERENCES kernel.product_variants(id) ON DELETE RESTRICT,
    quantity bigint NOT NULL CHECK (quantity > 0),
    unit_price_minor bigint NOT NULL CHECK (unit_price_minor >= 0),
    total_minor bigint NOT NULL CHECK (total_minor >= 0),
    currency char(3) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON kernel.order_items (organization_id, order_id);

CREATE TABLE IF NOT EXISTS kernel.payments (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    order_id text NOT NULL
        REFERENCES kernel.orders(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'AUTHORIZED',
                'CAPTURED',
                'FAILED',
                'CANCELLED',
                'REFUNDED'
            )
        ),
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    provider_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payments_order
    ON kernel.payments (organization_id, order_id);

CREATE TABLE IF NOT EXISTS kernel.refunds (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    payment_id text NOT NULL
        REFERENCES kernel.payments(id) ON DELETE RESTRICT,
    amount_minor bigint NOT NULL CHECK (amount_minor > 0),
    currency char(3) NOT NULL,
    reason text NOT NULL,
    status text NOT NULL DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'SUCCEEDED',
                'FAILED',
                'CANCELLED'
            )
        ),
    provider_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_refunds_payment
    ON kernel.refunds (organization_id, payment_id);

CREATE TABLE IF NOT EXISTS kernel.discounts (
    id text PRIMARY KEY,
    organization_id text NOT NULL
        REFERENCES kernel.organizations(id) ON DELETE RESTRICT,
    workspace_id text NOT NULL,
    project_id text NOT NULL,
    environment_id text NOT NULL,
    discount_type text NOT NULL
        CHECK (discount_type IN ('FIXED', 'PERCENTAGE')),
    value_minor bigint,
    basis_points integer,
    currency char(3),
    active boolean NOT NULL DEFAULT true,
    starts_at timestamptz,
    ends_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        (
            discount_type = 'FIXED'
            AND value_minor IS NOT NULL
            AND value_minor > 0
            AND basis_points IS NULL
            AND currency IS NOT NULL
        )
        OR
        (
            discount_type = 'PERCENTAGE'
            AND basis_points BETWEEN 1 AND 10000
            AND value_minor IS NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_discounts_tenant
    ON kernel.discounts (organization_id, active);
