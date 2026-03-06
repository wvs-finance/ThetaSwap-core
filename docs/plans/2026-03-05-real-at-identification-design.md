# Real A_T Identification Strategy — Design Document

**Date:** 2026-03-05
**Replaces:** Exit hazard model with equal-share proxy A_T (failed: beta_1 = -4.90, p=0.15).

## Problem Statement

The current `DAILY_AT_MAP` computes A_T with equal-share proxy x_k = 1/N:

```
A_T_proxy = SQRT(SUM(1/blocklife)) / COUNT(*)
```

This is the Ma & Crapis (2024) symmetric equilibrium — the **null hypothesis** of zero fee concentration. The exit hazard model tested whether position turnover (not fee concentration) drives exits, and correctly found no signal.

The real A_T (Eq. 1 from main.pdf) requires per-position fee shares:

```
A_T = SQRT(SUM(theta_k * x_k^2))   where x_k = fees_k / fees_total, theta_k = 1/blocklife_k
```

With real x_k from Collect events, A_T captures what Aquilina et al. (2024) document empirically: 7% of LPs capture 80% of fees. This transforms A_T from a position-turnover statistic into a fee-inequality measure.

### Literature Grounding

| Paper | A_T Component Validated |
|-------|------------------------|
| Capponi & Zhu (Optimal Exit) | A_T modulates effective phi: high A_T -> passive LP fee rate drops -> exit threshold falls |
| Capponi, Jia, Zhu (JIT) | x_k captures realized fee dilution from JIT |
| Ma & Crapis (Permissionless) | Symmetric equilibrium x_k=1/N is A_T's lower bound (the null) |
| Aquilina et al. (Dealers) | Empirical: fee share asymmetry is massive (80/20 rule) |
| Bichuch & Feinstein (FLAIR/IV) | Pool-level fee rate; A_T measures distribution across LPs |

## Solution: Compute Real A_T from Collect Events

### Step 1 — Dune Query (~10 credits)

Extract per-position Collect amounts for ETH/USDC 30bps pool during our 41-day window:

```sql
SELECT
  c.evt_block_time::date AS collect_date,
  c.owner,
  c.tickLower,
  c.tickUpper,
  c.amount0,
  c.amount1,
  b.evt_block_number - m.evt_block_number AS blocklife
FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Collect c
JOIN uniswap_v3_ethereum.UniswapV3Pool_evt_Burn b
  ON c.evt_tx_hash = b.evt_tx_hash
  AND c.tickLower = b.tickLower AND c.tickUpper = b.tickUpper
JOIN uniswap_v3_ethereum.UniswapV3Pool_evt_Mint m
  ON b.owner = m.sender AND b.tickLower = m.tickLower AND b.tickUpper = m.tickUpper
  AND m.evt_block_number < b.evt_block_number
WHERE c.contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
  AND c.evt_block_time >= DATE '2025-12-05'
  AND c.evt_block_time <= DATE '2026-01-14'
```

Output: ~600 rows with (collect_date, owner, ticks, fee_amounts, blocklife).

### Step 2 — Local Python Computation

Hardcode Dune results into `econometrics/data.py` as `RAW_COLLECT_FEES`.
New pure function in `econometrics/ingest.py`:

```python
def compute_real_daily_at(
    collect_data: Sequence[CollectFeeRow],
) -> dict[str, float]:
    """Compute real A_T per day using Eq. 1 from main.pdf.

    For each day:
      x_k = fee_k / sum(fees_on_day)
      theta_k = 1 / blocklife_k
      A_T = sqrt(sum(theta_k * x_k^2))
    """
```

### Step 3 — Drop-in Replacement

```python
# Old: DAILY_AT_MAP = {d: at for d, _, at in RAW_POSITIONS}
# New: DAILY_AT_MAP = compute_real_daily_at(RAW_COLLECT_FEES)
```

Everything downstream (build_exit_panel, logit_mle, notebook) works unchanged.

## Econometric Specification

### Model (unchanged)

```
P(exit_i,t = 1) = sigma(beta_0 + beta_1 * A_T,t-lag + beta_2 * IL_t + beta_3 * log(age_i,t))
```

- **beta_1 > 0** = higher fee concentration -> higher exit probability -> insurance demand
- Day-clustered sandwich SEs (41 clusters)
- Lag sensitivity: {1, 2, 3, 5, 7} days

### Predicted Sign Change

With equal-share proxy: beta_1 was -4.90. Proxy A_T is high when many short-lived positions exit (turnover), which correlates mechanically with high exit rates -> negative beta_1.

With real A_T: high A_T means fee share concentrated in few positions. Passive LPs earn less -> exit more. Expected: **beta_1 > 0**.

### Success Criteria

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| beta_1 sign | Positive | Capponi: lower phi -> exit |
| Cluster p-value | < 0.10 | 41 clusters is demanding |
| Dose-response | Monotonic Q1->Q4 | Exit rate increases with A_T |
| Lag robustness | beta_1 > 0 for >= 3 of 5 lags | Not driven by lag choice |

### Fallback (if beta_1 still null)

1. Add position-level controls (tickRange, L_i/L_active) — ~10 more Dune credits
2. Try position-level fee rate phi_hat_i = x_i * feeGrowth as treatment
3. Report negative result — null with correct data is informative

### Insurance Pricing Output

```
Marginal Effect = beta_1 * P_bar * (1 - P_bar)
Premium per 0.10 delta_A_T = ME * 0.10 * avg_fee_revenue * avg_remaining_hours
```

Already implemented in `marginal_effect_at_means()` — no code change needed.

## Architecture (econometrics/ package)

| File | Changes |
|------|---------|
| `types.py` | Add `CollectFeeRow` frozen dataclass |
| `data.py` | Add `RAW_COLLECT_FEES` hardcoded from Dune; recompute `DAILY_AT_MAP` |
| `ingest.py` | Add `compute_real_daily_at()` pure function |
| `hazard.py` | No changes |
| `notebooks/exit_hazard_results.ipynb` | Re-run (no code changes) |

## Constraints

- Dune free tier: ~2498 credits remaining, query costs ~10 credits
- JAX 0.9.1 CPU, uhi8 venv
- @functional-python: frozen dataclasses, free pure functions, full typing
- .gitignore has *.py — use `git add -f`

## Dune Budget

| Item | Credits |
|------|---------|
| Collect events query | ~10 |
| Remaining after | ~2488 |
| Fallback (position controls) | ~10 if needed |
