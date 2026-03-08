# Reactive Network Testnet Shadow Oracle — Design

**Date**: 2026-03-07
**Feature**: 003-reactive-integration
**Branch**: 003-reactive-integration
**Pool**: ETH/USDC 500bps (`0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`)

## Problem

Reactive Network contracts cannot be fork-tested in Foundry (SystemContract at `0x...fffFfF` cannot be simulated). We need an end-to-end validation strategy that deploys real contracts on Reactive Network testnet, lets them process real V3 events, and compares the resulting FCI state against an independent off-chain oracle.

## Architecture

```
Ethereum mainnet                    Reactive Network testnet
┌──────────────────┐               ┌─────────────────────────┐
│ ETH/USDC V3 pool │──V3 events──▶│ ThetaSwapReactive       │
│ 0x88e6...5640    │               │  (RN instance: subs)    │
│                  │               │  (ReactVM: processLog)  │
└──────────────────┘               └──────────┬──────────────┘
                                              │ Callback
                                              ▼
                                   ┌─────────────────────────┐
                                   │ ReactiveHookAdapter     │
                                   │  (Sepolia)              │
                                   │  getIndex() → FCI state │
                                   └──────────┬──────────────┘
                                              │ cast call / httpx
                                              ▼
Off-chain                          ┌─────────────────────────┐
│ fci_v3_oracle.py │──expected───▶│ compare_fci.py          │
│ (Dune SQL data)  │               │  |on_chain - off_chain| │
└──────────────────┘               │  < ε (1%) ?             │
                                   └─────────────────────────┘
```

## Deliverables

### 1. Deployment script (`scripts/deploy-reactive-testnet.sh`)

Three steps, all via `forge create` / `cast send`:

1. **Deploy ReactiveHookAdapter on Sepolia**
   - Constructor arg: Sepolia callback proxy address
   - Sepolia is the destination chain for Reactive testnet callbacks

2. **Deploy ThetaSwapReactive on Reactive Network testnet**
   - Constructor args: `(adapter_address_on_sepolia, service_address)`
   - Must be `payable` — deploy with `--value 0.1ether`
   - Self-subscribes to PoolRegistered/PoolUnregistered in constructor

3. **Register the V3 pool**
   - `cast send $REACTIVE "registerPool(uint256,address)" 1 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`
   - Creates 4 subscriptions: Swap, Mint, Burn, Collect on Ethereum mainnet (chain ID 1)

Environment variables (`scripts/.env`, gitignored):
- `REACTIVE_RPC_URL` — Reactive Network testnet RPC
- `SEPOLIA_RPC_URL` — Sepolia RPC
- `DEPLOYER_PRIVATE_KEY` — funded on both networks

### 2. V3 FCI oracle (`research/scripts/fci_v3_oracle.py`)

Off-chain FCI computation adapted from existing `fci_oracle.py` (V4) for V3 events:

- **Position key**: `keccak256(owner, tickLower, tickUpper)` (no salt)
- **Events**: Swap, Mint, Burn, Collect (not ModifyLiquidity)
- **Collect accumulation**: fees stored per-position, consumed on Burn (mirrors ReactVM `CollectedFees` pattern)
- **Synthetic fee growth**: derived from Burn amounts, not native feeGrowthInside

Data source: Dune SQL query (`research/data/queries/dune/fci_v3_weth_usdc_events.sql`) pulling V3 events for the pool over a configurable block range.

Output: JSON fixtures at `research/data/fixtures/fci_v3_weth_usdc.json`:
```json
{
  "pool": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
  "blockRange": [21500000, 21500500],
  "eventCount": 1234,
  "snapshots": [
    {
      "blockNumber": 21500500,
      "expectedIndexA": "0x...",
      "expectedThetaSum": "0x...",
      "expectedPosCount": 42
    }
  ]
}
```

### 3. Comparison harness (`research/scripts/compare_fci.py`)

Polls on-chain FCI from the Sepolia adapter, compares against oracle fixtures.

**Inputs** (env vars):
- `SEPOLIA_RPC_URL`
- `ADAPTER_ADDRESS` — ReactiveHookAdapter on Sepolia
- Fixtures path (default: `research/data/fixtures/fci_v3_weth_usdc.json`)

**Convergence model**: On-chain FCI lags real-time due to Reactive Network event delivery latency. Comparison checks convergence after a configurable wait period, not block-exact matching.

**Tolerance**: ε = 1% relative error on `indexA`.

**Output**:
```
Pool: ETH/USDC 500bps
Window: block 21500000 → 21500500

  On-chain  indexA: 0x1a3f...  posCount: 42  thetaSum: 0x8b2...
  Off-chain indexA: 0x1a41...  posCount: 42  thetaSum: 0x8b2...
  Drift: 0.02%  PASS

  Overall: 1/1 snapshots converged within ε=1%
```

### 4. Dune query (`research/data/queries/dune/fci_v3_weth_usdc_events.sql`)

Pulls V3 Swap, Mint, Burn, Collect events for `0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640` over a parameterized block range. Returns:
- `event_type` (Swap/Mint/Burn/Collect)
- `block_number`, `tx_hash`, `log_index`
- Event-specific fields: tick, owner, tickLower, tickUpper, liquidity, amount0, amount1, feeAmount0, feeAmount1

## File Map

```
scripts/
  deploy-reactive-testnet.sh        Deploy + register pool
  .env.example                      Template for required env vars

research/
  scripts/
    fci_v3_oracle.py                Off-chain V3 FCI computation
    compare_fci.py                  On-chain vs off-chain comparison
  data/
    queries/dune/
      fci_v3_weth_usdc_events.sql   Dune query for V3 events
    fixtures/
      fci_v3_weth_usdc.json         Oracle output (generated)
```

## No New Solidity

Existing `src/reactive-integration/` contracts deployed as-is:
- `ThetaSwapReactive.sol`
- `adapters/uniswapV3/ReactiveHookAdapter.sol`
- All modules, types, libraries

## Workflow

1. Create Dune query → execute → download V3 events
2. Run `fci_v3_oracle.py` → produce expected snapshots
3. Run `deploy-reactive-testnet.sh` → deploy contracts, register pool
4. Wait for events to flow (minutes to hours)
5. Run `compare_fci.py` → assert convergence within ε

## Constraints

- `forge script --broadcast` does NOT work for Reactive Network (SystemContract)
- All deployment via `forge create` / `cast send`
- Sepolia callback proxy address must be fetched from Reactive Network docs
- Testnet ETH required on both Reactive testnet and Sepolia
- Pool activity on Ethereum mainnet drives event flow — cannot be accelerated
