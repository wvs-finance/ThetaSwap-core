# Codebase Concerns

**Analysis Date:** 2026-03-17

## Tech Debt

**Reactive Callback Gas Limit Fragility:**
- Issue: Initial callback gas limit set to 300K insufficient for V3 reactive integration. Adapter performs 4 staticcalls + cold SSTOREs, causing out-of-gas failures.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`, `src/reactive-integration/uniswapV3/modules/UniswapV3ReactiveMod.sol`
- Impact: Callbacks fail silently. Proxy catches OOG and still calls pay(), masking the root cause. Callback success cannot be verified from pay() alone.
- Fix approach: Increase callback gas limit to 1M. Implement explicit callback success signal in callback proxy. Add integration tests that verify callback completion before proceeding.

**Storage Read-After-Delete Pattern:**
- Issue: Reading storage references after clearing them. Must copy storage refs to memory BEFORE clearing state.
- Files: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol:65` (deleteFeeGrowthBaseline), `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol:107`
- Impact: Data loss, incorrect state calculations, position tracking failures in removePositionInRange flow.
- Fix approach: Move storage deletion to end of function. Copy all required state to local variables first.

**Branch Synchronization Drift Risk:**
- Issue: Research state and .gitignore MUST be identical across branches 001/002/003. Current diff shows 269 lines variance between branches.
- Files: `research/` directory, `.gitignore`
- Impact: Inconsistent test fixtures, shared oracle data divergence, failed test reproduction across branches. Blocks PR merges to main.
- Fix approach: Implement CI check that fails if `git diff origin/001-* origin/002-* -- research/` returns non-zero. Cherry-pick research changes atomically to all feature branches before merging.

**Vault Redemption Model B→C Transition Pending:**
- Issue: Vault currently uses FCI oracle for redemption split (model B). Must transition to fixed 50/50 mint/burn (model C) when CFMM ships (branch 002).
- Files: `src/fci-token-vault/facets/OraclePayoffFacet.sol:113`, `src/fci-token-vault/modules/OraclePayoffMod.sol`
- Impact: Vault semantics block CFMM integration. Oracle payoff coupling prevents clean CFMM deployment. Blocks branch 002 merge.
- Fix approach: Create upstream GitHub issue tracking B→C transition. When 002 ships, strip poke/settle/payoff math from vault and make it pure mint/burn machine. Move P² payoff logic entirely to CFMM pool. Plan for coordinated deployment.

**Large Contract Complexity (6+ files exceeding 200 LOC):**
- Issue: Six Solidity contracts exceed 200 lines. FeeConcentrationIndexV2.sol (363), UniswapV3Facet.sol (300), NativeUniswapV4Facet.sol (283) are large monoliths.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`, `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol`, `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol`, `src/fee-concentration-index/FeeConcentrationIndex.sol`, `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol`
- Impact: High cognitive load for code review, increased surface area for bugs, delegatecall fan-out (FeeConcentrationIndexV2 makes 5+ delegatecalls per function), testing complexity.
- Fix approach: Split facets into smaller modules (e.g., swap logic separate from position management). Extract shared validation into libraries. Reduce delegatecall depth by consolidating V3/V4 behavior divergence.

## Known Bugs

**Zero-Burn Handling in V3 Reactive Path:**
- Symptoms: V3 burnPosition() performs two phases: zero-burn (liq=0, fee collection only), then full-burn (liq=0 → remove). Without skip, adapter deregisters twice.
- Files: `src/reactive-integration/uniswapV3/modules/UniswapV3ReactiveMod.sol:190-197`, `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`
- Trigger: Call v3Pool.decreasePosition() with any liquidity amount. V3 emits two BURN events.
- Workaround: Skip zero-liquidity burns in _handleBurn by checking `if (data.liquidity == 0) return`. Already implemented but fragile — relies on event log ordering.

**Transient Storage Assumption in BeforeRemoveLiquidity:**
- Symptoms: beforeRemoveLiquidity and afterRemoveLiquidity rely on transient storage to share state within same transaction. If callback is delayed (e.g., async), transient storage clears.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:207-215` (tstoreRemovalData/tloadRemovalData)
- Trigger: Not currently an issue for Uniswap V4 hooks (same-tx guarantee). Breaks if ported to cross-chain scenarios.
- Workaround: Use persistent storage (diamond storage slot) for removal state if cross-chain support added. Document transaction atomicity requirement in NatDoc.

