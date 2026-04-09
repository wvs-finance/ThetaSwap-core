# Token Supply Mutation Research: Bonding Curves, Rebasing, and Custom Supply Functions

**Date**: 2026-04-09
**Context**: ERC-4626 vault where shares = f(deposits, lpRewardAccumulator)
**Codebase**: ThetaSwap RaN (Range Accrual Notes) on Angstrom

---

## Executive Summary

The design space for "custom functions that drive token supply changes" spans four distinct paradigms: (1) bonding curves where price = f(supply), (2) rebasing tokens where balances mutate, (3) ERC-4626 share-price appreciation where totalAssets grows, and (4) hybrid models combining accumulator-driven yield with share math. For the ThetaSwap use case -- an ERC-4626 vault whose yield is driven by Angstrom's growthInside accumulator -- **the share-price-appreciation model (paradigm 3) is the correct choice**, with the supply function implicitly defined by `totalAssets() = deposits + f(growthInsideDelta)`. This report catalogs the full design space, the mathematical properties each approach requires, and the concrete libraries and protocols implementing them.

---

## Part 1: Bonding Curves / Token Bonding Curves (TBCs)

### 1.1 Core Concept

A bonding curve defines a deterministic relationship between token supply `S` and token price `P`:

```
P(S) = f(S)
```

The reserve (collateral locked) is the integral of the price function:

```
R(S) = integral from 0 to S of f(s) ds
```

Minting `dS` tokens costs `R(S + dS) - R(S)`. Burning returns the same amount. The curve is the "market maker" -- no counterparty needed.

### 1.2 Common Curve Shapes

| Curve | Price Function P(S) | Reserve Function R(S) | Properties |
|-------|--------------------|-----------------------|------------|
| Linear | a*S + b | a*S^2/2 + b*S | Simplest; price grows linearly with adoption |
| Polynomial | a*S^n | a*S^(n+1)/(n+1) | Steepness controlled by exponent n |
| Exponential | a*e^(b*S) | (a/b)*e^(b*S) | Aggressive price growth; can overflow |
| Square root | a*sqrt(S) | (2a/3)*S^(3/2) | Sublinear growth; favors early entrants less |
| Logarithmic | a*ln(S+1) + b | a*((S+1)*ln(S+1) - S) + b*S | Diminishing price growth |
| Sigmoid | L/(1+e^(-k*(S-S0))) | Complex (no closed form) | S-shaped; bounded price ceiling |
| Bancor (power) | R/(S*CW) where CW=connector weight | R = R0*(S/S0)^(1/CW) | The production standard |

### 1.3 Bancor Formula

**Repository**: `github.com/bancorprotocol/contracts-solidity` (historical; also `bancor-protocol/contracts-v3`)
**License**: Apache-2.0

The Bancor formula is the most widely deployed bonding curve math:

```
Return = S * ((1 + dR/R)^CW - 1)
```

Where CW (connector weight, also called reserve ratio) in [0,1] controls the curve shape:
- CW = 1.0: constant price (stablecoin)
- CW = 0.5: linear price (quadratic reserve)
- CW = 0.1: steep exponential-like growth

**Key file**: `BancorFormula.sol` -- implements the power function via integer approximation (no floating point). Uses a lookup table + Taylor series for `power(baseN, baseD, expN, expD)`.

**Mathematical properties enforced**:
- Monotonicity: price strictly increases with supply (for CW < 1)
- Integrability: closed-form reserve computation
- Solvency invariant: reserve always exactly covers all burns at current curve price
- No admin key: curve is immutable once deployed

**Edge cases**:
- Zero supply: handled by initial reserve requirement
- Overflow: BancorFormula uses careful intermediate precision (256-bit)
- Front-running: NOT handled by Bancor itself; requires batching or commit-reveal

### 1.4 Simon de la Rouviere's Continuous Token Model

**Reference**: "Tokens 2.0: Curved Token Bonding" (2017, Medium)
**Repository**: `github.com/simondlr/thisartworkisalwaysonsale` (production use)

The original formulation. Key insight: bonding curves create "automated market makers for token supply." The price function is also the marginal cost of minting.

Rouviere's formulation uses polynomial curves with explicit integral computation:
```
P(S) = m * S^n  =>  Cost(S1, S2) = m/(n+1) * (S2^(n+1) - S1^(n+1))
```

### 1.5 Solidity Libraries for Bonding Curve Math

| Library | Curve Types | Precision | License | Notes |
|---------|-------------|-----------|---------|-------|
| `BancorFormula.sol` | Power (via CW) | ~128-bit intermediate | Apache-2.0 | Production-hardened; ~15k gas |
| `ABDKMath64x64` | Any (provides exp, ln, pow) | 64.64 fixed-point | BSD-4-Clause | General-purpose; not curve-specific |
| `PRBMath` (Paul R. Berg) | Any (provides exp2, log2, pow, sqrt) | SD59x18 / UD60x18 | MIT | Modern; well-tested; ~5-10k gas per op |
| Solady `FixedPointMathLib` | mulDiv, sqrt, expWad, lnWad | 256-bit intermediates | MIT | Lowest gas; used in this codebase |
| `yieldspace-v2` (Yield Protocol) | ts-specific (y^(1-t) + x^(1-t) = k) | Custom | BUSL-1.1 | Yield-space invariant for time-weighted |

