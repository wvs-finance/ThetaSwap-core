# RAN Residual Risk & LP Scenario Analysis Under Angstrom

Date: 2026-04-08
Scope: Range Accrual Note product risk decomposition for Angstrom-settled concentrated liquidity

---

## Section 1: Scenario Matrix -- LP Archetypes and RAN Usage

The Aquilina et al. (BIS WP 1227) classification identifies five LP archetypes on Uniswap V3.
Each archetype's behavior changes fundamentally under Angstrom because the revenue source shifts
from swap fees (volume-determined) to auction rewards (bid_in_asset0, auction-determined). The
RAN tokenizes the theta component of that reward stream.

### 1.1 Sophisticated Concentrated LP

**Aquilina profile**: 7% of addresses, 80% TVL, 23% tick-range spread, 16-day median
duration, +5bps/day excess return from active management, tight ranges repositioned
around current price.

**Would they use RAN?** SHORT (seller of theta).

**Motivation under Angstrom**: These LPs already dominate in-range liquidity. Under Angstrom,
their revenue is `bid_in_asset0 * (their_liquidity / total_in_range_liquidity)` per block.
The auction mechanism rewards in-range liquidity proportionally, so their tight ranges capture
disproportionate reward share -- identical to V3 but with the JIT threat eliminated by the
`JustInTimeLiquidityChange()` revert in GrowthOutsideUpdater (line 22, the `expectedLiquidity`
check against pool liquidity).

These LPs would SHORT the RAN because:
1. They are natural theta producers -- their positions accrue growthInside at high rates
2. Selling RANs (writing the "how much time in range" bet) monetizes their confidence in
   active repositioning
3. The premium received from RAN longs is additive to their auction reward income
4. Their 16-day duration means they can write short-epoch RANs, collect premium, and
   reposition before the range becomes stale

**Expected payoff**: Premium income from RAN sales + auction rewards - repositioning gas costs.
Net positive in moderate vol. Risk: extreme vol events where price exits range faster than
their repositioning cadence (16-day median suggests ~4% of positions may be caught).

### 1.2 Sophisticated JIT LP (Eliminated by Angstrom)

**Aquilina profile**: The extreme end of sophistication -- adds massive liquidity just before
a large swap, captures most fees, removes immediately. Duration: 1-3 blocks. Responsible
for the fee concentration that the FCI oracle measures (delta* ~ 0.09 threshold).

**Would they use RAN?** NO -- this archetype does not exist under Angstrom.

**Motivation under Angstrom**: The GrowthOutsideUpdater enforces `expectedLiquidity == poolLiquidity`
at reward distribution time. Any liquidity added between the node's snapshot and the bundle
execution triggers `JustInTimeLiquidityChange()`. This is a hard revert, not a penalty -- JIT
is structurally impossible.

The JIT LP's entire alpha source (capturing fees at 1-3 block resolution) is destroyed. They
either become a standard sophisticated concentrated LP (Type 1.1) or exit the protocol entirely.

**RAN implication**: The elimination of JIT is one of Angstrom's key contributions to making
the RAN viable. On V3, JIT LPs dilute the growthInside that accrues to longer-duration positions,
making the RAN's accruedTheta computation noisy and adversarial. Under Angstrom, the monotonicity
invariant (`accruedTheta(t2) >= accruedTheta(t1)`) becomes robust because no adversary can
dilute mid-block.

### 1.3 Retail Concentrated LP

**Aquilina profile**: Tight range but no repositioning skill. 63% tick-range spread
(wider than sophisticated), 120-day median duration, -2.84bps/day net return vs
sophisticated, loses 6.4bps more in high vol.

**Would they use RAN?** LONG (buyer of theta protection).

**Motivation under Angstrom**: This is the RAN's primary target customer. Under Angstrom:
1. They still earn auction rewards proportional to in-range liquidity
2. But they do NOT actively reposition (120-day duration = set and forget)
3. When price drifts out of their range, their growthInside stops incrementing
4. The Aquilina data shows they earn 3.5bps/day less fee yield -- mostly because they
   spend more time out-of-range

Buying a RAN LONG gives them: `payoff = coupon * (n/N)` where n = observations in-range.
This is valuable because:
- If price stays in range: they collect both auction rewards AND the RAN coupon -- overpaying
  for protection they did not need, but the net position is still positive
