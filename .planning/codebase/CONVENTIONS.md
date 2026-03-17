# Coding Conventions

**Analysis Date:** 2026-03-17

## Naming Patterns

**Files:**
- Contracts: `PascalCase.sol` (e.g., `FeeConcentrationIndexV2.sol`, `UniswapV3Facet.sol`)
- Modules (functions): `PascalCaseWithMod.sol` suffix (e.g., `FeeConcentrationIndexRegistryStorageMod.sol`)
- Libraries: `PascalCaseLib.sol` suffix (e.g., `UniswapV3PoolKeyLib.sol`)
- Tests: `PascalCase.t.sol` suffix with test type indicator (e.g., `DifferentialFCI.fork.t.sol`, `FeeConcentrationIndexV2Full.integration.t.sol`)
- Python modules: `snake_case.py` (e.g., `fci_oracle.py`, `mechanism_sweep.py`)

**Functions (Solidity):**
- External/public: camelCase (e.g., `afterAddLiquidity()`, `getDeltaPlus()`)
- Free functions (module-level): camelCase (e.g., `fciRegistryStorage()`, `getProtocolFlagFromHookData()`)
- Internal: camelCase with leading underscore for private helpers (e.g., `_setFci()`, `_setProtocolStateView()`)
- Modifiers: camelCase (e.g., `onlyDelegateCall()`)
- Event handlers: afterXxx, beforeXxx (e.g., `afterAddLiquidity()`, `beforeSwap()`)

**Functions (Python):**
- Module-level functions: snake_case (e.g., `delta_to_price()`, `run_exit_payoff_backtest()`)
- Private helpers: leading underscore (e.g., `_make_state()`)
- Test functions: `test_` prefix (e.g., `test_delta_to_price()`)

**Variables:**
- State variables (Solidity): camelCase (e.g., `liquidity`, `feeGrowthInside0LastX128`)
- Constants (Solidity): UPPER_SNAKE_CASE (e.g., `TICK_LOWER`, `TICK_UPPER`, `DEADLINE`)
- Immutable storage slots: camelCase with `_` prefix where immutable (e.g., `_self`)
- Loop counters: short names acceptable (e.g., `i`, `idx`)
- Storage structs: PascalCase (e.g., `FeeConcentrationIndexRegistryStorage`, `DailyPoolState`)

**Types:**
- Solidity structs: PascalCase (e.g., `LiquidityPositionSnapshot`, `RangeSnapshot`, `ExitPayoffResult`)
- Solidity interfaces: `IPascalCase` prefix (e.g., `IFCIProtocolFacet`, `IFeeConcentrationIndex`)
- Errors: PascalCase with no prefix (e.g., `PoolAlreadyRegistered`, `ZeroAddress`)
- Events: PascalCase (e.g., `FCITermAccumulated`, `PoolAdded`)
- Type aliases/wrappers: PascalCase (e.g., `PoolId`, `Currency`)

**Flags & Enums:**
- Protocol flags: UPPER_SNAKE_CASE (e.g., `UNISWAP_V3_REACTIVE`, `NATIVE_V4`)
- Bytes constants: camelCase (e.g., `FCI_REGISTRY_SLOT`)
- Hex constants: camelCase (e.g., `CALLBACK_PROXY`)

## Code Style

**Formatting:**
- Solidity compiler version: ^0.8.26 via IR (`via_ir = true`)
- EOL: LF
- Indentation: 4 spaces
- Line length: Soft limit ~88 chars; hard break at contract/function definitions

**Linting:**
- Solidity compiler warnings enabled; no `warning:` directives ignored
- No unchecked blocks unless explicitly justified with comment
- Assembly blocks marked with `"memory-safe"` when applicable

