#!/usr/bin/env bash
# Differential test orchestrator: deploys infra, sets up reactive,
# runs V4+V3 scenarios, waits for relay, verifies deltaPlus convergence.
#
# Flow:
#   Phase 1: Deploy FCI hook + adapter on Sepolia
#   Phase 2: Deploy ThetaSwapReactive on Lasna
#   Phase 3: Fund adapter + run V4 scenario + create V3 pools
#   Phase 4: Register V3 pool on reactive
#   Phase 5: Execute V3 operations (events captured by relay)
#   Phase 6: Wait for relay + verify convergence
#
# Prerequisites:
#   - .env with MNEMONIC, ALCHEMY_API_KEY, REACTIVE_RPC_URL
#   - Deployer funded on Sepolia + Lasna
#
# Usage:
#   ./script/reactive-integration/run-differential.sh [mild|crowdout]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

source .env 2>/dev/null || true

DIFF_TEST="test/reactive-integration/uniswapV3/differential/FeeConcentrationIndexV4ReactiveV3.diff.t.sol"
CONTRACT="FeeConcentrationIndexV4ReactiveV3DiffTest"
STATE_FILE="broadcast/diff-test-state.json"
REACTIVE_DEPLOY_FILE="broadcast/reactive-deploy.json"
REACTIVE_RPC="${REACTIVE_RPC_URL:?REACTIVE_RPC_URL not set}"
LASNA_SYSTEM="0x0000000000000000000000000000000000fffFfF"

DEPLOYER_PK=$(cast wallet derive-private-key "$MNEMONIC" 0 2>/dev/null)

SCENARIO="${1:?Usage: $0 [mild|crowdout]}"

# ── Phase 1: Deploy FCI hook + adapter on Sepolia ──
echo "=== Phase 1: Deploying FCI hook + adapter on Sepolia ==="
forge script "${DIFF_TEST}:${CONTRACT}" \
    --sig "deploy()" \
    --broadcast --slow \
    --rpc-url sepolia \
    -vv

echo ""
cat "$STATE_FILE"
echo ""

ADAPTER=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['adapter'])")
echo "Adapter: $ADAPTER"

# ── Phase 2: Deploy ThetaSwapReactive on Lasna ──
echo ""
echo "=== Phase 2: Deploying ThetaSwapReactive on Lasna ==="

BYTECODE=$(forge inspect ThetaSwapReactive bytecode)
CONSTRUCTOR_ARGS=$(cast abi-encode "constructor(address,address)" "$ADAPTER" "$LASNA_SYSTEM")

DEPLOY_RESULT=$(cast send \
    --rpc-url "$REACTIVE_RPC" \
    --private-key "$DEPLOYER_PK" \
    --value 0.1ether \
    --json \
    --gas-limit 5000000 \
    --create "${BYTECODE}${CONSTRUCTOR_ARGS#0x}")

REACTIVE_ADDR=$(echo "$DEPLOY_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['contractAddress'])")
REACTIVE_STATUS=$(echo "$DEPLOY_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

echo "ThetaSwapReactive: $REACTIVE_ADDR (status: $REACTIVE_STATUS)"

if [ "$REACTIVE_STATUS" != "0x1" ]; then
    echo "ERROR: Reactive deploy failed"
    exit 1
fi

echo "{\"address\":\"$REACTIVE_ADDR\"}" > "$REACTIVE_DEPLOY_FILE"

# ── Phase 3: Fund adapter + run V4 scenario + create V3 pools ──
echo ""
echo "=== Phase 3a: Funding adapter with 0.05 ETH ==="
cast send "$ADAPTER" \
    --rpc-url sepolia \
    --private-key "$DEPLOYER_PK" \
    --value 0.05ether 2>&1 | grep -E "status"

echo ""
echo "=== Phase 3b: Running ${SCENARIO} — V4 scenario + V3 pool creation ==="
forge script "${DIFF_TEST}:${CONTRACT}" \
    --sig "run_${SCENARIO}()" \
    --broadcast --slow \
    --rpc-url sepolia \
    -vv

echo ""
cat "$STATE_FILE"
echo ""

V3_POOL=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['v3_pool'])")
echo "V3 Pool: $V3_POOL"

# ── Phase 4: Register V3 pool on reactive ──
echo ""
echo "=== Phase 4: Registering V3 pool on reactive ==="
cast send "$REACTIVE_ADDR" \
    "registerPool(uint256,address)" \
    11155111 "$V3_POOL" \
    --rpc-url "$REACTIVE_RPC" \
    --private-key "$DEPLOYER_PK" 2>&1 | grep -E "status"

echo "V3 pool registered. Waiting 10s for subscription to activate..."
sleep 10

# ── Phase 5: Execute V3 operations (events now captured) ──
echo ""
echo "=== Phase 5: Executing V3 ${SCENARIO} operations ==="
forge script "${DIFF_TEST}:${CONTRACT}" \
    --sig "execute_${SCENARIO}_v3()" \
    --broadcast --slow \
    --rpc-url sepolia \
    -vv

# ── Phase 6: Wait for relay + verify ──
echo ""
echo "=== Phase 6a: Waiting 90s for reactive relay ==="
sleep 90

echo ""
echo "=== Phase 6b: Verifying deltaPlus convergence ==="
forge script "${DIFF_TEST}:${CONTRACT}" \
    --sig "verify()" \
    --rpc-url sepolia \
    -vv

echo ""
echo "=== DONE ==="