**Recommendation for ThetaSwap**: Solady `FixedPointMathLib` is already a dependency. Use `mulDiv`, `lnWad`, `expWad` for any curve evaluation needed. No need to add ABDKMath or PRBMath.

### 1.6 Mathematical Properties Required for Bonding Curves

For a bonding curve P(S) to be economically sound:

1. **Monotonicity**: P'(S) >= 0 (price never decreases as supply grows). Strict monotonicity (P'(S) > 0) prevents zero-cost minting.
2. **Integrability**: P(S) must have a computable integral R(S) for on-chain reserve calculation.
3. **Continuity**: P(S) must be continuous to prevent arbitrage at discontinuities.
4. **Positive definiteness**: P(S) > 0 for all S > 0.
5. **Reserve solvency**: R(S) >= sum of all burns at curve prices. Automatically satisfied if burns follow the same curve.
6. **Convexity** (P''(S) >= 0): ensures early minters get better prices (incentive alignment for bootstrapping). Not strictly required but economically desirable.

### 1.7 Relevance to ThetaSwap Use Case

**Low-Medium**. Bonding curves model supply as the independent variable and price as the dependent variable. In the ThetaSwap vault, the independent variable is the external observable (growthInside accumulator), not the supply itself. However, the mathematical framework (monotonic functions, integrability for reserve computation, fixed-point arithmetic libraries) is directly applicable.

---

## Part 2: Launch / Creation Markets

### 2.1 pump.fun Style

**Pattern**: Constant-product bonding curve on (virtualReserves, supply).

```
x * y = k    where x = virtual token reserve, y = virtual SOL reserve
price = y / x
```

Minting tokens reduces x, increasing price. When supply hits a threshold, liquidity migrates to a real AMM (Raydium). The "curve" is actually a standard xy=k AMM where one side is virtual.

**Solidity implementations**: Multiple clones exist on EVM chains (`pump.fun` itself is Solana/Rust). Key EVM variants:
- `friend.tech` (Base): `price = supply^2 / 16000` (pure quadratic, no virtual reserves)
- Various "fair launch" contracts on Ethereum/Base using UniV3 as the graduation target

**Mathematical properties**:
- Monotonic by construction (xy=k guarantees price increases with supply)
- Bounded: price goes to infinity as x approaches 0
- Integral: closed-form (logarithmic for constant-product)
- Front-running: NOT handled; sandwich attacks are the primary attack vector

### 2.2 friend.tech Bonding Curve

```solidity
function getPrice(uint256 supply, uint256 amount) public pure returns (uint256) {
    uint256 sum1 = supply == 0 ? 0 : (supply - 1) * supply * (2 * (supply - 1) + 1) / 6;
    uint256 sum2 = (supply + amount - 1) * (supply + amount) * (2 * (supply + amount - 1) + 1) / 6;
    return (sum2 - sum1) * 1 ether / 16000;
}
```

This is the sum of squares: `Cost(S1, S2) = sum_{i=S1}^{S2-1} i^2 / 16000`. Discrete (integer supply), quadratic price growth.

### 2.3 Augmented Bonding Curves (Commons Stack)

**Repository**: `github.com/commons-stack/augmented-bonding-curve`
**License**: GPL-3.0

Extension of Bancor curves with:
- A "hatch" phase (initial contributors get tokens at a discount)
- A "tribute" on each transaction (portion goes to a funding pool, not the reserve)
- Split between reserve and funding pool controlled by governance

**Mathematical modification**: The tribute introduces a wedge between buy and sell prices:
```
Buy price = P(S) / (1 - tributeRate)
Sell price = P(S)
```

This means the reserve is undercollateralized relative to the curve -- burns return less than the curve would suggest. The spread creates a "funding" mechanism.

**Relevance**: Low for ThetaSwap directly, but the concept of a "wedge function" between deposit and withdrawal value is structurally similar to how LP fee accrual creates a spread between entry and exit share price.

### 2.4 Token Curated Registries (TCRs) with Bonding Curves

**Reference**: Mike Goldin's "Token-Curated Registries 1.0" (2017)

TCRs use bonding curves for curation markets: stake tokens to curate a list, bonding curve prices reflect curation demand. The supply function here is secondary to the staking/challenge mechanism.

**Relevance**: Low.

---

## Part 3: Rebasing / Elastic Supply Tokens

### 3.1 Ampleforth (AMPL)

**Repository**: `github.com/ampleforth/ampleforth-contracts`
**License**: GPL-3.0

**Mechanism**: Daily rebase adjusts all balances proportionally to target a $1 TWAP.

```
rebaseRatio = targetPrice / currentTWAP
newSupply = oldSupply * rebaseRatio
for each holder: newBalance = oldBalance * rebaseRatio
```

