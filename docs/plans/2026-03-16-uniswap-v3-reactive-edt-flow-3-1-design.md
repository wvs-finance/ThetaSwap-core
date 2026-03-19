# Flow 3.1 Design: listen() -> PoolAdded -> EDT Bind -> V3 Event Dispatch -> Callback Arrival

**Date:** 2026-03-16
**Branch:** 008-uniswap-v3-reactive-integration
**Approach:** Layered Composition (B)
**Scope:** Flow-based — implements component pieces that complete a testable flow, not entire components.

## Goal

Implement the first testable reactive flow for Uniswap V3 integration using the new Event Dispatch Table (EDT) from reactive-hooks. 

The flow starts with `listen(poolRpt)` on the origin chain and ends with `MockCallbackReceiver` confirming data arrival on the destination chain.

## Flow Summary

```
Origin Chain                    Reactive Network                  Destination Chain
─────────────                   ────────────────                  ─────────────────
UniswapV3Facet.listen(poolRpt)
  │
  ├─ emit PoolAdded(facet, callback, poolId, flag, data)
  │       data = UniswapV3PoolAddedLib.encode(chainId, pool, protocolStateView)
  │
  │                              RN Instance
  │                              (cross-chain subscription to PoolAdded at deploy)
  │                                │
  │                              ReactVM receives PoolAdded via RN cross-chain subscription
  │                                │
  │                              ReactiveDispatchMod:
  │                                ├─ decode log.data via UniswapV3PoolAddedLib
  │                                │   → (chainId, pool, protocolStateView)
  │                                ├─ register 3 OriginEndpoints (Swap/Mint/Burn × pool)
  │                                ├─ register 1 CallbackEndpoint (unlockCallbackReactive)
  │                                ├─ create 3 Bindings via EDT (per pool)
  │                                └─ reactVMBatchSubscription(chainId, pool, v3PoolSigs())
  │
  │                              V3 pool event arrives (Swap/Mint/Burn)
  │                                │
  │                              ReactiveDispatchMod:
  │                                ├─ construct OriginEndpoint from log fields
  │                                │   → OriginEndpoint(uint32(log.chain_id), log._contract, bytes32(log.topic_0))
  │                                ├─ call originId() on the endpoint
  │                                ├─ dispatch(edt, originId) → activeCallbackIds
  │                                ├─ for each active callback:
  │                                │   ├─ look up CallbackEndpoint from registry
  │                                │   ├─ UniswapV3PayloadMutatorLib.mutate(log, reactVmStorage)
  │                                │   └─ emit Callback(chainId, target, gasLimit,
  │                                │        abi.encodeWithSelector(selector, enrichedPayload))
```

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where does EDT binding happen? | ReactVM | Reactive Network constraint: ReactVM calls reactVMBatchSubscription() for external chains |
| Who subscribes to PoolAdded? | RN constructor with fixed (chainId, facet) pairs | Simple, sufficient. Redeploy to add facets |
| PoolAdded data encoding | Generic `bytes data` field, protocol lib encodes/decodes | Keeps event protocol-agnostic; UniswapV3PoolAddedLib handles V3 specifics |
| PoolAdded event change | `bytes data` added to ALL PoolAdded events (FCIProtocolFacet, UniswapV3Facet, NativeUniswapV4Facet) | Unified topic0 across all protocols — single `POOL_ADDED_SIG` for RN subscription |
| Number of callback selectors | 1 — `unlockCallbackReactive(address,bytes)` | Single entry point; event type encoded in payload |
| protocolStateView for V3 | == pool address (V3 pool IS the state source) | V3 state is read from the pool contract directly |
| Destination chainId for CallbackEndpoint | Same as origin chainId | Callback target lives on same chain as V3 pool |
| Payload mutation | Open extension point per protocol via library | Pre-swap tick injection is one instance; future protocols define their own mutator |
| Funding model | listen() only emits PoolAdded; ReactVM handles EDT funding autonomously | Origin chain can't call EDT. ReactVM already manages ETH via fund()/receive()/debt |
| Event decoding | Happens in unlockCallbackReactive, NOT in ReactVM | ReactVM is a thin router; callback target does protocol-specific decoding |
| Flow completion criteria | MockCallbackReceiver confirms data arrived | Flow-based scope: testable end-to-end without full FCI implementation |