- If price exits range: auction rewards stop, but the RAN coupon pays based on the fraction
  of time they WERE in range -- partial recovery of lost income
- The RAN premium they pay is essentially the cost of Capponi's first-passage-time insurance

**Expected payoff**: Auction rewards + RAN coupon*(n/N) - RAN premium. Net negative in calm
markets (premium wasted), net positive in volatile markets where the price exits their range
early. The RAN converts their binary "in or out" exposure into a graded payout.

### 1.4 Retail Unconcentrated LP

**Aquilina profile**: Wide ranges (approaching full-range V2-style), minimal fee
capture per unit liquidity, very long durations (120+ days), negative excess returns.

**Would they use RAN?** UNLIKELY -- economic mismatch.

**Motivation under Angstrom**: Their wide ranges mean they are almost always "in range" but
capture very little reward per unit liquidity. The RAN's value proposition is protection
against going out-of-range. For an LP who is always in-range, the RAN premium is pure cost
with no protective benefit.

The one scenario where they might participate: if they SHORT the RAN. Their near-certainty
of being in-range means selling RANs (promising "I'll be in range") appears low-risk. But:
- Their per-unit reward capture is so low that the RAN premium received is small
- They face collateral requirements from the CollateralManager
- The capital efficiency is terrible (lots of collateral locked for small premium)

**Expected payoff**: Near-zero edge case. The RAN does not serve this archetype well. They
are better served by Panoptic's delta decomposition (hedging IL on their wide range).

### 1.5 Retail Range-Order LP

**Aquilina profile**: Uses LP positions as limit orders -- places liquidity in a narrow band
above or below current price, waiting for price to cross. Duration: variable (until
fill or expiry). Not a theta strategy -- a directional bet.

**Would they use RAN?** NO -- misaligned payoff.

**Motivation under Angstrom**: Range orders are delta bets, not theta bets. The LP wants
price to cross their range once, converting one token to another. They do NOT want to stay
in-range accumulating fees. The RAN's "time in range" payoff is the opposite of what they
seek -- they want a first-passage event, not range-bound accrual.

Under Angstrom specifically, range orders still function as Uniswap V4 hook passes through
to the underlying pool. But the RAN adds no value because the range-order LP's holding period
is measured in blocks (waiting for a single price crossing), not epochs.

**Expected payoff**: N/A. This archetype should use Angstrom's native user order flow
(limit orders in the orderbook) rather than LP positions at all.

---

## Section 2: Residual Risk Analysis

Angstrom mitigates several risks that plague V3 LPs: JIT dilution, sandwich attacks, and
toxic flow. But it does NOT eliminate all risks. The following analysis examines each residual
risk and how the RAN transforms it.

### 2.1 Price Exits Range (First-Passage Risk)

**What Angstrom does**: Nothing. Price dynamics are exogenous. Angstrom's auction mechanism
does not stabilize the underlying asset price.

**How the RAN transforms it**: The RAN TRANSFERS this risk from the LP (long side) to the
RAN short seller.

- **Without RAN**: LP stops earning when price exits range. Binary outcome.
- **With RAN long**: LP receives `coupon * (n/N)` proportional to time spent in-range.
  The out-of-range period is compensated by the coupon's accrued fraction.
- **With RAN short**: The theta seller bears the loss. If price exits range early, the
  short's collateral is drawn down to pay the long's partial coupon.

**New risks created**:
1. **Pricing risk**: The RAN premium must correctly price the first-passage-time distribution.
   Under Capponi's framework, `E[tau] = expected_first_passage_time` determines fair value.
   But Angstrom's auction-based rewards change the drift -- the price process seen by the RAN
   is the same external market price, but the INCOME process is auction-determined, creating
   a wedge between the theoretical (BS/Capponi) and realized theta.
2. **Basis risk**: The RAN pays based on observations (block/epoch), while the LP's actual
   income accrues per-reward-distribution. If the observation frequency mismatches the reward
   frequency, the LP may be "in range" at observation time but earn no reward (because the
   node allocated zero reward in that block).

