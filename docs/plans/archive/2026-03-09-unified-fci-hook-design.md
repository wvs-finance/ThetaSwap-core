# Unified FCI Hook — Eliminating ReactiveHookAdapter

## Goal

Merge V3 reactive callback handling into the FeeConcentrationIndex hook contract, eliminating the standalone ReactiveHookAdapter. One contract, one IHooks interface, composable hookData flags dispatch V3/V4/reactive behavior.

## Architecture

The `FeeConcentrationIndex` contract becomes the single entry point for both V4 (PoolManager) and V3 (reactive callbacks). The `ReactiveHookAdapter` is eliminated. `ThetaSwapReactive` emits callbacks targeting the FCI hook directly, encoding V3 event data as IHooks calldata with flagged hookData.

### HookData Flag System (Composable Bitmask)

```
uint8 constant REACTIVE_FLAG = 0x01;  // callback from Reactive Network
uint8 constant V3_FLAG       = 0x02;  // Uniswap V3 source
uint8 constant V4_FLAG       = 0x04;  // Uniswap V4 source

// hookData layout when flags present:
// [flags: uint8] [protocol-specific data...]
//
// Composable combos:
//   REACTIVE | V3  (0x03) = reactive callback from V3 pool (current use case)
//   REACTIVE | V4  (0x05) = future: cross-chain V4 monitoring
//   V4 only  (0x04) = future: V4 with explicit hookData
//   empty hookData  = V4 native path (no flags, backward compatible)
```

### Event → IHooks Mapping

| V3 Event | IHooks Function | hookData contents |
|----------|----------------|-------------------|
| Mint | `afterAddLiquidity` | `flags(REACTIVE\|V3) + owner + tickLower + tickUpper + liquidity` |
| Swap | `afterSwap` | `flags(REACTIVE\|V3) + tickBefore + tickAfter` |
| Burn | `afterRemoveLiquidity` | `flags(REACTIVE\|V3) + owner + tickLower + tickUpper + liquidity` |

### Dispatch Logic (inside each IHooks function)

```
if hookData is empty:
    → V4 native path (unchanged)
else:
    read flags (first uint8 via CalldataReader)
    if flags & REACTIVE:
        → verify msg.sender == callbackProxy, rvmSender == rvmId
    if flags & V3:
        → use reactiveFciStorage()
        → decode V3-specific fields from remaining hookData
        → position key = keccak256(owner, tickLower, tickUpper)
        → x_k = liquidity ratio (fromFeeGrowth)
        → skip transient storage (tick/fee data arrives in hookData)
    if flags & V4:
        → use fciStorage() (or reactiveFciStorage() if also REACTIVE)
        → position key = Position.calculatePositionKey(sender, tL, tU, salt)
        → x_k = fee growth delta (fromFeeGrowthDelta)
```

### beforeSwap / beforeRemoveLiquidity

Only needed for V4 native path (transient storage caching). When hookData has REACTIVE flag, these are either:
- Not called at all (ReactVM only emits afterSwap/afterAddLiquidity/afterRemoveLiquidity callbacks)
- No-ops if called (check flags, early return)

### FCI Hook Additions

The FeeConcentrationIndex contract gains:
- `authorizedCallers` mapping (callback proxy addresses)
- `rvmId` (deployer EOA, mutable with owner setter)
- `pay(uint256)` (IPayer for callback gas)
- `receive() external payable` (ETH funding)
- `payable` constructor

### ReactLogicMod.sol Changes

Callback target changes from `adapter` to `fciHook`. Callback payload changes from custom signatures to IHooks signatures:

```
// Before:
emit Callback(chainId, adapter, gas, abi.encodeWithSignature("onV3Swap(address,(address,int24,int24))", ...))

// After:
emit Callback(chainId, fciHook, gas, abi.encodeWithSignature("afterSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),int256,bytes)", rvmSender, poolKey, swapParams, balanceDelta, hookData))
```

Where hookData = `abi.encodePacked(uint8(REACTIVE | V3), tickBefore, tickAfter)`

### Position Key Unification (fetchPositionKey)

```solidity
function fetchPositionKey(
    uint8 flags,
    address sender,
    ModifyLiquidityParams calldata params
) pure returns (bytes32) {
    if (flags & V3_FLAG != 0) {
        return keccak256(abi.encodePacked(sender, params.tickLower, params.tickUpper));
    }
    return Position.calculatePositionKey(sender, params.tickLower, params.tickUpper, params.salt);
}
```

## Component Breakdown (incremental, one at a time)

1. **Flag constants + hookData codec** — pure functions, no contract changes
2. **FCI hook: callback auth + IPayer** — additive, no existing logic touched
3. **FCI afterSwap: V3 reactive path** — one function branch added
4. **FCI afterAddLiquidity: V3 reactive path** — one function branch added
5. **FCI afterRemoveLiquidity: V3 reactive path** — one function branch added
6. **ReactLogicMod: retarget callbacks** — change payload encoding + target
7. **fetchPositionKey: unified V3/V4** — uncomment + wire pseudo code

## Testing

- Unit tests: flag encoding/decoding roundtrip
- Unit tests: each IHooks function with REACTIVE|V3 hookData (mock calldata)
- Fork test: deploy unified FCI hook, run buildMildV3(), verify deltaPlus > 0
- Regression: existing V4 path unaffected (empty hookData)

## Files Affected

- `src/fee-concentration-index/FeeConcentrationIndex.sol` — main changes
- `src/libraries/HookUtilsMod.sol` — fetchPositionKey (uncomment pseudo code)
- `src/reactive-integration/modules/ReactLogicMod.sol` — retarget callbacks
- `src/reactive-integration/ThetaSwapReactive.sol` — adapter → fciHook
- New: flag constants + codec module (e.g., `src/fee-concentration-index/types/HookDataFlagsMod.sol`)
- Deprecated: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol` (commented out, not deleted)
