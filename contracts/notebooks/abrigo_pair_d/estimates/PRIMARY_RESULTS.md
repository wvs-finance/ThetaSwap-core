# Pair D NB02 — PRIMARY_RESULTS

**Spec sha256 (governing):** `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`
**Panel sha256:** `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
**Committed primary_ols.json sha256:** `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`
**N:** 134 | **Window:** 2015-01-31 → 2026-02-28 | **HAC NW bw:** 4

## §1 PRIMARY (spec §5.3 verbatim — AUTHORITATIVE)

`Y_broad_logit = α + β_6·log_cop_usd_lag6 + β_9·log_cop_usd_lag9 + β_12·log_cop_usd_lag12 + ε`

| Coef | Point | HAC SE | t | p (two-sided) |
|---|---|---|---|---|
| const | -0.516062 | 0.199328 | -2.589 | 0.0096 |
| log_cop_usd_lag6 | **+0.108899** | 0.077671 | +1.402 | 0.1609 |
| log_cop_usd_lag9 | **+0.011648** | 0.083043 | +0.140 | 0.8884 |
| log_cop_usd_lag12 | **+0.016162** | 0.083310 | +0.194 | 0.8462 |

**Composite β = β_6 + β_9 + β_12** (contrast `c = [0, 1, 1, 1]`, `Var(c'β) = c'Σ_HAC c`):

- Point: **+0.13670985**
- HAC SE: **0.02465197**
- t-stat: **+5.5456**
- One-sided p (H1: β > 0): **1.464781e-08**
- One-sided 95% CI lower: **+0.096161**
- Two-sided 95% CI: [+0.088393, +0.185027]
- Individual-lag sign pattern (β_6 / β_9 / β_12): **+/+/+**
- R² = 0.1677 (R²_adj = 0.1485); joint F-test β_6 = β_9 = β_12 = 0: F = 10.5193, p = 3.053311e-06

### §2 §3 Verdict-tree mapping (preliminary, pre-NB03 R-consistency)

| Spec ref | Check | Truth |
|---|---|---|
| §3.1 | `β > 0 AND p_one ≤ 0.05` | **True** |
| §3.3 Clause A | `β > 0 AND p_one ∈ (0.05, 0.20]` | False |
| §3.4 Clause B-ii | `\|skew\|>1` OR `excess_kurt>3` | False |
| §3.4 Clause B FAIL | `β ≤ 0` OR `p > 0.20` | False |

**PRIMARY VERDICT (preliminary): PASS**

Joint-verdict integration deferred to NB03 §5 per spec §8.1 step 4.

### §3 Diagnostics (residuals from primary OLS)

- Breusch-Pagan: LM = 2.0717, p = 0.5576 → no heteroskedasticity
- Durbin-Watson: 1.4157 → mild +AR; HAC absorbs
- Jarque-Bera: stat = 0.8692, p = 0.6475 → residuals near-Gaussian
- Skew: -0.0511 (`|skew| ≤ 1` → §3.4 B-ii does NOT fire)
- Excess kurtosis: +0.3811 (`≤ 3` → §3.4 B-ii does NOT fire)
- ADF on residuals: stat = -3.7985, p = 0.0029 → stationary
- Ljung-Box L=4: stat = 23.5321, p = 9.9111e-05 → AR present (ANTICIPATED; addressed by NB03 R4 HAC NW L=12)
- Ljung-Box L=12: stat = 39.4745, p = 8.7871e-05 → AR at annual lag (ANTICIPATED; addressed by NB03 R4 HAC NW L=12)

## §4 OFF-SPEC SENSITIVITY (orchestrator-brief variant WITH marco2018_dummy — NON-AUTHORITATIVE)

The Phase-2 orchestrator brief specified a "primary" OLS that adds `marco2018_dummy` (1 if `t ≥ 2021-01-01` else 0). This contradicts spec §5.3 verbatim, which has NO such dummy in the primary; per §6 the dummy is the R1 robustness alternative ONLY. Per §9.1 / §9.2 / §9.7 the spec governs. The dummied variant is reported here for transparency.

**Composite β over [const, lag6, lag9, lag12, marco2018_dummy]** (`c = [0, 1, 1, 1, 0]`):

- Point: **+0.081456**
- HAC SE: 0.058051
- t-stat: +1.4032
- One-sided p: **0.080282**
- One-sided 95% CI lower: -0.014030
- Individual-lag sign pattern: **+/+/-** (lag-12 flips sign)
- `marco2018_dummy` point: +0.028285 (HAC SE 0.026642)

**Verdict the dummied variant WOULD have mapped to (NON-AUTHORITATIVE): ESCALATE (Clause A).** This would have triggered the §3.3 Clause A escalation suite per spec §5.5 — quantile / GARCH-X / lower-tail. Per spec §9.1, the spec governs and the §3 verdict (PASS) stands.

## §5 Cryptographic round-trip

- `primary_ols.json` sha256: `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf` — verified
- All §2 composite-β scalars reproduced to 1e-9 absolute tolerance against committed JSON
- All §4 off-spec composite-β scalars reproduced to 1e-9 absolute tolerance against committed JSON `off_spec_sensitivity_orchestrator_brief` block

**Recommendation for NB03 (Phase 2.2 / 2.3).** Spec-verbatim primary triggers §3.1 PASS. Per §8.1 step 4(a), if R-consistency (R1–R4 from NB03) is AGREE or MIXED, joint verdict = PASS and Stage-2 M sketch unblocked. Escalation NOT triggered. Task 2.2 must run; residual-AR diagnostic pre-validates R4 (HAC L=12) materiality.
