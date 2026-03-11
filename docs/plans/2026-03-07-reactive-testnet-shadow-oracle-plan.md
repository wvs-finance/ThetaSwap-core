# Reactive Testnet Shadow Oracle — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy ThetaSwapReactive + ReactiveHookAdapter on Reactive Network Lasna testnet (callbacks to Sepolia), then validate on-chain FCI against an off-chain Python oracle fed by Dune V3 event data for ETH/USDC 500bps.

**Architecture:** Three deliverables — (1) Dune SQL query + V3 FCI oracle producing expected snapshots, (2) deployment bash script using `forge create` / `cast send` to Reactive Lasna + Sepolia, (3) comparison harness polling on-chain FCI and asserting convergence within ε=1%.

**Tech Stack:** Python 3.11+ (httpx, eth_abi, pycryptodome), Foundry (forge create, cast send/call), Dune MCP for V3 event extraction.

**Design doc:** `docs/plans/2026-03-07-reactive-testnet-shadow-oracle-design.md`

**Network Config:**

| Network | Chain ID | RPC | Callback Proxy |
|---------|----------|-----|----------------|
| Reactive Lasna (testnet) | 5318007 | `https://lasna-rpc.rnk.dev/` | `0x...fffFfF` (system) |
| Ethereum Sepolia | 11155111 | user-provided | `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA` |

**Pool:** ETH/USDC 500bps (`0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`) on Ethereum mainnet (chain ID 1).

**Origin:** Ethereum mainnet (chain ID 1) — V3 events.
**Destination:** Ethereum Sepolia (chain ID 11155111) — adapter receives callbacks.

---

## Task 1: Dune query — V3 events for ETH/USDC 500bps

**Files:**
- Create: `research/data/queries/dune/fci_v3_weth_usdc_events.sql`

**Step 1: Write the Dune SQL query**

Query pulls Swap, Mint, Burn, Collect events from the V3 pool over a parameterized block range. Uses decoded Dune tables (`uniswap_v3_ethereum.UniswapV3Pool_evt_*`).

```sql
-- Dune Query: V3 events for FCI shadow oracle
-- Pool: ETH/USDC 500bps (0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640)
-- Parameterized: {{block_start}}, {{block_end}}

WITH swaps AS (
  SELECT
    'Swap' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    NULL AS owner,
    NULL AS tickLower,
    NULL AS tickUpper,
    NULL AS liquidity,
    CAST(amount0 AS varchar) AS amount0,
    CAST(amount1 AS varchar) AS amount1,
    NULL AS fee_amount0,
    NULL AS fee_amount1,
    tick AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Swap
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
),
mints AS (
  SELECT
    'Mint' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    CAST(owner AS varchar) AS owner,
    tickLower,
    tickUpper,
    CAST(amount AS varchar) AS liquidity,
    CAST(amount0 AS varchar) AS amount0,
    CAST(amount1 AS varchar) AS amount1,
    NULL AS fee_amount0,
    NULL AS fee_amount1,
    NULL AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Mint
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
),
burns AS (
  SELECT
    'Burn' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    CAST(owner AS varchar) AS owner,
    tickLower,
    tickUpper,
    CAST(amount AS varchar) AS liquidity,
    CAST(amount0 AS varchar) AS amount0,
    CAST(amount1 AS varchar) AS amount1,
    NULL AS fee_amount0,
    NULL AS fee_amount1,
    NULL AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Burn
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
),
collects AS (
  SELECT
    'Collect' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    CAST(owner AS varchar) AS owner,
    tickLower,
    tickUpper,
    NULL AS liquidity,
    NULL AS amount0,
    NULL AS amount1,
    CAST(amount0 AS varchar) AS fee_amount0,
    CAST(amount1 AS varchar) AS fee_amount1,
    NULL AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Collect
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
)
SELECT * FROM swaps
UNION ALL SELECT * FROM mints
UNION ALL SELECT * FROM burns
UNION ALL SELECT * FROM collects
ORDER BY block_number, log_index
```

**Step 2: Save the query to Dune via MCP and execute**

Use `mcp__dune__createDuneQuery` then `mcp__dune__executeQueryById` with a recent 500-block window.

**Step 3: Download results and save as raw fixture**

Save to `research/data/raw/fci_v3_weth_usdc_events.json`.

**Step 4: Commit**

```bash
git add -f research/data/queries/dune/fci_v3_weth_usdc_events.sql
git commit -m "feat(003): Dune query — V3 Swap/Mint/Burn/Collect events for ETH/USDC 500bps"
```

---

## Task 2: V3 FCI oracle — off-chain computation

