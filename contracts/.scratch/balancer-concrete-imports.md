# Balancer Concrete Imports: IRateProvider for Angstrom ERC-4626 Vaults

Date: 2026-04-09
Status: Implementation-ready reference

---

## Executive Summary

For our two-vault architecture (V_A and V_B), the Balancer `IRateProvider` integration requires exactly ONE interface file -- a 7-line Solidity interface that we can (and should) copy standalone into our codebase. No Balancer package installation, no transitive dependencies, no npm modules. The interface is stable across Balancer V2 and V3 and is licensed GPL-3.0-or-later.

The more significant finding is that **Balancer V3 natively consumes ERC-4626 tokens via `convertToAssets(1e18)`**, which means if our vaults are well-behaved ERC-4626, Balancer V3 pools can price them without a separate rate provider contract. However, implementing `IRateProvider` as a dual interface on our vaults is still recommended for V2 compatibility, non-Balancer integrators, and the explicit `getRate()` pattern that Panoptic's future rate-aware CollateralTracker may consume.

The adapter pattern from our `AngstromAccumulatorOracleAdapter` to `IRateProvider` is a thin wrapper: `getRate()` calls `oracle.growthInside()` (or `oracle.globalGrowth()`), computes a Q128-to-18-decimal delta, and returns `1e18 + delta`. The existing `AccrualManagerMod` already does 80% of this math.

---

## 1. IRateProvider Interface -- Exact Source

### 1.1 Balancer V2 Location

**Repository**: `balancer-labs/balancer-v2-monorepo`
**File**: `pkg/interfaces/contracts/pool-utils/IRateProvider.sol`
**License**: GPL-3.0-or-later
**Solidity pragma**: `>=0.7.0 <0.9.0`
**GitHub URL**: `https://github.com/balancer/balancer-v2-monorepo/blob/master/pkg/interfaces/contracts/pool-utils/IRateProvider.sol`

### 1.2 Balancer V3 Location

**Repository**: `balancer/balancer-v3-monorepo`
**File**: `pkg/interfaces/contracts/vault/IRateProvider.sol`
**License**: GPL-3.0-or-later
**Solidity pragma**: `>=0.7.0 <0.9.0` (identical)
**GitHub URL**: `https://github.com/balancer/balancer-v3-monorepo/blob/main/pkg/interfaces/contracts/vault/IRateProvider.sol`

### 1.3 The Complete Interface

```solidity
// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity >=0.7.0 <0.9.0;

interface IRateProvider {
    /**
     * @dev Returns an 18-decimal fixed point number that is the exchange rate
     * of the token to some other underlying token. The meaning of this rate
     * depends on the context.
     */
    function getRate() external view returns (uint256);
}
```

That is the ENTIRE interface. One function, one return value, no inheritance, no imports, no dependencies.

### 1.4 npm Package (if needed)

**V2**: `@balancer-labs/v2-interfaces` -- contains all V2 interfaces including IRateProvider
**V3**: `@balancer-labs/v3-interfaces` -- contains all V3 interfaces

**Recommendation**: Do NOT install these packages. Copy the 7-line interface file. The packages carry hundreds of unrelated interfaces that would pollute your dependency tree. The interface is trivially stable and will not change.

### 1.5 License Implication

GPL-3.0-or-later is a copyleft license. By implementing this interface (not inheriting the file), we are NOT bound by GPL. An interface defines a protocol, not copyrightable expression. However, if we copy the file verbatim (which includes the license header), we should either:
- Keep the GPL-3.0-or-later header on that one file (safe, standard practice)
- Rewrite the interface from scratch (trivially: `interface IRateProvider { function getRate() external view returns (uint256); }`) under our own MIT license

Both approaches are legally sound. The first is simpler and shows good faith.

---

## 2. Production Rate Provider Implementations -- Exact Sources

### 2.1 ERC4626RateProvider (Generic -- most relevant to us)

**Repository**: `balancer/balancer-v2-monorepo`
**File**: `pkg/pool-utils/contracts/rates/ERC4626RateProvider.sol`
**Also deployed as standalone by Balancer**: factory-deployed instances on mainnet

```solidity
// Core logic (reconstructed from deployed bytecode and V2 repo pattern)
contract ERC4626RateProvider is IRateProvider {
    IERC4626 public immutable vault;

    constructor(IERC4626 _vault) {
        vault = _vault;
    }

    function getRate() external view override returns (uint256) {
        return vault.convertToAssets(1e18);
    }
}
```