## Type Compatibility Note

`EventSignatures.sol` declares event sigs as `uint256`. `OriginEndpoint.eventSig` is `bytes32`. These are bit-identical but require explicit casts. `ReactiveDispatchMod` constructs `OriginEndpoint` with `bytes32(log.topic_0)`. When passing to `reactVMBatchSubscription` (which takes `uint256[] memory sigs`), cast back to `uint256`.

## Architecture: Layered Composition

### Layer 1 — EDT Primitives (from reactive-hooks, imported)

Already implemented in reactive-hooks at commit `01bbb3e`. Consumed as-is:

- **Types:** `OriginEndpoint`, `CallbackEndpoint`, `Binding`, `BindingState`
- **Storage:** `OriginRegistryStorageMod`, `CallbackRegistryStorageMod`, `EventDispatchStorageMod`
- **Logic:** `EventDispatchLib` (validateBind, immediateBind, scheduledBind, fundedBind, dispatch, quoteBind, activatePendingBindings, pauseBind, resumeBind, unbind)
- **Utilities:** `DoublyLinkedListLib`, `SelfSyncLib`
- **Auth:** Callback authentication types

### Layer 2 — Reactive Dispatch (protocol-agnostic, new)

`ReactiveDispatchMod.sol` — file-level free functions (SCOP style). Located at `src/fee-concentration-index-v2/modules/` because it is part of the FCI V2 system, not the old `reactive-integration/` architecture. It runs on the ReactVM instance.

**Self-sync handler responsibilities:**
1. Receive `PoolAdded` log (delivered via RN cross-chain subscription, NOT self-sync — the event originates on the origin chain, not on Reactive Network)
2. Extract `protocolFlag` from log topics
3. Route to protocol-specific lib for `log.data` decoding (e.g., `UniswapV3PoolAddedLib.decode(log.data)` → `(chainId, pool, protocolStateView)`)
4. Construct and register `OriginEndpoint`s for the protocol's event signatures — 3 per pool for V3 (Swap/Mint/Burn)
5. Register `CallbackEndpoint` (idempotent — same target for all pools of a protocol)
6. Create `Binding`s via EDT (`fundedBind` or `scheduledBind` based on balance) — 3 bindings per pool, each origin → the single callback
7. Subscribe to pool events via `reactVMBatchSubscription`

**Idempotency:** Duplicate `PoolAdded` logs (from event replay or re-org) are safe. EDT's `setOrigin`, `setCallback`, and `setBinding` are all idempotent (return existing ID if already registered). `reactVMBatchSubscription` re-subscribes, which wastes gas but does not corrupt state.

**Event dispatch responsibilities:**
1. Construct `OriginEndpoint` from incoming log: `OriginEndpoint(uint32(log.chain_id), log._contract, bytes32(log.topic_0))`
2. Compute `originId` via `originId()` on the endpoint
3. Call `dispatch(edt, originId)` to get active callback list
4. Look up `CallbackEndpoint` for each active callback
5. Delegate to protocol payload mutator for log enrichment
6. Emit `Callback(chainId, target, gasLimit, abi.encodeWithSelector(selector, enrichedPayload))`

### Layer 3 — V3 Protocol (V3-specific, new)

**UniswapV3PoolAddedLib.sol** — encode/decode the `bytes data` field of `PoolAdded`:
- `encode(uint256 chainId, address pool, address protocolStateView) returns (bytes memory)`
- `decode(bytes calldata data) returns (uint256 chainId, address pool, address protocolStateView)`

**UniswapV3PayloadMutatorLib.sol** — enriches raw V3 log data before callback emission:
- `mutate(IReactive.LogRecord calldata log, ReactVmStorage storage ctx) returns (bytes memory)`
- `ctx` is the existing `UniswapV3ReactVMStorageMod` storage (provides `getLastTick`/`setLastTick` for TickShadow)
- For Swap: injects pre-swap tick from TickShadow storage, updates TickShadow with post-swap tick
- For Mint/Burn: passes through (enrichment added later as needed)
- Open extension point: other protocols implement their own mutator with the same interface shape

