# Codebase Concerns

**Analysis Date:** 2026-03-18

---

## Tech Debt

**FCIProtocolLib stubs — all four functions revert unconditionally:**
- Issue: `positionKey`, `currentTick`, `poolRangeFeeGrowthInside`, `latestPositionFeeGrowthInside` in `FCIProtocolLib.sol` all contain `revert("not implemented")`. These are intended as per-protocol overrides but the base implementations are unusable. Any new protocol that inherits from `FCIProtocolFacet` and forgets to override any of these four functions will silently register but crash at runtime.
- Files: `src/fee-concentration-index-v2/libraries/FCIProtocolLib.sol`
- Impact: A third protocol added to FCI V2 using `FCIProtocolFacet` as its base would inherit unimplemented functions with no compile-time error — failures only at transaction time.
- Fix approach: Either remove `FCIProtocolLib.sol` entirely (all protocol-specific logic lives in concrete facets like `UniswapV3Facet`) or mark as abstract base with explicit `mustOverride` NatDoc convention.

**`PoolKeyExtLib.fromPoolRptToPoolKey` only reads pool address — returns empty PoolKey fields:**
- Issue: `fromPoolRptToPoolKey` reads a single address from `poolRpt` and sets `key.hooks = fciHook` but leaves `currency0`, `currency1`, `fee`, `tickSpacing` all zero. The TODO comment confirms this is unfinished.
- Files: `src/fee-concentration-index-v2/libraries/PoolKeyExtLib.sol:16`
- Impact: `FCIProtocolFacet.listen()` — the template contract — produces a structurally invalid PoolKey. Any protocol that uses `FCIProtocolFacet` directly instead of `UniswapV3Facet` or `NativeUniswapV4Facet` will register a broken pool.
- Fix approach: Per-protocol facets must override `listen()` entirely (as `UniswapV3Facet` does). `FCIProtocolFacet` should be marked abstract or removed from production deployments.

**`FeeConcentrationIndexV2.getDeltaPlusEpoch` ignores the `flags` parameter — always reads V4 epoch storage:**
- Issue: `getDeltaPlusEpoch(PoolKey, bytes2 flags)` calls `protocolEpochFciStorage(flags)` correctly but the V1 `FeeConcentrationIndex.getDeltaPlusEpoch` comment says `// TODO(chunk-3): reactive ? reactiveEpochFciStorage() : epochFciStorage()`. The V1 function always calls `epochDeltaPlus(poolId)` regardless of the `reactive` bool.
- Files: `src/fee-concentration-index/FeeConcentrationIndex.sol:206`
- Impact: V1 epoch delta-plus reads are incorrect for reactive pools — reads native V4 epoch storage instead of the reactive epoch namespace. Vault oracle poke using V1 with `reactive=true` returns wrong FCI signal.
- Fix approach: Implement the reactive epoch storage dispatch in `FeeConcentrationIndex.getDeltaPlusEpoch`.

**`setProtocolFacet` has commented-out access control:**
- Issue: `setProtocolFacet(bytes2, IFCIProtocolFacet)` in `FeeConcentrationIndexRegistryStorageMod.sol` has `// note: Add this from Compose` with `// LibOwner.requireOwner();` commented out. The gate is currently missing; the function has no caller restriction.
- Files: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol:20`
- Impact: Any address can call `FeeConcentrationIndexV2.registerProtocolFacet()` to overwrite a registered facet address. An attacker can point the V3 or V4 facet to a malicious contract and redirect all `delegatecall`s from the FCI core.
- Fix approach: Add `requireOwner()` inside `setProtocolFacet` or enforce at the `FeeConcentrationIndexV2.registerProtocolFacet` call site before removing the comment. The `requireOwner()` call is already present one level up in `FeeConcentrationIndexV2.registerProtocolFacet` — verify that gate is sufficient given the delegatecall context.

**`fciV2Storage()` function declared and imported but never called:**
- Issue: `fciV2Storage()` returns `FeeConcentrationIndexV2Storage` at slot `keccak256("thetaSwap.fci")`. It is imported in `FeeConcentrationIndexV2.sol` but never invoked — all actual reads use `protocolFciStorage(flag)` which hashes `("thetaSwap.fci", flag)`. The base slot accessor is dead code.
- Files: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol:23`, `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:26`
- Impact: Dead import obscures the storage layout. If ever called accidentally it accesses a slot that collides with V1's `FCI_STORAGE_SLOT` (both are `keccak256("thetaSwap.fci")`).
- Fix approach: Remove `fciV2Storage()` and its import from `FeeConcentrationIndexV2.sol`.

