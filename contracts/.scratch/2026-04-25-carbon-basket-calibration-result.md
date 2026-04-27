# Carbon-Basket Calibration Result — Task 11.N.2c (Rev-5.3)

**Date:** 2026-04-25T10:26Z
**Plan reference:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2c (lines 1024-1089).
**Design doc (immutable):** `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §1, §2, §3, §4.
**Predecessor:** Task 11.N.2b.2 commit `2855240ae` — populated `onchain_xd_weekly` with eight Carbon-related `proxy_kind` series.
**Verdict:** **pathological-HALT** per design doc §4 row 4. See companion disposition memo `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md`.

---

## 1. Summary

| field | value |
|---|---|
| `decision_branch` | `pathological-HALT` |
| `basket_n_nonzero_obs` (carbon_basket_user_volume_usd) | **77** |
| `N_MIN` (pre-committed gate) | **80** |
| Gate result | **77 < 80 ⇒ HALT** |
| `MDES_FORMULATION_HASH` integrity | **PASS** (live SHA256 of `required_power` source matches `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`) |
| `required_power(80, 13, 0.40)` (Cohen f²) | **0.887746** ≥ POWER_MIN=0.80 (operative power floor preserved) |
| Rev-4 `decision_hash` | `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` (byte-exact preserved) |

The basket-aggregate user-only USD volume series falls **3 weeks short** of the pre-committed N_MIN threshold. Per design doc §4 row 4 ("Data structurally pathological"), the calibration **does NOT silently set arb-only as primary** — that would conflate stress-detection with capital-flow magnitude. The calibration raises `CalibrationStructurallyPathological`; a disposition memo is filed; the user decides next-step pivot.

---

## 2. Per-currency stats (informational)

Computed from `onchain_xd_weekly` rows tagged `carbon_per_currency_<sym>_volume_usd` over the 82-Friday panel (2024-08-30 → 2026-04-03; populated by Task 11.N.2b.2).

| currency | total_weeks | non-zero | mean USD | median USD | std USD | p95 USD | max USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| `copm` | 82 |  47 |   6,138.99 |   703.69 |    8,923.18 |  24,999.50 |   37,073.24 |
| `usdm` | 82 |   2 |     631.98 |     0.00 |    5,687.41 |       0.00 |   51,818.67 |
| `eurm` | 82 |  41 |  23,868.25 |   105.19 |   46,331.76 | 108,543.00 |  256,438.32 |
| `brlm` | 82 |  44 |  24,242.15 |    23.90 |   41,948.14 |  98,804.32 |  248,067.45 |
| `kesm` | 82 |  30 |  16,869.11 |     0.00 |   36,270.41 | 102,811.17 |  174,602.60 |
| `xofm` | 82 |   0 |       0.00 |     0.00 |        0.00 |       0.00 |        0.00 |

**Observations.**

1. **XOFm has zero user activity** across the entire panel (matches the data/carbon_celo/README.md note: "XOFm has zero user activity"). The PCA path standardizes XOFm using `safe_std = 1.0` (no division-by-zero); the column contributes zero loading weight.
2. **USDm has only 2 non-zero weeks** — also a low-activity stablecoin in the user-only partition. Its loading on PC1 is ≈ +0.08 (idiosyncratic, below the PC1_LOADING_FLOOR=0.40 convention).
3. **EURm and BRLm are the high-activity currencies** with ≈ 50% of weeks active and median activity well below mean (right-skewed distribution; whales drive aggregate volume).
4. **COPM** (the Colombia-pilot anchor) has 47 non-zero weeks — below N_MIN=80 in isolation, exactly the empirical observation that motivated the design doc §3 retirement of methodology (I) per RC-CF-1 + RC-CF-2.

---

## 3. Basket-aggregate stats

| measure | value |
|---|---|
| `proxy_kind` | `carbon_basket_user_volume_usd` |
| total weeks | 82 |
| **non-zero weeks** | **77** |
| zero weeks | 5 |
| mean USD | (computed from sum across all six per-currency columns) |
| min Friday | 2024-08-30 |
| max Friday | 2026-04-03 |

The basket-aggregate non-zero count (77) is the **union** of weeks where any of the six per-currency series is non-zero. Even with EURm + BRLm contributing the majority of activity, 5 weeks have zero basket activity — the panel does not clear the 80-week N_MIN floor.

---

## 4. PCA diagnostic (informational; not path-selecting)

PCA fitted on the standardized 6-column per-currency matrix (XOFm column safe-divided due to zero variance). Computed via `sklearn.decomposition.PCA(n_components=6)`; independent reproduction witness via numpy explicit `(X.T @ X) / n` eigendecomposition agreed to within 1e-6.

| component | variance explained |
|---|---:|
| PC1 | **0.5159** |
| PC2 | 0.2022 |
| PC3 | 0.1681 |
| PC4 | 0.1006 |
| PC5 | 0.0132 |
| PC6 | 0.0000 (XOFm-induced rank deficiency) |

### PC1 loadings (per-currency)

| currency | PC1 loading | non-trivial? (\|loading\| ≥ 0.40) |
|---|---:|:---:|
| `copm` | **−0.3010** | no |
| `usdm` | +0.0827 | no |
| `eurm` | **+0.5877** | yes |
| `brlm` | **+0.5637** | yes |
| `kesm` | **+0.4893** | yes |
| `xofm` | +0.0000 | no |

### Reading

PC1 captures ≈ 52% of the cross-currency standardized variance and is **dominated by EURm + BRLm + KESm** (all positive, all above the 0.40 non-triviality floor). **COPM loads negatively on PC1** (−0.30, idiosyncratic by the floor convention), indicating that on weeks when EURm/BRLm/KESm activity surges, COPM activity tends to be slightly below average — the Colombia slice is not co-moving with the regional EM cluster.

This is consistent with the design-doc §4 row 2 narrative ("regional-basket framing; documented limitation: 'Colombian on-chain slice too thin in isolation'") but is presented HERE only as a diagnostic — under the RC-CF-2 collapse, PCA does NOT drive primary X_d selection. The basket-aggregate is the committed primary regardless of loading distribution; the gating constraint is the N_MIN threshold, which fails.

---

## 5. CalibrationResult / exception payload

The PASS-branch `CalibrationResult` is **NOT returned**. The pathological-HALT branch raises `CalibrationStructurallyPathological` with the following structured payload (would-be `CalibrationResult` fields are recorded here for downstream provenance):

```text
CalibrationStructurallyPathological(
    basket_n_nonzero_obs = 77,
    n_min = 80,
    rationale = "Basket-aggregate carbon_basket_user_volume_usd has 77 weekly "
                "non-zero observations across the available panel; required "
                "minimum is 80. The Carbon-basket X_d thesis is empirically "
                "failing at the basket-wide level — escalate to user. Do NOT "
                "silently set arb-only as primary (would conflate stress-"
                "detection with capital-flow magnitude). See design doc §4 "
                "row 4."
)
```

For diagnostic provenance (had the gate passed, these are the fields the `CalibrationResult` would have carried):

```text
primary_choice                 = "basket_aggregate"   (locked per CR-CF-1 + RC-CF-1 + RC-CF-2)
copm_n_nonzero_obs             = 47
copm_pc1_loading               = -0.3010
basket_pc1_variance_explained  = 0.5159
decision_branch                = "PASS"   (NOT REACHED — HALT fired)
basket_n_nonzero_obs           = 77
per_currency_pc1_loadings      = {copm: -0.3010, usdm: +0.0827, eurm: +0.5877,
                                  brlm: +0.5637, kesm: +0.4893, xofm: +0.0000}
