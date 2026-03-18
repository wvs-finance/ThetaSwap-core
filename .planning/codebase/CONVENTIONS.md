# Coding Conventions

**Analysis Date:** 2026-03-18

## Naming Patterns

**Files:**
- Source contracts: `PascalCase.sol` for main contracts (e.g., `FeeConcentrationIndex.sol`, `UniswapV3Facet.sol`)
- Storage modules: `PascalCaseMod.sol` suffix for diamond storage modules (e.g., `FeeConcentrationIndexStorageMod.sol`, `FCIProtocolFacetStorageMod.sol`)
- Extension files: `PascalCaseExt.sol` suffix for extensions on imported types (e.g., `FeeConcentrationIndexStorageExt.sol`, `FeeGrowthReaderExt.sol`, `PoolKeyExtMod.sol`)
- Interfaces: `IPascalCase.sol` prefix (e.g., `IFeeConcentrationIndex.sol`, `IFCIProtocolFacet.sol`)
- Storage structs: `PascalCaseStorage.sol` suffix (e.g., `CustodianStorage.sol`, `OraclePayoffStorage.sol`)
- Libraries: `PascalCaseLib.sol` suffix (e.g., `FCIProtocolLib.sol`, `UniswapV3PoolKeyLib.sol`)
- Types: `PascalCaseMod.sol` suffix for UDVT files (e.g., `HookDataFlagsMod.sol`, `BlockCountExt.sol`)

**Functions:**
- Public/external: `camelCase` (e.g., `afterAddLiquidity`, `getDeltaPlus`, `registerProtocolFacet`)
- Internal/free functions: `camelCase` (e.g., `derivePoolAndPosition`, `sortTicks`, `fetchPositionKey`)
- Storage accessor free functions: `camelCase` matching the struct they return (e.g., `fciStorage()`, `fciRegistryStorage()`, `protocolAdapterStorage()`)
- Storage accessor overloads with explicit slot: `camelCase(bytes32 slot)` pattern (e.g., `protocolAdapterStorage(bytes32 slot)`)
- Admin write free functions aliased with underscore prefix: `_setFci`, `_setProtocolStateView` when imported alongside a public function of the same name

**Variables:**
- Storage struct pointers: `$` (single dollar sign) — the universal convention throughout the codebase
- Function parameters: `camelCase`
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `FCI_STORAGE_SLOT`, `LONG`, `SHORT`, `CALLBACK_GAS_LIMIT`)
- State variables in contracts: `camelCase`, immutables prefixed with `_` (e.g., `address immutable _self`)
- Mappings in storage structs: descriptive `camelCase` keys (e.g., `fciState`, `feeGrowthBaseline0`, `protocolFacets`)

**Types:**
- Structs: `PascalCase` (e.g., `FeeConcentrationIndexStorage`, `ProtocolAdapterStorage`, `Accounts`)
- Errors: `PascalCase` (e.g., `VaultAlreadySettled`, `DepositCapExceeded`, `ZeroAmount`)
- Events: `PascalCase` (e.g., `FCITermAccumulated`, `PoolAdded`, `FundsMigrated`)
- UDVTs (User-Defined Value Types): `PascalCase` (e.g., `TickRange`, `FeeShareRatio`, `SwapCount`, `BlockCount`)
- Protocol flag constants: `SCREAMING_SNAKE_CASE` with `bytes2` type (e.g., `NATIVE_V4`, `UNISWAP_V3_REACTIVE`)

## Code Style

**Formatting:**
- Foundry native linting via `[lint]` section in `foundry.toml`
- Several lint rules explicitly excluded in `foundry.toml` lines 60-71:
  - `mixed-case-function`, `mixed-case-variable`: allows deliberate convention deviations
  - `pascal-case-struct`: allows non-PascalCase struct names in some contexts
  - `screaming-snake-case-immutable`: `_self` style immutables allowed
  - `unsafe-typecast`, `asm-keccak256`, `erc20-unchecked-transfer`, `unwrapped-modifier-logic`, `unused-import`

