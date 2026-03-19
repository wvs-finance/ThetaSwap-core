# Capponi JIT Sequential Game — Design Spec

## Goal

Build a parameterized Forge script that simulates the Period 1 Capponi JIT sequential game on an Anvil fork of Unichain Sepolia (V4). The script acts as a **delta-plus generator**: given (N, jitCapital, jitEntryProbability, tradeSize), it leaves the forked pool in a post-game state with a measurable fee concentration index (delta-plus). Downstream vault tests consume this state to compare hedged vs unhedged LP outcomes.

## Context

- Extends the existing `Scenario.sol` delta-plus factory (2-LP, 3 fixed recipes) to N passive LPs + 1 JIT LP with probabilistic entry.
- The JIT LP's optimal strategy parameters (p*, l*) are **not known** — this script is the experimental apparatus to discover them by sweeping the parameter space.
- Protocol-agnostic via existing `Protocol` enum dispatch, defaulting to V4.

## Types and Configuration

### JitGameConfig (input)

| Field | Type | Description |
|-------|------|-------------|
| `n` | `uint256` | Number of identical passive LPs |
| `jitCapital` | `uint256` | Liquidity units the JIT LP deploys |
| `jitEntryProbability` | `uint256` | Probability of JIT entry (bps, 0-10000) |
| `tradeSize` | `uint256` | Swap amount that triggers the game |
| `zeroForOne` | `bool` | Swap direction |
| `protocol` | `Protocol` | V3 or V4 dispatch |

### JitGameResult (output)