```

---

## 6. Branch traversal trace

1. Plan §1027: design-doc §4 row 4 fires — basket-aggregate 77 < N_MIN=80.
2. `compute_basket_calibration` reaches the N_MIN gate and raises `CalibrationStructurallyPathological`.
3. Orchestrator catches the exception and invokes the disposition-memo path (Step 5 of plan).
4. This memo records the calibration diagnostic (per-currency stats + PCA loadings + variance-explained) for downstream provenance.
5. Companion memo `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md` records the escalation and decision options.

---

## 7. Anti-fishing integrity check

| guard | status |
|---|---|
| `MDES_FORMULATION_HASH` matches live SHA256 of `required_power` source | **PASS** |
| `MDES_SD = 0.40` (not free-tuned) | **PASS** |
| `N_MIN = 80` (not relaxed to recover power) | **PASS** |
| `POWER_MIN = 0.80` (Rev-4 standard, unchanged) | **PASS** |
| `PC1_LOADING_FLOOR = 0.40` (informational only post-RC-CF-2) | **PASS** |

Per the §0.3 final-fix-pass anti-fishing guard, the correct response to under-coverage is HALT, **not** free-tuning N_MIN downward (e.g., to 75) to re-enter the PASS branch. The HALT discipline is preserved.

---

## 8. Files touched by Task 11.N.2c

- **Created**: `contracts/scripts/carbon_calibration.py` (pure module; 5 module-level `Final` constants; 1 frozen-dataclass `CalibrationResult`; 1 exception `CalibrationStructurallyPathological`; 1 pinned `required_power` function; 1 entry-point `compute_basket_calibration`).
- **Created**: `contracts/scripts/tests/inequality/test_carbon_calibration.py` (19 tests covering Step 0 constants/pinned-source, Step 1 PASS-branch behaviour, Step 1 independent-reproduction witness, Step 5 HALT-branch behaviour).
- **Created**: `contracts/.scratch/2026-04-25-carbon-basket-calibration-result.md` (this memo).
- **Created**: `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md` (escalation memo).
- **Modified**: NONE — calibration is READ-only against canonical DB; canonical DB checksum unchanged through this task.

---

## 9. References

- Plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2c (lines 1024-1089)
- Design doc: `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §1, §2, §3, §4
- Gate memo: `contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md` (Task 11.N.2b.1)
- Corrigendum: `contracts/.scratch/2026-04-25-carbon-basket-gate-memo-corrigendum.md` (Task 11.N.2b.2 partition rule)
- Pre-aggregation provenance: `contracts/data/carbon_celo/README.md`
- Rev-4 decision-hash anchor: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23` (= `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`)

— end of memo —