**Module Pattern (Functions-as-Modules):**
- NO `library` keyword per project guidelines
- Free functions at file scope, storage structs defined at file-level
- Storage access via `function() pure returns (StorageType storage $)` pattern:
  ```solidity
  bytes32 constant FCI_REGISTRY_SLOT = keccak256("thetaSwap.fci.registry");

  function fciRegistryStorage() pure returns (FeeConcentrationIndexRegistryStorage storage $) {
      bytes32 slot = FCI_REGISTRY_SLOT;
      assembly ("memory-safe") { $.slot := slot }
  }
  ```
- Functions that operate on storage use delegation pattern (see delegatecall sections)

**Contracts:**
- NO `is` inheritance in production contracts (SCOP: Solidity standards as option)
- Immutable references to self for guard checks (e.g., `address immutable _self`)
- Delegation via `LibCall.delegateCallContract()` for protocol adapters
- Modifiers for auth checks (e.g., `onlyDelegateCall()`, `requireOwner()`)

## Import Organization

**Order:**
1. Pragma statement
2. Third-party framework imports (`v4-core/`, `forge-std/`)
3. Protocol-specific imports (`@uniswap/`, `reactive-lib/`)
4. Project libraries and utilities (`@types/`, `@libraries/`, `@utils/`)
5. Project-specific types and modules (`@fee-concentration-index/`, `@fee-concentration-index-v2/`)
6. Relative imports within same feature (`./libraries/`, `./interfaces/`)

**Path Aliases:**
- `v4-core/=lib/uniswap-hooks/lib/v4-core/src/` — V4 core
- `@uniswap/v3-core/=lib/v3-core/` — V3 interfaces
- `@fee-concentration-index/=src/fee-concentration-index/` — FCI v1
- `@fee-concentration-index-v2/=src/fee-concentration-index-v2/` — FCI v2
- `@types/=src/types/` — Shared type extensions
- `@libraries/=src/libraries/` — Utility libraries
- `@utils/=src/utils/` — Utility functions
- `solady/=lib/solady/src/` — Solady (FixedPointMathLib, LibCall)
- `permit2/=lib/v4-periphery/lib/permit2/` — Permit2

**Example:**
```solidity
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {LibCall} from "solady/utils/LibCall.sol";
```

## Error Handling

**Pattern — Custom Errors:**
- Always use custom errors, never strings with `require(condition, "message")`
- Define errors at contract level (preferred) or module level (for free functions)
- Error name describes the condition, not the action

**Examples:**
```solidity
error ZeroAddress();
error InvalidRvmId();
error NotAuthorized();
error PoolAlreadyRegistered(PoolId poolId);
error OwnerUnauthorizedAccount();

// Usage
if (sender == address(0)) revert ZeroAddress();
if (!isAuthorized) revert NotAuthorized();
```

**Pattern — Validation:**
- Validate inputs at function entry, before side effects
- Use `require()` only for delegatecall guard checks (rare)
- Copy storage to memory before clearing (defensive against use-after-free):
  ```solidity
  RemovalData memory data = tloadRemovalData(posKey);  // Copy to memory
  _tstoreRemovalData(posKey, RemovalData(0, 0));      // Clear storage
  // Now use `data` not storage
  ```

**Pattern — Call Failures:**
- Delegatecall failures: emit `CallbackFailure` but continue (callback proxy pattern)
- External calls: catch with try/catch or low-level call, check return boolean
- Revert on critical failures only (auth, vault operations)

## Logging

**Framework:** Native Solidity events (no logging library)

**Patterns:**
- Administrative actions: emit event for user notification (e.g., `PoolAdded`)
- Accumulation of index terms: emit `FCITermAccumulated` with full snapshot
- No console logging in production; `console2` from `forge-std` only in tests

**Example:**
```solidity
event FCITermAccumulated(
    PoolId indexed poolId,
    bytes2 indexed protocolFlags,
    bytes32 indexed posKey,
    uint128 xk,
    uint256 xSquaredQ128,
    uint256 thetaK,
    uint256 blockLifetime,
    uint256 swapLifetime
);

emit FCITermAccumulated(poolId, protocolFlags, posKey, xk, xSquaredQ128, thetaK, blockLifetime, swapLifetime);
```