**`V3CallbackRouter` (non-production utility) lives in `src/`:**
- Issue: `V3CallbackRouter` is explicitly documented "Not for production" but resides in `src/utils/` alongside production contracts. It accepts arbitrary callers for mint and swap callbacks.
- Files: `src/utils/V3CallbackRouter.sol`
- Impact: If accidentally deployed with a production system it provides an unauthenticated token pull path for any pool. Also pollutes the deployment surface.
- Fix approach: Move to `test/fixtures/` or `foundry-script/` and exclude from any production deployment manifests.

---

## Known Bugs

**First-swap `tickBefore` defaults to `tickAfter` — FCI swap count inflated on pool launch:**
- Symptoms: On the first swap observed on a pool via the Reactive Network, `getLastTick` returns `isSet=false`. `mutateV3Payload` then sets `tickBefore = tickAfter`. `sortTicks(tickAfter, tickAfter)` produces `tickMin == tickMax`. `incrementOverlappingRanges` still increments every range that "intersects" a zero-width tick range. Whether `intersects` returns true for an empty range depends on the library's boundary conditions.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol:22`
- Trigger: First reactive swap on any newly subscribed V3 pool before any shadow tick exists.
- Workaround: The first swap after `listen()` / `registerPool()` carries a benign tick delta that may or may not overlap any position range. In practice, if no LPs have minted yet, no ranges exist and the effect is zero.

**Shadow position underflow on burn when ReactVM missed the mint:**
- Symptoms: If a V3 Mint event is dropped (network partition, subscription gap, contract redeployment), the shadow liquidity for that position remains at zero. When the corresponding Burn arrives, `setPositionShadow(pool, posKey, 0 - liquidity)` runs inside `unchecked` block, wrapping to `type(uint128).max`.  The callback then sends `posLiqBefore = ~0` to the Sepolia callback, and `decodePosLiqBefore` overrides the real position liquidity with the wrapped value. FCI then accumulates an astronomically large `xk` term.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol:46-47`
- Trigger: Any gap in Reactive Network event delivery for Mint events followed by a Burn.
- Workaround: None currently. The `posLiqBefore > 0` check in `latestPositionFeeGrowthInside` prevents zero overrides but does not protect against wrapped values.

---

## Security Considerations

**`registerProtocolFacet` is callable by owner only, but `setProtocolFacet` module function has no guard:**
- Risk: As noted in Tech Debt, `setProtocolFacet` in the storage module has a commented-out `requireOwner()`. The external entry point `FeeConcentrationIndexV2.registerProtocolFacet` does call `requireOwner()` before `setProtocolFacet`. Since `setProtocolFacet` itself is a free function (not a storage-internal helper), there is no defense-in-depth if it gets called from a future code path that skips the outer gate.
- Files: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol:19`
- Current mitigation: Single-layer `requireOwner()` at the `FeeConcentrationIndexV2` entry point.
- Recommendations: Re-enable `requireOwner()` inside `setProtocolFacet` itself as defense-in-depth.