**Contract Structure Order:**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// imports (external libs first, then internal by layer: interfaces, types, storage, libs)

// file-level constants (if storage module)
// file-level structs (if storage module)

contract/abstract contract Name {
    // events
    // errors
    // immutables
    // constructor
    // modifiers
    // admin functions
    // main interface functions (grouped by action type)
    // view functions
    // IERC165
}
```

**Section Dividers:**
```solidity
// ── SectionName ──
```
Used consistently to separate logical groups within contracts and modules.

**Transient Storage:**
Functions using transient storage (`tstore`/`tload`) are named with `t_` prefix for internal free functions, or `tstore`/`tload` prefix for module-level functions (e.g., `t_storeTick`, `_tstoreTick`, `tloadTick`).

## Import Organization

**Order in source files:**
1. External library imports (v4-core, v3-core, forge-std, solady, typed-uniswap-v4, reactive-lib)
2. Internal imports by path alias group (`@fee-concentration-index/`, `@fee-concentration-index-v2/`, `@protocol-adapter/`, `@fci-token-vault/`, `@libraries/`, `@types/`, `@utils/`)

**Path Aliases (from `foundry.toml`):**
- `@fee-concentration-index/` → `src/fee-concentration-index/`
- `@fee-concentration-index-v2/` → `src/fee-concentration-index-v2/`
- `@protocol-adapter/` → `src/protocol-adapter/`
- `@fci-token-vault/` → `src/fci-token-vault/`
- `@libraries/` → `src/libraries/`
- `@types/` → `src/types/`
- `@utils/` → `src/utils/`
- `@foundry-script/` → `foundry-script/`
- `v4-core/` → `lib/uniswap-hooks/lib/v4-core/`
- `@uniswap/v3-core/` → `lib/v3-core/`
- `solady/` → `lib/solady/src/`
- `compose/` → `lib/hook-bazaar/contracts/lib/Compose/src/`

**Named import style:**
Use named imports throughout: `import {Symbol} from "path";` — never bare imports. Multi-symbol imports are grouped in `{}` with line breaks for readability when more than ~3 symbols.

## Diamond Storage Pattern

**Canonical pattern for every storage module:**
```solidity
// 1. Struct definition
struct FooStorage {
    mapping(Key => Value) data;
}

// 2. Slot constant
bytes32 constant FOO_SLOT = keccak256("thetaSwap.foo");

// 3. Storage accessor free function
function fooStorage() pure returns (FooStorage storage s) {
    bytes32 slot = FOO_SLOT;
    assembly {
        s.slot := slot
    }
}

// 4. Operational free functions (parameterized + no-arg convenience overloads)
function doOperation(FooStorage storage $, ...) { ... }
function doOperation(...) { doOperation(fooStorage(), ...); }
```

**Slot naming convention:**
- `keccak256("thetaSwap.<feature>")` — e.g., `"thetaSwap.fci"`, `"thetaSwap.fci.reactive"`, `"thetaSwap.fci.epoch"`
- `keccak256("thetaswap.<feature>")` — lowercase for vault (e.g., `"thetaswap.oracle-payoff"`, `"thetaswap.collateral-custodian"`)
- `keccak256("thetaSwap.protocolAdapter.<protocol>")` — for protocol adapters

**Storage pointer convention:**
Always assign `storage $` (dollar sign) for the storage struct pointer inside functions.

## No Inheritance in Production Contracts (SCOP Rule)

Production contracts MUST NOT use `is` inheritance. This is a hard project rule ("SCOP: no is inheritance").

```solidity
// CORRECT
contract FeeConcentrationIndex {
    // implements IFeeConcentrationIndex but does NOT declare `is IFeeConcentrationIndex`
    function supportsInterface(...) external pure returns (bool) { ... }
}

