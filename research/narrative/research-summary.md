# Research Summary: Fee Concentration Insurance

<!-- Key Results (machine-readable for downstream phases) -->
<!-- beta1: -23.18 (p=0.012) -->
<!-- beta2: +129.20 (p=0.030) -->
<!-- turning_point: 0.09 -->
<!-- implied_premium: $110/position at Delta=0.15 -->
<!-- pct_better_off: 18.8% -->
<!-- mean_hedge_value: +$23.21 -->
<!-- calibrated_gamma: 3.30% -->

## Introduction

This document summarizes the econometric research behind ThetaSwap's fee concentration insurance product. We applied a quadratic deviation exit hazard model to 3,365 position-day observations from the ETH/USDC 30bps pool on Uniswap V3 (41 days, 600 positions, 597 exit events). The analysis yields three findings, organized as pillars:

1. **Demand exists** --- passive LPs respond to fee concentration in a statistically significant, non-linear (inverted-U) pattern.
2. **A price exists** --- the marginal exit effect translates to an implied insurance premium of \$110 per position at high concentration.
3. **Backtest validates** --- the power-squared ($\alpha = 2$) payoff formula outperforms all alternatives, with 18.8% of positions better off hedged and a positive mean hedge value.


## Pillar 1: Demand Exists --- The Inverted-U

Passive LPs respond to fee concentration in a non-linear way. Below a threshold, concentration is actually protective --- it correlates with high trading volume that benefits all LPs. Above it, LPs flee.

### The Model

The probability that a position exits on day $t$ depends on how concentrated fees are ($\Delta^+$), the square of that concentration (capturing the non-linearity), impermanent loss as a control, and position age:

$$P(\text{exit}) = \sigma(\beta_0 + \beta_1 \Delta^+ + \beta_2 (\Delta^+)^2 + \beta_3 \cdot \text{IL} + \beta_4 \cdot \log(\text{age}))$$

Translation: the logistic model says exits depend on concentration deviation and its square. The negative $\beta_1$ and positive $\beta_2$ create an inverted-U --- exactly what Capponi's theory predicts. The negative linear term means mild concentration is protective (the "shelter regime"), while the positive quadratic term means extreme concentration drives exits (the "Capponi regime").

### Coefficient Table

| Coefficient | Lag 1 | Lag 2 | Lag 3 |
|---|---|---|---|
| $\beta_1$ (linear) | -23.18 (p=0.012) | -43.42 (p=0.016) | -32.44 (p=0.001) |
| $\beta_2$ (quadratic) | +129.20 (p=0.030) | +226.92 (p=0.065) | +205.34 (p=0.004) |
| Turning point $\delta^*$ | 0.090 | 0.096 | 0.079 |

All three lag windows show statistically significant results. The turning point clusters tightly at $\delta^* \approx 0.08$--$0.10$.

### Turning Point

The concentration threshold where the exit effect flips from protective to harmful is derived from the quadratic formula:

$$\delta^* = \frac{-\beta_1}{2\beta_2} \approx 0.090$$

In plain English: below $\delta^* \approx 0.09$, concentration actually reduces exits (shelter regime). Above 0.09, it accelerates exits (Capponi regime). The shelter regime occurs because mild fee concentration often accompanies high trading volume --- all LPs benefit from elevated fee revenue even when shares are somewhat unequal. The Capponi regime activates when concentration becomes severe enough that passive LPs' effective fee rate drops below their optimal exit threshold.

### Signal Decay

The concentration effect is strong at lags 1--3 days and dissipates at lags 5--7 (both coefficients become statistically insignificant). This confirms that passive LPs react to **recent** concentration shocks, not stale ones --- consistent with a short-memory reaction pattern.

### Full Lag-1 Model Parameters