**`UniswapV3Callback.unlockCallbackReactive` validates `rvmSender == rvmId` but `rvmId` is mutable by owner:**
- Risk: `setRvmId` allows the owner to redirect which ReactVM identity is trusted. If ownership is compromised, an attacker can set `rvmId` to any address they control and inject arbitrary event payloads, causing the FCI to accumulate fraudulent terms.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol:55-59`
- Current mitigation: `requireOwner()` on `setRvmId`.
- Recommendations: Consider a timelock or two-step ownership transfer for critical addresses.

**`V3 slot0()` reads on callback — stale tick if V3 pool was manipulated in same block:**
- Risk: `UniswapV3Facet.currentTick()` calls `IUniswapV3Pool(pool).slot0()` on the origin chain via a staticcall on the callback chain. For `AFTER_SWAP`, `AFTER_ADD_LIQUIDITY`, and `BEFORE_REMOVE_LIQUIDITY`, the tick read is from the pool's current state, not the state at the time the log was emitted. In a multi-transaction block on the origin chain, the tick may have moved between the logged event and the callback.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:167`
- Current mitigation: The Reactive Network introduces latency that makes same-block manipulation unlikely; `BEFORE_SWAP` action uses the injected `tickBefore` from the payload mutator instead.
- Recommendations: Document this as an accepted approximation, or read tick from the event data directly.

**`UniswapV3Facet.onlyDelegateCall` modifier checks `fciFacetAdminStorage(UNISWAP_V3_REACTIVE).fci` — admin storage can be changed by owner post-deploy:**
- Risk: The `onlyDelegateCall` guard verifies `address(this) == address(fciFacetAdminStorage(UNISWAP_V3_REACTIVE).fci)`. Because `setFci` on the admin storage can be called by the owner, an owner can temporarily point `fci` at any address, effectively disabling the guard.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:54-57`
- Current mitigation: `requireOwner()` on admin setters.
- Recommendations: Accept this as an operational risk managed by key security; document it explicitly.

**`poolWhitelist` in `UniswapV3ReactVMStorageMod` is never enforced in `react()` or `mutateV3Payload()`:**
- Risk: The `poolWhitelist` mapping exists with `isWhitelisted`/`setWhitelisted` functions, but neither `UniswapV3Reactive.react()` nor `mutateV3Payload()` checks `isWhitelisted(chainId, pool)` before processing events. Any pool on the subscribed chain that emits `Swap/Mint/Burn` signatures will be processed.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/modules/UniswapV3ReactVMStorageMod.sol:64-70`, `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol:45-62`
- Current mitigation: Subscription is controlled by `registerPool` (owner-only). Only explicitly subscribed pools send events. But the ReactVM processes all events matching the subscribed signatures regardless of pool identity.
- Recommendations: Add `isWhitelisted` check at the start of `react()` or document that subscription acts as the sole admission gate.

---

## Performance Bottlenecks

**`incrementOverlappingRanges` — O(N) loop over all active ranges on every swap:**
- Problem: Both `UniswapV3Facet.incrementOverlappingRanges` and `NativeUniswapV4Facet.incrementOverlappingRanges` iterate over `$.registries[poolId].activeRangeCount()` positions and call `intersects()` for each.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:224-233`, `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol:208-217`
- Cause: There is no tick-indexed range index; the full active range set must be scanned linearly.
- Improvement path: A tick-indexed skiplist or a segment tree over active ranges would reduce per-swap cost to O(log N + K) where K is the number of overlapping ranges. In the reactive path this runs inside a callback on Sepolia, so gas is less critical than in V4 native hooks — but it still limits the number of trackable positions per pool.

**`getRegistryAllSnapshots` — O(N) view function exposed as non-view (`external returns`) requiring a transaction:**
- Problem: The five `getRegistry*` functions in `FeeConcentrationIndexV2` use `LibCall.delegateCallContract` which requires a mutable call context, preventing them from being `view`. Callers must use `eth_call` but any contract trying to call these for computation will incur a state-change transaction.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:371-413`
- Cause: `LibCall.delegateCallContract` is not compatible with `staticcall`; Solidity therefore cannot mark these functions `view`.
- Improvement path: Expose a parallel set of pure view functions that read from `protocolFciStorage(flag)` directly without delegatecall, for off-chain read paths.

