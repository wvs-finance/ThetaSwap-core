# Exit Hazard Model — Design Document

**Date:** 2026-03-05
**Replaces:** Duration model (`log(blocklife) ~ A_T`) which failed due to mechanical collinearity.

## Problem Statement

The duration model produced beta_1 = +10.07 (positive) because:
1. **Mechanical collinearity:** A_T contains theta_k = 1/blocklife, so blocklife is inside A_T's construction.
2. **Wrong response variable:** LPs are long theta — positive duration-concentration correlation is natural, not informative.

## Solution: Binary Exit Hazard (Discrete-Time Survival Model)

### Response Variable

Y_i,t = 1 if position i exits on day t, 0 otherwise.

This is completely outside A_T's construction:
- A_T uses theta_k = 1/blocklife and x_k = fee_share — neither is the binary exit decision.
- A_T,t reflects positions that ALREADY exited by time t (theta_k computed at afterRemoveLiquidity).
- Using lagged A_T (t-1 or t-lag) breaks any same-day simultaneity.

### Model Specification

```
P(exit_i,t = 1) = sigma(beta_0 + beta_1 * A_T,t-lag + beta_2 * IL_t + beta_3 * log(age_i,t))
```

where sigma(z) = 1/(1+exp(-z)) is the logistic function.

- **beta_1 > 0** = higher concentration increases exit probability = **insurance demand signal**
- **beta_2**: IL control (nuisance parameter, absorbs price-movement risk)
- **beta_3**: Duration dependence (log-linear baseline hazard)
- **lag**: Default 1 day, sensitivity sweep over {1, 2, 3, 5, 7}

### Data Construction (Zero Dune Cost)

From existing 600 positions in `econometrics/data.py`:

1. Compute `mint_date = burn_date - blocklife / 7200 days`
2. For each day t in the 41-day daily_at_map window:
   - Identify positions alive: `mint_date <= t <= burn_date`
   - Y_i,t = 1 if burn_date == t, else 0
   - A_T treatment = daily_at_map[t - lag]
   - IL = il_map[t]
   - age_i,t = (t - mint_date).days, floored at 1

Expected panel: ~5,000-12,000 position-day observations, ~600 exits.

### Estimation

**Maximum Likelihood** (logit log-likelihood):

```
L(beta) = sum_i,t [ Y_i,t * log(sigma(X*beta)) + (1 - Y_i,t) * log(1 - sigma(X*beta)) ]
```

Optimized via JAX `jax.scipy.optimize.minimize` (BFGS) or Newton-Raphson.

### Inference

**Day-clustered sandwich standard errors:**

```
V(beta_hat) = H^{-1} * (sum_t g_t * g_t') * H^{-1}
```

where g_t = sum of scores within day t, H = Hessian. 41 clusters (days).

Positions on the same day share the same A_T shock, so clustering by day is essential.

### Specification Tests

1. **Quartile dose-response:** Split by A_T quartile, compare exit rates. Monotonic increase = dose-response.
2. **Lag sensitivity:** Sweep lag in {1, 2, 3, 5, 7} days.
3. **Nested models:** Full vs A_T-only vs IL-only.
4. **Age interaction:** beta_4 * A_T * log(age) — does concentration hit young vs old positions differently?

### Insurance Pricing Connection

1. **Marginal effect:** ME = beta_1 * P_bar * (1 - P_bar)
2. **Expected fee loss per 0.10 A_T shock:** ME * 0.10 * avg_daily_fee_revenue * avg_remaining_days
3. **Actuarially fair premium:** = expected fee loss (floor for WTP)
4. **Market sizing:** premium * number_active_positions = total addressable insurance demand
5. **Funding rate floor:** premium / position_value informs minimum viable funding rate for ThetaSwap CFMM

### Architecture (econometrics/ package)

| File | Changes |
|------|---------|
| `types.py` | Add `PanelRow`, `LogitResult`, `MarginalEffect` frozen dataclasses |
| `ingest.py` | Add `build_exit_panel()` — constructs position-day panel from existing data |
| `hazard.py` | NEW — logit MLE, clustered SEs, marginal effects, specification tests |
| `data.py` | No changes (existing data sufficient) |
| `notebooks/exit_hazard_results.ipynb` | NEW — display notebook |

### Constraints

- JAX 0.9.1 CPU, uhi8 venv
- @functional-python: frozen dataclasses, free pure functions, full typing
- Zero additional Dune credits
- .gitignore has *.py — use `git add -f`