// WRONG — never do this in production
contract FeeConcentrationIndex is BaseHook, IFeeConcentrationIndex { ... }
```

Test contracts and abstract helpers use inheritance freely (e.g., `abstract contract FCIFixture is PosmTestSetup, FCITestHelper`).

## No `library` Keyword

Free functions are used instead of `library`. Libraries are only used from external dependencies. Use file-level free functions with file-level `struct`/`constant` definitions.

```solidity
// CORRECT
function sortTicks(int24 a, int24 b) pure returns (int24 tickMin, int24 tickMax) { ... }

// WRONG
library TickUtils {
    function sortTicks(int24 a, int24 b) pure returns (...) { ... }
}
```

## Error Handling

**Custom errors only** — `revert` with typed custom errors:
```solidity
error VaultAlreadySettled();
error DepositCapExceeded();
error ZeroAmount();

if (amount == 0) revert ZeroAmount();
if (cs.depositCap > 0 && newTotal > cs.depositCap) revert DepositCapExceeded();
```

**Require strings** — `require` with strings used only in modifiers for delegatecall guards:
```solidity
modifier onlyDelegateCall() {
    require(address(this) != _self, "UniswapV3Facet: direct call");
    require(...);
    _;
}
```

**No raw `revert()` or `require(cond)` without message** in production (except in `require` for obvious guard checks in modifiers).

**SafeCastLib** (Solady) used for downcasts: `SafeCastLib.toUint128(amount)` — never silent truncation.

## Comments

**NatDoc (`///`) for:**
- Public/external functions with non-obvious behavior
- Interface function declarations
- Design decisions that need justification
- `@param` and `@dev` tags when behavior is non-trivial

**Inline `//` comments for:**
- Step numbering within hook functions (e.g., `// 1. positionKey`, `// 2. latestPositionFeeGrowthInside`)
- Invariant references: `/// @dev INV-001: deposit mints equal LONG + SHORT`
- Design decisions: `// Partial removes and fee-only collects (liquidityDelta == 0) leave the position alive`
- Cross-reference to external docs: `/// See docs/superpowers/specs/2026-03-12-protocol-adapter-storage-design.md`

**Block comments with `// ──`** used as section dividers (not `/* */`).

**Module file headers:**
```solidity
// Diamond storage for Fee Concentration Index HookFacet.
// Runs via delegatecall in MasterHook's storage context.
// Namespace: keccak256("thetaSwap.fci") — disjoint from MasterHook and DiamondCut slots.
```

## Function Design

**Parameterized + no-arg overloads:**
Every storage operation has two signatures — one taking explicit `Storage storage $` (for multi-storage use), and one no-arg that calls the default storage accessor:
```solidity
function setFeeGrowthBaseline(FeeConcentrationIndexStorage storage $, PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) { ... }
function setFeeGrowthBaseline(PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    setFeeGrowthBaseline(fciStorage(), poolId, positionKey, feeGrowth0X128);
}
```

**Delegatecall dispatch in V2:**
Protocol-specific behavior is isolated to registered facets via `LibCall.delegateCallContract(facet, abi.encodeCall(...))`. Hook orchestration stays in `FeeConcentrationIndexV2`. Step comments are numbered sequentially.

**Parameter naming:**
Unused parameters in hook callback signatures are left unnamed (no identifier):
```solidity
function afterSwap(address, PoolKey calldata key, SwapParams calldata, BalanceDelta, bytes calldata hookData)
```

## Module Design

**Exports:**
Storage modules export: struct definition + slot constant + accessor function + all operational free functions.

**No barrel files.** Each module is imported directly by path alias.

**Protocol flag dispatch:**
All protocol-branching logic uses `bytes2` flags (from `src/fee-concentration-index-v2/types/FlagsRegistry.sol`). Never use `if (protocol == "v3")` string comparisons.

---

*Convention analysis: 2026-03-18*
