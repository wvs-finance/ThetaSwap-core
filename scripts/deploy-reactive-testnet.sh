#!/usr/bin/env bash
set -euo pipefail

# Load env
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/.env"

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
