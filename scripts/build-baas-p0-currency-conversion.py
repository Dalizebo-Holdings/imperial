#!/usr/bin/env python3
from pathlib import Path
import sys
import py_compile

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"
KERNEL_OUTBOX = ROOT / "kernel" / "outbox"

REQUIRED = [
    BAAS / "currency_conversion/CONVERSION_CONTRACT.md",
    BAAS / "currency_conversion/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in REQUIRED:
    if not path.exists():
        print(f"ERROR: missing Currency Conversion artifact: {path}")
        sys.exit(1)

for py_file in [
    BAAS / "currency_conversion/runtime.py",
    BAAS / "runtime/request_context.py",
]:
    try:
        py_compile.compile(str(py_file), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"ERROR: compilation failed for {py_file}: {e}")
        sys.exit(1)

print("OK: Currency Conversion runtime compiled.")
print("OK: Currency Conversion contract present.")
print("NEXT: python scripts/validate-baas-p0-currency-conversion.py")