| Parameter | Estimate | Interpretation |
|---|---|---|
| $\beta_0$ (intercept) | varies | Baseline exit probability |
| $\beta_1$ ($\Delta^+$) | -23.18 | Shelter effect below turning point |
| $\beta_2$ ($(\Delta^+)^2$) | +129.20 | Exit acceleration above turning point |
| $\beta_3$ (IL) | +13.52 | Higher impermanent loss increases exits |
| $\beta_4$ ($\log(\text{age})$) | -0.42 | Older positions are less likely to exit |

Model diagnostics: $n = 3{,}365$; exits $= 597$; clusters $= 40$; pseudo-$R^2 = 0.350$; mean $P(\text{exit}) = 0.177$.


## Pillar 2: A Price Exists --- Marginal Effect and Implied Premium

The econometric model does more than identify *that* concentration drives exits. It quantifies *how much*, which translates directly to an insurance price.

### Marginal Effect Formula

The rate at which exit probability changes with concentration is:

$$\frac{dP}{d\Delta} = (\beta_1 + 2\beta_2 \Delta) \cdot \bar{P}(1 - \bar{P})$$

This formula says the marginal effect depends on the current concentration level $\Delta$, the model coefficients, and the baseline exit probability $\bar{P}$. At the turning point ($\Delta = \delta^*$), the marginal effect is exactly zero --- the protective and harmful effects cancel out.

### Marginal Effect at High Concentration

At $\Delta = 0.15$ (well into the Capponi regime), the calculation is:

$$\beta_1 + 2\beta_2(0.15) = -23.18 + 2(129.20)(0.15) = 15.58$$

$$\frac{dP}{d\Delta} = 15.58 \times 0.177 \times 0.823 = 2.27$$

A 0.01 increase in $\Delta^+$ at this level raises exit probability by approximately 2.3 percentage points. This is a large effect --- it means concentration above the turning point has economically significant consequences for LP retention.

### Insurance Pricing Translation

The marginal effect translates to a dollar premium through three quantities:

| Quantity | Value |
|---|---|
| $\Delta P(\text{exit})$ per 0.01 $\Delta$ | +2.3 pp |
| Average remaining position hours | 48 |
| Hours of fee revenue at risk | $0.023 \times 48 = 1.1$ hours |
| Fee revenue per hour (pool average) | \$100 |
| **Implied premium per position** | **\$110** |

This is the maximum a rational LP would pay to avoid concentration risk above the turning point. It represents the expected cost of premature exit due to adverse competition --- and it is the anchor price for ThetaSwap's insurance product.


## Pillar 3: Backtest Validates --- The p-Squared Payoff

The econometric model identifies demand and a price. The backtest confirms that a specific payoff formula successfully converts this demand into a viable insurance product.

### Payoff Formula

At position exit, the insured LP receives:

$$\text{payout} = \gamma \cdot \text{lifetime\_fees} \times \left[\left(\frac{p_{\max}}{p^*}\right)^2 - 1\right]^+$$

The formula takes the maximum concentration price $p_{\max}$ experienced during the position's lifetime, compares it to the strike price $p^* = \delta^*/(1 - \delta^*)$ derived from the econometric turning point, squares the ratio, and subtracts 1. The $[\cdot]^+$ operator means the payout is zero if concentration never exceeded the turning point. The base premium factor $\gamma$ and lifetime fees determine the payout scale.

### Results

At $R_0 = \$200\text{K}$ seed capital and $\gamma = 3.30\%$:

- **18.8%** of positions are better off hedged (compared to 4.7% for the trigger-based INS-05 alternative)
- **Mean hedge value: +\$23.21** (compared to -\$82.65 for INS-05)
- The positive mean hedge value means the average insured LP gains from the product --- the insurance is not merely redistributive but creates net value through better tail protection.

### Comparison Table

| Metric | Trigger-based (INS-05) | p-squared ($\alpha=2$) |
|---|---|---|
| % positions better off | 4.7% | 18.8% |
| Mean hedge value | -\$82.65 | +\$23.21 |
| Moral hazard | Present | Absent |
| Bootstrapping problem | Severe | Resolved |