| Field | Type | Description |
|-------|------|-------------|
| `deltaPlus` | `uint128` | Measured fee concentration index |
| `hedgedLpPayout` | `uint256` | Fees collected by the vault-hedged LP |
| `unhedgedLpPayout` | `uint256` | Fees collected by the non-hedged passive LP with minimum fees (worst performer) |
| `jitLpPayout` | `uint256` | Fees collected by JIT LP (0 if didn't enter) |
| `jitEntered` | `bool` | Whether randomness resolved to entry |

### JitAccounts

| Field | Type | Description |
|-------|------|-------------|
| `passiveLps` | `Vm.Wallet[]` | N wallets at HD indices 0..N-1 |
| `jitLp` | `Vm.Wallet` | HD index N |
| `swapper` | `Vm.Wallet` | HD index N+1 |
| `hedgedIndex` | `uint256` | Which passive LP is the hedged one |

## Wallet Generation

`initJitAccounts(Vm vm, uint256 n)` -> `JitAccounts memory`

- Derives N+2 wallets from MNEMONIC env var using `vm.deriveKey` at sequential HD indices.
- **Note:** `vm.deriveKey` index parameter is `uint32`. Loop counter must be explicitly cast: `vm.deriveKey(mnemonic, path, uint32(i))`.
- Passive LPs: indices 0..N-1
- JIT LP: index N
- Swapper: index N+1
- `hedgedIndex`: 0 by default

Funding via `vm.deal` for ETH + direct token minting on the Anvil fork. Each passive LP gets 1 unit of both tokens. JIT LP gets `jitCapital` units of both.

## Game Execution Flow

`runJitGame(Context storage ctx, JitGameConfig memory cfg)` -> `JitGameResult memory`

0. **Preconditions**: `require(cfg.n >= 2, "JitGame: N must be >= 2")` (need at least 1 hedged + 1 unhedged). `require(cfg.jitEntryProbability <= 10000, "JitGame: probability must be <= 10000 bps")`.
1. **Setup**: Call `initJitAccounts(vm, cfg.n)`. Fund all wallets.
2. **Passive LP entry**: Loop i=0..N-1, each mints 1 unit of liquidity at (TICK_LOWER, TICK_UPPER). Total passive liquidity = N.
3. **JIT decision**: `vm.randomUint(0, 9999)`. If result < `cfg.jitEntryProbability`, JIT LP mints `cfg.jitCapital` liquidity. Set `jitEntered = true`.
4. **Trade arrives**: Execute swap with `cfg.tradeSize` in direction `cfg.zeroForOne`. **Note:** The existing `executeSwap` in Scenario.sol uses a hardcoded `AMOUNT_SPECIFIED`. `JitGame.sol` defines a new `executeSwapWithAmount(ctx, protocol, pk, zeroForOne, amountSpecified)` overload to support parameterized trade size.
5. **JIT exit**: If JIT entered, burn JIT position immediately (same block sandwich).
6. **Passive LP exit**: Loop i=0..N-1. For each LP, record `balanceOf(token0)` and `balanceOf(token1)` before burn, then burn position, then compute `feesCollected = balanceAfter - balanceBefore` for each token. Tag `passiveLps[hedgedIndex]` payout as `hedgedLpPayout`. Select `min(feesCollected)` across all non-hedged LPs as `unhedgedLpPayout`.
7. **Measure delta-plus**: Compute inline HHI from the fee payout array across N passive LPs: `deltaPlus = HHI(payouts) - 1/N`. No dependency on the FCI hook contract.
8. **Return JitGameResult**.

The hedged vs unhedged distinction is labeling only at this stage. The actual hedge payoff modification comes from the vault contract wrapping the hedged LP's position. This script sets up the scenario; vault tests apply the hedge and compare.

## Script Orchestrator

`CapponiJITSequentialGame.s.sol` — thin entrypoint.

`run(uint256 n, uint256 jitCapital, uint256 jitEntryProbability, uint256 tradeSize)`:

1. Fork Unichain Sepolia via `vm.createSelectFork("unichain_sepolia")`
2. Build `Context` — deploy/load PoolManager, PositionManager, tokens, pool
3. Build `JitGameConfig` from args (default: `zeroForOne = true`, `protocol = UniswapV4`)
4. Call `runJitGame(ctx, cfg)` -> `JitGameResult`
5. Emit results via `console.log`

### Invocation

```bash
forge script foundry-script/simulation/CapponiJITSequentialGame.s.sol \
  --fork-url unichain_sepolia \
  --sig "run(uint256,uint256,uint256,uint256)" \
  10 5 7000 1000000000000000000
```

(N=10, JIT capital=5 units, 70% entry probability, 1e18 trade size)

Leaves the Anvil fork in the post-game state for vault tests to snapshot from.

## File Layout

```
foundry-script/
  simulation/
    CapponiJITSequentialGame.s.sol   # Orchestrator (rewrite from scaffold)
    JitGame.sol                       # New: types, accounts, runJitGame()
  types/
    Accounts.sol                      # Untouched
    Context.sol                       # Untouched
    Scenario.sol                      # Untouched
    Protocol.sol                      # Untouched
```

### Import Chain

- `JitGame.sol` imports: `Scenario.sol` (mintPosition, burnPosition, executeSwap, encoding helpers), `Context.sol`, `Protocol.sol`, `forge-std`
- `CapponiJITSequentialGame.s.sol` imports: `JitGame.sol`, `Context.sol`, deploy helpers

## Reused Primitives

From `Scenario.sol`: `mintPosition()`, `burnPosition()`, `encodeMint()`, `encodeDecrease()`, `encodeBurn()` (note: `executeSwap` is NOT reused — `JitGame.sol` defines its own `executeSwapWithAmount` to support parameterized trade size)

From `Context.sol`: `Context` struct

From `Protocol.sol`: `Protocol` enum, `isUniswapV3()`, `isUniswapV4()`

From `Accounts.sol`: `DEFAULT_DERIVATION_PATH` constant

## New Primitives in JitGame.sol

### executeSwapWithAmount

The existing `executeSwap` in Scenario.sol uses a hardcoded `AMOUNT_SPECIFIED` constant. `JitGame.sol` defines a new overload:

```
executeSwapWithAmount(Context storage ctx, Protocol protocol, uint256 pk, bool zeroForOne, int256 amountSpecified)
```

Same V3/V4 dispatch logic as `executeSwap`, but accepts the trade amount as a parameter.

## Constraints

- `n >= 2` (at least 1 hedged + 1 unhedged passive LP)
- `jitEntryProbability <= 10000` bps
- Each passive LP provides exactly 1 unit of liquidity (capital-homogeneous)
- All passive LPs use the same tick range
- JIT entry is resolved via `vm.randomUint` per the configured probability
- Single-block execution (JIT sandwich pattern)
- Protocol-agnostic but defaults to V4
- Fee tracking uses `balanceOf` before/after burn (balance-delta pattern)
- Delta-plus computed inline via HHI (no FCI hook dependency)
