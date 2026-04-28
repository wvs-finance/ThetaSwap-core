# Pair D — Phase 2 Task 2.1 Findings (Primary OLS)

**Spec sha256:** `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`
**Panel sha256:** `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
**Results JSON sha256:** `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`
**Residuals parquet sha256:** `c1344d47ad6e3d7c78cf1d37190e3f11901ea7078884a4c35afc5dc49d89ba9e`
**Reproducibility:** seed=42; statsmodels 0.14.6 / numpy 2.4.4 / scipy 1.17.1 / pandas 3.0.2.

## §1 Sample summary

- N = 134; window 2015-01-31 → 2026-02-28 (UTC, month-end)
- `marco2018_dummy` 1-count: 62 (informational; NOT in spec primary — see §2)
- HAC: Newey-West, bandwidth = ⌊4·(134/100)^(2/9)⌋ = 4

## §2 Anti-fishing flag — orchestrator-brief vs. spec contradiction

The Phase-2 brief specified a "primary" with a `marco2018_dummy`. **Spec §5.3 verbatim has no such dummy in the primary**; per §6 the dummy is the R1 robustness alternative ONLY. (Note: Y is a ratio of expansion factors with the same FEX in numerator and denominator within each month, so any single-multiplicative empalme is operationally a no-op at the share level — Phase 1 correctly omitted it.) Per §9.1 / §9.2 / §9.7 + memories `feedback_strict_tdd` and `feedback_pathological_halt_anti_fishing_checkpoint`, the spec governs. **Authoritative result = spec-verbatim primary**; dummied variant reported as off-spec sensitivity (§5).

## §3 Spec-verbatim primary OLS (AUTHORITATIVE)

`Y_broad_logit = α + β_6·log_cop_usd_lag6 + β_9·log_cop_usd_lag9 + β_12·log_cop_usd_lag12 + ε`.

| Coef | Point | HAC SE | t | p (two-sided) |
|---|---|---|---|---|
| const | -0.5161 | 0.1994 | -2.589 | 0.010 |
| log_cop_usd_lag6 | **+0.1089** | 0.0777 | +1.402 | 0.161 |
| log_cop_usd_lag9 | **+0.0116** | 0.0832 | +0.140 | 0.888 |
| log_cop_usd_lag12 | **+0.0162** | 0.0834 | +0.194 | 0.846 |

**Composite β = β_6 + β_9 + β_12** (variance c'Σ_HAC c, c=[0,1,1,1]):

- Point: **+0.13671** | HAC SE: 0.02465 | t = **+5.5456**
- One-sided p (H1: β > 0): **≈1.5×10⁻⁸**
- One-sided 95% CI lower: **+0.09616** (excludes zero by ~4 SE)
- R² = 0.168; joint-F (β_6 = β_9 = β_12 = 0): F = 10.52, p = 3.1×10⁻⁶

### PRIMARY VERDICT: **PASS** (spec §3.1: β_composite > 0 AND p_one ≤ 0.05)

**Individual lag-sign pattern (β_6 / β_9 / β_12): +/+/+** — all three lags positive, consistent with the BPO Baumol → wage-arbitrage → offshoring chain. Per spec §5.3 + MQS R2: highly serially correlated lag regressors inflate individual SEs but the negative cross-coefficient covariance terms deflate the composite SE; reading "individual lags weren't significant" is methodologically incorrect. Composite is significant at >5σ.

## §4 Diagnostics

| Test | Stat | p | Concern |
|---|---|---|---|
| Breusch-Pagan | LM=2.07 | 0.558 | None |
| Durbin-Watson | 1.416 | — | Mild +AR; HAC absorbs |
| Jarque-Bera | 0.87 | 0.648 | None |
| Skew / excess kurt | -0.05 / +0.38 | — | Gaussian-like |
| ADF on residuals | -3.80 | 0.003 | Stationary |
| Ljung-Box L=4 | 23.5 | 0.0001 | **Residual AR present** |
| Ljung-Box L=12 | 39.5 | 0.0001 | **AR at annual lag** |

Ljung-Box rejections at L=4 / L=12 indicate residual autocorrelation beyond bandwidth-4 NW. **This is precisely what spec §7 R4 (HAC NW with L=12) pre-registered for.** Anticipated, not a deviation. Clause-B (B-ii) `|skew|>1` OR `excess kurt>3` does NOT fire — moot since primary PASSES.

## §5 Off-spec sensitivity — orchestrator-brief variant WITH dummy (NON-AUTHORITATIVE)

Coefficients with HAC SE: const -0.080 (0.459), lag6 +0.083 (0.079), lag9 +0.007 (0.084), **lag12 -0.009** (0.077), dummy +0.028 (0.027). Composite β = +0.0815, HAC SE = 0.0581, t = 1.40, **p_one = 0.080** (sign +/+/−; would map to ESCALATE Clause A in spec §3.3). The dummy absorbs ~55% of composite-β magnitude — standard collinearity-induced obscuring of a cumulative-lag effect when a regime indicator is added without theoretical pre-justification. This is exactly why the spec excludes it.

## §6 Recommendation for Phase 2.2 / 2.3

Spec-verbatim primary triggers §3.1 PASS. Per §8.1 step 4(a), if R-row consistency (Task 2.2 R1-R4) is AGREE or MIXED, verdict = PASS and Stage-2 M sketch unblocked. **Escalation NOT triggered** (Clause A requires p ∈ (0.05, 0.20]; primary p = 1.5×10⁻⁸). Task 2.2 must run; residual-AR diagnostic pre-validates R4 (HAC L=12) materiality.

**Orchestrator must confirm**: Phase 2 proceeds on spec-verbatim primary (recommended per §9.1) — OR the dummied variant supersedes, which would require a CORRECTIONS block + 3-way review per §9.5 / §9.7 + new spec sha256.

---
**Outputs (absolute paths):**
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/simple-beta-pair-d/results/primary_ols.json`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/simple-beta-pair-d/results/primary_ols_residuals.parquet`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/simple-beta-pair-d/scripts/task_2_1_primary_ols.py`