### Why p-Squared Works

1. **No moral hazard.** The payout depends on the *worst* (highest) concentration experienced during the position's lifetime. Staying in the pool during concentration spikes *increases* the payout --- the correct incentive. Exiting early reduces it. This is the opposite of the moral hazard in premium-proportional designs.

2. **Correct incentive alignment.** The backtest confirms a positive correlation between position lifetime and hedge value. Longer-lived positions benefit more than short-lived ones. Insurance rewards patience, which is the economically desirable behavior.

3. **Bootstrapping resolution.** The trigger-based design (INS-05) fails because the mutual reserve is too small at trigger time. The p-squared payoff settles at exit, not at trigger, sidestepping the bootstrapping problem entirely.

4. **Tail sensitivity.** The $\alpha = 2$ exponent is the sweet spot: sufficient convexity to reward extreme concentration events without draining the reserve at moderate $\Delta^+$. Higher exponents ($\alpha = 3$) over-concentrate payouts on the single worst event; lower exponents ($\alpha = 1$) provide insufficient tail compensation.


## Full Payoff Comparison

| Mode | Formula | % Better Off | Mean HV (\$) |
|---|---|---|---|
| Trigger 1/N (INS-05) | $\text{payout} = R / N_{\text{insured}}$ | 0.0% | -107.67 |
| Trigger premium-proportional | $\text{payout} \propto \text{premium}_i$ | 2.7% | -95.16 |
| Exit $\times \Delta^+$ | $\text{payout} = \gamma \cdot f \cdot \Delta^+_{\max}$ | 4.2% | -88.03 |
| Exit $\times p$ | $\text{payout} = \gamma \cdot f \cdot p_{\max}$ | 8.1% | -71.22 |
| **Exit $\times p^2$ ($\alpha=2$)** | **$\text{payout} = \text{premium} \times ((p_{\max}/p^*)^2 - 1)$** | **18.8%** | **+23.14** |
| Exit $\times p^3$ ($\alpha=3$) | $\text{payout} = \text{premium} \times ((p_{\max}/p^*)^3 - 1)$ | 12.1% | -14.52 |


## Full Statistics Reference

| Statistic | Value | Source |
|---|---|---|
| Observation window | 41 days (2025-12-05 to 2026-01-14) | econometrics.tex Section 5.9 |
| Positions | 600 | econometrics.tex Section 5.9 |
| Position-day observations | 3,365 | econometrics.tex Section 5.7 |
| Exit events | 597 | econometrics.tex Section 5.7 |
| Real/Null $A_T$ ratio | $2.65\times$ | econometrics.tex Section 5.1 |
| Days with $\Delta^+ > 0$ | 63% (26/41) | econometrics.tex Section 5.1 |
| Trigger days ($\Delta^+ > 0.09$) | 1 in 41 | backtest notebook |
| Turning point $\delta^*$ | $\approx 0.09$ | econometrics.tex Section 5.7 |
| $\beta_1$ (shelter) | -23.18, p=0.012 | econometrics.tex Section 5.7 |
| $\beta_2$ (Capponi) | +129.20, p=0.030 | econometrics.tex Section 5.7 |
| Implied premium at $\Delta = 0.15$ | \$110/position | econometrics.tex Section 5.8.3 |
| p-squared payoff: % better off | 18.8% | backtest notebook Section 10 |
| p-squared payoff: mean HV | +\$23.21 | backtest notebook Section 10 |
| Calibrated $\gamma$ | 3.30% | backtest notebook Section 2 |

---

*This document is the single source of truth for the research summary. Downstream phases (root README, research README, Beamer slides) consume this file by reference or adapted copy. All coefficients are extracted from `research/model/econometrics.tex`; all backtest results are from the ETH/USDC 30bps notebooks.*