**Callback Proxy Success Ambiguity:**
- Symptoms: Callback proxy catches out-of-gas and reverts from callback, BUT still calls pay(). If pay() succeeds, caller cannot distinguish between successful callback and failed callback + successful pay.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol:78-100` (unlockCallback)
- Trigger: Callback runs out of gas during 4 staticcalls or cold SSTOREs. Proxy emits CallbackFailure log but returns success to PoolManager.
- Workaround: Always use `cast run <tx_hash>` to inspect logs for CallbackFailure event. Use Sepolia testnet deployment for end-to-end verification before mainnet. Monitor callback gas via forge gas reports.

**Stale Submodule References:**
- Symptoms: Recent commits removed stale submodule refs (lib/reactive-lib, lib/typed-uniswap-v4, lib/reactive-hooks). Old branches still point to broken refs.
- Files: `.gitmodules`, recent commits 9b95d5e, c119ad9
- Trigger: Checkout old branches or CI runs against stale history. Git submodule init fails.
- Workaround: Do not checkout branches before c119ad9. Use `git submodule update --init --recursive` to reset. Deprecate old branches.

## Security Considerations

**Delegatecall Attack Surface in Diamond Storage Pattern:**
- Risk: FeeConcentrationIndexV2 makes 5+ delegatecalls per hook function to facets (UniswapV3Facet, NativeUniswapV4Facet). Facets access shared diamond storage (fciV2Storage, fciFacetAdminStorage). If facet contract is compromised or contains logic bugs, delegatecall can corrupt shared state.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:58-250` (delegateCallContract calls), `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol` (shared storage), `lib/solady/src/utils/LibCall.sol` (delegateCallContract)
- Current mitigation: Facets are immutable once deployed. Access control via onlyDelegateCall modifier. Factory-controlled initialization.
- Recommendations: Add facet upgrade governance (timelock before facet swap). Implement delegatecall guard in LibCall to prevent re-entrancy during cascading calls. Audit delegatecall entry points for storage layout misalignment. Consider reading-only facets for metrics (FCIMetricsFacet) to reduce write surface.

**Reactive Network Callback Authentication:**
- Risk: UniswapV3Callback and ReactiveHookAdapter authenticate callbacks via authorizedCallers mapping + rvmId check. If callback proxy address is compromised, attacker can emit arbitrary hooks to FCI.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol:81-82` (authorizedCallers + rvmId validation), `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol:62-63`
- Current mitigation: Owner-controlled authorizedCallers. rvmId hardcoded at deployment. setAuthorized() restricted to owner.
- Recommendations: Add timelock for setAuthorized changes. Log all callback proxy updates. Monitor for suspicious hook emissions. Use multisig for callback proxy ownership transfer. Implement rate limiting on callback frequency per pool.

**Pool State Mutability in V3 Fee Growth Reads:**
- Risk: UniswapV3Facet reads V3 pool state (positions, ticks, feeGrowthGlobal) without staleness guarantees. If pool is frontrun after FCI position snapshot, fee calculations diverge.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:102-137` (latestPositionFeeGrowthInside, poolRangeFeeGrowthInside)
- Current mitigation: V1 approach: x_k = posLiq / totalRangeLiq bypasses fee snapshots, using only liquidity ratio (exact for V3). Callback carries posLiqBefore from ReactVM shadow, not live state.
- Recommendations: Document assumption that callbacks carry historical snapshots, not live state. Add validation that decoded posLiqBefore ≤ current pool liquidity. Consider oracle timestamp validation for cross-chain scenarios.

**Storage Slot Collision in Diamond Pattern:**
- Risk: 18 modules define storage accessors using keccak256(abi.encode(storageId)). If two modules accidentally use same storageId, storage reads return wrong state.
- Files: `src/fee-concentration-index-v2/modules/` (18 *Mod.sol files), `src/fee-concentration-index/modules/` (storage pattern)
- Current mitigation: Naming convention (e.g., fciV2Storage, fciFacetAdminStorage, protocolFciStorage). Slot calculation is deterministic.
- Recommendations: Add storage layout verification test in foundry that checks all storageIds are unique. Use enum instead of magic bytes2 flags to reduce slot collision risk. Create storage registry contract that blocks duplicate registration.

