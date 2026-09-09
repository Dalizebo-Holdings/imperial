#!/usr/bin/env python3
from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parent.parent
BAAS = ROOT / "baas"

REQUIRED = [
    BAAS / "currency_conversion/CONVERSION_CONTRACT.md",
    BAAS / "currency_conversion/runtime.py",
    BAAS / "runtime/request_context.py",
]

for path in REQUIRED:
    if not path.exists():
        print(f"ERROR: missing Currency Conversion artifact: {path}")
        sys.exit(1)

for py_file in [BAAS / "currency_conversion/runtime.py", BAAS / "runtime/request_context.py"]:
    try:
        py_compile.compile(str(py_file), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"ERROR: compilation failed for {py_file}: {e}")
        sys.exit(1)

print("OK: Currency Conversion runtime compiled.")
print("OK: Currency Conversion contract present.")
print("NEXT: implement Currency Conversion validator and wire into IMPLEMENTATION_STATUS.md.")
