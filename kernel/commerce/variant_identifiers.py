from __future__ import annotations

import re


BARCODE_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._/-]{2,127}"
)


class VariantIdentifierError(ValueError):
    pass


def validate_barcode(value: str) -> str:
    barcode = str(value).strip()

    if not BARCODE_PATTERN.fullmatch(barcode):
        raise VariantIdentifierError(
            "barcode must be 3..128 safe identifier characters"
        )

    return barcode
