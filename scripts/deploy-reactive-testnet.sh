#!/usr/bin/env bash
set -euo pipefail

# Prerequisites
command -v jq >/dev/null || { echo "ERROR: jq is required"; exit 1; }
command -v forge >/dev/null || { echo "ERROR: forge is required"; exit 1; }
command -v cast >/dev/null || { echo "ERROR: cast is required"; exit 1; }

# Load env
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/.env"

# Validate required variables
for var in REACTIVE_RPC_URL SEPOLIA_RPC_URL DEPLOYER_PRIVATE_KEY SEPOLIA_CALLBACK_PROXY V3_POOL V3_ORIGIN_CHAIN_ID; do
    [[ -z "${!var:-}" ]] && echo "ERROR: $var is not set in .env" && exit 1
done
[[ "$DEPLOYER_PRIVATE_KEY" == "0x..." ]] && echo "ERROR: DEPLOYER_PRIVATE_KEY is still the placeholder" && exit 1

echo "=== Step 1: Deploy ReactiveHookAdapter on Sepolia ==="
ADAPTER=$(forge create \
    src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol:ReactiveHookAdapter \
    --constructor-args "$SEPOLIA_CALLBACK_PROXY" \
    --rpc-url "$SEPOLIA_RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY" \
    --json | jq -r '.deployedTo')

echo "Adapter deployed: $ADAPTER"

echo "=== Step 2: Deploy ThetaSwapReactive on Reactive Lasna ==="
REACTIVE=$(forge create \
    src/reactive-integration/ThetaSwapReactive.sol:ThetaSwapReactive \
    --constructor-args "$ADAPTER" "0x0000000000000000000000000000000000fffFfF" \
    --rpc-url "$REACTIVE_RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY" \
    --value 0.1ether \
    --json | jq -r '.deployedTo')

echo "ThetaSwapReactive deployed: $REACTIVE"

echo "=== Step 3: Register V3 pool ==="
cast send "$REACTIVE" \
    "registerPool(uint256,address)" \
    "$V3_ORIGIN_CHAIN_ID" "$V3_POOL" \
    --rpc-url "$REACTIVE_RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY"

echo "=== Done ==="
echo "ADAPTER_ADDRESS=$ADAPTER"
echo "REACTIVE_ADDRESS=$REACTIVE"
echo ""
echo "Add to scripts/.env:"
echo "  ADAPTER_ADDRESS=$ADAPTER"
echo "  REACTIVE_ADDRESS=$REACTIVE"
