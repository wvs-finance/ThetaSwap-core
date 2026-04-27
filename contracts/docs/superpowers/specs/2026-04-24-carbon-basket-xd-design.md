# Carbon-Basket X_d Structural Design

**Date:** 2026-04-24
**Status:** Brainstorm-converged; awaiting plan-fold + 3-way review.
**Trigger:** Task 11.N.2 research (`contracts/.scratch/2026-04-24-copm-bot-attribution-research.md`) identified the dominant on-chain COPM addresses as Bancor Carbon DeFi protocol contracts (CarbonController + BancorArbitrage / Arb Fast Lane). The 94.5% of COPM Transfer events previously dismissed as "bot noise" is actually the protocol-level Carbon basket-rebalancing activity that operates the Mento working-class-stablecoin basket against the global-asset basket — a direct on-chain proxy for capital flow across class boundaries.
**Brainstorm trail:** see this session's superpowers:brainstorming invocation; user approvals on Sections 1–5 below.

---

## 1. Architecture (data flow)

```
Full Mento basket ingestion
        ↓
  ~613k Carbon TokensTraded + ArbitrageExecuted events
  across 6 Mento stablecoins × 4 global tokens, Sep 2024 → today
        ↓
Calibration exercise
  ├─ Primary methodology (I): statistical-power-driven
  │    Pick the variant (COPM-only OR basket-aggregate) with
  │    ≥ N_min weekly non-zero obs AND ≥ power_min for the 13-regressor
  │    specification at MDES = 0.20 SD (Rev-4 anchor)
  └─ Cross-validation methodology (II): PCA-driven
       Per-currency PCA on weekly series; report COPM loading on PC1
       and PC1's variance-explained share
        ↓
Primary X_d (calibration output)
  ├─ User-initiated trades only, weekly Friday-anchored America/Bogota
  ├─ Volume-weighted USD magnitude crossing Mento↔global boundary
  └─ Either: COPM-only (if pass N_min) OR basket-aggregate
        ↓
Diagnostic columns (always populated)
  ├─ X_d_arb_only        — Arb Fast Lane volume crossing the same boundary
  ├─ X_d_per_currency    — 6-element vector, one weekly series per Mento stablecoin
  └─ X_d_basket_aggregate — full Mento basket sum (kept regardless of primary choice)
        ↓
Task 11.O (structural-econometrics spec authoring)
        ↓
Task 11.P (3-way Rev-2 spec review)
        ↓
Phase 2b (panel extension + downstream estimation)
```

**Anti-fishing position:** the architecture is one-way (calibration → primary selection → spec → review). Once primary X_d is chosen by the calibration's pre-committed methodology, downstream tasks consume it without re-selection. Mid-stream re-tuning of the primary measure is banned (mirrors Rev-4.1 Task 11.K kill-criterion discipline).

---

## 2. Components and I/O contracts

| Component | Type | Inputs | Outputs |
|---|---|---|---|
| `onchain_carbon_tokenstraded` | DuckDB table (NEW) | `carbon_defi_celo.carboncontroller_evt_tokenstraded` Dune ingestion | columns: `block_time TIMESTAMP, block_date DATE, tx_hash VARCHAR(66), source_token VARCHAR(42), target_token VARCHAR(42), source_amount HUGEINT, target_amount HUGEINT, trader VARCHAR(42), source_amount_usd VARCHAR (text-preserving per Rev-5.1 11.M.5 precedent), target_amount_usd VARCHAR` |
| `onchain_carbon_arbitrages` | DuckDB table (NEW) | `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted` Dune ingestion | columns: `block_time TIMESTAMP, tx_hash VARCHAR(66), profit_usd VARCHAR, route VARCHAR` (route encodes the asset path; treat as opaque for now) |
| `compute_basket_calibration()` | pure free function (`carbon_calibration.py` NEW) | per-currency + aggregate weekly series (DataFrames) | frozen-dataclass `CalibrationResult{primary_choice: Literal["copm_only","basket_aggregate"], copm_n_nonzero_obs: int, copm_power: float, copm_pc1_loading: float, basket_pc1_variance_explained: float, threshold_passed: tuple[bool, bool], rationale: str}` |
| `compute_carbon_xd()` | pure free function (`carbon_xd_filter.py` NEW; NOT extension of `copm_xd_filter.py`) | ingested Carbon events DataFrame + `CalibrationResult` | frozen-dataclass `WeeklyCarbonXdPanel{primary_series: tuple[float,...], primary_proxy_kind: str, arb_only: tuple[float,...], per_currency: dict[str, tuple[float,...]], basket_aggregate: tuple[float,...], weeks: tuple[date,...], is_partial_week: tuple[bool,...]}` |
| `onchain_xd_weekly` | DuckDB table (EXISTING; schema-migrated) | extended with new `proxy_kind` values: `carbon_basket_user_volume_usd`, `carbon_basket_arb_volume_usd`, `carbon_per_currency_<COPM|cUSD|cEUR|cREAL|cKES|XOFm>_volume_usd` | additive rows; existing supply-channel + distribution-channel rows preserved byte-exact |
| `load_onchain_xd_weekly(proxy_kind=…)` | EXISTING; extended to accept new `proxy_kind` literal values | as before | same |

