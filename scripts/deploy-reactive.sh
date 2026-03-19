#!/usr/bin/env bash
# Deploy UniswapV3Reactive on Lasna, register pool, fund, write address to file.
# Usage: ./scripts/deploy-reactive.sh <rpc_url> <private_key> <callback_address> <v3_pool> <output_file>
set -euo pipefail
RPC="$1"
PK="$2"
CALLBACK="$3"
V3_POOL="$4"
OUTPUT="$5"

echo "Deploying UniswapV3Reactive..." >&2

BYTECODE=$(forge inspect UniswapV3Reactive bytecode 2>/dev/null)
ARGS=$(cast abi-encode "constructor(address)" "$CALLBACK")

RESULT=$(cast send --rpc-url "$RPC" --private-key "$PK" \
    --value 5ether --json --gas-limit 5000000 \
    --create "${BYTECODE}${ARGS#0x}" 2>/dev/null)

ADDR=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['contractAddress'])")
STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

if [ "$STATUS" != "0x1" ]; then
    echo "ERROR: Deploy failed (status=$STATUS)" >&2
    exit 1
fi
echo "Reactive: $ADDR" >&2

# Wait for deploy tx to confirm
sleep 5

# Register pool
echo "Registering pool..." >&2
cast send --rpc-url "$RPC" --private-key "$PK" --gas-limit 300000 \
    "$ADDR" "registerPool(uint256,address)" 11155111 "$V3_POOL" >&2
echo "Pool registered" >&2

# Wait for register tx to confirm
sleep 5

# Fund via fund()
echo "Funding reactive..." >&2
cast send --rpc-url "$RPC" --private-key "$PK" --value 5ether \
    "$ADDR" "fund()" >&2
echo "Funded" >&2

# Write address to file for Solidity to read
echo -n "$ADDR" > "$OUTPUT"
echo "Address written to $OUTPUT" >&2
