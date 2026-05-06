# Dev-AI-Cost Stage-1 simple-β — Colombia Section J 2015-2026

**Gate Verdict: FAIL** — β̂_composite = −0.146 (HAC L=12 SE = 0.085, t = −1.726, p_one = 0.958, n = 134). Sign-flipped from positive expectation per Baumol→arbitrage→offshoring chain.

**Migration provenance**: this iteration was migrated from `contracts/.scratch/dev-ai-stage-1/` to `contracts/notebooks/dev_ai_cost/` on 2026-05-06 per user directive: *"the miss-specifications serve for learning AND give insights AND the data is preserved for testing new things"*. Mirrors `fx_vol_cpi_surprise/Colombia/` canonical 3-NB pattern.

## Hypothesis (rejected)

Y_p = Colombian young-worker (14-28) employment share in CIIU Rev. 4 Section J ("Información y Comunicaciones" — software / data-processing / telecom / information services). X = log(COP/USD) lagged 6, 9, 12 months. Sample window 2015-01 → 2026-02 (134 monthly observations; Pair D Option-α' window inheritance).

Sign expectation pre-pinned positive per Baumol cost disease → US-Colombia tech-labor wage arbitrage → US tech-firm offshoring of Section J ICT services → Colombian Section J young-worker employment share rises at lag.

## Primary Results

| Specification | β̂_composite | HAC SE | t-stat | p_one | Sign | n |
|---|---|---|---|---|---|---|
| **Primary OLS** (HAC L=12) | **−0.14613** | 0.0847 | **−1.726** | 0.958 | **−** | 134 |
| OLS-homoskedastic (per spec §3.4 mandate) | −0.14613 | 0.0649 | −2.252 | 0.988 | − | 134 |
| R1 (2021 regime dummy) | −0.51294 | 0.0918 | −5.59 | 1.00 | − | 134 |
| **R2 (Section M sensitivity)** | **+0.45483** | 0.0962 | **+4.73** | **1.13e-06** | **+** | 134 |
| R3 (raw OLS, no logit) | −0.00340 | 0.00194 | −1.76 | 0.96 | − | 134 |
| R4 (HAC SE substitution; same point estimate) | −0.14613 | 0.0847 | −1.73 | 0.958 | − | 134 |

Lag-pattern decomposition (composite = β_6 + β_9 + β_12):
- β_6 share: +10.98% / β_9 share: +6.38% / **β_12 share: +82.64%** (long-lag dominant)
- Pair D contrast: β_6 ≈ 80% concentration (RC FLAG #3); this iteration is opposite

## Robustness Battery (NB03)

| Test | Verdict | Role |
|---|---|---|
| §7.1 R-row consistency | MIXED (n_agree=3/4; R2 sign-DISAGREE) | §8.1 step 2 input |
| §3.5 SUBSTRATE_TOO_NOISY (>2 of 4 sign-flipped) | False | §8.1 + §3.5 pre-empt |
| §6 v1.0.2 κ-tightened pair (R1 + R3 BOTH sign-AGREE) | True at NEGATIVE sign | §3.3 Clause-A |
| §3.3 Clause-A (κ-tightened) | NOT triggered | Routing |
| §8.1 step 4(d) FAIL routing | β ≤ 0 AND p > 0.05 AND Clause-B does NOT fire | Final |

## Escalation Suite (NB03 Trio 6; pre-authorized per §9.6)

| Disjunct | β | p_one | Sign | §3.4 verdict |
|---|---|---|---|---|
| D-i (quantile τ=0.90) | −0.129 | 0.645 | − | FAIL (β not > 0) |
| D-ii (GARCH(1,1)-X composite) | −0.154 | 0.993 | − | FAIL (β not > 0) |
| D-iii (EVT POT upper-tail) | **+0.113** | **0.012** | **+** | FAIL per spec §3.4 (literal text requires β > 0 AND p ≤ 0.10; D-iii satisfies BOTH; under strict-§5.5 reading the escalation suite should not have been run because §3.3 trigger never fired — see disposition memo) |

Per spec §3.4 literal: "ESCALATE-PASS fires if any one or more of the three disjuncts hold". D-iii literally satisfies (β>0, p≤0.10). However, spec §5.5 line 252 says "escalation suite is run if and only if §3.3 ESCALATE-trigger fires" — and §3.3 ESCALATE-trigger did NOT fire (Clause-A: β not > 0; Clause-B: B-i+B-ii both False). Under strict §5.5 reading, the D-iii result is methodologically inadmissible. **User pick (Option C)** preserves D-iii for cross-iteration framing while keeping verdict = FAIL per §5.5 strict; flag spec v1.0.3 reconciliation of §5.5/§9.6 contradiction.

## Per-Test Gate Table (§3 verdict primitives)

| Test | Verdict | Role |
|---|---|---|
| §3.1 PASS-trigger (β > 0 AND p ≤ 0.05) | FAIL TO TRIGGER | Primary gate |
| §3.2 FAIL (β ≤ 0 wrong-signed-significant or β > 0 p > 0.20) | FAIL via 4(d) | Primary gate |
| §3.3 ESCALATE Clause A (β > 0 AND p ∈ (0.05, 0.20]) | NOT FIRED | Auxiliary |
| §3.3 ESCALATE Clause B (B-i AND B-ii) | NOT FIRED (B-i False, B-ii False) | Auxiliary |
| §3.5 SUBSTRATE_TOO_NOISY (>50% R-rows sign-flipped) | NOT FIRED (1/4 sign-flipped) | Diagnostic |
| §6 v1.0.2 κ-tightened pair (R1 OR R3 sign-different) | NOT FIRED (BOTH AGREE at negative) | Verdict overlay |
| **§8.1 step 4(d) FAIL** | **FIRES** | **Primary verdict** |

Aggregation rule: §8.1 step 4(d) FAIL is the final verdict. §5.5 escalation was run under disputed §9.6 pre-authorization framing; D-iii literal pass preserved as Phase-3 finding for future Section M iteration consideration (per Option C disposition).

## CORRECTIONS-κ FLAG-A + FLAG-B (Phase 1)

Spec §1 v1.0.2 acknowledges:
- **FLAG-A**: Section J cell_count realized [94, 267] vs Y feasibility memo §1.1 baseline [700, 1200] — 5-7× below; 1 sub-100 month at 2024-10-31 (post-2021 era → R1 captures); 55% of months below 150
- **FLAG-B**: Section J raw_share realized [0.014, 0.031] vs spec §5.1 [0.04, 0.10] — 1.3-3× below; logit-derivative `1/[Y(1-Y)]` realized [33, 73] (median 45.4) vs spec-anticipated 2.34× baseline (3-7× larger)

Wave-2 MQS FLAG-MED disambiguation (computed at execution; binding for Phase-3 §11.X(a) per spec §9.17(a)):

| Amplification framing | Realized value |
|---|---|
| Linear within-range ratio | 2.750× to 2.971× |
| Linear cross-corner ratio (worst) | 6.446× |
| Variance ratio (quadratic) within-range | 7.563× to 8.830× |
| Variance ratio cross-corner | 41.547× |
| Combined cell-count + derivative typical | ~3,685× (vs Pair D) |
| Combined cell-count + derivative worst-corner | ~14,121× (vs Pair D) |

User pick on Task 1.1 disposition (cell-pathology + raw-share gap): **Option A** (Proceed-with-FLAG-disclosure; R1 + R3 hedges become more load-bearing). Disposition at `dispositions/disposition-memo-task-1.1-flag-A-flag-B.md`.

## Empalme residual bias (NB02 Trio 1 boundary_anomaly)

DANE Marco-2005 → Marco-2018 empalme correction did NOT fully neutralize the methodology break:
- Boundary differential `Y_p_logit[2021-01] − Y_p_logit[2020-12]` = +0.375 logit-units
- 3× envelope (within-segment median |ΔY|): 0.335
- **boundary_anomaly = TRUE** (0.375 > 0.335)
- β_regime_R1 = +0.188 (t=+4.36): post-2021 era has higher Y_p_logit conditional on X-lags

This is an empirical methodological finding for future-iteration spec authoring on DANE GEIH-based panels.

## Most striking finding — Section M positive surprise

R2 sensitivity arm (Y_s2 = Section M, professional/scientific/technical/admin Sections {69-75}) produces β = **+0.4548** at p = **1.13e-06**. This empirically RESOLVES the spec §9.16 compositional-accounting ambiguity:

> Pair D's Section G–T positive β = +0.137 was NOT a re-discovery of Section J ICT signal. Section J carries OPPOSITE-sign signal; Pair D's PASS came from Section M-style subsectors (consultants / legal / accounting / scientific R&D / admin services).

(Per spec §9.16(c) the formal resolution requires (G–T minus J) decomposition; the Section M comparator here is *consistent with* but not *equivalent to* the spec-authorized resolution. Disposition: flagged-not-resolved per spec literal.)

This opens a **candidate-next-iteration**: Section M as primary Y for a separate iteration if framework targets align with broader knowledge-worker scope.

## Six-school multi-framework interpretation (Phase 2.5 EA application)

Per `ea_install_path_pin = option_iii_manual_framework_application`, the orchestrator applied the Economist Analyst skill's 6-school framework manually. Two schools natively predict the realized sign-flip:

- **Austrian** (capital-structure unwind in post-ZIRP era contracts AI-vendor labor demand → β NEGATIVE)
- **Neoclassical Synthesis** (sector-specific import/export elasticity asymmetry explains Section J β<0 vs Section M β>0)

Cross-school agreement: 5 of 6 schools (Classical, Keynesian, Austrian, Monetarist, Neoclassical Synthesis) read the R2 Section M positive β as a real Section-M-specific transmission, not noise. Anti-fishing disclosure: Austrian + NCS predictions were applied AFTER seeing data; not pre-registered.

Full multi-school analysis: `estimates/EA_FRAMEWORK_APPLICATION.md`.

## Reconciliation

| Check | Verdict |
|---|---|
| HAC vs OLS-homoskedastic primary SE | DEVIATION-ACKNOWLEDGED (NB02 Trio 2 fit primary with HAC; spec §3.4 mandates OLS-homoskedastic; both numerics reported in PRIMARY_RESULTS.md + MEMO §10) |
| §5.5/§9.6 spec-internal contradiction | Disposition memo at `dispositions/disposition-memo-3way-review-D-iii-spec-contradiction.md`; user pick Option C (FAIL strict §5.5 + D-iii preservation) |
| §9.16 compositional-accounting (Section J ⊂ G–T) | flagged-not-resolved per spec §9.16(c); R2 Section M result is *consistent with* but not *equivalent to* the spec-authorized (G–T minus J) decomposition |
| §3.5 SUBSTRATE_TOO_NOISY check | NOT FIRED (1/4 sign-flipped; threshold ≥3) |
| §7.1 R-row classification | MIXED (n_agree=3/4) |
| §6 v1.0.2 κ-tightened pair | CLEARS at NEGATIVE sign (R1 + R3 BOTH AGREE) |
| §3.4 escalation disjunction (literal) | D-iii passes (β>0, p=0.012); D-i + D-ii FAIL |
| §3.4 escalation disjunction (under strict §5.5) | inadmissible (§3.3 trigger never fired) |

## Folder structure

```
contracts/notebooks/dev_ai_cost/
├── env.py                                 # path constants + verify_panel + helpers
├── references.bib                         # BibTeX (12 entries)
├── 01_data_eda.ipynb                      # NB01 (15 cells; 4 trios + skeleton)
├── 02_estimation.ipynb                    # NB02 (16 cells; 4 trios + skeleton)
├── 03_tests_and_sensitivity.ipynb         # NB03 (22 cells; 6 trios + skeleton)
├── README.md                              # This file
├── data/
│   ├── panel_combined.parquet             # Joint Y × X panel (134 rows, 11 cols)
│   ├── geih_young_workers_section_j_share.parquet  # Y_p Section J
│   ├── geih_young_workers_section_m_share.parquet  # Y_s2 Section M
│   ├── cop_usd_panel.parquet              # X COP/USD lag panel (135 rows; X-back-extension)
│   ├── DATA_PROVENANCE.md                 # Audit trail (606 lines; Tasks 1.1+1.2+1.3 sections)
│   ├── logs/                              # Task 1.1 ingest logs + per-month diagnostics
│   └── scripts/                           # Task 1.1 ingest_geih_section_jm.py
├── scripts/
│   └── build_cop_usd_panel.py             # Task 1.2 X panel constructor
├── estimates/                             # Notebook execution outputs
│   ├── PRIMARY_RESULTS.md                 # NB02 Trio 3 emit
│   ├── ROBUSTNESS_RESULTS.md              # NB03 Trio 5 emit
│   ├── ESCALATION_RESULTS.md              # NB03 Trio 6 emit
│   ├── gate_verdict.json                  # Machine-readable verdict
│   ├── EA_FRAMEWORK_APPLICATION.md        # Phase 2.5 6-school analysis
│   └── MEMO.md                            # Phase 3 result memo (final, post-3-way-review)
├── dispositions/                          # Pathological-HALT disposition memos (Option-A/C picks)
│   ├── disposition-memo-task-1.1-flag-A-flag-B.md
│   └── disposition-memo-3way-review-D-iii-spec-contradiction.md
├── figures/                               # matplotlib outputs (inline in notebooks)
├── pdf/                                   # Reserved (per fx_vol convention; empty)
└── _nbconvert_template/                   # Reserved (per fx_vol convention; empty)
```

## Spec + plan + Phase-1 commit pins

- **Spec v1.0.2**: `contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md`
  - decision_hash (sentinel-intact): `7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a`
  - on-disk file sha256: `d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e`
  - committed at `c4e0032a0`
- **Plan v1.1.1**: `contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md`
  - on-disk file sha256: `772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036`
  - committed at `354841f3f`
- **Phase 1 Gate B1 close**: commit `627f509b8` (Task 1.3 `panel_combined.parquet` emission)
- **Phase 2 close**: commit `6354fc82b` (NB01 + NB02 + NB03 executed; verdict FAIL)
- **Pair D PASS verdict precedent (sibling)**: spec sha `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`; β=+0.13670985; HAC SE 0.02465; t=+5.5456; p_one=1.46e-08; project memory `project_pair_d_phase2_pags`

## Spec v1.0.3 reconciliation flag (NEW per Phase-3 3-way review disposition)

Spec §5.5 line 252 ("escalation suite run if and only if §3.3 ESCALATE-trigger fires") and spec §9.6 (per NB03 Trio 6 dispatch brief reading: "ran whether or not mean-OLS passed") are CONTRADICTORY on the EXECUTION question. NB03 Trio 6 ran §5.5 under §9.6 pre-authorization framing. Under strict §5.5 reading the escalation should not have been run; under loose §9.6 reading D-iii literally passes → ESCALATE-PASS verdict.

User pick (Option C) holds verdict = FAIL per strict §5.5 (the load-bearing rule); preserves D-iii numerics in MEMO §11.X(d) as Phase-3 finding for future iterations; flags spec v1.0.3 reconciliation. Future Pair-D-style iterations should resolve §5.5/§9.6 unambiguously before §5.5 invocation.

## Reproducibility

To re-execute the iteration end-to-end:

```bash
# Activate venv
source contracts/.venv/bin/activate

# Re-execute notebooks in order
cd contracts/notebooks/dev_ai_cost
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 01_data_eda.ipynb
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 02_estimation.ipynb
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 03_tests_and_sensitivity.ipynb

# Outputs populate at estimates/
ls estimates/
# PRIMARY_RESULTS.md  ROBUSTNESS_RESULTS.md  ESCALATION_RESULTS.md  gate_verdict.json  MEMO.md  EA_FRAMEWORK_APPLICATION.md
```

Raw data sources (locally cached):
- DANE GEIH micro-data: 58 ZIPs at `contracts/.scratch/simple-beta-pair-d/data/downloads/` (6.5 GB; Pair-D-cached, dev-AI re-used)
- Banrep TRM daily: `contracts/data/structural_econ.duckdb` table `banrep_trm_daily` (cached 2026-04-16 from datos.gov.co Socrata API)

End of dev_ai_cost iteration README.
