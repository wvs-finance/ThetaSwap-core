#!/usr/bin/env bash
# V3 Reactive FCI V2 Integration Test — fully reproducible.
# Deploys everything fresh, plays 2-LP scenario, waits for callbacks, verifies deltaPlus > 0.
#
# Uses a DEDICATED reactive-deployer EOA (HD index 4) for clean ReactVM.
# Unsubscribes any previous reactive from this deployer before testing.
#
# Usage: ./scripts/run-v3-integration.sh
#
# Prerequisites:
#   - .env with MNEMONIC, ALCHEMY_API_KEY, REACTIVE_RPC_URL
#   - Deployer (index 0) funded: Sepolia ~0.5 ETH
#   - Reactive deployer (index 4) funded: Lasna ~15 lREACT
#     (first run: fund via deployer → faucet → index 4 transfer)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

source .env 2>/dev/null || true

SEPOLIA_RPC="https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}"
LASNA_RPC="${REACTIVE_RPC_URL:?REACTIVE_RPC_URL not set}"
TEST_FILE="test/fee-concentration-index-v2/protocols/uniswapV3/UniswapV3FeeConcentrationIndex.integration.t.sol"
CONTRACT="UniswapV3FCI_IntegrationScript"
STATE_FILE="broadcast/v3-integration-state.json"
REACTIVE_FILE="broadcast/reactive-addr.txt"
PREV_REACTIVE_FILE="broadcast/prev-reactive-addr.txt"
V3_POOL="${V3_POOL:-0xF66da9dd005192ee584a253b024070c9A1A1F4FA}"

# HD index 0 = deployer (Sepolia), HD index 4 = reactiveDeployer (Lasna)
DEPLOYER_PK=$(cast wallet private-key --mnemonic "$MNEMONIC" --mnemonic-derivation-path "m/44'/60'/0'/0/0" 2>/dev/null)
REACTIVE_PK=$(cast wallet private-key --mnemonic "$MNEMONIC" --mnemonic-derivation-path "m/44'/60'/0'/0/4" 2>/dev/null)
REACTIVE_DEPLOYER=$(cast wallet address --mnemonic "$MNEMONIC" --mnemonic-derivation-path "m/44'/60'/0'/0/4" 2>/dev/null)

echo "Deployer (Sepolia):  $(cast wallet address --mnemonic "$MNEMONIC" --mnemonic-derivation-path "m/44'/60'/0'/0/0" 2>/dev/null)"
echo "Reactive deployer:   $REACTIVE_DEPLOYER"
echo ""

# ── Phase 0: Cleanup — unsubscribe previous reactive if any ──
if [ -f "$PREV_REACTIVE_FILE" ]; then
    PREV_REACTIVE=$(cat "$PREV_REACTIVE_FILE")
    echo "=== Phase 0: Unsubscribe previous reactive $PREV_REACTIVE ==="
    cast send --rpc-url "$LASNA_RPC" --private-key "$REACTIVE_PK" --gas-limit 300000 \
        "$PREV_REACTIVE" "unregisterPool(uint256,address)" 11155111 "$V3_POOL" 2>&1 | grep status || true
    echo ""
fi

# ── Phase 0b: Fund reactive deployer if needed ──
REACTIVE_BAL=$(cast balance --rpc-url "$LASNA_RPC" "$REACTIVE_DEPLOYER" --ether 2>/dev/null)
echo "Reactive deployer Lasna balance: $REACTIVE_BAL lREACT"
# If balance < 12, fund from main deployer
NEED_FUND=$(python3 -c "print('yes' if float('$REACTIVE_BAL') < 12 else 'no')")
if [ "$NEED_FUND" = "yes" ]; then
    echo "Funding reactive deployer with 15 lREACT from main deployer..."
    cast send --rpc-url "$LASNA_RPC" --private-key "$DEPLOYER_PK" \
        --value 15ether "$REACTIVE_DEPLOYER" 2>&1 | grep status
    echo ""
fi

# ── Phase 1: Deploy Sepolia ──
echo "=== Phase 1: Deploy FCI V2 + Facet + Callback on Sepolia ==="
forge script "${TEST_FILE}:${CONTRACT}" \
    --sig "deploy()" \
    --broadcast --slow \
    --rpc-url "$SEPOLIA_RPC" \
    -vv

CALLBACK=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['callback'])")
# Read FRESH pool address from state (deploy() creates a new pool each run)
V3_POOL=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['v3Pool'])")
echo "Callback: $CALLBACK"
echo "V3 Pool:  $V3_POOL"
echo ""

# ── Phase 2: Deploy Reactive on Lasna (dedicated EOA → clean ReactVM) ──
echo "=== Phase 2: Deploy Reactive on Lasna (dedicated deployer) ==="
./scripts/deploy-reactive.sh "$LASNA_RPC" "$REACTIVE_PK" "$CALLBACK" "$V3_POOL" "$REACTIVE_FILE"
REACTIVE=$(cat "$REACTIVE_FILE")
echo "Reactive: $REACTIVE"

# Save for cleanup on next run
cp "$REACTIVE_FILE" "$PREV_REACTIVE_FILE"

echo "Waiting 15s for subscriptions to activate..."
sleep 15

# ── Phase 3: Mint + Swap ──
echo ""
echo "=== Phase 3: Mint 2 LPs (1:2) + Swap ==="
forge script "${TEST_FILE}:${CONTRACT}" \
    --sig "mint()" \
    --broadcast --slow \
    --rpc-url "$SEPOLIA_RPC" \
    -vv

echo ""
echo "Waiting 90s for mint + swap callbacks..."
sleep 90

# ── Phase 4: Burn ──
echo ""
echo "=== Phase 4: Burn both LPs ==="
forge script "${TEST_FILE}:${CONTRACT}" \
    --sig "burn()" \
    --broadcast --slow \
    --rpc-url "$SEPOLIA_RPC" \
    -vv

echo ""
echo "Waiting 90s for burn callbacks..."
sleep 90

# ── Phase 5: Verify ──
echo ""
echo "=== Phase 5: Verify ==="
forge script "${TEST_FILE}:${CONTRACT}" \
    --sig "verify()" \
    --rpc-url "$SEPOLIA_RPC" \
    -vv

echo ""
echo "=== DONE ==="