**Economic intuition**: First-passage risk is the irreducible risk of concentrated liquidity.
It cannot be diversified away or structurally eliminated. The RAN re-slices it into a market
with willing buyers (retail concentrated LPs) and sellers (sophisticated LPs who reposition
before passage), but the risk quantum is conserved.

### 2.2 Reward Allocation Discretion (Node Risk)

**What Angstrom does**: The node (block proposer within the Angstrom network) decides how to
allocate `bid_in_asset0` across tick ranges. The `_decodeAndReward` function in
GrowthOutsideUpdater accepts the node's reward allocation via calldata and distributes it
to `rewardGrowthOutside[tick]`. Staking and slashing provide economic security.

**What Angstrom does NOT do**: It does not guarantee that the node allocates rewards
"fairly" in any specific sense. The node could, within slashing constraints:
- Concentrate rewards on tick ranges where it holds positions
- Starve certain tick ranges of rewards
- Vary allocation unpredictably across blocks

**How the RAN transforms it**: The RAN AMPLIFIES this risk.

- **Without RAN**: LP earns whatever the node allocates. If allocation is unfair, LP earns
  less but retains the principal.
- **With RAN long**: The note's `accruedTheta = currentGrowthInside - entryGrowthInside`
  depends on the node's allocation. If the node starves the RAN's tick range, accruedTheta
  stalls even though price is in-range. The long receives a lower coupon payout despite being
  "in range" by price.
- **With RAN short**: The short benefits from node under-allocation (pays less).

**New risks created**:
1. **Oracle manipulation**: The RAN's IAccumulatorSource reads growthInside from the
   Angstrom reward accumulator. A colluding node could manipulate this to benefit RAN
   shorts at the expense of longs. The slashing mechanism must be calibrated to make
   this unprofitable.
2. **Correlation risk**: In V3, fee income is mechanically determined by volume. The RAN's
   digital-option decomposition (Pap Eq. 4.12) assumes an exogenous observation process. Under
   Angstrom, the "observation" (growthInside increment) is endogenous to node behavior, breaking
   the independence assumption.

**Economic intuition**: Angstrom replaces the adversarial but deterministic V3 fee mechanism
(volume * fee_rate / liquidity) with a stochastic mechanism (auction surplus allocated by node).
The RAN, which bets on the accumulator trajectory, inherits the node's allocation variance as
a new risk factor that has no V3 analog.

### 2.3 Collateral Shortfall (Extreme Volatility)