**Implementation pattern**: `UFragments.sol` uses a `_gonsPerFragment` scaling factor:
```solidity
// Internal balances stored in "gons" (fixed representation)
mapping(address => uint256) _gonBalances;
uint256 _gonsPerFragment;

function balanceOf(address who) public view returns (uint256) {
    return _gonBalances[who] / _gonsPerFragment;
}

function rebase(uint256 epoch, int256 supplyDelta) external onlyPolicy {
    _totalSupply = _totalSupply + supplyDelta;
    _gonsPerFragment = TOTAL_GONS / _totalSupply;
}
```

**Mathematical properties**:
- **Share preservation**: Each holder's fraction of total supply is preserved across rebases. `balanceOf(user) / totalSupply()` is invariant.
- **Monotonicity**: NOT enforced -- supply can decrease (negative rebase).
- **Continuity**: Discrete (daily), not continuous.
- **Oracle dependency**: Requires TWAP oracle; vulnerable to oracle manipulation.
- **Composability problem**: Most DeFi protocols (Uniswap, Aave, etc.) break when balances change without transfers. This is the fundamental problem with rebasing tokens.

### 3.2 Olympus (OHM)

**Repository**: `github.com/OlympusDAO/olympus-contracts`
**License**: AGPL-3.0

**Mechanism**: Rebasing distributes treasury yield to stakers. sOHM (staked OHM) rebases upward based on reward rate.

```
rebaseAmount = OHM_in_staking_contract - sOHM_total_supply
rebaseRatio = 1 + rebaseAmount / sOHM_total_supply
```

The newer gOHM (governance OHM) is a non-rebasing wrapper:
```
gOHM_balance = sOHM_balance / index
```

This is exactly the ERC-4626 pattern: gOHM is the "share" token, sOHM is the rebasing underlying, and the index is totalAssets/totalShares.

**Key insight**: OHM v2 abandoned rebasing for the wrapped (index-based) approach because rebasing breaks composability.

### 3.3 Aave aTokens

**Repository**: `github.com/aave/aave-v3-core`
**License**: BUSL-1.1

**Mechanism**: aToken balances grow continuously based on the liquidity index:

```solidity
function balanceOf(address user) public view returns (uint256) {
    return _scaledBalance[user].rayMul(pool.getReserveNormalizedIncome(asset));
}
```

Where `normalizedIncome` is a monotonically increasing accumulator:
```
normalizedIncome(t) = normalizedIncome(t-1) * (1 + liquidityRate * dt / SECONDS_PER_YEAR)
```

**Mathematical properties**:
- **Monotonicity**: normalizedIncome only increases (interest rate >= 0).
- **Continuity**: Piecewise linear between updates; updated on every interaction.
- **Precision**: RAY (1e27) fixed-point arithmetic via `WadRayMath.sol`.
- **Composability**: Better than AMPL because the scaled balance is stored and the index is a view function, but still causes issues with naive ERC20 integrations that cache balanceOf.

**Relevance to ThetaSwap**: HIGH. The Aave pattern of `scaledBalance * accumulatorIndex` is structurally identical to how ThetaSwap's NoteSnapshot works: `entryGrowthInside` is the "last index" and `currentGrowthInside` is the "current index". The delta gives accrued yield.

### 3.4 Lido stETH

**Repository**: `github.com/lidofinance/lido-dao`
**License**: GPL-3.0

**Mechanism**: Daily oracle report updates `totalPooledEther`, causing all stETH balances to rebase:

```solidity
function balanceOf(address _account) public view returns (uint256) {
    return _sharesOf(_account) * _getTotalPooledEther() / _getTotalShares();
}
```

This is precisely ERC-4626 math: `balanceOf = shares * totalAssets / totalShares`.

Lido also provides **wstETH** -- a non-rebasing wrapper that accumulates value (like gOHM). wstETH is an ERC-4626-like share token.

**Key lesson**: Every mature rebasing protocol eventually ships a non-rebasing wrapper because DeFi composability demands it.

### 3.5 Mathematical Framework for Rebasing

A rebase operation must satisfy the **share preservation invariant**:

```
For all holders h:
    balanceOf(h) / totalSupply() is unchanged by the rebase
    (assuming no deposits/withdrawals during the rebase)
```

This is equivalent to saying: the rebase is a uniform scaling of all balances by a factor `r`:
```
newBalance(h) = oldBalance(h) * r
newTotalSupply = oldTotalSupply * r
```

The scaling factor r can be derived from any external observable:
```
r = f(observable_new) / f(observable_old)
```

For this to be well-defined:
1. `f` must be positive-valued (balances cannot be negative)
2. `f` should be monotonically increasing if the observable only increases (supply should not shrink if yield only accrues)
3. `f(0) > 0` to avoid division by zero at genesis
4. `f` should be bounded above if the observable can grow unboundedly (to prevent overflow)

---

## Part 4: ERC-4626 Share Price Mutation

### 4.1 The Two Approaches

ERC-4626 represents yield via the exchange rate between shares and assets:

```
assets = shares * totalAssets / totalShares
shares = assets * totalShares / totalAssets
```

There are exactly two ways to represent yield accrual:

**Approach A: Share-price appreciation (totalAssets grows, totalShares constant)**
```
// At time 0: totalAssets = 100, totalShares = 100, price = 1.0
// At time 1: totalAssets = 110, totalShares = 100, price = 1.1
```
The share price rises. Each share is worth more assets. This is the standard ERC-4626 pattern.

**Approach B: Supply rebase (totalShares grows, totalAssets constant)**
```
// At time 0: totalAssets = 100, totalShares = 100, price = 1.0
// At time 1: totalAssets = 100, totalShares = 110, price = 0.909...
// But each holder has 10% more shares
```
More shares are minted to existing holders. Share price stays constant (or near it). This is the rebasing pattern.

**Mathematical equivalence**: Both approaches produce the same `assets = shares * totalAssets / totalShares` for each holder. The difference is representational:
- Approach A: share count is stable (good for DeFi composability)
- Approach B: share price is stable (good for UX -- "1 share = 1 dollar")

### 4.2 Why Share-Price Appreciation Wins

For DeFi composability, Approach A dominates:

1. **ERC20 compatibility**: No balance changes without transfers. All ERC20 integrations work.
2. **Accounting simplicity**: Share count is immutable after mint. PnL = (exitPrice - entryPrice) * shares.
3. **Gas efficiency**: No rebase transaction needed. Yield accrues implicitly.
4. **Oracle simplicity**: One number (share price) captures all yield history.
5. **Composability**: Can be used as collateral in Aave, Compound, etc. without special adapters.

### 4.3 The totalAssets() Override Pattern

The canonical ERC-4626 approach to custom yield functions:

```solidity
contract CustomVault is ERC4626 {
    function totalAssets() public view override returns (uint256) {
        return _deposits + _yieldFromExternalObservable();
    }

    function _yieldFromExternalObservable() internal view returns (uint256) {
        // YOUR CUSTOM FUNCTION HERE
        // e.g., read Angstrom growthInside accumulator and compute accrued fees
    }
}
```

This is the simplest and most composable approach. The custom function `_yieldFromExternalObservable()` is where all the design freedom lives.

### 4.4 Key ERC-4626 Implementations

| Implementation | totalAssets() Pattern | Precision | License |
|---------------|----------------------|-----------|---------|
| OpenZeppelin ERC4626 | Virtual, user overrides | Standard uint256 | MIT |
| Solady ERC4626 | Virtual, gas-optimized mulDiv | Full 512-bit intermediate | MIT |
| Solmate ERC4626 | Abstract (must implement) | Standard | MIT |
| Yearn V3 | `totalIdle + totalDebt` (periodic harvest) | Standard | AGPL-3.0 |
| MetaMorpho | Sum over market supply positions | Standard | GPL-2.0 |

**Recommendation**: Solady's ERC4626 base. Already a dependency. Uses `mulDiv` for share/asset conversion, matching the precision of X128MathLib already in this codebase.

### 4.5 Mathematical Properties for totalAssets() Functions

For `totalAssets() = deposits + f(observable)` to be safe:

1. **Non-negativity**: `f(observable) >= 0` always. totalAssets must never be less than 0.
2. **Monotonicity**: If the observable only increases, f should only increase. Otherwise share price could decrease, enabling sandwich attacks on deposits.
3. **Continuity**: f should not have discontinuities that could be exploited (e.g., a step function that jumps at specific accumulator values).
4. **Boundedness**: f should not overflow uint256 for any realistic observable value. With Q128.128 accumulators and 256-bit intermediates, this requires careful analysis.
5. **Solvency**: `totalAssets()` must reflect actually claimable value. If f(observable) exceeds actual claimable rewards, the vault is insolvent.
6. **Atomicity**: f(observable) and the actual claimable rewards must update atomically, or sandwiching is possible.

---

## Part 5: Mathematical Properties of Supply Functions (Deep Dive)

### 5.1 Formal Framework

Let `O(t)` be an external observable (e.g., Angstrom growthInside accumulator) at time t.
Let `S(t)` be the token supply (or equivalently, totalAssets in an ERC-4626).
Let `f: R+ -> R+` be the supply function such that `S(t) = f(O(t))` or `totalAssets(t) = f(O(t))`.

### 5.2 Required Properties

**Property 1: Monotonicity**
```
If O(t1) <= O(t2) then f(O(t1)) <= f(O(t2))
```
*Why*: If the observable increases (more fees accrued), share price should not decrease. A decrease enables a sandwich attack: attacker deposits before the decrease, withdraws after the next increase.

*Strength levels*:
- Weak monotonicity: `f(a) <= f(b)` for `a <= b` (non-decreasing). Allows flat regions.
- Strict monotonicity: `f(a) < f(b)` for `a < b`. Prevents stuck share prices.
- For ERC-4626 vaults, weak monotonicity suffices (share price can plateau during low-fee periods).

**Property 2: Continuity**
```
For all epsilon > 0, there exists delta > 0 such that |O1 - O2| < delta implies |f(O1) - f(O2)| < epsilon
```
*Why*: Discontinuities create exploitable jumps. If share price jumps from 1.0 to 1.1 at a specific accumulator value, an attacker can deposit just before the jump and withdraw just after.

