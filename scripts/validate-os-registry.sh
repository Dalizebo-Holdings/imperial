#!/usr/bin/env bash
set -euo pipefail

REGISTRY="operating-systems/activation/registry/os-registry.csv"

if [[ ! -f "$REGISTRY" ]]; then
  echo "ERROR: OS registry missing."
  exit 1
fi

COUNT=$(tail -n +2 "$REGISTRY" | wc -l)

if [[ "$COUNT" -ne 269 ]]; then
  echo "ERROR: Expected 269 Operating Systems, found $COUNT."
  exit 1
fi

echo "OK: 269 Operating Systems registered."
