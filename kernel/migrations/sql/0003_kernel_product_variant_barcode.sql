-- Shared Kernel Product Variant barcode extension for POS/Commerce.
-- Barcode remains authoritative on the shared Product Variant model.

ALTER TABLE kernel.product_variants
    ADD COLUMN IF NOT EXISTS barcode text;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_product_variants_barcode'
    ) THEN
        ALTER TABLE kernel.product_variants
            ADD CONSTRAINT chk_product_variants_barcode
            CHECK (
                barcode IS NULL
                OR barcode ~ '^[A-Za-z0-9][A-Za-z0-9._/-]{2,127}$'
            );
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_variants_org_barcode
    ON kernel.product_variants (organization_id, barcode)
    WHERE barcode IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_product_variants_org_sku
    ON kernel.product_variants (organization_id, sku);