*Practical note*: On-chain, all values are discrete (uint256). True continuity is impossible. The relevant property is that f should not have large jumps for small input changes. Specifically, for Angstrom accumulators updated per block, the maximal single-block change in f should be bounded.

**Property 3: Lipschitz Continuity (Bounded Rate of Change)**
```
|f(O1) - f(O2)| <= L * |O1 - O2| for some constant L
```
*Why*: Bounds the maximum yield per unit of observable change. Prevents runaway appreciation that could break integrations or create extreme MEV.

*For the ThetaSwap case*: L should be bounded by the maximum possible fee accrual per unit of growthInside delta, which is itself bounded by the liquidity and fee tier.

**Property 4: Positive Definiteness**
```
f(O) > 0 for all O >= 0
```
*Why*: totalAssets must be positive for share/asset conversion to be well-defined. Division by zero in `shares = assets * totalShares / totalAssets`.

*Implementation*: Ensure `f(0) = initialDeposits > 0`. The vault should not be deployed with zero assets.

**Property 5: Overflow Safety (Boundedness in Machine Arithmetic)**
```
f(O) < 2^256 for all achievable O
```
*Why*: Overflow causes totalAssets to wrap around, breaking solvency.

*For Q128.128 accumulators*: growthInside can theoretically reach 2^256 - 1. If f is linear, `f(O) = deposits + O * liquidity >> 128`, then overflow is possible if liquidity * growthInsideDelta exceeds 2^384 before the right shift. X128MathLib.fullMulX128 handles this with 512-bit intermediate, reverting on overflow. This is the correct behavior.

**Property 6: Additivity / Superposition (for Multi-Position Vaults)**
```
f(O_total) = sum_i f_i(O_i) where O_i are per-position observables
```
*Why*: If the vault holds multiple LP positions across different tick ranges, the total yield should be the sum of per-position yields. This requires f to be additive (linear) in the observable.

*This is satisfied by the Angstrom accumulator model*: total accrued fees = sum over positions of (growthInsideDelta_i * liquidity_i) >> 128.

### 5.3 Interaction with Solvency Invariants

The critical solvency invariant for an ERC-4626 vault:

```
totalAssets() >= sum over all share holders of (shares[h] * totalAssets() / totalShares())
```