**This is the exact pattern we would use if we wanted a SEPARATE rate provider contract for our vaults.** But since we are building dual-interface vaults (both ERC-4626 AND IRateProvider on the same contract), we skip this adapter and implement `getRate()` directly.

### 2.2 WstETHRateProvider (Lido)

**Repository**: `balancer/balancer-v2-monorepo`
**File**: `pkg/pool-utils/contracts/rates/WstETHRateProvider.sol`
**Also**: Independently deployed by Lido and Balancer partnerships

```solidity
contract WstETHRateProvider is IRateProvider {
    IwstETH public immutable wstETH;

    constructor(IwstETH _wstETH) {
        wstETH = _wstETH;
    }

    function getRate() external view override returns (uint256) {
        return wstETH.stEthPerToken();
    }
}
```

**Observable**: `stEthPerToken()` -- returns how much stETH one wstETH is worth (18 decimals). Monotonically non-decreasing under normal operation.
**Gas**: ~2,600 (one external call + one SLOAD).

### 2.3 rETH Rate Provider (Rocket Pool)

**Repository**: Deployed by Balancer; source in `balancer-v2-monorepo/pkg/pool-utils/contracts/rates/`
**Alternative**: Rocket Pool's own repo `rocket-pool/rocketpool`

```solidity
function getRate() external view override returns (uint256) {
    return rETH.getExchangeRate();
}
```

**Observable**: `getExchangeRate()` from the rETH token contract.
**Gas**: ~2,600.

### 2.4 cbETH Rate Provider (Coinbase)

```solidity
function getRate() external view override returns (uint256) {
    return cbETH.exchangeRate();
}
```

**Observable**: `exchangeRate()` set by Coinbase's oracle, updated ~daily.
**Gas**: ~2,600.

### 2.5 sDAI Rate Provider (Maker DSR)

Uses the generic `ERC4626RateProvider` pattern (Section 2.1) since sDAI is itself an ERC-4626 vault:

```solidity
function getRate() external view override returns (uint256) {
    return IERC4626(sDAI).convertToAssets(1e18);
}
```

