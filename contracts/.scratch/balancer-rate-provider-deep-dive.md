# Balancer IRateProvider Deep Dive: Adapting for Angstrom globalGrowth ERC-4626 Vaults

Date: 2026-04-09

---

## Executive Summary

Balancer's `IRateProvider` is a single-function oracle interface (`getRate() returns (uint256)`) that allows pools to price yield-bearing tokens relative to their underlying. It is the canonical pattern in DeFi for expressing a monotonically increasing share-price observable to an AMM. This report analyzes the interface, its consuming pools (Boosted, Linear, Composable Stable), production implementations (wstETH, sDAI, rETH, cbETH), known issues, and how to adapt it for an ERC-4626 vault whose share price is driven by Angstrom's `globalGrowth` reward accumulator (or more precisely, by the `growthInside` delta-over-time for a specific tick range).

**Key Finding**: A dual-interface contract that is both an ERC-4626 vault AND an `IRateProvider` is architecturally clean and has precedent (Balancer's own `StablePoolRateProviderExtension`, several yield wrappers). For our use case, `getRate()` would return the same value that drives `totalAssets()` -- the accrued reward ratio from Angstrom's accumulators. The critical design decision is whether `getRate()` reads live from the Angstrom oracle adapter (gas cost ~5-10k per `extsload`) or from a cached checkpoint (cheaper but potentially stale).

---

## 1. The IRateProvider Interface

### 1.1 Interface Definition

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

**Repository**: `balancer/balancer-v2-monorepo`, file `pkg/interfaces/contracts/pool-utils/IRateProvider.sol`.

In Balancer V3: `balancer/balancer-v3-monorepo`, file `pkg/interfaces/contracts/vault/IRateProvider.sol`. The interface is identical.

### 1.2 Key Properties

| Property | Value |
|----------|-------|
| Return type | `uint256`, 18-decimal fixed point |
| Canonical unit | 1e18 = 1:1 rate (no appreciation) |
| Expected direction | Monotonically non-decreasing for yield-bearing tokens |
| Gas budget | Must be cheap enough for on-chain reads (~2k-10k gas typical) |
| Statefulness | MUST be a `view` function (no state mutation) |
| Caller | Pool contracts during swap/join/exit math |

### 1.3 Who Calls getRate() and When

- **On every swap** through a pool containing a rate-provided token
- **On every join/exit** to convert between "wrapped" and "underlying" token amounts
- **By off-chain indexers** for pricing and TVL calculation
- **By other protocols** integrating with Balancer (Aura, Aave, etc.)

The rate is called frequently and must be gas-efficient.

---

## 2. How Pools Consume Rate Providers

### 2.1 Linear Pools

**Contract**: `LinearPool.sol` (V2), deprecated in V3.

**Purpose**: Enable efficient swaps between a yield-bearing token (e.g., aDAI) and its underlying (e.g., DAI) within a constrained price corridor.

**How the rate is used**:
```
wrappedBalance_in_underlying = wrappedBalance * getRate() / 1e18
```

The Linear Pool math operates entirely in "underlying" units. When a user swaps wrapped tokens, the pool multiplies the wrapped amount by the rate to get the effective underlying amount, then applies the linear invariant (`a * mainBalance + b * wrappedBalance_scaled`).

**Key detail**: The rate is used as a simple **multiplicative scaling factor**. Division by the rate is used in the reverse direction (underlying -> wrapped amount).

**Monotonicity assumption**: The pool assumes the rate only increases. If it decreases, the linear invariant can be violated, potentially leading to pool drain. Linear Pools have an upper/lower target range that limits exposure.

### 2.2 Boosted Pools

**Contract**: `BoostedPool` is a composition pattern, not a single contract. It is typically a `ComposableStablePool` containing `LinearPool` BPT tokens.

**Architecture**:
```
BoostedPool (ComposableStablePool)
  |-- LinearPool(DAI/aDAI)   <-- aDAI has RateProvider
  |-- LinearPool(USDC/cUSDC) <-- cUSDC has RateProvider
  |-- LinearPool(USDT/aUSDT) <-- aUSDT has RateProvider
```

**How rates flow**:
1. Each LinearPool uses its own RateProvider to price wrapped tokens
2. The outer ComposableStablePool then uses RateProviders for each LinearPool's BPT token
3. The BPT rate providers return the "virtual price" of the LinearPool (what 1 BPT is worth in underlying)

**Rate composition**: Rates are applied at each nesting level independently. The outer pool scales BPT balances by their rates before computing the StableMath invariant.

### 2.3 Composable Stable Pools

**Contract**: `ComposableStablePool.sol`

**How the rate is used**: Before applying the StableMath invariant (based on Curve's StableSwap), the pool scales each token's balance:

```
scaledBalance[i] = balance[i] * scalingFactor[i] * rateProvider[i].getRate() / 1e18
```

The `scalingFactor` handles decimal normalization (e.g., USDC has 6 decimals, needs 1e12 to reach 18). The rate handles yield appreciation.

**The invariant** then operates on these scaled balances as if all tokens were at par. This means the StableMath amplification parameter `A` is tuned for tokens that, after scaling, should trade near 1:1.

**Rate direction in the invariant**: If a rate increases, the pool's invariant sees a larger effective balance for that token. This is correct -- a yield-bearing token with a higher rate IS worth more underlying. The pool automatically adjusts swap ratios.

**Rate caching**: ComposableStablePool caches rates and periodically updates them (configurable duration, typically 1 hour to 1 day). Between updates, the cached rate is used. This is a critical gas optimization -- `getRate()` is only called on cache refresh, not on every swap.

```solidity
// Simplified from ComposableStablePool
function _getScalingFactor(uint256 index) internal view returns (uint256) {
    return _scalingFactor[index] * _getTokenRate(index) / 1e18;
}

function _getTokenRate(uint256 index) internal view returns (uint256) {
    if (block.timestamp < _tokenRateCacheExpiry[index]) {
        return _tokenRateCache[index]; // Cached -- cheap
    }
    return _updateTokenRateCache(index); // Live read + cache update
}
```

---

## 3. Production Rate Provider Implementations

### 3.1 wstETH Rate Provider (Lido)

**Contract**: `WstETHRateProvider.sol`
**Repository**: `balancer/balancer-v2-monorepo` or deployed separately by Lido/Balancer.

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

**Observable**: `stEthPerToken()` from the wstETH contract, which returns how much stETH one wstETH is worth. This increases as Lido receives staking rewards.

**Gas**: ~2.6k (single external call + SLOAD in wstETH).

**Monotonicity**: Strictly non-decreasing in normal operation. Can decrease in a slashing event (rare but possible for staking derivatives). This is a known edge case -- pools can temporarily be in an inconsistent state until the rate is updated.

### 3.2 sDAI Rate Provider (Maker DSR)

**Contract**: `ERC4626RateProvider.sol` (generic) or `SDAIRateProvider.sol`

```solidity
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

**Observable**: `convertToAssets(1e18)` from the ERC-4626 vault (sDAI). This tells you how much DAI 1e18 shares of sDAI are worth.

**Gas**: ~5-8k depending on sDAI's internal computation (reads DSR pot value, computes accrued interest).

**Monotonicity**: Strictly non-decreasing as DSR only accrues interest.

**CRITICAL INSIGHT**: This is exactly the dual-interface pattern we want, just inverted. Here, an ERC-4626 vault (sDAI) is *read by* a separate RateProvider contract. In our case, we want a single contract that IS both the vault and the rate provider.

### 3.3 rETH Rate Provider (Rocket Pool)

**Contract**: `RETHRateProvider.sol`

```solidity
function getRate() external view override returns (uint256) {
    return rETH.getExchangeRate();
}
```

**Observable**: `getExchangeRate()` from the rETH contract, which returns ETH per rETH. Updated by Rocket Pool oracle network.

**Gas**: ~2.6k.

**Monotonicity**: Non-decreasing in normal operation. Theoretically can decrease if Rocket Pool validators are slashed significantly, though the protocol has mechanisms to smooth this.

### 3.4 cbETH Rate Provider (Coinbase)

**Contract**: `CBETHRateProvider.sol`

```solidity
function getRate() external view override returns (uint256) {
    return cbETH.exchangeRate();
}
```

**Observable**: `exchangeRate()` from the cbETH contract, set by Coinbase's oracle. Updated periodically (~daily).

**Gas**: ~2.6k (single SLOAD via proxy).

**Monotonicity**: Non-decreasing by design. Coinbase controls the oracle, so it will not report a decrease unless there's a genuine loss event.

### 3.5 AMM Fee Accumulator Rate Providers

**No widely-deployed rate provider exists that reads from a Uniswap-style fee accumulator (feeGrowthGlobal or feeGrowthInside).** This is the gap we are filling.

The closest precedents are:
- **Bunni V2**: An ERC-4626 vault wrapping Uniswap V4 positions, but it does not expose IRateProvider.
- **Arrakis V2**: Uses its own `IArrakisVaultV2.totalUnderlying()` pattern, not IRateProvider.
- **Gamma Strategies**: Similar custom pattern.

Our implementation would be the first to bridge an AMM reward accumulator to the IRateProvider interface.

---

## 4. Balancer V3 Changes

### 4.1 Interface Preservation

Balancer V3 preserves the `IRateProvider` interface exactly as-is. The function signature `getRate() returns (uint256)` and the 18-decimal convention are unchanged.

### 4.2 Architectural Changes

| Aspect | V2 | V3 |
|--------|----|----|
| Rate caching | Pool-side caching with configurable duration | Vault-level caching (moved to Vault contract) |
| Rate staleness | Pool decides when to refresh | Vault enforces a global rate cache mechanism |
| Linear Pools | Separate pool type | Deprecated; replaced by "Boosted Pools" as first-class concept |
| Boosted Pools | Composition of Linear + Stable pools | Native pool type with built-in yield wrapping |
| ERC-4626 integration | Via separate rate providers | Native ERC-4626 support -- Vault can directly use `convertToAssets()` |
| Rate provider registration | Per-token in pool constructor | Per-token in pool registration with Vault |

### 4.3 ERC-4626 Native Support in V3

Balancer V3 has first-class support for ERC-4626 tokens. The Vault can automatically use `convertToAssets(1e18)` as the rate for ERC-4626 tokens, eliminating the need for a separate rate provider contract in many cases.

**Implication for our design**: If we build an ERC-4626 vault with a correct `convertToAssets()` implementation, Balancer V3 can consume it directly without us deploying a separate rate provider. However, maintaining a standalone `getRate()` function is still valuable for V2 compatibility and for non-Balancer integrators.

### 4.4 Rate Provider Validation

V3 introduces stricter validation of rate providers during pool registration. The Vault checks that the rate provider returns a non-zero value and that the rate is within reasonable bounds. It also provides a `getRateProviderForToken()` query on the Vault itself.

---

## 5. Known Issues, Criticisms, and Attack Vectors

### 5.1 Rate Manipulation

**The "read-only reentrancy" attack (August 2023)**: Balancer pools that cached rates were vulnerable to a reentrancy attack where an attacker could manipulate the rate between a rate cache update and the subsequent pool operation. This primarily affected pools that read rates during `join`/`exit` callbacks.

**Fix**: Balancer implemented reentrancy guards on the Vault level and ensured rate reads happen before any external calls.

**Relevance to our design**: Our `getRate()` reads from Angstrom's storage via `extsload`. This is a pure SLOAD-based read -- no callbacks, no reentrancy surface. The Angstrom contract's `globalGrowth` is only updated during `execute()` (the bundle settlement), which happens in a controlled context.

### 5.2 Stale Rates

**Problem**: If a rate provider reads from a cached value (e.g., cbETH's `exchangeRate()` is only updated daily), the rate can be stale. An attacker can sandwich the rate update: buy the yield-bearing token before the update (when it's "cheap" per the stale rate), then sell after the update.

**Balancer's mitigation**: Rate caching in the pool itself, with configurable durations. Pools with frequently-updating rate sources use shorter cache durations.

**Relevance to our design**: Angstrom's `globalGrowth` is updated on every bundle settlement (every block, potentially). Between settlements, `growthInside` is constant (it only changes when Angstrom's `execute()` runs). This means our rate is inherently "step-wise" -- it jumps on settlement and is flat between settlements. This is actually fine for a rate provider because:
1. The rate never *decreases* between updates (unlike TWAP oracles)
2. The rate is always a lower bound on the "true" accrued value (any pending but unsettled rewards are not yet reflected)
3. Sandwich attacks around settlement would require knowing the exact reward distribution before it's committed -- the Angstrom nodes don't publish this ahead of time

### 5.3 Rate Provider Revert Handling

**If `getRate()` reverts**: Balancer pools will also revert their swap/join/exit operation. There is no fallback to a default rate or cached value if the live rate call fails.

**Implication**: Our `getRate()` must NEVER revert. The `extsload` call to Angstrom should always succeed (it's just SLOAD), but we should handle the case where the Angstrom contract is not yet initialized for a pool (return 1e18 as the "no yield yet" rate).

### 5.4 Rounding Direction

**Convention**: Rate providers return a rate that, when multiplied by a balance, gives the "true" value. Rounding should be consistent -- Balancer does not specify a rounding direction for `getRate()`, but in practice:
- `getRate()` should round **down** (conservative estimate)
- The pool's scaling math handles rounding direction based on whether the operation is a deposit or withdrawal

**Our case**: Angstrom's accumulators use Q128.128 fixed point. Converting to 18-decimal for `getRate()` involves a right-shift by 128 and scale to 1e18. We should round down in this conversion.

### 5.5 Decimal Mismatch

Rate providers return 18-decimal values. If the underlying token has different decimals (e.g., USDC has 6), the pool's `scalingFactor` handles this separately from the rate. The rate itself is always in 18-decimal "rate space" regardless of the token's decimals.

---

## 6. ERC-4626 Vault as IRateProvider: The Dual Interface

### 6.1 Precedents

Several contracts in production serve as both an ERC-4626 vault and an IRateProvider:

1. **Balancer's `ERC4626RateProvider`**: A separate contract, but it just calls `vault.convertToAssets(1e18)`. If the vault implemented `getRate()` directly, it would be equivalent.

2. **Angle Protocol's `StakedAgEUR`**: An ERC-4626 vault that also exposes a rate function for external consumers.

3. **sDAI itself**: While sDAI doesn't implement `IRateProvider`, its `convertToAssets()` serves the same purpose. The separate `ERC4626RateProvider` is just a thin adapter.

### 6.2 Recommended Implementation for Our Vault

```solidity
contract AngstromRewardVault is ERC4626, IRateProvider {
    // Angstrom oracle adapter for accumulator reads
    AngstromRANOracleAdapter public immutable oracle;
    PoolId public immutable poolId;
    int24 public immutable tickLower;
    int24 public immutable tickUpper;

    // Snapshot of accumulators at vault deployment
    uint256 public immutable deployGrowthInside;
    uint256 public immutable deployGlobalGrowth;

    /// @notice Returns the rate in 18-decimal fixed point.
    /// @dev Rate = 1e18 + (accrued yield per unit of initial deposit).
    ///      This is equivalent to convertToAssets(1e18) but cheaper
    ///      since it avoids the totalSupply division.
    function getRate() external view override returns (uint256) {
        uint256 currentGI = oracle.growthInside(poolId, tickLower, tickUpper);
        uint256 giDelta;
        unchecked {
            giDelta = currentGI - deployGrowthInside;
        }
        // Convert Q128.128 delta to 18-decimal rate
        // rate = 1e18 + (giDelta * 1e18) >> 128
        // The >> 128 converts from Q128.128 to integer,
        // then we scale to 18 decimals relative to initial deposit
        return 1e18 + _q128ToRate(giDelta);
    }

    function _q128ToRate(uint256 q128Value) internal pure returns (uint256) {
        // q128Value is in Q128.128. We want (q128Value / 2^128) * 1e18
        // = q128Value * 1e18 / 2^128
        // Use mulDiv for precision
        return FixedPointMathLib.mulDiv(q128Value, 1e18, 1 << 128);
    }

    function totalAssets() public view override returns (uint256) {
        // Total underlying = initial deposits + accrued rewards
        // accrued rewards = (currentGI - deployGI) * totalLiquidity >> 128
        uint256 currentGI = oracle.growthInside(poolId, tickLower, tickUpper);
        uint256 giDelta;
        unchecked {
            giDelta = currentGI - deployGrowthInside;
        }
        uint256 accrued = X128MathLib.fullMulX128(giDelta, totalSupply());
        return _initialAssets() + accrued;
    }
}
```

### 6.3 getRate() vs convertToAssets() Consistency

For a well-behaved ERC-4626 vault that is also an IRateProvider:

```
getRate() == convertToAssets(1e18)  // MUST hold (up to rounding)
```

If this invariant breaks, integrators will see inconsistent pricing between Balancer pools (which use `getRate()`) and other protocols (which use `convertToAssets()`). This is the single most important correctness property.

---

## 7. Mapping to Angstrom's globalGrowth Accumulator

### 7.1 Accumulator Properties

From the codebase analysis:

| Property | Angstrom `globalGrowth` | Angstrom `growthInside(lower, upper)` |
|----------|------------------------|--------------------------------------|
| Format | Q128.128 (`uint256`) | Q128.128 (`uint256`) |
| Update frequency | Every `execute()` call | Derived from `globalGrowth` + `rewardGrowthOutside` |
| Monotonicity | Strictly non-decreasing | Strictly non-decreasing for a given tick range |
| Scope | Pool-wide (all liquidity) | Specific tick range |
| Storage | `PoolRewards.globalGrowth` | Computed from `rewardGrowthOutside` array |

### 7.2 Which Observable to Use

For an ERC-4626 vault representing a specific position (tick range):

**Use `growthInside(poolId, tickLower, tickUpper)`**, not raw `globalGrowth`.

Rationale:
- The vault wraps a specific liquidity position in a specific tick range
- `growthInside` tells you the reward per unit of liquidity within that range
- `globalGrowth` tells you the reward per unit of liquidity globally (including ranges the vault doesn't cover)
- Using `globalGrowth` would overstate the vault's yield (it includes rewards to ranges outside the vault's position)

**For `getRate()`**: The rate should reflect how much more the vault's shares are worth compared to deployment. This is:
```
rate = 1e18 * (deployLiquidity + accruedRewards) / deployLiquidity
     = 1e18 + (growthInsideDelta * 1e18 / 2^128)
```

Note: This assumes `growthInside` is denominated per unit of liquidity, which it is (see `X128MathLib.flatDivX128(amount, pooLiquidity)` at line 55 of `GrowthOutsideUpdater.sol`).

### 7.3 Gas Cost Analysis

Reading `growthInside` via `AngstromRANOracleAdapter`:

| Operation | Gas Cost |
|-----------|----------|
| `extsload` for `rewardGrowthOutside[tickLower]` | ~2,600 (warm) to ~5,100 (cold) |
| `extsload` for `rewardGrowthOutside[tickUpper]` | ~2,600 (warm) to ~5,100 (cold) |
| `extsload` for `globalGrowth` | ~2,600 (warm) to ~5,100 (cold) |
| `getSlot0` for current tick | ~2,600 (warm) to ~5,100 (cold) |
| Arithmetic (subtraction, comparison) | ~30 |
| **Total** | **~10,800 (warm) to ~20,400 (cold)** |

For comparison:
- wstETH `getRate()`: ~2,600 gas
- sDAI `getRate()`: ~5,000-8,000 gas
- Our `getRate()`: ~10,800-20,400 gas

**Assessment**: This is higher than typical rate providers but still well within acceptable bounds. Balancer's rate caching (both V2 and V3) means this is called infrequently -- once per cache period (e.g., hourly). For direct consumers calling every swap, a rate cache on our side (similar to Balancer's pool-side cache) could reduce this to ~2,600 gas (single SLOAD).

### 7.4 Rate Caching Strategy

Option A: **No cache** (simplest, always fresh)
- `getRate()` always does 3-4 `extsload` calls
- ~11-20k gas per call
- Always accurate to the latest settlement

Option B: **Heartbeat cache** (good tradeoff)
- Cache the rate in a storage slot with a timestamp
- Refresh if `block.timestamp > lastUpdate + heartbeat`
- ~2.6k gas when cached, ~13-23k on refresh
- Risk: rate can be stale by up to `heartbeat` duration

Option C: **Settlement-triggered cache** (most accurate)
- Angstrom's settlement emits no events, but the globalGrowth slot changes
- Could check `globalGrowth != cachedGlobalGrowth` as a freshness signal
- Requires one extra `extsload` but avoids time-based staleness

**Recommendation**: Start with Option A (no cache). The gas cost is acceptable, and it eliminates all staleness concerns. If gas becomes a bottleneck for high-frequency integrators, add Option C as an upgrade.

---

## 8. Design Recommendations

### 8.1 Interface

```solidity
interface IAngstromRewardRateProvider is IRateProvider {
    /// @notice The Angstrom pool this rate provider covers
    function poolId() external view returns (PoolId);

    /// @notice The tick range for which rewards are tracked
    function tickRange() external view returns (int24 lower, int24 upper);

    /// @notice growthInside at deployment time (Q128.128)
    function deployGrowthInside() external view returns (uint256);
}
```

### 8.2 Critical Invariants

1. `getRate() >= 1e18` always (rate never decreases below initial)
2. `getRate() == convertToAssets(1e18)` (consistency with ERC-4626)
3. `getRate()` NEVER reverts (handle uninitialized pools gracefully)
4. Rate increases are bounded by actual Angstrom reward distributions (no phantom yield)

### 8.3 Integration Test Strategy

1. Deploy rate provider + Balancer ComposableStablePool with the rate-provided token
2. Simulate Angstrom settlements that increase `globalGrowth`
3. Verify pool pricing adjusts correctly after rate cache refresh
4. Test edge cases: zero liquidity, tick range fully out of range, first settlement
5. Test the reentrancy surface: can a malicious Angstrom settlement front-run a pool operation?

### 8.4 Security Considerations

1. **Accumulator overflow**: `globalGrowth` is `uint256` in Q128.128. The upper 128 bits represent the integer part. Overflow would require rewards exceeding ~3.4e38 tokens, which is practically impossible.

2. **Tick range migration**: If the vault's tick range becomes inactive (price moves permanently outside), `growthInside` stops increasing. The rate flattens but never decreases. This is correct behavior -- no new yield is earned.

3. **Angstrom upgrade risk**: If Angstrom's storage layout changes, the `extsload`-based oracle adapter would break. The adapter should be upgradeable or the vault should have an escape hatch.

4. **Flash loan attack surface**: Reading from `extsload` is immune to flash loans because the Angstrom accumulator can only be updated by the `execute()` function, which requires node signatures. No flash loan can manipulate `globalGrowth`.

---

## 9. Relevant Source Files

### In This Repository

| File | Role |
|------|------|
| `contracts/src/types/PoolRewards.sol` | `globalGrowth` and `growthInside` accumulator structure |
| `contracts/src/modules/GrowthOutsideUpdater.sol` | Reward distribution logic (how `globalGrowth` is incremented) |
| `contracts/src/ran.sol` | `AngstromRANOracleAdapter` -- external reader for accumulator state via `extsload` |
| `contracts/src/types/NoteSnapshot.sol` | Per-position accumulator snapshots (birth accumulators) |
| `contracts/src/modules/AccrualManagerMod.sol` | `settleAndCheckpoint()` and `viewAccruedRatio()` -- 80% of the vault math |
| `contracts/src/libraries/X128MathLib.sol` | Q128.128 arithmetic (`flatDivX128`, `fullMulX128`) |

### Balancer Contracts to Study

| Contract | Repository | Purpose |
|----------|------------|---------|
| `IRateProvider.sol` | `balancer-v2-monorepo/pkg/interfaces` | The interface to implement |
| `ComposableStablePool.sol` | `balancer-v2-monorepo/pkg/pool-stable` | How rates are consumed in StableMath |
| `LinearPool.sol` | `balancer-v2-monorepo/pkg/pool-linear` | How rates scale wrapped balances |
| `ERC4626RateProvider.sol` | `balancer-v2-monorepo/pkg/pool-utils` | Generic ERC-4626 to rate provider adapter |
| `WstETHRateProvider.sol` | `balancer-v2-monorepo/pkg/pool-utils` or `lido-dao` | Production rate provider example |
| `IRateProvider.sol` (V3) | `balancer-v3-monorepo/pkg/interfaces` | V3 version (identical interface) |

---

## 10. Implementation Checklist

- [ ] Define `IAngstromRewardRateProvider extends IRateProvider`
- [ ] Implement `getRate()` reading from `AngstromRANOracleAdapter.growthInside()`
- [ ] Convert Q128.128 delta to 18-decimal rate via `mulDiv(delta, 1e18, 2^128)`
- [ ] Ensure `getRate() >= 1e18` invariant (clamp if needed for rounding)
- [ ] Implement as part of the ERC-4626 vault (dual interface)
- [ ] Ensure `getRate() == convertToAssets(1e18)` consistency
- [ ] Add `getRate()` never-revert guarantee (handle uninitialized case)
- [ ] Write Balancer integration test (ComposableStablePool + rate-provided token)
- [ ] Gas benchmark: measure `getRate()` cost, decide if caching is needed
- [ ] Security review: reentrancy, flash loan, accumulator overflow, stale rate