**`FeeConcentrationIndexV2` hook handlers — 6–9 `delegatecall`s per hook invocation:**
- Problem: Every hook call (`afterAddLiquidity`, `afterSwap`, `afterRemoveLiquidity`, `beforeRemoveLiquidity`) makes multiple separate `LibCall.delegateCallContract` calls to the facet (up to 9 in `afterRemoveLiquidity`). Each delegatecall carries overhead for ABI encoding, dispatch, and context switch.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:59-296`
- Cause: The facet pattern requires per-function dispatch; there is no batching.
- Improvement path: Aggregate multiple reads into a single delegatecall that returns a tuple, reducing round-trips from 6–9 to 2–3 per hook.

---

## Fragile Areas

**V1 FCI and V2 FCI share identical diamond storage slot (`keccak256("thetaSwap.fci")`):**
- Files: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol:28`, `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol:21`
- Why fragile: `FCI_STORAGE_SLOT` and `FCI_V2_STORAGE_SLOT` both equal `keccak256("thetaSwap.fci")`. If V1 `FeeConcentrationIndex` and V2 `FeeConcentrationIndexV2` are ever deployed as facets in the same diamond proxy, their storage structs collide. The V1 struct layout (`poolManager` as first field) differs from V2 (no `poolManager`), so reads/writes would corrupt each other silently.
- Safe modification: Ensure V1 and V2 are never co-deployed in the same proxy. The `fciV2Storage()` function is imported but not called in V2, providing a latent hazard.
- Test coverage: No test verifies isolation between V1 and V2 storage; the slot identity is not checked.

**V1 hookData flag encoding (byte bitmask) vs V2 (bytes2 first two bytes):**
- Files: `src/types/HookDataFlagsMod.sol`, `src/fee-concentration-index-v2/types/FlagsRegistry.sol`
- Why fragile: V1 checks `hookData[0]` for bitmask flags (`REACTIVE_FLAG=0x01`, `V3_FLAG=0x02`). V2 reads the first two bytes as a `bytes2` protocol identifier (`UNISWAP_V3_REACTIVE=0x52FF`). The high byte of `0x52FF` is `0x52` which satisfies V1's `isUniswapV3` test (`0x52 & 0x02 != 0`) but not `isReactive` (`0x52 & 0x01 == 0`). As a result, V2 V3-reactive hookData would be misclassified by V1 dispatch functions as V3 (non-reactive). Any shared utility that reads V1 flags from V2 hookData will silently use the wrong storage branch.
- Safe modification: Never pass V2 hookData to V1 dispatch functions (`fciStorageFor`, `isUniswapV3Reactive`, `writeCacheTick`, `readCacheTick`). The V1 and V2 hook pipelines must remain strictly separate.
- Test coverage: The differential test `FCIV1DiffFCIV2.diff.t.sol` compares outputs but may not test cross-contamination of hookData between V1 and V2 dispatch paths.

**Transient storage slots for removal data use additive offsets from a base — slot overlap possible if base is unlucky:**
- Files: `src/fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol:36-44`
- Why fragile: `transientBase(flag)` returns `keccak256(abi.encode("thetaSwap.fci.transient", flag))`. Slots at `base+1`, `base+2`, `base+3` are used for `feeLast`, `posLiquidity`, `rangeFeeGrowth`. If two different protocol flags produce base values that differ by exactly 1, 2, or 3, one protocol's transient data would overwrite another's within the same transaction.
- Safe modification: The keccak256 address space makes accidental collision astronomically unlikely. However, adding a comment explaining the offset assumptions and listing all active flags helps maintainers reason about correctness.
- Test coverage: No explicit test for transient slot non-collision across two simultaneous protocol flags.

