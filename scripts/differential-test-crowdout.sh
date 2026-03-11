#!/usr/bin/env bash
set -euo pipefail

SCRIPT="FeeConcentrationIndexBuilderScript"
BLOCK_WAIT=30

echo "=== Differential Crowdout Test ==="

echo "--- Phase 1 ---"
forge script "$SCRIPT" --sig "buildCrowdoutPhase1()" --broadcast --rpc-url unichain_sepolia
forge script "$SCRIPT" --sig "buildCrowdoutPhase1()" --broadcast --rpc-url sepolia
echo "Waiting ${BLOCK_WAIT}s for next block..."
sleep "$BLOCK_WAIT"

echo "--- Phase 2 ---"
forge script "$SCRIPT" --sig "buildCrowdoutPhase2()" --broadcast --rpc-url unichain_sepolia
forge script "$SCRIPT" --sig "buildCrowdoutPhase2()" --broadcast --rpc-url sepolia
echo "Waiting ${BLOCK_WAIT}s for next block..."
sleep "$BLOCK_WAIT"

echo "--- Phase 3 ---"
TOKEN_A="${TOKEN_A:?Set TOKEN_A from phase 1 output}" \
    forge script "$SCRIPT" --sig "buildCrowdoutPhase3()" --broadcast --rpc-url unichain_sepolia
TOKEN_A="$TOKEN_A" \
    forge script "$SCRIPT" --sig "buildCrowdoutPhase3()" --broadcast --rpc-url sepolia

echo "Waiting ${BLOCK_WAIT}s for reactive callback..."
sleep "$BLOCK_WAIT"

echo "--- Comparing deltaPlus ---"
forge script CompareDeltaPlusScript --sig "run()" --rpc-url sepolia

echo "=== Done ==="