## Comments

**When to Comment:**
- **High-level logic**: Explain the "why" in multi-step functions (e.g., afterAddLiquidity)
- **Non-obvious math**: Cite spec (e.g., "FCI-09: p = Δ⁺ / (1 - Δ⁺)")
- **Storage patterns**: Document keccak slot names and delegation setup
- **Guard conditions**: Explain why delegatecall check is stricter than normal auth

**NatSpec/JSDoc:**
- Use `///` for functions, `///` for parameters (`@param`), `///` for returns (`@return`)
- Contract-level: one-line `@title` + brief description
- Public/external functions: full NatSpec
- Internal functions: brief inline comments if complex
- No over-documentation of obvious code

**Example:**
```solidity
/// @title UniswapV3Facet
/// @dev Protocol facet for Uniswap V3 reactive integration.
/// Called via delegatecall from FeeConcentrationIndexV2 for each behavioral function.
contract UniswapV3Facet { }

/// @notice Register a V3 pool for FCI tracking.
/// @dev poolRpt = abi.encode(IUniswapV3Pool).
function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey) { }
```

## Function Design

**Size:**
- Target <50 lines for internal functions
- Larger functions should delegate to helpers or use numbered sections with comments
- Complex protocols (afterAddLiquidity, afterSwap): 30-40 line orchestration OK if sectioned

**Parameters:**
- Limit to ≤5 positional params; use `calldata struct` for >5
- Types: prefer concrete types over `bytes` unless protocol-agnostic
- Array params: must be `calldata` not `memory`

**Return Values:**
- ≤2 values preferred; use struct if >2
- Example: `returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount)` is at limit

**Pattern — Delegatecall:**
When facet function needs to call via delegatecall:
```solidity
bytes32 posKey = abi.decode(
    LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.positionKey, (hookData, sender, params))),
    (bytes32)
);
```

## Python Conventions

**Dataclasses:**
- Use frozen dataclasses for all domain types (immutable)
- Type hints on every field
- Full qualified imports

**Example:**
```python
@dataclass(frozen=True)
class ExitPayoffResult:
    """Result for one (γ, α, Δ*) payoff backtest."""
    gamma: float
    alpha: float
    delta_star: float
    initial_balance: float
```

**Functions:**
- Pure functions preferred (no side effects)
- Type hints on all params and return
- Docstrings for complex logic
- Underscore prefix for private helpers

**Imports:**
- `from __future__ import annotations` at top for forward references
- Alphabetical within groups
- Group by: stdlib, third-party, local

## Module Design

**Solidity Modules (Free Functions):**
- One concern per file (storage, logic, adapters)
- Export a primary "getter" function (e.g., `fciRegistryStorage()`)
- Use function names to chain concerns: `getProtocolFacet()`, `setProtocolFacet()`
- Avoid re-exporting from other modules; import directly

**Barrel Files:**
- None enforced; import directly from source
- Project aliases (`@fee-concentration-index-v2/`) point to feature directory, not a barrel

**Python Modules:**
- One logical unit per file (types.py, payoff.py, oracle_comparison.py)
- Use `__init__.py` to allow test imports but don't re-export

## Storage Patterns

**Diamond Storage Slots:**
- Define const `bytes32 SLOT_NAME = keccak256("namespace.feature.item")`
- Access via function: `function storageFunction() pure returns (StorageType storage $)`
- Assembly pattern: `assembly ("memory-safe") { $.slot := slot }`
- Each facet/feature has disjoint slot namespace (no collisions)

**Example:**
```solidity
bytes32 constant FCI_REGISTRY_SLOT = keccak256("thetaSwap.fci.registry");

function fciRegistryStorage() pure returns (FeeConcentrationIndexRegistryStorage storage $) {
    bytes32 slot = FCI_REGISTRY_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}
```

---

*Convention analysis: 2026-03-17*