**Module-boundary invariants:**
- Each function is independently testable (single-input → single-output, no shared mutable state).
- All public outputs are frozen dataclasses or `pd.DataFrame` (treated immutably by convention).
- No inheritance; composition only (per `functional-python` skill).

---

## 3. Pre-committed calibration thresholds

Three fixed numbers — pre-committed BEFORE the calibration is run. Each is anchored to existing Rev-4 panel discipline, not to the unobserved Carbon data.

| Threshold | Value | Anchor |
|---|---|---|
| `N_min` (weekly non-zero observations needed for COPM-only primary) | **80** | Existing CPI Rev-4 panel of 947 weekly obs filtered to where the regressors are populated; prior Banrep IBR / DFF weekly extraction yielded 78–84 obs in similar tasks (11.M.6 commit `fff2ca7a3`). |
| `power_min` (statistical power for MDES = 0.20 SD under 13-regressor spec) | **0.80** | Rev-4 standard; computed via `scipy.stats.ncf.ppf` per Task 11.M.6 + corrected MDES per Rev-1.1.1 CR-E2 fix. |
| `pc1_loading_floor` (cross-validation: COPM's loading on PC1) | **\|loading\| ≥ 0.40** | Conventional "non-trivial" loading in PCA reporting; below this, COPM is idiosyncratic relative to the basket. |

Anti-fishing guarantee: these three numbers are committed in the calibration module's source code AND in this design doc BEFORE any Carbon data is ingested. Modification requires a new design-doc revision + 3-way review cycle.

---

## 4. Decision branches

Calibration outputs one of four states; downstream behaviour is fully specified per state.

| Calibration result | Primary X_d | Diagnostic columns | Spec narrative |
|---|---|---|---|
| COPM passes (I) AND COPM passes (II) | `carbon_basket_user_volume_usd` filtered to COPM-only | arb-only + per-currency vector + basket-aggregate | Colombia-pilot framing; basket-aggregate cross-validation |
| COPM fails (I) — too few non-zero weeks | `carbon_basket_user_volume_usd` aggregated over full Mento basket | arb-only + per-currency vector + COPM-only diagnostic | Regional-basket framing; documented limitation: "Colombian on-chain slice too thin in isolation" |
| COPM passes (I) but fails (II) — powered but idiosyncratic | COPM-only WITH flagged caveat | as in COPM-only path | Colombia-pilot framing with explicit "idiosyncratic loading" note in Rev-2 spec §0; basket-aggregate offered as alternative robust read |
| Data structurally pathological (user-only series ≈ empty; Arb Fast Lane is ≈100% of activity) | HALT — escalate to user | n/a | Disposition memo; do NOT silently set arb-only as primary (would conflate stress-detection with capital-flow magnitude) |

---

## 5. Testing strategy (TDD invariants)

Each component lands via the strict-TDD pattern from `feedback_strict_tdd.md`:

1. **Failing-first.** Test written + verified to fail BEFORE implementation. Each of the four NEW components (Carbon ingestion, calibration, X_d compute, schema migration) gets its own failing-first cycle.
2. **Independent reproduction witness.** Every committed weekly-aggregation pipeline has a second-path SQL witness (mirrors Task 11.B `test_golden_fixture_matches_independent_fit` + Task 11.M.5 checksum patterns).
3. **Decision-hash preservation.** Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23` byte-exact through all migrations.
4. **Idempotent migrations.** Every schema change re-runs as a no-op (composite-PK + relaxed-CHECK pattern from Rev-5.2.1 Task 11.N.1 Step 0 commit `a724252c6`).
5. **Real-data over mocks.** All tests hit the real Dune-ingested DuckDB tables; mocks reserved for HTTP failure modes that can't be reproduced (`feedback_real_data_over_mocks.md`).

---

## 6. Out-of-scope (deferred)

Explicitly NOT in this design's scope:

- **Y-target redefinition.** Task 11.O Step 1 is currently anchored on `Y_asset_leg = (Banrep_rate − Fed_funds)/52 + ΔTRM/TRM` (USD-COP carry). The Carbon-basket X_d may motivate a different Y (CELO/crypto-volatility, Mento-peg-spread). This is queued as **amendment-rider A1** in the Rev-5.3 plan-revision and explicitly deferred until 11.N.2b.2 lands and the empirical Carbon X_d distribution is observed. Pre-committing a new Y now would be specification-search.
- **Per-country Y-panel construction.** If calibration → basket-aggregate primary, a follow-on tier-2 work-stream constructs Kenyan / Brazilian / Senegalese / Eurozone Y panels for cross-currency validation. Out of Phase 1.5.5 scope.
- **Direction-signed X_d (option B from brainstorm).** User picked option (A) magnitude. Direction-signed series can be added as another diagnostic in a future revision if the calibration suggests cross-direction asymmetry — but is not a primary candidate now.

---

## 7. Inputs to plan-fold (Technical Writer's brief)

Three new tasks insert into the Rev-5.3 plan revision (the in-flight TW fix-pass at `contracts/.scratch/2026-04-24-plan-rev5.3-draft.md` is updated to incorporate these):

- **Task 11.N.2b.1** (already proposed by Rev-5.3 PM decomposition): schema migration + Dune-credit-budget probe + small-LIMIT sample probe. Now also: pre-commit the calibration thresholds (N_min, power_min, pc1_loading_floor) in source.
- **Task 11.N.2b.2** (already proposed): full ingestion + Mento↔global boundary filter + weekly aggregation across all 6 Mento × 4 global pairs. Output: populated `onchain_carbon_tokenstraded` + `onchain_carbon_arbitrages` tables.
- **Task 11.N.2c (NEW per this design):** basket-share calibration exercise. Runs `compute_basket_calibration()` against the 11.N.2b.2 output; emits `CalibrationResult`; chooses primary X_d per Section 4 decision branches; persists primary + diagnostic columns to `onchain_xd_weekly`. Gate-test: HALT-on-pathological per Section 4 row 4.

After 11.N.2c lands, Task 11.O (Rev-2 spec authoring) consumes the chosen primary X_d. Task 11.P (3-way review) follows. Phase 2b unblocks.

---

## 8. References

- **Memory:** `project_abrigo_inequality_hedge_thesis.md` (updated 2026-04-24 with Carbon-basket reframing); `feedback_onchain_native_priority.md`
- **Bot research:** `contracts/.scratch/2026-04-24-copm-bot-attribution-research.md`
- **Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `1d059e3fa` (Rev-5.2.1)
- **Plan draft:** `contracts/.scratch/2026-04-24-plan-rev5.3-draft.md` (in-flight TW fix-pass, agent `a7f7ec0e502db04c5`)
- **Reviewer reports:** `2026-04-24-plan-rev5.3-review-{code-reviewer,reality-checker,senior-pm}.md`
- **Code precedents:** Task 11.M.5 commit `af98bb659` (DuckDB type discipline); Task 11.M.6 `fff2ca7a3` (panel extension); Task 11.N.1 Step 0 `a724252c6` (composite-PK schema migration); Task 11.N supply-channel X_d `d688bb973`; Task 11.N.1 partial backfill `f1f114cd1`