This is trivially satisfied (it's an equality). The real invariant is:

```
totalAssets() <= actualClaimableValue()
```

Where `actualClaimableValue()` is the sum the vault could actually withdraw from its positions. If `f(observable)` overestimates claimable value, the vault is insolvent.

For the ThetaSwap case, this means:
```
totalAssets() = deposits + settleAndCheckpoint() <= deposits + actualFeesClaimed
```

The `settleAndCheckpoint()` function in AccrualManagerMod.sol computes `(growthInsideDelta * holderBalance) >> 128`. This is the exact fee amount owed, not an approximation. So the solvency invariant is automatically satisfied if fees are actually claimable.

### 5.4 Dilution and Anti-Dilution

When new shares are minted (new depositor), existing holders are diluted if and only if:
```
mintPrice < currentSharePrice
```

ERC-4626 prevents this by computing mint amount as:
```
shares = assets * totalShares / totalAssets
```

This ensures the new depositor gets shares at the current price, preserving existing holders' value. No dilution occurs regardless of the supply function.

When the supply function causes totalAssets to increase (fee accrual), all holders benefit proportionally. No anti-dilution mechanism is needed because ERC-4626's pro-rata math handles it automatically.

---

## Part 6: Concrete Protocol Patterns (Detailed)

### 6.1 Panoptic CollateralTracker

**Repository**: `github.com/panoptic-labs/panoptic-v1-core`
**License**: BUSL-1.1
**Local path**: `contracts/lib/2025-12-panoptic/`

**Pattern**: ERC-4626 vault where `totalAssets = deposits + assetsInAMM + unrealizedPremium`.

The CollateralTracker is the closest production pattern to what ThetaSwap needs:
- It wraps Uniswap V4 LP positions
- yield comes from fee accumulators (feeGrowthInside)
- It uses the share-price-appreciation model
- totalAssets() reads live accumulator values

**Key functions**:
```solidity
function totalAssets() public view returns (uint256) {
    return _internalBalance() + _poolBalance();
}
// Where _poolBalance() reads Uniswap accumulators
```

**Relevance**: CRITICAL -- structurally identical to ThetaSwap's problem.

### 6.2 Bunni V2

**Repository**: `github.com/Bunni-xyz/bunni`
**License**: BSL-1.1

**Pattern**: ERC-4626 wrapping Uniswap V4 concentrated liquidity with auto-compounding.

Bunni reads `feeGrowthInside0X128` and `feeGrowthInside1X128` from Uniswap V4, exactly as ThetaSwap reads `growthInside` from Angstrom. The vault's totalAssets includes uncollected fees computed from the accumulator delta.

**Mathematical framework**:
```
unclaimedFees0 = (feeGrowthInside0_current - feeGrowthInside0_last) * liquidity / 2^128
totalAssets = token0Balance + token1Balance_in_token0_terms + unclaimedFees0 + unclaimedFees1
```

### 6.3 Balancer Rate Providers

**Repository**: `github.com/balancer/balancer-v2-monorepo` (also v3)
**License**: GPL-3.0

**Pattern**: Single-function oracle interface:
```solidity
interface IRateProvider {
    function getRate() external view returns (uint256);
}
```

Rate providers abstract any yield source into a single monotonically-increasing number. This is used by Balancer's boosted pools and linear pools to integrate yield-bearing tokens.

**Relevance**: HIGH as an interface pattern. The ThetaSwap vault could expose an `IRateProvider` to enable integration with Balancer and other protocols that consume rate oracles.

### 6.4 Yearn V3 Tokenized Strategy

**Repository**: `github.com/yearn/tokenized-strategy`
**License**: AGPL-3.0

**Pattern**: Periodic "harvest" where a keeper calls `report()`:
```solidity
function report() external onlyKeeper returns (uint256 profit, uint256 loss) {
    // Read external yield source
    // Update totalAssets
    // Collect management/performance fees
}
```

**Mathematical model**: Push-based (keeper triggers update) vs pull-based (totalAssets() reads live). Push model has latency but lower gas per read. Pull model is always accurate but costs more per view call.

**Relevance**: MEDIUM. The ThetaSwap accumulator model is inherently pull-based (growthInside is always live). A push model would add unnecessary latency and keeper dependency.

### 6.5 Yield Protocol YieldSpace

**Repository**: `github.com/yieldprotocol/yieldspace-v2`
**License**: BUSL-1.1

**Pattern**: Time-weighted AMM invariant:
```
x^(1-t) + y^(1-t) = k
```

Where `t` is time to maturity. This creates a bonding curve whose shape changes over time -- flattening as maturity approaches. Not directly a supply mutation pattern, but relevant as a mathematical framework for time-dependent pricing functions.

**Mathematical properties**:
- The invariant transitions from constant-product (t=0) to constant-sum (t=1)
- This is a parametric family of bonding curves indexed by time
- The time parameter is analogous to ThetaSwap's accumulator parameter

**Relevance**: MEDIUM. The concept of a "parametric family of curves indexed by an external observable" is the mathematical generalization of what ThetaSwap needs.

---

## Part 7: Token Engineering Frameworks and Tooling

### 7.1 cadCAD

**Repository**: `github.com/cadCAD-org/cadCAD`
**License**: MIT (Python)

Python-based simulation framework for modeling tokenomics. Can simulate:
- Bonding curve behavior under various demand profiles
- Rebase mechanics and their interaction with DeFi protocols
- Supply function parameter sensitivity analysis

**Relevance**: MEDIUM. Useful for parameter selection and attack simulation, but not for on-chain implementation.

### 7.2 Token Engineering Commons (TEC)

**Repository**: `github.com/CommonsBuild/commons-config-dashboard`

Provides:
- Augmented bonding curve parameter configuration tools
- Conviction voting mechanics
- Token flow simulation

**Relevance**: LOW for implementation, but the TEC's documentation on bonding curve parameter selection is valuable reference material.

### 7.3 Formal Verification Approaches

**Invariant testing (Foundry)**:
```solidity
function invariant_totalAssetsMonotonicallyIncreasing() public {
    assertGe(vault.totalAssets(), lastTotalAssets);
    lastTotalAssets = vault.totalAssets();
}
```

**Symbolic execution (Halmos, KEVM/Kontrol)**:
```
forall observable1 <= observable2:
    totalAssets(observable1) <= totalAssets(observable2)
```

This codebase already uses `kontrol-cheatcodes` (per CLAUDE.md), so Kontrol-based verification of monotonicity is the natural approach.

### 7.4 Economic Attack Vectors

| Attack | Mechanism | Mitigation |
|--------|-----------|------------|
| Sandwich on rebase | Deposit before rebase, withdraw after | Use share-price model (no discrete rebase) |
| Oracle manipulation | Manipulate growthInside to inflate totalAssets | Angstrom's growthInside is protocol-controlled, not user-manipulable |
| Donation attack | Donate assets to vault, inflate share price | ERC-4626 "virtual shares" offset (OZ 5.0+, Solady) |
| First depositor | Deposit 1 wei, donate to inflate, grief next depositor | Virtual shares/assets (Solady default) |
| Rounding exploit | Exploit rounding in share/asset conversion | mulDiv with proper rounding direction (Solady) |
| Front-running deposit | Deposit before a large yield event | Yield accrues continuously (accumulator model), no discrete events to front-run |

---

## Part 8: Solidity Libraries and Tooling (Comprehensive)

### 8.1 Fixed-Point Math Libraries

| Library | Key Functions | Precision | Gas | License | In Codebase? |
|---------|--------------|-----------|-----|---------|--------------|
| Solady FixedPointMathLib | mulDiv, mulDivUp, sqrt, expWad, lnWad, powWad | 256/512-bit | Lowest | MIT | YES |
| X128MathLib (Angstrom) | flatDivX128, fullMulX128 | Q128.128 native | Very low | MIT | YES |
| RayMathLib (Angstrom) | mulRayDown/Up, divRayDown/Up | RAY (1e27) | Low | MIT | YES |
| PRBMath | SD59x18, UD60x18 full suite | 59.18 decimal | Medium | MIT | No |
| ABDKMath64x64 | exp, ln, pow, sqrt in 64.64 | 64.64 fixed | Medium | BSD | No |
| WadRayMath (Aave) | wadMul, rayMul, rayDiv | WAD/RAY | Medium | BUSL | No |

**Recommendation**: The codebase already has three math libraries covering all needed operations. No additional dependencies needed.

### 8.2 ERC20 Supply Modification Extensions

| Extension | What It Does | License | Relevance |
|-----------|-------------|---------|-----------|
| OZ ERC20Burnable | Public burn function | MIT | LOW -- vault controls burns |
| OZ ERC20Capped | Max supply cap | MIT | LOW -- not a cap issue |
| OZ ERC20Snapshot | Historical balance snapshots | MIT | MEDIUM -- useful for governance |
| Solady ERC4626 | Virtual shares/assets, mulDiv conversion | MIT | HIGH -- recommended base |

### 8.3 Curve Registry / Factory Patterns

No production "curve registry" exists as a standalone library. The closest patterns:

1. **Balancer WeightedPool factory**: Each pool has configurable weights (analogous to Bancor CW). The "curve" is selected at deployment via parameters.
2. **Uniswap V4 Hooks**: The hook mechanism allows custom curve logic per pool. This is the most general "pluggable curve" pattern in production.
3. **Diamond pattern with curve facets**: A vault could use the diamond pattern (EIP-2535) to swap curve implementations. This codebase already uses diamond storage (`keccak256` slot hashing, per CLAUDE.md).

**Recommendation for ThetaSwap**: Use a simple `totalAssets()` override rather than a pluggable curve factory. The relationship between growthInside and yield is fixed by Angstrom's protocol design -- there is no need for runtime curve selection.

---

## Part 9: Academic and Research References

### 9.1 Foundational Works

1. **Vitalik Buterin, "On Path Independence"** (2017): Establishes that bonding curves must be path-independent (final state depends only on total supply, not the sequence of mints/burns). This is automatically satisfied by any deterministic f(S).

2. **Simon de la Rouviere, "Tokens 2.0: Curved Token Bonding"** (2017): The original bonding curve formulation. Polynomial curves with explicit integrals.

3. **Zargham, Shorish, Paruch, "From Curved Bonding to Configuration Spaces"** (2020): Formalizes bonding curves using differential geometry. Key insight: the set of all bonding curves forms a configuration space, and the curve parameters define a manifold. Token engineering is navigation on this manifold.

4. **Zargham et al., "Economic Games as Estimators"** (2019): Framework for analyzing token mechanisms as parameter estimation games. Relevant for understanding how supply functions create incentive structures.

### 9.2 AMM-Bonding Curve Equivalence

**Key insight**: AMM invariants and bonding curves are the same mathematical object.

An AMM with invariant `phi(x, y) = k` defines an implicit price function:
```
P = -dx/dy = (dphi/dy) / (dphi/dx)
```

A bonding curve with price function `P(S)` and reserve `R(S)` defines an implicit invariant:
```
phi(S, R) = R - integral(P(s), 0, S) = 0
```

These are dual representations. Uniswap's xy=k is a bonding curve with `P(S) = k/S^2` and `R(S) = k/S`.

**Relevance to ThetaSwap**: The Angstrom AMM's invariant determines the fee accumulation rate, which determines the supply function. The supply function is not independent of the AMM -- it is derived from it.

### 9.3 Yield-Bearing Token Standards

1. **ERC-4626**: The standard. Tokenized vaults with share/asset conversion.
2. **ERC-7535**: Multi-asset vault extension. Allows vaults with heterogeneous assets.
3. **ERC-7575**: Decoupled share/vault. Share token is separate from vault logic.

For ThetaSwap, ERC-4626 suffices. The vault has a single asset (the LP position's underlying token) and a single share token.

---

## Part 10: Synthesis and Recommendations for ThetaSwap

### 10.1 The Design Decision

Given the existing codebase (AccrualManagerMod, AngstromRANOracleAdapter, X128MathLib, Solady), the recommended architecture is:

```
ERC-4626 Vault (Solady base)
  |
  +-- totalAssets() = deposits + accruedFees()
  |
  +-- accruedFees() = sum over positions of:
  |       (currentGrowthInside - entryGrowthInside) * positionLiquidity >> 128
  |
  +-- currentGrowthInside: read from AngstromRANOracleAdapter.growthInside()
  +-- entryGrowthInside: stored in NoteSnapshot
```

### 10.2 The Supply Function

The effective supply function is:

```
totalAssets(t) = D + sum_i [ (GI_i(t) - GI_i(t0)) * L_i / 2^128 ]
```

Where:
- `D` = total deposits
- `GI_i(t)` = growthInside for position i at time t
- `GI_i(t0)` = growthInside for position i at entry time
- `L_i` = liquidity of position i

**Properties satisfied**:
- Monotonicity: GI only increases (fees only accrue), so totalAssets only increases. CHECK.
- Continuity: GI updates per Angstrom bundle (per block). Changes are bounded by max fee per block. CHECK.
- Positive definiteness: D > 0 at genesis, fee term >= 0. CHECK.
- Boundedness: X128MathLib.fullMulX128 reverts on overflow. CHECK.
- Solvency: Fee amount exactly matches claimable value from settleAndCheckpoint(). CHECK.
- Additivity: Linear in positions. CHECK.
- Lipschitz: Bounded by max(L_i) * max(dGI per block) / 2^128. CHECK.

### 10.3 What Remains to Build

Based on the existing code:

1. **ERC-4626 shell**: Inherit Solady ERC4626. Override `totalAssets()` with the accumulator read. (~50 lines)
2. **Multi-position aggregation**: If the vault holds multiple tick ranges, sum the per-position accrued fees. The AccrualManagerMod already handles single positions; need a registry of active positions.
3. **Virtual shares/assets offset**: Solady's ERC4626 supports this natively to prevent the first-depositor attack. Enable it.
4. **Deposit/withdrawal hooks**: On deposit, snapshot the current growthInside. On withdrawal, settle and checkpoint. Both patterns exist in AccrualManagerMod.
5. **IRateProvider**: Optional. Expose `getRate() = totalAssets() * 1e18 / totalShares()` for external integrations.

### 10.4 What NOT to Build

1. **Rebasing token**: The share-price model is strictly superior for composability.
2. **Bonding curve**: The vault is not a bonding curve. The supply function is determined by the external observable, not by supply itself.
3. **Pluggable curve factory**: Overkill. The yield function is fixed by Angstrom's protocol design.
4. **Push-based harvest**: The accumulator model is naturally pull-based. Adding a keeper adds latency and trust assumptions.

---

## Appendix A: Quick Reference -- All Projects Mentioned

| # | Project | Type | License | Repo |
|---|---------|------|---------|------|
| 1 | Bancor | Bonding curve | Apache-2.0 | bancorprotocol/contracts-solidity |
| 2 | Ampleforth | Rebasing | GPL-3.0 | ampleforth/ampleforth-contracts |
| 3 | Olympus | Rebasing + wrapped | AGPL-3.0 | OlympusDAO/olympus-contracts |
| 4 | Aave V3 | Accumulator rebase | BUSL-1.1 | aave/aave-v3-core |
| 5 | Lido | Oracle rebase + wrapped | GPL-3.0 | lidofinance/lido-dao |
| 6 | Panoptic | ERC-4626 + accumulators | BUSL-1.1 | panoptic-labs/panoptic-v1-core |
| 7 | Bunni V2 | ERC-4626 + UV4 accumulators | BSL-1.1 | Bunni-xyz/bunni |
| 8 | Yearn V3 | ERC-4626 + harvest | AGPL-3.0 | yearn/tokenized-strategy |
| 9 | MetaMorpho | ERC-4626 + multi-market | GPL-2.0 | morpho-org/metamorpho |
| 10 | Balancer | Rate providers | GPL-3.0 | balancer/balancer-v2-monorepo |
| 11 | Commons Stack | Augmented bonding curve | GPL-3.0 | commons-stack/augmented-bonding-curve |
| 12 | Yield Protocol | Time-weighted AMM | BUSL-1.1 | yieldprotocol/yieldspace-v2 |
| 13 | Solady | Math library | MIT | Vectorized/solady |
| 14 | PRBMath | Math library | MIT | PaulRBerg/prb-math |
| 15 | ABDKMath | Math library | BSD-4 | abdk-consulting/abdk-libraries-solidity |
| 16 | OpenZeppelin | ERC-4626 + ERC20 extensions | MIT | OpenZeppelin/openzeppelin-contracts |
| 17 | cadCAD | Token simulation | MIT | cadCAD-org/cadCAD |
| 18 | friend.tech | Quadratic bonding | Proprietary | (Base chain, no public repo) |
| 19 | pump.fun | Constant-product launch | Proprietary | (Solana, no public repo) |

## Appendix B: Relevant Files in This Codebase

- `contracts/src/ran.sol` -- AngstromRANOracleAdapter (accumulator read layer)
- `contracts/src/modules/AccrualManagerMod.sol` -- Checkpoint + settle logic + viewAccruedRatio
- `contracts/src/types/PoolRewards.sol` -- globalGrowth + growthOutside structure
- `contracts/src/types/NoteSnapshot.sol` -- Per-note accumulator snapshots
- `contracts/src/libraries/X128MathLib.sol` -- Q128.128 fixed-point arithmetic
- `contracts/src/libraries/RayMathLib.sol` -- RAY (1e27) fixed-point arithmetic
- `contracts/src/AccrualManager.sol` -- Stub (Task 3 pending)
- `contracts/lib/solady/src/utils/FixedPointMathLib.sol` -- Base math
- `contracts/lib/solady/src/tokens/ERC4626.sol` -- Recommended vault base class