**Files:**
- Create: `research/scripts/fci_v3_oracle.py`
- Test: `research/tests/test_fci_v3_oracle.py`
- Reference: `research/data/scripts/fci_oracle.py` (V4 oracle)

**Step 1: Write the failing test**

```python
"""Tests for V3 FCI oracle — mirrors V4 oracle tests but with V3 event types."""
from __future__ import annotations

import math
from fci_v3_oracle import FCIStateV3, Q128, v3_position_key

def test_v3_position_key_matches_solidity():
    """keccak256(abi.encodePacked(owner, tickLower, tickUpper))"""
    # Known value from Solidity: v3PositionKey(0xABC...001, -60, 60)
    pk = v3_position_key("0x" + "00" * 19 + "01", -60, 60)
    assert len(pk) == 32
    assert isinstance(pk, bytes)

def test_single_mint_burn_produces_index():
    state = FCIStateV3()
    owner = "0x" + "00" * 19 + "01"
    state.process_mint(owner, -60, 60, 1_000_000, block_number=100)
    state.process_swap(tick=0)
    state.process_swap(tick=10)
    state.process_collect(owner, -60, 60, fee0=500, fee1=0)
    state.process_burn(owner, -60, 60, 1_000_000, block_number=110)
    assert state.pos_count == 0
    assert state.accumulated_sum > 0
    idx = state.to_index_a()
    assert 0 < idx <= (1 << 128) - 1

def test_collect_without_burn_does_not_affect_index():
    state = FCIStateV3()
    owner = "0x" + "00" * 19 + "01"
    state.process_mint(owner, -60, 60, 1_000_000, block_number=100)
    state.process_collect(owner, -60, 60, fee0=500, fee1=0)
    assert state.accumulated_sum == 0  # No burn yet — no FCI term

def test_snapshot_fields():
    state = FCIStateV3()
    snap = state.snapshot(block_number=100)
    assert "blockNumber" in snap
    assert "expectedIndexA" in snap
    assert "expectedPosCount" in snap
    assert "expectedThetaSum" in snap
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=research/scripts:research pytest research/tests/test_fci_v3_oracle.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fci_v3_oracle'`

**Step 3: Write the V3 oracle implementation**

Adapt `fci_oracle.py` (V4) → `fci_v3_oracle.py` (V3):
- Position key: `keccak256(owner, tickLower, tickUpper)` — no salt
- `process_mint()`, `process_burn()`, `process_collect()`, `process_swap()` instead of ModifyLiquidity
- Collect fees accumulate per-position in `collected_fees` dict, consumed on Burn
- Synthetic fee growth: `fee0 / posLiquidity` (from Burn amounts)
- `replay()` reads the V3 event JSON and drives the state machine
- `main()` produces `research/data/fixtures/fci_v3_weth_usdc.json`

Key differences from V4 oracle:
- No `salt` in position key
- Collect events accumulate fees (no FCI term added)
- Burn events consume accumulated fees, compute FeeShareRatio, add FCI term
- Range key is still `keccak256(tickLower, tickUpper)`

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=research/scripts:research pytest research/tests/test_fci_v3_oracle.py -v`
Expected: 4 PASS

**Step 5: Run oracle against real Dune data**

Run: `PYTHONPATH=research/scripts:research python research/scripts/fci_v3_oracle.py`
Expected: Produces `research/data/fixtures/fci_v3_weth_usdc.json` with snapshots

**Step 6: Commit**

```bash
git add research/scripts/fci_v3_oracle.py research/tests/test_fci_v3_oracle.py
git commit -m "feat(003): V3 FCI oracle — off-chain computation from Dune events"
```

---

## Task 3: Environment template and deployment script

**Files:**
- Create: `scripts/.env.example`
- Create: `scripts/deploy-reactive-testnet.sh`

**Step 1: Create .env.example**

```bash
# Reactive Network Lasna testnet
REACTIVE_RPC_URL=https://lasna-rpc.rnk.dev/
REACTIVE_CHAIN_ID=5318007

# Ethereum Sepolia (destination for callbacks)
SEPOLIA_RPC_URL=https://rpc.sepolia.org
SEPOLIA_CHAIN_ID=11155111
SEPOLIA_CALLBACK_PROXY=0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA

# Deployer (must be funded on both networks)
DEPLOYER_PRIVATE_KEY=0x...

