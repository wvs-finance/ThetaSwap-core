# FCI HookFacet Adaptation Design

**Date**: 2026-03-06
**Branch**: `001-fee-concentration-index`
**Upstream issues**: #17, #18, #20, #24, #25, #26

## Problem

FeeConcentrationIndex currently inherits `BaseHook` (standalone V4 hook contract). It must become a HookFacet in the hook-bazaar MasterHook Diamond system, running via `delegatecall` in MasterHook's storage context.

## Architecture

### Call Flow

```
PoolManager ──call──> MasterHook.afterSwap()
  MasterHook.fallback() ──delegatecall──> FCI facet
    FCI facet ──call──> PoolManager (StateLibrary reads via extsload)
```

PoolManager inherits `NoDelegateCall` but this is not an issue: FCI makes regular external calls to PoolManager, never delegatecalls into it.

### Storage

- **FCI state**: `keccak256("hook-bazaar.fci")` — unique namespace for all FCI mappings (accumulatedHHI, registries, feeGrowthBaseline0)
- **poolManager**: read from MasterHook's existing `keccak256("hook-bazar.hooks")` slot (single source of truth, no duplication)
- **Transient storage**: unchanged (TSTORE/TLOAD slots are transaction-scoped, unaffected by delegatecall)

### Contract Shape

```solidity
contract FeeConcentrationIndex is IERC165, IHookFacet {
    // No BaseHook, no constructor args, no immutables
    // poolManager read from MasterHook storage via delegatecall context

    // External IHooks-matching signatures
    function afterAddLiquidity(...) external returns (bytes4, BalanceDelta) { ... }
    function beforeSwap(...) external returns (bytes4, BeforeSwapDelta, uint24) { ... }
    function afterSwap(...) external returns (bytes4, int128) { ... }
    function beforeRemoveLiquidity(...) external returns (bytes4) { ... }
    function afterRemoveLiquidity(...) external returns (bytes4, BalanceDelta) { ... }
    function getIndex(PoolKey calldata) external view returns (uint128, uint256, uint256) { ... }

    function supportsInterface(bytes4 interfaceID) external view returns (bool) { ... }
}
```

### Registration

```solidity
// Deploy FCI facet
FeeConcentrationIndex fci = new FeeConcentrationIndex();

// Register in MasterHook — hook selectors auto-detected + getIndex as additional
bytes4[] memory additional = new bytes4[](1);
additional[0] = FeeConcentrationIndex.getIndex.selector;
masterHook.addHook(address(fci), additional);
```

### Constraints

- SCOP: no `is` in production except interfaces (`IERC165`, `IHookFacet`)
- No `library`, no `modifier`, no `public` functions
- Storage namespace must be disjoint from MasterHook, DiamondCut, AccessControl slots
- Hook function signatures must match IHooks exactly
