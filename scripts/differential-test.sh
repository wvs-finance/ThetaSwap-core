#!/usr/bin/env bash
set -euo pipefail

SCENARIO=${1:-"buildEquilibrium"}
SCRIPT="FeeConcentrationIndexBuilderScript"

echo "=== Differential Test: $SCENARIO ==="

echo "--- V4: Unichain Sepolia (local FCI hook) ---"
forge script "$SCRIPT" --sig "${SCENARIO}()" \
    --broadcast --rpc-url unichain_sepolia

echo "--- V3: Eth Sepolia (reactive adapter) ---"
forge script "$SCRIPT" --sig "${SCENARIO}()" \
    --broadcast --rpc-url sepolia

echo "--- Waiting for reactive callback (30s) ---"
sleep 30

echo "--- Comparing deltaPlus ---"
forge script CompareDeltaPlusScript --sig "run()" --rpc-url sepolia

echo "=== Done ==="