# V3 pool to monitor (Ethereum mainnet, chain ID 1)
V3_POOL=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
V3_ORIGIN_CHAIN_ID=1
```

**Step 2: Create deployment script**

```bash
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
```

**Step 3: Verify script is syntactically valid**

Run: `bash -n scripts/deploy-reactive-testnet.sh`
Expected: exit 0 (no syntax errors)

**Step 4: Commit**

```bash
git add scripts/.env.example scripts/deploy-reactive-testnet.sh
chmod +x scripts/deploy-reactive-testnet.sh
git commit -m "feat(003): deployment script — Reactive Lasna + Sepolia adapter"
```

---

## Task 4: Comparison harness

**Files:**
- Create: `research/scripts/compare_fci.py`
- Test: `research/tests/test_compare_fci.py`

**Step 1: Write the failing test**

```python
"""Tests for compare_fci — mocked RPC responses."""
from __future__ import annotations

from compare_fci import parse_index_response, check_convergence

def test_parse_index_response():
    """Decode (uint128 indexA, uint256 thetaSum, uint256 posCount) from eth_call."""
    # All zeros
    raw = "0x" + "00" * 96
    idx, theta, pos = parse_index_response(raw)
    assert idx == 0
    assert theta == 0
    assert pos == 0

def test_check_convergence_pass():
    result = check_convergence(
        on_chain_index=1000,
        off_chain_index=1005,
        epsilon=0.01,
    )
    assert result.passed is True
    assert result.drift < 0.01

def test_check_convergence_fail():
    result = check_convergence(
        on_chain_index=1000,
        off_chain_index=1200,
        epsilon=0.01,
    )
    assert result.passed is False
    assert result.drift > 0.01
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=research/scripts:research pytest research/tests/test_compare_fci.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'compare_fci'`

**Step 3: Write the comparison harness**

`compare_fci.py`:
- `parse_index_response(hex_data)` — ABI-decode `(uint128, uint256, uint256)` from `getIndex()` return
- `check_convergence(on_chain, off_chain, epsilon)` — returns `ConvergenceResult(passed, drift)`
- `poll_on_chain(rpc_url, adapter, pool_key)` — `eth_call` to `getIndex(PoolKey)` via httpx
- `load_off_chain(fixtures_path)` — load expected snapshots from oracle JSON
- `main()` — load fixtures, poll on-chain, compare, print report

Environment variables: `SEPOLIA_RPC_URL`, `ADAPTER_ADDRESS`, `FIXTURES_PATH` (default: `research/data/fixtures/fci_v3_weth_usdc.json`).

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=research/scripts:research pytest research/tests/test_compare_fci.py -v`
Expected: 3 PASS

**Step 5: Commit**

```bash
git add research/scripts/compare_fci.py research/tests/test_compare_fci.py
git commit -m "feat(003): comparison harness — on-chain vs off-chain FCI convergence check"
```

---

## Task 5: End-to-end integration

**Step 1: Fund deployer on Sepolia and Reactive Lasna**

```bash
# Get Sepolia ETH from faucet (manual)
# Get lREACT: send Sepolia ETH to faucet contract
cast send 0x9b9BB25f1A81078C544C829c5EB7822d747Cf434 \
    "request(address)" "$DEPLOYER_ADDRESS" \
    --rpc-url "$SEPOLIA_RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY" \
    --value 1ether
```

**Step 2: Deploy**

Run: `./scripts/deploy-reactive-testnet.sh`
Expected: prints adapter + reactive addresses

**Step 3: Add deployed addresses to .env**

```bash
echo "ADAPTER_ADDRESS=0x..." >> scripts/.env
echo "REACTIVE_ADDRESS=0x..." >> scripts/.env
```

**Step 4: Verify subscription is active**

```bash
cast call 0x0000000000000000000000000000000000fffFfF \
    "debt(address)(uint256)" "$REACTIVE_ADDRESS" \
    --rpc-url "$REACTIVE_RPC_URL"
```
Expected: returns debt amount (confirms contract is registered)

**Step 5: Wait for events, then run comparison**

Wait 10-30 minutes for V3 events to flow through Reactive Network.

Run: `PYTHONPATH=research/scripts:research python research/scripts/compare_fci.py`
Expected: convergence report showing on-chain matches off-chain within ε=1%

**Step 6: Commit any adjustments**

```bash
git add -A
git commit -m "feat(003): end-to-end shadow oracle validation on Reactive Lasna testnet"
```

---

## Dependency Graph

```
Task 1: Dune query (V3 events)
  └─ Task 2: V3 FCI oracle (depends: Dune data from Task 1)
Task 3: Deploy script (independent)
Task 4: Comparison harness (depends: oracle output format from Task 2)
Task 5: End-to-end (depends: all above)
```

Tasks 1+3 can run in parallel. Task 2 needs Task 1 output. Task 4 needs Task 2 types. Task 5 needs everything.
