# V3 Reactive Differential Testing Design

**Goal:** Run the same 3 FCI scenarios (equilibrium, mild, crowdout) through V3 on Sepolia with the Reactive Network adapter computing deltaPlus, and assert it matches the V4 local hook result.

## Architecture

```
EOA --broadcast--> V3CallbackRouter --> V3 Pool (Sepolia)
                                          |
                                     V3 events
                                          |
                                    Reactive Network
                                          |
                                     ReactVM callback
                                          |
                              ReactiveHookAdapter (Sepolia)
                                          |
                                   FCI deltaPlus
```

Both FCI instances (V4 hook + ReactiveHookAdapter) live on Sepolia. Single-chain comparison.

## New Contract: V3CallbackRouter

Minimal contract implementing `IUniswapV3MintCallback` + `IUniswapV3SwapCallback`. Pulls tokens from `tx.origin` via `transferFrom` in callbacks. No constructor args.

Functions:
- `mint(pool, recipient, tickLower, tickUpper, liquidity)` — calls `pool.mint()`, callback does `transferFrom(tx.origin)`
- `swap(pool, recipient, zeroForOne, amountSpecified, sqrtPriceLimit)` — calls `pool.swap()`, callback does `transferFrom(tx.origin)`

`burn()` and `collect()` don't need routing — they don't use callbacks.

## Deployment Sequence

### Sepolia
1. Deploy V3CallbackRouter
2. Approve tokens to router (3 accounts)
3. Deploy ReactiveHookAdapter (constructor: `SEPOLIA_CALLBACK_PROXY`)
4. Set authorized caller on adapter: `setAuthorized(callbackProxy, true)`
5. Create fresh V3 pool (fee=3000, same tokens, same tick spacing)
6. Create fresh V4 pool (fee=3000, same tokens, same FCI hook — gets fresh PoolId/state)

### Reactive Network
7. Deploy ThetaSwapReactive (constructor: adapter address + subscription service)
8. Register fresh V3 pool: `registerPool(SEPOLIA_CHAIN_ID, v3Pool)`

## Scenario.sol Changes

- Add `mapping(uint256 chainId => address) v3Router` to `Scenario` struct
- `registerV3Pool()` takes additional `router` parameter
- `mintPosition()` V3 path: `router.mint(pool, ...)` instead of `pool.mint(...)`
- `executeSwap()` V3 path: `router.swap(pool, ...)` instead of `pool.swap(...)`
- `burnPosition()` V3 path: unchanged (`pool.burn()` + `pool.collect()` don't use callbacks)

## Builder Changes

Separate entry points for V3 and V4:
- `buildEquilibriumV3()` / `buildEquilibriumV4()`
- `buildMildV3()` / `buildMildV4()`
- `buildCrowdoutPhase1V3()` / `buildCrowdoutPhase1V4()` (etc.)

setUp registers both V3 (with router) and V4 paths on Sepolia.

## Comparison (Per-Scenario Increments)

Both V3 and V4 use fresh pools (fee=3000) so state starts at zero.

Per scenario:
1. Read V4 deltaPlus before → run V4 scenario → read after → `v4Delta = after - before`
2. Read V3 deltaPlus before → run V3 scenario → wait ~30s for reactive callback → read after → `v3Delta = after - before`
3. Assert `v4Delta ≈ v3Delta` (5% tolerance via `assertApproxEqRel`)

## Key Addresses

- `SEPOLIA_CALLBACK_PROXY`: `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA`
- `REACTIVE_RPC_URL`: `https://lasna-rpc.rnk.dev/`
- FCI Hook (V4): `0xc3e8Cb062EC61b40530aBea9Df9449F5b95987C0`
- V3 Pool (fee=500, existing): `0xF66da9dd005192ee584a253b024070c9A1A1F4FA`
- Fresh pools use fee=3000 for clean FCI state
