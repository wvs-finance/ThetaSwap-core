# Carbon-Basket Calibration Result — Task 11.N.2c (Rev-5.3.1, post-CORRECTIONS)

**Date:** 2026-04-25T(post-pathological-HALT)Z
**Plan reference:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2c (lines 1024-1089) + CORRECTIONS block (Rev-5.3.1).
**Design doc (immutable):** `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §1, §2, §3, §4.
**Predecessor:** Rev-5.3 commit `13cfe5f56` (pathological-HALT verdict at original N_MIN=80) + user-approved path α (relax N_MIN to 75).
**Verdict:** **PASS** per design doc §4 row 1.

---

## 1. Summary

| field | value |
|---|---|
| `decision_branch` | `PASS` |
| `primary_choice` | `basket_aggregate` (locked per design doc §1, §4) |
| `basket_n_nonzero_obs` (carbon_basket_user_volume_usd) | **77** |
| `N_MIN` (post-Rev-5.3.1 CORRECTIONS) | **75** |
| Gate result | **77 ≥ 75 ⇒ PASS** |
| `MDES_FORMULATION_HASH` integrity | **PASS** (live SHA256 = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`) |
| `required_power(75, 13, 0.40)` (Cohen f²) | **0.8638** ≥ POWER_MIN=0.80 ✓ |
| `required_power(77, 13, 0.40)` | 0.8739 |
| `required_power(80, 13, 0.40)` (original anchor) | 0.8877 |
| Rev-4 `decision_hash` | `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` (byte-exact preserved) |

---

## 2. PCA cross-validation (informational)

| field | value |
|---|---|
| Basket PC1 variance-explained | 0.5159 |
| COPM loading on PC1 | **-0.3010** |
| `PC1_LOADING_FLOOR` (cross-validation convention) | 0.40 |
| COPM cross-validation status | idiosyncratic (\|loading\| < floor) — **informational only**, does NOT change primary X_d which is committed to basket-aggregate |

### Per-currency PC1 loadings

| currency | PC1 loading | non-zero weeks of 82 | direction |
|---|---:|---:|---|
| EURm | +0.5877 | 41 | dominant basket driver |
| BRLm | +0.5637 | 44 | dominant basket driver |
| KESm | +0.4893 | 30 | secondary basket driver |
| COPM | **-0.3010** | 47 | **anti-correlated with EU/BR/KE trio** |
| USDm | +0.0827 | 2 | ~zero (sparse activity) |
| XOFm | +0.0000 | 0 | zero (no activity) |

**Notable**: COPM loads negatively on PC1, opposite the EURm/BRLm/KESm trio. This means COPM weekly activity is anti-correlated with the dominant EU/BR/KE block — when EU+BR+KE are active, COPM is quiet, and vice-versa. This is itself an empirically interesting finding for downstream Task 11.O resolution-matrix interpretation; documented here as informational-only (not a gate).

---

## 3. Rationale (rev-2)

> Basket-aggregate carbon_basket_user_volume_usd has 77 weekly non-zero observations ≥ N_MIN=75 (relaxed from 80 per Rev-5.3.1 CORRECTIONS); primary X_d locked to carbon_basket_user_volume_usd per CR-CF-1 + RC-CF-1 + RC-CF-2. PC1 explains 0.5159 of the standardized per-currency variance; COPM loading on PC1 = -0.3010 (idiosyncratic per |loading| ≥ 0.4 convention). PASS verdict; downstream Task 11.N.2d unblocked.

---

## 4. CORRECTIONS-block reference

The N_MIN relaxation 80 → 75 is documented in:
1. Source: `contracts/scripts/carbon_calibration.py` line 109+ (Final constant + 8-line docstring rationale citing scipy power computations)
2. Test: `contracts/scripts/tests/inequality/test_carbon_calibration.py` line 71+ (`test_n_min_is_75` asserts the new value)
3. Plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2c CORRECTIONS-Rev-2 block (this commit)
4. Calibration result memo: this file (supersedes `2026-04-25-carbon-basket-calibration-result.md`)

Anti-fishing trail: pathological-HALT verdict was filed at commit `13cfe5f56`; user reviewed the disposition memo + 4 enumerated pivot options + selected path α (relax threshold with documented rationale); the relaxation goes through CORRECTIONS-block discipline AND preserves POWER_MIN ≥ 0.80 at the operative MDES_SD = 0.40 (NOT a free-tune to chase a power target). 3-way review of this CORRECTIONS revision dispatched in parallel; pending convergence.

---

## 5. Hand-off to Task 11.N.2d

Task 11.N.2d (Y₃ inequality-differential dataset construction) is now unblocked. Inputs:
- Primary X_d: `carbon_basket_user_volume_usd` (82 Fridays, 77 non-zero, 2024-08-30 → 2026-04-03) — load via `econ_query_api.load_onchain_xd_weekly(proxy_kind="carbon_basket_user_volume_usd")`
- Diagnostic X_d's: `carbon_basket_arb_volume_usd`, 6 per-currency, supply-channel `net_primary_issuance_usd`, distribution-channel `b2b_to_b2c_net_flow_usd`
- Y₃ design doc §1, §5: per-country differentials Δ_country = R_equity + Δlog(WC_CPI) for CO/BR/KE/EU; equal-weighted aggregation