**Shadow liquidity uses `unchecked` subtraction — can silently underflow:**
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol:46-47`
- Why fragile: `setPositionShadow(chainId_, pool, posKey, posLiqBefore - liquidity)` is inside an `unchecked` block. If `posLiqBefore < liquidity` (due to a missed Mint event), the result wraps to a large `uint128` value and is stored as the shadow. The next burn for the same position will read an enormous `posLiqBefore`, causing `xk` to diverge.
- Safe modification: Remove `unchecked`, or add a guard: `if (posLiqBefore < liquidity) { setPositionShadow(chainId_, pool, posKey, 0); return ...; }`.
- Test coverage: Not tested for the missed-mint-then-burn scenario.

**`listen()` functions are `payable` but never consume `msg.value` — ETH is permanently locked:**
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:74`, `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol:71`, `src/fee-concentration-index-v2/FCIProtocolFacet.sol:23`
- Why fragile: Any ETH sent to `listen()` is accepted and silently trapped in the contract with no withdrawal path (no `receive()` or `migrateFunds` on the facets themselves). The `payable` modifier was likely inherited from a pattern where calling fees were expected.
- Safe modification: Remove `payable` unless fees are intentionally accepted and a withdrawal path exists. Alternatively add explicit `require(msg.value == 0)`.

**`OraclePayoffFacet` is documented as "removable Model B" — removal requires diamond cut, not guarded in code:**
- Files: `src/fci-token-vault/facets/OraclePayoffFacet.sol:29-30`, `src/fci-token-vault/interfaces/IOraclePayoff.sol:4-5`
- Why fragile: The transition from Model B (oracle redemption) to Model C (CFMM 50/50) requires removing `OraclePayoffFacet` from the diamond and deploying a CFMM facet. There is no on-chain migration guard or state migration function. If the facet is removed while tokens are still outstanding and un-redeemed, LONG token holders lose their redemption path permanently.
- Safe modification: Before any diamond cut removing `OraclePayoffFacet`, all LONG tokens must be redeemed. Add a migration function that verifies `erc6909TotalSupply(LONG) == 0` before allowing removal.
- Test coverage: `VaultLifecycleGuards.t.sol` tests some lifecycle paths, but Model B→C transition is not tested end-to-end.

---

## Scaling Limits

**`incrementOverlappingRanges` per-pool range list grows unboundedly:**
- Current capacity: No cap on `activeRangeCount()` per pool.
- Limit: At ~100 active tick ranges per pool, `afterSwap` / the reactive callback starts consuming significant gas. V4 native hooks have a 30M block gas limit; at ~500 ranges the loop approaches block gas limits.
- Scaling path: Either cap active ranges per pool (e.g., max 200), implement range pruning on full-exit, or replace the linear scan with a tick-indexed bitmap.

**Reactive Network gas budget capped at 1M per callback:**
- Current capacity: `CALLBACK_GAS_LIMIT = 1_000_000` (defined in both `UniswapV3Reactive.sol` and `ReactiveDispatchMod.sol`).
- Limit: At ~50 active ranges per pool, the callback gas may be insufficient. Prior operational experience (documented in MEMORY.md) showed 300K was too low; 1M was required for 4 staticcalls + cold SSTOREs.
- Scaling path: Increasing the gas limit increases the Reactive Network fee per callback. Consider splitting multi-range increment into batched callbacks.

---

## Dependencies at Risk

**`angstrom/src/types/CalldataReader` used in production routing:**
- Risk: `CalldataReaderLib` from the `angstrom` library is imported in `FeeConcentrationIndexRegistryStorageMod.sol` and `PoolKeyExtLib.sol` for hookData parsing. Angstrom is an external dependency with its own release cadence; it is not pinned to a specific commit in `foundry.toml` beyond a submodule ref.
- Impact: API changes to `CalldataReaderLib` would break protocol flag dispatch silently.
- Migration plan: If Angstrom API changes, the two import sites must be updated. Consider copying the three-line `readU16` / `readAddr` implementation inline to remove the dependency for such narrow usage.