**What Angstrom does**: Angstrom does not provide collateral management. The RAN's
CollateralManager (Panoptic's CollateralTracker pattern) is a separate layer.

**How the RAN transforms it**: The RAN CREATES this risk.

- **Without RAN**: No collateral risk. LP's principal is the liquidity itself, and it can
  always be withdrawn (possibly at a loss due to IL, but never "seized").
- **With RAN short**: The short must post collateral >= premiumOwed at all times (Solvency
  invariant: `collateral >= premiumOwed`). In extreme vol, accruedTheta can spike rapidly
  (price stays in range during a volatile period with high auction surplus), causing
  premiumOwed to exceed posted collateral.

**New risks created**:
1. **Liquidation cascade**: If collateral shortfall triggers `forceExercise` (Panoptic
   pattern), multiple RAN shorts may be liquidated simultaneously, reducing the pool of
   theta sellers and causing a liquidity crunch in the RAN market itself.
2. **Pro-cyclicality**: High vol increases both (a) the value of being in-range (auction
   surplus is larger) and (b) the probability of range exit (Capponi's tau decreases).
   The collateral requirement must balance these opposing forces. From the volume-fee
   elasticity finding (epsilon ~ +0.78 to +0.85), LP income is LONG vol, meaning
   accruedTheta increases in vol -- requiring MORE collateral from shorts exactly when
   they are most likely to be stressed.

**Economic intuition**: The RAN converts the LP's unlevered position (own capital at risk,
no margin) into a levered position (collateral can be called). This is the fundamental
cost of making theta tradeable: bilateral markets require margin, and margin creates
pro-cyclical stress.

### 2.4 Accumulator Staleness / Liveness

**What Angstrom does**: The `globalGrowth` accumulator in `PoolRewards` only updates when the
node submits a bundle containing reward allocations. If no bundle is submitted (node downtime,
censorship, network partition), the accumulator stalls.

**How the RAN transforms it**: The RAN EXPOSES this risk.

- **Without RAN**: LP simply does not earn during downtime. No loss beyond opportunity cost.
- **With RAN long**: The note's ratioInRange = accruedTheta / (globalGrowth - entryGlobalGrowth).
  If both numerator and denominator stall, the ratio is undefined or stale. Epoch-based
  observation may count a stale block as "not in range" (accruedTheta = 0), penalizing the
  long even though the system was simply not updating.
- **Staleness detection**: The failure mode table specifies `last_accumulator_update < max_staleness`
  as the detection criterion, but on-chain the RAN cannot distinguish "node did not allocate
  because there were no searchers" from "node is down."

**New risks created**:
1. **Observation gap**: The RAN's payoff depends on `n/N` (fraction of observations in-range).
   If N includes stale epochs, the denominator inflates while the numerator does not, unfairly
   diluting the long's payout.
2. **Gaming**: A sophisticated RAN short could, if they control or influence the node, selectively
   suppress reward allocation during periods when the long's range is in-range, reducing
   accruedTheta without moving price.

**Economic intuition**: The liveness risk is the on-chain analog of settlement risk in TradFi
derivatives. The RAN converts a "live" fee stream into a "sampled" payoff, and any gap in
sampling creates exploitable asymmetry.

### 2.5 Zero Liquidity in Range (Bootstrapping Problem)

**What Angstrom does**: If no LP provides liquidity in a tick range, the pool cannot execute
swaps through that range. The node's reward allocation to an empty range is meaningless.

**How the RAN transforms it**: The RAN has an EXISTENTIAL dependency on this.

- The RAN cannot be minted for a tokenId with `totalLiquidity == 0`. From NOTES.md:
  "Notes cannot be minted for that tokenId. Existing notes settle at whatever they accrued."
- But even with nonzero liquidity, if the liquidity provider withdraws mid-epoch, the
  growthInside accumulator becomes stale because no new rewards flow to that range.

**New risks created**:
1. **Counterparty correlation**: The RAN short seller is likely the LP providing the underlying
   liquidity. If they withdraw their LP position, the RAN's accumulator source dries up.
   This is a form of wrong-way risk: the entity guaranteeing the theta stream is the same
   entity providing the theta.
2. **Thin market**: For less popular tick ranges (far-from-spot), there may be only one LP.
   The RAN market for that range becomes bilateral, losing the benefits of multilateral
   clearing that the ERC-1155 fungibility provides.

**Economic intuition**: The RAN is a derivative on a derivative (a bet on the trajectory of
fees earned by an LP position). If the underlying position ceases to exist, the derivative
is orphaned. This is analogous to a CDS on a bond where the bond issuer can unilaterally
retire the bond.

### 2.6 Epoch Cross-Contamination and Transfer Integrity

**What Angstrom does**: N/A -- this is purely a RAN-layer risk.

**How the RAN transforms it**: The epoch isolation invariant (Invariant 4:
`claim(tokenId_e1) does not affect accruedTheta(tokenId_e2)`) and transfer neutrality
(Invariant 5) must hold at the smart contract level. Violations could arise from:

1. **Integer overflow in growth accumulators**: The `unchecked` blocks in GrowthOutsideUpdater
   rely on modular arithmetic. If entryGrowthInside is snapshotted in one epoch and
   currentGrowthInside wraps around in a later epoch, the subtraction produces a wrong
   (but not reverting) result.
2. **Transfer during accumulator update**: If a RAN token is transferred between two holders
   mid-epoch, the premium split between them must satisfy transfer neutrality. The SFPM
   pattern (s_accountPremiumOwed) handles this, but the integration with Angstrom's
   non-standard accumulator (reward-based rather than fee-based) must be carefully validated.

**Economic intuition**: These are implementation risks, not market risks. They persist
regardless of Angstrom's mitigation because they arise from the RAN's own accounting layer.
Formal verification (kontrol targets in NOTES.md) is the appropriate mitigation.

---

## Section 3: The Options Analogy

### 3.1 Capponi's First-Passage-Time Framework

The RAN's payoff `coupon * (n/N)` is economically a bet on the occupation time of price
within a range `[K_low, K_high]` over `[0, T]`. This connects directly to Capponi's
first-passage-time analysis of LP positions:

- Define `tau = inf{t > 0 : S_t not in [K_low, K_high]}` (first exit time)
- The RAN's `n/N` is related to the occupation time: `n/N ~ (1/T) * integral_0^T 1_{S_t in range} dt`
- For GBM with drift mu and vol sigma, the expected occupation time of a symmetric range
  `[S_0 * e^{-d}, S_0 * e^{+d}]` depends on the ratio `d / (sigma * sqrt(T))`

**Key result**: For an LP at tick range `[tickLower, tickUpper]`:

```
E[n/N] = P(occupation_fraction > threshold)
       = f(range_width / (sigma * sqrt(T)), drift)
```

This is monotonically decreasing in sigma (wider vol means more time out-of-range) and
increasing in range width. The RAN premium should be calibrated such that:

```
premium = E[coupon * (1 - n/N)] = coupon * (1 - E[n/N])
```

The fair premium equals the coupon times the expected fraction of time OUT of range.

**Under Angstrom**: The first-passage-time distribution is UNCHANGED because Angstrom does
not affect the external price process. What changes is what happens DURING the in-range
periods: the reward rate is auction-determined rather than volume-determined. This means:

- `E[n/N]` is the same under Angstrom and V3 (same price process)
- `E[accruedTheta | in-range]` is DIFFERENT (auction vs volume)
- The RAN's total expected value = `E[n/N] * E[reward_rate | in-range] * T`

The two factors decouple: Capponi's framework prices the time risk, and the auction
mechanism determines the rate risk.

### 3.2 The Panoptic Convergence: fee_rate = sigma^2 * S^2 * L / (2 * width)

Lambert's convergence result establishes that for a concentrated LP position:

```
dFee/dt = sigma^2 * S^2 * L / (2 * width) = Theta_BS(short_straddle_at_K)
```

The integral over paths converges to the Black-Scholes premium when realized vol matches
implied vol. This means:

1. **An LP position IS a written option** (short straddle on sqrt(price))
2. **The fee income IS the theta** (time decay of the written option)
3. **The RAN tokenizes this theta** as a separate tradeable instrument

**The digital option decomposition connection**: Pap (2022) shows the RAN decomposes
into a sum of digital options:

```
V_RAN = (c/N) * SUM_i [D(t_i, K_low) - D(t_i, K_high)]
```

Each digital option `D(t_i, K)` pays 1 if `S_{t_i} > K`. Under the Panoptic convergence,
each digital option's price can be extracted from the fee accumulation stream:

```
D(t_i, K) ~ N(d2) where d2 uses sigma_implied = sqrt(2 * fee_rate * width / (S^2 * L))
```

This closes the loop: the on-chain fee accumulator IS the implied vol oracle, the implied
vol determines digital option prices, and the sum of digital options equals the RAN price.
No external oracle is needed.

### 3.3 Angstrom's lpReward vs Uniswap's Fee Income: Theta Dynamics

This is the most critical distinction for the RAN product. The theta dynamics are
fundamentally different under Angstrom.

**Uniswap V3 theta (volume-determined)**:

```
dTheta/dt = fee_rate * volume(t) * liquidity_share(t)
```

- Volume is stochastic but correlated with sigma (high vol -> high volume)
- Fee rate is constant (pool parameter: 1bps, 5bps, 30bps, 100bps)
- Liquidity share is adversarial (JIT dilution)
- Net: theta is procyclical with vol but DILUTABLE

**Angstrom theta (auction-determined)**:

```
dTheta/dt = bid_in_asset0(t) * liquidity_share(t)
bid_in_asset0 = quantityIn - swap_cost
```

Where `swap_cost` is the cost of executing the swap through the V4 pool, and `quantityIn`
is what the searcher bid. The surplus `bid_in_asset0` is the searcher's willingness to pay
for the execution slot.

Key differences:
1. **Auction surplus replaces fee income**: Instead of `fee_rate * volume`, the LP earns
   `auction_surplus / total_in_range_liquidity`. Auction surplus depends on MEV opportunity,
   not raw volume.
2. **Not dilutable**: JIT protection means liquidity_share is stable within a block.
3. **Node-mediated**: The reward allocation path goes through the node's calldata encoding,
   adding a governance/trust layer between the economic surplus and the LP.
4. **Less predictable, higher variance**: Auction surplus varies based on arbitrage
   opportunities, which depend on cross-exchange price discrepancies. On V3, fee income
   is smoother (every swap pays fees). On Angstrom, rewards are lumpy (determined by
   the top-of-block auction outcome).

**Implications for the RAN's theta dynamics**:

| Property | V3 RAN | Angstrom RAN |
|----------|--------|-------------|
| Theta rate | `sigma^2 * S^2 * L / (2*w)` | `auction_surplus / L_in_range` |
| Correlation with sigma | Positive (Lambert) | Positive (more MEV in vol) but INDIRECT |
| Accumulator noise | JIT dilution noise | Node allocation variance |
| Observation quality | Direct (each swap increments) | Mediated (node decides increment) |
| Digital option pricing | Standard BS with fee-implied vol | Requires auction-implied vol extraction |
| Mean reversion of theta rate | Yes (vol mean-reverts -> theta mean-reverts) | Uncertain (auction dynamics less studied) |

**The sigma^2 bridge**: Under V3, the Panoptic convergence gives `fee_rate ~ sigma^2`.
Under Angstrom, the analogous relationship is:

```
auction_surplus ~ f(MEV_opportunity) ~ g(sigma, cross_exchange_spread, block_demand)
```

The MEV opportunity is correlated with sigma (volatile markets create more arbitrage)
but also depends on factors orthogonal to the LP's range (block space demand, cross-exchange
spreads, searcher competition). This means:

1. The RAN's accruedTheta under Angstrom has HIGHER VARIANCE than under V3 for the same
   occupation time
2. The implied vol extracted from Angstrom's accumulator (`sigma_implied = sqrt(2 * reward_rate * width / (S^2 * L))`)
   reflects MEV-adjusted vol, not pure price vol
3. The Pap digital-option decomposition remains valid in structure but requires
   recalibration: the model vol input is not market sigma but MEV-adjusted sigma

**Net assessment**: The RAN under Angstrom is a cleaner product (no JIT contamination of the
accumulator) but a harder-to-price product (auction surplus is less theoretically characterized
than fee income). The first-passage-time risk (Section 3.1) is identical; the conditional
theta rate (what you earn while in range) is better-behaved (no dilution) but noisier (auction
variance). The overall risk-return profile favors the RAN LONG relative to V3 because the
elimination of JIT increases `E[accruedTheta | in-range]` for non-JIT LPs (the Aquilina 3.5bps/day
gap narrows under Angstrom), but the short side faces novel node-allocation risk that has no
V3 analog.

---

## Summary Table: Risk Transformation Map

| Risk | V3 Status | Angstrom Status | RAN Transformation | Net Effect |
|------|-----------|-----------------|-------------------|------------|
| JIT dilution | Severe (80% TVL captured by 7%) | ELIMINATED | Moot -- accumulator is clean | Strongly positive for RAN viability |
| Sandwich/toxic flow | Present | ELIMINATED (hook-protected) | Moot | Positive |
| First-passage (price exits range) | Present | Present (unchanged) | TRANSFERRED from long to short | Risk conserved, market created |
| Node allocation discretion | N/A | NEW RISK | AMPLIFIED (accumulator depends on node) | New risk factor, needs slashing calibration |
| Collateral shortfall | N/A | N/A | CREATED by RAN | Pro-cyclical stress, needs careful parameterization |
| Accumulator staleness | N/A (fees are automatic) | Present (node must submit) | EXPOSED (stale epochs dilute n/N) | Design challenge for observation counting |
| Zero liquidity bootstrap | Present (both V3 and Angstrom) | Present | EXISTENTIAL dependency | Wrong-way risk if short = LP |
| Epoch/transfer integrity | N/A | N/A | CREATED by RAN | Implementation risk, formal verification target |

---

*Analysis produced 2026-04-08 for the thetaswap-patches branch, drawing on Angstrom contract source (GrowthOutsideUpdater, PoolUpdates, PoolRewards, Settlement), NOTES.md RAN architecture, Aquilina BIS WP 1227 findings, Pap (2022) digital-option decomposition, Lambert/Panoptic convergence, and Capponi first-passage-time framework.*