## Performance Bottlenecks

**Delegatecall Fan-Out in Hook Orchestration:**
- Problem: Each hook function (afterAddLiquidity, beforeRemoveLiquidity, afterRemoveLiquidity) makes 5-10 delegatecalls to facet. Total per transaction: 50+ delegatecalls for multi-position removal.
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:58-250` (nested delegatecall chains)
- Cause: Protocol-agnostic orchestrator in FeeConcentrationIndexV2 dispatches to protocol-specific facets. Each step (positionKey, latestFeeGrowth, addPositionInRange, etc.) is separate delegatecall.
- Improvement path: Batch delegatecalls into single call per hook phase. Return multi-value struct from facet instead of chaining. Use calldata encoding for batch operations. Measure gas savings before/after via forge gas reports.

**Registry Loop for Overlapping Range Count:**
- Problem: afterSwap increments overlappingRanges counter for every range that overlaps swap tick range. Large pools with 100+ ranges execute 100+ writes.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:219-229` (incrementOverlappingRanges loop)
- Cause: Linear iteration over activeRangeCount, no index or bit-tree. Swap cost scales with range density.
- Improvement path: Use TickBitmap (already imported from v4-core) to batch range lookups. Implement interval tree or segment tree for O(log n) range query. Test gas scaling with 1000-range pool benchmark.

**FCI State Accumulation Per Position:**
- Problem: Each position removal accumulates FCI term (blockLifetime, xSquaredQ128) into pool state. Large pool with frequent rebalancing does 100+ SSTOREs to fciState[poolId].
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:240-250` (addStateTerm, addEpochTerm)
- Cause: State is cumulative; no batching or compression. Epoch tracking adds secondary write.
- Improvement path: Defer state accumulation to epoch boundary (batch N positions per epoch). Use sparse merkle tree to compress FCI state. Implement state snapshot + delta design to reduce write frequency.

## Fragile Areas

**V3 Position Key Derivation in Reactive Path:**
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:96-98` (positionKey)
- Why fragile: V3 position key = keccak256(owner, tickLower, tickUpper). Callback must decode owner from V3 event log. If log decoding is off-by-one in topic/data parsing, wrong position is deregistered.
- Safe modification: All log decoding logic lives in `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/V3HookDataLib.sol` and `UniswapV3PayloadMutatorLib.sol`. Never modify positionKey derivation without updating both. Add differential test comparing V3Facet positionKey against raw V3 pool.positions() result.
- Test coverage: `test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1_ListenDispatch.t.sol` covers end-to-end flow. Unit tests missing for positionKey in isolation.

**Transient Storage Usage in V3 V4 Hybrid:**
- Files: `src/fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol` (tstore/tload), `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:207-215`
- Why fragile: beforeRemoveLiquidity tstore, afterRemoveLiquidity tload. If hooks are called out-of-order or in different transactions, transient storage is stale. V4 guarantees same-tx, but only because hooks are called by PoolManager. If ported to external callers, breaks.
- Safe modification: Add onlyDelegateCall guard to beforeRemoveLiquidity to enforce call order. Document: "transient storage assumes hooks called sequentially in same transaction by PoolManager." Never use transient storage for state that survives beyond tx boundary.
- Test coverage: Positive test exists (happy path). Missing: test that tload returns zero if beforeRemoveLiquidity not called, test that tstoreRemovalData survives intermediate calls.