**`foundational-hooks` for `SqrtPriceLibrary`:**
- Risk: `SqrtPriceLookbackPayoffX96Lib.sol` imports `SqrtPriceLibrary` from `foundational-hooks`. This library is not a standard dependency; if the submodule is removed or renamed, payoff calculations silently break.
- Impact: `oraclePoke()` and `lookbackPayoffX96()` in the vault would fail to compile.
- Migration plan: The two functions used (`fractionToSqrtPriceX96`, `divX96`, `Q96`) are simple enough to inline if the dependency becomes unavailable.

---

## Missing Critical Features

**No epoch initialization guard in `initializeEpochPool`:**
- Problem: `FeeConcentrationIndexV2.initializeEpochPool` sets `epochLength` and resets `currentEpochId` to `block.timestamp`. Calling it a second time on an already-running pool resets the epoch mid-cycle, discarding all accumulated terms in the current epoch.
- Blocks: Safe re-initialization after a deployment upgrade.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:338-344`

**`token1` fee growth completely ignored in FCI V2 accumulation:**
- Problem: `LiquidityPositionSnapshot.feeGrowthInside1LastX128` is always set to `0` in both `afterAddLiquidity` and `afterRemoveLiquidity`. FCI accumulation uses only `token0` fee growth as a proxy for total fee share. For pools where most volume is `token1 → token0`, the index underestimates JIT concentration.
- Blocks: Accurate FCI signal for non-USDC-denominated pools.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:89`, `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:257`

---

## Test Coverage Gaps

**V3 reactive integration test has placeholder TODOs — core flow is not end-to-end tested:**
- What's not tested: `test_addLiquidity` and `test_queryIndex` stubs exist as TODO comments; the full mint→swap→burn→check-index cycle is not covered in a single integration test.
- Files: `test/fee-concentration-index-v2/protocols/uniswap-v3/integration/FeeConcentrationIndexV2Full.integration.t.sol:152-153`
- Risk: Regressions in the V3 reactive callback path may not be caught before deployment.
- Priority: High

**Shadow position underflow (missed-mint-then-burn) has no test:**
- What's not tested: The scenario where ReactVM processes a Burn event for a position that was never Minted (or missed) is not covered.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol:44-49`
- Risk: Silent `uint128` wraparound produces an enormous `posLiqBefore` value, corrupting the FCI state permanently.
- Priority: High

**V1 / V2 storage slot collision is not tested:**
- What's not tested: No test deploys V1 `FeeConcentrationIndex` and V2 `FeeConcentrationIndexV2` in the same diamond and verifies their storage is isolated.
- Files: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol:28`, `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol:21`
- Risk: Co-deployment in a shared diamond would silently corrupt state with no error.
- Priority: High (pre-merge)

**`fetchPositionKey` implicit no-return for unknown protocol flags:**
- What's not tested: `fetchPositionKey` in `HookUtilsMod.sol` returns `bytes32` via two conditional branches (`isUniswapV4`, `isUniswapV3`). If neither flag matches, the function returns the default zero value with no revert. This path is not tested.
- Files: `src/libraries/HookUtilsMod.sol:14-34`
- Risk: A new protocol or malformed hookData silently produces `positionKey = 0x00`, causing all positions for different owners to collide at the same key.
- Priority: Medium

**`poolWhitelist` enforcement gap is not tested:**
- What's not tested: No test verifies that an unregistered pool address with a matching event signature (Swap/Mint/Burn) is ignored by the ReactVM `react()` function.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol:45-62`
- Risk: An attacker observing the subscription can emit events from a fake pool address with matching signatures, and the ReactVM would process them if it receives them via the Reactive Network.
- Priority: Medium

---

*Concerns audit: 2026-03-18*
