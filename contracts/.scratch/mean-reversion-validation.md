# Mean-Reversion Validation: Concentration Ratio R(t) = growthInside / globalGrowth

**Date:** 2026-04-09
**Author:** Papa Bear analysis
**Status:** Theoretical framework + actionable recommendations

---

## Executive Summary

The cumulative concentration ratio R(t) = growthInside(tL, tU, t) / globalGrowth(t) is **NOT mean-reverting** in general. It is a ratio of two monotonically non-decreasing accumulators and converges to a constant (the time-weighted average share of fees) by the law of large numbers. However, the **instantaneous flow concentration** (the derivative ratio) and certain **delta-over-delta transformations** ARE mean-reverting under conditions that hold for typical active ranges. This document provides the full analysis and identifies the correct underlying process for option pricing.

---

## 1. The Cumulative Ratio R(t) Is NOT Mean-Reverting

### 1.1 Definition from the Codebase

From `PoolRewardsLib.getGrowthInside` (PoolRewards.sol:26-44) and `GrowthOutsideUpdater._decodeAndReward` (GrowthOutsideUpdater.sol:31-107):

```
growthInside(tL, tU, t) = globalGrowth(t) - outsideBelow(tL, t) - outsideAbove(tU, t)
                          (when tL <= currentTick < tU, i.e. in range)
```

Both `growthInside` and `globalGrowth` are cumulative sums of `amount / liquidity` increments (X128 fixed-point). They are monotonically non-decreasing.

### 1.2 Why the Ratio Converges Rather Than Mean-Reverts

Define:
- G(t) = globalGrowth(t) -- total accumulated fee growth per unit liquidity
- I(t) = growthInside(tL, tU, t) -- accumulated fee growth inside the range
- R(t) = I(t) / G(t)

At each block/epoch, some fee increment dG accrues to the pool. The fraction that accrues inside [tL, tU] depends on whether currentTick is in range:

```
dI = dG * 1_{tL <= tick(t) < tU} * (L_range / L_total)
```

where L_range is liquidity in the range and L_total is total active liquidity.

By the strong law of large numbers, as t -> infinity:

```
R(t) = I(t)/G(t) -> E[1_{in range} * L_range/L_total]
```

This means R(t) is **asymptotically constant**. It does not mean-revert -- it converges. The "memory" of the cumulative sum grows, so deviations from the long-run mean get progressively dampened. This is the opposite of mean reversion: it is **averaging out** (Cesaro convergence), not **reverting back**.

### 1.3 Formal Non-Stationarity Argument

For a process to be (weakly) stationary, its mean and autocovariance must be time-invariant. R(t) has:

1. **Time-varying mean**: E[R(t)] converges to a constant but is not constant for finite t. Early values are more volatile.
2. **Declining variance**: Var[R(t)] ~ O(1/t) since it is a running average. This violates stationarity.
3. **Non-negative autocorrelation**: Since R(t) is a cumulative average, R(t) and R(t+h) share most of their history. The autocorrelation is positive and increasing toward 1, not negative (which would indicate mean reversion).

**Verdict: R(t) is non-stationary and not mean-reverting. Using it as the underlying for Panoptic options is problematic.**

---

## 2. The Instantaneous Flow Concentration IS Mean-Reverting

### 2.1 Definition

Define the **instantaneous flow concentration**:

```
r(t) = dI/dG = 1_{tL <= tick(t) < tU} * L_range(t) / L_total(t)
```

This is the fraction of fees going to the range at time t. It is a binary-weighted ratio: either the range captures its proportional share of fees (when in range), or it captures zero (when out of range).

### 2.2 Mean-Reversion Mechanism

For a range centered around the current price, tick(t) follows a process closely related to a geometric Brownian motion (the underlying asset price). The indicator function 1_{in range} therefore follows a regime-switching process:

- **In-range regime**: r(t) = L_range/L_total (approximately constant if liquidity doesn't change much)
- **Out-of-range regime**: r(t) = 0

For a GBM price process, the occupation time of any bounded interval is well-studied. The price will:
- Exit the range (first-passage)
- But for mean-reverting pairs (e.g., stablecoin/stablecoin, correlated tokens), return to the range

The key insight: **for any pair where price is mean-reverting or at least recurrent (which includes GBM for bounded intervals over finite horizons), the indicator function 1_{in range} is a recurrent process**. The flow concentration r(t) inherits this recurrence.

### 2.3 Conditions for Mean Reversion of r(t)

r(t) is mean-reverting when:

1. **Price is recurrent with respect to the range**: The price visits the range infinitely often. For GBM (which is NOT recurrent on R+), this fails for very narrow ranges if the price trends away. But for:
   - Stablecoin pairs: price is mean-reverting around 1.0 -- strongly recurrent
   - ETH/BTC-type pairs: random walk, recurrent in log-space over practical horizons
   - Wide ranges: the range captures most price action

2. **Liquidity distribution is approximately stable**: If L_range/L_total changes slowly relative to price dynamics, the in-range value of r(t) is approximately constant.

3. **The range is not permanently abandoned**: This is the critical failure mode -- if price undergoes a regime change (e.g., a depeg), the range may never be revisited.

### 2.4 Mathematical Model

For a mean-reverting pair, model tick(t) as Ornstein-Uhlenbeck:

```
d(tick) = theta * (mu - tick(t)) dt + sigma * dW(t)
```

Then 1_{tL <= tick(t) < tU} is a function of an OU process, and its time-average converges to:

```
P(tL <= tick_stationary < tU) = Phi((tU - mu)/(sigma/sqrt(2*theta))) - Phi((tL - mu)/(sigma/sqrt(2*theta)))
```

The flow concentration r(t) = 1_{in range} * c (where c = L_range/L_total) is then a **hidden Markov model with OU-driven regime switching**, and its autocorrelation function is:

```
Corr(r(t), r(t+h)) ~ exp(-theta * h) * [terms depending on range width]
```

This exhibits exponential decay -- classic mean reversion with rate theta (inherited from the price process).

---

## 3. The Delta-Over-Delta Ratio: Your `viewAccruedRatio`

### 3.1 What the Code Computes

From `AccrualManagerMod.sol:139-160`, the `viewAccruedRatio` function computes:

```
ratioQ128 = (currentGI - entryGI) / (currentGG - entryGG)
```

This is the **incremental concentration ratio** since entry: "what fraction of all fees accrued since I entered have been captured by my range?" Call this:

```
R_delta(t; t0) = [I(t) - I(t0)] / [G(t) - G(t0)]
```

### 3.2 Behavior of R_delta

This is better than R(t) but still has issues:

- It is anchored at t0 (the entry time). As t -> infinity, it converges to the same limit as R(t).
- It IS more volatile for small (t - t0), which is good for options that expire in finite time.
- It can be written as:

```
R_delta(t; t0) = (1/(t-t0)) * integral_{t0}^{t} r(s) ds
```

(approximately, weighting by fee volume at each instant)

This is a **running average of the flow concentration** over [t0, t]. By the ergodic theorem, it converges to E[r] = P(in range) * L_range/L_total.

### 3.3 Is R_delta Mean-Reverting?

No, for the same reason as R(t) -- it is a running average that converges. Its variance decreases as the window grows. However:

- For **short-dated options** (small t - t0), R_delta is dominated by recent flow concentration, which IS volatile and (for appropriate pairs) mean-reverting.
- The **change** in R_delta over a fixed window, i.e., R_delta(t+dt; t0) - R_delta(t; t0), is driven by the current r(t) minus the running average -- which IS a mean-reverting quantity (Cesaro deviations are mean-reverting).

---

## 4. Recommended Underlying Process for Option Pricing

### 4.1 The Correct Choice: Windowed Flow Concentration

For Panoptic-style options to work, the underlying should be:

**Option A: Rolling-window flow concentration**

```
rho(t; W) = [I(t) - I(t-W)] / [G(t) - G(t-W)]
```

This is the fraction of fees captured by the range over the most recent window of width W. Properties:

- **Stationary** (for stationary price process and stable liquidity): since it depends only on the last W units of time
- **Mean-reverting**: inherits mean reversion from the price process / flow concentration
- **Bounded**: in [0, L_range/L_total] (assuming liquidity stability)
- **Economically meaningful**: "how is my range performing right now?"

For W = option expiry tenor, this is exactly the quantity that determines option payoff.

**Option B: Instantaneous flow rate ratio**

```
r(t) = dI/dG (at time t)
```

This is mean-reverting but binary (0 or L_range/L_total), making it difficult to price options on directly. It is better as a building block.

**Option C: Log-transformed delta ratio**

```
z(t) = log(R_delta(t; t0)) - log(R_delta(t-dt; t0))
```

The log-returns of the delta ratio. These are approximately stationary for short dt but have declining volatility as the cumulative window grows (the denominator of R_delta stabilizes).

### 4.2 Recommendation for V_A / V_B Design

Given your design where V_A tracks growthInside and V_B tracks globalGrowth:

**The ratio V_A / V_B as currently defined (cumulative) will NOT produce well-priced options** because:

1. It converges to a constant, so implied volatility collapses to zero over time
2. Short straddle sellers are not at risk of large moves -- they are at risk of slow convergence
3. The "LP as straddle" analogy from Panoptic's design breaks down because Panoptic's fee accumulators are PER POSITION (they reset on each mint), whereas a global ratio has full history

**Instead, the underlying should be constructed from INCREMENTAL accumulators over a rolling window:**

```
V_A(t) = growthInside(t) - growthInside(t - W)
V_B(t) = globalGrowth(t) - globalGrowth(t - W)
underlying(t) = V_A(t) / V_B(t)
```

This requires storing periodic checkpoints of the accumulators (e.g., every epoch/block) or using the existing `entryGrowthInside` / `entryGlobalGrowth` snapshots with a fixed-tenor structure.

### 4.3 How `viewAccruedRatio` Maps to This

Your `viewAccruedRatio` (AccrualManagerMod.sol:139-160) already computes R_delta(t; t0) where t0 = entry time. For fixed-expiry options:

- **If all options sharing a NoteId have the same epoch start time**, then R_delta with t0 = epoch start is exactly the rolling-window concentration with W = (t - epoch_start).
- **The window W grows with time**, which means the process slowly loses its volatility. This is acceptable for European options that expire at a known time, because the relevant quantity is R_delta at expiry.
- **For perpetual/American options**, you would need a true rolling window (TWAP-style checkpointing).

---

## 5. Mathematical Framework: When Is R(t) "Close Enough" to Mean-Reverting?

### 5.1 Decomposition

Write R(t) = R_bar + epsilon(t), where R_bar = lim_{t->inf} R(t). Then:

```
epsilon(t) = R(t) - R_bar = [I(t) - R_bar * G(t)] / G(t)
```

The numerator N(t) = I(t) - R_bar * G(t) is a martingale (under appropriate assumptions), so epsilon(t) = N(t)/G(t) where:
- N(t) ~ O(sqrt(t)) (martingale CLT)
- G(t) ~ O(t) (deterministic drift)

Therefore epsilon(t) ~ O(1/sqrt(t)), which means:
- Deviations from the mean decay as 1/sqrt(t) -- this looks like mean reversion but is actually just dampening
- The "half-life" of a deviation is not constant (it depends on when the deviation occurred)
- An ADF test on R(t) will likely reject the unit root for long series (because it converges), giving a FALSE POSITIVE for mean reversion

### 5.2 Key Distinction: Dampening vs. Mean Reversion

- **Mean reversion (OU process)**: Deviations decay exponentially with a CONSTANT half-life. The process has constant variance in stationarity.
- **Dampening (Cesaro convergence)**: Deviations decay as 1/sqrt(t). The variance goes to zero. No stationary distribution exists.

R(t) exhibits dampening, not mean reversion. This means:
- Short-term options (small tenor relative to total accrual history) might "feel" like they are on a mean-reverting underlying, because recent price movements dominate
- Long-term options will be systematically mispriced if you assume mean reversion

### 5.3 The LVR Connection

Milionis et al. (2022) decompose LP losses into LVR (loss-versus-rebalancing). The per-range LVR share follows similar dynamics to the flow concentration r(t):

```
LVR_range(t) / LVR_total(t) = 1_{in range} * f(L_range, L_total, sigma)
```

The **cumulative** LVR ratio has the same non-stationarity problem as R(t). But the **instantaneous** LVR share is driven by whether the range is active, which IS recurrent for non-trending pairs.

---

## 6. Practical Recommendations

### 6.1 For the ThetaSwap Options Design

1. **Use epoch-bounded ratios, not cumulative ratios.** Each option epoch should have a fresh t0. The `entryGrowthInside` / `entryGlobalGrowth` snapshot mechanism in AccrualManagerMod.sol already does this correctly.

2. **Keep option tenors short relative to price dynamics.** For a range of width W_ticks with price volatility sigma:
   - Characteristic time to exit range: tau ~ (W_ticks / sigma)^2
   - Option tenor should be O(tau) or smaller for the mean-reversion approximation to hold
   - For ETH/USDC 30bps pool with +/-5% range, tau ~ 1-2 weeks

3. **Do NOT use the cumulative R(t) as an oracle price.** Use R_delta(t; t_epoch_start) as the underlying. This is what `viewAccruedRatio` computes.

4. **For short straddles specifically:** The risk is that price exits the range and does not return before expiry. This is a first-passage problem, not a mean-reversion problem. Price the options using first-passage probabilities for the price process, not OU dynamics on R(t).

### 6.2 Empirical Validation Roadmap

To confirm these theoretical findings empirically:

1. **Collect historical data**: feeGrowthGlobal0X128 and feeGrowthInside0LastX128 for major Uniswap V3 pools (ETH/USDC 5bp, ETH/USDC 30bp, USDC/USDT 1bp) at block-level granularity via Dune or direct archive node queries.

2. **Compute R(t) and test for stationarity**:
   - Augmented Dickey-Fuller test (expect: rejects unit root due to convergence, NOT due to mean reversion)
   - KPSS test (expect: rejects stationarity for level, may not reject for trend-stationary)
   - Variance ratio test (expect: ratio < 1, declining, consistent with dampening)

3. **Compute rolling-window rho(t; W) for various W** (1 hour, 1 day, 1 week):
   - ADF test (expect: strong rejection of unit root -- genuinely mean-reverting)
   - Fit OU model, estimate theta (half-life)
   - Test for regime-switching (Hamilton filter) to capture in-range / out-of-range dynamics

4. **Compare flow concentration r(t) across range widths**:
   - Narrow (+/-1%): highly volatile, binary, fast mean reversion when price is OU
   - Medium (+/-5%): moderately volatile, good OU fit
   - Wide (+/-20%): near-constant, very slow mean reversion
   - Full range: trivially 1.0 (no variance at all)

### 6.3 Known Mean-Reverting Transformations

If you must use cumulative accumulators, these transformations produce mean-reverting processes:

| Transformation | Formula | Mean-Reverting? | Practical? |
|---|---|---|---|
| First difference of R | R(t) - R(t-1) | Yes (for short lags) | Noisy, near-zero mean |
| Rolling-window ratio | [I(t)-I(t-W)] / [G(t)-G(t-W)] | Yes | Best option -- requires checkpoints |
| Log-return of R | log(R(t)/R(t-1)) | Approximately | Undefined when R near 0 |
| Standardized deviation | (R(t) - R_bar) * sqrt(t) | Converges to Brownian motion | Not mean-reverting, but stationary variance |
| Flow concentration | dI/dG (instantaneous) | Yes | Binary; need smoothing |

---

## 7. Connection to Panoptic's Architecture

### 7.1 How Panoptic Handles This

Panoptic's "LP as option" model works because:

1. **Each position has its own accumulators**: feeGrowthInsideLast is per-position, not global. When you mint a new Panoptic position, you get a FRESH snapshot.
2. **Premia are computed as deltas**: premiumOwed = (currentFeeGrowthInside - lastFeeGrowthInside) * liquidity. This is an increment, not a ratio.
3. **The VEGOID mechanism**: Panoptic adds a spread between premiumOwed (what the long pays) and premiumGross (what the short receives), which handles the non-mean-reversion problem by making short sellers overcollateralized.

### 7.2 Why Your Design Needs Special Care

Your `viewAccruedRatio` computes a RATIO of deltas, not just a delta:

```solidity
ratioQ128 = FixedPointMathLib.mulDiv(giDelta, Q128, ggDelta);  // line 159
```

This ratio has better properties than R(t) but still converges as the position ages. For option pricing:

- **Short-dated options**: The ratio is driven by recent flow concentration. Approximation as mean-reverting is reasonable.
- **Long-dated options**: The ratio is dominated by historical average. Mean-reversion assumption breaks down.
- **At-the-money options**: Most sensitive to the mean-reversion assumption. These need the most careful handling.

### 7.3 The VEGOID Equivalent

If you cannot guarantee mean reversion, you need a mechanism analogous to Panoptic's VEGOID spread:

- Charge short sellers a premium above the fair value of the option
- This premium covers the risk that the underlying converges rather than mean-reverts
- The premium should be proportional to sqrt(remaining_tenor / total_accrual_time)

---

## 8. Conclusion

### The Answer

**R(t) = growthInside / globalGrowth is NOT mean-reverting. It is a converging process (dampening).**

However:
- The **instantaneous flow concentration** r(t) = dI/dG IS mean-reverting for pairs with recurrent price processes
- The **delta-over-delta ratio** R_delta(t; t0) used in `viewAccruedRatio` is the correct building block for option pricing, provided option tenors are short relative to total accrual history
- A **rolling-window** formulation rho(t; W) would be the theoretically ideal underlying

### For the ThetaSwap Design

1. The current `viewAccruedRatio` with per-NoteId epoch snapshotting is a reasonable approximation for short-to-medium tenor options
2. Do NOT build perpetual options on cumulative R(t)
3. Consider implementing rolling-window checkpoints for longer-tenor products
4. The short straddle risk is fundamentally a first-passage problem, not a mean-reversion problem
5. Empirical validation on mainnet data is the critical next step to quantify half-lives and regime-switching frequencies

### Risk Matrix

| Range Type | Price Process | R(t) behavior | r(t) behavior | Option viability |
|---|---|---|---|---|
| Narrow, stablecoin | OU | Converges fast | Mean-reverting, fast | Good for short tenor |
| Medium, ETH/USDC | GBM-like | Converges slowly | Regime-switching | Good with care |
| Narrow, ETH/USDC | GBM-like | Volatile then converges | Binary, long excursions | Risky -- first-passage dominates |
| Wide, any | Any | Near-constant | Near-constant | Trivial, no vol to price |
| Any, after depeg | Trending | Converges to 0 | Stuck at 0 | Option worthless, short wins permanently |