**Fee Growth Baseline Deletion Race:**
- Files: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol:240-250` (afterRemoveLiquidity → deleteFeeGrowthBaseline), `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol:65`
- Why fragile: Position is deleted from registry, then feeGrowthBaseline is deleted. If an event fires between deletion and baseline deletion, state mismatch occurs. Baseline query could fail.
- Safe modification: Delete baseline BEFORE deregistering position. Verify baseline is cleared by reading it back with expect(read == 0). Add test case: remove position, then call getRegistryPositionBaseline and verify revert.
- Test coverage: AfterRemoveLiquidity.t.sol tests position removal but not baseline cleanup verification. Missing edge case: double-removal attempt after baseline deleted.

**Reactive Module Event Handling for V3 Burn:**
- Files: `src/reactive-integration/uniswapV3/modules/UniswapV3ReactiveMod.sol:188-198`, `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol:94-96`
- Why fragile: V3Burn event can fire twice per position (zero-burn + full-burn). Code skips zero-burns by checking `if (data.liquidity == 0) return`. But this assumes event log ordering is stable. If Reactive Network reorders logs, duplicate deregistration can occur.
- Safe modification: Use posKey as idempotency key. Check if position already deregistered before removing again. Store "removed" flag in diamond storage. Add assertion: removedPosCount >= 0 and removedPosCount <= totalPosCount.
- Test coverage: FeeConcentrationIndexV4ReactiveV3.diff.t.sol covers differential testing. Missing: explicit zero-burn scenario test, log reordering stress test.

**HookData Encoding Length Assumptions:**
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:110` (if (hookData.length >= 39))
- Why fragile: hookData carries posLiqBefore override at offset 39. Hardcoded magic number. If payload mutator changes encoding, offset breaks silently.
- Safe modification: Define const POS_LIQ_BEFORE_OFFSET = 39 in V3HookDataLib. Add length validation before decode. Create decoderSafe function that returns Option type (success/failure). Never assume hookData layout.
- Test coverage: Unit test for decodePosLiqBefore exists. Missing: test that decode fails gracefully if hookData.length < 39, test encode→decode roundtrip.

## Test Coverage Gaps