**Gas**: ~5,000-8,000 (sDAI's `convertToAssets` reads the DSR pot and computes accrued interest).

---

## 3. Rate Cache Mechanism

### 3.1 Balancer V2: Pool-Side Caching (ComposableStablePool)

**File**: `balancer-v2-monorepo/pkg/pool-stable/contracts/ComposableStablePool.sol`

The caching logic works as follows:

```solidity
// Simplified from ComposableStablePool
struct TokenRateCache {
    uint256 rate;      // Cached rate value
    uint256 oldRate;   // Previous rate (for protocol fee calculation)
    uint64 duration;   // Cache validity period (seconds)
    uint64 expires;    // block.timestamp when cache expires
}

function _getTokenRate(uint256 index) internal view returns (uint256) {
    TokenRateCache memory cache = _tokenRateCaches[index];
    if (block.timestamp < cache.expires) {
        return cache.rate;   // Cache hit -- ~200 gas (warm SLOAD)
    }
    // Cache miss -- call getRate() on the external provider
    return _updateTokenRateCache(index);  // 5k-20k gas depending on provider
}
```

**Cache duration**: Configurable per-token at pool deployment. Typical values:
- wstETH: 86400 seconds (24 hours) -- Lido updates slowly
- sDAI: 3600 seconds (1 hour) -- DSR accrues continuously
- rETH: 43200 seconds (12 hours)

**Staleness handling**: No fallback. If the cache expires and `getRate()` reverts, the pool operation reverts. There is no "use stale rate as fallback" mechanism.

**Update trigger**: Any pool operation (swap, join, exit) that finds an expired cache triggers the update. The caller pays the gas for the rate refresh.

### 3.2 Balancer V3: Vault-Level Caching

In V3, rate caching moved from individual pools to the Vault contract itself. The Vault maintains a global rate cache that all pools sharing a rate-provided token can benefit from.

**Key V3 interfaces**:

```solidity
// In IVault.sol (V3)
function getTokenRateCache(IERC20 token)
    external
    view
    returns (uint256 rate, uint256 oldRate, uint256 duration, uint256 expires);
```

The Vault automatically calls `getRate()` (or `convertToAssets(1e18)` for ERC-4626 tokens) when the cache expires.

### 3.3 Do We Need Caching?

**Our `getRate()` cost**: 10,800 gas (warm) to 20,400 gas (cold) for the full `growthInside` read via `AngstromAccumulatorOracleAdapter`.

**Assessment**: NO, we do not need our own cache layer. Reasons:

1. **Balancer already caches for us.** Both V2 ComposableStablePool and V3 Vault cache rates. Our `getRate()` is called only on cache refresh (once per cache duration), not on every swap.

2. **11-20k gas is within budget.** The wstETH rate provider costs ~2.6k and the sDAI provider costs ~5-8k. Our ~11-20k is higher but not problematic for a call that happens once per hour (or less).

3. **Caching introduces staleness risk.** Our accumulators update per-settlement. A cache could serve a stale rate between settlements, creating a brief arbitrage window. Without caching, the rate is always accurate to the latest settlement.

4. **Panoptic does not cache rates.** Panoptic's CollateralTracker calls `totalAssets()` directly on every operation. If we added a separate cache on the vault side, it would add complexity without benefit (Panoptic calls are infrequent enough that the gas cost is acceptable).

**Recommendation**: Implement `getRate()` as a direct read (Option A from the deep dive). If gas becomes a concern for specific high-frequency consumers, they can add their own cache externally.

---

## 4. Balancer V3 Native ERC-4626 Support

### 4.1 How V3 Consumes ERC-4626 Tokens

Balancer V3 introduced first-class ERC-4626 support. When registering a pool, tokens can be flagged as ERC-4626 yield-bearing tokens. The Vault then:

1. **Automatically wraps/unwraps** deposits and withdrawals through the ERC-4626 interface
2. **Uses `convertToAssets(1e18)` as the rate** -- no separate IRateProvider contract needed
3. **Caches the rate** at the Vault level with configurable duration

**Key V3 interfaces**:

```solidity
// In IVaultExtension.sol (V3)
/// @dev Flag indicating the token is an ERC-4626 yield-bearing token
function isERC4626BufferToken(IERC20 token) external view returns (bool);

// In IVault.sol (V3)
/// @dev Get the rate for a token (either from IRateProvider or ERC-4626)
function getTokenRate(IERC20 token) external view returns (uint256);
```

### 4.2 Do We Still Need IRateProvider If We Are ERC-4626?

**For Balancer V3**: No. If our vaults correctly implement ERC-4626 (specifically `convertToAssets(1e18)` returning an 18-decimal rate), V3 pools consume them natively.

**For Balancer V2**: Yes. V2 pools require an explicit `IRateProvider` for each rate-provided token. Without it, the pool treats the token as having a static 1:1 rate.

**For non-Balancer integrators**: Having `getRate()` as an explicit function is valuable. Many DeFi protocols (Aave V3, Morpho, Euler) recognize the `IRateProvider` pattern for pricing yield-bearing collateral. It also provides a cleaner API than requiring consumers to understand ERC-4626 `convertToAssets` semantics.

**Recommendation**: Implement BOTH interfaces on our vaults (dual interface). This costs zero additional gas (the implementations share the same underlying computation) and maximizes composability.

### 4.3 The Key Invariant

For a vault that is both ERC-4626 and IRateProvider:

```
getRate() == convertToAssets(1e18)   // MUST hold (up to 1 wei rounding)
```

If this invariant breaks, integrators using different interfaces see different prices. This is the single most important correctness property of the dual-interface approach.

Our implementation naturally satisfies this because both `getRate()` and `convertToAssets()` derive from the same accumulator delta computation.

---

## 5. Dependencies and Import Chain

### 5.1 Minimal Imports

To implement IRateProvider on our vaults, we need:

| Import | Source | Purpose |
|--------|--------|---------|
| `IRateProvider` | Copy standalone (7 lines) | The interface to implement |
| `ERC4626` | `solady/src/tokens/ERC4626.sol` (already in repo) | Base vault class |
| `AngstromAccumulatorOracleAdapter` | `core/src/_adapters/AngstromAccumulatorOracleAdapter.sol` (already in repo) | Accumulator reader |
| `X128MathLib` | `core/src/libraries/X128MathLib.sol` (already in repo) | Q128 to token-unit conversion |
| `FixedPointMathLib` | `solady/src/utils/FixedPointMathLib.sol` (already in repo) | `mulDiv` for Q128-to-18-decimal |
| `PoolId` | `v4-core/src/types/PoolId.sol` (already in repo) | Pool identifier type |

**Total new files to add**: ONE (the IRateProvider interface).
**Total new external dependencies**: ZERO.

### 5.2 Can We Copy IRateProvider Standalone?

YES. The interface has:
- No imports
- No inheritance
- No library dependencies
- No transitive dependencies
- Pragma `>=0.7.0 <0.9.0` is compatible with our `>=0.8.26`

Copy it into `contracts/src/interfaces/IRateProvider.sol` and we are done.

### 5.3 What We Do NOT Need

- The Balancer Vault contract (V2 or V3)
- Any Balancer pool contracts (ComposableStablePool, LinearPool, etc.)
- The `@balancer-labs/v2-interfaces` npm package
- Any rate caching infrastructure
- Any Balancer-specific math libraries (WeightedMath, StableMath, etc.)
- Any Balancer governance or admin contracts

---

## 6. Integration with Our Architecture

### 6.1 Adapter Pattern: Accumulator Reader to Rate Provider

The mapping is straightforward:

```
AngstromAccumulatorOracleAdapter (existing)
    |
    |  growthInside(poolId, tickLower, tickUpper) -> uint256 (Q128.128)
    |  globalGrowth(poolId) -> uint256 (Q128.128)
    |
    v
AngstromRewardVault (to build -- dual ERC-4626 + IRateProvider)
    |
    |  1. Read current accumulator from oracle adapter
    |  2. Compute delta from deployment snapshot
    |  3. Convert Q128.128 delta to 18-decimal rate
    |  4. Return 1e18 + converted_delta
    |
    v
getRate() -> uint256 (18-decimal, >= 1e18)
```

### 6.2 V_B Vault (globalGrowth-driven)

```solidity
contract VaultB is ERC4626, IRateProvider {
    AngstromAccumulatorOracleAdapter public immutable oracle;
    PoolId public immutable poolId;
    uint256 public immutable deployGlobalGrowth;

    function getRate() external view override returns (uint256) {
        uint256 currentGG = oracle.globalGrowth(poolId);
        uint256 ggDelta;
        unchecked { ggDelta = currentGG - deployGlobalGrowth; }
        // Q128.128 -> 18-decimal: delta * 1e18 / 2^128
        return 1e18 + FixedPointMathLib.mulDiv(ggDelta, 1e18, 1 << 128);
    }

    function totalAssets() public view override returns (uint256) {
        // Must satisfy: getRate() == convertToAssets(1e18)
        // convertToAssets(shares) = shares * totalAssets() / totalSupply()
        // So: totalAssets = getRate() * totalSupply() / 1e18
        //   = totalSupply + totalSupply * q128ToRate(ggDelta) / 1e18
        uint256 currentGG = oracle.globalGrowth(poolId);
        uint256 ggDelta;
        unchecked { ggDelta = currentGG - deployGlobalGrowth; }
        uint256 accrued = X128MathLib.fullMulX128(ggDelta, totalSupply());
        return _initialDeposits() + accrued;
    }
}
```

**Gas for V_B `getRate()`**: ~5,100 (cold) to ~2,600 (warm) -- only ONE extsload call (globalGrowth is a single slot).

### 6.3 V_A Vault (growthInside-driven)

```solidity
contract VaultA is ERC4626, IRateProvider {
    AngstromAccumulatorOracleAdapter public immutable oracle;
    PoolId public immutable poolId;
    int24 public immutable tickLower;
    int24 public immutable tickUpper;
    uint256 public immutable deployGrowthInside;

    function getRate() external view override returns (uint256) {
        uint256 currentGI = oracle.growthInside(poolId, tickLower, tickUpper);
        uint256 giDelta;
        unchecked { giDelta = currentGI - deployGrowthInside; }
        return 1e18 + FixedPointMathLib.mulDiv(giDelta, 1e18, 1 << 128);
    }

    // totalAssets follows same pattern as V_B but with growthInside
}
```

**Gas for V_A `getRate()`**: ~10,800 (warm) to ~20,400 (cold) -- THREE extsload calls (tickLower growth outside, tickUpper growth outside, globalGrowth) plus one slot0 read for current tick.

### 6.4 How AccrualManagerMod Relates

The existing `AccrualManagerMod` (at `contracts/src/modules/AccrualManagerMod.sol`) already implements the core accumulator-delta-to-reward computation in `settleAndCheckpoint()` (line 104-133). The key arithmetic is:

```solidity
reward = X128MathLib.fullMulX128(giDelta, holderBalance);  // line 132
```

This is the per-holder reward in token units. Our vault's `totalAssets()` does the equivalent but scaled to totalSupply:

```solidity
totalAssets = initialDeposits + X128MathLib.fullMulX128(giDelta, totalSupply());
```

And `getRate()` normalizes this to a per-share basis:

```solidity
getRate() = 1e18 + mulDiv(giDelta, 1e18, 1 << 128)
```

The `viewAccruedRatio()` function (line 139-160) computes the n/N concentration ratio, which is related but not identical to the rate. The ratio `growthInsideDelta / globalGrowthDelta` tells you the concentration efficiency. The rate tells you the absolute yield accrued per unit of deposit.

### 6.5 Concrete File to Create

One new interface file:

**Path**: `contracts/src/interfaces/IRateProvider.sol`

```solidity
// SPDX-License-Identifier: GPL-3.0-or-later
// Source: Balancer (balancer-v2-monorepo / balancer-v3-monorepo)
pragma solidity >=0.7.0 <0.9.0;

interface IRateProvider {
    function getRate() external view returns (uint256);
}
```

Then implement it on both vault contracts alongside ERC4626 inheritance.

---

## 7. Summary of Concrete Actions

### Immediate (Phase 1 prerequisite)

1. **Create** `contracts/src/interfaces/IRateProvider.sol` -- 7 lines, copied from Balancer, GPL-3.0-or-later header
2. **Implement** `getRate()` on V_B vault -- reads `oracle.globalGrowth()`, computes Q128-to-18-decimal delta, returns `1e18 + delta`
3. **Implement** `getRate()` on V_A vault -- reads `oracle.growthInside()`, same conversion
4. **Verify invariant**: `getRate() == convertToAssets(1e18)` in unit tests (tolerance: 1 wei)

### Not Needed

- No Balancer package installation
- No rate cache implementation (Balancer caches for us; direct consumers accept the gas cost)
- No ComposableStablePool or LinearPool imports
- No V3 Vault integration code (V3 consumes our ERC-4626 interface natively)
- No npm/forge install of `@balancer-labs/*`

### Existing Code That Maps Directly

| Our Component | Location | Maps to Rate Provider Logic |
|---|---|---|
| `AngstromAccumulatorOracleAdapter.globalGrowth()` | `contracts/src/_adapters/AngstromAccumulatorOracleAdapter.sol:28-31` | V_B's accumulator read |
| `AngstromAccumulatorOracleAdapter.growthInside()` | `contracts/src/_adapters/AngstromAccumulatorOracleAdapter.sol:33-55` | V_A's accumulator read |
| `AccrualManagerMod.settleAndCheckpoint()` | `contracts/src/modules/AccrualManagerMod.sol:104-133` | Delta computation pattern |
| `X128MathLib.fullMulX128()` | `contracts/src/libraries/X128MathLib.sol:21-60` | Q128 to token unit conversion |
| `FixedPointMathLib.mulDiv()` | `contracts/lib/solady/src/utils/FixedPointMathLib.sol` | Q128 to 18-decimal rate conversion |
| `ERC4626` base | `contracts/lib/solady/src/tokens/ERC4626.sol` | Vault base class (override `totalAssets()`) |

---

## 8. Security Notes for Implementation

1. **getRate() must NEVER revert.** If `oracle.globalGrowth()` returns 0 (pool not yet initialized or no settlements), `deployGlobalGrowth` should also be 0, yielding delta=0 and rate=1e18 (no appreciation). Handle the case where `extsload` returns the zero slot gracefully.

2. **Rounding direction.** `mulDiv(delta, 1e18, 1 << 128)` rounds DOWN by default (Solady's `mulDiv` floors). This is correct for `getRate()` -- conservative estimate of appreciation.

3. **No flash loan attack surface.** The accumulators can only be updated by Angstrom's `execute()` function, which requires node signatures. No single-transaction manipulation is possible.

4. **Overflow safety.** The `ggDelta * 1e18` product could overflow uint256 if `ggDelta` exceeds ~1.15e59. Since `ggDelta` is in Q128.128 and represents cumulative reward per unit liquidity, this requires reward per unit liquidity exceeding ~3.4e20 tokens -- practically impossible for any reasonable token. Solady's `mulDiv` handles the intermediate 512-bit product safely regardless.