## Modified Files

| File | Change |
|------|--------|
| `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol` | `PoolAdded` event adds `bytes data` field; `listen()` encodes V3 data via `UniswapV3PoolAddedLib` |
| `src/fee-concentration-index-v2/FCIProtocolFacet.sol` | `PoolAdded` event adds `bytes data` field (unified signature) |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol` | Add `POOL_ADDED_SIG` constant |

## New Files

| File | Layer | Purpose |
|------|-------|---------|
| `src/fee-concentration-index-v2/modules/ReactiveDispatchMod.sol` | 2 (agnostic) | ReactVM-side self-sync handler + EDT event dispatch |
| `src/fee-concentration-index-v2/libraries/PoolAddedSig.sol` | 2 (agnostic) | `POOL_ADDED_SIG` constant — shared across protocols, not in V3-specific EventSignatures |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol` | 3 (V3) | Encode/decode PoolAdded data for V3 |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol` | 3 (V3) | V3 log enrichment (pre-swap tick, etc.) |
| `test/fee-concentration-index-v2/protocols/uniswap-v3/mocks/MockCallbackReceiver.sol` | Test | Implements `unlockCallbackReactive`, stores + emits received data |
| `test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1_ListenDispatch.t.sol` | Test | End-to-end flow test |

## Submodule Update

reactive-hooks updated from `72721d2` to `01bbb3e` (origin/main) to pull in EDT:
- DoublyLinkedListLib
- OriginRegistryStorageMod, CallbackRegistryStorageMod, EventDispatchStorageMod
- EventDispatchLib
- OriginEndpoint, CallbackEndpoint, Binding types
- SelfSyncLib
- Callback auth types

## RN Instance Constructor (pseudo-code)

```
// NOTE: pseudo-code — actual Solidity will use a named struct for the facet list
struct WatchedFacet {
    uint256 chainId;
    address facet;
}

constructor(
    WatchedFacet[] memory watchedFacets,
    address service_
) payable
```

- Subscribes to `POOL_ADDED_SIG` from each facet on each chain (cross-chain subscription, not self-sync)
- Pre-funds SystemContract with remaining balance

## Test Strategy (Flow 3.1)

**MockCallbackReceiver:**
- Implements `unlockCallbackReactive(address rvmSender, bytes calldata data)`
- Stores last received `data` in public storage
- Emits `CallbackReceived(bytes data)` for assertion
- Counts total callbacks received

**Flow3_1_ListenDispatch.t.sol:**
1. Deploy UniswapV3Facet, MockCallbackReceiver
2. Call `listen(poolRpt)` — verify `PoolAdded` emitted with correct data
3. Simulate ReactVM: feed `PoolAdded` log to dispatch handler
4. Verify EDT state: 3 origins registered (per pool), 1 callback registered, 3 bindings active (per pool)
5. Simulate V3 Swap event: feed raw Swap log to dispatch handler
6. Verify: MockCallbackReceiver received enriched payload with correct data
7. Repeat for Mint and Burn events

**Flow is complete when:** MockCallbackReceiver confirms data arrived for all 3 event types.

## Dependencies

- reactive-hooks submodule at `01bbb3e` (EDT feature)
- Existing: `UniswapV3PoolKeyLib`, `fromUniswapV3PoolToPoolKey`
- Existing: `FCIFacetAdminStorageMod`, `addPool`, `UNISWAP_V3` flag
- Existing: `UniswapV3ReactVMStorageMod` (TickShadow storage for payload mutator)

## Out of Scope

- Full FCI state updates (swap -> incrementOverlappingRanges, mint -> registerPosition, burn -> deregisterPosition) — covered by future flows
- Multi-protocol dispatch (V4 reactive) — ReactiveDispatchMod is agnostic but only V3 lib exists for now
- Pause/resume/unbind EDT operations — EDT supports them, but flow 3.1 only tests the happy path
- Scheduled bind / auto-activate — flow 3.1 uses immediate bind (assumes ReactVM is pre-funded)
- Production callback target (FeeConcentrationIndexV2) — MockCallbackReceiver used instead