**Untested V3 Reactive Callback Failure Paths:**
- What's not tested: Callback gas out-of-gas handling, callback revert handling, callback proxy OOG with pay() success scenario.
- Files: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`, `test/reactive-integration/fork/FeeConcentrationIndexFull.fork.t.sol`
- Risk: Callback failures silently masked by pay() success. Deployments can get stuck with partial state updates.
- Priority: High. Add explicit test: call onV3Burn with minimal gas, verify CallbackFailure event emitted, verify pay() was still called, verify FCI state unchanged.

**Missing Cross-Pool FCI State Consistency Tests:**
- What's not tested: Multiple pools with overlapping ranges, FCI state accumulation across pools, registry deduplication.
- Files: `test/fee-concentration-index-v2/` (22 tests, none multi-pool)
- Risk: Pool isolation assumptions broken. Epoch state could leak across pools.
- Priority: High. Create integration test with 3 pools, mint overlapping ranges across pools, verify each pool's FCI state is independent.

**Untested Storage Layout Collision Scenarios:**
- What's not tested: Storage slot collision between diamond modules, migration of state between facet versions, storage layout compatibility after upgrade.
- Files: `src/fee-concentration-index-v2/modules/` (18 modules with storage accessors)
- Risk: Silent state corruption during facet upgrades. Undetected storage collisions.
- Priority: Medium. Create storage layout test that hashes all storageIds, verifies uniqueness, and logs layout diagram for code review.

**Python Econometrics Test Coverage Incomplete:**
- What's not tested: Hazard rate model with live V3 event stream, duration analysis with async callbacks, oracle fallback behavior.
- Files: `research/tests/` (22 Python tests), `research/econometrics/` (13 modules)
- Risk: Research assumptions diverge from contract behavior. Backtest results not reproducible in production.
- Priority: Medium. Add Python tests that mock Reactive callbacks with real V3 event logs. Add replay scenario: record events from Sepolia, feed to econometrics, verify FCI output matches live deployment.

## Scaling Limits

**Single PoolId Registry Size:**
- Current capacity: Tested with 10 ranges per pool. No known limits.
- Limit: Registry uses activeRangeAt(i) iteration for overlap counting. 100+ ranges = 100+ SLOAD ops per swap. 1000+ ranges likely hits block gas limit on afterSwap.
- Scaling path: Implement TickBitmap-based range index (O(1) lookup). Use batch swap events to accumulate overlaps across multiple transactions. Compress registry via merkle tree. Test with simulation: generate 1000-range pool, measure afterSwap gas.

**FCI State Accumulation Over Time:**
- Current capacity: Tested with 50 epochs per pool. Each epoch adds ~4 slots (currentEpochId, fciState, etc.).
- Limit: Epoch state grows linearly: storage cost = O(epochs * pools). After 1000 epochs, epoch storage ~10KB per pool.
- Scaling path: Implement state pruning: archive epochs older than 90 days. Use sparse storage only for active epochs. Compress old epoch snapshots to single hash. Add admin function to prune epochs.

**Reactive Network Callback Volume:**
- Current capacity: No rate limiting. Callback gas budget is per-call. Tested with <5 callbacks/block.
- Limit: Reactive Network can fire 100+ callbacks/block on mainnet V3. If all target FCI, callback queue backs up.
- Scaling path: Batch callbacks per block. Implement callback coalescing in callback proxy (merge overlapping swaps). Add priority queue for high-value positions. Test throughput: simulate 100 callbacks/block against Sepolia deployment.

## Dependencies at Risk

**Uniswap V3 Core Dependency (lib/v3-core):**
- Risk: V3 contract deployed on mainnet (immutable). If V3 pool interface changes (which it won't), integration breaks. Submodule pinning relies on git history.
- Impact: V3Facet.latestPositionFeeGrowthInside() calls IUniswapV3Pool(pool).positions(posKey). If pool interface diverges, contract fails to compile.
- Migration plan: V3 is immutable upstream, so this is very low risk. If V3 fork or chain fork introduces V3 variant, create V3VariantFacet. Document V3 version in CLAUDE.md. Use version guards in remappings.

**Reactive Network Dependency (lib/reactive-lib, lib/reactive-hooks):**
- Risk: Reactive Network is in beta. Callback interface can change. Recent commits removed stale submodule refs (commits 9b95d5e, c119ad9).
- Impact: Callback authentication (authorizedCallers + rvmId) assumes Reactive Network call flow. If Reactive changes rvmId injection or callback proxy, authentication breaks.
- Migration plan: Abstract ReactiveNetwork interface into IReactiveNetwork. Create mock for local testing. Version Reactive dependency explicitly in foundry.toml. Add integration tests that verify callback flow end-to-end on Reactive testnet before mainnet deploy.

**MasterHook Diamond (lib/hook-bazaar):**
- Risk: Hook-Bazaar is external monorepo. Diamond storage pattern may evolve. Current version uses facet registry + delegatecall.
- Impact: FCI uses hook-bazaar's Compose extensions. If Compose storage layout changes, FCI storage accessors may collide.
- Migration plan: Pin hook-bazaar version explicitly. Create storage collision test. If Compose changes, fork and maintain own Compose version. Document Compose version in CLAUDE.md.

**Typed UniswapV4 (lib/typed-uniswap-v4):**
- Risk: Typed wrappers (TickRange, FeeShareRatio, SwapCount) may have performance implications. Recent submodule removal suggests transition away from this library.
- Impact: FCI uses typed wrappers throughout (src/fee-concentration-index-v2/types/). If typed library is abandoned, no bug fixes for performance issues.
- Migration plan: Audit Typed library usage. If critical, copy type definitions into src/types/ and maintain locally. Replace typed FeeShareRatio with raw uint256 if performance needed.

## Missing Critical Features

**Feature Gap: Callback Success Verification:**
- Problem: No explicit signal that callback succeeded. pay() succeeding does NOT mean callback completed.
- Blocks: End-to-end verification on live deployments. Deployment validation scripts cannot confirm FCI state was updated.
- Approach: Modify Reactive Network callback proxy to return success bool. Or: emit CallbackSuccess event in UniswapV3Callback after FCI call completes. Consume event in deployment script to verify.

**Feature Gap: Facet Version Tracking:**
- Problem: No version numbers on deployed facets. When facet is upgraded, cannot distinguish old from new.
- Blocks: Multi-facet migration scenarios. Cannot safely degrade gracefully if new facet is broken.
- Approach: Add version() function to each facet. Store facet version in diamond admin storage. Version facet before each deployment. Add version check in FCI.delegateCall.

**Feature Gap: State Pruning / Cleanup:**
- Problem: No mechanism to delete old epoch state, deregister inactive positions, or archive inactive pools.
- Blocks: Long-term scaling. Storage cost grows unbounded.
- Approach: Add admin function to prune epochs older than X blocks. Add position garbage collection: remove positions not touched in 1000 blocks. Add pool deregistration.

---

*Concerns audit: 2026-03-17*
