# Phase-A.0 Remittance-Surprise → TRM-RV Implementation Plan

> **Status:** Rev 5.3 (consolidated v2) — TW fix-pass + brainstorm-fold + consolidated-review v2 (2026-04-24). Brainstorm-converged X_d design at `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` (immutable; MDES-correction documented as Task 11.N.2c CORRECTIONS block — design doc unchanged) + brainstorm-converged Y₃ design at `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (immutable; committed `23560d31b`). Task 11.N.2 (COPM bot-attribution research, report at `contracts/.scratch/2026-04-24-copm-bot-attribution-research.md` §1-§3) returned a **macro-channel reframing** of the X_d source. The two dominant addresses in the COPM Transfer log (`0x6619871118D144c1c28eC3b23036FC1f0829ed3a` = CarbonController; `0x8c05ea305235a67c7095a32ad4a2ee2688ade636` = BancorArbitrage / Arb Fast Lane) are not retail or remittance noise — they are the official Bancor Carbon DeFi protocol contracts on Celo. Their economic primitive is **closed-loop two-sided market-making across the Mento working-class-stablecoin basket {COPM, USDm, EURm, BRLm, KESm, XOFm} ↔ global-asset basket {CELO, USDT, USDC, WETH}** (canonical 2026 Mento naming; legacy names cUSD/cEUR/cREAL/cKES are pre-rebrand and will be Step-1-verified). Rev 5.3 inserts SIX new tasks: **Task 11.N.1b** resumes missing-blocks backfill via a six-path ladder (path 1 = Celo public RPC re-verified live today); **Task 11.N.2b.1** pre-commits the schema-migration test, basket-address verification (HALT-VERIFY-MANDATORY on USDT + WETH), and Dune-credit-budget probe; **Task 11.N.2b.2** atomically ingests Carbon `TokensTraded` + BancorArbitrage `arbitrageexecuted` events with HALT-on-partial-ingestion enforcement (PM-CF-3); **Task 11.N.2c** runs PCA cross-validation diagnostic only (RC-CF-1/RC-CF-2 collapse: COPM-only proxy-kind dropped per CR-CF-1; basket-aggregate is committed primary out of the gate; calibration emits per-currency PCA loadings + decision branch ∈ {PASS, pathological-HALT}). NEW **Task 11.N.2d** (Y₃ inequality-differential dataset construction; per Y₃ design doc §13 plan-fold instructions) ingests per-country equity + 10Y bond + WC-CPI components (CO/BR/KE/EU), computes per-country differentials with pre-registered 60/25/15 weights, aggregates equal-weight to `Y₃_t`, persists to `onchain_y3_weekly` table. NEW **Task 11.N.2d.1** (PM-FF-1 atomicity-hygiene split) constructs the Aug-2023→2026-04-24 sensitivity panel under `source_methodology = 'y3_v1_sensitivity'`. Task 11.O Step 1 updated: primary Y = `Y₃_t` (not USD-COP carry); diagnostic Y's = per-country differentials + Y₃_bond + supply-channel + distribution-channel for cross-validation. Pre-committed calibration thresholds (per Task 11.N.2c CORRECTIONS block; design doc §3 amended): `N_min=80, power_min=0.80, MDES=0.40 SD, pc1_loading_floor=0.40` (MDES relaxed from design-doc 0.20 SD per RC-CF-1 scipy-verified power computation; smaller-panel exercise n≈84 weekly obs vs Rev-4's 947 obs requires larger detectable effect size). MDES formulation pinned to canonical Cohen f² (Cohen 1988 ch. 9) with `MDES_FORMULATION_HASH: Final[str]` tamper-evident anchor (RC NEW BLOCKER fix). **Task 11.O DAG override (amendment-rider A9, APPLIED):** 11.O now BLOCKS on 11.N.2d (full Y₃ panel + calibrated X_d before Rev-2 spec authoring); supply-channel surrogate becomes secondary diagnostic. Amendment-rider A1 (Y-target shift) RETIRED-as-applied via Task 11.N.2d. 3-way review (CR + RC + Senior PM) converged across two cycles; final reports at `contracts/.scratch/2026-04-24-plan-rev5.3-final-review-{code-reviewer,reality-checker,senior-pm}.md`. Task count: **63** active (Rev-5.2.1's 57 + 11.N.1b + 11.N.2b.1 + 11.N.2b.2 + 11.N.2c + 11.N.2d + 11.N.2d.1).
> **Status:** Rev 5.2.1 (2026-04-24) — 3-way plan review of Rev-5.2 converged. CR ACCEPT-WITH-FIXES (2 BLOCKERs), RC NEEDS WORK (2 BLOCKs), PM ACCEPT-WITH-FIXES. Convergent fixes: (1) Task 11.N.1 now pre-registers schema migration as Step 0 BEFORE any RPC code (relax `onchain_xd_weekly` CHECK constraint to allow multiple `proxy_kind` values + adopt composite PK `(week_start, proxy_kind)`; create new `onchain_copm_transfers` table rather than in-place sample replacement — preserves additive-ness per CR-B1/RC-B1). (2) Dropped `web3.py` — use `requests`-only JSON-RPC since `contracts/.venv/` already has it and lacks web3 (CR/RC MAJOR). (3) Acknowledged `copm_xd_filter.py:71` hardcodes `proxy_kind` constant — Step 4 must update it (RC-new). (4) Explicit DAG: Task 11.O CAN run in parallel on the supply-channel surrogate; 11.N.1's distribution-channel X_d gets applied via an amendment-rider step in 11.O after 11.N.1 lands (PM-P1). (5) Added per-10k-block checkpoint for resumability (PM-P2). (6) `.env.example` + `os.environ.get("ALCHEMY_API_KEY")` HALT-on-missing (CR). Reports at `contracts/.scratch/2026-04-24-plan-rev5.2-review-{code-reviewer,reality-checker,senior-pm}.md`. Task count unchanged at 57.
> **Status:** Rev 5.2 (2026-04-24) — inserts Task 11.N.1 (COPM raw-transfers backfill via Celo RPC + Alchemy fallback) after Task 11.N escalated `X_D_INSUFFICIENT_DATA` at commit `d688bb973`. The committed X_d is a supply-channel surrogate (`net_primary_issuance_usd`); 11.N.1 backfills the 110k-row raw-transfers dataset via free Celo RPC (`forno.celo.org` + Ankr fallback) with Alchemy `getAssetTransfers` as secondary fallback if public RPC fails. Once 11.N.1 lands, Task 11.N regenerates X_d under the original distribution-channel meaning (B2B→B2C net flow) while keeping the supply-channel series as a secondary cross-validation column for Task 11.O. Architecturally on-chain-native (no third-party indexer; no API key required for primary path) per `feedback_onchain_native_priority.md`. Task count: 57 active (56 + 11.N.1).
> **Status:** Rev 5.1 (2026-04-24) — 3-way plan review converged with consolidated fixes. Reports at `contracts/.scratch/2026-04-24-plan-rev5-review-{code-reviewer,reality-checker,senior-pm}.md`; CR ACCEPT-WITH-FIXES, RC NEEDS WORK (2 BLOCKs), PM ACCEPT-WITH-FIXES. Load-bearing RC BLOCKER: Rev-5's Y_asset_leg claim of "computable from Rev-4 panel controls already in hand" was FALSE — Fed funds rate (DFF series) is rejected by the `fred_daily` CHECK constraint at `contracts/scripts/econ_schema.py:73` (only VIXCLS/DCOILWTICO/DCOILBRENTEU allowed), and Banrep IBR level is not a materialized panel column (only event-study surprise exposed at `econ_panels.py:143-148`). Rev-5.1 adds new Task 11.M.6 (FRED + Banrep panel extension) to close the data-access gap before Task 11.O consumes Y_asset_leg. Secondary BLOCKER: Task 11.M COPM Dune agent stalled 2h+ with 2/4 CSVs landed — Rev-5.1 adds explicit liveness gate. Task count: 56 active (55 + new 11.M.6).
> **Status:** Rev 5 (2026-04-24). See Revision history below. **Rev 5 plots the post-Phase-A.0-EXIT inequality-differential pivot into the existing plan (NOT a new plan). Task 11.K's EXIT fired 2026-04-24 at commit `2317f72a5` (verdict EXIT_NON_REMITTANCE per `contracts/.scratch/2026-04-24-phase-a0-exit-disposition.md`); Tasks 11.G/H/I/J from Rev-4.1 are RETIRED. Rev 5 inserts new Tasks 11.L–11.Q implementing the inequality-differential exercise per `project_abrigo_inequality_hedge_thesis.md`: (L) literature-landscape research as a mandatory guardrail input for the structural-econometrics invocation; (M) COPM per-transaction profile (background agent `aa0bf238c4ca1b501` in flight); (N) X_d filter design from COPM B2B→B2C network structure; (O) `superpowers:structural-econometrics` skill invocation to author Rev-2 spec with functional equation + null hypothesis; (P) three-way Rev-2 spec review; (Q) multi-Y panel assembly from existing Rev-4 panel (TRM RV, CPI surprise, Banrep rate, Fed funds already in hand — no new off-chain fetch required for tier-1 run). X_carry_onchain (cUSD-Celo-yield − cCOP-yield) is DROPPED — cCOP yield data not accessible. Consumption-leg Y (DANE EMMV + BanRep HDS) is a tier-2 parallel work-stream out of Phase 1.5.5 scope. Task count: 55 active headers (Rev-4.1's 51 count included 11.G/H/I/J which are now retired but preserved as audit headers; the active-task enumeration is Phase 0 [5] + Phase 1 [5] + Phase 2a [1] + Phase 1.5 [5, 11.A-E] + Phase 1.5.5 active [9: 11.F + 11.K + 11.L + 11.M + 11.M.5 + 11.N + 11.O + 11.P + 11.Q] + Phase 2b [4] + Phase 3 [18] + Phase 4 [8] = 55; retired preserved headers 11.G/H/I/J add 4 inactive markers for audit only). Pending 3-way plan review per `feedback_three_way_review.md`.**
> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Revision history

- **Rev 1 (2026-04-20):** initial plan, 30 tasks across 5 phases, committed alongside the three-way-reviewed design doc at `437fd8bd2`.
- **Rev 2 (2026-04-20):** three-way plan review applied (Code Reviewer + Reality Checker + Senior PM); 6 BLOCKs + 14 FLAGs + 7 NITs addressed; task splits and inserts executed (Tasks 17 → 17a/17b/17c; 21 → 21a/21b/21c with a separate Task 21d review gate; 22 → 22a/22b; 24 → 24a/24b with a separate Task 24c review gate; 30 → 30a/30b/30c; + intra-phase review-gate inserts at 18a, 21d, 24c); Phase-0 Task 1 tightened with the "13-input resolution matrix" deliverable requirement; Task 11 data-access mechanism corrected from "pinned Socrata endpoint" to MPR-derived manual compilation (no public remittance API exists; `mcec-87by` is TRM-only). See fix-log at `contracts/.scratch/2026-04-20-remittance-plan-fix-log.md`. Total task count: **41** (5+5+5+18+8 across Phases 0-4).
- **Rev 3 (2026-04-20):** mid-execution methodology escalation. Task 11 implementation (committed at `939df12e1` DONE_WITH_CONCERNS) confirmed the Rev-2 RC B1 finding was worse than anticipated: **BanRep publishes remittance at QUARTERLY cadence only**, not monthly. The load-bearing grounding is the **BanRep suameca series 4150 metadata** at `https://suameca.banrep.gov.co/estadisticas-economicas/informacionSerie/4150/remesas_trabajadores` (series id `REMESAS_TRIMESTRAL`, `descripcionPeriodicidad=Trimestral`, `fechaUltimoCargue=2026-03-06`; in-tree provenance at `contracts/data/banrep_mpr_sources.md:42-52`), corroborated by the ficha metodológica. Four MPR PDFs were inspected as corroborating-only evidence (their "C. Ingresos secundarios (transferencias corrientes)" row is total-current-transfers, not disaggregated remittance; they do not themselves publish a disaggregated monthly aggregate — a negative corroboration, not a confirmation). 104 real quarterly rows (2000-Q1 → 2025-Q4) were committed; Rev-1 spec §§4.6 (monthly LOCF), §4.7 (AR(1) on monthly), §4.8 (real-time vintage primary) are thereby invalidated for the monthly-cadence primary. Rev 3 inserts a **daily-native middle-plan** (new Tasks 11.A–11.E) that: (a) acquires daily on-chain COPM + cCOP flow data via Dune MCP, (b) aggregates daily → weekly via a rich statistics vector preserving intra-week information, (c) cross-validates against the BanRep quarterly series via a pre-registered bridge ρ-gate at N=7 quarterly obs, (d) patches the Rev-1 spec to Rev-1.1 with the new primary X definition + BanRep quarterly as validation row, (e) three-way reviews the Rev-1.1 patch before Phase 2 resumes at Task 12. Total task count: **46** (5+5+**5**+5+18+8 after Rev 3.1 Phase-1.5 promotion; see Rev 3.1 below). **Rev 3 patch is awaiting three-way plan review; no Rev 3 tasks shall execute until that review converges.**
- **Rev 3.1 (2026-04-20):** three-way plan review of the Rev 3 patch converged (Code Reviewer + Reality Checker + Senior PM, same trio as Rev-2 plan review). Unanimous "needs fixes": 6 BLOCKs, 10 FLAGs, 9 NITs. Rev 3.1 applies consolidated fixes in place. Key changes: (1) **plan-body amendment riders** patch upstream stale references to monthly-cadence primary (Goal line 12; Task 9 `CleanedRemittancePanelV1` scope; Task 10 AR(1)-surprise purpose; Task 13 `a1r_monthly_rebase` renamed to `a1r_quarterly_rebase_bridge`) that Rev 3's spec-only patch had left inconsistent; (2) **Task 11.B silent-test-pass hardening** — pinned expected values require an independent reproduction witness (mirrors Task 10 `test_golden_fixture_matches_independent_fit` pattern); (3) **factual-attribution rewrite** of the Rev 3 history bullet grounding BanRep-quarterly-only on the suameca series 4150 metadata (load-bearing) with MPR PDFs relegated to corroborating-only; (4) **cCOP-TOKEN vs Mento-BROKER address disambiguation** in Task 11.A (`0x777a8255…` is the broker venue, not the token; post-2026-01-25 migration renamed cCOP → COPm at the same contract address); (5) **new Rule 14** formalizing retroactive-authorization semantics for in-flight subagents launched before plan-review convergence; (6) **Rule 13 cycle-cap boundary** defined at Task 11.E Step 3 (one cycle = one full 3-parallel-reviewer round-trip + TW consolidation); (7) **Phase 1.5 "Data-Bridge" promotion** — Tasks 11.A–11.E lift out of Phase 2 into a new Phase 1.5 between Phase 1 and Phase 2, restoring Rev-2 PM F4 Task-11/12 parallelism; Phase 2 reverts to its Rev-2 shape (5 tasks: 11, 12, 13, 14, 15); (8) **recovery protocols** added to Tasks 11.A/11.C/11.E enumerating explicit fallback behavior for three distinct failure modes; (9) **decision gates** formalized at Task 11.D Step 1 (wording-only vs economic-mechanism change) and Task 11.C Step 1 (3-HALT vs 5-HALT split). Task IDs 11.A–E preserved; task count unchanged at **46** (5+5+5+5+18+8). See fix-log at `contracts/.scratch/2026-04-20-remittance-plan-rev3-fix-log.md` for per-finding disposition.
- **Rev 5.3 (2026-04-24):** Task 11.N.2 (COPM bot-attribution research, dispatched after Task 11.N.1 landed at `f1f114cd1` with 47.3% coverage = 52,068 / 110,069 rows over blocks 27,786,128 → 30,485,761) reframed the X_d source. Report at `contracts/.scratch/2026-04-24-copm-bot-attribution-research.md` (5.9 of 15-credit budget consumed by 11.N.2; HIGH-confidence verdict). Brainstorm-converged X_d design at `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` and brainstorm-converged Y₃ design at `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (committed `23560d31b`) — both immutable for this fold. Key changes:
  **(1) Bot-identity verdict (report §2.1-§2.2):** the "two dominant bots" are NOT retail-payments/remittance/MEV-noise — they are CarbonController (`0x6619871118D144c1c28eC3b23036FC1f0829ed3a`; the Carbon DeFi DEX strategy registry, deployed ~July 2024 per Bancor "Hello Celo" launch) and BancorArbitrage / Arb Fast Lane (`0x8c05ea305235a67c7095a32ad4a2ee2688ade636`; the on-chain arbitrage executor). Attribution is HIGH-confidence: Carbon DeFi mainnet-contracts docs at `https://docs.carbondefi.xyz/contracts-and-functions/contracts/deployments/mainnet-contracts` lists the CarbonController address verbatim; Dune decodes 52 + 16 event tables under `carbon_defi_celo.carboncontroller_*` and `carbon_defi_celo.bancorarbitrage_*` keyed to those addresses. The remaining caller EOAs (`0xd9dc2b01…` 751,813 calls; `0xd6bea8b8…` 96,600; etc.) are independent operators of Bancor's open-source `fastlane-bot` framework.
  **(2) Macro-channel reframing (report §3):** the aggregate behaviour is **closed-loop two-sided market-making across the Mento basket {COPM, USDm (legacy: cUSD), EURm (legacy: cEUR), BRLm (legacy: cREAL), KESm (legacy: cKES), XOFm} versus the global-asset basket {CELO, USDT, USDC, WETH}**. This pattern is delta-neutral round-tripping (n_copm_sold ≈ n_copm_bought every day, daily delta typically <2% of volume per report §3 Option-1 evidence). Report §3 channel-fit table ranks (a) CELO–USD volatility = "Strongest", (d) crypto-market-wide vol = "Strong", (b) Mento broker reset rate = "Strong", (c) cross-stable TRM-cKES-cEUR drift = "Weak-to-moderate".
  **(3) X_d redefinition (brainstorm-resolved, design doc §1, §2):** new primary X_d `X_carbon_rebalancing_user_volume_usd_t = Σ |source_amount_usd|` over Carbon `TokensTraded` events in week t with `tx_origin ≠ 0x8c05ea305235a67c7095a32ad4a2ee2688ade636` (BancorArbitrage filtered out; user-initiated trades only) crossing the Mento ↔ global basket boundary. Volume-weighted USD magnitude (option A); arb-as-diagnostic (option iii); option I+II calibration (PCA cross-validation only post v2 fix-pass).
  **(4) Tasks inserted (six total):** **Task 11.N.1b** (resume missing-blocks backfill, narrow) backfills blocks 30,486,128 → chain-tip via a SIX-path ladder ordered by RC empirical evidence: path 1 = Celo public RPC retry (forno + Ankr re-verified live today, HTTP 200; Ankr 1k-block window vs forno 5k-block tolerance) → path 2 = paid Alchemy Celo tier → path 3 = Covalent/GoldRush trial-tier → path 4 = Flipside Crypto SQL REST (verify-existence-first) → path 5 = Dune REST API direct → path 6 = Dune-web manual CSV export (zero-credential fallback). Appends additively to existing `copm_transfers_full.csv` + `onchain_copm_transfers` table preserving the 52,068 rows already landed. **Task 11.N.2b.1** (Carbon-basket pre-commitment + budget probe) authors schema-migration TEST against in-memory DuckDB; basket-address verification with HALT-VERIFY-MANDATORY on the two RC-flagged truncations (USDT, WETH); Dune-credit-budget probe. **Task 11.N.2b.2** (Carbon basket-rebalancing dataset, broad — NEW X_d source) ingests `carbon_defi_celo.carboncontroller_evt_tokenstraded` + `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted` filtered to swaps where `sourceToken ∈ Mento-basket AND targetToken ∈ global-basket` (or reverse); commits the schema migration to `onchain_xd_weekly` CHECK ONLY AFTER ingestion + smoke-probe succeed (atomicity-preserving inversion); HALT-on-partial-ingestion enforcement (≥0.95 × Dune-reported count per PM-CF-3). **Task 11.N.2c** (basket-share calibration; PCA cross-validation diagnostic only post §0.2 RC-CF-1/RC-CF-2 collapse) emits PASS or pathological-HALT; pre-committed thresholds N_MIN=80, POWER_MIN=0.80, MDES_SD=0.40 SD, PC1_LOADING_FLOOR=0.40, MDES_FORMULATION_HASH (Cohen f² per Cohen 1988 ch. 9 — RC NEW BLOCKER fix). **Task 11.N.2d** (Y₃ inequality-differential dataset; per Y₃ design doc §13 plan-fold instructions) constructs `Y₃_t = (1/4) × (Δ_CO + Δ_BR + Δ_KE + Δ_EU)` regional pan-EM differential per design doc §1, §5; primary panel Sep-2024 → 2026-04-24 (~84 weeks); pre-registered budget-share weights 60% food / 25% energy+housing / 15% transport-fuel per design doc §4. **Task 11.N.2d.1** (PM-FF-1 atomicity-hygiene split) constructs the Aug-2023 → 2026-04-24 sensitivity panel under `source_methodology = 'y3_v1_sensitivity'`; runs in parallel with Task 11.O (consumed lazily by 11.O sensitivity-cross-validation step).
  **(5) Data-scope broadening:** the X_d data scope expands from COPM Transfer events alone (~110k rows; one token) to Carbon `TokensTraded` events across the full Mento + global 10-token basket. RC empirical probe (2026-04-24): basket-wide Carbon event count 2024-09-01 → 2026-04-24 is 613,603 at 0.028 credits for count-only aggregate; full-pull cost expected ≤ 10 credits given current Dune community-plan budget remainder ≈ 24,994 credits. The longer time-series is now load-bearing because the macro-event-study window must cover the full Sep-2024-launch → today window of crypto-volatility events.
  **(6) Y-target shift APPLIED via Task 11.N.2d (RETIRED-as-applied):** the Y₃ design doc landed (committed `23560d31b`); per its §13 plan-fold instructions the Y-target shift is APPLIED in Rev-5.3, not deferred. Task 11.O Step 1 updated: primary Y = `Y₃_t` (not USD-COP carry); diagnostic Y's = per-country differentials + Y₃_bond + supply-channel (Rev-5.1) + distribution-channel (11.N.1b) for cross-validation. Original Rev-5 Y_asset_leg formula `(Banrep_rate − Fed_funds)/52 + ΔTRM/TRM` is SUPERSEDED by §4 Task 11.N.2d body and §5 amendment-rider A1 status flip to RETIRED-as-applied.
  **(7) 11.O DAG override (amendment-rider A9, APPLIED) — supply-channel-parallelism RETIRED:** the Rev-5.2.1 supply-channel-parallelism clause is RETIRED. Task 11.O now BLOCKS on Task 11.N.2d (full Y₃ panel + calibrated X_d primary committed before Rev-2 spec authoring). Supply-channel surrogate `net_primary_issuance_usd` becomes a SECONDARY diagnostic in 11.O's resolution matrix. Authoring 11.O Rev-2 on supply-channel-only and patching via Rev-3 amendment-rider would violate the X_d design doc §1 anti-fishing position. Documented in §6 "Task 11.O DAG amendment". 11.N.2d.1 sensitivity panel runs in parallel with 11.O.
  **(8) Memory grounding:** `project_abrigo_inequality_hedge_thesis.md` was already updated 2026-04-24 with the Carbon-basket reframing — no plan change needed there; the memory is the load-bearing thesis citation, the plan is the operational instantiation.
  **(9) Three-way review converged across two cycles:** Original Rev-5.3 → 4 BLOCKERs + 4 MAJORs + 6 MINORs (CR/RC/PM); Consolidated v1 → CR-CF-1/2/3 + RC-CF-1/2 BLOCKERs + PM-CF-1/2/3; Consolidated v2 → CR-FF-1..7 + RC-FF NEW BLOCKER (MDES formulation pinning) + RC-FF MAJORs + PM-FF-1/2/3. All convergent fixes applied. Final reports at `contracts/.scratch/2026-04-24-plan-rev5.3-final-review-{code-reviewer,reality-checker,senior-pm}.md`. Per §5 amendment-rider queue: A1 RETIRED-as-applied (Task 11.N.2d landing); A9 APPLIED (DAG override); A2-A8 deferred to future Rev-5.4.
  Task count: **63** active (Rev-5.2.1's 57 + 11.N.1b + 11.N.2b.1 + 11.N.2b.2 + 11.N.2c + 11.N.2d + 11.N.2d.1).
- **Rev 5.2.1 (2026-04-24):** three-way plan review of Rev-5.2 (commit `b745e4e22`) converged same-day. CR (ACCEPT-WITH-FIXES, 2 BLOCKERs + 4 MAJORs + 2 MINORs + 2 PASS-verified, report `contracts/.scratch/2026-04-24-plan-rev5.2-review-code-reviewer.md`), RC (**NEEDS WORK, 2 BLOCKs + 3 FLAGs + 2 NITs**, report `contracts/.scratch/2026-04-24-plan-rev5.2-review-reality-checker.md`; RC confirmed RPC endpoints LIVE, COPM bytecode present, Transfer topic correct, 110,069 target grounded, Rev-4 hash preserved), PM (ACCEPT-WITH-FIXES, 3-risk register, report `contracts/.scratch/2026-04-24-plan-rev5.2-review-senior-pm.md`). Rev 5.2.1 applies consolidated BLOCKER + convergent MAJOR fixes to Task 11.N.1: **(1) BLOCKER CR-B1/RC-B1 (schema)** — `onchain_xd_weekly` CHECK at `econ_schema.py:367-374` pins `proxy_kind='net_primary_issuance_usd'` as a singleton; Task 11.N.1 now has a new **Step 0 (schema migration pre-registration + failing test)** BEFORE any RPC code, relaxing the CHECK to `IN ('net_primary_issuance_usd', 'b2b_to_b2c_net_flow_usd')` and adopting a composite PK `(week_start, proxy_kind)` to allow both channels to coexist row-wise. **(2) BLOCKER CR-B2 (table design)** — `onchain_copm_transfers` pre-committed as a NEW table (not in-place replacement of `onchain_copm_transfers_sample`), preserving additive-ness since LOCKED_DECISIONS hash does not cover DDL. **(3) MAJOR CR/RC dependency** — dropped `web3.py` references; Task 11.N.1 uses `requests`-only JSON-RPC since `contracts/.venv/` has `requests` + `eth-hash`/`eth-typing`/`eth-utils` but no `web3`. **(4) RC-new constant** — `copm_xd_filter.py:71` hardcodes the `proxy_kind` constant; Task 11.N.1 Step 4 now explicitly updates it. **(5) PM-P1 DAG** — Task 11.O is NOT blocked on 11.N.1; 11.O can run in parallel on the supply-channel surrogate, and when 11.N.1 lands the distribution-channel X_d is folded in via an amendment-rider step in 11.O Step 4. **(6) PM-P2 resumability** — per-10k-block checkpoint file at `contracts/.scratch/copm_transfers_backfill_progress.json` so a mid-pull interruption resumes from the last completed block range rather than from zero. **(7) CR hygiene** — `ALCHEMY_API_KEY` loaded via `os.environ.get(...)` with HALT-on-missing when Alchemy fallback is actually needed; `.env.example` file created with `ALCHEMY_API_KEY=` placeholder. Deferred to future pass: 11.N.1 decomposition into 11.N.1a-d sub-tasks (PM NIT — the expanded Step structure in this revision achieves the atomic-rollback property without splitting the task ID). See fix-log at `contracts/.scratch/2026-04-24-plan-rev5.2.1-fix-log.md`. Task count: **57** unchanged.
- **Rev 5.2 (2026-04-24):** Task 11.N shipped at commit `d688bb973` with a data-availability escalation `X_D_INSUFFICIENT_DATA`: the Dune MCP pagination limit prevented pulling the 110,069-row raw `copm_transfers` table (only a 10-row sample reached DuckDB), so X_d was committed as a surrogate `net_primary_issuance_usd` (supply channel: Σ mints − Σ burns per Friday-week) tagged `proxy_kind` for downstream visibility. The originally-pitched distribution-channel X_d (B2B→B2C net flow) remains the preferred construct per `project_abrigo_inequality_hedge_thesis.md`. Rev 5.2 inserts **Task 11.N.1 (COPM raw-transfers backfill, Celo RPC primary + Alchemy fallback)** between Task 11.N and Phase 2b to enable the distribution-channel X_d. Data-path rationale: the primary path uses free Celo public RPC (`https://forno.celo.org` + `https://rpc.ankr.com/celo` fallback) with `eth_getLogs` over 10,000-block windows — no third-party indexer, no API key, architecturally aligned with on-chain-native priority (`feedback_onchain_native_priority.md`); the secondary fallback uses Alchemy `getAssetTransfers` (free-tier 300M compute units/month, batches 1000 transfers per call) triggered only if the public RPC fails the row-count check vs the Dune-reported 110,069 (±1% tolerance) or rate-limits excessively. Once 11.N.1 lands, Task 11.N re-computes X_d under the distribution-channel definition, updates `onchain_xd_weekly` with `proxy_kind = "b2b_to_b2c_net_flow_usd"`, and preserves the supply-channel series as a secondary column for Task 11.O cross-validation. Task count: **57** active (Rev-5.1's 56 + 11.N.1). Pending three-way plan review of this Rev 5.2 patch per `feedback_three_way_review.md`.
- **Rev 5.1 (2026-04-24):** three-way plan review of the Rev 5 draft converged same-day. CR (ACCEPT-WITH-FIXES, 1 BLOCKER + 3 MAJORs, report `contracts/.scratch/2026-04-24-plan-rev5-review-code-reviewer.md`), RC (**NEEDS WORK, 2 BLOCKs + 4 FLAGs + 2 NITs**, report `contracts/.scratch/2026-04-24-plan-rev5-review-reality-checker.md`), PM (ACCEPT-WITH-FIXES, 7 amendment-rider targets across Phase 2b/3/4, report `contracts/.scratch/2026-04-24-plan-rev5-review-senior-pm.md`). Rev 5.1 applies consolidated BLOCKER + convergent MAJOR fixes in place; NITs and non-convergent MAJORs deferred to subsequent revision. Key changes: (1) **Y_asset_leg data-path BLOCKER (RC)** — Rev-5's claim that Fed funds + Banrep IBR level are "already in hand" was false. Fed funds (FRED `DFF`) is schema-rejected by the `fred_daily` CHECK constraint at `contracts/scripts/econ_schema.py:73` (only VIXCLS/DCOILWTICO/DCOILBRENTEU allowed); Banrep IBR level is not a materialized panel column (`econ_panels.py:143-148` exposes only the surprise). **New Task 11.M.6 (FRED + Banrep rate panel extension)** inserted between 11.M.5 and 11.N; Task 11.O inputs updated to consume the extension. (2) **Task 11.M liveness-gate BLOCKER (RC)** — COPM background agent stalled 2h with 2/4 CSVs landed; Task 11.M now includes explicit >2h-silence → orchestrator re-dispatches fresh agent with resume instructions; downstream 11.M.5/N blocked on all-4-CSVs presence + row-count check; 3-restart escalation to user. (3) **Task-count BLOCKER (CR)** — status banner said 53, Rev-5 bullet said 54, CR enumeration found 55; reconciled to active-count 56 under Rev 5.1 (55 + 11.M.6). (4) **Deep-link hazard MAJOR (CR)** — retired Tasks 11.H/I/J now carry inline `⟨RETIRED Rev-5⟩` markers in their headers (in addition to the block banner at 11.G). (5) **DuckDB `uint256` correction (CR)** — `uint256` is not a DuckDB native type; Task 11.M.5 Step 2 now specifies `HUGEINT` / `DECIMAL(38,0)` with overflow-guard assertion in ingestion. Deferred to Rev 5.2 (future pass): Phase 2b/3/4 amendment riders for remittance→inequality scope migration (PM finding), spec-coverage self-check rewrite at line ~991 (PM finding), explicit DAG block in Phase 1.5.5 header (PM finding), 11.M.5 additive-only test strengthening with schema-diff catch (CR finding), non-stop-policy explicit retirement clause (PM NIT), Task 11.O Step 4 cycle-cap framing (PM NIT), tier-2 consumption-leg governance memo (PM NIT), Task 11.C ρ-gate orphan-rationale touch-up (CR MAJOR). See fix-log at `contracts/.scratch/2026-04-24-plan-rev5.1-fix-log.md`.
- **Rev 5 (2026-04-24):** inequality-differential pivot post-Phase-A.0-EXIT. Plotted into the existing plan (NOT a new plan) per user directive. Phase-A.0 remittance exercise CLOSED at commit `2317f72a5` (verdict EXIT_NON_REMITTANCE per `contracts/.scratch/2026-04-24-phase-a0-exit-disposition.md`); Tasks 11.G/H/I/J from Rev-4.1 RETIRED. Product thesis refined in memory `project_abrigo_inequality_hedge_thesis.md`: Abrigo hedges the DIFFERENTIAL between rich-household asset returns (USD-COP carry = (Banrep_rate − Fed_funds)/52 + ΔTRM/TRM) and working-class consumption returns (real consumption growth, tier-2 fetch). Rev 5 inserts Tasks 11.L–11.Q + new 11.M.5: (L) literature-landscape research via arxiv MCP as mandatory guardrail input for structural-econometrics invocation (user: "look if there is existing research pointing this direction before running"); (M) COPM per-transaction profile via Dune MCP (background agent `aa0bf238c4ca1b501` in flight — partial 2/4 CSVs landed at edit time); (**M.5 NEW**) DuckDB migration — ingest on-chain CSVs (Task 11.A daily flow + Task 11.M per-tx data) into `contracts/data/structural_econ.duckdb` via `econ_schema.py`/`econ_pipeline.py`/`econ_query_api.py` to match the Rev-4 pipeline pattern; this is non-negotiable — downstream Tasks 11.N and 11.Q MUST read from DuckDB, not raw CSVs; (N) X_d filter design from COPM B2B→B2C network structure, reading from DuckDB via `load_onchain_copm_transfers()`; (O) `superpowers:structural-econometrics` skill invocation to author Rev-2 spec with functional equation + null hypothesis + scipy-correct MDES (fixes Rev-1.1.1 CR-E2 arithmetic error); (P) three-way Rev-2 spec review (CR + RC + TW); (Q) multi-Y panel assembly via `econ_panels.py` extension — additive columns Y_asset_leg + X_d_weekly in DuckDB, decision-hash-preserving. **X_carry_onchain DROPPED** (cCOP yield data not accessible per user). **Y consumption-leg DEFERRED** to tier-2 parallel work-stream out of Phase 1.5.5 scope (DANE EMMV retail-sales + BanRep household-debt-service-ratio fetch); the tier-1 gate test runs against Y_asset_leg only using existing Rev-4 panel controls. Task count: **54** (51 − 4 retired + 7 new — L/M/M.5/N/O/P/Q).
- **Rev 4.1 (2026-04-24):** intellectual-honesty amendment to Rev 4, applied same-day before any Task 11.F/G/H/I/J work completed. User flagged two gaps in Rev 4: (i) Task 11.F's original scope (peak-day events only) was necessary-but-not-sufficient — it omitted two research axes of equal importance: **user-intent classification** (what are cCOP/COPM transactions actually FOR? — the prior research at `CELO_ECOSYSTEM_USERS.md` documents payments/UBI/DAO-community use cases that are NOT remittance) and **data-source correctness verification** (is Dune query #7366593 the right source, or are we missing flow paths through MiniPay, Carbon DeFi, Uniswap-V3 cCOP/cUSD pools, or CeFi exchange on/off-ramps?); (ii) the Rev-4 non-stop policy created an intellectual trap — "iterate until M_threshold met" could force a spurious filter if no remittance signal truly exists in the data. Rev 4.1 fixes both: (a) Task 11.F scope expanded to five research axes (peak events + intent + data-source verification + transaction-size distribution + pivot-candidate identification); (b) **new Task 11.K (EXIT plan / kill criterion)** inserted between Task 11.F and Task 11.G, formally defining the conditions under which we halt Phase 1.5.5 and accept "no remittance signal exists in this data" as a valid scientific outcome rather than forcing a filter. Kill criteria: (k1) >70% non-remittance intent volume per 11.F, (k2) data-source systematic error per 11.F, (k3) Task 11.H argmax M_max < 0.40 across pre-committed F (evaluated inside 11.H), (k4) median transaction size < $30 USD consistent with payments not remittance (vs World Bank KNOMAD Colombia median remittance ~$350/tx). **EXIT disposition** (if any kill fires): author disposition memo + re-scope to pivot candidate per `project_colombia_yx_matrix.md`. **Explicit pivot candidate documented in plan:** if intent research shows dominant usage is retail payments / consumption, re-scope exercise from "remittance surprise → TRM-RV" to "on-chain payment/consumption surprise → TRM-RV" reusing the same infrastructure (cleaning.py, Phase 2b panel extension, notebooks) with BanRep retail-sales or consumption-confidence index as validation anchor. Task count: **51** (5+5+5+5+**6**+18+8 — one task added, 11.K). Non-stop policy updated: "iterate until argmax M ≥ M_threshold OR kill criterion fires."
- **Rev 4 (2026-04-24):** structural escalation after Task 11.E Rev-1.1.1 three-way review returned CR REJECT + RC NEEDS WORK + TW NEEDS FIXES, compounded by a user-surfaced cCOP representativeness concern. **Trigger signals:** (a) **CR REJECT** — patches 4 (§4.1 scalar → 6-D vector primary X) and 5 (§4.4 scalar t-test → joint F-test) mis-classified as wording-only per Task 11.D decision gate; scipy-verified MDES arithmetic error (spec λ≈13 overstates by ~8%; correct λ=11.97 at df₂=72 → MDES_R²=0.134 not 0.143 at N_eff=78); reports at `contracts/.scratch/2026-04-24-tier1e-rev111-review-code-reviewer.md` and `2026-04-24-tier1e-rev111-review-reality-checker.md`. (b) **TW NEEDS FIXES** — doc title still says "Rev-1"; §12 superseded rows lack visual marker; seven sections retain orphaned Rev-1 scalar/monthly language. (c) **cCOP representativeness concern corroborated by prior research:** `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CELO_ECOSYSTEM_USERS.md:157` ("cCOP user base is small and concentrated in Medellín-area early adopters"), `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/identification/2026-04-02-ccop-qa-audit.md:73` (power users 1,300–1,600 txns each, likely bots/payment processors), `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md:74` (selection bias: "on-chain sample is not representative of ALL Colombian income converters"). **Empirical corroboration in current panel:** top 5 single-day flow events show inflow ≈ outflow to <1% — textbook roundtripping (e.g., 2025-09-18 balanced to the seventh decimal: in=$429,592.26, out=$429,592.27). **Rev 4 inserts Tasks 11.F–11.J** (new Phase 1.5.5): (F) peak-day event research (background web-search agent to identify confounding events on top-flow days — migration announcements, arbitrage opportunities, airdrop days — usable as dummy variables or instruments); (G) power-user filter brainstorm via `superpowers:brainstorming` skill, consuming prior-research artifacts + 11.F output; (H) **non-stop filter-design iteration** under pre-committed composite symmetric similarity objective against BanRep quarterly series; (I) `structural-econometrics` skill re-invocation to author Rev-2 spec using the argmax filter from Task 11.H; (J) Rev-2 spec three-way review + TW consolidation + Rule 13 cycle-cap. **Non-stop policy:** iteration continues until argmax M ≥ M_threshold or all pre-committed filter families exhausted; Rule 13's 3-cycle cap does NOT apply to filter iteration (it applies only at Task 11.J). **Anti-fishing guard:** the symmetric similarity objective M, filter search space F, and component weights are pre-committed in Task 11.H Step 1 BEFORE any filter is evaluated; mid-search modification is banned (deferred to a hypothetical Task 11.H.2 with full re-commitment). **Rev-1.1.1 at `ac5189363` is hereby SUPERSEDED** — do not reference its §§4.1/4.4/4.5 after this bullet; Rev-2 spec authored at Task 11.I becomes the next canonical spec. Task count: **50** (5+5+5+5+**5**+18+8 after Phase 1.5.5 insertion; 5 tasks 11.F/G/H/I/J).

**Goal (Rev 5 amended — inequality-differential pivot):** Implement the Abrigo structural-econometric program under the **inequality-differential hedge thesis** (per `project_abrigo_inequality_hedge_thesis.md`): the product hedges the DIFFERENTIAL between rich-household asset returns (USD-COP carry = `(Banrep_rate − Fed_funds)/52 + ΔTRM/TRM`, computable from Rev-4 panel controls already in hand) and working-class consumption returns (real consumption growth net of inflation; data-acquisition tier-2 work-stream out of current phase scope). The exercise calibrates the on-chain-derivable asset-leg mapping: does a filtered X_d (COPM B2B→B2C network-derived signal) predict Y_asset_leg, with Y₁ TRM RV and Y₂ CPI surprise as diagnostic secondaries? All data flows through `contracts/data/structural_econ.duckdb` per Rev-4 pipeline pattern (per Task 11.M.5 DuckDB migration). Phase-A.0 remittance exercise EXITED 2026-04-24 (`project_phase_a0_exit_verdict.md`); Rev-1/1.1/1.1.1 specs SUPERSEDED. Rev 5 inherits Rev-4 infrastructure (cleaning.py, nb2_serialize.py, gate_aggregate.py, render_readme.py, econ_schema/pipeline/query_api/panels) additively, extending the 947-obs weekly panel with X_d and Y_asset_leg columns (decision-hash preserved, not replaced), under pre-committed anti-fishing framing and mandatory literature-research guardrail (Task 11.L) BEFORE structural-econometrics skill invocation (Task 11.O).

**Architecture:** Three notebooks (NB1 EDA + panel-fingerprint-extension, NB2 OLS ladder + GARCH(1,1)-X + T3b gate + reconciliation, NB3 T1-T7 tests + forest plot + sensitivity sweep + gate aggregation + README auto-render) co-located under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/`. The exercise reuses the Rev-4 `scripts/` pipeline additively — `cleaning.py`, `nb2_serialize.py`, `gate_aggregate.py`, `render_readme.py`, `env.py` — with remittance-specific extensions. Phase 0 invokes the `structural-econometrics` skill to derive the Rev-1 spec resolving the 13 methodology mandatory-inputs enumerated in the design doc. No code in this plan — every task dispatches a specialized subagent with a prose specification.

**Tech Stack:** Python 3.12+, DuckDB 1.5+, statsmodels, arch, scipy, pandas, numpy, matplotlib, specification_curve, Jinja2, jupyter + nbconvert, bibtexparser, ruptures, just (existing worktree justfile).

**Design doc:** `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md` (committed at `437fd8bd2`, three-way-reviewed CR+RC+MQ, TW-consolidated).

**Reference plan:** `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md` (Rev-4 CPI 33-task plan that shipped successfully 2026-04-19 with FAIL verdict).

---

## Non-Negotiable Rules (enforced on every task)

1. **Strict TDD.** Every task writes a failing test first, verifies the failure, implements minimally via a dispatched subagent, verifies the pass, then commits. Never write implementation before an observably failing test.
2. **Specialized subagent per task.** Foreground orchestrates and verifies; never authors. Each task below names exactly one subagent.
3. **X-trio checkpoint for notebook authoring.** Every task that dispatches a subagent to write notebook cells follows the Notebook Authoring Protocol below. Bulk authoring forbidden.
4. **Scripts-only extended allow-list.** Pipeline work touches `contracts/notebooks/fx_vol_remittance_surprise/`, `contracts/scripts/`, `contracts/scripts/tests/remittance/`, `contracts/data/`, `contracts/.gitignore`, and `contracts/docs/superpowers/specs/` + `contracts/docs/superpowers/plans/` (design-doc + plan directory extensions per Rev-4 precedent). Never `src/`, `test/*.sol`, `foundry.toml`, or any Solidity. **Exception (Rev-2):** completion-record writes to `~/.claude/projects/*/memory/` are permitted out-of-worktree per Rev-4 precedent (see `project_fx_vol_cpi_notebook_complete.md` — the CPI project wrote its completion memory to this path on 2026-04-19). This exception is scoped to Task 30a only.
5. **Additive-only to the frozen panel.** Decision-hash from Rev-4 panel is **extended**, not replaced. Any mutation of existing columns aborts the panel load.
6. **Citation block before every decision/test/fit.** Four parts: reference, why used, relevance to results, connection to Phase-B simulator. Enforced by the Rev-4 pre-commit citation lint (reused as-is).
7. **Chasing-offline rule.** Spec searching, model comparison, rejected alternatives live in the Analytics Reporter's private scratch — never in committed notebooks. Rev-4 forbidden-phrase lint reused.
8. **Anti-fishing discipline.** Every task asserts this is Phase-A.0 — a distinct pre-commitment on the remittance external-inflow channel — not a rescue of the CPI-FAIL. Commit messages and notebook headers reference the design doc's "Why this is not a rescue of CPI-FAIL" section.
9. **Push origin, not upstream.** `origin` = JMSBPP.
10. **Real data over mocks.** Tests hit real DuckDB and real BanRep-derived fixtures; mocks only for HTTP errors that cannot be reproduced.
11. **Test-file naming convention.** All Phase-A.0 tests live under `contracts/scripts/tests/remittance/` to avoid collision with CPI tests. Naming: `test_nb{N}_remittance_section{FIRST}[_{LAST}].py`. **Exception:** environment / scaffold / fixture / integration-guard tests are exempt (e.g., `test_env_remittance.py`, `test_scaffold.py`, `test_banrep_remittance_fetcher.py`, `test_end_to_end_determinism.py`).
12. **Artifact path constants.** All inter-task artifact paths reference constants from `env_remittance.py` (a remittance-specific sibling to the Rev-4 `env.py`).
13. **Reviewer-loop cycle cap.** Any task that says "iterate to PASS" (Task 27, Task 29 sequences) is capped at 3 reviewer cycles. After the third failed cycle, halt and escalate to the user for scope renegotiation rather than recursing silently. (Addresses PM F3; mirrors the Rev-4 spec-derivation 12-cycle cost as a visibility guardrail.)
14. **Retroactive-authorization of in-flight subagents (Rev 3.1 insert — PM-B1).** Any subagent dispatch started before a plan-review convergence point is **frozen-pending-authorization**. Its outputs shall not be committed until the gating review returns unanimous PASS (or PASS-WITH-FIXES) and the TW-consolidation fix-pass lands. Concretely: the Task 11.A implementer dispatched at 2026-04-20 prior to Rev-3 plan-review convergence is specifically named as frozen-pending-authorization. Its artifacts (if returned) are speculative — unused by downstream tasks — until Task 11.E PASSes. Disposition by scenario: (a) if the in-flight subagent completes successfully and its artifacts satisfy Task 11.A Step-1 test assertions, the artifacts become eligible-to-commit under the Task-11.A commit message only *after* Task 11.E PASSes; (b) if the in-flight subagent fails (Dune free-tier hit or schema mismatch), the failure mode + proposed remediation become explicit Task-11.E inputs and no artifact is committed from that dispatch; (c) if the in-flight subagent returns DONE_WITH_CONCERNS, Task 11.E inputs the concern log and either authorizes commit or halts for scope renegotiation. This rule generalizes beyond Task 11.A: any future mid-execution plan-review convergence point inherits the same frozen-pending-authorization semantics for any subagent launched before that point.

---

## Notebook Authoring Protocol (X-trio checkpoint)

Per memory rule `feedback_notebook_trio_checkpoint.md`. Every task that dispatches Analytics Reporter to author notebook cells proceeds trio by trio:

**Trio = (why-markdown cell) + (code cell) + (interpretation-markdown cell)**

1. Subagent writes one markdown cell with the four-part citation block. The "Why used" part explains why the next code cell runs.
2. Subagent writes the code cell.
3. Subagent executes the code cell and verifies it runs without error.
4. Subagent writes one markdown cell interpreting the specific results the code cell just produced.
5. Subagent HALTS and requests human review before authoring the next trio.

Bulk authoring of multiple trios in a single dispatch is forbidden. Infrastructure tasks (scaffold, lint scripts, env, CI tests) are exempt.

---

## Amendment-Rider Queue (Rev-5.3 Deferred)

**Purpose (PM-P3 fix):** This section is a stable top-level anchor for deferred amendment work. The Rev-5.3 revision-history bullet points HERE for the queue contents, instead of inlining the queue items in a dense bullet that loses visibility across revisions.

The following sections of the plan become STALE under the Carbon-basket reframing once Task 11.N.2b.2 lands and the empirical Carbon X_d distribution is observed. Rev 5.3 does NOT amend these sections in-place — they are queued for a future Rev-5.x amendment rider authored after 11.N.2b.2's Step 6 verification commits and the Carbon X_d weekly distribution is in DuckDB. Deferral rationale: the Y-target shift (originally A1) was data-driven; A1 is now RETIRED-as-applied via Task 11.N.2d landing per §0.2 PM-CF-1 + §0.3 CR-FF-7 / PM-FF-3.

**Queue table (CR-MINOR-4: task-id cites, not line-number cites):**

| Rider ID | Target section / task | Trigger event | Status |
|---|---|---|---|
| A1 | Task 11.O Step 1 (the primary-Y-formula step) — formerly `Y_asset_leg_t = (Banrep_rate − Fed_funds)/52 + ΔTRM/TRM`; now `Y₃_t` per Task 11.N.2d | Y₃ design doc landed (committed `23560d31b`); Task 11.N.2d constructs the panel | **RETIRED-as-applied (Task 11.N.2d landing; §0.2 PM-CF-1 + §0.3 CR-FF-7 / PM-FF-3)** |
| A2 | Task 11.O Step 2 (13-input resolution matrix inputs) — five rows depend on Y choice (expected sign / MDES anchor / identification source / alternate-LHS sensitivity / GARCH parametrization) | A1 resolved | DEFERRED |
| A3 | Task 11.O Step 3 (MDES computation) | A1 resolved | DEFERRED |
| A4 | Task 11.Q (panel-assembly columns step); also `econ_panels.py` view + `CleanedInequalityPanelV1` frozen-dataclass + `_compute_decision_hash_inequality` extension | A1 resolved | DEFERRED |
| A5 | Goal section (the §0/§1 high-level goal block; rewrites the inequality-differential operationalization). Future amendment-rider preserves the trailing sentences of the current Goal block (Phase-A.0 EXIT cite + Rev-4 infrastructure inheritance clause) — only the operationalization is rewritten (CR-P10) | A1 resolved | DEFERRED |
| A6 | Memory file `project_abrigo_inequality_hedge_thesis.md` | Already updated 2026-04-24 by user | NO PLAN CHANGE NEEDED (recorded for completeness) |
| A7 | Test-file naming convention (the test-file-naming Non-Negotiable Rule, currently `test_nb{N}_remittance_section{FIRST}[_{LAST}].py`); extend with `inequality/` sub-tree convention for Carbon-basket tests per Task 11.Q precedent | After 11.N.2b.2 lands and `inequality/` sub-tree usage is established | DEFERRED |
| A8 | Spec-coverage self-check section (per PM-N6: doc-debt now spans Rev-5 → Rev-5.3 = 4 revisions stale) | Rev-5.4 author session | DEFERRED |
| A9 | Task 11.O DAG override — supply-channel-parallelism RETIRED; 11.O now BLOCKS on Task 11.N.2d (Y₃ panel + calibrated X_d both required); 11.N.2d.1 sensitivity panel runs in parallel with 11.O (consumed lazily by 11.O's sensitivity-cross-validation step) | Brainstorm-fold landing + §0.2 PM-CF-1 (Y₃ design doc landing) + §0.3 PM-FF-1 (sensitivity-panel split) | **APPLIED in Rev-5.3 brainstorm-fold + Rev-5.3 §0.2 + Rev-5.3 §0.3** (not deferred); see "Task 11.O DAG amendment" below for operational details |

**A1 candidate Y replacements (NOT pre-committed; for future revision; preserved for historical record now that A1 is RETIRED-as-applied via Task 11.N.2d):**
- `Y_crypto_vol_t = realized weekly volatility of CELO returns` (measures the global-asset side of the basket boundary)
- `Y_mento_peg_spread_t = weekly std of Mento-basket peg deviations across {USDm (legacy: cUSD), EURm (legacy: cEUR), BRLm (legacy: cREAL), KESm (legacy: cKES), XOFm, COPM}` (measures the Mento side of the basket boundary; aligns directly with the inequality-differential thesis since the working-class-stablecoin side IS the Mento basket)
- Composite `Y_basket_dislocation_t = f(Y_crypto_vol, Y_mento_peg_spread)` — conceptually the right Y but adds estimation complexity

**Recommended sequencing of the future amendment-rider revision (Rev-5.4 candidate):**
1. Wait for 11.N.1b + 11.N.2b.2 to commit (both gates green); also wait for the Y₃ panel from 11.N.2d to commit so candidate-Y rankings can be done against the calibrated X_d.
2. Empirically rank candidate Y's against the Carbon X_d in a brief exploratory worknotes scratch, pre-committing the ranking criterion BEFORE running the rankings.
3. Author Rev-5.4 status line + revision-history bullet + Goal section rewrite (A5) + Task 11.O Step 1/2/3 amendment riders (A2/A3) + Task 11.Q amendment rider (A4) + Rule extension for `inequality/` sub-tree (A7) + spec-coverage self-check refresh (A8).
4. 3-way review of Rev-5.4 per `feedback_three_way_review.md`.
5. Commit Rev-5.4; Task 11.O dispatches with the new Y. If 11.O's Rev-2 spec was already authored on supply-channel-only by that time, that spec gets a Rev-3 amendment under Task 11.J (Rule 13) discipline rather than being thrown out wholesale.

---

## Task 11.O DAG amendment (Rev-5.3 brainstorm-fold insert — supply-channel-parallelism RETIRED)

**Trigger:** brainstorm-fold delta (Rev-5.3 §0.1) + design doc §1 anti-fishing position + design doc §7 sequencing. Amendment-rider A9 in queue table above: **APPLIED in Rev-5.3 brainstorm-fold** (not deferred).

**What changes:**
- The Rev-5.1 / Rev-5.2.1 / Rev-5.3 §0 fix-pass clause permitting "Task 11.O CAN run in parallel on supply-channel surrogate" is **RETIRED**. The Rev-5.2.1 supply-channel-parallelism clause (`11.O remains on supply-channel surrogate until BOTH 11.N.1b and 11.N.2b.2 land`) is OVERRIDDEN by this amendment.
- **Task 11.O now BLOCKS on Task 11.N.2d.** Rev-2 spec authoring cannot begin until BOTH the Carbon-basket X_d primary is calibrated (Task 11.N.2c committed) AND the Y₃ regional-pan-EM inequality-differential panel is constructed (Task 11.N.2d committed under `source_methodology = 'y3_v1'`). The Aug-2023 → 2026-04-24 sensitivity panel from Task 11.N.2d.1 is NOT a Task 11.O blocking dependency — Task 11.O's sensitivity-cross-validation step consumes 11.N.2d.1's output lazily once both have committed.
- The supply-channel surrogate `proxy_kind = "net_primary_issuance_usd"` (already in `onchain_xd_weekly` from Task 11.N) becomes a **SECONDARY diagnostic** in 11.O's resolution matrix. It is no longer the primary X_d candidate; it is one of several diagnostic rows fed to the resolution-matrix sensitivity analysis.
- The COPM Transfer-channel X_d from Task 11.N.1b (`proxy_kind = "b2b_to_b2c_net_flow_usd"`) likewise becomes a secondary diagnostic, NOT a co-equal primary (this was already noted in 11.N.1b's PM-N1 hierarchy paragraph; this amendment formalizes the demotion).

**Rationale:** the design doc §1 anti-fishing position is "the architecture is one-way (calibration → primary selection → spec → review). Once primary X_d is chosen by the calibration's pre-committed methodology, downstream tasks consume it without re-selection. Mid-stream re-tuning of the primary measure is banned." Authoring 11.O's Rev-2 spec on supply-channel-only and then patching it via Rev-3 amendment-rider once Carbon X_d arrives would violate this discipline by giving the spec author two bites at the apple. Better: wait for the calibration-resolved primary, author 11.O Rev-2 once, against the canonical primary.

**Y-target shift (amendment-rider A1) status:** **RETIRED-as-applied (Task 11.N.2d landing; per §0.2 PM-CF-1 + §0.3 CR-FF-7 / PM-FF-3).** The Y₃ design doc landed at `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (committed `23560d31b`); per its §13 plan-fold instructions, Task 11.N.2d constructs the `Y₃_t` regional-pan-EM inequality-differential panel and Task 11.O Step 1 is updated to consume `Y₃_t` as primary Y. The DAG override here + the A1 retirement together constitute the operational Y-target shift; no further Rev-5.4 amendment-rider is needed for A1.

**Operational impact:**
- The orchestrator dispatches 11.N.1b + 11.N.2b.1 + 11.N.2b.2 + 11.N.2c + 11.N.2d sequentially-or-parallel-as-DAG-permits (11.N.1b can parallelize with 11.N.2b.1; 11.N.2b.2 blocks on 11.N.2b.1; 11.N.2c blocks on 11.N.2b.2; 11.N.2d blocks on 11.N.2c). **11.O dispatches AFTER 11.N.2d commits**; 11.N.2d.1 (sensitivity panel) may dispatch in parallel with 11.O.
- If a future Rev-5.x revision wants to parallelize 11.O with the Carbon-X_d ingestion-and-calibration chain or with the Y₃ panel construction, it MUST author a new amendment-rider justifying why the §1 anti-fishing position no longer applies — not just re-instate the old supply-channel parallelism clause silently.

**Cross-references:**
- Amendment-rider A9 in queue table above (DAG override status: APPLIED in Rev-5.3 brainstorm-fold + §0.2 PM-CF-1 + §0.3 PM-FF-1; not deferred).
- Rev-5.3 §0.1 brainstorm-fold delta bullet "Task 11.O DAG override".
- Rev-5.3 §0.2 PM-CF-1 (Task 11.N.2d insertion shifts blocker from 11.N.2c to 11.N.2d).
- Rev-5.3 §0.3 PM-FF-1 (Task 11.N.2d.1 sensitivity-panel split; runs in parallel with 11.O).
- Carbon-basket X_d design doc §1 anti-fishing position; §7 sequencing.
- Task 11.N.2d DAG clarification block ("Task 11.O BLOCKS on Task 11.N.2d").

---

## Phase 0 — Rev-1 Spec Derivation + Three-Way Review

### Task 1: Invoke `structural-econometrics` skill for Rev-1 spec

**Subagent:** foreground invokes the `structural-econometrics` skill (per user's global CLAUDE.md convention of skill-as-spec-deriver).

**Files:**
- Create: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`

- [ ] **Step 1:** Pin the design-doc commit hash via `git rev-parse HEAD -- contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md` and confirm it matches `437fd8bd2` (or record the current hash in the Rev-1 spec header if it has advanced). The Rev-1 spec derivation consumes the design doc verbatim. (Addresses RC N1.)
- [ ] **Step 2:** Invoke `structural-econometrics` skill passing: (a) the design doc absolute path as the question-scope; (b) the 13 items under §"Mandatory inputs to the Phase-0 structural-econometrics skill call" in the design doc as the resolution set. The skill must produce a Rev-1 spec that resolves every one of the 13 items with a concrete pre-committed choice and a justification trail.
- [ ] **Step 3:** Verify the Rev-1 spec file was written to the expected path with a non-empty body.
- [ ] **Step 4 (Rev-2 tightened — gating deliverable):** Require the Rev-1 spec to include a **13-input resolution matrix** as a standalone table with exactly four columns: (item | resolution | justification | reviewer-checkable condition). The 13 rows must be: sign prior, MDES, HAC kernel, bandwidth rule, interpolation side, alternate-LHS sensitivity, AR order, vintage discipline, reconciliation rule under heteroskedasticity, Quandt-Andrews window, GARCH parametrization, Dec-Jan seasonality, event-study co-primary. Each row's "reviewer-checkable condition" column must state the objective signal Tasks 2-4 reviewers will verdict against (e.g., "HAC kernel row PASSes iff a Bartlett/Parzen/QS choice is named AND a one-sentence citation is given AND a bandwidth-selection rule is specified"). Absence of the matrix, or any row with a null reviewer-checkable condition, is a spec-derivation failure. (Addresses PM B2.)
- [ ] **Step 5: Commit** the Rev-1 spec with message `spec(remittance): Rev-1 spec derived by structural-econometrics skill; 13-input resolution matrix embedded`.

### Task 2: Code Reviewer independent review of Rev-1 spec

**Subagent:** Code Reviewer

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-review-code-reviewer.md`

- [ ] **Step 1:** Dispatch Code Reviewer agent with the Rev-1 spec as input and the design doc's Phase-0 mandatory-inputs list as the coverage checklist. Focus: row-by-row verdict against the 13-input resolution matrix (Task 1 Step 4) — for each row, assert the reviewer-checkable condition is met. Do not tell the agent about parallel reviewers.
- [ ] **Step 2:** Verify the report landed at the expected path.
- [ ] **Step 3:** Log verdict (PASS / PASS-WITH-FIXES / BLOCK) and itemized BLOCK/FLAG/NIT findings.
- [ ] **Step 4:** Commit the scratch report with message `review(remittance): Code Reviewer Rev-1 spec review`.

### Task 3: Reality Checker independent review of Rev-1 spec

**Subagent:** Reality Checker

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-review-reality-checker.md`

- [ ] **Step 1:** Dispatch Reality Checker with the Rev-1 spec as input. Instruct the agent to audit every factual claim, data-source availability statement, literature citation, and evidence-backed methodology choice. Focus: for each row of the 13-input resolution matrix, verify the "justification" column cites something that exists (paper, corpus file, public dataset) and the "reviewer-checkable condition" can be evaluated against observable reality.
- [ ] **Step 2:** Verify report landed.
- [ ] **Step 3:** Log verdict + findings.
- [ ] **Step 4:** Commit with message `review(remittance): Reality Checker Rev-1 spec review`.

### Task 4: Technical Writer independent review of Rev-1 spec

**Subagent:** Technical Writer

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-review-technical-writer.md`

- [ ] **Step 1:** Dispatch Technical Writer with the Rev-1 spec as input. Focus: clarity, internal consistency, ambiguity resolution, reference integrity, reader-auditability of each pre-committed choice. Explicitly audit the 13-input resolution matrix for column-completeness and cross-section consistency (no row orphaned, no row with conflicting language elsewhere in the spec).
- [ ] **Step 2:** Verify report landed.
- [ ] **Step 3:** Log verdict + findings.
- [ ] **Step 4:** Commit with message `review(remittance): Technical Writer Rev-1 spec review`.

### Task 5: Technical Writer consolidates + applies fixes to Rev-1 spec

**Subagent:** Technical Writer

**Files:**
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1-fix-log.md`

- [ ] **Step 1:** Dispatch Technical Writer with all three review reports + the Rev-1 spec. Apply fixes in place: BLOCKs first (design-level issues in place; methodology BLOCKs escalated back to `structural-econometrics` skill if the reviewer-revealed methodology choice cannot be made at Technical-Writer level).
- [ ] **Step 2:** Verify the fix-log documents every finding's disposition (applied / deferred with reason / rejected with reasoning).
- [ ] **Step 3:** If any BLOCK was deferred, halt and require re-invocation of `structural-econometrics` skill for that specific item.
- [ ] **Step 4:** Confirm word-count delta is documented.
- [ ] **Step 5: Commit** the Rev-1 spec update + fix-log with message `spec(remittance): Rev-1 spec fix-pass, all 3-way reviewer findings addressed`.

---

## Phase 1 — Infrastructure Extension (Additive to Rev-4 Pipeline)

### Task 6: Scaffold remittance-exercise folders + scoped `.gitignore` rules

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/.gitkeep`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/figures/.gitkeep`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/pdf/.gitkeep`
- Create: `contracts/scripts/tests/remittance/__init__.py`
- Modify: `contracts/.gitignore`

- [ ] **Step 1: Write the failing test.** `contracts/scripts/tests/remittance/test_scaffold.py` asserts: three subfolders exist under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/`; `contracts/.gitignore` contains scoped rules for `contracts/notebooks/fx_vol_remittance_surprise/**/estimates/*.pkl`, `contracts/notebooks/fx_vol_remittance_surprise/**/pdf/`, and the same `_nbconvert_template/**/*.aux` pattern (or whichever pattern Rev-4 actually emits — cross-check the Rev-4 `contracts/.gitignore` block added by the CPI project and mirror it exactly to avoid drift; addresses CR N3); the `remittance/__init__.py` test package is importable.
- [ ] **Step 2: Run the test and confirm failure.**
- [ ] **Step 3: Create folders + gitkeeps; extend `.gitignore` with the three scoped rules.**
- [ ] **Step 4: Run the test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): folder scaffold + scoped gitignore for Phase-A.0`.

### Task 7: `env_remittance.py` — path constants + package pins

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/env_remittance.py`
- Create: `contracts/scripts/tests/remittance/test_env_remittance.py`

- [ ] **Step 1: Write the failing test.** Assert `env_remittance` exposes: `DUCKDB_PATH` (same value as Rev-4 `env.DUCKDB_PATH` — shared DB), `ESTIMATES_DIR`, `FIGURES_DIR`, `PDF_DIR`, `FINGERPRINT_PATH`, `POINT_JSON_PATH`, `FULL_PKL_PATH`, `GATE_VERDICT_REMITTANCE_PATH`, `README_REMITTANCE_PATH`, `NBCONVERT_TIMEOUT` (inherit from Rev-4), `REQUIRED_PACKAGES` (inherit from Rev-4). Assert `pin_seed(seed)` helper is re-exported from the Rev-4 `env.py` (no duplication). Assert the `conn` fixture at `contracts/scripts/tests/remittance/conftest.py` yields a DuckDB connection to the same DB.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3 (Rev-2 disambiguated — CR F2):** Implement `env_remittance.py` as a sibling to Rev-4 `env.py`. The absolute source path for the Rev-4 module is `contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py`. Import strategy: add a top-of-file block of the form `from contracts.notebooks.fx_vol_cpi_surprise.Colombia.env import pin_seed, NBCONVERT_TIMEOUT, REQUIRED_PACKAGES, DUCKDB_PATH as _REV4_DUCKDB_PATH`; set `DUCKDB_PATH = _REV4_DUCKDB_PATH` to signal the shared-DB contract. The remittance-specific `ESTIMATES_DIR`, `FIGURES_DIR`, `PDF_DIR`, `FINGERPRINT_PATH`, `POINT_JSON_PATH`, `FULL_PKL_PATH`, `GATE_VERDICT_REMITTANCE_PATH`, `README_REMITTANCE_PATH` are declared as module-level constants in `env_remittance.py` (NOT re-exported from Rev-4). If Python-package-import semantics fail (`contracts.notebooks…` is not a declared package), use a `sys.path`-insert shim with the absolute notebook-directory path; document the chosen strategy in the module docstring.
- [ ] **Step 4: Implement `conftest.py`** deferring to the Rev-4 conftest fixture. The Rev-4 conftest exists at `contracts/scripts/tests/conftest.py` (verified on disk per RC evidence); assume it exists (per PM N2; Rev-4 shipped). If the fixture-import fails at test time, fail loudly rather than silently re-implement.
- [ ] **Step 5: Run and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(remittance): env_remittance.py path constants, inherit-from-Rev-4 package pins`.

### Task 8: Empty `.ipynb` skeletons + placeholder README

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/README.md` (placeholder, overwritten by Task 24)
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/_readme_template.md.j2`
- Test: `contracts/scripts/tests/remittance/test_notebook_skeletons.py`

- [ ] **Step 1: Write the failing test.** Assert each `.ipynb` is valid `nbformat.v4` with: (a) title markdown cell; (b) "Phase-A.0 — Remittance-surprise → TRM RV" header with explicit anti-fishing disclaimer paragraph from the design doc's §"Why this is not a rescue of CPI-FAIL"; (c) "Gate Verdict" placeholder admonition ("populated after NB2 and NB3"); (d) zero code cells; (e) the Jinja2 template has the 7-section structure from Rev-4 but with remittance-specific wording.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author skeletons using `nbformat`.** Jinja2 template copied from Rev-4 `_readme_template.md.j2` as starting point with wording swaps.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): .ipynb skeletons + anti-fishing disclaimer headers + README template`.

### Task 9: Extend `cleaning.py` with `load_cleaned_remittance_panel`

**Subagent:** Data Engineer

**Files:**
- Modify: `contracts/scripts/cleaning.py` (additive only — new function)
- Test: `contracts/scripts/tests/remittance/test_cleaning_remittance.py`

**Rev 3.1 plan-body amendment rider (CR-B1):** Under Rev 3.1, the primary X is the weekly rich-aggregation vector from Phase-1.5 Task 11.B (6 on-chain channels per week), not a single scalar monthly-remittance column. The `CleanedRemittancePanelV1` scaffold below is *retained as a vestigial seam* so the dataclass hierarchy (V1→V2→V3) and the decision-hash-extension seam remain intact; its "remittance primary-RHS column" semantics are overridden by Phase-1.5 Task 11.B at panel-assembly time (Task 12+), where the 6-channel vector replaces the scalar. Implementers: the V1 dataclass should either (a) carry a scalar placeholder column that Task 11.A/B overwrites on load, or (b) promote the scalar slot to a `Mapping[str, np.ndarray]` container that Task 11.B populates. Decide at implementation time after reading Rev-1.1 spec §4.1 (Task 11.D output).

- [ ] **Step 1 (Rev-2 scoped — CR B2; Rev 3.1 amended — CR-B1): Write the failing test, restricted to primary-RHS only.** Assert `load_cleaned_remittance_panel(conn) → CleanedRemittancePanelV1` exists, where `CleanedRemittancePanelV1` is a new frozen dataclass mirroring `CleanedPanel` but adding **only** the remittance primary-RHS scaffold column (vestigial seam per the rider above — Phase-1.5 Task 11.B overrides the actual content; no auxiliary columns, no quarterly-corridor column — those extend the dataclass in Tasks 13 and 14). Assert it inherits the Rev-4 `LockedDecisions` + extends with remittance-primary-RHS decision identifiers only. Assert the existence (but not the full behavior) of a `_compute_decision_hash_remittance` seam that the Task-12 test will exercise end-to-end; Task 9 only asserts the primary-RHS scaffold column is hashed. Full-dataclass validation (V1 → V2 aux columns → V3 corridor) is deferred to Task 15 panel-integration.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.** The new function loads the Rev-4 frozen panel via `load_cleaned_panel(conn)`, joins the remittance primary-RHS column, and installs the decision-hash-extension seam. Do not pre-declare fields that Tasks 13/14 will add; let those tasks extend the dataclass additively (`CleanedRemittancePanelV2` extending V1, etc.) so each task's test asserts only the columns it is responsible for.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): cleaning.py extension — load_cleaned_remittance_panel (V1: primary-RHS only), additive to Rev-4`.

### Task 10: AR(1) surprise constructor module

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/surprise_constructor.py` (pure — frozen dataclass + free functions per functional-python skill)
- Test: `contracts/scripts/tests/remittance/test_surprise_constructor.py`

**Rev 3.1 plan-body amendment rider (CR-B1):** Under Rev 3.1, the AR(1)-surprise pathway is **no longer applied to the primary X** (the primary is the Phase-1.5 Task 11.B weekly 6-channel vector, which does not go through AR(1) surprise construction). Task 10's `construct_ar1_surprise` is retained as a reusable pure module scoped to **validation row S14 — the BanRep-quarterly series** (per Rev-1.1 spec §6). Its role is to emit the quarterly-cadence AR(1) surprise that the bridge-validation notebook (Phase-1.5 Task 11.C) and the downstream sensitivity-row ladder (Task 23) consume. Implementers: the AR-order parameter, the pre-sample discipline, and the interpolation-side resolution-matrix rows (Rev-1.1 §12 rows 6/7/8) are resolved by Task 11.D with the caveat that row 6 (LOCF direction) no longer applies under Rev 3.1 — BanRep-quarterly has no intra-quarter vintages to interpolate — and row 8 (vintage discipline) shifts from daily-on-chain-no-revision to quarterly-snapshot-at-publication-date.

- [ ] **Step 1 (Rev 3.1 amended — CR-B1): Write the failing test, scoped to the BanRep-quarterly validation path only.** Assert `construct_ar1_surprise(series, pre_sample_end_date, vintage_policy) → SurpriseSeries` exists. Assert the pre-sample / rolling refit policy pinned in the Rev-1.1 spec is honored. Assert the quarterly-snapshot vintage-policy path (per Rev-1.1 §12 row 8 after patch) is honored; the LOCF-interpolation path is no longer exercised (Rev-1.1 §12 row 6 superseded). Explicitly flag that the surprise constructor does NOT run against the primary X (Task 11.B weekly vector bypasses this module).
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.** Pure function; no side effects; input validation at boundaries only.
- [ ] **Step 4: Run and confirm pass with golden fixtures** (real BanRep-derived test data in `contracts/scripts/tests/remittance/fixtures/`).
- [ ] **Step 5: Commit** with message `feat(remittance): AR(1) surprise constructor per Rev-1 spec`.

---

## Phase 2a — Data Ingestion (historical anchor: Task 11 only)

> **Rev-3.1 F-3.1-1 reconciliation note**: Phase sequence is intentionally non-monotone (0, 1, **2a**, 1.5, **2b**, 3, 4). Task 11 landed DONE_WITH_CONCERNS BEFORE the escalation, so it physically precedes the Phase-1.5 middle-plan that responds to its finding. Phase 2b (Panel Extension, Tasks 12-15) resumes after Phase 1.5 convergence. Readers: follow 0 → 1 → 2a (Task 11) → 1.5 (Rev-3 middle-plan) → 2b (Tasks 12-15) → 3 → 4.

**Rev 3.1 structural note (PM-F2):** Phase 2 in Rev-3.1 spans Task 11 (DONE_WITH_CONCERNS at `939df12e1`, retained here as historical context because its quarterly-only BanRep finding is the trigger for Phase 1.5) followed by the textual insert of **Phase 1.5 — Data-Bridge** (Tasks 11.A–11.E) and then Phase 2 resumes with Tasks 12-15. Textually this means "Phase 2" appears as two section blocks in the document: the first containing only Task 11 (historical), the second (after Phase 1.5) containing Tasks 12–15. This is intentional — it preserves the causal ordering (Task 11 triggers Phase 1.5 triggers Phase-2-resume) while keeping Task 11 inside Phase 2 per the Rev-2 shape.

### Task 11: BanRep aggregate monthly remittance — MPR-derived manual compilation (Rev-2, may parallelize with Task 12)

**Subagent:** Data Engineer

**Scheduling note (Rev-2, PM F4):** Task 11 and Task 12 share no code dependency; their failing-test authoring and implementation can run in parallel. The Task-12 decision-hash-extension only depends on Task 9's `CleanedRemittancePanelV1` seam, not on Task 11's fixture.

**Rev-2 correction (RC B1):** The original plan asserted a "pinned public Socrata endpoint" for aggregate monthly remittance. This is **factually wrong**: the BanRep Socrata dataset `mcec-87by` at `datos.gov.co/resource/mcec-87by.json` is the *Tasa de Cambio Representativa del Mercado* (TRM) feed, not remittance. No public API (Socrata, SDMX, REST, or otherwise) publishes BanRep aggregate-monthly family-remittance inflows as a single time series. The access pattern is: BanRep's quarterly **Monetary Policy Report (MPR)** / *Informe de Política Monetaria* PDFs and Excel annexes publish remittance aggregates in Balance-of-Payments tables. These must be compiled by hand once per quarter, committed as a real-data fixture, and re-pulled manually (not by API) when a new MPR vintage drops. Vintage-timestamp = MPR publication date.

**Files:**
- Create: `contracts/scripts/banrep_remittance_loader.py` (loader, not API fetcher)
- Create: `contracts/data/banrep_remittance_aggregate_monthly.csv` (manually compiled real-data fixture, committed; source column names each cell's originating MPR table)
- Create: `contracts/data/banrep_remittance_aggregate_monthly.SOURCE.md` (per-row provenance: MPR quarter, table number, URL, access date)
- Test: `contracts/scripts/tests/remittance/test_banrep_remittance_loader.py`

- [ ] **Step 1 (Rev-2 manual-compilation subtask):** Before writing any code, the Data Engineer manually compiles `banrep_remittance_aggregate_monthly.csv` from the BanRep MPR series covering the Rev-4 sample window. Each row: `date` (month-end), `aggregate_inflow_usd`, `mpr_vintage_date`, `source_table`. The `SOURCE.md` file records per-row provenance (MPR URL + table reference + access timestamp) so a reviewer can audit the compilation by hand.
- [ ] **Step 2: Write the failing test.** Assert `load_banrep_aggregate_monthly_remittance(csv_path) → DataFrame` exists and returns columns `date` (month-end) + `aggregate_inflow_usd` + `mpr_vintage_date`. Assert the loader is a pure read of the committed CSV (no network calls). Assert the row count matches the expected monthly count over the Rev-4 sample window. Assert every row has a non-null `mpr_vintage_date`. Do **not** assert "pinned endpoint returns the same data" — the re-pull mechanism is manual MPR re-parse, not an API call.
- [ ] **Step 3: Run and confirm failure.**
- [ ] **Step 4: Implement** the pure-read loader. Document explicitly in the module docstring that re-pulling requires MPR re-parse; there is no API.
- [ ] **Step 5: Run and confirm pass** against the committed fixture.
- [ ] **Step 6: Commit** with message `feat(remittance): MPR-derived aggregate monthly remittance loader + manually compiled fixture with per-row SOURCE provenance`.

**Task 11 post-implementation status (Rev 3, 2026-04-20):** implementation committed at `939df12e1` as DONE_WITH_CONCERNS. File name actually used was `banrep_remittance_fetcher.py` (not `_loader.py` as the Rev-2 plan text said); schema emitted `{reference_period, value_usd, mpr_vintage_date, source_url}`. The implementer exhaustively verified that BanRep publishes this series at QUARTERLY cadence only (104 rows 2000-Q1 → 2025-Q4, all carrying `mpr_vintage_date = 2026-03-06` snapshot; no revision archive). The monthly-cadence primary in Rev-1 spec §§4.6/4.7/4.8 is invalidated. **Phase 1.5 Tasks 11.A–11.E (below, promoted out of Phase 2 per Rev-3.1 PM-F2) are the Rev-3 middle-plan response.**

---

## Phase 1.5 — Data-Bridge (Rev 3.1 promoted per PM-F2)

**Phase-1.5 rationale:** Rev-3 originally placed Tasks 11.A–11.E inside Phase 2 alongside Task 11 and Tasks 12–15. Rev-3.1 (PM-F2) promotes them to a new Phase 1.5 "Data-Bridge" sub-phase between Phase 1 and Phase 2, for three reasons: (i) the 5 tasks form a single atomic workstream (daily-native primary acquisition + bridge-validation + spec patch + spec-patch review) distinct from the Phase-2 panel-extension workstream (Tasks 12–15); (ii) promoting them restores the Rev-2 PM F4 granted parallelism between Task 11 and Task 12 (which Rev-3's Phase-2-gate had silently retracted); (iii) a standalone phase boundary makes the gate language ("Phase 2 resumes only after Task 11.E PASSes") clean rather than surgical-mid-phase. Task IDs 11.A–E are preserved.

**Phase-1.5 gate (clarified per Rev 3.1 PM-F2 alt-resolution):** Task 12 depends only on Task 9's `CleanedRemittancePanelV1` scaffold (per Rev-2 PM F4) and may begin its failing-test authoring in parallel with Phase 1.5. However, Task 12's *implementation step* (merging primary X into the panel) is blocked until Task 11.E PASSes, because the primary X definition is set by the Rev-1.1 spec patch (Task 11.D output). Tasks 13–15 remain fully blocked until Phase 1.5 closes. Phase 3 remains fully blocked until Phase 2 closes.

### Task 11.A: Daily on-chain COPM + cCOP flow acquisition via Dune MCP (Rev 3 insert; Rev-3.1 Phase-1.5 promoted)

**Subagent:** Data Engineer (MANDATORY: `mcp__dune__*` tools)

**Rationale (Rev 3.1 amended — RC-F2, RC-N2):** The quarterly-only BanRep finding means the monthly-cadence primary cannot be built from public off-chain data. The daily-native middle-plan replaces it with a daily on-chain signal aggregated to weekly via a rich statistics vector (not a flat sum), preserving intra-week information that a monthly-aggregate X would discard. COPM launched Apr-2024 (adoption-colour figures such as "$200M/mo" and "100K Littio users" circulate in marketing materials but are not in-corpus-verified by Reality Checker at Rev 3.1 review; removed from load-bearing rationale per RC-N2; retained only as non-load-bearing background). cCOP launched Oct-2024. Per `CCOP_BEHAVIORAL_FINGERPRINTS.md` line 27: the 4,913-sender figure is specifically the cCOP-OLD cohort (address `0x8a56…`, "Dead (migrated Jan 2025)") — it is a pre-migration lifetime stock, NOT a forward-looking active-post-Oct-2024 population (RC-F2 correction). The post-migration cohort populating Apr-2024 → present may be smaller and must be recomputed by the Task 11.A subagent at acquisition time; "≥4,913 lifetime cleaned-cohort senders (pre-migration)" is the only defensible phrasing. Union window: Apr-2024 → most-recent ≈ 22-24 months daily. **Pre-committed N for downstream T3b critical value and bridge-gate power analysis: N = 95 weekly observations** (the conservative floor anchored to Rev-4-panel-end Feb-2026; RC-F3 single-number commitment). If the observed sample yields more than 95 weekly rows at Task 11.A implementation time, the additional rows are held in the fixture but the pre-committed test statistic uses exactly N=95 anchored at the Feb-2026 floor.

**Data-target disambiguation (Rev 3.1 — RC-B2):** two distinct on-chain entities must not be conflated:
- **cCOP TOKEN contract address** — the ERC-20 token itself (holds balances, `transfer`/`transferFrom` events are the raw transfer signal). The Task 11.A subagent must look up the current cCOP token contract via Dune `mcp__dune__searchTablesByContractAddress` or Celo block explorer before querying; **note the post-2026-01-25 migration renamed cCOP → COPm at the SAME contract address** (per corpus `CCOP_BEHAVIORAL_FINGERPRINTS.md` migration row) — the subagent must handle the rename and verify the address maps to the active (not "old/dead") contract. **Rev-3.1 F-3.1-2 footnote**: the corpus file `CCOP_BEHAVIORAL_FINGERPRINTS.md` has an internal date inconsistency on this migration — line 27 reads "Jan 2025" while line 163 reads "Jan 2026"; Rev-3.1 aligns with the more specific line-163 date ("2026-01-25") as the canonical rename date. The subagent MUST use 2026-01-25 as the cutover and ignore the line-27 reading.
- **Mento BROKER contract address** `0x777a8255ca72412f0d706dc03c9d1987306b4cad` — the swap venue (Mento protocol broker, NOT the token). Its events are swap-level, not transfer-level. Dune query `#6939814` queries broker swaps and is the correct source for swap-venue volumes; it is **not** a source for token-level transfers.

A subagent that confuses these two queries the broker when it needs token transfers, or vice versa — the data acquired will be categorically wrong. Task 11.A Step 3 must explicitly verify each query's target entity before execution.

**Files:**
- Create: `contracts/scripts/dune_onchain_flow_fetcher.py` (pure loader + validator; no network on import) — filename preserved per Rev-3 precedent (CR-N1 optional rename to `dune_onchain_remittance_fetcher.py` rejected as unnecessary churn)
- Create: `contracts/data/copm_ccop_daily_flow.csv` (real-data fixture, committed; columns: `date, copm_mint_usd, copm_burn_usd, copm_unique_minters, ccop_usdt_inflow_usd, ccop_usdt_outflow_usd, ccop_unique_senders, source_query_ids`)
- Create: `contracts/data/dune_onchain_sources.md` (per-query provenance log)
- Test: `contracts/scripts/tests/remittance/test_dune_onchain_flow_fetcher.py`

- [ ] **Step 1 (Rev 3.1 tightened — CR-F1; Rev 3.2 factual correction):** Write failing test asserting the 8-column schema + daily-monotone date index + pre-Oct-2024 NaN cCOP discipline + non-negative USD + non-empty `source_query_ids` + `FileNotFoundError` on missing path + determinism + **row count ≥ 580 AND ≥ 500 rows with non-zero `copm_mint_usd OR ccop_usdt_inflow_usd`** (CR-F1 tightening: bare row-count is satisfiable by zero-filled padding; the non-zero constraint ensures the data is economically load-bearing). **Rev 3.2 threshold correction**: the Rev-3.1 text said `≥ 720` on the premise of "24 months × 30 days" but COPM's actual on-chain launch is 2024-09-17 (verified via Dune `#6940691`), yielding 585 calendar days to April 2026. The 720 figure would force zero-padding a pre-launch synthetic window — the exact anti-pattern CR-F1's 500-non-zero companion is designed to forbid. The COPM-launch-anchored floor of 580 preserves CR-F1's intent. Additionally assert `copm_mint_usd` has non-NaN values spanning 2024-09-17 → latest and `ccop_usdt_inflow_usd` has non-NaN values spanning 2024-10-31 → latest with no internal NaN gaps exceeding 3 consecutive days (per CR-F1 full recommendation).
- [ ] **Step 2:** Run and confirm failure.
- [ ] **Step 3 (Rev 3.1 schema-verification step added — RC-F1):** Acquire via Dune MCP. Before executing any cached query, call `mcp__dune__getDuneQuery` on each query ID (`#6941901`, `#6940691`, `#6939814`) and verify the **actual** query title and target entity match the expected role. Specifically: `#6940691` is labeled "COP Token Comparison (all 3 tokens)" in `CCOP_BEHAVIORAL_FINGERPRINTS.md:209` — NOT "COPM transfers" as the Rev-3 plan text said (RC-F1). If the verified schema does not match the expected per-role schema for this task, **log the mismatch in `contracts/data/dune_onchain_sources.md`** and either (a) use `mcp__dune__executeQueryById` on a different cached query whose schema matches, or (b) use `mcp__dune__updateDuneQuery` only if existing-query modification is required (RC-N1: prefer read-only `mcp__dune__executeQueryById` before any `updateDuneQuery` that burns credits). Credit budget: ≤30 free-tier credits.
- [ ] **Step 4:** Write CSV with real joined data + `dune_onchain_sources.md` provenance log (including schema-verification log from Step 3).
- [ ] **Step 5:** Implement pure loader + validator.
- [ ] **Step 6:** Run tests, confirm pass.
- [ ] **Step 7:** Commit with message `feat(remittance): daily COPM+cCOP on-chain flow fixture + Dune loader (Rev-3 Task 11.A, Rev-3.1 schema-verified)`.

**Recovery protocol (Rev 3.1 — PM-F1; replaces Rev-3 "Fallback" note):** Three concrete failure modes enumerated:
1. **Dune MCP free-tier exhausted (credits burned).** Action: foreground decides between (a) manual Dune CSV export paste-in — the `source_query_ids` field of the fixture becomes a pasted-from-Dune-UI URL list rather than an MCP-returned ID list, satisfying Step-1's non-empty assertion; the `dune_onchain_sources.md` log records the paste-in method explicitly; (b) direct Celo RPC via Alchemy free tier — the loader adopts a different source-column taxonomy and the `source_query_ids` field is replaced by `source_rpc_endpoints`. Decision criterion: prefer (a) if Dune has the exact query cached; prefer (b) if Dune queries need modification beyond the credit budget. Log the decision + error messages + paste-in sources at `contracts/.scratch/2026-04-20-dune-mcp-fallback-log.md` (PM-N3 explicit scratch path).
2. **Query schema mismatch at Step-3 verification.** Action: per Step 3 body above. Does not require user escalation unless all three cached query IDs fail schema verification simultaneously, in which case escalate.
3. **Zero or near-zero data returned (e.g., all-zero-flow days exceeding 50% of rows).** Action: halt acquisition and escalate to user — either the query filters are misconfigured (fixable by Step-3 verification re-run) or the on-chain rails are genuinely sparse (a finding that itself requires re-scoping of the identification strategy). Do NOT fabricate data or pad with zeroes.

Do NOT fabricate data under any failure mode.

### Task 11.B: Weekly rich-aggregation module (daily → weekly vector; Rev 3 insert)

**Subagent:** Data Engineer

**Rationale:** Flat daily-sum-to-weekly loses intra-week heterogeneity. A multi-channel weekly vector preserves information that is load-bearing for the primary identification at small sample size (N≈95 weekly obs).

**Files:**
- Create: `contracts/scripts/weekly_onchain_flow_vector.py` (pure transformation module)
- Create: `contracts/scripts/tests/remittance/test_weekly_onchain_flow_vector.py`
- Create: `contracts/scripts/tests/remittance/fixtures/golden_daily_flow.csv` (hand-authored synthetic 35-row fixture spanning 5 Friday-anchored weeks)

- [ ] **Step 1 (Rev 3.1 hardened — CR-B2; silent-test-pass prevention; Rev 3.3 concentration-channel clarification):** Write failing test for `aggregate_daily_to_weekly_vector(daily_df, friday_anchor_tz="America/Bogota") → pd.DataFrame` with 6 output channels per week: `flow_sum_w`, `flow_var_w` (daily-within-week variance), **`flow_concentration_w` (HHI of the 7 daily |net_flow| values within the week, computed as `(|daily_flow|² summed) / (|daily_flow| summed)²`; this is INTRA-WEEK CONCENTRATION — a weekly scalar that captures whether the week's activity is spiky vs diffuse across its 7 days; it is NOT per-address concentration — the daily CSV does not carry per-address data and Task 11.B does not require it; a Task-11.A code-review reviewer misread this as per-address HHI, which is explicitly NOT the intended channel semantics)**, `flow_directional_asymmetry_w` (pos-day count minus neg-day count, where a pos-day is defined per-channel as `net_flow_usd > 0` for COPM (`copm_mint_usd − copm_burn_usd`) and for cCOP (`ccop_usdt_inflow_usd − ccop_usdt_outflow_usd`); resolving CR-N3), `unique_daily_active_senders_w` (union across COPM+cCOP), `flow_max_single_day_w`. Assert pinned values from the golden fixture at 6-decimal tolerance.

  **Independent reproduction witness (MANDATORY — mirrors Task 10 `test_golden_fixture_matches_independent_fit` pattern against the 5-instance CPI silent-test-pass catalogue):** the pinned expected values MUST be computed via an independent reproduction path in the test file that does NOT import `weekly_onchain_flow_vector`. For each of the 6 channels, the test file inlines an independent computation (e.g., `flow_sum_w` via a pandas `resample('W-FRI').sum()` one-liner; `flow_var_w` via `resample('W-FRI').var(ddof=0)`; `flow_concentration_w` via an inline `(abs_flow ** 2).sum() / abs_flow.sum()**2` reduction; analogously for the remaining three channels). The 6 pinned values in the assertion block are the outputs of these inline independent computations, committed to the test file BEFORE Step 3 implementation. Step 3's implementation must match those pinned values to pass. This guards against the silent-test-pass pattern where an implementer computes expected values from the same function being written.

  Assert determinism + order-invariance + pre-data-window NaN discipline.
- [ ] **Step 2:** Run and confirm failure — the failure mode must be "function does not exist" or "function returns wrong shape", NOT a tolerance mismatch (tolerance mismatch at this stage is evidence the independent reproduction witness is buggy, which is itself a blocker).
- [ ] **Step 3:** Implement pure vectorized aggregation (pandas groupby + named-agg). The implementation must match the independent reproduction witness to 6-decimal tolerance; any divergence means either (a) the implementation is wrong, or (b) the independent reproduction witness is wrong — both are blocking.
- [ ] **Step 4:** Run tests, confirm pass.
- [ ] **Step 5:** Commit with message `feat(remittance): weekly rich-aggregation vector preserving daily information + independent reproduction witness (Rev-3 Task 11.B, Rev-3.1 silent-test-pass hardening)`.

### Task 11.C: Bridge-validation notebook (pre-registered ρ-gate; Rev 3 insert)

**Subagent:** Analytics Reporter (X-trio discipline per `feedback_notebook_trio_checkpoint.md`)

**Rationale:** Cross-validate that the daily on-chain aggregate is an economically meaningful proxy for the BanRep remittance channel. Pre-register the gate BEFORE computing any correlation. Under FAIL-BRIDGE the primary regression still runs (X is a well-defined on-chain observable), but the economic-interpretation narrative shifts from "remittance" to "crypto-rail income-conversion."

**Files:**
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb` (one-off validation notebook, 4-5 X-trio cells)
- Create: `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md` (scratch log of the gate outcome)

- [ ] **Step 1 (Rev 3.1 clarified — CR-F2, PM-F3 decision gate):** Author failing test for the notebook's §1 (data alignment), §2 (quarterly aggregation), §3 (Pearson ρ + sign-concordance), §4 (verdict emission). The test is a **post-authoring behavior test** (asserts cells execute correctly and emit the expected verdict structure), NOT a structural-existence test (it does not fail merely because §1 does not exist yet). Author-implementer's choice of granularity (PM-F3): either (a) a single Task 11.C authoring pass of 4-5 X-trios under the atomicity ceiling if the data alignment is simple enough (recommended when Task 11.A returns a clean Apr-2024 → present daily CSV with no gaps > 3 days), or (b) split into 11.C.1 (§1 alignment + §2 quarterly aggregation, 2-3 X-trios) and 11.C.2 (§3 Pearson-ρ + §4 verdict emission, 2-3 X-trios) if data cleanup adds complexity. The decision is made at 11.C authoring time by the foreground; if split, renumber internally (task IDs remain 11.C.1 / 11.C.2 — the Phase 1.5 task count stays at 5 by convention). X-trio HALTs between each section for human review.
- [ ] **Step 2:** Run nbconvert-execute; confirm failure (expected failure mode: notebook has no code cells yet, nbconvert returns non-zero).
- [ ] **Step 3:** Author NB 0B cells trio-by-trio. Pre-registered gate logic (committed BEFORE any ρ computation):
  - PASS-BRIDGE: ρ > 0.5 on N=7 quarterly obs AND sign-concordant on Δ quarter-over-quarter
  - FAIL-BRIDGE: ρ ≤ 0.3 OR sign-discordant
  - INCONCLUSIVE-BRIDGE: 0.3 < ρ ≤ 0.5
- [ ] **Step 4:** Run notebook, confirm test pass + emit scratch log with verdict.
- [ ] **Step 4.5 (Rev 3.1 mandatory — CR-F2):** Inline integration-test execution: `subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb", "--ExecutePreprocessor.timeout=600"])` and assert `returncode == 0`. This is the bridge-notebook analogue of the Phase-3 protocol note (line 384) — every notebook-authoring task gets an inline nbconvert-execute guard to catch the silent-test-pass pattern locally.
- [ ] **Step 5:** Commit with message `feat(remittance): bridge-validation notebook (on-chain vs BanRep quarterly; Rev-3 Task 11.C, Rev-3.1 nbconvert-guarded)`.

**Recovery protocol (Rev 3.1 — PM-F1):** Bridge-gate outcome recovery paths:
1. **FAIL-BRIDGE (ρ ≤ 0.3 or sign-discordant).** The primary regression still runs (the on-chain X is a well-defined observable), but the economic-interpretation narrative shifts from "remittance" to "crypto-rail income-conversion." This shift MUST be documented in the completion memory (Task 30a) and the Rev-1.1.1 spec patch (not-yet-authored; create at the time FAIL-BRIDGE is observed) re-scopes the X interpretation in §4.1 only (no mechanism change — §§4.2+ unchanged). No new three-way spec review required for Rev-1.1.1 scope-narrowing of the interpretation alone; the mechanism-preservation qualifier matches Task 11.D's decision gate (see below).
2. **INCONCLUSIVE-BRIDGE (0.3 < ρ ≤ 0.5).** The primary regression still runs; the completion memory documents the inconclusive bridge as a caveat; no spec patch required.
3. **PASS-BRIDGE.** Proceed without narrative shift.

**Rev 3.4 addition — NaN-ambiguity handling** (Task 11.B code-review "subtlety #1"): The Task 11.B output's 6 channels emit NaN for BOTH (a) partial-week boundary weeks (< 7 days present) and (b) all-zero full weeks (concentration denominator = 0). The Task 11.C §2 quarterly aggregation MUST distinguish these two cases when propagating to the quarterly bridge sample, because "no flow" and "insufficient data" are economically different signals. Concretely: at §2 time, before quarterly resampling, the notebook must flag each weekly row with a `nan_reason_w` enum in `{"partial_week", "all_zero_full_week", "valid"}` computed from the underlying 7-day count + sum-of-abs. Quarterly aggregation drops `partial_week` rows (no-data) but treats `all_zero_full_week` rows as valid zero-observations (included in the quarterly sum at value 0). Document this rule in the bridge-result scratch log.

**Rev 3.4 addition — N≥95 vs observed-84 reconciliation** (forward-looking from Task 11.B real-data smoke test): Task 11.B's smoke test produced 84 weekly rows from the Task 11.A 585-row daily CSV (83 full + 1 partial boundary). The Rev-3.1 pre-committed floor of N=95 was anchored to the Rev-4-panel-end (Feb-2026) but assumed a longer acquisition window than the actual COPM launch allows. Task 11.D's Rev-1.1 spec patch MUST reconcile: either (a) drop the pre-committed N floor to 78-84 (clipped to Rev-4-panel-end) with revised MDES in §4.5, or (b) authorize a Task-11.A refresh to extend the acquisition window past 2026-04 until the Rev-4-panel-end includes ≥95 weeks (not feasible since Rev-4 panel ends Feb-2026 which is BEFORE the current 2026-04-24 CSV end — so option (a) is the only coherent resolution). Task 11.D Step 1's decision-gate treats this as a **wording/cadence-only change** (numeric threshold adjustment on an already-defined resolution row) — no `structural-econometrics` skill re-invocation required.

### Task 11.D: Rev-1.1 spec patch (Rev 3 insert — SPEC amendment)

**Subagent:** Technical Writer (amendment) + structural-econometrics skill re-invocation if any new methodology decision surfaces

**Rationale:** The daily-native middle-plan changes the primary X definition; the Rev-1 spec must reflect the amendment with explicit supersedes-banner language. The 13-input resolution matrix must be revisited for any row whose resolution is affected (sign prior, MDES at new effective-N, HAC bandwidth at new sample size, interpolation side no longer applies, AR order no longer on monthly-source, vintage policy now on daily on-chain source, reconciliation unchanged, Quandt-Andrews window unchanged, GARCH-X unchanged, Dec-Jan seasonality unchanged, event-study unchanged).

**Files:**
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (patch to Rev-1.1 in place; update frontmatter `status` + `Revision history`)
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md`

- [ ] **Step 1 (Rev 3.1 decision gate — PM-F4; matrix-row checklist — CR-N2):** Up-front classification gate: for each of the four §12 matrix rows being patched (5 Andrews bandwidth, 6 interpolation side, 7 AR order, 8 vintage discipline), classify the patch as either **wording-only/cadence-only** (TW completes alone) or **economic-mechanism change** (requires `structural-econometrics` skill re-invocation for that row before TW continues). The concrete rule: if the row's resolution column changes a named kernel/method/parameter/number (e.g., Andrews bandwidth rule changes from Bartlett to Parzen, AR order changes from 1 to 2, MDES target changes numerically), it is an economic-mechanism change. If the row's resolution column changes only which cadence or data source is described (e.g., "monthly series" → "daily on-chain aggregated weekly vector" with the same AR order), it is wording-only. Decision-gate output committed to the fix-log before any patch text is authored.

  Author the Rev-1.1 patch in place as a checklist:
  - [ ] Add "supersedes banner" section noting the Task 11 finding and the quarterly-only BanRep reality, grounded on the suameca series 4150 metadata (matching Rev-3.1 Revision history rewrite).
  - [ ] Redefine primary X in §4.1 as the weekly rich-aggregation vector from Phase-1.5 Task 11.B.
  - [ ] Add BanRep quarterly as a pre-registered validation row S14 in §6, fed by the Task-10 AR(1)-constructor-on-quarterly path and Task-13 `a1r_quarterly_rebase_bridge` aux column.
  - [ ] Update §4.5 MDES to reflect new N = 95 (the pre-committed conservative floor per Task 11.A Rev-3.1 rationale; RC-F3 single-number commitment).
  - [ ] Patch §12 matrix row 5 (Andrews bandwidth at new N=95; classify per decision gate).
  - [ ] Patch §12 matrix row 6 (interpolation side → "no longer applies under daily-on-chain primary; superseded"; wording-only).
  - [ ] Patch §12 matrix row 7 (AR order → "no longer applies to primary; retained for validation-row S14 quarterly AR(1) per Task 10"; classify per decision gate).
  - [ ] Patch §12 matrix row 8 (vintage discipline → "daily on-chain does not revise; quarterly validation-row vintage = BanRep MPR publication date"; wording-only).
- [ ] **Step 2:** Fix-log documents every matrix-row change with its decision-gate classification from Step 1. Any methodology-row classified as economic-mechanism change requires `structural-econometrics` skill re-invocation BEFORE TW patches the row body; fix-log records the skill-re-invocation output.
- [ ] **Step 3:** Commit with message `spec(remittance): Rev-1.1 patch — daily-native primary X + BanRep-quarterly validation row (Rev-3 Task 11.D, Rev-3.1 decision-gated)`.

### Task 11.E: Three-way review of Rev-1.1 spec patch (Rev 3 insert)

**Subagent:** three parallel dispatches — Code Reviewer + Reality Checker + Technical Writer (spec-review trio per `feedback_three_way_review.md`).

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-review-technical-writer.md`

- [ ] **Step 1 (Rev 3.1 fix-log-as-input — CR-F3):** Dispatch three reviewers in parallel; each receives **both** the patched spec at `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (now Rev-1.1) AND the fix-log at `contracts/.scratch/2026-04-20-remittance-spec-rev1.1-fix-log.md` as first-class review inputs (precedent: Rev-2 plan-review's fix-log was similarly a first-class reviewer deliverable; without the fix-log the reviewers cannot evaluate the decision-gate classifications Task 11.D Step 2 committed). Each reviewer independently reviews the Rev-1.1 patch against: (a) consistency with Rev-1 pre-Rev-1.1 content not superseded, (b) coverage of all 13 resolution-matrix rows that need updating, (c) anti-fishing framing preserved or strengthened (the patch is explicitly framed as a methodology escalation responding to a real-world data reality, NOT as a rescue of a null result), (d) factual grounding of any new claims (RC), (e) clarity of the supersedes-banner and the new primary X definition (TW).
- [ ] **Step 2:** Consolidate via Technical Writer; apply all BLOCKs + FLAGs in place; NITs optional.
- [ ] **Step 3 (Rev 3.1 cycle-cap boundary — PM-B2):** Iterate with an explicit cycle definition. **One cycle = one full round-trip** of: (a) three reviewers dispatched in parallel, (b) Technical Writer consolidates all three reports, (c) if any reviewer flagged BLOCK, the offending reviewer's specific BLOCK items are fixed in the spec and **that same reviewer** is re-dispatched (not all three) on the next round-trip. Plan Rule 13 caps the **count of full round-trips at 3**. Additionally, to guard against pathological ping-pong, a per-reviewer re-dispatch counter is also capped at 3 (a single reviewer may BLOCK at most 3 times before escalation). After the third failed full round-trip OR the third re-dispatch of the same reviewer — whichever triggers first — halt and escalate to the user for scope renegotiation, not silent recursion. If a BLOCK is methodology-level (reveals an economic-mechanism error in the §12 resolution matrix that was mis-classified as wording-only at Task 11.D Step 1), the `structural-econometrics` skill is re-invoked before the next round-trip; skill re-invocation does NOT itself count as a new cycle.
- [ ] **Step 4:** Commit with message `spec(remittance): Rev-1.1 fix-pass, all 3-way reviewer findings addressed (Rev-3 Task 11.E, Rev-3.1 cycle-bounded)`.

**Recovery protocol (Rev 3.1 — PM-F1):** BLOCK-routing decision tree:
1. **Code Reviewer BLOCK** (e.g., file-path errors, citation-block format violations, commit-message convention drift). Route to Technical Writer for in-place patch; re-dispatch Code Reviewer only.
2. **Reality Checker BLOCK** (e.g., cited paper does not exist, data-source availability claim is unverified, numeric value does not ground in in-tree provenance). Route to Technical Writer if the fix is textual; route to `structural-econometrics` skill if the fix requires re-deriving a methodology choice; re-dispatch Reality Checker only.
3. **Technical Writer BLOCK** (e.g., ambiguous supersedes banner, contradictory paragraphs, unclear primary-X definition). Route to Technical Writer for self-consolidation; re-dispatch Technical Writer only (a second-TW-pass is permitted and is counted as a cycle).
4. **Multiple simultaneous BLOCKs.** TW consolidation batches all fixes into one round-trip; all offending reviewers are re-dispatched in parallel (counts as one cycle, not N cycles).

**Gate:** Phase-2 tasks' implementation steps shall NOT resume until Task 11.E returns a unanimous PASS-WITH-FIXES or PASS verdict and TW consolidation is committed. This gate is non-negotiable per memory rule `feedback_three_way_review.md`. Task 12's failing-test authoring may begin in parallel with Phase 1.5 per the Phase-1.5 rationale above, but its implementation step is blocked on Task 11.E.

---

## Phase 1.5.5 — Spec Escalation: Power-User Filter Design Under Symmetric Similarity Objective (Rev 4 insert)

**Rationale.** Task 11.E three-way review of Rev-1.1.1 returned CR REJECT + RC NEEDS WORK + TW NEEDS FIXES (see Rev 4 history bullet above). Beyond the review findings, a 4th structural concern was surfaced: the unfiltered cCOP aggregate in Task 11.A's Dune query #7366593 is contaminated by a small power-user group (Medellín early adopters, bots, treasury operations, payment processors) whose behavior does NOT map to household remittance. This is directly evidenced by the top 5 single-day events showing inflow ≈ outflow roundtripping to <1%. Rev-1.1.1's bridge FAIL verdict at Task 11.C (ρ=+0.7554 levels PASS but 2-of-5 quarter-over-quarter sign-concordance FAIL) is therefore most parsimoniously explained not as "on-chain remittance proxies fail" but as "this particular unfiltered aggregate does not measure household remittance." Phase 1.5.5 inserts a discovery-research-brainstorm-iterate workflow producing a Rev-2 spec with an explicit power-user filter.

**Non-stop filter-design policy with explicit exit criterion (Rev 4.1 amended).** Tasks 11.G and 11.H form an iterative search loop with a pre-committed objective: find the filter F that maximizes a composite symmetric similarity measure M(filter_applied_to_on_chain_series, BanRep_quarterly_remittance). **Rule 13's 3-cycle cap does NOT apply to filter iteration within Task 11.H** — the cap applies only to Rev-2 spec three-way review at Task 11.J. The "non-stop" guardrail is pre-commitment, not cycle-limiting: M, F, and the weights across component similarity measures are pre-committed in Task 11.H Step 1 BEFORE any filter is evaluated, and mid-search modification is banned. **Critical coexistence with Task 11.K exit criterion (Rev 4.1):** "non-stop" means "iterate until argmax M ≥ M_threshold OR any Task 11.K kill criterion fires." The non-stop policy does NOT force a filter when no remittance signal exists — it forces completeness of the pre-committed search, after which either a filter passes (proceed to Task 11.I) or the EXIT disposition is authored (re-scope to pivot candidate per `project_colombia_yx_matrix.md`).

### Task 11.F: Peak-day events + user-intent + data-source verification research (Rev 4 insert; Rev 4.1 scope-expanded)

**Subagent:** background-mode general-purpose subagent with WebSearch + WebFetch (and Dune MCP for on-chain disambiguation + mcp__arxiv for any academic-paper lookups on cCOP/CELO usage studies).

**Files:**
- Create: `contracts/.scratch/2026-04-24-ccop-peak-day-event-research.md`
- Create (if evidence log exceeds 1500 words): `contracts/.scratch/2026-04-24-ccop-peak-day-event-research-evidence.md`
- Inputs:
  - `contracts/data/copm_ccop_daily_flow.csv`
  - `contracts/scripts/dune_onchain_flow_fetcher.py` (for Dune query #7366593 provenance + SQL logic reference)
  - Prior research corpus at `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/` and `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/`

**Research axes (Rev 4.1 — five axes, all required).** The prior Rev-4 scope covered only Axis 1 (peak events); Rev 4.1 adds Axes 2-5 per user amendment.

- [ ] **Step 1 (Axis 1 — Peak-day events):** Enumerate the top 30 single-day flow events ranked by `abs(ccop_usdt_inflow_usd) + abs(ccop_usdt_outflow_usd) + abs(copm_mint_usd) + abs(copm_burn_usd)`. Record date, magnitude, and roundtrip ratio `|inflow − outflow| / max(inflow, outflow)` (ratio < 0.01 is arbitrage-suspect). For each top-30 date, run web-search queries: `"cCOP" OR "Celo" OR "Mento" OR "COPM" OR "Minteo" <date>`; `"Colombia stablecoin" <date>`; `"Celo Colombia DAO" <date>`; `"Mento broker" migration <date>`; `"airdrop" Celo <month-year>`. Classify each peak by event-type: (a) migration/technical upgrade, (b) airdrop/liquidity-mining campaign, (c) governance-call / DAO disbursement, (d) arbitrage opportunity (TRM dislocation / exchange depeg), (e) treasury operation (single-entity mint/burn), (f) unknown. Propose ≥3 candidate dummy variables / instruments with proposed windows (e.g., `D_migration_2026_01_24_to_26`, `D_airdrop_week_YYYY_WW`, `D_governance_thursday`). Each proposal includes (i) event justification, (ii) window justification, (iii) exogeneity argument vs TRM-RV.

- [ ] **Step 2 (Axis 2 — User-intent classification):** Research the dominant USAGE INTENT of cCOP and COPM transactions. Queries: `"cCOP" use case`; `"Celo Colombia" payments OR remittance OR UBI`; `"Minteo COPM" launch purpose`; `"MiniPay" Colombia`; `"impactMarket" Colombia cCOP`; `"El Dorado" Colombia on-ramp cCOP`; forum.celo.org Colombia proposals and grants. Classify the cCOP user population by intent category (non-exclusive, but report dominant category by volume share where derivable):
    - (i) **Remittance** — cross-border transfers to Colombian recipients (what we originally hoped to measure)
    - (ii) **Retail payment / consumption** — in-country purchases, cashback programs (e.g., Celo Colombia Medellín pilot), point-of-sale
    - (iii) **UBI / community-grant claims** — impactMarket-style weekly disbursements
    - (iv) **DAO-contributor payments** — Celo Colombia DAO treasury disbursements to contributors
    - (v) **Arbitrage / market-making** — bot-driven pair rebalancing (consistent with roundtrip pattern)
    - (vi) **Speculation / treasury** — concentrated mint/burn by few holders, no user-facing transaction
    - (vii) **Unknown / unclassified**
  Record a volume-share estimate per category with citation. If any non-remittance category exceeds 50% by volume, flag `INTENT_NON_REMITTANCE_DOMINANT` at top of report (this is a signal to Task 11.K kill criterion k1).

- [ ] **Step 3 (Axis 3 — Data-source correctness verification):** Audit whether Dune query #7366593 captures the TRUE flow that a remittance study would measure. Check:
    - (a) **Coverage:** does `stablecoins_multichain.transfers` with filter `blockchain='celo' AND currency='COP'` capture ALL relevant flows? Specifically, are Mento broker SWAPs (token-swap events at address `0x777a8255…6cad`) separately captured? Are Uniswap V3 cCOP/cUSD pool swaps captured? Are Carbon DeFi limit-order fills captured? Are CeFi exchange on/off-ramp flows captured via MiniPay's El Dorado integration?
    - (b) **Double-counting:** for a single remittance, how many transfer rows does Dune produce? (e.g., Mento mint → user wallet → user swap → receiver wallet = 3 rows; if the query sums all rows, the reported volume is 3x the underlying remittance.)
    - (c) **Denomination:** is `amount_usd` a spot-converted value at tx timestamp, or a book value? Small but real.
    - (d) **TVL sanity-check:** compare panel cumulative volume ($35.8M cCOP + $1.2M COPM = ~$37M) against Mento protocol's published cCOP TVL (~$75k per `CELO_ECOSYSTEM_USERS.md:153` as of June 2025). If panel volume is 500× circulating supply, this is either churn (high velocity = consistent with payments, not remittance) or double-counting (data-source error).
    - (e) **Missing alternative sources:** list ≥3 alternative or complementary data sources that a remittance-focused analysis should consider (e.g., BanRep's SIC database, CeFi API flow from Bitso/Buda Colombia, Bancolombia cross-border-transfer reports, World Bank KNOMAD Colombia bilateral-corridor stats).
  If verification finds systematic coverage gaps or ≥2x double-counting, flag `DATA_SOURCE_SUSPECT` at top of report (signal to Task 11.K kill criterion k2).

- [ ] **Step 4 (Axis 4 — Transaction-size distribution vs remittance benchmark):** Compute from `copm_ccop_daily_flow.csv` the derived per-tx average implied by `daily_volume_usd / daily_unique_senders`. Compare against benchmarks:
    - **Colombian median remittance:** ~$350 USD/tx (World Bank KNOMAD 2024 Colombia corridor stats — verify URL before citing).
    - **Retail payment median:** $10-$50/tx (per `CELO_ECOSYSTEM_USERS.md:127` cited ImpactMarket + Valora use cases).
    - **Arbitrage median:** typically $100k-$1M/tx (the roundtrip pattern in top-5 days).
  Report the distribution percentiles (p10, p25, p50, p75, p90, p99). If median < $30 USD/tx, flag `TX_SIZE_PAYMENT_NOT_REMITTANCE` (signal to Task 11.K kill criterion k4). If median is in the arbitrage range (>$10k/tx), flag `TX_SIZE_ARBITRAGE_DOMINATED`.

- [ ] **Step 5 (Axis 5 — Pivot-candidate identification):** If Axes 2-4 surface evidence that cCOP is NOT remittance but IS payments / consumption / UBI, document this as an explicit pivot candidate. Record: (a) what Y in `project_colombia_yx_matrix.md` would match the actual dominant intent (e.g., Y₃ TRM-RV paired with X = "on-chain retail-payment surprise"), (b) what BanRep or DANE series would serve as validation anchor (e.g., BanRep retail-sales monthly index, DANE household-consumption survey), (c) what sections of the current Rev-4 plan would be preserved vs rewritten under the pivot (answer expected: Phase 2b panel mechanics preserved; Phase 1.5.5 tasks 11.F/G/H re-run under new Y; Rev-1 spec retired entirely, Rev-2 pivot-specific).

- [ ] **Step 6 (report authoring):** Author the `.scratch` report with structure: **Executive Summary** (≤150 words, state overall verdict: REMITTANCE-PLAUSIBLE / INTENT-MIXED / NON-REMITTANCE-DOMINANT / DATA-SOURCE-SUSPECT), **Axis 1 findings** (peak table + classifications + dummies), **Axis 2 findings** (intent categories + volume shares + citations), **Axis 3 findings** (coverage/double-counting audit + alternative sources), **Axis 4 findings** (tx-size distribution + benchmark comparison), **Axis 5 findings** (pivot candidate if applicable), **Flags section** (list any `INTENT_NON_REMITTANCE_DOMINANT` / `DATA_SOURCE_SUSPECT` / `TX_SIZE_PAYMENT_NOT_REMITTANCE` / `TX_SIZE_ARBITRAGE_DOMINATED` triggers), **Task 11.K hand-off** (summary of which kill criteria appear triggerable from the evidence).

**Constraints (Rev 4.1 reinforced):** NO quote >15 words per copyright hygiene; every claim has a URL citation; report total under 1500 words with evidence log as separate file if overflow. No code written in Task 11.F.

**Recovery protocol:** if web-search returns nothing for >50% of top-30 peak dates (Axis 1 sparse), escalate to user before Task 11.G with `RESEARCH_SPARSE_ESCALATE` flag — may need manual Twitter/X archive review, on-chain address-labeling research (Nansen / Arkham), or direct outreach to Celo Colombia DAO. If Axis 3 data-source verification cannot be completed because Dune schema is opaque, escalate for a richer Dune query (Task 11.G.0.1 address-level re-fetch) BEFORE Task 11.G convenes.

**Gate:** Task 11.F completes when the `.scratch` report is authored and committed. Output is consumed by Task 11.K (kill-criterion evaluation) AND Task 11.G (filter brainstorm) AND Task 11.H (pre-committed search space).

### Task 11.K: EXIT plan / kill-criterion specification + post-11.F evaluation (Rev 4.1 insert)

**Rationale.** Phase 1.5.5 cannot run "non-stop filter iteration" without a kill criterion — that would create a specification-search trap forcing a filter even if no remittance signal exists in the data. Task 11.K formally defines the conditions under which we conclude "the on-chain cCOP/COPM aggregate does NOT proxy Colombian household remittance" and EXIT Phase 1.5.5 rather than author a spurious Rev-2 spec. This is not pessimism — it is the same intellectual-honesty discipline that closed the CPI-surprise exercise as an honest FAIL on 2026-04-19. "No remittance signal here" is a valid scientific outcome.

**Subagent:** Model QA (criterion formalization + evaluation against Task 11.F evidence) + Senior Project Manager (disposition and pivot-path authoring if any kill fires).

**Files:**
- Create: `contracts/.scratch/2026-04-24-phase-a0-kill-criterion-spec.md` (the criterion definitions + thresholds)
- Create (conditionally, only if any kill fires): `contracts/.scratch/2026-04-24-phase-a0-exit-disposition.md` (the EXIT memo + pivot recommendation)

- [ ] **Step 1 (criterion definition — pre-committed BEFORE Task 11.F report is read):** Author `2026-04-24-phase-a0-kill-criterion-spec.md` with the following four kill criteria and their evaluation rules. Criteria MUST be committed BEFORE Task 11.F report is opened to prevent post-hoc criterion drift.
    - **k1 (intent):** Task 11.F Axis 2 reports that non-remittance categories (retail-payment + UBI + DAO-contributor + arbitrage + speculation + unknown) account for **>70% of volume**. Rationale: a filter removing non-remittance users would leave <30% residual volume; at the current 84 weekly rows, 30% residual is insufficient for N_eff to support the 13-regressor specification.
    - **k2 (data-source):** Task 11.F Axis 3 flags `DATA_SOURCE_SUSPECT` because (i) Dune query #7366593 systematically misses a material flow path (MiniPay/El Dorado, Carbon DeFi, or CeFi on-ramps), OR (ii) double-counting exceeds 2× the underlying economic flow, OR (iii) panel cumulative volume vs Mento TVL ratio exceeds a plausibility threshold (e.g., >100× circulating supply suggests either extreme churn consistent with payments-velocity or a counting error).
    - **k3 (argmax):** Task 11.H returns `M_max < 0.40` across the FULL pre-committed search space F, OR argmax filter satisfies M but fails component floors (ρ_Pearson < 0.6 OR sign_concordance < 0.6). Rationale: an M of 0.40 would correspond to weak similarity across all four components; no honest reading of "representative of remittance" is consistent with M < 0.40 on the [−1, +1] composite.
    - **k4 (tx-size):** Task 11.F Axis 4 reports median per-tx USD < $30 (consistent with retail payments per `CELO_ECOSYSTEM_USERS.md:127`) AND World Bank KNOMAD Colombia corridor median remittance is >$100 (verified URL in criterion doc). Rationale: the transaction-size distribution is a strong structural fingerprint; if the on-chain distribution is payment-sized not remittance-sized, no address-level filter can fix it because the PER-TX behavior is wrong.
    - **Reliability guard:** the criterion document includes a **git-hash pin** of the exact commit at which the criteria are committed. Any subsequent modification requires a new commit with a different hash, establishing an audit trail. This addresses the "prereg enforcement gap" that the Rev-4 CR review flagged (CR-P3, `contracts/.scratch/2026-04-24-plan-rev4-review-code-reviewer.md`).

- [ ] **Step 2 (evaluate k1, k2, k4 against Task 11.F report):** Open the Task 11.F report. Model QA independently evaluates each of k1, k2, k4 against the evidence. Record each evaluation as PASS (criterion not triggered, Phase 1.5.5 continues) / FIRE (criterion triggered, EXIT) / INCONCLUSIVE (evidence insufficient, escalate to user). If ANY of k1/k2/k4 fires, skip to Step 4; else proceed to Task 11.G.

- [ ] **Step 3 (k3 evaluation hand-off):** k3 is evaluated inside Task 11.H Step 3 after the full-enumeration argmax is computed. Task 11.K Step 3 is a forward reference ensuring that whoever runs Task 11.H knows that `M_max < 0.40` OR component-floor failure at argmax MUST trigger a Task 11.K Step 4 disposition, not an option-(β) "lower the threshold" path. **Option (β) from Rev-4 Task 11.H Step 3 is CLOSED by Rev 4.1 — a lowered M_threshold is NOT a legitimate continuation path.** Only options (α) enlarge F via a new Task 11.G.2 + Task 11.H.2 full re-commitment cycle (with its own Task 11.K re-evaluation), or (γ) EXIT via Task 11.K Step 4, remain open.

- [ ] **Step 4 (EXIT disposition, conditional):** If any of k1/k2/k3/k4 fires, Senior PM authors `2026-04-24-phase-a0-exit-disposition.md` containing:
    - (a) Which kill criteria fired, with evidence pointers
    - (b) Disposition statement: "Phase-A.0 exercise concludes with EXIT_NON_REMITTANCE verdict. The on-chain cCOP/COPM aggregate from Dune query #7366593 does NOT proxy Colombian household remittance for reasons <k1/k2/k3/k4>."
    - (c) **Pivot recommendation** (one of three explicit options, chosen by evidence):
        - **Pivot-α (Payment/Consumption surprise):** if k1 shows retail-payment intent dominates, re-scope exercise as "on-chain retail-payment surprise → TRM-RV" with BanRep retail-sales monthly index (DANE/EMCM series) as validation anchor. Reuse: Task 11.A loader (same CSV), Task 11.B weekly aggregator (same channels), Phase 2b panel mechanics, Phase 3 notebooks, Phase 4 tests. Rewrite: design doc, Rev-1 spec, Task 11.C bridge validation (against retail-sales not remittance), Task 11.F intent-research section (re-interpret intent data).
        - **Pivot-β (Different Y×X cell):** if k3 shows no filter produces remittance representativeness, re-open `project_colombia_yx_matrix.md` and select an alternative cell (options: Y=CPI / X=on-chain payment-burst; Y=TRM-RV / X=Colombian equity microstructure; Y=Colombian-equity-vol / X=on-chain flow). New design doc required; no inheritance from Rev-4 infrastructure beyond the `scripts/` core (cleaning.py pattern, nb2_serialize, gate_aggregate).
        - **Pivot-γ (Abandon Phase-A.0 entirely):** if k2 shows the data source is structurally wrong AND no alternative data source is feasible under current constraints, close Phase-A.0 with NO_VIABLE_PROXY verdict. Memory-file close-out per pattern of `project_fx_vol_cpi_notebook_complete.md`.
    - (d) Memory-file updates: close `project_phase_a0_remittance_execution_state.md` with final disposition; create `project_phase_a0_exit_verdict.md` with the EXIT findings; update `project_colombia_yx_matrix.md` noting the remittance cell is CLOSED with verdict.
    - (e) User notification: explicit ask for approval of the pivot direction before any new work is dispatched.

- [ ] **Step 5 (if no kill fires at Step 2):** Commit the kill-criterion spec at Step 1 with message `spec(abrigo): Rev-4.1 Task 11.K kill-criterion pre-commitment`. Proceed to Task 11.G.

**Non-negotiable anti-fishing guard:** criterion thresholds in Step 1 (70%, 2x, 0.40, $30, $100) are pre-committed in a committed file BEFORE Task 11.F report is opened; they cannot be modified mid-evaluation. If Task 11.F evidence is ambiguous, the honest action is INCONCLUSIVE + user escalation, NOT criterion-threshold revision.

**Gate:** Task 11.K Step 2 completes with one of three outcomes: (i) all of k1/k2/k4 PASS → proceed to Task 11.G; (ii) ≥1 of k1/k2/k4 FIRE → Step 4 EXIT disposition + user approval → Phase-A.0 closes or pivots; (iii) ≥1 INCONCLUSIVE → user escalation before Task 11.G dispatches.

### ⟨RETIRED Rev-5⟩ Tasks 11.G / 11.H / 11.I / 11.J

**Retirement rationale.** These four tasks were the Rev-4.1 power-user filter-iteration + Rev-2 remittance-spec authoring path. Under Phase-A.0 EXIT_NON_REMITTANCE (2026-04-24, commit `2317f72a5`, disposition at `contracts/.scratch/2026-04-24-phase-a0-exit-disposition.md`, kill criteria k1 intent + partial k2 data-source fired) the remittance exercise is CLOSED. These tasks do NOT execute. The Rev-5 inequality-differential pivot tasks **11.L through 11.Q plus 11.M.5** (authored below this retirement block) replace this work-stream with a functional-equation + null-hypothesis authoring path grounded in literature research (11.L) and DuckDB-native data flow (11.M.5). Plan text preserved in place as historical audit trail. Implementers: do NOT reference Tasks 11.G/H/I/J as active work.

---

### Task 11.G: Power-user filter brainstorm (Rev 4 insert) — ⟨RETIRED Rev-5⟩

**Subagent:** foreground invocation of `superpowers:brainstorming` skill by the orchestrator; consults prior-research artifacts + Task 11.F output.

**Files:**
- Create: `contracts/.scratch/2026-04-24-ccop-filter-brainstorm.md`
- Inputs:
  - `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CELO_ECOSYSTEM_USERS.md`
  - `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/identification/2026-04-02-ccop-qa-audit.md`
  - `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` (§3.1 bias direction + sensitivity S3 top-22-power-user exclusion)
  - Task 11.F peak-day event report

- [ ] **Step 1:** Invoke `superpowers:brainstorming` skill. Define the problem: "design a filter family F such that F applied to the raw Dune #7366593 daily-flow series produces a series whose weekly rich-aggregation vector is maximally representative of Colombian household remittance, measured by a symmetric similarity objective M against BanRep quarterly remittance." Do NOT evaluate filters in this task — only enumerate candidate filter families.
- [ ] **Step 2:** Enumerate ≥5 candidate filter families along orthogonal dimensions:
   - (a) **Address-exclusion filters:** top-K by transaction count for K ∈ {10, 22, 50, 100, 200} (inherits prior S3 top-22); top-K by USD volume; known-bot-address blocklist (requires address-labeling research, potentially from Dune query addressable via #6940691 or Nansen labels); known-treasury-address blocklist.
   - (b) **Transaction-size filters:** per-tx amount ∈ [$10, $50] (the documented "remittance-size" range from `CELO_ECOSYSTEM_USERS.md:127`); ∈ [$10, $200]; tail-trim at 95th/99th percentile.
   - (c) **Roundtrip-symmetry filters:** exclude days where `|inflow − outflow| / max(inflow, outflow) < threshold` (captures arbitrage roundtrips); threshold ∈ {0.001, 0.01, 0.05}.
   - (d) **Event-window filters:** exclude dates flagged by Task 11.F dummies (migration, airdrop, treasury events).
   - (e) **Entropy/diversity filters:** require unique-address count per day > threshold (concentration-based gate); Herfindahl-Hirschman concentration cap on daily sender distribution.
   - (f) **Composite filters:** conjunction/disjunction of the above (at minimum, try: "(a) top-22-excl AND (b) [$10,$200] AND (c) roundtrip>0.05").
- [ ] **Step 3:** For each candidate filter family, record: (i) mechanism (why it should isolate household remittance), (ii) expected bias direction (which user types are excluded), (iii) data-availability (computable from Dune query #7366593 alone vs requires address-level re-query; some filters need a richer Dune query with `from_address`/`to_address` per-tx granularity, which is itself a Task 11.G.0.1 sub-task if committed to).
- [ ] **Step 4:** Propose the pre-committed composite **symmetric similarity objective** M for Task 11.H. Baseline candidate:

    `M(x, y) = w_1·ρ_Pearson(x, y) + w_2·ρ_Spearman(x, y) + w_3·sign_concordance(Δx, Δy) + w_4·τ_Kendall(x, y)`

    where x = quarterly-aggregated filtered on-chain series, y = BanRep quarterly series, Δ = quarter-over-quarter first difference, sign_concordance = fraction of quarters where `sign(Δx)·sign(Δy) = +1`, M ∈ [−1, +1]. Weights pre-committed equal (w_i = 0.25) as baseline; Task 11.G may propose alternative weights with justification (e.g., overweight sign_concordance if the primary concern is direction-of-change rather than level-tracking). Document alternative objectives considered (e.g., normalized mutual information, Hoeffding's D, distance correlation) and reason for choosing the Pearson+Spearman+sign+Kendall baseline.
- [ ] **Step 5:** Commit the `.scratch` brainstorm file with message `brainstorm(abrigo): Rev-4 Task 11.G cCOP filter family enumeration + symmetric similarity objective`. No code written in Task 11.G.

**Recovery protocol:** if ≥3 candidate filters require address-level Dune data not present in the current CSV, Task 11.G.0.1 is triggered: re-fetch via a new Dune query with per-tx `from_address`, `to_address`, `amount_usd` granularity. This sub-task has its own mini-review before Task 11.H.

**Gate:** Task 11.G completes when the brainstorm `.scratch` file is committed. Output is consumed by Task 11.H.

### Task 11.H: Non-stop filter iteration under pre-committed symmetric similarity objective (Rev 4 insert) — ⟨RETIRED Rev-5⟩

**Subagent:** Data Engineer (iteration loop implementation + execution) + Model QA (objective pre-commitment verification).

**Files:**
- Create: `contracts/scripts/ccop_filter_search.py` (pure; iterates filters from Task 11.G candidate family)
- Create: `contracts/.scratch/2026-04-24-filter-search-prereg.md` (pre-commitment log)
- Create: `contracts/.scratch/2026-04-24-filter-search-results.md` (argmax results + full search trace)
- Test: `contracts/scripts/tests/remittance/test_ccop_filter_search.py`

- [ ] **Step 1 (PRE-COMMITMENT — Model QA verification required BEFORE any filter is evaluated):** Author `2026-04-24-filter-search-prereg.md` fixing: (a) the composite symmetric similarity objective M with explicit weights (from Task 11.G Step 4), (b) the pre-committed filter search space F = union of Task 11.G candidate families, (c) the BanRep quarterly series decision-hash (including the 104-row 2000Q1–2025Q4 series at the committed fixture path + hash), (d) the tie-breaking rule if multiple filters achieve M_max within floating-point precision (e.g., prefer the filter with fewest parameters; secondary tie-break: higher minimum component score), (e) the threshold M_threshold (baseline proposal: M_threshold = 0.70 on the [−1, +1] composite range, with component floors ρ_Pearson ≥ 0.6 AND sign_concordance ≥ 0.6 to prevent gaming by one inflated component). Dispatch Model QA to independently verify that (i) no filter has been evaluated yet, (ii) the objective is well-defined (bounded, symmetric under argument swap, deterministic), (iii) the search space is finite and each filter is deterministic. Commit the pre-reg with message `prereg(abrigo): Rev-4 Task 11.H filter-search pre-commitment` BEFORE Step 2.
- [ ] **Step 2 (failing test):** Write `test_ccop_filter_search.py` with (i) a fixture filter that intentionally fails (e.g., identity filter on raw data → known low M-score from Task 11.C's ρ=0.7554, sign=2/5 → baseline M); (ii) assertion that `filter_search()` returns a structured result `{filter_id, filter_params, m_score, component_scores, quarterly_series_hash, filter_count_evaluated}`; (iii) assertion that `filter_search()` iterates over the full pre-committed search space F; (iv) **independent-reproduction witness:** a second instance of `scipy.stats.pearsonr` + `scipy.stats.spearmanr` + `scipy.stats.kendalltau` + a manual sign-concordance computation must match the module output to the sixth decimal (mirrors the Task 11.B and Task 10 silent-test-pass hardening pattern).
- [ ] **Step 3 (non-stop iteration policy):** Implement `filter_search()` as a deterministic enumeration over F. No human-in-the-loop mid-iteration adjustment of objective, weights, or search space. Run the full enumeration. If `max_F M(F) ≥ M_threshold` AND component floors are met: report argmax + proceed to Step 4. If `max_F M(F) < M_threshold` OR any component floor fails at the argmax: flag `M_THRESHOLD_UNMET` and escalate to user for scope renegotiation (options: (α) enlarge F with a second-pass Task 11.G.2 → Task 11.H.2 full re-commitment cycle, (β) accept a lower M_threshold with documented rationale recorded in a new Rev-5 history bullet, (γ) abandon the on-chain remittance proxy and re-scope to a different Y×X cell per `project_colombia_yx_matrix.md`). **Rule 13 cycle-cap does NOT apply to Task 11.H filter iteration** — the search is a pre-committed enumeration, not a review loop.
- [ ] **Step 4:** Commit full search trace (every filter's M score + component scores) at `2026-04-24-filter-search-results.md` with message `result(abrigo): Rev-4 Task 11.H filter-search argmax = <filter_id> M=<value>`.
- [ ] **Step 5:** Hand off argmax filter definition to Task 11.I for Rev-2 spec authoring. If `M_THRESHOLD_UNMET`, halt and escalate to user; do not proceed to Task 11.I.

**Anti-fishing guard (Rev 4 non-negotiable):** The Step-1 pre-commitment is load-bearing. If at any point in Step 3–4 the team observes an interim result and wishes to modify M, the weights, or F, that modification is NOT applied to the current search — it is recorded as a candidate for a hypothetical Task 11.H.2 (full re-commitment + re-audit cycle). The current search runs to completion on the frozen Step-1 pre-commitment. This prevents the specification-search failure mode documented in Simonsohn, Simmons & Nelson (2020).

**Gate:** Task 11.H completes when `2026-04-24-filter-search-results.md` is committed AND either (a) M_max ≥ M_threshold with component floors met (proceed to Task 11.I) or (b) `M_THRESHOLD_UNMET` escalation resolved by user.

### Task 11.I: Rev-2 spec authoring via `structural-econometrics` skill re-invocation (Rev 4 insert) — ⟨RETIRED Rev-5⟩

**Subagent:** foreground invocation of `superpowers:structural-econometrics` skill by the orchestrator; consumes Task 11.F + 11.G + 11.H argmax filter output.

**Files:**
- Create: `contracts/docs/superpowers/specs/2026-04-24-remittance-surprise-trm-rv-spec-rev2.md` (NEW file, not a patch)
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` — append a single "SUPERSEDED BY Rev-2 at `<path>`" banner at §0; no other edits to Rev-1.1.1 content

- [ ] **Step 1:** Invoke `structural-econometrics` skill with the 13-input resolution matrix, now with updated inputs: (a) primary X = Task 11.H argmax filter applied to daily on-chain flow, weekly-aggregated per Task 11.B's channel vocabulary (channels possibly pruned to those the argmax filter preserves); (b) auxiliary dummies from Task 11.F peak-day events; (c) BanRep quarterly series demoted to S14 sensitivity row (unchanged from Rev-1.1.1 disposition); (d) updated N_eff: re-derive from the argmax filter's output row count, do NOT re-use Rev-1.1.1's N_eff=78 floor.
- [ ] **Step 2:** **MDES recomputation (non-negotiable — fixes the CR-verified arithmetic error):** compute λ via `scipy.stats.ncf.ppf` root-finding at the actual N_eff and df₂ = N_eff − k where k = total regressor count (including intercept, primary-X channels, controls, Task 11.F dummies). Do NOT use the analytical approximation that produced Rev-1.1.1's λ≈13. Verify with an independent-reproduction witness (a second compute path using `statsmodels.stats.power.FTestPower` or a manual non-central-F root-find).
- [ ] **Step 3:** Author Rev-2 spec as a NEW file (not a patch to Rev-1.1.1). All 13 resolution-matrix rows re-derived in §12. §4.1 defines the primary X using the argmax filter (document the filter lineage: "argmax of Task 11.H pre-committed search; filter-id, params, M-score"). §4.4 specifies the gate test (joint F-test if primary X is multi-channel, or t-test if argmax filter collapses the 6-channel vector to a scalar). §4.5 specifies the corrected MDES.
- [ ] **Step 4:** §0 of Rev-2 spec states explicitly: "Rev-2 supersedes Rev-1, Rev-1.1, and Rev-1.1.1. Do not read pre-Rev-2 sections for methodology guidance." §13 references include Task 11.F–11.H commits and the filter-search pre-reg.
- [ ] **Step 5:** Commit Rev-2 spec with message `spec(remittance): Rev-2 — argmax-filtered primary X + structural-econometrics re-invocation (Rev-4 Task 11.I)`. Simultaneously commit the Rev-1 banner append.

**Recovery protocol:** if `structural-econometrics` skill output conflicts with the Task 11.H argmax (e.g., skill recommends a filter not in F), halt and escalate to user — do not silently override either the skill or the pre-commitment.

**Gate:** Task 11.I completes when Rev-2 spec is committed AND the Rev-1 supersession banner is committed. Rev-1.1.1 is officially superseded at this point; all downstream tasks reference Rev-2.

### Task 11.J: Rev-2 spec three-way review (Rev 4 insert) — ⟨RETIRED Rev-5⟩

**Subagent:** three parallel dispatches — Code Reviewer + Reality Checker + Technical Writer (same trio pattern as Task 11.E).

**Files:**
- Create: `contracts/.scratch/2026-04-2X-remittance-spec-rev2-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-2X-remittance-spec-rev2-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-2X-remittance-spec-rev2-review-technical-writer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against Rev-2 spec + Task 11.H filter-search pre-reg + Task 11.H results file as first-class inputs. CR audits whether the argmax filter was honestly computed from the pre-committed search space (no post-hoc enlargement) and whether the 13-row resolution matrix is internally consistent. RC audits numerical claims, citation grounding, MDES recomputation correctness (independent scipy reproduction). TW audits §0 banner clarity, pedagogical coherence of the new primary-X definition, supersedes typography, and absence of orphaned Rev-1.1.1 language.
- [ ] **Step 2:** TW consolidation; apply BLOCKs + FLAGs; Rule 13 cycle-cap APPLIES here (3 full round-trips max, 3 per-reviewer re-dispatches max; one cycle = one parallel 3-reviewer round + TW consolidation).
- [ ] **Step 3:** Commit TW-consolidated spec with message `spec(remittance): Rev-2 fix-pass, all 3-way reviewer findings addressed (Rev-4 Task 11.J)`.

**Gate:** Phase 2b Task 12 implementation step is blocked until Task 11.J returns unanimous PASS / PASS-WITH-FIXES verdict and TW consolidation is committed. Phase 2b Task 12 failing-test authoring may begin in parallel with Phase 1.5.5 per Rev-3.1 Phase-1.5 parallelism rationale.

---

### Task 11.L: Literature-landscape research guardrail (Rev 5 insert)

**Rationale.** Before the `structural-econometrics` skill formulates a functional equation for the inequality-differential exercise, we need to know whether prior research has already measured, modelled, or instrumented similar constructs. The user directive (2026-04-24): "once we look up a functional equation with a null hypothesis, we need to look if there is existing research pointing [in that] direction or that can give us insights... that needs to be first put on the plan by an agent that guards." Task 11.L is that guardrail — its output is MANDATORY input to Task 11.O.

**Subagent:** background general-purpose subagent with arxiv MCP (`mcp__arxiv__*`, prioritized per `~/.claude/CLAUDE.md` global rule) + WebSearch + WebFetch.

**Files:**
- Create: `contracts/.scratch/2026-04-24-inequality-differential-literature-review.md`
- Inputs: `project_abrigo_inequality_hedge_thesis.md`; `contracts/.scratch/2026-04-24-phase-a0-exit-disposition.md`; `contracts/.scratch/2026-04-24-ccop-peak-day-event-research.md`

- [ ] **Step 1 (arxiv landscape scan):** search arxiv corpus on: *labor-vs-capital return differential*; *Piketty r > g empirics*; *Atkinson-Piketty-Saez top-income shares*; *Solt SWIID standardized inequality*; *Campbell-Cochrane consumption-based asset pricing*; *Lettau-Ludvigson cay consumption-wealth ratio*; *Colombian real carry return Latam macro*; *parametric insurance income smoothing*; *catastrophe bond structure inequality*; *DeFi inequality / labor-return instruments*; *on-chain dollarization proxies Latam*.
- [ ] **Step 2 (per-paper deep reads):** for top-10 most relevant papers — abstract, key finding, identification strategy, theoretical sign + magnitude, relevance-to-our-exercise paragraph, URL + full citation.
- [ ] **Step 3 (functional-equation candidates):** extract specific equation forms proposed by prior work that could serve as our primary spec. Each candidate includes: canonical form; authors + paper; assumed data; estimation method; pre-registered expected sign of key coefficient.
- [ ] **Step 4 (identification strategies):** enumerate instrument/natural-experiment/identification-assumption patterns used by prior papers on similar constructs. These inform structural-econometrics skill Row-7 (identification source) in Task 11.O.
- [ ] **Step 5 (novelty claim):** honest statement of what's new in our approach vs existing work — what gap does this exercise fill, and what existing result does it extend?
- [ ] **Step 6:** Report ≤2000 words with structure: *Executive Summary*, *Literature Landscape*, *Top-10 Paper Deep Reads*, *Functional-Equation Candidates*, *Identification Strategies*, *Novelty Claim*, *Recommendations for Task 11.O*. Commit with message `research(abrigo): Rev-5 Task 11.L literature-landscape for inequality-differential`.

**Constraints:** arxiv MCP MUST be primary tool (global rule); ≤15-word quotes per copyright hygiene; URL + title for every citation; no code. If arxiv coverage is sparse on a specific topic, flag `LIT_SPARSE_<topic>` and expand WebSearch on that axis only.

**Gate:** report committed. Mandatory input to Task 11.O.

### Task 11.M: COPM per-transaction profile (Rev 5 insert; in flight)

**Subagent:** background agent `aa0bf238c4ca1b501` (launched 2026-04-24 per session log).

**Files:** per agent brief:
- `contracts/data/copm_per_tx/copm_mints.csv` ✓ (landed 2026-04-24)
- `contracts/data/copm_per_tx/copm_burns.csv` ✓ (landed 2026-04-24)
- `contracts/data/copm_per_tx/copm_transfers.csv` (in flight)
- `contracts/data/copm_per_tx/copm_freeze_thaw.csv` (in flight)
- `contracts/data/copm_per_tx/README.md` (provenance + query IDs)
- `contracts/.scratch/2026-04-24-copm-per-tx-profile.md` (structural characterization)

- [ ] **Step 1:** complete Dune per-tx pull from `copm_token_v_1_celo.*` decoded tables (mints / burns / transfers / freeze events).
- [ ] **Step 2:** profile: mint receiver concentration (HHI), B2B→B2C diffusion, holder concentration, freeze activity, time patterns, usage classification with volume-share breakdown.
- [ ] **Step 3:** hand off to Task 11.M.5 (DuckDB ingestion) and Task 11.N (X_d filter design).

**Liveness gate (Rev 5.1 — addresses RC BLOCKER):** if agent silent >2h (no file writes to `contracts/data/copm_per_tx/`), orchestrator MUST dispatch fresh COPM agent with resume instructions (continue from Dune query IDs recorded in partial `README.md`; avoid re-pulling completed CSVs). Downstream Tasks 11.M.5 and 11.N MUST NOT begin execution until all 4 CSVs + profile `.scratch` are present; check mtimes + row counts before dispatch. If 11.M restarts 3× without convergence, escalate to user (the Dune per-tx table may be too large for 10-credit budget).

**Gate:** all 4 CSVs + provenance README + profile `.scratch` committed; file presence + row-count liveness check passed.

### Task 11.M.5: DuckDB migration — ingest on-chain CSVs into structural_econ.duckdb (Rev 5 insert)

**Rationale.** User directive (2026-04-24): "if we're using the cCOP or COPM data, we need to include in the plan the migration from the current way it's laid out to the DuckDB structure we have for all the other data." Phase-A.0 wrote on-chain data as plain CSVs (`contracts/data/copm_ccop_daily_flow.csv`, `contracts/data/copm_per_tx/*.csv`) outside the `contracts/data/structural_econ.duckdb` store used by the Rev-4 CPI pipeline (`contracts/scripts/econ_schema.py`, `econ_pipeline.py`, `econ_query_api.py`, `econ_panels.py`, `cleaning.py`). This is non-negotiable: downstream Tasks 11.N (X_d filter) and 11.Q (panel assembly) MUST consume data via the same DuckDB-backed query API to preserve Rev-4 decision-hash integrity and the `functional-python` frozen-dataclass pattern.

**Subagent:** Data Engineer.

**Files:**
- Modify: `contracts/scripts/econ_schema.py` (additive — declare tables `onchain_daily_flow`, `onchain_copm_mints`, `onchain_copm_burns`, `onchain_copm_transfers`, `onchain_copm_freeze_thaw` with types matching CSV schemas; no existing-table mutation)
- Modify: `contracts/scripts/econ_pipeline.py` (additive — CSV→DuckDB ingestion path, idempotent, with schema validation + dtype coercion)
- Modify: `contracts/scripts/econ_query_api.py` (additive — expose `load_onchain_daily_flow()`, `load_onchain_copm_mints()`, `load_onchain_copm_burns()`, `load_onchain_copm_transfers()`, `load_onchain_copm_freeze_thaw()` as pure functions returning frozen-dataclass result types per `functional-python` skill)
- Create: `contracts/scripts/tests/test_onchain_duckdb_migration.py`

- [ ] **Step 1 (failing test):** assert (a) Task 11.A's 585-row `copm_ccop_daily_flow.csv` loads losslessly into `onchain_daily_flow` (row count + per-column checksum); (b) each per-tx CSV from 11.M loads losslessly (row count + column-hash); (c) Rev-4 `decision_hash` on the existing CPI panel is preserved byte-exact post-migration (additive-only constraint — no mutation of existing tables or columns); (d) `load_onchain_*` query-API functions return canonical frozen-dataclass types per `functional-python` skill.
- [ ] **Step 2 (Rev 5.1 type correction — addresses CR finding):** declare table schemas in `econ_schema.py`. Dtype mapping: addresses → `VARCHAR(42)` (40-hex + "0x" prefix) or `BLOB(20)` to match Rev-4 panel convention; timestamps → `TIMESTAMP` (UTC); amounts → `HUGEINT` or `DECIMAL(38, 0)` per DuckDB support for large integers (DuckDB has NO native `uint256` — Rev-5's initial mention was incorrect per CR review; the Dune `uint256` wire type must be cast to HUGEINT/DECIMAL before ingestion, with overflow-guard assertion in the ingestion path since max HUGEINT ≈ 1.7e38 accommodates typical COPM/cCOP amounts below the uint256 max but a boundary check is cheap insurance).
- [ ] **Step 3:** implement ingestion in `econ_pipeline.py` (idempotent — re-running on unchanged CSVs is a no-op).
- [ ] **Step 4:** expose query-API functions in `econ_query_api.py` returning typed frozen dataclasses.
- [ ] **Step 5:** run migration; confirm tests pass; commit with message `feat(abrigo): Rev-5 Task 11.M.5 — DuckDB migration for on-chain Abrigo data`.

**Constraints (`feedback_scripts_only_scope.md`, non-negotiable):** touches ONLY `contracts/scripts/` + `contracts/scripts/tests/` + the DuckDB binary under `contracts/data/`; NEVER modifies Solidity, `foundry.toml`, `contracts/src/`, or `contracts/test/*.sol`.

**Gate:** migration committed; downstream Tasks 11.N and 11.Q MUST read via `econ_query_api.py`, NOT from raw CSVs. CSVs preserved as provenance fixtures with a note in their README pointing to the DuckDB tables as authoritative.

### Task 11.M.6: FRED + Banrep rate panel extension for Y_asset_leg feasibility (Rev 5.1 insert — addresses RC BLOCKER)

**Rationale.** RC plan review (`contracts/.scratch/2026-04-24-plan-rev5-review-reality-checker.md`) surfaced that Rev-5's Y_asset_leg formula `Y_asset_leg = (Banrep_rate − Fed_funds)/52 + ΔTRM/TRM` is NOT computable from the Rev-4 panel as-is: (i) Fed funds (FRED series `DFF`) is rejected by the `fred_daily` CHECK constraint at `contracts/scripts/econ_schema.py:73` which only allows `VIXCLS`, `DCOILWTICO`, `DCOILBRENTEU`; (ii) Banrep IBR rate LEVEL is not materialized as a panel column — `econ_panels.py:143-148` exposes only the Banrep surprise (event-study residual), not the rate level itself. Task 11.M.6 closes both gaps additively before Task 11.O consumes Y_asset_leg.

**Subagent:** Data Engineer.

**Files:**
- Modify: `contracts/scripts/econ_schema.py` — EXTEND the `fred_daily` CHECK constraint to additionally allow `DFF` (Fed funds effective rate daily); DO NOT modify other constraints or tables
- Modify: `contracts/scripts/econ_pipeline.py` — ADD FRED-API fetch path for `DFF` series; ADD Banrep IBR-level series fetch (BanRep open-data API; weekly-Friday-anchored); both are additive ingestion steps that write to existing tables or new `banrep_ibr_daily` table if needed
- Modify: `contracts/scripts/econ_panels.py` — extend weekly panel view with columns `fed_funds_weekly`, `banrep_ibr_weekly`; preserve existing columns byte-exact
- Create: `contracts/scripts/tests/test_rate_panel_extension.py`

- [ ] **Step 1 (failing test):** assert (a) `fred_daily` accepts `DFF` rows after extension; (b) existing `VIXCLS`/`DCOILWTICO`/`DCOILBRENTEU` rows unchanged byte-exact; (c) Rev-4 `decision_hash` = `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23` preserved after extension (pure additive); (d) `load_fed_funds_weekly()` returns frozen-dataclass with correct weekly series 2008+; (e) `load_banrep_ibr_weekly()` likewise.
- [ ] **Step 2:** extend CHECK constraint in `econ_schema.py` to additionally allow `DFF`.
- [ ] **Step 3:** fetch DFF via FRED API (`fredapi` or requests against `api.stlouisfed.org/fred/series/observations?series_id=DFF`); ingest to `fred_daily` with series_id='DFF'.
- [ ] **Step 4:** fetch Banrep IBR via BanRep open-data API (verify endpoint URL in implementation; fallback to `suameca.banrep.gov.co` if direct API rate-limited).
- [ ] **Step 5:** extend panel view in `econ_panels.py` with weekly-Friday-anchored columns; expose via `econ_query_api.py` as `load_fed_funds_weekly()` + `load_banrep_ibr_weekly()`.
- [ ] **Step 6:** run tests; confirm pass; commit with message `feat(abrigo): Rev-5.1 Task 11.M.6 — FRED DFF + Banrep IBR panel extension for Y_asset_leg`.

**Constraints:** additive-only; same scripts-only scope rule as 11.M.5.

**Gate:** panel extension committed; Task 11.O can now compute Y_asset_leg from the extended panel.

### Task 11.N: X_d filter design + implementation (Rev 5 insert)

**Subagent:** Data Engineer, consuming Task 11.M profile + Task 11.L literature insights; reads from DuckDB via `load_onchain_copm_transfers()` (NOT raw CSV).

**Files:**
- Create: `contracts/scripts/copm_xd_filter.py` (pure; functional-python; frozen-dataclass result)
- Create: `contracts/scripts/tests/inequality/test_copm_xd_filter.py`
- Create: `contracts/.scratch/2026-04-24-xd-filter-design-memo.md`

- [ ] **Step 1 (pre-commitment):** design memo pre-commits (a) B2B vs B2C classification rule from 11.M profile + `copm_token_v_1_celo.tokenv1_evt_rolegranted` role-graph; (b) filter transformation (e.g., `X_d_t = weekly net USD flow from B2B-receiver set to B2C-downstream set, Friday-anchored America/Bogota`); (c) golden-fixture values for one reproducible weekly slice. Model QA verifies no data peek before commitment (mirrors Task 11.H Step 1 pattern from Rev-4.1, retired but applicable here).
- [ ] **Step 2 (failing test):** golden fixture + independent-reproduction witness (mirrors Task 11.B pattern per `feedback_implementation_review_agents.md` silent-test-pass hardening).
- [ ] **Step 3:** implement `compute_weekly_xd(per_tx_frozen_dc, friday_anchor_tz)` as pure function returning a frozen-dataclass weekly panel.
- [ ] **Step 4:** run test; confirm pass.
- [ ] **Step 5:** compute X_d over full 2024-09-17 → 2026-04-24 range; persist to DuckDB table `onchain_xd_weekly` via `econ_pipeline.py` additive path; commit.

**Gate:** X_d weekly series in DuckDB with test + independent-witness passing. Output consumed by Task 11.O (spec authoring) and Task 11.Q (panel assembly).

### Task 11.N.1: COPM raw-transfers backfill via Celo RPC + Alchemy fallback (Rev 5.2 insert)

**Rationale.** Task 11.N (commit `d688bb973`) fired `X_D_INSUFFICIENT_DATA` because the Dune MCP pagination limit prevented pulling the full 110,069-row raw `copm_transfers` dataset (query `7369028`); DuckDB currently holds only a 10-row sample. The committed X_d is a supply-channel surrogate (`net_primary_issuance_usd`). Task 11.N.1 backfills the full raw-transfers dataset via a free on-chain-native data path so Task 11.N can regenerate X_d under its originally-pitched distribution-channel (B2B→B2C net flow) meaning per `project_abrigo_inequality_hedge_thesis.md`.

**Subagent:** Data Engineer.

**Primary data path (on-chain-native, no API key, no third-party indexer):**
- Celo public RPC at `https://forno.celo.org` (official cLabs endpoint; fallback to `https://rpc.ankr.com/celo` on failure)
- `eth_getLogs` for COPM Transfer events: `topics[0] = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` (the `Transfer(address,address,uint256)` event signature), `address = 0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`
- Block-range pagination: 10,000-block windows from COPM contract deployment (first transfer timestamp 2024-09-17 per `dune_onchain_flow_fetcher.py` docstring) to latest
- **Python `requests`-only JSON-RPC** (Rev 5.2.1 — `web3.py` NOT installed in `contracts/.venv/` per RC-B2 check; `requests` + `eth-hash`/`eth-typing`/`eth-utils` ARE present and sufficient for eth_getLogs hex-decoding)
- **Per-10k-block checkpoint** (Rev 5.2.1 PM-P2): after each completed block-range window, write `contracts/.scratch/copm_transfers_backfill_progress.json` with `{last_completed_end_block: int, total_rows_so_far: int, data_source: "forno"|"ankr"|"alchemy"}`; on restart, resume from `last_completed_end_block + 1`

**Secondary fallback (only if primary fails trigger criteria):**
- Alchemy `getAssetTransfers` at `https://celo-mainnet.g.alchemy.com/v2/<ALCHEMY_API_KEY>`
- Free tier 300M CU/month; 1000 transfers per call → ~110 paginated calls
- API key read from env var `ALCHEMY_API_KEY` (if missing, halt + escalate rather than silently fail)

**Fallback trigger criteria (document which triggered + why in provenance README):**
1. Public RPC returns < 110,069 × 0.99 rows (>1% under Dune-reported count)
2. Any of the fallback RPC endpoints times out >3 consecutive block ranges
3. RPC rejects `eth_getLogs` with `query returned more than N results` for a 10k-block window AND binary-search narrowing below 1k blocks still fails
4. Total RPC wall-time exceeds 30 minutes

**Files:**
- Modify: `contracts/scripts/econ_pipeline.py` — ADD `fetch_copm_transfers_rpc(start_block: int, end_block: int, rpc_url: str) -> pd.DataFrame` (pure; paginated; exponential-backoff retries); ADD `fetch_copm_transfers_alchemy(api_key: str) -> pd.DataFrame` (pure; secondary path); ADD orchestration `backfill_copm_transfers() -> pd.DataFrame` that tries primary then falls back
- Modify: `contracts/data/copm_per_tx/copm_transfers.csv` — REPLACE 10-row sample with full ~110k-row backfill; preserve Task-11.M column schema byte-exact (same column names + dtypes as Dune export)
- Modify: `contracts/data/copm_per_tx/README.md` — ADD provenance block: data source used (primary RPC vs fallback Alchemy), block range covered, timestamp of pull, row count vs Dune-reported 110,069, fallback-trigger log if applicable
- Modify: `contracts/scripts/econ_schema.py` — (Rev 5.2.1 CR-B2/RC-B1 BLOCKER resolution, pre-committed) (a) ADD a NEW table `onchain_copm_transfers` for the full dataset; do NOT modify `onchain_copm_transfers_sample` — it remains as historical-sample pointer for audit. (b) MIGRATE `onchain_xd_weekly` table DDL: relax the singleton CHECK at lines 367-374 to `CHECK (proxy_kind IN ('net_primary_issuance_usd', 'b2b_to_b2c_net_flow_usd'))`; change PK from single-column `week_start` to composite `(week_start, proxy_kind)` so both channels coexist row-wise. This is a schema-level change that breaks additive-byte-exact for `onchain_xd_weekly` data, BUT the Rev-4 `decision_hash` covers only `LOCKED_DECISIONS` (not arbitrary DuckDB tables), so additive-ness with respect to the Rev-4 discipline is preserved. Pre-register this migration in Step 0 BEFORE the RPC code.
- Modify: `contracts/scripts/copm_xd_filter.py` — (Rev 5.2.1 RC-new) line 71 hard-codes the `proxy_kind` constant as `"net_primary_issuance_usd"`; parametrize to accept a `proxy_kind: Literal["net_primary_issuance_usd", "b2b_to_b2c_net_flow_usd"]` argument in `compute_weekly_xd()` so the function produces BOTH variants under the same filter contract. The supply-channel path continues to compute from mint/burn; the distribution-channel path computes from full transfers (available after this task).
- Modify: `contracts/scripts/econ_query_api.py` — ADD `load_onchain_copm_transfers()` returning frozen-dataclass for the FULL dataset; update `load_onchain_xd_weekly()` to accept an optional `proxy_kind: str | None = None` argument (None returns both; explicit value filters).
- Create: `contracts/.env.example` — (Rev 5.2.1 CR hygiene) file with `ALCHEMY_API_KEY=` placeholder + inline comment explaining it is OPTIONAL (only consulted if primary RPC path fails); repo `.gitignore` already ignores `.env` — verify before committing `.env.example`.
- Modify: `contracts/scripts/tests/test_onchain_duckdb_migration.py` — (a) update expected row count for `onchain_copm_transfers` to 110,069 ± 1% tolerance; (b) add assertion that the relaxed CHECK constraint on `onchain_xd_weekly` accepts both `proxy_kind` values; (c) add assertion that the composite PK allows both channels to coexist for the same `week_start`; (d) assert Rev-4 `decision_hash` unchanged.

**Steps (Rev 5.2.1 — Step 0 prepended per CR-B1/RC-B1):**
- [ ] **Step 0 (SCHEMA MIGRATION — pre-committed BEFORE any RPC code; Rev 5.2.1 BLOCKER resolution):** Author a schema-migration module that (a) relaxes `onchain_xd_weekly` CHECK to `IN ('net_primary_issuance_usd', 'b2b_to_b2c_net_flow_usd')` and migrates PK to composite `(week_start, proxy_kind)`; (b) creates new `onchain_copm_transfers` table (distinct from `onchain_copm_transfers_sample`); (c) parametrizes `copm_xd_filter.py:71` to accept `proxy_kind` argument. Write a failing test FIRST asserting the migrated schema accepts both `proxy_kind` values and Rev-4 `decision_hash` is preserved. Implement; run; confirm green. Commit Step 0 separately with message `feat(abrigo): Rev-5.2.1 Task 11.N.1 Step 0 — onchain_xd_weekly schema migration (composite PK + relaxed CHECK)`. This commit is atomically rollback-able; downstream Steps 1-6 are blocked on Step 0 green.
- [ ] **Step 1 (failing test extension):** extend `test_onchain_duckdb_migration.py` with assertions that (a) full `copm_transfers.csv` has 110,069 ± 1% rows against Dune-reported total; (b) `onchain_copm_transfers` table round-trips byte-exactly; (c) `load_onchain_copm_transfers()` returns a frozen-dataclass with the full dataset (not a sample); (d) Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` preserved byte-exact (additive-only guarantee); (e) Task 11.N.1 RPC-fetcher + Alchemy-fallback functions are deterministic on a fixed block range (mock-free: hit real RPC with a narrow 10k-block range as a smoke test).
- [ ] **Step 2 (RPC primary):** implement `fetch_copm_transfers_rpc()` using `web3.py` or equivalent. Paginate 10k-block windows. Capture each block range's log count; if total <110,069 × 0.99 after full pass, trigger fallback.
- [ ] **Step 3 (Alchemy fallback):** implement `fetch_copm_transfers_alchemy()` consuming `ALCHEMY_API_KEY` env var. Auto-invoked by `backfill_copm_transfers()` on any fallback trigger.
- [ ] **Step 4 (run + verify):** run extended test; all assertions pass; verify Rev-4 decision-hash preserved.
- [ ] **Step 5 (re-run Task 11.N):** re-compute X_d via `compute_weekly_xd()` on full data; persist to `onchain_xd_weekly` with `proxy_kind = "b2b_to_b2c_net_flow_usd"`. Keep the existing supply-channel rows (`proxy_kind = "net_primary_issuance_usd"`) — do NOT delete them; both serve Task 11.O.
- [ ] **Step 6:** commit with message `feat(abrigo): Rev-5.2 Task 11.N.1 — COPM raw-transfers backfill (Celo RPC + Alchemy fallback)`.

**Non-negotiable rules (same stack as 11.M.5, 11.M.6, 11.N):**
- **STRICT TDD** (`feedback_strict_tdd.md`): failing-test extension first
- **Scripts-only scope** (`feedback_scripts_only_scope.md`): touch only `contracts/scripts/` + `contracts/scripts/tests/` + `contracts/data/` (CSVs + DuckDB binary)
- **functional-python**: frozen dataclasses, free pure functions, full typing, no inheritance
- **Additive-only**: Rev-4 `decision_hash` preserved byte-exact; Task 11.M.5 + 11.M.6 + 11.N migrations unchanged; existing DuckDB tables mutate only via the additive `onchain_copm_transfers` row replacement
- **Real data over mocks** (`feedback_real_data_over_mocks.md`): hit the real RPC; mocks only for HTTP-error failure modes we can't reproduce
- **Activate venv before Python**: `source contracts/.venv/bin/activate`

**Recovery protocols:**
- If BOTH primary RPC and Alchemy fallback fail (e.g., API key missing + public RPCs all rate-limited), HALT + escalate to user with `X_D_STILL_INSUFFICIENT`. Do NOT silently regress to the 10-row sample or invent a third surrogate.
- If row count drifts >1% from Dune query 7369028 (e.g., chain reorg is implausible at this scale), HALT + document discrepancy in the provenance README — user decides whether to accept, re-pull, or treat as a pagination bug.
- If the test-time smoke RPC call is rate-limited (symptom: 429 or timeout on a single small range), retry via Ankr fallback; if Ankr also fails, document `RPC_RATE_LIMITED_AT_TEST_TIME` in the test skip-reason + escalate.

**Gate:** full `copm_transfers.csv` committed with provenance README + Task 11.N re-run committed with distribution-channel X_d + all Task 11.M.5 tests remain green + Rev-4 decision-hash unchanged. Task 11.O (spec authoring) can then consume both X_d variants as primary + secondary in the resolution matrix.

**DAG clarification (Rev 5.2.1 PM-P1):** Task 11.N.1 is NOT a pre-requisite to Task 11.O. Task 11.O MAY begin authoring the Rev-2 spec using the supply-channel surrogate X_d (`net_primary_issuance_usd`) as the primary — this unblocks the spec-authoring timeline. When Task 11.N.1 completes, Task 11.O Step 4 (targeted lit re-check + spec refinement) folds in the distribution-channel X_d as a SECONDARY primary (co-equal in the 13-input resolution matrix), and the Rev-2 spec is updated via an amendment-rider commit BEFORE Task 11.P three-way review dispatches. This permits 11.O and 11.N.1 to run in parallel without violating pre-commitment discipline because both X_d variants are pre-registered in the Rev-5.2.1 spec-authoring inputs.

### Task 11.N.1b: Resume missing-blocks backfill via alternative paths (Rev 5.3 insert)

**Rationale.** Task 11.N.1 landed at commit `f1f114cd1` with `X_D_STILL_INSUFFICIENT` partial-coverage: 52,068 of the Dune-reported 110,069 rows (47.3%) were fetched over blocks `27,786,128 → 30,485,761` (2024-09-17 → 2025-02-09) before the public Celo RPC path encountered intermittent failures during the 11.N.1 wall-clock window. The checkpoint file at `contracts/.scratch/copm_transfers_backfill_progress.json` records `{last_completed_end_block: 30486127, total_rows_so_far: 52068, data_source: "forno"}`. **RC empirical re-verification 2026-04-24:** `forno.celo.org` and `https://rpc.ankr.com/celo` are BOTH alive today and respond HTTP 200 to fresh `eth_getLogs` probes (forno tolerates 5k-block windows; Ankr enforces a smaller 1k-block window cap). The "503 stickiness" rationale anchoring the prior fallback ladder ordering is therefore retired; public Celo RPC is the FIRST option to retry, and the alternative paths become genuine fallbacks triggered only on actual failure. Task 11.N.1b resumes from block `30,486,128` to chain-tip (per RC: ~65,173,365; ≈ 34.7M blocks; 2025-02-09 → today) under a six-path ladder ordered by expected reliability and zero-API-key preference. First working path wins. Resumes additively against the already-landed 52,068 rows in `onchain_copm_transfers` and the `copm_transfers_full.csv` artifact — does NOT re-fetch covered ranges (would breach additive-only discipline and waste cycles). Down-stream Task 11.N's `compute_weekly_xd()` is re-run over the now-complete panel to produce a distribution-channel X_d covering the full ~84-Friday weekly cadence.

**Subagent:** Data Engineer.

**Primary alternative-data ladder (six paths; first-working wins; provenance README must record which path fired and why predecessors did not):**
1. **Celo public RPC retry (forno + Ankr)** — re-verified live by RC empirical probe today (2026-04-24): both endpoints respond HTTP 200 with valid JSON to `eth_blockNumber` and `eth_getLogs`. Window sizing: forno tolerates up to 5k blocks per `eth_getLogs`; Ankr requires reduction to 1k blocks per request (response: "Block range is too large"). Implementer adapts the request-window per endpoint. Single-stream concurrency with exponential back-off cap at 30s. This is the FIRST-try path, not a last-resort.
2. **Paid Alchemy Celo tier** — same `getAssetTransfers` endpoint as Task 11.N.1's tertiary path but on a paid plan; HALT-and-escalate-to-user if `ALCHEMY_API_KEY_PAID` env var is unset (path-2 only consulted if user has explicitly provisioned this credential; do NOT silently fall through to path 3 — surface the missing-credential to the user as an actionable choice). Note: dollar-cost claim NOT pinned in the plan (per RC: lowest paid tier cost not surfaced from Alchemy pricing page reliably).
3. **Covalent / GoldRush API** at `https://api.covalenthq.com/v1/celo-mainnet/address/0xc92e8fc2947e32f2b574cca9f2f12097a71d5606/transfers_v2/` — paginated by block range. **Trial-only credit availability per RC:** GoldRush pricing page documents 25,000 credits / 14-day trial, NOT a renewable monthly free tier. Step 3 includes a trial-validity check before production pull. API key read from `COVALENT_API_KEY` env var with HALT-on-missing.
4. **Flipside Crypto SQL via REST** — query CELO Transfer events with the same address + topic filter as the Dune query. **Verify-existence-first per RC:** Celo is NOT explicitly listed on Flipside's chain-coverage pricing page; Step 4 begins with a `describe-table` probe to confirm `celo.core.fact_event_logs` exists and has the expected schema before any production query. API key from `FLIPSIDE_API_KEY` env var.
5. **Dune REST API (direct, NOT MCP)** — single execution of query `7369028` via `POST https://api.dune.com/api/v1/query/7369028/execute`, then `GET https://api.dune.com/api/v1/execution/{execution_id}/results/csv` for full CSV download (sidesteps the MCP pagination limit that caused Task 11.N's `X_D_INSUFFICIENT_DATA`). Per RC: the `/results/csv` endpoint URL must be confirmed via `mcp__dune__searchDocs` or direct API spec at Step-5 entry — current Dune API doc fetched does not surface it explicitly. API key from `DUNE_API_KEY` env var.
6. **User manual Dune web-UI CSV export** — interactive step: orchestrator pings user with link `https://dune.com/queries/7369028`, user clicks "Download CSV", places file at `contracts/data/copm_per_tx/copm_transfers_dune_manual.csv`; orchestrator detects file presence and continues. Zero-code path; tolerates total credential exhaustion across paths 1-5.

**Fallback trigger criteria (per-path; document trigger + provenance in README):**
- A path is considered FAILED if (a) credential unavailable when required, (b) >3 consecutive request failures (HTTP 4xx/5xx) on a single block range that cannot be narrowed, (c) total wall-time on the path exceeds 30 minutes without progress, (d) row-count drift exceeds 1% from the Dune-reported 110,069 ± 0.5% target after a full pass.
- A path is considered SUCCEEDED when the cumulative `onchain_copm_transfers` row count reaches **110,069 ± 0.5%** (tightened from Task 11.N.1's ±1% — we now have a 52,068-row baseline against which to verify the remaining 58,001 ± 580).
- Per-path success criterion (PM-N3): "full coverage of the post-checkpoint range to chain-tip" — partial coverage on a path is a path-FAILURE that drops back to the prior checkpoint, not a hybrid-stitch with the next path. The orchestrator does NOT mix-and-match partial pulls across paths; each path either fully covers post-checkpoint → tip or yields and the next path restarts from the post-52k checkpoint.
- If ALL six paths fail, HALT + escalate to user with `X_D_STILL_INSUFFICIENT_PHASE_2`. Do NOT silently regress to the partial 52,068-row dataset for downstream X_d computation.

**Files:**
- Modify: `contracts/scripts/econ_pipeline.py` — ADD `fetch_copm_transfers_celo_rpc_retry(start_block: int, endpoint: str, window_blocks: int) -> pd.DataFrame` (path-1; window_blocks defaults to 5000 for forno, 1000 for Ankr); ADD `fetch_copm_transfers_alchemy_paid(api_key: str, start_block: int) -> pd.DataFrame`; ADD `fetch_copm_transfers_covalent(api_key: str, start_block: int) -> pd.DataFrame`; ADD `fetch_copm_transfers_flipside(api_key: str, start_block: int) -> pd.DataFrame`; ADD `fetch_copm_transfers_dune_rest(api_key: str, query_id: int = 7369028) -> pd.DataFrame`; ADD `ingest_copm_transfers_dune_manual_csv(path: pathlib.Path) -> pd.DataFrame`; ADD orchestrator `resume_copm_transfers_backfill() -> pd.DataFrame` that consults the existing checkpoint at `contracts/.scratch/copm_transfers_backfill_progress.json` and walks the six-path ladder for blocks > `last_completed_end_block`. All functions pure / functional-python / frozen-dataclass result.
- Modify: `contracts/data/copm_per_tx/copm_transfers_full.csv` — APPEND new rows for blocks 30,486,128 → chain-tip; preserve column schema byte-exact; preserve existing 52,068 rows byte-exact (additive-only — any mutation of an existing row aborts). **NOTE (RC-B1):** the active data file is `copm_transfers_full.csv` (real 52,068 rows); `copm_transfers.csv` in the same directory is a 17-line header stub kept for backwards-compatibility and is NOT modified by this task.
- Modify: `contracts/data/copm_per_tx/README.md` — APPEND a "Phase 2 backfill provenance" block recording: which of the six paths fired, predecessor-path failure reasons, block range covered (30,486,128 → end_block), timestamp, row count delta vs prior 52,068, total row count vs target 110,069, fallback-trigger log.
- Modify: `contracts/.env.example` — ADD placeholders `ALCHEMY_API_KEY_PAID=`, `COVALENT_API_KEY=`, `FLIPSIDE_API_KEY=`, `DUNE_API_KEY=` each with a 4-12-line inline comment block following the Rev-5.2.1 `ALCHEMY_API_KEY` template (purpose / OPTIONAL marker / fallback-trigger pointer / HALT-on-missing policy citation). Comment density (CR-MINOR-3): each placeholder gets 2-3 sentences explaining (a) which path consults it, (b) when the path is triggered (e.g., "consulted ONLY when path-1 forno+Ankr exhaust without reaching the 110,069 ± 0.5% target"), (c) what HALT behavior applies on missing-credential, (d) cost expectation if known (e.g., "Dune community plan: 25,000 monthly credits per RC empirical 2026-04-24"; explicitly no dollar-cost claim for paid Alchemy per RC). The HALT-on-missing comment cites the recovery-protocol bullet by name.
- Modify: `contracts/scripts/tests/test_onchain_duckdb_migration.py` — TIGHTEN row-count tolerance from `110,069 ± 1%` to `110,069 ± 0.5%`; ADD test that the resume orchestrator reads the existing checkpoint correctly (cannot start from block 0); ADD test that the existing 52,068 rows in `copm_transfers_full.csv` are preserved byte-exact post-resume (CR-MINOR-2): `pd.read_csv(copm_transfers_full.csv).head(52068)` after resume completion must be byte-exact equal to the pre-resume snapshot at commit `f1f114cd1`; ADD checkpoint-corruption tests (PM-N2): corrupted JSON → orchestrator HALTs with `CHECKPOINT_CORRUPTED`, missing file → HALT with `CHECKPOINT_MISSING_RESTART_FROM_TASK_11.N.1`, schema-mismatch → HALT with explicit field-list dump (none of these silently default to block 0).
- Modify: `contracts/.scratch/copm_transfers_backfill_progress.json` — at each completed 10k-block window during the resume, atomically rewrite this file with the new `last_completed_end_block` + `total_rows_so_far` + `data_source` reflecting the active path; on FINAL convergence, set `data_source` to a comma-separated list (`"forno+ankr"`, `"forno+covalent"`, etc.) so the historical record names every path that contributed.

**Steps:**
- [ ] **Step 1 (failing test extension; mirrors Task 11.N.1 Step 1 pattern):** extend `test_onchain_duckdb_migration.py` with assertions that (a) full `copm_transfers_full.csv` has 110,069 ± 0.5% rows; (b) the existing 52,068 rows are preserved byte-exact (additive-only on the row dimension; CR-MINOR-2 byte-exact-equal head-52068 assertion); (c) `load_onchain_copm_transfers()` returns the full dataset (not a partial); (d) Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` preserved byte-exact; (e) `resume_copm_transfers_backfill()` reads the existing checkpoint and starts from block `last_completed_end_block + 1` (not zero) — mock the checkpoint file with a fixture pointing at block 30,486,127 and assert the first RPC call uses block 30,486,128; (f) checkpoint-corruption HALT assertions per PM-N2. Run; confirm failure (no resume orchestrator yet).
- [ ] **Step 2 (path-1 Celo public RPC retry, FIRST option):** implement `fetch_copm_transfers_celo_rpc_retry()` against forno (5k-block window) and Ankr (1k-block window) with single-stream concurrency + 30s exponential back-off cap. Pull blocks 30,486,128 → tip. Per RC empirical 2026-04-24 both endpoints respond HTTP 200; expected probability of success: high.
- [ ] **Step 3 (path-2 paid Alchemy; opt-in only):** if Step 2 fails per the per-path failure criteria, check `os.environ.get("ALCHEMY_API_KEY_PAID")`; if unset, log "path-2 SKIPPED (credential unset)" and proceed to Step 4. If set, implement `fetch_copm_transfers_alchemy_paid()` with `getAssetTransfers` paginated for blocks 30,486,128 → tip; on success, halt the ladder.
- [ ] **Step 4 (path-3 Covalent / GoldRush trial-tier):** if Step 3 skipped/failed, check `COVALENT_API_KEY`; if set, perform a trial-validity probe (RC: trial is 25k credits / 14 days, not renewable). If trial is still active and credit budget appears sufficient (>1k pages worth), implement `fetch_copm_transfers_covalent()` and pull blocks 30,486,128 → tip. The endpoint URL `https://api.covalenthq.com/v1/celo-mainnet/.../transfers_v2/` is unverified per RC; verify URL responsiveness with a small request before bulk pull. If trial-expired or credit-exhaustion encountered mid-pull, write checkpoint and proceed to Step 5.
- [ ] **Step 5 (path-4 Flipside SQL REST):** if Step 4 skipped/failed, check `FLIPSIDE_API_KEY`; if set, FIRST run a `describe-table` probe to verify `celo.core.fact_event_logs` exists with the expected schema (per RC: Celo not explicitly listed on Flipside chain-coverage page). If table exists, submit a SELECT query filtering on the COPM contract address + Transfer topic + `block_number > 30485761`; download CSV; verify row schema matches Task 11.N.1 column dtypes byte-exact before append. If table missing, log "path-4 SKIPPED (Celo not on Flipside)" and proceed to Step 6.
- [ ] **Step 6 (path-5 Dune REST direct):** if Step 5 skipped/failed, check `DUNE_API_KEY`; if set, FIRST verify the `/api/v1/execution/{id}/results/csv` URL via `mcp__dune__searchDocs` or direct API-spec fetch (per RC: not surfaced from current docs). If URL confirmed, execute Dune query `7369028` via `POST /api/v1/query/{id}/execute`; poll `GET /api/v1/execution/{id}/status` until completed; download `GET /api/v1/execution/{id}/results/csv`; the full 110,069-row CSV sidesteps the MCP pagination limit. Subset to `block_number > 30485761` before append.
- [ ] **Step 7 (path-6 manual Dune-web export, user-interactive):** if Steps 2-6 all failed/skipped, ping user with the Dune web URL `https://dune.com/queries/7369028` and request CSV download to `contracts/data/copm_per_tx/copm_transfers_dune_manual.csv`. Orchestrator polls for file presence (timeout: 24 hours; document the block in `.scratch` if exceeded). On file appearance, ingest via `ingest_copm_transfers_dune_manual_csv()` and verify schema match.
- [ ] **Step 8 (run + verify):** run extended test from Step 1; all assertions pass; verify Rev-4 decision-hash preserved + the 52,068-row baseline preserved byte-exact + total reaches 110,069 ± 0.5%.
- [ ] **Step 9 (re-run Task 11.N distribution-channel computation):** re-execute `compute_weekly_xd(proxy_kind="b2b_to_b2c_net_flow_usd")` over the now-complete panel; verify the output panel covers ~84 Fridays (matching the supply-channel surrogate's coverage in `onchain_xd_weekly`). Append rows to `onchain_xd_weekly` with `proxy_kind = "b2b_to_b2c_net_flow_usd"`. The existing `proxy_kind = "net_primary_issuance_usd"` rows are preserved (already pre-committed in Rev-5.2.1 Step 5).
- [ ] **Step 10:** confirm `pytest contracts/scripts/tests/` exits 0 (PM-N4 cumulative-test-suite-green requirement); commit with message `feat(abrigo): Rev-5.3 Task 11.N.1b — resume missing-blocks backfill (alternative-path ladder)`.

**Dependency discipline (CR-P2):**
- **No new Python dependencies.** All six paths use `requests` directly against published HTTP endpoints. No SDK installs (`web3.py`, `eth_account`, `dune-client`, `flipside-sdk`, `covalent-api-sdk-python` all forbidden). The venv is locked at the Rev-5.1 surface; any dep addition requires its own plan revision. If an SDK is desired for ergonomic reasons, that's a separate plan rev — not a Rev-5.3 task.

**Non-negotiable rules (same stack as Task 11.N.1):**
- **STRICT TDD** (`feedback_strict_tdd.md`): failing-test extension first. PM-N4 sub-clause: every plan-task commit includes a worknotes line confirming `pytest contracts/scripts/tests/` exits 0.
- **Scripts-only scope** (`feedback_scripts_only_scope.md`): touch only `contracts/scripts/`, `contracts/scripts/tests/`, `contracts/data/`, `contracts/.scratch/copm_transfers_backfill_progress.json`, `contracts/.env.example` — never `src/`, `test/*.sol`, `foundry.toml`, or any Solidity
- **functional-python**: frozen dataclasses, free pure functions, full typing strictness, no inheritance
- **Additive-only**: Rev-4 `decision_hash` preserved byte-exact; existing 52,068 rows in `onchain_copm_transfers` preserved byte-exact; existing `proxy_kind = "net_primary_issuance_usd"` rows in `onchain_xd_weekly` preserved byte-exact; the new distribution-channel rows APPEND and do not mutate
- **Real data over mocks** (`feedback_real_data_over_mocks.md`): hit real third-party APIs; mocks only for HTTP errors that cannot be reproduced (the resume-checkpoint test in Step 1 IS allowed to mock the checkpoint file since that is filesystem state under our control, not an external API response)
- **Activate venv before Python**: `source contracts/.venv/bin/activate`
- **Push origin not upstream** (`feedback_push_origin_not_upstream.md`): `origin` = JMSBPP

**Recovery protocols:**
- If ALL SIX paths fail, HALT + escalate to user with `X_D_STILL_INSUFFICIENT_PHASE_2`. Do NOT silently regress to the partial 52,068-row dataset for downstream X_d computation. The 52,068-row distribution-channel partial X_d is NOT to be folded into Task 11.O even as a sensitivity row — partial coverage produces a structurally-biased X_d (only the early portion of the time-series, before the post-Feb-2025 acceleration documented in report §2.2 daily-execution counts).
- If row count drifts >0.5% from the Dune-reported 110,069 (e.g., chain reorg or counting-rule discrepancy between Dune's decoded layer and Celo native-RPC), HALT + document discrepancy in the provenance README — user decides whether to accept the drift (e.g., the original Dune row count itself may have changed since the 11.N.1 target was set; re-pull `https://dune.com/queries/7369028` to verify the current canonical total).
- If the schema returned by a non-Dune path (Covalent / Flipside / paid Alchemy) does NOT match the Task 11.N.1 column dtypes byte-exact, HALT + escalate. Do NOT silently coerce — the column-dtype contract is load-bearing for the Rev-4 additive-only invariant tested in `test_onchain_duckdb_migration.py`.
- If the user-interactive path (Step 7) is invoked, document the user's CSV-download timestamp in the provenance README so the data-recency claim is auditable.
- If the checkpoint file is corrupted/missing/schema-mismatched (PM-N2), HALT with the appropriate error code; do NOT silently default to block 0.

**Gate:** `onchain_copm_transfers` table contains 110,069 ± 0.5% rows; existing 52,068 rows preserved byte-exact; `onchain_xd_weekly` carries distribution-channel rows under `proxy_kind = "b2b_to_b2c_net_flow_usd"` covering ~84 Fridays; Rev-4 `decision_hash` unchanged; all Task 11.M.5 + 11.N.1 + 11.N.1b tests green; `pytest contracts/scripts/tests/` exits 0; provenance README records which of the six paths fired. Task 11.O can then consult the distribution-channel X_d as a co-equal SECONDARY primary in the resolution matrix per the Rev-5.2.1 DAG-clarification mechanism, subject to the §5 amendment-rider queue ordering.

**DAG clarification (Rev 5.3 — extends Rev-5.2.1 PM-P1):** Task 11.N.1b is NOT a pre-requisite to Task 11.O. The Rev-5.2.1 amendment-rider mechanism (Task 11.O Step 4 "targeted lit re-check + spec refinement folds in distribution-channel X_d as a SECONDARY primary") naturally accommodates the Task 11.N.1b distribution-channel X_d when it lands. Independently, Task 11.N.1b is NOT a pre-requisite to Task 11.N.2b.1 — the Carbon-basket X_d in 11.N.2b is a DIFFERENT data source (Carbon `TokensTraded` events, not COPM Transfer events) and requires its own pre-commitment + budget probe. 11.N.1b and 11.N.2b.1 can run in parallel; the orchestrator may dispatch them concurrently if Data Engineer capacity permits.

**PM-N1 hierarchy note (post-11.N.2 reframing):** under report §4 Option 1, the COPM Transfer-channel X_d that 11.N.1b finishes is now THIRD-RANK in the X_d hierarchy (Carbon-basket-rebalancing primary; Carbon COPM-only-trade-count sensitivity per report §4 Option 3; COPM Transfer-channel third). 11.N.1b is retained because Rev-5.2.1 already pre-committed to producing it AND because its independence from the Carbon data source makes it a useful triangulation row in the resolution matrix, not because it is co-equal with the Carbon-basket X_d. This re-ranking is documented here so Task 11.O does not allocate equal resolution-matrix slots to a deprecated candidate.

---


### Task 11.N.2b.1: Carbon-basket pre-commitment + Dune-credit-budget probe (Rev 5.3 insert — gate task)

**Rationale.** Task 11.N.2 (report at `contracts/.scratch/2026-04-24-copm-bot-attribution-research.md` §2-§4) attributed the two dominant addresses in COPM Transfer events to the Bancor Carbon DeFi protocol on Celo and recommended (§4 Option 1) a NEW X_d source measuring **basket-rebalancing volume across the Mento ↔ global-asset boundary**. Task 11.N.2b.1 is the GATE task: it (a) authors a failing schema-migration test against an in-memory/temporary DuckDB without committing the schema migration to the canonical `structural_econ.duckdb`; (b) verifies all Mento + global basket addresses against canonical sources with a HALT-VERIFY-MANDATORY block on the two RC-flagged truncations (USDT, WETH); (c) probes Dune-credit budget empirically. On clean GO verdict, Task 11.N.2b.2 proceeds; on any HALT, the schema migration is NEVER committed to the canonical DuckDB, preserving atomic-rollback hygiene per CR-P5 / PM-P1 BLOCKER-fix.

**Subagent:** Data Engineer.

**Inputs:** Task 11.N.2 attribution report (mandatory; supplies the basket-membership pre-commitment + reframing rationale); `project_abrigo_inequality_hedge_thesis.md` (2026-04-24 update; supplies the inequality-differential semantic for the new X_d); Rev-5.2.1 schema-migration pattern at Task 11.N.1 Step 0 (template, but inverted ordering per Step Atomicity Protocol below).

**Mento-basket addresses — Step 1 verification required (CR-P3 fix; addresses are PROVISIONAL until Step 1 design memo commits; symbols use canonical 2026 Mento naming per RC-additional-1, with legacy pre-rebrand symbols noted in parentheses for Step-1 cross-reference):**
- COPM `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` (verified in Task 11.N.1 RC review) — provisional, re-verify in Step 1
- USDm (legacy: cUSD) provisional `0x765de816845861e75a25fca122bb6898b8b1282a` — verify in Step 1; Step-1 confirms canonical 2026 symbol `USDm` against Mento docs
- EURm (legacy: cEUR) provisional `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73` — verify in Step 1; Step-1 confirms canonical 2026 symbol `EURm` against Mento docs
- BRLm (legacy: cREAL) provisional `0xe8537a3d056da446677b9e9d6c5db704eaab4787` — verify in Step 1; Step-1 confirms canonical 2026 symbol `BRLm` against Mento docs
- KESm (legacy: cKES) — Provisional address — Step 1 verification required: report §2.1 lists `0x456a3D04…3B0d0` (truncated); RC verified canonical full form `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` against Celo token list (symbol `KESm` confirmed). Step 1 confirms the canonical form is the basket member.
- XOFm — Provisional address — Step 1 verification required: report §2.1 lists `0x73f93dcc…f29a08` (truncated); RC verified canonical full form `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` against Celo token list. Step 1 confirms the canonical form is the basket member.

**Global-basket addresses — same verification rule, with HALT-VERIFY-MANDATORY on USDT + WETH (RC-truncated-addresses BLOCKER fix):**
- CELO native — provisional `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` (Carbon convention per report §2.1) — verify in Step 1
- USDT — **HALT-VERIFY-MANDATORY**: research report §2.1 lists `0x48065fbb…83d5e` (truncated); RC empirical 2026-04-24 found this prefix does NOT reconcile to canonical Celo token list. Canonical USDT bridged on Celo per RC: `0x88eEC49252c8cbc039DCdB394c0c2BA2f1637EA0` — DIFFERENT prefix from the report. Step 1.1 (5-minute HALT gate, see Steps below) blocks ingestion until this discrepancy is resolved by the implementer: either (a) confirm the canonical `0x88eEC49252c8cbc039DCdB394c0c2BA2f1637EA0` is the basket member (preferred — matches authoritative token list); (b) document existence of a separate non-canonical USDT bridge that matches the report's `0x48065fbb…` prefix and pre-commit which one the basket includes; or (c) drop USDT from the basket and document the reduced basket as a deviation from report §4 Option 1. The implementer cannot proceed past Step 1.1 without writing the resolution to the design memo.
- USDC — provisional `0xceba9300…32118c`; RC verified canonical `0xcebA9300f2b948710d2653dD7B07f33A8B32118C` against Celo token list (matches the report prefix). Verify in Step 1.
- WETH — **HALT-VERIFY-MANDATORY**: research report §2.1 lists `0x66803fb8…fb207` (truncated); RC empirical 2026-04-24 found this prefix does NOT reconcile to canonical Celo token list. Canonical WETH bridged on Celo per RC: `0xd221812de1bd094f35587ee8e174b07b6167d9af` (symbol "wETH", native bridge) — DIFFERENT prefix from the report. Step 1.1 blocks ingestion until resolved, same options (a)/(b)/(c) as USDT. Document the chosen WETH bridge in the design memo.

**X_d definition (RESOLVED by brainstorm-fold delta 2026-04-24; design doc `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §1, §2):**
- **Primary X_d formula:** `X_carbon_rebalancing_user_volume_usd_t = Σ |source_amount_usd| over Carbon TokensTraded events in week t WHERE (a) tx_origin ≠ 0x8c05ea305235a67c7095a32ad4a2ee2688ade636 (BancorArbitrage / Arb Fast Lane filtered OUT — user-initiated trades only) AND (b) (sourceToken ∈ Mento_basket AND targetToken ∈ global_basket) OR (sourceToken ∈ global_basket AND targetToken ∈ Mento_basket)`. Volume-weighted USD magnitude (option A), arb-as-diagnostic (option iii). Mento basket = `{COPM, USDm (legacy: cUSD), EURm (legacy: cEUR), BRLm (legacy: cREAL), KESm (legacy: cKES), XOFm}`; global basket = `{CELO, USDT, USDC, WETH}` (Celo-bridged versions; HALT-verify per Step 1.1).
- **Boundary-crossing predicate:** swap is "rebalancing" iff exactly ONE of source/target is in Mento basket and the OTHER is in global basket; Mento↔Mento and global↔global swaps are EXCLUDED from primary X_d (they do not cross the inequality boundary).
- **Diagnostic columns (always populated alongside primary; never dropped regardless of calibration outcome):**
  - `carbon_basket_arb_volume_usd` — Arb Fast Lane volume crossing the same Mento↔global boundary (allows post-hoc decomposition of stress vs flow)
  - `carbon_per_currency_<symbol>_volume_usd` for each of `{COPM, USDm, EURm, BRLm, KESm, XOFm}` — six-element vector of weekly user-only volume per Mento stablecoin (allows per-currency PCA cross-validation in Task 11.N.2c)
  - `carbon_basket_user_volume_usd` (basket-aggregate sum of the six per-currency series) — ALWAYS computed; whether this OR the COPM-only filtered slice becomes the primary scalar is decided by Task 11.N.2c calibration
- **Primary scalar choice — RESOLVED (post §0.2 RC-CF-1/RC-CF-2 collapse + §0.3 CR-FF-1):** the basket-aggregate `carbon_basket_user_volume_usd` is the COMMITTED primary scalar out of the gate; the COPM-only variant is retired. Task 11.N.2c runs `compute_basket_calibration()` against the per-currency vector populated by 11.N.2b.2 as a PCA cross-validation diagnostic only; pre-committed thresholds `N_min=80, power_min=0.80, MDES_SD=0.40, pc1_loading_floor=0.40` (design doc §3 amended per Task 11.N.2c CORRECTIONS block) drive the **two-state decision branch** (PASS / pathological-HALT) per design doc §4 post-collapse. Task 11.N.2b.2 persists the full panel (primary user-volume + arb-only + six per-currency diagnostic) and 11.N.2c verifies the basket-aggregate ≥ `N_min` gate without re-selecting the primary.
- Friday-anchor + America/Bogota timezone consistent with existing `onchain_xd_weekly` convention.
- USD-equivalent of `sourceAmount` computed via daily token-price oracle (Mento broker rate for USDm/EURm/BRLm/KESm/XOFm/COPM; CELO/USDC TWAP for CELO; 1.0 for USDT/USDC; ETH/USD oracle for WETH). Dune-decoded `source_amount_usd` field (text-preserving `VARCHAR` per 11.M.5 precedent) is the canonical source if present; oracle fallback only if Dune does not pre-compute USD.

**DDL fragments (CR-P4 fix — explicit dtype pre-commitment, 11.M.5 commit `af98bb659` precedent):**
- `onchain_carbon_tokenstraded` (per-event from `carbon_defi_celo.carboncontroller_evt_tokenstraded`):
  - `tx_hash`: `VARCHAR(66)` (32-byte hex with `0x` prefix; Dune decoded namespace exposes hashes as hex strings)
  - `evt_index`: `BIGINT`
  - `evt_block_number`: `BIGINT`
  - `evt_block_time`: `TIMESTAMP`
  - `trader`: `VARBINARY(20)` (20-byte EVM address per Dune decoded namespace dtype convention; precedent set by 11.M.5 commit `af98bb659`)
  - `sourceToken`: `VARBINARY(20)`
  - `targetToken`: `VARBINARY(20)`
  - `sourceAmount`: `HUGEINT` (uint256 raw — same dtype precedent as 11.M.5 commit `af98bb659` for token amounts; native `BIGINT` would silently truncate)
  - `targetAmount`: `HUGEINT`
  - `tradingFeeAmount`: `HUGEINT`
  - `byTargetAmount`: `BOOLEAN`
- `onchain_carbon_arbitrages` (per-event from `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted`):
  - `tx_hash`: `VARCHAR(66)`
  - `evt_index`: `BIGINT`
  - `evt_block_number`: `BIGINT`
  - `evt_block_time`: `TIMESTAMP`
  - `caller`: `VARBINARY(20)` (20-byte EVM address per Dune decoded namespace dtype convention)
  - `sourceToken`: `VARBINARY(20)`
  - `tokenPath`: `VARCHAR` (variable-length encoded JSON array; Dune decodes as JSON-string)
  - `sourceAmount`: `HUGEINT`
  - `protocolId`: `VARCHAR` (Dune decode; size unknown; stored as VARCHAR text-preserving)
- `onchain_xd_weekly` CHECK extension (UPDATED post brainstorm-fold + §0.3 final-fix-pass CR-FF-1 collapse): relax CHECK to admit the brainstorm-resolved values `IN ('net_primary_issuance_usd', 'b2b_to_b2c_net_flow_usd', 'carbon_basket_user_volume_usd', 'carbon_basket_arb_volume_usd', 'carbon_per_currency_copm_volume_usd', 'carbon_per_currency_usdm_volume_usd', 'carbon_per_currency_eurm_volume_usd', 'carbon_per_currency_brlm_volume_usd', 'carbon_per_currency_kesm_volume_usd', 'carbon_per_currency_xofm_volume_usd')`. **Ten values total** (two pre-existing + eight new). Rationale: the basket-aggregate primary value `carbon_basket_user_volume_usd` is the COMMITTED primary scalar out of the gate per CR-CF-1 + RC-CF-1 + RC-CF-2 collapse + §0.3 CR-FF-1; the COPM-only variant `_copm_only` was retired (deterministically dead at 44 weeks vs `N_min = 80`). Diagnostic columns (`carbon_basket_arb_volume_usd` + six `carbon_per_currency_<symbol>_volume_usd` rows where `<symbol> ∈ {copm, usdm, eurm, brlm, kesm, xofm}` — canonical 2026 Mento naming, lowercase per `proxy_kind` literal convention) are always populated by 11.N.2b.2. Old `carbon_basket_rebalancing_count` and `carbon_basket_rebalancing_volume` placeholders from the §0 fix-pass are SUPERSEDED — the brainstorm-resolved naming is canonical.

**Files:**
- Modify: `contracts/scripts/econ_schema.py` — author the third schema-migration code path (relaxed CHECK + two new tables). **DO NOT execute against canonical `structural_econ.duckdb` in this task** — only against in-memory/temporary DuckDB for the failing test. Production migration commit is deferred to Task 11.N.2b.2 Step 5 (atomic-commit-after-population). Cite the 11.M.5 commit `af98bb659` HUGEINT precedent in the docstring.
- Create: `contracts/.scratch/2026-04-24-carbon-xd-pre-commitment-memo.md` — Step-1 design memo with: (a) full basket-address table with USDT + WETH HALT-VERIFY resolutions documented; (b) X_d primary-vs-sensitivity declaration (deferred to brainstorm landing — placeholder text "TBD pending brainstorm at <path>"); (c) one reproducible golden-fixture week with expected count + volume values computed manually from Dune query results BEFORE the production filter is run; (d) Model-QA verifies no data peek (mirrors Task 11.N Step 1 pattern); (e) Dune-credit-budget probe results with RC-P12 reference numbers.
- Modify: `contracts/scripts/tests/test_onchain_duckdb_migration.py` — ADD failing test asserting (a) the relaxed CHECK constraint admits all four `proxy_kind` values when run against in-memory DuckDB; (b) the two new tables are created with the dtype-pre-committed schema; (c) Rev-4 `decision_hash` unchanged; (d) the test runs WITHOUT mutating canonical `structural_econ.duckdb` — verify by checksumming the canonical DB before and after test execution.

**Steps:**
- [ ] **Step 1 (basket-address verification + pre-commitment design memo):** verify every Mento + global basket address against Celo token list `https://github.com/celo-org/celo-token-list/blob/main/celo.tokenlist.json` and Mento docs `https://docs.mento.org/mento`; complete the truncated addresses (KESm, XOFm, USDT, USDC, WETH). Author the pre-commitment design memo at `contracts/.scratch/2026-04-24-carbon-xd-pre-commitment-memo.md`. Commit memo before Step 1.1 begins.
- [ ] **Step 1.1 (HALT-VERIFY-MANDATORY for USDT + WETH; 5-minute halt gate):** within the implementer's first 5 minutes of Step 2 Dune probe, the implementer MUST resolve the USDT and WETH address discrepancies flagged by RC. Resolution options: (a) accept canonical `0x88eEC49252c8cbc039DCdB394c0c2BA2f1637EA0` (USDT) + `0xd221812de1bd094f35587ee8e174b07b6167d9af` (WETH) and document choice in design memo; (b) document an alternative non-canonical bridge with cite + reasoning; (c) drop the token from the basket. Implementer CANNOT skip this gate; if 5 minutes elapse without resolution, HALT + escalate to user. Resolution writes to design memo with timestamp.
- [ ] **Step 2 (Dune-credit-budget probe; PRE-PRODUCTION):** before any production data pull, query Dune `searchTables` for the full `carbon_defi_celo.carboncontroller_evt_tokenstraded` and `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted` row counts via small-LIMIT exploratory queries. RC empirical 2026-04-24 reference: count-only aggregate = 0.028 credits for 613,603 events Sep-2024→today; full per-event pull estimated ≤ 5 credits for tokenstraded + < 1 credit for arbitrages; total 11.N.2b cost ≤ 10 credits against current 24,994-credit budget. Document in worknotes. Run a LIMIT-100 sample probe to confirm column-name + dtype mapping aligns with the DDL pre-commitment in the Files block. If any probe surfaces dtype divergence (e.g., a `sourceAmount` field returned as scientific-notation float instead of decimal-string), HALT + revise DDL before Step 3.
- [ ] **Step 3 (failing schema-migration test against in-memory DuckDB):** write the failing test in `test_onchain_duckdb_migration.py` asserting the relaxed CHECK + two new tables work against in-memory DuckDB; assert the canonical DB checksum is unchanged after test run; assert dtype mapping matches Step-2 LIMIT-100 sample probe. Run; confirm failure (no migration code path yet).
- [ ] **Step 4 (implement schema-migration code path):** implement the migration in `econ_schema.py` such that the failing test passes against in-memory DuckDB; canonical DB is NOT touched.
- [ ] **Step 5 (run + verify):** run all assertions; confirm green; canonical DB checksum unchanged; design memo committed; HALT-VERIFY resolutions documented; Dune-budget probe results in worknotes.
- [ ] **Step 6:** confirm `pytest contracts/scripts/tests/` exits 0; commit with message `feat(abrigo): Rev-5.3 Task 11.N.2b.1 — Carbon-basket pre-commitment + budget probe (canonical DB untouched)`.

**Step Atomicity Protocol (CR-P5 / PM-P1 BLOCKER-fix):**
- The schema-migration TEST (Step 3) is written and run FIRST against in-memory/temporary DuckDB — preserves test-first TDD invariant.
- The schema-migration CODE PATH (Step 4) exists in `econ_schema.py` after this task but is NOT executed against the canonical `structural_econ.duckdb` until Task 11.N.2b.2 Step 5 (atomic-commit-after-population — the smoke-probe at Step 4 of 11.N.2b.2 must be fully green before Step 5 atomic commit fires).
- This inversion of the Rev-5.2.1 "Step 0 first" ordering is intentional and necessary because Task 11.N.2b carries three atomic-rollback concerns simultaneously (schema; address verification with HALT path; credit budget unknown) — committing schema first before HALT-points clear leaves the canonical DB in partially-applied state.
- Atomic rollback boundary: 11.N.2b.1 is reversible (memo + tests live in `.scratch/` and `scripts/tests/`; no canonical DB mutation). 11.N.2b.2 atomically commits both the canonical schema migration AND the populated tables in a single Step 6 commit.

**Dependency discipline (CR-P2):** No new Python dependencies. `requests`-only HTTP. Dune queries use the Dune MCP server already available; no `dune-client` SDK install.

**Non-negotiable rules (same stack as Tasks 11.N.1, 11.N.1b):** STRICT TDD; Scripts-only scope; functional-python; Additive-only (Rev-4 `decision_hash` byte-exact); Real data over mocks (Dune MCP probe is real data); Activate venv before Python; Push origin not upstream. PM-N4: `pytest contracts/scripts/tests/` exits 0 at commit boundary.

**Recovery protocols:**
- If Step 1.1 HALT-VERIFY does not resolve USDT/WETH within 5 minutes, escalate to user; do NOT proceed to Step 2 with truncated/unverified addresses.
- If Step 2 Dune-credit budget probe surfaces budget shortfall (current RC evidence says trivially affordable, but probe re-validates at execution time), HALT + escalate. Possible mitigations: (a) Dune-budget top-up; (b) Flipside SQL REST as alternative source if `celo.core.fact_event_logs` exists per Task 11.N.1b Step 5 verify-existence-first — this is unverified per RC; (c) defer 11.N.2b until budget refreshes. Do NOT silently truncate the time-series window.
- If Step 2 LIMIT-100 sample probe surfaces dtype divergence from the pre-committed DDL, HALT + revise DDL in design memo + re-run Step 2 probe; DO NOT silently coerce dtypes at the Python layer.

**Gate:** design memo committed at `contracts/.scratch/2026-04-24-carbon-xd-pre-commitment-memo.md` with full basket-address table + USDT/WETH HALT-VERIFY resolution + Dune-credit-budget probe results + Model-QA no-data-peek attestation; failing schema-migration test passes against in-memory DuckDB; canonical `structural_econ.duckdb` checksum UNCHANGED; `pytest contracts/scripts/tests/` exits 0. GO verdict for 11.N.2b.2 is implicit on this Gate green.

**DAG clarification (Rev 5.3):** Task 11.N.2b.1 is NOT a pre-requisite to Task 11.O. 11.N.2b.2 IS a successor of 11.N.2b.1 (Step 1.1 HALT gate + Step 2 budget probe + Step 5 in-memory schema test must all pass). 11.N.2b.1 may run in parallel with Task 11.N.1b (different data sources, no shared schema-migration concern).

---

### Task 11.N.2b.2: Carbon basket-rebalancing dataset — full ingestion + filter + aggregation (Rev 5.3 insert)

**Rationale.** Predicated on Task 11.N.2b.1 GO verdict (design memo committed; schema-migration test green against in-memory DuckDB; HALT-VERIFY resolutions documented; Dune-credit-budget probe within budget). Task 11.N.2b.2 ingests the full Carbon `TokensTraded` + BancorArbitrage `arbitrageexecuted` event tables, applies the basket-membership filter pre-committed in 11.N.2b.1's design memo, computes the weekly X_d panel, and atomically commits the schema migration + populated tables to canonical `structural_econ.duckdb` in a single Step 6 commit. The atomic-commit-after-population ordering preserves rollback hygiene per CR-P5 / PM-P1 fix.

**Subagent:** Data Engineer.

**Inputs:** Task 11.N.2b.1 design memo (mandatory; supplies basket addresses, X_d formula, golden fixture); Task 11.N.2 attribution report; Rev-5.2.1 schema-migration code path in `econ_schema.py` (authored in 11.N.2b.1 Step 4 but not yet executed against canonical DB).

**X_d aggregation formula (RESOLVED by brainstorm-fold; design doc `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §1, §2):** the primary measure is **user-initiated trades only, volume-weighted USD magnitude**: `X_t = Σ |source_amount_usd| over events in week t where tx_origin ≠ 0x8c05ea305235a67c7095a32ad4a2ee2688ade636 (BancorArbitrage filtered out) AND the swap crosses the Mento ↔ global basket boundary as defined in 11.N.2b.1`. This task computes the FULL panel (primary user-volume + arb-only diagnostic + six per-currency vector + basket-aggregate sum) and writes ALL diagnostic columns to `onchain_xd_weekly`. The COPM-only-vs-basket-aggregate scalar choice for the PRIMARY `proxy_kind` is DEFERRED to Task 11.N.2c calibration — 11.N.2b.2 stages both candidates as panel rows and 11.N.2c picks one. No count-variant produced (the brainstorm resolved on volume-only; option (B) direction-signed series is also out-of-scope per design doc §6).

**Files:**
- Create: `contracts/scripts/carbon_xd_filter.py` — NEW pure module (NOT extension of `copm_xd_filter.py` per design doc §2 component table — separation enforces the brainstorm-resolved module-boundary invariants). Contains `compute_carbon_xd(events: pd.DataFrame, calibration_result: Optional["CalibrationResult"], mento_basket: frozenset[str], global_basket: frozenset[str], friday_anchor_tz: str = "America/Bogota") -> WeeklyCarbonXdPanel`. The `WeeklyCarbonXdPanel` frozen-dataclass per design doc §2 contains: `primary_series: tuple[float, ...]`, `primary_proxy_kind: str`, `arb_only: tuple[float, ...]`, `per_currency: dict[str, tuple[float, ...]]` (six entries), `basket_aggregate: tuple[float, ...]`, `weeks: tuple[date, ...]`, `is_partial_week: tuple[bool, ...]`. When `calibration_result` is `None` (i.e., 11.N.2b.2 invocation pre-calibration), `primary_proxy_kind` defaults to `"carbon_basket_user_volume_usd"` (basket-aggregate) and `primary_series` is the basket-aggregate vector; Task 11.N.2c re-runs with non-None `calibration_result` and persists the chosen primary.
- Modify: `contracts/scripts/econ_pipeline.py` — ADD `fetch_carbon_tokenstraded_dune(query_id: int, api_key: str) -> pd.DataFrame` and `fetch_carbon_arbitrages_dune(query_id: int, api_key: str) -> pd.DataFrame` (both via Dune REST direct since the MCP pagination limit observed in Task 11.N applies to large pulls; basket-wide Carbon event count is 613,603 per RC-P12).
- Modify: `contracts/scripts/econ_query_api.py` — ADD `load_onchain_carbon_tokenstraded()` + `load_onchain_carbon_arbitrages()` returning frozen-dataclass; `load_onchain_xd_weekly()` already accepts `proxy_kind` parameter per Rev-5.2.1; verify it transparently passes through the two new values without code change.
- Create: `contracts/scripts/tests/inequality/test_carbon_xd_filter.py` — golden-fixture test for the basket-membership filter on a small fixture week + independent-reproduction-witness assertion (mirrors Task 11.B + 11.N silent-test-pass-hardening pattern per `feedback_implementation_review_agents.md`).
- Modify: `contracts/scripts/tests/test_onchain_duckdb_migration.py` — assertions: (a) the relaxed CHECK constraint admits all four `proxy_kind` values against canonical DB (post-Step-6 atomic commit); (b) the composite PK `(week_start, proxy_kind)` allows three or four channels to coexist for the same `week_start`; (c) Rev-4 `decision_hash` unchanged; (d) `onchain_carbon_tokenstraded` row count matches the Dune-reported event count for the COPM-touching subset (cross-check vs report §2.1's "57,382 trades" figure on the COPM-touching slice as a smoke test, and against the basket-wide 613,603 figure per RC-P12).
- Create: `contracts/data/carbon_celo/README.md` — provenance block documenting Dune query IDs used for ingestion, basket-address verification source, ingestion timestamp, row counts, credit budget consumed.

**Steps:**
- [ ] **Step 1 (failing test for full pipeline):** write the golden-fixture test in `test_carbon_xd_filter.py` asserting (a) the basket-membership filter excludes Mento↔Mento and global↔global swaps; (b) the user-only volume-weighted USD magnitude reproduces the design-memo manually-computed golden value byte-exact (single primary formula post brainstorm-fold; no count-variant); (c) the `tx_origin = 0x8c05ea305235a67c7095a32ad4a2ee2688ade636` (Arb Fast Lane) filter correctly partitions arb volume into the `carbon_basket_arb_volume_usd` diagnostic column; (d) all six per-currency vector entries are populated and sum to the basket-aggregate; (e) independent-reproduction witness (a second compute path; e.g., direct DuckDB SQL aggregation vs the Python frozen-dataclass pipeline); (f) `proxy_kind` parameter routing is correct across all admitted values. Run; confirm failure.
- [ ] **Step 2 (Dune ingestion):** implement `fetch_carbon_tokenstraded_dune()` and `fetch_carbon_arbitrages_dune()` via Dune REST direct (NOT MCP — MCP pagination limit caused Task 11.N's escalation; Rev-5.3 does not repeat that mistake). Pull full `carbon_defi_celo.carboncontroller_evt_tokenstraded` and `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted` filtered to the basket-membership filter at the SQL layer where possible (reduces credit cost vs full pull + Python-side filter). Persist to a TEMPORARY DuckDB (canonical DB still untouched).
- [ ] **Step 3 (filter + weekly aggregation against TEMPORARY DB):** implement `compute_carbon_xd()` per design doc §2 contract; consume the persisted event tables; produce the FULL weekly panel containing (a) basket-aggregate user-only volume series under `proxy_kind = "carbon_basket_user_volume_usd"` (default primary pre-calibration); (b) arb-only diagnostic under `proxy_kind = "carbon_basket_arb_volume_usd"`; (c) six per-currency diagnostic series under `proxy_kind = "carbon_per_currency_<symbol>_volume_usd"`. Persist all rows to TEMPORARY DuckDB. The COPM-only-vs-basket-aggregate scalar choice for the primary is NOT made here — that's Task 11.N.2c's job. NO count-variant computed (brainstorm-resolved volume-only).
- [ ] **Step 4 (smoke probe against TEMPORARY DB):** run all golden-fixture assertions; verify row counts match Step-2 ingestion; verify Friday-anchor + America/Bogota timezone consistency; verify basket-membership filter correctness. Any failure HALTs before Step 5.
- [ ] **Step 5 (atomic schema-migration commit to canonical DB):** ONLY after Step 4 smoke-probe is fully green, atomically commit the schema migration to canonical `structural_econ.duckdb` using the migration code path authored in 11.N.2b.1 Step 4. Migration is wrapped in a single DuckDB transaction that either applies the relaxed CHECK + two new tables AND populates them with the Step-2/Step-3 data, OR rolls back entirely. Existing `proxy_kind = "net_primary_issuance_usd"` rows preserved byte-exact; existing `proxy_kind = "b2b_to_b2c_net_flow_usd"` rows from Task 11.N.1b (if landed) preserved byte-exact.
- [ ] **Step 6 (run + verify against canonical DB):** re-run all assertions against canonical DB; verify Rev-4 `decision_hash` preserved + supply-channel + distribution-channel rows in `onchain_xd_weekly` preserved byte-exact + new Carbon-basket rows correctly filtered + golden-fixture values match design-memo pre-commitment.
- [ ] **Step 7:** confirm `pytest contracts/scripts/tests/` exits 0; commit with message `feat(abrigo): Rev-5.3 Task 11.N.2b.2 — Carbon basket-rebalancing X_d ingestion + atomic schema migration`.

**Step Atomicity Protocol (CR-P5 / PM-P1 BLOCKER-fix, continued from 11.N.2b.1):**
- Steps 1-4 operate against TEMPORARY DuckDB; canonical `structural_econ.duckdb` is untouched.
- Step 5 atomically commits BOTH schema migration AND populated tables in a single transaction. Rollback semantics: if any sub-step of Step 5 fails (CHECK constraint update, table creation, row population), the transaction rolls back entirely and canonical DB is unchanged.
- Step 6 verifies canonical DB post-commit.
- This ordering ensures the canonical DB never ends up in a state with relaxed CHECK + empty tables (the partially-applied state PM-P1 flagged).

**Dependency discipline (CR-P2):** No new Python dependencies. `requests`-only HTTP. No `dune-client`, `flipside-sdk`, `covalent-api-sdk-python`, or `web3.py`.

**Non-negotiable rules (same stack as 11.N.2b.1):** STRICT TDD; Scripts-only scope; functional-python; Additive-only; Real data over mocks; Activate venv before Python; Anti-fishing discipline (the 11.N.2b.1 design-memo + golden-fixture-before-implementation flow + Model-QA no-data-peek attestation prevent X_d definition from drifting toward whatever fits Y best); PM-N4: `pytest contracts/scripts/tests/` exits 0 at commit boundary.

**Recovery protocols:**
- If Step 4 smoke probe fails, HALT + diagnose; do NOT proceed to Step 5 atomic commit. Canonical DB remains untouched until Step 4 is green.
- If Step 5 atomic transaction fails partway, DuckDB rolls back automatically; canonical DB is unchanged; document failure mode in worknotes; HALT + escalate.
- If the basket-membership SQL filter at Step 2 returns zero rows (e.g., the tokens-traded events table doesn't expose `sourceToken`/`targetToken` fields with the expected names), HALT + dispatch a Dune `describe-table` probe to map the actual column names; document the mapping in the worknotes; do NOT silently rename columns at the Python layer.
- If the user-only volume series is ≈ empty (Arb Fast Lane is ≈100% of activity) — i.e., the data is structurally pathological per design doc §4 row 4 — HALT + escalate to user. Do NOT silently fall back to arb-only as primary (that conflates stress-detection with capital-flow magnitude). Disposition memo lands at `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md`. Task 11.N.2c will then enter the "structurally-pathological" decision branch (design doc §4 row 4) and emit its own escalation memo.
- If the basket-aggregate and per-currency-COPM-only weekly series produce wildly different rankings of high-X_d weeks (Spearman rank correlation < 0.5 between the two candidates), document the divergence in worknotes — this is a SCIENTIFIC finding feeding Task 11.N.2c's PCA cross-validation methodology (II) and is expected behavior, NOT a regression.

**Gate:** `onchain_carbon_tokenstraded` + `onchain_carbon_arbitrages` tables populated with full Sep-2024 → today event series (per RC-P12 ≈ 613,603 events for tokenstraded; arbitrages estimated 70-100k); `onchain_xd_weekly` carries Carbon-basket rows under (a) `proxy_kind = "carbon_basket_user_volume_usd"` (default primary pre-calibration; basket-aggregate sum); (b) `proxy_kind = "carbon_basket_arb_volume_usd"` (Arb Fast Lane diagnostic); (c) six rows under `proxy_kind = "carbon_per_currency_<symbol>_volume_usd"` (per-currency vector for COPM, USDm, EURm, BRLm, KESm, XOFm); golden-fixture test + independent-reproduction witness green; Rev-4 `decision_hash` unchanged; all prior tests green; `pytest contracts/scripts/tests/` exits 0; canonical DB schema migration ATOMICALLY committed alongside populated rows (no partially-applied state). Task 11.N.2c (calibration) is unblocked.

**DAG clarification (Rev 5.3 — UPDATED post brainstorm-fold):** Task 11.N.2b.2 is BLOCKED on 11.N.2b.1 GO. **Task 11.N.2c IS BLOCKED on 11.N.2b.2** (needs the populated panel for calibration). **Task 11.O is now BLOCKED on 11.N.2c** (amendment-rider A9; supply-channel-parallelism RETIRED — see §6). 11.N.2b.2 may run in parallel with 11.N.1b (different data sources, atomicity-isolated via the in-memory-then-canonical-DB pattern). The prior Rev-5.2.1 / §0 fix-pass clause permitting 11.O parallelism on supply-channel surrogate is OVERRIDDEN by the brainstorm-fold delta.

---

### Task 11.N.2c: Basket-share calibration exercise (Rev 5.3 brainstorm-fold insert — primary X_d scalar selection)

**Rationale.** Task 11.N.2b.2 produces the FULL Carbon-basket panel (basket-aggregate user-only volume + arb-only diagnostic + six-element per-currency vector). Task 11.N.2c runs a PCA cross-validation diagnostic on the per-currency series — it does NOT select between candidates because the basket-aggregate `carbon_basket_user_volume_usd` is the committed primary out of the gate (per CR-CF-1 + RC-CF-1 + RC-CF-2: COPM-only `_copm_only` proxy_kind retired since the per-country COPM share is empirically dead-branch at 44 weeks vs `N_min = 80`; methodology (I) primary-selection retired since the basket-aggregate candidate is committed primary unconditionally). Output is a `CalibrationResult` frozen-dataclass reporting per-currency PCA loadings + variance-explained share + the locked primary `carbon_basket_user_volume_usd`. Task 11.N.2c emits ONE of TWO states: PASS (basket-aggregate primary persisted; downstream tasks proceed) or pathological-HALT (the full Mento basket has fewer than `N_min = 80` weekly non-zero obs — anomalous; escalate to user; do NOT silently set arb-only as primary).

**CORRECTIONS-Rev-2 block (Rev-5.3.1, 2026-04-25, user-approved path α from pathological-HALT disposition):** Task 11.N.2c initial run (commit `13cfe5f56`) fired pathological-HALT at the original `N_MIN = 80` because basket-aggregate landed 77 nonzero weeks (3 short). User reviewed the disposition memo at `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md` and selected path α: relax `N_MIN` to 75 with documented rationale. **`N_MIN: Final[int] = 75`** (was 80). Power-floor preservation verified via the pinned Cohen f² formulation: `required_power(75, 13, 0.40) = 0.8638` ≥ `POWER_MIN = 0.80` (scipy live-reproduced 2026-04-25); `required_power(77, 13, 0.40) = 0.8739`; `required_power(80, 13, 0.40) = 0.8877` (original anchor). MDES_SD remains 0.40 (unchanged). Anti-fishing trail: the relaxation is NOT a free-tune to chase a target — it's a documented response to an empirical pathological-HALT, with the new floor still satisfying `POWER_MIN ≥ 0.80` at the operative MDES_SD. Calibration re-run at relaxed N_MIN: PASS verdict at 77 ≥ 75; basket-aggregate `carbon_basket_user_volume_usd` is the committed primary X_d; PC1 explains 0.5159 of standardized per-currency variance; per-currency loadings: EURm +0.59, BRLm +0.56, KESm +0.49, COPM −0.30 (anti-correlated with EU/BR/KE trio — informational), USDm +0.08, XOFm 0.00. Updated calibration result memo at `contracts/.scratch/2026-04-25-carbon-basket-calibration-result-rev2.md`. 3-way review of this CORRECTIONS-Rev-2 dispatched in parallel; pending convergence (does NOT block 11.N.2d dispatch since the relaxation is mathematically defensible; review can land convergent fixes post-hoc).

**CORRECTIONS block (Rev-5.3 v2 fix-pass, RC-CF-1 BLOCKER; updated by Rev-5.3 §0.3 final-fix-pass for MDES formulation pin):** the design doc §3 cites `MDES = 0.20 SD` as the Rev-4 standard. The Rev-5.3 v2 fix-pass relaxes the operative MDES to `0.40 SD` per RC's scipy-verified power computation. The §0.3 final-fix-pass adds the MDES formulation pin below — RC's final-review live scipy reproduction across four standard formulations yielded 0.770 / 0.989 / 0.987 / 0.888, so the operative power figure must be derived from a single canonical formulation, not free-tuned. Pinned `required_power(80, 13, 0.40) ≈ 0.888` under Cohen f² (live-scipy reproduced 2026-04-25; supersedes the prior `≈ 0.85` narrative figure). Achievable power 0.888 ≥ `POWER_MIN = 0.80` — `MDES_SD = 0.40` stands; no upward re-tuning. The smaller-panel exercise (n ≈ 84 weekly obs vs Rev-4's 947 obs) requires a larger detectable effect size. The design doc remains immutable; the correction is recorded HERE in the plan and propagated to source via the `MDES_SD: Final[float] = 0.40` and `MDES_FORMULATION_HASH: Final[str]` constants added in Step 0. Methodology (I) is retired by RC-CF-2 + CR-CF-1, so the MDES correction is only a documentation requirement (not a path-selection input); the value is persisted in source for downstream reference in Task 11.O Rev-2 spec authoring (where MDES anchors enter the resolution-matrix).

**MDES formulation pin (Rev-5.3 §0.3 final-fix-pass — RC NEW BLOCKER fix; canonical Cohen f²):** to prevent the §0.2 narrative figure (`≈ 0.85`) from being interpreted under any of the four scipy formulations RC reproduced (0.770 / 0.989 / 0.987 / 0.888 — non-deterministic), the operative power computation is pinned to **Cohen f²** per Cohen 1988 (*Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., chapter 9). The canonical formulation is:

> Compute `f² = MDES_SD² / (1 − MDES_SD²)` (Cohen's effect-size transform); compute non-centrality parameter `λ = n × f²`; compute the critical F-value `crit = scipy.stats.f.ppf(1 − α, df₁, df₂)` with `α = 0.10`, `df₁ = 6` (the primary block of macro regressors per Rev-4 13-regressor specification), `df₂ = n − k` (`n = 80`, `k = 13`); return `1 − scipy.stats.ncf.cdf(crit, df₁, df₂, λ)` as the achievable power.

Under this pinned formulation, `required_power(80, 13, 0.40) ≈ 0.888` (live-scipy reproduced 2026-04-25 by orchestrator; supersedes the §0.2 `≈ 0.85` narrative). The pinned source text — including the function signature, docstring quoting Cohen 1988 ch. 9, and the four-line body — is committed to `carbon_calibration.py` at Step 0 alongside `MDES_FORMULATION_HASH: Final[str]` whose value is the SHA256 of the pinned source text exactly as written; the Step-0 failing test asserts that `hashlib.sha256(inspect.getsource(required_power).encode("utf-8")).hexdigest() == MDES_FORMULATION_HASH`. Modification of the pinned source — including whitespace, docstring, df₁ value, or alpha — invalidates the hash and HALTs the test. The hash is the load-bearing tamper-evident anchor; the pinned formulation is the load-bearing scientific anchor.

**Anti-fishing guard (Rev-5.3 §0.3 final-fix-pass — Task 11.N.2c modification policy):** `MDES_SD`, `MDES_FORMULATION_HASH`, and the source text of `required_power()` are pre-committed in source at Step 0 of this task. **Modification of any of the three after Step 0 commits requires (a) a full design-doc revision (§3 amended at `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`); (b) a CORRECTIONS block landed in the next plan revision; (c) a full 3-way review cycle (CR + RC + Senior PM) before commit.** Free-tuning `MDES_SD` upward to chase a target power figure is **anti-fishing-banned** per X_d design doc §1 ("Once primary X_d is chosen, downstream tasks consume it without re-selection; mid-stream re-tuning of the primary measure is banned") — the same discipline applies symmetrically to MDES anchors. If `required_power(80, 13, 0.40)` under the pinned formulation drifts below `POWER_MIN = 0.80` due to `n` or `k` changes (e.g., 11.N.2c lands fewer than 80 weekly non-zero obs and the operative `n` becomes the actual count), the correct response is **HALT under `CalibrationStructurallyPathological`**, not free-tuning of `MDES_SD` upward to recover power.

**Subagent:** Data Engineer (light analysis only — EDA + decision memo; no heavy ingestion. The data is already in `onchain_carbon_tokenstraded` + `onchain_carbon_arbitrages` + `onchain_xd_weekly` from 11.N.2b.2; this task only computes derived statistics and persists the calibration result).

**Inputs:**
- `onchain_carbon_tokenstraded` + `onchain_carbon_arbitrages` (populated by 11.N.2b.2; canonical DB)
- `onchain_xd_weekly` rows tagged `carbon_basket_user_volume_usd`, `carbon_basket_arb_volume_usd`, six `carbon_per_currency_<symbol>_volume_usd` (populated by 11.N.2b.2)
- Design doc `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §3 (pre-committed thresholds), §4 (decision branches)
- Rev-4 panel anchors (CPI 947-week panel; Rev-4 MDES anchor = 0.20 SD; 13-regressor spec) — referenced for provenance only; 11.N.2c operative MDES is 0.40 SD per CORRECTIONS block above (smaller-panel exercise relaxation per RC-CF-1)

**Files:**
- Create: `contracts/scripts/carbon_calibration.py` — NEW pure module containing `compute_basket_calibration(per_currency_panel: pd.DataFrame, basket_aggregate: pd.Series, n_min: int, power_min: float, mdes_sd: float, pc1_loading_floor: float) -> CalibrationResult` AND a pinned `required_power(n_obs: int, k_regressors: int, mdes_sd: float, alpha: float = 0.10, df1: int = 6) -> float` per the §0.3 MDES formulation pin (Cohen f² canonical). Module-level `Final` constants pre-commit the FIVE thresholds (FOUR scientific + ONE tamper-evident): `N_MIN: Final[int] = 80`, `POWER_MIN: Final[float] = 0.80`, `MDES_SD: Final[float] = 0.40`, `PC1_LOADING_FLOOR: Final[float] = 0.40`, `MDES_FORMULATION_HASH: Final[str] = "<sha256-of-required_power-source-text>"` (the orchestrator computed the hash via `hashlib.sha256(inspect.getsource(required_power).encode("utf-8")).hexdigest()` against the canonical source text of the pinned function — implementer recomputes at Step 0 commit time and bakes the hash into the constant; the Step-0 failing test then asserts the recomputed hash matches the constant byte-exact). Frozen-dataclass per design doc §2 contract (REVISED for Rev-5.3 v2 fix-pass two-state collapse): `CalibrationResult{primary_choice: Literal["basket_aggregate"], basket_n_nonzero_obs: int, per_currency_pc1_loadings: dict[str, float], pc1_variance_explained: float, basket_passes_n_min: bool, rationale: str}`. The `primary_choice` Literal admits ONE value (`basket_aggregate`) — pathological branch raises `CalibrationStructurallyPathological` instead of returning. PCA via `sklearn.decomposition.PCA` against the standardized per-currency matrix. Pure free functions; no inheritance; full typing strictness.
- Create: `contracts/scripts/tests/inequality/test_carbon_calibration.py` — failing-first test file. Step 0 tests assert (a) the five module-level `Final` constants in `carbon_calibration.py` match the post-correction values byte-exact (`N_MIN == 80`, `POWER_MIN == 0.80`, `MDES_SD == 0.40`, `PC1_LOADING_FLOOR == 0.40`, `MDES_FORMULATION_HASH == hashlib.sha256(inspect.getsource(required_power).encode("utf-8")).hexdigest()`); (b) `required_power(80, 13, 0.40)` returns `0.888` ± 1e-3 under the pinned Cohen f² formulation (live-scipy reproduced; this is the achievable-power floor — if the implementer's local scipy version drifts the value, HALT and escalate); (c) `required_power(80, 13, 0.40) >= POWER_MIN` (i.e., 0.888 ≥ 0.80) — assertion that the operative power exceeds the minimum, NOT that it equals a target. Subsequent tests cover the TWO decision branches (collapsed per RC-CF-1 + RC-CF-2): PASS (basket-aggregate has ≥ `N_MIN` weekly non-zero obs → `CalibrationResult` returned with locked `primary_choice = "basket_aggregate"`); pathological-HALT (basket-aggregate has fewer than `N_MIN` weekly non-zero obs → `CalibrationStructurallyPathological` exception raised). Independent-reproduction-witness assertion: a second compute path (numpy explicit standardization + covariance-matrix eigendecomposition) reproduces PC1 variance-explained share to within 1e-6 of the `sklearn.decomposition.PCA` output.
- Create: `contracts/.scratch/2026-04-24-carbon-basket-calibration-result.md` — calibration memo with: (a) per-currency stats table (mean, median, weeks-non-zero, std, percentile-95) for each of the six Mento stablecoins; (b) `CalibrationResult` dump in code-block; (c) confirmation of the locked primary X_d (`carbon_basket_user_volume_usd`); (d) per-currency PCA loadings and variance-explained per currency (informational/diagnostic — not path-selecting); (e) basket-aggregate `N_min` pass/fail trace.
- Modify: `contracts/scripts/econ_query_api.py` — extend `load_onchain_xd_weekly(proxy_kind=…)` admitted-set to include the calibration-confirmed primary value (no code change needed; literal-set is already the union of all admitted values per Rev-5.2.1 + 11.N.2b.1 schema migration; CR-CF-1 retirement of `_copm_only` already applied at 11.N.2b.1 Files block).
- Modify: `contracts/scripts/tests/test_onchain_duckdb_migration.py` — assert the basket-aggregate `proxy_kind = carbon_basket_user_volume_usd` row count matches `CalibrationResult.basket_n_nonzero_obs`; assert all six per-currency diagnostic rows are preserved byte-exact post-calibration (calibration READS but does not MUTATE the panel).

**Steps (mandatory ordering per design doc §3 anti-fishing guarantee):**
- [ ] **Step 0 (pre-commit thresholds + pinned MDES formulation in source + correction-block reference; failing-first test):** add `N_MIN: Final[int] = 80`, `POWER_MIN: Final[float] = 0.80`, `MDES_SD: Final[float] = 0.40`, `PC1_LOADING_FLOOR: Final[float] = 0.40`, `MDES_FORMULATION_HASH: Final[str] = "<sha256>"` to the top of `carbon_calibration.py` (module created with these constants AND the pinned `required_power()` function ONLY at this step — no calibration logic yet). The pinned `required_power()` source text follows the canonical Cohen f² formulation specified in the §0.3 MDES formulation pin block above; implementer copies the function body byte-exact as documented in that block. Implementer computes the SHA256 of `inspect.getsource(required_power).encode("utf-8")` and bakes the resulting hex digest into `MDES_FORMULATION_HASH`. Author a docstring on each constant citing the source anchor:
  - `N_MIN` ← existing CPI Rev-4 panel filtered range (Banrep IBR / DFF weekly extraction yielded 78–84 obs in similar tasks per 11.M.6 commit `fff2ca7a3`); unchanged anchor.
  - `POWER_MIN` ← Rev-4 standard target retained at 0.80; achievable power 0.888 at `MDES_SD = 0.40` under the pinned Cohen f² formulation per §0.3 MDES formulation pin block (NOT at MDES_SD = 0.20 — under the same pinned formulation that yielded power 0.320; `≥ POWER_MIN` is the operative gate, not equality to a target).
  - `MDES_SD` ← Phase-A.0 anchor; documented relaxation from Rev-4's 0.20 SD per RC-CF-1 BLOCKER scipy verification under the pinned Cohen f² formulation (n=80, k=13, df₁=6, α=0.10; MDES=0.20 SD yielded actual power 0.320 — far below 0.80; relaxed to 0.40 SD where the pinned formulation gives power 0.888 — exceeds `POWER_MIN = 0.80`). Smaller-panel exercise (n ≈ 84 weekly obs vs Rev-4's 947 obs) requires a larger detectable effect size. See Task 11.N.2c CORRECTIONS block + MDES formulation pin block in this plan for the full provenance; design doc §3 unchanged (immutable); the corrected operative value lives here.
  - `PC1_LOADING_FLOOR` ← PCA non-trivial-loading convention (≥ 0.40 absolute value); used as informational/diagnostic threshold only (per RC-CF-2 collapse, no longer a path-selection input).
  - `MDES_FORMULATION_HASH` ← tamper-evident anchor for the pinned `required_power()` function source text per §0.3 MDES formulation pin block. SHA256 of the function source as committed at Step 0; modification of the function (whitespace, docstring, df₁ value, α value, body lines) invalidates the hash and HALTs the Step-0 test. The hash is the load-bearing tamper-evident anchor; the pinned formulation is the load-bearing scientific anchor.
  Write the failing tests in `test_carbon_calibration.py` Step-0 block asserting (a) the five constants match the post-correction values byte-exact; (b) `MDES_FORMULATION_HASH == hashlib.sha256(inspect.getsource(required_power).encode("utf-8")).hexdigest()`; (c) `required_power(80, 13, 0.40)` returns `0.888 ± 1e-3` under the pinned formulation; (d) `required_power(80, 13, 0.40) >= POWER_MIN`. Run; confirm failure (no `compute_basket_calibration()` function yet — Step-0 tests import the constants + `required_power()` only). Commit threshold-only file before Step 1.
- [ ] **Step 1 (implement `compute_basket_calibration()` per design doc §2 contract, post-collapse):** implement the function consuming per-currency panel + basket-aggregate; compute basket-aggregate non-zero weekly observation count against `N_MIN` (PASS gate); compute PCA diagnostic on the per-currency matrix (standardize; fit `PCA(n_components=...)`; extract per-currency loadings on PC1 + PC1 variance-explained share — informational only, not path-selecting); return `CalibrationResult` with locked `primary_choice = "basket_aggregate"` and full diagnostic payload, OR raise `CalibrationStructurallyPathological` if `basket_n_nonzero_obs < N_MIN`. The TWO decision branches (PASS / pathological-HALT) must be covered by failing-first tests in `test_carbon_calibration.py`; run tests; confirm green. Methodology (I) statistical-power computation is NOT part of the path-selection logic (retired per RC-CF-2); however, the `MDES_SD` constant is exposed for downstream Task 11.O Rev-2 spec authoring's resolution-matrix MDES anchor.
- [ ] **Step 2 (run against 11.N.2b.2 data):** activate venv (`source contracts/.venv/bin/activate`); load `onchain_carbon_tokenstraded` + `onchain_carbon_arbitrages` + `onchain_xd_weekly` rows from canonical DB (READ-only); pass through `compute_basket_calibration()`; capture the returned `CalibrationResult`. Do NOT branch logic here — the function-return drives downstream behavior.
- [ ] **Step 3 (emit calibration memo):** write `contracts/.scratch/2026-04-24-carbon-basket-calibration-result.md` with the structured content from the Files block (per-currency stats table, `CalibrationResult` dump, chosen primary + rationale, PCA loadings, branch-traversal trace). Memo references the design-doc decision-branch row that fired.
- [ ] **Step 4 (confirm primary X_d in `onchain_xd_weekly`):** `primary_choice` is locked to `"basket_aggregate"` (no branching per RC-CF-2 collapse). The primary `proxy_kind = "carbon_basket_user_volume_usd"` is ALREADY populated by 11.N.2b.2 — no INSERT/UPDATE issued by 11.N.2c. This step issues a READ-only verification query against `onchain_xd_weekly` confirming row count matches `CalibrationResult.basket_n_nonzero_obs`; assert byte-exact preservation of the six `carbon_per_currency_<symbol>_volume_usd` diagnostic rows + the `carbon_basket_arb_volume_usd` diagnostic. Calibration does NOT mutate the canonical DB.
- [ ] **Step 5 (HALT-on-pathological — basket-aggregate insufficient):** if `basket_n_nonzero_obs < N_MIN` (the full Mento basket has fewer than 80 weekly non-zero observations across 84 candidate weeks — anomalous given Carbon DeFi's 613k-event volume per RC empirical probe), `compute_basket_calibration()` raises `CalibrationStructurallyPathological` with a structured payload; orchestrator catches and writes a disposition memo at `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md`; halt + escalate to user. The Carbon-basket X_d thesis is empirically failing at the basket-wide level; user decides whether to (a) abandon the X_d source; (b) pivot to a completely different X (resume Phase-A.0 brainstorm-α/β/γ); (c) drop the Mento-↔-global-boundary constraint and re-formulate. Do NOT silently set arb-only as primary (would conflate stress-detection with capital-flow magnitude — the exact failure mode the brainstorm-fold's user-only filter prevents).
- [ ] **Step 6 (verify + commit):** run all tests in `test_carbon_calibration.py` + `test_onchain_duckdb_migration.py`; confirm green; verify Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` byte-exact; confirm `pytest contracts/scripts/tests/` exits 0; commit with message `feat(abrigo): Rev-5.3 Task 11.N.2c — Carbon-basket calibration + primary X_d selection`.

**Step Atomicity Protocol (continued from 11.N.2b.1 / 11.N.2b.2):**
- Step 0 commits threshold-only source file (four frozen `Final` constants); reversible by file deletion.
- Steps 1-3 operate against READ-only loads of the canonical DB; no schema changes; no mutations.
- Step 4 is READ-only verification (basket-aggregate already populated by 11.N.2b.2; calibration only confirms row counts and diagnostic preservation); no transaction needed.
- Step 5 explicitly does NOT mutate canonical DB on pathological branch — escalation memo lands in `.scratch/` instead.

**Collapse-rejected rationale (PM-CF-2 propagated):** 11.N.2c stays decomposed from 11.N.2b.2 even though Step 4 is now READ-only. Two reasons: (i) 11.N.2b.2 mutation surface is ingestion-write (additive Carbon-event INSERT) which has its own rollback semantics + atomicity protocol; collapsing would re-introduce the partially-applied-state failure mode PM-P1 originally flagged; (ii) the calibration `CalibrationResult` artifact — including PCA loadings + variance-explained — is a downstream-consumed contract for Task 11.O Rev-2 spec authoring (Y selection cross-validation) and Task 11.N.2d's per-country-differential design check; emitting it as a separate task with its own gate keeps the artifact provenance clean.

**Dependency discipline (CR-P2 propagated):** `scipy` and `sklearn` are already in the venv from Rev-4 / Task 11.M.6. NO new Python dependencies introduced. No `dune-client`, `flipside-sdk`, etc.

**Non-negotiable rules (same stack as 11.N.1b / 11.N.2b.1 / 11.N.2b.2):** STRICT TDD (failing-first; threshold-pre-commitment as a separate Step 0 commit before any logic); Scripts-only scope (touch `contracts/scripts/`, `contracts/scripts/tests/inequality/`, `contracts/.scratch/` only — never `src/`, `test/*.sol`, `foundry.toml`); functional-python (frozen dataclass, free pure function, full typing strictness, no inheritance); Additive-only (Rev-4 `decision_hash` byte-exact; existing `onchain_xd_weekly` rows preserved); Real data over mocks (calibration runs against real 11.N.2b.2 data; mocks reserved for the four-branch coverage tests in `test_carbon_calibration.py`); Activate venv before Python; Push origin not upstream; PM-N4 (`pytest contracts/scripts/tests/` exits 0 at commit boundary).

**Recovery protocols (post-collapse, two-state):**
- **Case 1 (PASS — basket-aggregate ≥ N_MIN weekly non-zero obs):** primary `proxy_kind = "carbon_basket_user_volume_usd"` confirmed; downstream Task 11.O Rev-2 spec adopts regional-basket framing (consistent with Y₃ regional-pan-EM differential per Task 11.N.2d); per-currency PCA loadings carried forward as cross-validation diagnostic for the Y selection in 11.O. Basket-aggregate is the sole primary X_d (no Colombia-only sub-branch).
- **Case 2 (HALT — basket-aggregate < N_MIN weekly non-zero obs):** raise `CalibrationStructurallyPathological`; do NOT proceed to canonical-DB-read confirmation; escalate to user. The Carbon-basket X_d thesis is empirically falsified at the basket-wide level (anomalous given RC's 613k-event empirical probe); user decides next-step pivot.
- If PCA fitting fails (e.g., singular covariance matrix because one currency series is identically zero), HALT + diagnose; document in memo; user decides whether to drop the singular currency from the basket and re-run, or to pivot.
- The `MDES_SD = 0.40` constant is exposed for downstream use in Task 11.O Rev-2 spec authoring (resolution-matrix MDES anchor); 11.N.2c does NOT consume `scipy.stats.ncf.ppf` in the path-selection logic (methodology I retired per RC-CF-2 collapse), so the prior NaN-on-power-computation recovery clause is no longer applicable to this task.

**Gate:** `CalibrationResult` committed at `contracts/.scratch/2026-04-24-carbon-basket-calibration-result.md` (with full per-currency stats + locked primary `carbon_basket_user_volume_usd` + per-currency PCA loadings + variance-explained share + N_MIN pass/fail trace); primary X_d already persisted to `onchain_xd_weekly` under `proxy_kind = "carbon_basket_user_volume_usd"` from Task 11.N.2b.2 (READ-only verified by Step 4) — OR pathological-branch escalation memo at `contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md`; Rev-4 `decision_hash = 6a5f9d1b…` preserved byte-exact; all 11.M.5 / 11.N.1 / 11.N.1b / 11.N.2b.1 / 11.N.2b.2 / 11.N.2c tests remain green; `pytest contracts/scripts/tests/` exits 0; module-level `Final` thresholds match the post-correction values byte-exact (Step-0 tests assert `N_MIN = 80`, `POWER_MIN = 0.80`, `MDES_SD = 0.40`, `PC1_LOADING_FLOOR = 0.40`, and `MDES_FORMULATION_HASH` matches the live SHA256 of the pinned `required_power()` source); pinned `required_power(80, 13, 0.40)` reproduces 0.888 ± 1e-3 under the canonical Cohen f² formulation. Task 11.N.2d is unblocked (Y₃ panel construction).

**DAG clarification (Rev 5.3 brainstorm-fold + v2 fix-pass):** Task 11.N.2c is BLOCKED on Task 11.N.2b.2 (needs ingested Carbon data + populated `onchain_xd_weekly` rows). **Task 11.N.2d BLOCKS on Task 11.N.2c** (needs the basket-aggregate calibration PASS verdict + locked primary X_d before Y₃ panel construction). **Task 11.O BLOCKS on Task 11.N.2d** (needs both the calibrated primary X_d AND the Y₃ panel before Rev-2 spec authoring) — this overrides the prior Rev-5.2.1 / §0 fix-pass parallelism claim that 11.O could run on supply-channel surrogate. Amendment-rider A9 in §5 documents this DAG override; §6 below ("11.O DAG amendment") gives the operational details. 11.N.2c MAY run in parallel with 11.N.1b (different data sources).

---

### Task 11.N.2d: Y₃ inequality-differential dataset construction (Rev 5.3 v2 fix-pass insert — Y-target shift APPLIED)

**Rationale.** The Carbon-basket X_d (Task 11.N.2c-confirmed `carbon_basket_user_volume_usd`) is regional-scope by construction (6 Mento stablecoins × 4 global tokens). The Rev-5.1 / Rev-5.2.1 / Rev-5.3 §0 / Rev-5.3 §0.1 anchored Task 11.O on `Y_asset_leg = (Banrep_rate − Fed_funds)/52 + ΔTRM/TRM` (USD-COP carry, Colombia-specific) — but a regional X paired with Colombia-specific Y is a thesis mismatch. The brainstorm-converged Y₃ design at `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (committed `23560d31b`) specifies a regional pan-EM inequality differential Y₃ that pairs cleanly with the basket-aggregate X_d. Task 11.N.2d constructs that Y₃ panel; amendment-rider A1 is RETIRED-as-applied at this task's landing.

**Rationale for X_d/Y₃ scope asymmetry (RC-FF-11; per §0.3 final-fix-pass):** the X_d basket spans 6 Mento stablecoins (`COPM, USDm, EURm, BRLm, KESm, XOFm`) while Y₃ aggregates 4 anchor countries (`CO, BR, KE, EU`). USDm and XOFm have **no per-country macro anchors** in the WC-CPI panel: USDm pegs to USD (no single-country sovereign-bond + WC-CPI panel applies — it is a global numeraire), and XOFm pegs to the West African CFA franc (a multi-country currency union spanning eight WAEMU members; constructing a single representative "WAEMU" anchor would require its own multi-country panel separate from Y₃'s methodology). The 4-country anchor set is therefore correct by design, not a coverage gap; the X_d/Y₃ scope mismatch is the intended reduction from 6 stablecoin-side observables to 4 country-side macro panels. Implementer does NOT attempt to extend Y₃ to 6 countries — that's a separate methodology revision requiring its own design-doc amendment.

**Subagent:** Data Engineer.

**Inputs:**
- Per-country equity-index data (COLCAP / IBOVESPA / NSE 20 / STOXX 600) — weekly Friday-anchored log-returns
- Per-country 10Y sovereign-bond yield (TES / NTN-B / Kenya 10Y / German Bund) — weekly Friday-anchored level (basis points)
- Per-country WC-CPI components (Banrep / IBGE / KNBS / Eurostat — food + energy/housing-utilities + transport-fuel) — monthly per-country, interpolated to weekly via LOCF
- Existing Rev-4 panel (TRM, CPI surprise, Banrep IBR, Fed DFF — for sample-window alignment); already persisted in canonical DuckDB
- Y₃ design doc `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` §1 (sign convention), §4 (60/25/15 weights), §5 (panel windows), §8 (table contract), §9 (pre-committed parameters), §10 (recovery protocols)

**Files (NEW):**
- Create: `contracts/scripts/y3_data_fetchers.py` — pure free functions `fetch_country_equity(country: Literal["CO","BR","KE","EU"], start: date, end: date) -> pd.DataFrame`, `fetch_country_sovereign_yield(country: ..., start: date, end: date) -> pd.DataFrame`, `fetch_country_wc_cpi_components(country: ..., start: date, end: date) -> pd.DataFrame` per design doc §8 contract.
- Create: `contracts/scripts/y3_compute.py` — pure free functions `compute_wc_cpi_weighted(components: pd.DataFrame) -> pd.Series`, `interpolate_monthly_to_weekly_locf(monthly: pd.Series, friday_anchor_tz: str) -> pd.Series`, `compute_per_country_differential(equity_returns: pd.Series, wc_cpi_logchange: pd.Series) -> pd.Series`, `compute_y3_aggregate(per_country_diffs: dict[str, pd.Series]) -> Y3Panel` per design doc §8. Module-level `Final` constants pre-commit eight parameters per design doc §9.
- Create: `contracts/scripts/tests/inequality/test_y3.py` — strict-TDD test suite covering pre-commit constants (Step 0), per-country fetchers (Steps 1-3), WC-CPI weighting + LOCF (Step 4), per-country differential (Step 5), Y₃ aggregate (Step 6), DuckDB persistence (Step 7), sensitivity panel (Step 8). Failing-first authored before each implementation step.
- Modify: `contracts/scripts/econ_schema.py` — additive schema migration: NEW table `onchain_y3_weekly` per design doc §8 contract — `week_start DATE PK, y3_value DOUBLE NOT NULL, copm_diff DOUBLE, brl_diff DOUBLE, kes_diff DOUBLE, eur_diff DOUBLE, source_methodology VARCHAR DEFAULT 'y3_v1'`. Migration is purely additive — no existing tables touched; Rev-4 `decision_hash` byte-exact preserved.
- Modify: `contracts/scripts/econ_pipeline.py` — additive ingestion path for Y₃ panel; idempotent re-run (UPSERT-by-(`week_start`, `source_methodology`) — does NOT mutate prior rows).
- Modify: `contracts/scripts/econ_query_api.py` — NEW loader `load_onchain_y3_weekly(source_methodology: Literal["y3_v1","y3_v1_sensitivity"] = "y3_v1") -> OnchainY3Weekly` returning frozen-dataclass `OnchainY3Weekly{week_start: pd.Timestamp, y3_value: float, copm_diff: float, brl_diff: float, kes_diff: float, eur_diff: float, source_methodology: str}` (vector-of-rows representation per econ-query-api convention).

**Pre-committed parameters (per design doc §9; embedded as `Final` constants in `y3_compute.py` at Step 0):**
- `WC_CPI_FOOD_WEIGHT: Final[float] = 0.60`
- `WC_CPI_ENERGY_HOUSING_WEIGHT: Final[float] = 0.25`
- `WC_CPI_TRANSPORT_FUEL_WEIGHT: Final[float] = 0.15`
- `COUNTRY_AGGREGATION_WEIGHT: Final[float] = 0.25` (equal-weight, 1/4 per anchor country: CO / BR / KE / EU)
- `PRIMARY_PANEL_START: Final[date] = date(2024, 9, 1)`
- `PRIMARY_PANEL_END: Final[date] = date(2026, 4, 24)`
- `SENSITIVITY_PANEL_START: Final[date] = date(2023, 8, 1)`
- `LOCF_TIMEZONE: Final[str] = "America/Bogota"`

**Steps (mandatory ordering):**
- [ ] **Step 0 (pre-commit constants + failing-first test):** add the 8 `Final` constants to `y3_compute.py` (module created with these constants ONLY at this step — no compute logic yet). Failing test in `test_y3.py` Step-0 block asserts each constant matches design doc §9 byte-exact. Run; confirm failure (no compute functions yet — test imports the constants only). Commit threshold-only file before Step 1.
- [ ] **Step 1 (per-country equity fetcher; failing-first):** failing test for `fetch_country_equity()` returning weekly Friday log-returns for one country (e.g., Colombia COLCAP, last 8 Fridays of primary panel); independent reproduction witness via Yahoo Finance OR direct stat-agency historical CSV (whichever is the pre-registered source per design doc §8); assert log-return computation byte-exact via second-pass numpy. Implement; run; confirm pass. Repeat per country (BR / KE / EU).
- [ ] **Step 2 (per-country sovereign-bond fetcher):** same failing-first pattern for `fetch_country_sovereign_yield()` per country (TES 10Y / NTN-B / Kenya 10Y / German Bund). Independent reproduction witness via Investing.com OR direct central-bank historical series.
- [ ] **Step 3 (per-country WC-CPI components fetcher):** same failing-first pattern for `fetch_country_wc_cpi_components()` returning monthly per country (food + energy/housing-utilities + transport-fuel). Kenya is the bottleneck per Y₃ research — handle as KNBS Excel-append fetch with documented fragility; on failure, fall back to 3-country aggregate per design doc §10 row 2 with documented limitation flag persisted to `source_methodology`.
- [ ] **Step 4 (WC-CPI weighting + LOCF):** implement `compute_wc_cpi_weighted()` (60/25/15 weights from `Final` constants) + `interpolate_monthly_to_weekly_locf()` (Friday-anchored America/Bogota timezone). Independent reproduction witness via pandas DataFrame manual rebuild.
- [ ] **Step 5 (per-country differential):** implement `compute_per_country_differential()` returning weekly `Δ_country_t = R_equity + Δlog(WC_CPI)` per design doc §1 sign convention. Pinned-fixture golden test for week 2025-W45 per country (CO / BR / KE / EU); golden values computed manually from raw inputs and checked into `test_y3.py`.
- [ ] **Step 6 (Y₃ aggregate):** implement `compute_y3_aggregate()` returning frozen-dataclass `Y3Panel{week_start: pd.Timestamp, y3_value: float, per_country_diffs: dict[str, float]}` per design doc §8. Independent reproduction witness via second-pass pandas computation (manual dict-mean vs the function output).
- [ ] **Step 7 (DuckDB persistence):** schema migration in `econ_schema.py` (additive — NEW `onchain_y3_weekly` table); ingestion in `econ_pipeline.py` (idempotent UPSERT by `(week_start, source_methodology)` PK); loader `load_onchain_y3_weekly()` in `econ_query_api.py` returning frozen-dataclass `OnchainY3Weekly`. Schema-migration TEST authored against in-memory DuckDB FIRST (Step Atomicity Protocol per 11.N.2b.1 / 11.N.2b.2 / 11.N.2c precedent); commit happens AFTER ingestion + smoke-probe succeed. **Persists primary panel only** (`source_methodology = 'y3_v1'`); the sensitivity panel (Aug-2023 → 2026-04-24) is carved out into NEW Task 11.N.2d.1 per §0.3 PM-FF-1 atomicity-hygiene split.
- [ ] **Step 8 (verify + commit):** run all tests in `test_y3.py` + `test_onchain_duckdb_migration.py`; confirm green; verify Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` byte-exact; confirm `pytest contracts/scripts/tests/` exits 0; commit with message `feat(abrigo): Rev-5.3 Task 11.N.2d — Y₃ inequality-differential dataset, primary panel (4-country equal-weight, WC-CPI 60/25/15, Sep-2024→2026-04-24)`.

**Step Atomicity Protocol (continued from 11.N.2b.1 / 11.N.2b.2 / 11.N.2c):**
- Step 0 commits threshold-only source file (eight frozen `Final` constants); reversible by file deletion.
- Steps 1-6 are pure-compute (no canonical-DB writes); reversible by code revert.
- Step 7 is the first canonical-DB-mutating step (additive `onchain_y3_weekly` table creation + INSERT under `source_methodology = 'y3_v1'`); schema-migration TEST authored against in-memory DuckDB BEFORE the canonical-DB migration commit; canonical-DB commit after Step 7 ingestion + smoke-probe succeed.
- Step 8 is verification-only; no mutations.
- The Aug-2023 → 2026-04-24 sensitivity panel is NOT part of this task post-§0.3 PM-FF-1 split; it lives in Task 11.N.2d.1.

**Collapse-rejected rationale (PM-CF-2 propagated):** 11.N.2d stays decomposed from 11.N.2c. Reasons: (i) the data sources are disjoint (Carbon-basket on-chain events vs per-country macro time-series); collapsing would force a single subagent to context-switch between Dune-credit-budgeted on-chain ingestion and free-tier macro-data fetching; (ii) the Step Atomicity Protocol's atomic-rollback property is preserved by keeping `onchain_y3_weekly` migration separate from `onchain_carbon_*` migrations — failure in one does not corrupt the other; (iii) Y₃ panel construction is a single semantically-coherent unit and warrants its own gate in the cumulative test-suite green requirement (PM-N4).

**Dependency discipline (CR-P2 propagated):** `pandas`, `numpy`, `requests`, `python-dateutil`, `pytz` are already in the venv from Rev-4. No new Python dependencies introduced. No `web3.py`, `dune-client`, `flipside-sdk`, `covalent-api-sdk-python`, etc.

**Non-negotiable rules (same stack as 11.N.1b / 11.N.2b.1 / 11.N.2b.2 / 11.N.2c):** STRICT TDD (failing-first; threshold-pre-commitment as a separate Step 0 commit before any logic; pinned-fixture golden tests for per-country differentials at Step 5); Scripts-only scope (touch `contracts/scripts/`, `contracts/scripts/tests/inequality/`, `contracts/.scratch/` only — never `src/`, `test/*.sol`, `foundry.toml`); functional-python (frozen dataclass `Y3Panel` + `OnchainY3Weekly`, free pure functions, full typing strictness, no inheritance); Additive-only (Rev-4 `decision_hash` byte-exact preserved through schema migration; Task 11.N.2c output `onchain_xd_weekly` byte-exact through this task — Y₃ migration touches only the new `onchain_y3_weekly` table); Real data over mocks (per-country equity / bond / WC-CPI fetched from real sources; mocks reserved for the recovery-protocol failure-mode tests); Activate venv before Python (`source contracts/.venv/bin/activate`); Push origin not upstream; PM-N4 (`pytest contracts/scripts/tests/` exits 0 at commit boundary).

**Recovery protocols (per design doc §10):**
- **Kenya WC-CPI ETL fails (KNBS PDF/Excel parse fragility per design-doc-flagged risk):** compute Y₃ from 3 countries (CO / BR / EU); document limitation in source-methodology flag (`source_methodology = "y3_v1_3country_kenya_unavailable"` row variant); persist alongside the 4-country panel where available.
- **Eurozone HICP transport-fuel unavailable:** substitute `(transport CPI − food/energy double-count adjustment)` per design doc §10 row 2; document substitution in calibration memo at `contracts/.scratch/2026-04-24-y3-construction-result.md`.
- **Equity holiday calendar misalignment** (Friday is a national holiday in CO / BR / KE / EU): roll the Friday log-return to the last trading day per country per design doc §10 row 3; never silently substitute zero return.
- **Y₃ has fewer than `N_MIN = 80` weekly non-zero obs** (anomalous given ~84 weeks of primary-panel coverage): HALT with `Y3_PANEL_INSUFFICIENT` flag; do NOT proceed to Task 11.O; orchestrator catches and writes a disposition memo at `contracts/.scratch/2026-04-24-y3-panel-insufficient-disposition.md`; user decides whether to (a) extend panel to sensitivity window (Aug-2023 → 2026-04-24, ~140 weeks) and re-run; (b) drop a country from the aggregate; (c) pivot.
- **Sign convention drift** (a country's `Δlog(WC_CPI)` regression coefficient lands at the wrong sign vs design doc §1 expected sign): flag in calibration memo; do NOT alter the sign convention in source — design doc §1 is immutable.

**Gate:** `onchain_y3_weekly` populated with primary panel ≥ `N_MIN = 80` weekly obs across 4-country (or 3-country fallback) aggregate; sensitivity panel populated under `source_methodology = "y3_v1_sensitivity"`; Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` byte-exact through schema migration; all 11.M.5 / 11.N.1 / 11.N.1b / 11.N.2b.1 / 11.N.2b.2 / 11.N.2c / 11.N.2d tests remain green; `pytest contracts/scripts/tests/` exits 0; `load_onchain_y3_weekly()` exposed via query-API and returns `OnchainY3Weekly` frozen-dataclass; module-level `Final` constants in `y3_compute.py` match design doc §9 byte-exact (Step-0 test). Task 11.O is unblocked (full Y₃ panel + calibrated X_d both available).

**DAG clarification (Rev 5.3 v2 fix-pass insert; updated by §0.3 PM-FF-1):** Task 11.N.2d is BLOCKED on Task 11.N.2c (needs the calibration PASS verdict + locked primary X_d `carbon_basket_user_volume_usd` before Y₃ panel construction can proceed under the regional-basket framing). **Task 11.N.2d.1 is BLOCKED on Task 11.N.2d** (sensitivity panel re-runs Steps 1-6 over a wider window using the same fetcher modules). **Task 11.O BLOCKS on Task 11.N.2d**; Task 11.O does NOT block on Task 11.N.2d.1 — the sensitivity panel is a cross-validation diagnostic for Task 11.O, consumed lazily once the panel lands. The §6 DAG amendment governs the Task 11.O DAG override (supply-channel-parallelism RETIRED). 11.N.2d.1 MAY run in parallel with Task 11.O if both are dispatched after 11.N.2d commits — Task 11.O does its Rev-2 spec authoring against the primary panel; 11.N.2d.1 produces the sensitivity rows under `source_methodology = 'y3_v1_sensitivity'` and Task 11.O's later sensitivity-cross-validation step consumes them whenever both have committed.

---

### Task 11.N.2d.1: Y₃ sensitivity panel construction (Aug-2023 → 2026-04-24) (Rev 5.3 §0.3 final-fix-pass insert — PM-FF-1 atomicity-hygiene split)

**Rationale.** Task 11.N.2d landed the primary Y₃ panel covering Sep-2024 → 2026-04-24 (~84 weeks). Per §0.3 PM-FF-1, the Aug-2023 → 2026-04-24 sensitivity panel construction (~140 weeks; +1-year-pre-period) is carved out into its own task to preserve Rev-5.2.1 atomicity-hygiene discipline (Task 11.N.2d's 9-step body was too large; Step 8 was a re-run of Steps 1-7 over a wider window). Task 11.N.2d.1 reuses the same fetcher and compute modules from `y3_data_fetchers.py` + `y3_compute.py`; it persists the sensitivity panel under `source_methodology = 'y3_v1_sensitivity'` to the same `onchain_y3_weekly` table, allowing Task 11.O's downstream sensitivity-cross-validation step to consume both panels via `load_onchain_y3_weekly(source_methodology='y3_v1_sensitivity')`.

**Subagent:** Data Engineer.

**Inputs:**
- Task 11.N.2d output (`onchain_y3_weekly` rows under `source_methodology = 'y3_v1'`; canonical DuckDB)
- `y3_data_fetchers.py` + `y3_compute.py` modules (committed by Task 11.N.2d Step 0/1-7; reused byte-exact, no module changes)
- Y₃ design doc `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` §5 (panel windows; sensitivity panel pre-registered), §9 row 7 (sensitivity panel start = 2023-08-01), §10 row 1 (Kenya-fallback recovery)
- Pre-committed constant `SENSITIVITY_PANEL_START: Final[date] = date(2023, 8, 1)` from Task 11.N.2d Step 0; assert byte-exact at this task's Step 0.

**Files (all MODIFY-only; no new modules):**
- Modify: `contracts/scripts/econ_pipeline.py` — extend the Task 11.N.2d ingestion path with a sensitivity-panel branch parameterized on `(start_date, source_methodology)`; idempotent UPSERT by `(week_start, source_methodology)` PK (matches Task 11.N.2d).
- Modify: `contracts/scripts/tests/inequality/test_y3.py` — add Step-1 to Step-3 sensitivity-panel test cases mirroring Task 11.N.2d's primary-panel pattern; assert (a) row count ≈ 140 ± 2 weeks; (b) primary-panel rows under `source_methodology = 'y3_v1'` preserved byte-exact; (c) sensitivity rows do NOT overlap-mutate the primary rows (they are a separate row set distinguished by `source_methodology`).
- Create: `contracts/.scratch/2026-04-25-y3-sensitivity-panel-result.md` — provenance memo: panel coverage, country-availability per week, Kenya-fallback rows (if KNBS data missing for Aug-2023 → Sep-2024 window), row count vs target.

**Steps (mandatory ordering):**
- [ ] **Step 0 (failing-first sensitivity test):** in `test_y3.py` add failing test asserting `load_onchain_y3_weekly(source_methodology='y3_v1_sensitivity')` returns ≥ `N_MIN = 80` rows with `week_start >= date(2023, 8, 1)`; assert `SENSITIVITY_PANEL_START` constant in `y3_compute.py` is byte-exact `date(2023, 8, 1)`; assert primary-panel rows under `source_methodology = 'y3_v1'` preserved byte-exact (`pd.read_sql("SELECT * FROM onchain_y3_weekly WHERE source_methodology='y3_v1' ORDER BY week_start")` matches a checksum captured before this task runs). Run; confirm failure.
- [ ] **Step 1 (sensitivity-panel ingestion):** invoke the same Task 11.N.2d fetchers (`fetch_country_equity`, `fetch_country_sovereign_yield`, `fetch_country_wc_cpi_components`) parameterized on `start = SENSITIVITY_PANEL_START`, `end = PRIMARY_PANEL_END`; run the same `compute_wc_cpi_weighted` + `interpolate_monthly_to_weekly_locf` + `compute_per_country_differential` + `compute_y3_aggregate` pipeline byte-exact. Write resulting rows to TEMPORARY DuckDB.
- [ ] **Step 2 (atomic-commit-after-population):** ONLY after Step 1 smoke-probe is green (≥ 138 weeks of rows; primary-panel checksum unchanged), atomically commit the sensitivity rows to canonical `onchain_y3_weekly` under `source_methodology = 'y3_v1_sensitivity'`. Idempotent UPSERT — re-run is safe.
- [ ] **Step 3 (verify + commit):** run all tests in `test_y3.py` + `test_onchain_duckdb_migration.py`; confirm green; verify Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` byte-exact; verify primary-panel rows preserved byte-exact (Step 0 checksum); confirm `pytest contracts/scripts/tests/` exits 0; emit provenance memo at `contracts/.scratch/2026-04-25-y3-sensitivity-panel-result.md`; commit with message `feat(abrigo): Rev-5.3 Task 11.N.2d.1 — Y₃ sensitivity panel (Aug-2023→2026-04-24, +1-year-pre-period; PM-FF-1 atomicity-hygiene split from 11.N.2d Step 8)`.

**Step Atomicity Protocol (continued from 11.N.2b.1 / 11.N.2b.2 / 11.N.2c / 11.N.2d):**
- Step 0 is failing-test-only; no mutations.
- Step 1 operates against TEMPORARY DuckDB; canonical DB untouched.
- Step 2 atomically commits sensitivity rows to canonical `onchain_y3_weekly` in a single DuckDB transaction; rollback semantics preserved (UPSERT under PK `(week_start, source_methodology)` — primary rows under `source_methodology = 'y3_v1'` are untouched by the sensitivity INSERT path).
- Step 3 is verification-only; no mutations.

**Collapse-rejected rationale (PM-CF-2 / PM-FF-1 propagated):** 11.N.2d.1 stays decomposed from 11.N.2d. Reasons: (i) atomicity hygiene — collapsing reintroduces the 9-step body PM-FF-1 flagged; (ii) the wider-window panel is a sensitivity diagnostic, not a primary-panel concern, and warrants its own gate in the cumulative test-suite green requirement (PM-N4); (iii) parallelism — Task 11.O may dispatch on the primary panel without waiting for the sensitivity panel, since Task 11.O's sensitivity-cross-validation step consumes the wider window lazily.

**Dependency discipline (CR-P2 propagated):** No new Python dependencies; reuses Task 11.N.2d module set byte-exact.

**Non-negotiable rules (same stack as 11.N.2d):** STRICT TDD; Scripts-only scope; functional-python; Additive-only (Rev-4 `decision_hash` byte-exact through this task; primary-panel rows byte-exact through this task — sensitivity INSERT is row-disjoint from primary INSERT under the `(week_start, source_methodology)` composite PK); Real data over mocks (per-country fetchers hit the same real sources Task 11.N.2d hits, just with an earlier `start` date); Activate venv before Python; Push origin not upstream; PM-N4 (`pytest contracts/scripts/tests/` exits 0 at commit boundary).

**Recovery protocols (per design doc §10 + this task):**
- **Kenya WC-CPI ETL fails for the Aug-2023 → Sep-2024 sub-window (KNBS PDF/Excel parse fragility):** compute the affected weeks from 3 countries (CO / BR / EU) per design doc §10 row 2; persist those rows with `source_methodology = 'y3_v1_sensitivity_3country_kenya_unavailable'` (variant flag); document scope in provenance memo.
- **Sensitivity panel has fewer than 138 weeks** (anomalous given ~140 weeks of expected coverage): HALT with `Y3_SENSITIVITY_PANEL_INSUFFICIENT` flag; do NOT silently truncate; orchestrator catches and writes a disposition memo at `contracts/.scratch/2026-04-25-y3-sensitivity-panel-insufficient-disposition.md`; user decides next step.
- **Primary-panel rows mutated by accidental UPSERT path** (e.g., a `source_methodology` column-binding bug): Step 0 checksum + Step 3 byte-exact assertion catches this; HALT with `Y3_PRIMARY_PANEL_MUTATED` flag — abort the canonical-DB transaction; investigate.

**Gate:** `onchain_y3_weekly` carries sensitivity-panel rows under `source_methodology = 'y3_v1_sensitivity'` covering Aug-2023 → 2026-04-24 (≥ 138 weeks); primary-panel rows under `source_methodology = 'y3_v1'` preserved byte-exact; Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` byte-exact; all 11.M.5 / 11.N.1 / 11.N.1b / 11.N.2b.1 / 11.N.2b.2 / 11.N.2c / 11.N.2d / 11.N.2d.1 tests remain green; `pytest contracts/scripts/tests/` exits 0; provenance memo committed at `contracts/.scratch/2026-04-25-y3-sensitivity-panel-result.md`. Task 11.O sensitivity-cross-validation step is unblocked (consumes the sensitivity rows lazily; does not gate Task 11.O Rev-2 spec authoring).

**DAG clarification:** Task 11.N.2d.1 is BLOCKED on Task 11.N.2d (reuses its fetcher and compute modules; primary-panel rows must be present in canonical DB before sensitivity rows are appended). Task 11.O Rev-2 spec authoring does NOT block on 11.N.2d.1 — it consumes the sensitivity rows lazily once both 11.O and 11.N.2d.1 have committed. 11.N.2d.1 MAY run in parallel with Task 11.O (Task 11.O's primary-panel-Y consumption is independent of the sensitivity rows; sensitivity-cross-validation is a downstream step within Task 11.O that can wait for 11.N.2d.1's commit).

---


### Task 11.O: Rev-2 spec authoring via `structural-econometrics` skill (Rev 5 insert)

> **Rev-5.3.2 scope-update applied:** the input references, primary-panel anchors, MDES-anchor narrative, and pre-commitment table below are updated by Task 11.O-scope-update (in §B of the Rev-5.3.2 CORRECTIONS block) to consume the freshly landed Rev-5.3.2 Y₃ panel. The structural-econometrics-skill invocation methodology is unchanged byte-exact — only the panel inputs and pre-commitments have been updated. Dispatch is BLOCKED until Task 11.N.2d-rev clears the joint-coverage gate (cleared at landing commit `c5cc9b66b` + admitted-set fix-up `2a0377057`; 76 ≥ 75 weeks).

**Subagent:** foreground invocation of `superpowers:structural-econometrics` skill by orchestrator.

**Inputs:**
- Task 11.L literature review (mandatory guardrail); Task 11.M profile; Task 11.N X_d (committed primary `proxy_kind = "carbon_basket_user_volume_usd"`).
- **Rev-5.3.2 primary Y₃ panel** under `source_methodology` literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` over the primary panel window `[2023-08-01, 2026-04-24]` (γ backward extension + δ-{BR via BCB SGS, CO via DANE}; EU=Eurostat preserved; KE skipped per design §10 row 1). Joint nonzero X_d × Y₃ overlap landed at **76 weeks** (≥ `N_MIN = 75` from Rev-5.3.1 path α; 1-week margin).
- **Rev-5.3.2 IMF-IFS-only sensitivity Y₃ panel** under `source_methodology` literal `y3_v2_imf_only_sensitivity_3country_ke_unavailable` over the same window (joint X_d × Y₃ overlap = 56 weeks; FAIL by 19 weeks against `N_MIN = 75`); committed at Task 11.N.2d.1-reframe per the comparison memo at `contracts/.scratch/2026-04-25-y3-imf-only-sensitivity-comparison.md`.
- Rev-4 panel (TRM RV, CPI surprise) **plus Task 11.M.6 panel extension (Fed funds + Banrep IBR rate-level columns)** loaded via `econ_query_api.py`.
- `MDES_FORMULATION_HASH` anchor `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (canonical Cohen f² formulation; preserved byte-exact through Rev-5.3.2).

**Files:**
- Create: `contracts/docs/superpowers/specs/2026-04-24-abrigo-inequality-differential-design.md`
- Create: `contracts/.scratch/2026-04-24-spec-authoring-worknotes.md`

- [ ] **Step 0 (Rev-5.3.2 precondition — addresses SD-RR-A1):** Before Step 1 invocation, the foreground orchestrator dispatches a separate Data-Engineer follow-up that (a) flips the `load_onchain_y3_weekly` default `source_methodology` from `"y3_v1"` to the Rev-5.3.2 v2 primary literal `"y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"`, and (b) migrates the Step-7 synthetic-DB round-trip test in `scripts/tests/inequality/test_y3.py` (lines 285–323 at fix-up commit `2a0377057`) to pass an explicit `source_methodology` argument rather than relying on the legacy default. This eliminates the residual silent-empty-tuple footgun (production caller reading the canonical DuckDB with the legacy default would receive an empty tuple instead of a `ValueError`). The follow-up is a precondition for spec authoring because any reader/citer of `load_onchain_y3_weekly` in the Rev-2 spec or downstream notebooks consumes the corrected default. Failing-test-first per `feedback_strict_tdd`.
- [ ] **Step 1:** invoke `superpowers:structural-econometrics` skill. Primary Y (gate target) = `Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}`, weekly series derivable from Rev-4 panel controls already in hand. Primary X = X_d from Task 11.N. Diagnostic Y's = Y₁ TRM RV (existing), Y₂ CPI surprise (existing). Deferred Y = Y_consumption_leg (tier-2 parallel work-stream; DANE EMMV retail-sales + BanRep HDS fetch; NOT in current scope). Spec authoring consumes the **Rev-5.3.2 primary Y₃ panel** (76 weeks joint coverage; landed via Task 11.N.2d-rev) as the operative `n` for all power calculations and resolution-matrix MDES anchors — superseding any prior 56-week-bound narrative used at amendment-rider A9 authoring time.
- [ ] **Step 2:** derive all 13 rows of the resolution matrix consuming Task 11.L recommendations (expected sign, magnitude, identification strategy). Formulate the functional equation + null hypothesis pre-committed before estimation. The Rev-2 spec's pre-commitment table MUST enumerate the BR BCB SGS source upgrade and the CO DANE source upgrade as documented panel-construction methodology choices (not vendor-internal details) — they are gate-load-bearing under Rev-5.3.2 (the IMF-IFS-only sensitivity demonstrates the 20-week joint-coverage loss without these upgrades).
- [ ] **Step 2b (Rev-5.3.2 pre-registered sensitivity — addresses RC A3 / SD-RR-A2):** the Rev-2 spec MUST pre-register a **`LOCF-tail-excluded` sensitivity row** in the resolution matrix or sensitivity panel (the sensitivity row name is the spec author's choice; the substance is fixed). The sensitivity is defined as: re-count joint nonzero X_d × Y₃ overlap after truncating Y₃ at the EU 2025-12-01 binding cutoff (i.e., before the 120-day LOCF tail forward-extension that lifts the panel from `2025-12-31 → 65 weeks` to `2026-03-27 → 76 weeks`). The pre-committed expected verdict is **65 weeks → FAIL by 10 weeks against `N_MIN = 75`**, byte-exactly matching Reality Checker probe-5 in `contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md`. This pre-registration locks the gate against silent re-tuning by any future revision that tightens the LOCF policy: if a downstream review proposes excluding LOCF-tail rows from the joint count, the pre-registered FAIL outcome is the immediate reference, not a discoverable-later defense. Pre-registration is in the Rev-2 spec body, not in scratch. The pre-registered IMF-IFS-only sensitivity (Rev-5.3.2 Task 11.N.2d.1-reframe; 56-week FAIL) is enumerated alongside as a separate sensitivity row guarding against silent source-upgrade reversal.
- [ ] **Step 3 (MDES — fixes Rev-1.1.1 CR-E2):** compute MDES via `scipy.stats.ncf.ppf` root-finding at actual N_eff (76 under primary Rev-5.3.2 panel; 65 under LOCF-tail-excluded sensitivity; 56 under IMF-IFS-only sensitivity) and df₂. Do NOT use the analytical approximation that produced Rev-1.1.1's λ ≈ 13 overstatement. Verify with an independent-reproduction witness (second compute path via `statsmodels.stats.power.FTestPower` or manual non-central-F root-find). The MDES anchor in the resolution-matrix narrative reflects the operative `n = 76` from the Rev-5.3.2 primary panel (no longer the prior 56-week-bound narrative).
- [ ] **Step 4 (targeted lit re-check):** once the functional equation is drafted, dispatch a focused re-read of the Task 11.L corpus AGAINST the specific equation — does any prior paper use this exact form? Are our identification assumptions defensible in light of prior work? Refine spec if material findings surface; record changes in work-notes.
- [ ] **Step 5:** commit Rev-2 spec with message `spec(abrigo): Rev-2 inequality-differential functional equation via structural-econometrics (Rev-5 Task 11.O)`.

**Future-maintenance note (admitted-set scaling — SD-A4 forwarded from Task 11.N.2d.1-reframe Senior-Developer review):** The `_KNOWN_Y3_METHODOLOGY_TAGS` admitted-set in `scripts/econ_query_api.py` currently holds 4 entries (`y3_v1`, `y3_v1_3country_ke_unavailable`, `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`, `y3_v2_imf_only_sensitivity_3country_ke_unavailable`). If the Rev-2 spec authoring above adds a 5th methodology tag for the LOCF-tail-excluded sensitivity (Step 2b) — e.g., a separately-persisted DuckDB row-set rather than a query-time truncation — the admitted-set + per-tag block-comment shape in `econ_query_api.py` will be approaching its scaling threshold. At ~6 entries the natural fold is to a structured `_Y3_METHODOLOGY_PROVENANCE: Final[dict[str, str]]` provenance dict (per SD-A4 advisory in `contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md` §2). Track but do NOT refactor preemptively — the current shape is fine for 4 entries and remains acceptable through 5. The fold becomes strictly better at 6+. Forwarded for future-revision consideration only.

**Gate:** Rev-2 spec committed with functional equation + pre-committed null + scipy-correct MDES + literature-grounded identification assumptions + Rev-5.3.2 panel anchors (primary 76-week + LOCF-tail-excluded sensitivity 65-week + IMF-IFS-only sensitivity 56-week) all enumerated as pre-committed sensitivity rows. All 13 resolution-matrix rows populated.

### Task 11.P: Three-way Rev-2 spec review (Rev 5 insert)

**Subagent:** three parallel dispatches — Code Reviewer + Reality Checker + Technical Writer (spec-review trio per `feedback_three_way_review.md`). Rule 13 cycle-cap applies (3 full round-trips max, 3 per-reviewer re-dispatches max, TW consolidation after each round).

**Files:**
- Create: `contracts/.scratch/2026-04-2X-rev2-ineq-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-2X-rev2-ineq-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-2X-rev2-ineq-review-technical-writer.md`

- [ ] **Step 1:** dispatch three reviewers in parallel against Rev-2 spec + Task 11.L literature review + Task 11.M/N artifacts as first-class review inputs. CR audits internal consistency of the 13-row resolution matrix + functional-equation classification. RC audits empirical claims, citation grounding, MDES arithmetic (independent scipy reproduction), and whether Task 11.L literature actually supports the claimed expected signs. TW audits clarity of the functional equation prose, §0 supersession banner (Rev-1/1.1/1.1.1 all superseded), and pedagogical coherence of the inequality-differential construct.
- [ ] **Step 2:** TW consolidation; apply BLOCKs + FLAGs per Rev-3.1 protocol.
- [ ] **Step 3:** iterate per Rule 13; if BLOCK is methodology-level, `structural-econometrics` re-invocation is required before next cycle.
- [ ] **Step 4:** commit TW-consolidated spec with message `spec(abrigo): Rev-2 fix-pass, 3-way review findings addressed (Rev-5 Task 11.P)`.

**Gate:** Phase 2b Task 12 implementation step blocked until Task 11.P returns unanimous PASS / PASS-WITH-FIXES verdict and TW consolidation is committed.

### Task 11.Q: Multi-Y panel assembly via DuckDB econ_pipeline extension (Rev 5 insert)

**Subagent:** Data Engineer.

**Files:**
- Modify: `contracts/scripts/econ_panels.py` (additive — new weekly panel view joining Rev-4 CPI-panel columns with `onchain_xd_weekly` + computed `y_asset_leg_weekly`)
- Modify: `contracts/scripts/cleaning.py` (additive — `CleanedInequalityPanelV1` frozen-dataclass; `_compute_decision_hash_inequality` that extends Rev-4 hash with X_d + Y_asset_leg column digests)
- Create: `contracts/scripts/tests/inequality/test_inequality_panel.py`
- Modify: `contracts/data/structural_econ.duckdb` (via pipeline — new materialized view or table)

- [ ] **Step 1 (failing test):** assert (a) Rev-4 CPI decision-hash (`6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` per `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23`) preserved byte-exact post-extension; (b) new column `y_asset_leg_t` is deterministically reproducible from `(banrep_rate, fed_funds, trm_level)` columns already in Rev-4 panel; (c) new column `x_d_weekly` matches Task 11.N DuckDB table row-for-row; (d) extended panel exposes via `econ_query_api.py` a new `load_inequality_panel()` function returning the frozen-dataclass type.
- [ ] **Step 2:** extend DuckDB panel view; compute `y_asset_leg` column; join `x_d_weekly` column.
- [ ] **Step 3:** run test; confirm pass; commit with message `feat(abrigo): Rev-5 Task 11.Q — inequality panel extension via DuckDB`.

**Tier-2 parallel note (out of current phase scope):** `Y_consumption_leg = f(DANE EMMV retail-sales monthly, BanRep household-debt-service-ratio)` fetch is a SEPARATE work-stream. A future plan revision will fold the consumption-leg series into `structural_econ.duckdb` at which point the full `Y_inequality = Y_asset_leg − Y_consumption_leg` differential becomes the gate target (per `project_abrigo_inequality_hedge_thesis.md`). Current Rev-5 gate test is single-leg (asset-leg only) as an intermediate calibration; the full-differential gate awaits tier-2 data completion.

**Gate:** extended inequality panel committed in DuckDB; Phase 2b Task 12 (existing decision-hash extension task) can now resume — it consumes the new `CleanedInequalityPanelV1` seam in place of the retired remittance-panel scope.

---

## Phase 2b — Panel Extension (resumes after Phase 1.5 convergence)

### Task 12: Decision-hash extension preserving Rev-4 fingerprint (may parallelize with Task 11)

**Subagent:** Data Engineer

**Scheduling note (Rev-2, PM F4):** Task 12 depends only on Task 9's `CleanedRemittancePanelV1` seam. It has no dependency on Task 11's fixture. Task 12's test and implementation can run in parallel with Task 11.

**Files:**
- Modify: `contracts/scripts/cleaning.py` (additive — new `_compute_decision_hash_remittance`)
- Test: `contracts/scripts/tests/remittance/test_decision_hash_extension.py`

- [ ] **Step 1 (Rev-2 scoped — CR B1): Write the failing test, restricted to primary-column hash only.** Assert (a) the Rev-4 decision-hash value (`6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`, verified by Reality Checker from `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23`) is preserved byte-exact when the remittance-panel loader runs; (b) the extended decision-hash is a deterministic function of the Rev-4 hash + the sorted primary-RHS-column spec hash (aux columns are hashed in Task 13, corridor column in Task 14 — their incremental hash contributions are deferred to those tasks' tests); (c) any mutation of an existing Rev-4 column aborts with `FrozenPanelViolation` at panel-load. Defer the "aux-column hash inclusion" and "corridor-column hash inclusion" assertions to the Task 13 and Task 14 test specs respectively.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** the extension function with a seam for aux-column and corridor-column hash contributions that Tasks 13 and 14 will plug into.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): decision-hash extension (primary-RHS only) preserving Rev-4 frozen panel invariants`.

### Task 13: Auxiliary columns — regime, event, A1-monthly, release-day

**Subagent:** Data Engineer

**Files:**
- Modify: `contracts/scripts/cleaning.py` (additive — new helper functions)
- Test: `contracts/scripts/tests/remittance/test_auxiliary_columns.py`

- [ ] **Step 1 (Rev 3.1 amended — CR-B1): Write the failing test.** Assert four auxiliary columns exist on the loaded panel: `regime_post_2015` (binary dummy), `event_petro_trump_2025` (binary dummy for documented Jan-2025 48h window), **`a1r_quarterly_rebase_bridge`** (the BanRep-quarterly AR(1) surprise from Task 10 rebased onto the weekly panel via step-constant within each quarter; this is the Rev 3.1 replacement for the obsolete `a1r_monthly_rebase` name, which assumed a monthly primary that no longer exists — renamed to reflect the Rev-1.1 quarterly-only BanRep reality; operationally serves as the S14 validation-row column per Rev-1.1 spec §6, exposed on the panel so the sensitivity forest-plot (Task 23) can render the bridge row alongside the on-chain primary), `release_day_indicator` (binary). Each column's computation rule matches the Rev-1.1 spec exactly. Assert each aux-column hash extends the decision-hash produced by Task 12's seam (i.e., the extended-hash after Task 13 is deterministic, includes all four aux-column spec hashes in sorted order, and still preserves the Rev-4 base hash). This test absorbs the aux-column portion of CR B1.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** extending `CleanedRemittancePanelV1` → `CleanedRemittancePanelV2` additively.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): auxiliary columns (regime/event/A1-R-bridge/release-day) per Rev-1.1 spec; hash extension`.

### Task 14: Quarterly corridor reconstruction sensitivity column

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/corridor_reconstruction.py`
- Create: `contracts/data/banrep_corridor_quarterly.csv` (committed fixture)
- Modify: `contracts/scripts/cleaning.py` (additive)
- Test: `contracts/scripts/tests/remittance/test_corridor_reconstruction.py`

- [ ] **Step 0 (Rev-2 pre-flight — RC F1):** Before writing any test, the Data Engineer reads Basco & Ojeda-Joya 2024 *Borrador* 1273 in full and produces a one-page reconstruction recipe as a scratch note at `contracts/.scratch/2026-04-20-remittance-corridor-reconstruction-recipe.md`. Borrador 1273 is cited as a *caveat* and *anchor* for corridor reconstruction in the Rev-1 spec — it is **not** a documented step-by-step replication target. If the recipe cannot be derived from the paper's published tables, Task 14 produces an **empty-placeholder sensitivity row** documenting the gap (with `corridor_reconstruction_available: false` in the downstream gate verdict) rather than silently omitting the row. Decide go/no-go at the end of Step 0.
- [ ] **Step 1: Write the failing test.** If Step-0 recipe is derivable: assert `reconstruct_us_corridor_quarterly(monthly_aggregate_df, mpr_quarterly_breakdown_df) → DataFrame` exists with a reconstruction-SE column propagated for downstream gate pricing. If Step-0 recipe is NOT derivable: assert the empty-placeholder path emits the `corridor_reconstruction_available: false` marker and a non-null reason-string pointing to the Step-0 scratch note.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** (reconstruction or empty-placeholder path per Step 0 outcome). Extend `CleanedRemittancePanelV2` → `CleanedRemittancePanelV3` with the corridor column (or placeholder null column with provenance flag). Include the corridor-column hash in the extended decision-hash per the Task-12 seam.
- [ ] **Step 4: Run and confirm pass** against a committed MPR-derived fixture (or the empty-placeholder path).
- [ ] **Step 5: Commit** with message `feat(remittance): quarterly corridor reconstruction sensitivity column (or documented-gap placeholder) + hash extension`.

### Task 15: Panel validation + integration smoke test

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/remittance/test_panel_integration.py`

- [ ] **Step 1: Write the failing test.** Run `load_cleaned_remittance_panel(conn)` end-to-end (loading the `CleanedRemittancePanelV3` that Tasks 9/13/14 build additively). Assert all columns present, row count = 947 (unchanged from Rev-4, verified by Reality Checker against `nb1_panel_fingerprint.json:188` and memory), decision-hash = Rev-4-hash-extended with primary-RHS + aux columns + corridor column (or null-corridor marker), no nulls in primary or auxiliary columns over sample window, primary-column mean and std are in expected ranges (from the Rev-1 spec).
- [ ] **Step 2: Run the test.** First run will likely reveal integration bugs.
- [ ] **Step 3: Fix integration issues.** Dispatch Data Engineer to address any panel-load failures; do not modify Rev-4 artifacts. **Escalation branch (Rev-2, PM F1):** if the failure implicates a Rev-4 decision (e.g., date-column join semantics, a Rev-4 decision-hash invariant changes shape, or a Rev-4 artifact must be re-emitted), **halt** and escalate to the user for scope-expansion approval rather than silently amending Rev-4. The scripts-only allow-list (rule #4) already forbids this; the escalation path is the documented exit.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(remittance): end-to-end panel-load integration test`.

---

## Phase 3 — Notebook Authoring (X-Trio Discipline)

**Phase-3 protocol note (Rev-2, PM F5):** Every Phase-3 authoring task's "nbconvert-execute" step means `subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", <committed-path>, "--ExecutePreprocessor.timeout=1800"])` against the committed notebook path (not a `/tmp` copy), with returncode=0 asserted inline in that task. This is additive to Task 25's end-to-end nbconvert guards; the inline per-task execution catches errors trio-locally so Task 25 is a final belt-and-braces layer, not the first-responder.

**Intra-phase review gates (Rev-2, PM B1):** After each notebook is fully authored, a three-way implementation-review trio (Code Reviewer + Reality Checker + Senior Developer, per memory `feedback_implementation_review_agents.md`) executes against just that notebook before the next notebook begins. These gates are Tasks 18a (after NB1), 21c (after NB2), 24c (after NB3). Rev-4's successful shipping relied on this pattern; omitting it risks systemic defects compounding across notebooks.

### Task 16: NB1 §1 — Panel load + fingerprint (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb1_panel_fingerprint.json`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section1.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §1 exists with the standard X-trio layout; fingerprint JSON is emitted atomically with extended decision-hash, Rev-4-base-hash, timestamp, package versions, auxiliary-column hashes.
- [ ] **Step 2:** Dispatch Analytics Reporter with the X-trio protocol. The agent authors trio 1 (panel load) + trio 2 (fingerprint emission) and HALTs after each trio. Foreground reviews between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline (see Phase-3 protocol note); assert returncode=0.
- [ ] **Step 4: Run the failing test;** confirm it passes.
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §1 panel load + fingerprint emission`.

### Task 17a: NB1 §2 — Decisions 1-4 (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section2_d1_4.py`

**Rev-2 context:** Rev-1 Task 17 packed 12 decisions into a single subagent dispatch. Rev-4 precedent (CPI Tasks 9-12) split decisions across 4 tasks of ~3 decisions each. At ~5 min foreground review per trio, 12 trios = ~60 min serial — violates subagent-driven-development atomicity. Splitting into 17a/17b/17c × 4 decisions each keeps each task under the 30-min granularity ceiling.

- [ ] **Step 1: Write the failing test.** Assert NB1 §2 contains `LockedDecisions`-equivalent entries for Decisions 1-4 (sample window preserved; LHS unchanged; primary RHS = remittance-AR(1) surprise; 6 controls preserved — whichever four the Rev-1 spec assigns to this batch). Each decision has a 4-part citation block.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio protocol — 4 trios (one per decision). HALT after each.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline (see Phase-3 protocol note above); assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §2 — Decisions 1-4 for remittance-surprise`.

### Task 17b: NB1 §2 — Decisions 5-8 (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section2_d5_8.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §2 contains Decisions 5-8 entries with 4-part citation blocks.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio — 4 trios. HALT after each.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §2 — Decisions 5-8 for remittance-surprise`.

### Task 17c: NB1 §2 — Decisions 9-12 (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section2_d9_12.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §2 contains Decisions 9-12 entries (frequency, collinearity, stationarity, plus whichever fourth decision the Rev-1 spec assigns) with 4-part citation blocks. Cross-assert the full §2 contains exactly 12 decisions (Tasks 17a + 17b + 17c summed).
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio — 4 trios. HALT after each.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §2 — Decisions 9-12 for remittance-surprise; full 12-decision block complete`.

### Task 18: NB1 §3-5 — EDA plots + diagnostics + panel validation (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/01_data_eda.ipynb`
- Create: figures under `contracts/notebooks/fx_vol_remittance_surprise/Colombia/figures/`
- Test: `contracts/scripts/tests/remittance/test_nb1_remittance_section3_5.py`

- [ ] **Step 1: Write the failing test.** Assert NB1 §3 (univariate EDA of remittance surprise + LHS + controls), §4 (bivariate co-movement diagnostics), §5 (stationarity tests per Rev-1 spec — ADF / KPSS / Phillips-Perron as pre-committed). Each section has ≥2 trios; each code cell executes; each figure is emitted to `figures/`.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; HALT between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB1 notebook inline (see Phase-3 protocol note); assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB1 §3-5 — EDA + diagnostics + stationarity tests`.

### Task 18a: Three-way review gate — NB1 complete (Rev-2 insert per PM B1)

**Subagent:** three parallel dispatches (Code Reviewer + Reality Checker + Senior Developer) per memory rule `feedback_implementation_review_agents.md`.

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-nb1-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb1-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb1-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against just NB1 (Tasks 16–18) + all NB1-derived artifacts (`nb1_panel_fingerprint.json`, §3-5 figures, Tasks 16-18 tests). Per-reviewer focus (Rev-2, CR F4):
  - **Code Reviewer:** file-path correctness, additive-only extension of Rev-4 `cleaning.py`, test coverage of NB1 §1 and §2 (12 decisions split across 17a/17b/17c), decision-hash invariant preservation.
  - **Reality Checker:** verify panel row_count = 947, verify each of the 12 Decisions' citation blocks points to existing references, audit stationarity-test outcomes against the Rev-1 spec's pre-committed expectations.
  - **Senior Developer:** architectural coherence — is NB1 a clean consumer of the `cleaning.py` extension layer, or are there private imports bypassing the intended API? Are the V1/V2/V3 dataclass extensions orthogonal and additive?
  None of the three reviewers sees the others' reports.
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix (subject to the 3-cycle cap in rule #13); re-dispatch the offending reviewer. Do not begin Task 19 until NB1 gate PASSes.
- [ ] **Step 5: Commit** the three scratch reports with message `review(remittance): NB1 three-way review gate (Tasks 16-18)`.

### Task 19: NB2 §1-3 — OLS ladder (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section1_3.py`

- [ ] **Step 1: Write the failing test.** Assert NB2 §1 (sample + panel verification), §2 (pre-fit diagnostics per Rev-1 spec), §3 (OLS ladder — base, +primary-surprise, +controls, final model) exist and execute cleanly. Final model coefficient β̂_remittance with HAC SE (kernel + bandwidth from Rev-1 spec) is emitted.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; one trio per sub-step.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §1-3 — OLS ladder with HAC SE per Rev-1 spec`.

### Task 20: NB2 §4-6 — GARCH(1,1)-X co-primary (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section4_6.py`

- [ ] **Step 1: Write the failing test.** Assert §4 (GARCH baseline fit), §5 (GARCH(1,1)-X with remittance-surprise in mean- OR variance-equation per Rev-1 spec), §6 (convergence diagnostics + GARCH-X β̂_remittance emission). `scipy` L-BFGS-B custom likelihood per Rev-4 pattern.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio. Flag convergence-instability handling per Rev-1 spec.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §4-6 — GARCH(1,1)-X co-primary per Rev-1 spec`.

### Task 21a: `build_payload_remittance` helper (Data Engineer; Rev-2 split per CR N5 / PM F2)

**Subagent:** Data Engineer

**Files:**
- Modify: `contracts/scripts/nb2_serialize.py` (additive — `build_payload_remittance`)
- Test: `contracts/scripts/tests/remittance/test_nb2_serialize_remittance.py`

**Rev-2 context:** Rev-1 Task 21 packed Analytics Reporter notebook authoring AND a Data Engineer helper into one task, violating the "one subagent per task" rule (CR N5, PM F2). Splitting 21a (DE helper) and 21b/c (AR notebook + gate) preserves subagent atomicity and lets the helper test run before the notebook depends on it.

- [ ] **Step 1: Write the failing test.** Assert `build_payload_remittance(point_results, reconcile_results, full_fit) → PayloadRemittance` exists, produces a JSON-serializable dict for `nb2_params_point.json` + `nb2_reconcile.json`, preserves atomic-emission semantics (stage→fsync→rename) shared with the Rev-4 helper.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** as an additive function in `nb2_serialize.py`. Do not modify the existing Rev-4 CPI-payload function.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): nb2_serialize.build_payload_remittance helper`.

### Task 21b: NB2 §7-9 — T3b gate + reconciliation + economic magnitude (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section7_9.py`

- [ ] **Step 1: Write the failing test.** Assert §7 (T3b gate per Rev-1 spec — one-sided or two-sided per sign prior; MDES check), §8 (reconciliation rule per Rev-1 spec — directional or numerical-intersection between OLS and GARCH-X; the rule chosen under heteroskedasticity per Rev-1 row 9 of the resolution matrix), §9 (economic-magnitude interpretation — basis-points-of-vol magnitude translated at the Rev-1 spec's pricing anchors). Each section has trio discipline.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; HALT between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §7-9 — T3b gate + reconciliation + economic magnitude`.

### Task 21c: NB2 §10-12 — sensitivity rows + atomic emission (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb2_params_point.json`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb2_reconcile.json`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb2_params_full.pkl`
- Test: `contracts/scripts/tests/remittance/test_nb2_remittance_section10_12.py`

- [ ] **Step 1: Write the failing test.** Assert §10 (alternate-LHS sensitivity row; Dec-Jan seasonality check — both specified by the Rev-1 spec resolution matrix; these are pre-registered sensitivities, not post-hoc spotlights), §11 (quarterly corridor reconstruction sensitivity — or the documented-gap placeholder path from Task 14), §12 (atomic JSON + pickle emission via `nb2_serialize.build_payload_remittance` from Task 21a). Integration-verify atomic emission (stage→fsync→rename). All three artifact files are emitted byte-deterministically.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; HALT between trios.
- [ ] **Step 3: nbconvert-execute** the committed NB2 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB2 §10-12 — sensitivity rows + atomic emission`.

### Task 21d: Three-way review gate — NB2 complete (Rev-2 insert per PM B1)

**Subagent:** three parallel dispatches (Code Reviewer + Reality Checker + Senior Developer).

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-nb2-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb2-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb2-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against NB2 (Tasks 19–21c) + NB2 artifacts. Per-reviewer focus:
  - **Code Reviewer:** additive-only `nb2_serialize.py` extension, HAC kernel/bandwidth correctness per Rev-1 spec row, GARCH-X convergence handling, atomic-emission test coverage.
  - **Reality Checker:** verify each cell's citation block references existing papers/data; independently recompute β̂_remittance point estimate (even roughly) to spot a missing multiplier or sign-flip; confirm reconciliation rule matches Rev-1 spec row 9.
  - **Senior Developer:** architectural coherence — is the GARCH-X fit layered on top of the OLS ladder correctly? Is the atomic emission separable from the authoring layer so Task 24a/b can reuse the payload unchanged?
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix (3-cycle cap); re-dispatch the offending reviewer. Do not begin Task 22a until NB2 gate PASSes.
- [ ] **Step 5: Commit** the three scratch reports with message `review(remittance): NB2 three-way review gate (Tasks 19-21c)`.

### Task 22a: NB3 §1-3 — pre-flight + T1 exogeneity + T2 Levene + T3a replay (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section1_3.py`

**Rev-2 context:** Rev-1 Task 22 packed 7 tests into one subagent dispatch (7 trios serial). Splitting into 22a (T1-T3a) + 22b (T3b + T4-T7) keeps each under the atomicity ceiling and matches Rev-4's narrower packing.

- [ ] **Step 1 (Rev-2 tightened — CR F3):** Write the failing test. Assert NB3 §1 (pre-flight — unpack NB2 PKL into bare-name variables per the Rev-4 silent-test-pass lesson; assert each bare-name variable is of the expected type and non-NaN), §2 (T1 exogeneity), §3 (T2 Levene + T3a stat-significance replay). Each test emits a verdict dict compatible with `gate_aggregate.build_gate_verdict`. **CR F3 fix — numerical assertions mandatory:** for each test the test spec asserts at least one numerical field, not only that the verdict-dict key exists:
  - T1: F-statistic is finite, > 0, and within ±0.1 of an independently pre-computed expected value from the Rev-1 spec's pre-fit-diagnostic block.
  - T2: Levene p-value lies in `[0.0, 1.0]` and is within ±0.05 of the independently pre-computed expected value.
  - T3a: |t-statistic| > 0 and the reported two-sided p-value matches within ±1e-6 a scipy-computed recomputation from the emitted β̂ and SE.
  These assertions guard against silent-test-pass pattern #1 — "test asserts a dict exists, not that its values are numerically correct." This pattern caused 3 of 5 CPI silent-test-pass incidents.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; one trio per test (pre-flight, T1, T2, T3a) = 4 trios.
- [ ] **Step 3: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB3 §1-3 — pre-flight + T1 + T2 + T3a with numerical assertions`.

### Task 22b: NB3 §4-6 — T3b gate replay + T4-T7 (Analytics Reporter, X-trio; Rev-2 split per PM B3)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section4_6.py`

- [ ] **Step 1 (Rev-2 tightened — CR F3):** Write the failing test. Assert NB3 §4 (T3b gate replay — the NB2 gate-stat is re-evaluated in NB3 and matches within tolerance; each arm of the gate has a numerical MDES-pass or MDES-fail flag with the underlying ES value asserted), §5 (T4 residual autocorrelation — Ljung-Box Q statistic is finite, >0, with p-value in `[0, 1]` and a reported lag matching Rev-1 spec), §6 (T5 Normal/robustness — Jarque-Bera stat finite, ≥0, p-value in `[0, 1]`; T6 heteroscedasticity — White/Breusch-Pagan stat finite, ≥0, p-value in `[0, 1]`; T7 specification-curve — at least N=k curves emitted where k is the Rev-1 spec's committed count, each with a numerical β̂ value). No test may assert merely "key exists"; each assertion must pin at least one numerical field.
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio; one trio per test (T3b, T4, T5+T6, T7) = 4 trios.
- [ ] **Step 3: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(remittance): NB3 §4-6 — T3b replay + T4-T7 with numerical assertions`.

### Task 23: NB3 §7-9 — Forest plot + anti-fishing halt + material-mover spotlight (Analytics Reporter, X-trio)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/figures/forest_plot.png`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb3_forest.json` (Rev-2 add per CR F1; design-doc §Deliverables item 5)
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/nb3_sensitivity_table.json` (Rev-2 add per CR F1; design-doc §Deliverables item 5)
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section7_9.py`

- [ ] **Step 1 (Rev 3.1 amended — CR-B1): Write the failing test.** Assert §7 (all primary + sensitivity rows: primary, alternate-LHS, **A1-R-bridge** (BanRep-quarterly AR(1)-surprise rebased-to-weekly — the validation-row S14 from Rev-1.1 §6; renamed from the obsolete "A1-R monthly" per CR-B1 since the monthly cadence is no longer a pre-committed sensitivity under Rev 3.1), release-day-only, pre/post-2015 Quandt-Andrews-windowed, Petro-Trump event-dummied, quarterly corridor reconstruction — or the documented-gap placeholder if Task 14 Step 0 decided no-recipe; plus any Rev-1.1-spec additions). Assert `nb3_forest.json` is emitted with one row per sensitivity (β̂, SE, CI bounds, row label). Assert `nb3_sensitivity_table.json` is emitted with the same rows plus gate-pass/fail flags per row. Assert §8 (forest-plot render at `figures/forest_plot.png`; rows sorted per Rev-1.1 spec). Assert §9 (anti-fishing halt condition — material-mover §9 spotlight is emitted ONLY if primary T3b PASSes; otherwise §9 cells emit empty placeholders referencing the design doc's anti-fishing framing and the §8 sensitivity-row pre-registration; A1-R-bridge + release-day-excluded rows are preserved as pre-registered sensitivities, not post-hoc rescue claims).
- [ ] **Step 2:** Dispatch Analytics Reporter with X-trio.
- [ ] **Step 3: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 4: Run test and confirm pass.** Verify `nb3_forest.json` + `nb3_sensitivity_table.json` are byte-deterministic across two runs.
- [ ] **Step 5: Commit** with message `feat(remittance): NB3 §7-9 — forest + anti-fishing halt + nb3_forest.json + nb3_sensitivity_table.json`.

### Task 24a: NB3 §10 — Gate aggregation (Data Engineer helper + Analytics Reporter cells; Rev-2 split per CR N5 / PM F2)

**Subagent:** Data Engineer (for `build_gate_verdict_remittance` + `render_readme` helper extension); then Analytics Reporter (for notebook §10 cells). Split across sub-dispatches per the "one-subagent-per-task" rule; the DE work and its test complete before AR authors cells against the function.

**Files:**
- Modify: `contracts/scripts/gate_aggregate.py` (additive — `build_gate_verdict_remittance`)
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/estimates/gate_verdict_remittance.json`
- Test: `contracts/scripts/tests/remittance/test_gate_aggregate_remittance.py`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section10.py`

- [ ] **Step 1a (DE sub-task):** Write the failing test asserting `gate_aggregate.build_gate_verdict_remittance(nb2_point, nb2_reconcile, nb3_tests, nb3_sensitivity) → dict` exists; produces a verdict payload with fields (primary-verdict, reconciliation-outcome, T1-T7 sub-verdicts, sensitivity rows, anti-fishing-halt flag); uses atomic emission via `write_gate_verdict_atomic`.
- [ ] **Step 1b (DE sub-task):** Run test, implement helper, confirm pass.
- [ ] **Step 2: Write the NB3 §10 failing test.** Assert §10 calls the Task-24a helper and emits `gate_verdict_remittance.json` byte-identically across two runs (determinism check; matches Rev-4 `_FINGERPRINT_NONDET_KEYS` allowlist pattern).
- [ ] **Step 3:** Dispatch Analytics Reporter with X-trio for §10 cells.
- [ ] **Step 4: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0. Verify `gate_verdict_remittance.json` is emitted.
- [ ] **Step 5: Run test and confirm pass** (byte-identical across two runs).
- [ ] **Step 6: Commit** with message `feat(remittance): NB3 §10 — build_gate_verdict_remittance helper + gate emission`.

### Task 24b: NB3 §11 — README auto-render (Data Engineer helper + Analytics Reporter cells; Rev-2 split per CR N5 / PM F2)

**Subagent:** Data Engineer (for `render_readme` remittance-template-selector extension); then Analytics Reporter (for notebook §11 cells).

**Files:**
- Modify: `contracts/scripts/render_readme.py` (additive — remittance template selector)
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Modify: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/README.md` (overwrites Task 8 placeholder — verified non-placeholder by Task 24b test per PM N3)
- Test: `contracts/scripts/tests/remittance/test_render_readme_remittance.py`
- Test: `contracts/scripts/tests/remittance/test_nb3_remittance_section11.py`

- [ ] **Step 1a (DE sub-task):** Write the failing test asserting `render_readme(gate_verdict_remittance, template_path=..._readme_template.md.j2)` returns a byte-identical rendered string across two calls (pure function; Jinja2 deterministic).
- [ ] **Step 1b (DE sub-task):** Run test, implement template-selector extension, confirm pass.
- [ ] **Step 2: Write the NB3 §11 failing test.** Assert §11 invokes `render_readme` and writes `README.md` byte-identically across two runs. Add a PM-N3 guard: assert the rendered README does NOT contain the Task-8 placeholder sentinel (e.g., assert the rendered README length > a minimum threshold and does not contain a known placeholder substring).
- [ ] **Step 3:** Dispatch Analytics Reporter with X-trio for §11 cells.
- [ ] **Step 4: nbconvert-execute** the committed NB3 notebook inline; assert returncode=0.
- [ ] **Step 5: Run test and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(remittance): NB3 §11 — README auto-render; verified non-placeholder`.

### Task 24c: Three-way review gate — NB3 complete (Rev-2 insert per PM B1)

**Subagent:** three parallel dispatches (Code Reviewer + Reality Checker + Senior Developer).

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-nb3-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb3-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-nb3-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against NB3 (Tasks 22a–24b) + NB3 artifacts. Per-reviewer focus:
  - **Code Reviewer:** numerical-assertion coverage in Tasks 22a/22b (no test asserts only dict-key existence); CR F1 deliverables (`nb3_forest.json`, `nb3_sensitivity_table.json`) present; atomic emission of `gate_verdict_remittance.json`; template-selector cleanly additive.
  - **Reality Checker:** audit the forest-plot row labels against the Rev-1 spec's pre-committed sensitivity list (no rows silently added, none silently dropped); verify A1-R renaming is consistent everywhere; audit the anti-fishing halt behavior under the (hypothetical) T3b-FAIL branch.
  - **Senior Developer:** architectural coherence — is the gate-aggregation layer a pure function of NB2+NB3 artifacts? Is the README auto-render deterministic and reproducible from committed inputs only?
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix (3-cycle cap); re-dispatch the offending reviewer. Do not begin Task 25 until NB3 gate PASSes.
- [ ] **Step 5: Commit** the three scratch reports with message `review(remittance): NB3 three-way review gate (Tasks 22a-24b)`.

---

## Phase 4 — Integration Tests + Review + Close

### Task 25: Three nbconvert-execute integration-test guards

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/remittance/test_nb1_remittance_end_to_end_execution.py`
- Create: `contracts/scripts/tests/remittance/test_nb2_remittance_end_to_end_execution.py`
- Create: `contracts/scripts/tests/remittance/test_nb3_remittance_end_to_end_execution.py`

- [ ] **Step 1: Write three failing tests.** Each test `subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute", <path>, "--output", "/tmp/<name>", "--ExecutePreprocessor.timeout=1800"])` and asserts returncode=0. Tests are guards against the silent-test-pass pattern (5 instances catalogued in the CPI exercise per memory `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md:68`). They are not skipped in CI. **Rev-2 explicit coverage per RC F3:** the three nbconvert guards catch pattern-1 (whole-notebook-execution failure) directly. The other four patterns are covered as follows: pattern-2 (prose-vs-code drift) caught by the CR F3 numerical assertions in Tasks 22a/22b; pattern-3 (zero-assertion tests) forbidden by rule #1 strict-TDD + each Phase-3 task's Step-1 test-assertion list; pattern-4 (silent-column-drift) caught by Task 12/13/14 decision-hash-extension invariants; pattern-5 (non-deterministic emission) caught by Task 26 byte-identical regression. Task 25's own test-spec header block enumerates these five patterns so a future reader can verdict whether coverage remains complete.
- [ ] **Step 2: Run and confirm failure** (tests will fail initially because `/tmp/<name>` doesn't exist or execution has a bug).
- [ ] **Step 3: Fix any end-to-end execution bug** that surfaces. Do not suppress the test.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(remittance): 3-notebook nbconvert-execute integration guards`.

### Task 26: End-to-end regression test (determinism + idempotency)

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/remittance/test_end_to_end_determinism.py`

- [ ] **Step 1: Write the failing test.** Run all three notebooks end-to-end twice, store all output artifacts in two scratch dirs, diff them. Assert byte-identical except for a frozen allowlist of non-deterministic keys (e.g., `{"generated_at"}` per Rev-4 `_FINGERPRINT_NONDET_KEYS` pattern). Include the Rev-4 mutation-test pattern: inject 5 known-wrong changes and assert the regression test catches each.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Iterate until determinism holds** for all artifacts.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(remittance): end-to-end determinism + mutation-catch gauntlet`.

### Task 27: Model QA Specialist econometric calibration review

**Subagent:** Model QA Specialist

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-model-qa.md`

- [ ] **Step 1:** Dispatch Model QA Specialist with the three notebooks (post-Phase-3), the Rev-1 spec, and the gate_verdict_remittance.json as inputs. Audit: did the implementation faithfully execute the Rev-1 spec's 13 mandatory choices? Are econometric calibrations (HAC bandwidth, GARCH-X convergence, MDES verification, Quandt-Andrews test) correctly executed?
- [ ] **Step 2:** Verify report landed.
- [ ] **Step 3:** Log verdict + findings.
- [ ] **Step 4:** If BLOCK findings: dispatch Data Engineer to fix; re-dispatch Model QA for re-verification. Iterate to PASS, bounded by rule #13's 3-cycle cap — after the third failed Model QA cycle, halt and escalate to the user.
- [ ] **Step 5: Commit** with message `review(remittance): Model QA implementation review (pass N)`.

### Task 28: Three-way implementation review (Code Reviewer + Reality Checker + Senior Developer)

**Subagent:** three parallel dispatches per memory rule `feedback_implementation_review_agents.md`.

**Files:**
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-code-reviewer.md`
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-reality-checker.md`
- Create: `contracts/.scratch/2026-04-20-remittance-impl-review-senior-developer.md`

- [ ] **Step 1:** Dispatch three reviewers in parallel against the full Phase-A.0 implementation (notebooks + scripts + tests + artifacts). Each receives the design doc + Rev-1 spec + fix-log + full implementation tree. None knows about the others. **Per-reviewer focus (Rev-2, CR F4):**
  - **Code Reviewer:** file-path and dependency correctness across all 38 tasks; allow-list compliance (rule #4 + its memory-file exception); scripts-only scope respected; no Solidity / foundry.toml / src/ touched; test-file naming convention honored (rule #11 with its infra-test exception); atomic-emission discipline on all JSON/pickle artifacts; decision-hash invariant holds end-to-end; all per-notebook intra-phase gates (Tasks 18a, 21d, 24c) left no unresolved BLOCKs.
  - **Reality Checker:** every cited reference in every notebook's 4-part citation blocks points to an existing paper/corpus file; every numerical assertion in tests can be independently recomputed by hand or a small scipy call; the Rev-4 frozen-panel invariants (row-count 947, base decision-hash) hold byte-exact after the remittance extension; anti-fishing framing language in notebook headers and commit messages is consistent; the gate verdict (PASS/FAIL) and its supporting statistics are internally consistent (β̂, SE, CI, p-value all agree arithmetically).
  - **Senior Developer:** architectural coherence — is the remittance pipeline a clean additive layer atop Rev-4, or are there private imports or hidden coupling? Is the V1/V2/V3 dataclass extension pattern applied consistently? Does the gate-aggregation + README-render layer reproduce byte-identically from committed inputs only? Could a Phase-A.1 downstream exercise reuse the remittance extension pattern without copy-paste?
- [ ] **Step 2:** Verify all three reports landed.
- [ ] **Step 3:** Log verdicts + itemize findings across severity tiers.
- [ ] **Step 4: Commit** the three scratch reports with message `review(remittance): 3-way implementation review reports`.

### Task 29: Data Engineer applies impl-review fixes

**Subagent:** Data Engineer (per memory rule `feedback_implementation_review_agents.md`: Data Engineer fixes)

**Files:**
- Modify: as-needed per review findings

- [ ] **Step 1:** Dispatch Data Engineer with all three review reports. Apply BLOCK fixes first, FLAGs second, NITs if time permits.
- [ ] **Step 2:** Re-run the full test suite + nbconvert integration guards + determinism test.
- [ ] **Step 3:** If any BLOCK was deferred, halt and re-invoke the specific reviewer. Bound by rule #13's 3-cycle cap across Task 28 ↔ Task 29 loops; after the third failed cycle, halt and escalate.
- [ ] **Step 4: Commit** with message `fix(remittance): apply 3-way implementation review fixes`.

### Task 30a: Completion memory (Technical Writer; Rev-2 split per PM F6)

**Subagent:** Technical Writer

**Files:**
- Create: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_remittance_surprise_exercise_complete.md` (Rev-4 precedent: CPI completion memory lives at same path prefix per `project_fx_vol_cpi_notebook_complete.md`; allow-list exception codified in rule #4 Rev-2 extension)

- [ ] **Step 1 (Rev 3.1 amended — CR-B1):** Dispatch Technical Writer to author the completion memory containing: verdict digest (PASS or FAIL), β̂_remittance + SE + CI, all test verdicts (T1-T7), reconciliation outcome, all sensitivity-row outcomes (primary, alternate-LHS, **A1-R-bridge** (BanRep-quarterly AR(1)-surprise rebased-to-weekly, replacing the obsolete "A1-R monthly" per Rev 3.1 CR-B1), release-day-only, pre/post-2015 Quandt-Andrews, Petro-Trump event-dummied, quarterly corridor reconstruction or its documented-gap placeholder), anti-fishing framing re-asserted (Phase-A.0 is a distinct pre-commitment on the remittance external-inflow channel via the on-chain COPM+cCOP rail, not a rescue of the CPI-FAIL; the Rev-3 methodology escalation is pre-commitment-preserving per Rev-3.1 Rule 14), pointers to all 11 artifacts (`nb1_panel_fingerprint.json`, `nb2_params_point.json`, `nb2_reconcile.json`, `nb2_params_full.pkl`, `nb3_forest.json`, `nb3_sensitivity_table.json`, `gate_verdict_remittance.json`, `README.md`, `forest_plot.png`, plus MPR-source provenance, bridge-validation scratch note from Task 11.C, and corridor-reconstruction-recipe scratch notes), lessons learned, Phase-A.1 go/no-go recommendation conditional on verdict.
- [ ] **Step 2:** Verify the memory file landed at the expected path.
- [ ] **Step 3: Commit** with message `docs(remittance): Phase-A.0 completion memory authored`.

### Task 30b: MEMORY.md index + design-doc completed-status footer (Technical Writer; Rev-2 split per PM F6)

**Subagent:** Technical Writer

**Files:**
- Modify: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/MEMORY.md` (one-line pointer to Task 30a memory; precedent: `project_fx_vol_cpi_notebook_complete.md` is indexed similarly)
- Modify: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md` (append "completed YYYY-MM-DD / verdict: {PASS|FAIL}" status footer; precedent: Rev-4 design doc footer pattern)

- [ ] **Step 1:** Technical Writer appends the completion pointer to `MEMORY.md` (one line, matching the Rev-4 CPI pointer format).
- [ ] **Step 2:** Technical Writer appends the completed-status footer to the design doc.
- [ ] **Step 3: Commit** with message `docs(remittance): MEMORY.md index + design-doc completed-status footer`.

### Task 30c: Final test run + push (Rev-2 split per PM F6 and N4)

**Subagent:** Data Engineer (final test run); foreground (push).

**Files:** no file modifications; verification + push only.

- [ ] **Step 1:** Data Engineer runs the full test + integration + determinism suite one final time to confirm clean state.
- [ ] **Step 2 (Rev-2 disambiguated — PM N4):** Verify clean `git status` on branch `phase0-vb-mvp`; push the branch to `origin` (JMSBPP remote) per memory rule `feedback_push_origin_not_upstream.md` — **NOT** `upstream` (wvs-finance). "Merge phase0-vb-mvp status" in the Rev-1 plan was ambiguous; Rev-2 clarifies that nothing is merged into `main` at this task — the branch is pushed and the user decides merge/PR disposition separately per memory rule `feedback_no_merge_without_approval.md`.
- [ ] **Step 3: Commit** (if test-run or push produced trivial follow-on edits) with message `chore(remittance): Phase-A.0 complete, verdict={PASS|FAIL}, push to origin` (CR N2 — replaced the non-conventional `close(...)` prefix with `chore(...)`).

---

## Spec-coverage self-check (Rev-2 updated for split task numbers; Rev-5.3 task-count reconciliation appended below)

**Rev-5.3 task-count reconciliation (PM-FF-2; DEFERRED-URGENT row-by-row refresh):** active task count under Rev-5.3 is **63** (Phase 0=5 + Phase 1=5 + Phase 2a=1 + Phase 1.5=5 + Phase 1.5.5 active=14 [11.F + 11.K + 11.L + 11.M + 11.M.5 + 11.M.6 + 11.N + 11.N.1 + 11.N.1b + 11.N.2b.1 + 11.N.2b.2 + 11.N.2c + 11.N.2d + 11.N.2d.1] + Phase 2b=4 + Phase 3=18 + Phase 4=8 = **60**; plus 4 retired-as-audit headers (11.G/11.H/11.I/11.J) = **64 total headers**). The discrepancy between the 60-active-task arithmetic and the Rev-5.3 status banner's claim of 63 reflects accounting drift accumulated across revisions; the status banner's 63 has been the canonical Rev-5.3 figure since the brainstorm-fold and is preserved as such pending a future row-by-row rebuild of the spec-coverage matrix below. The per-design-input coverage list below remains anchored to the original 13-input Phase-0 enumeration and references pre-Rev-5.3 tasks (11.D, 11.A, etc.); under Rev-5.3 the operative tasks are 11.N.2c (MDES, formulation pin), 11.N.2d (Y₃ construction; vintage discipline for equity/bond/WC-CPI), and 11.O Step 1 (sign prior, gate test). Row-by-row refresh deferred to Rev-5.4 per amendment-rider A8.

The design doc's Phase-0 mandatory-inputs enumeration has 13 items. Each is covered by Task 1's 13-input resolution matrix (Rev-2 tightened) and operationally by downstream tasks:

- Sign prior → Task 1 Step 4 + Task 21b §7 (T3b gate, one-sided or two-sided per sign prior)
- MDES → Task 1 Step 4 + Task 11.D Step 1 (Rev-1.1 §4.5 re-computation at N=95) + Task 22b §4 (numerical MDES assertion in T3b replay) + Task 27 (Model QA audit)
- Alternate-LHS sensitivity → Task 21c §10 (emission) + Task 23 §7 (forest-plot row)
- HAC kernel → Task 19 §3 + Task 21d (NB2 review-gate CR focus) + Task 27
- Andrews bandwidth → Task 19 §3 + Task 11.D Step 1 (Rev-1.1 §12 row 5 patch at N=95)
- Interpolation side → Rev 3.1 superseded for primary X (Task 11.D §12 row 6 marks as "no longer applies"); retained for validation-row S14 quarterly AR(1) path via Task 10
- AR order → Task 10 (validation-row S14 quarterly path only under Rev 3.1); Task 11.D Step 1 §12 row 7 patch
- Vintage discipline → Task 11 (quarterly BanRep MPR-vintage-date column, now demoted to validation-row S14) + Task 11.A (daily on-chain no-revision vintage for primary X) + Task 11.D Step 1 §12 row 8 patch
- Reconciliation rule under heteroskedasticity → Task 21b §8 (directional or numerical-intersection per Rev-1.1 spec row 9)
- Quandt-Andrews → Task 23 §7 (pre/post-2015 row)
- GARCH parametrization → Task 20 §5
- Dec-Jan seasonality → Task 21c §10 (pre-registered sensitivity row alongside alternate-LHS)
- Event-study co-primary → Task 23 §7-9 (Petro-Trump row, anti-fishing-halt-conditional spotlight)

All 13 covered across Phases 0/1.5/2/3/4. Phase 1.5 (Tasks 11.D Step 1) is the Rev-3.1 entry point for rows 5/6/7/8 re-resolution under the daily-native primary X.

**Task 21c packing note (Rev-2, CR N4 addressed):** Rev-1 §9 originally hosted both alternate-LHS and Dec-Jan seasonality in the same notebook section. Rev-2 lifts both into Task 21c §10 (sensitivity-rows batch) with separate trios so each is an independently auditable entry. The forest-plot row labels in Task 23 §7 then render these as distinct entries.

Anti-fishing framing appears in Task 8 (notebook headers), Task 11.D (Rev-1.1 supersedes-banner explicitly frames the methodology escalation as data-reality-driven, not null-result-driven), Task 11.E (three-way review of the Rev-1.1 patch guards against back-door unreviewed-spec execution), Tasks 22b-23 (NB3 §9 halt condition), Task 30a (completion memory). Three-way reviews at Phase 0 (Tasks 2-4 spec review CR+RC+TW per `feedback_three_way_review.md`), Phase 1.5 (Task 11.E spec-patch review CR+RC+TW, Rev-3 insert; Rev-3.1 cycle-cap-bounded per Rule 13 + Task 11.E Step 3 boundary definition), Phase 3 intra-phase gates (Tasks 18a, 21d, 24c CR+RC+SD per `feedback_implementation_review_agents.md`, Rev-2 inserts), Phase 4 (Tasks 27-28 impl review).

Additive-only scope: every Phase-1 task is additive to Rev-4 pipeline; Phase-1.5 tasks are additive to Phase-1 (new scripts, new data fixtures, new notebook 0B, spec-patch only to already-additive spec file); decision-hash extension preserves Rev-4 hash (Task 12 test) and extends in Tasks 13 (aux columns including `a1r_quarterly_rebase_bridge` per Rev-3.1 rename) + 14 (corridor column or placeholder).

**Total task count (Rev-3.1): 46.**
- Phase 0: Tasks 1-5 (5 tasks; unchanged from Rev-1)
- Phase 1: Tasks 6-10 (5 tasks; unchanged)
- Phase 1.5 (Rev-3.1 promoted per PM-F2): Tasks 11.A, 11.B, 11.C, 11.D, 11.E (**5 tasks**; Rev-3 daily-native middle-plan inserts, promoted out of Phase 2 in Rev-3.1 to form a standalone Data-Bridge sub-phase with clean gate boundaries)
- Phase 2: Tasks 11 (post-execution history), 12, 13, 14, 15 (**5 tasks**; Rev-2 shape restored after Rev-3.1 Phase-1.5 promotion)
- Phase 3: Tasks 16, 17a, 17b, 17c, 18, 18a, 19, 20, 21a, 21b, 21c, 21d, 22a, 22b, 23, 24a, 24b, 24c (18 tasks; unchanged from Rev-2)
- Phase 4: Tasks 25, 26, 27, 28, 29, 30a, 30b, 30c (8 tasks; unchanged from Rev-2)

Sum check: 5 + 5 + 5 + 5 + 18 + 8 = 46. Same task count as Rev-3; only the phase-boundary rearrangement changed in Rev-3.1.

**Growth narrative (Rev 3.1 re-baselined per PM-N1):** Rev-4 CPI shipped with 33 tasks as counted in `CLAUDE.md` (36 with letter-suffix expansions shown in the plan body). Rev-2 remittance was 41 tasks. Rev-3 remittance is 46 tasks — 5 tasks higher than Rev-2, reflecting the Rev-3 methodology-escalation insert (Tasks 11.A–11.E responding to the Task-11 quarterly-only BanRep finding). Rev-3.1 preserves the 46-task count and rearranges the phase structure for clarity. Growth vs Rev-1's nominal 30 reflects: (a) 3 intra-phase review gates (Rev-4 parity per PM B1), (b) split-for-atomicity of four over-packed authoring tasks (PM B3), (c) helper+author separation for dual-subagent tasks (CR N5 / PM F2), (d) completion unbundling (PM F6), (e) Rev-3 daily-native methodology-escalation insert (5 tasks).

---

## Execution handoff

**Plan complete and saved to `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. This matches the Rev-4 CPI plan's successful execution pattern.
2. **Inline Execution** — Execute tasks in this session using `executing-plans`, batch with checkpoints.

Which approach?

---

## CORRECTIONS — Rev-5.3.2 (2026-04-25, user-approved disposition path ζ)

**Trigger.** Anti-fishing pathological-HALT at Task 11.O scope: the primary X_d × Y₃ joint coverage measured **56 nonzero weeks** for `proxy_kind = "carbon_basket_user_volume_usd"` against the pre-committed `N_MIN = 75` (Rev-5.3.1 path α value, commit `7afcd2ad6`). Running 11.O at N=56 without an explicit pre-commitment update would constitute silent threshold tuning — the exact failure mode the `feedback_pathological_halt_anti_fishing_checkpoint` discipline forbids. Per protocol (HALT → disposition memo → user-enumerated pivot → CORRECTIONS block → post-hoc 3-way review), the orchestrator authored the disposition memo at `contracts/.scratch/2026-04-25-y3-coverage-halt-disposition.md` enumerating five paths (β / γ / δ / ε / ζ); user selected **path ζ** (γ panel-window swap + δ CPI-source upgrade for both BR and CO) as the only disposition that has any plausible path to recovering `N_MIN = 75` without further relaxation. This Rev-5.3.2 block is the user-approved CORRECTIONS payload, post-fix-up rewrite per the 3-way review (Reality Checker BLOCK on the original Rev-5.3.2 narrowing of δ to δ-BR-only — see RC review report `contracts/.scratch/2026-04-25-rev532-review-reality-checker.md` and the §"Why ζ" honesty note below). Reference commits: prior HALT memo `cefec08a7`; 11.N.2d completion `765b5e203`; Rev-5.3.1 N_MIN-relaxation correction `7afcd2ad6`.

### Why ζ over the alternatives (succinct)

- **β (further N_MIN relaxation 75 → ≤56):** REJECTED — would compound the Rev-5.3.1 80→75 relaxation into "tune until it passes." Anti-fishing-banned by the discipline that already governs `MDES_SD` and the `MDES_FORMULATION_HASH` (immutable, sha256 = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`). Two relaxations on one plan revision exceed reviewer tolerance.
- **γ alone (window swap only):** RECOVERS coverage from 56 → ~65 weeks; still below `N_MIN = 75` without a second relaxation. Insufficient.
- **δ alone (CPI source upgrade only):** RECOVERS coverage substantially but leaves Aug-2023→Sep-2024 pre-period unused; below the joint-coverage target unless paired with γ.
- **ε (run 11.O at N=56 fully disclosed):** REJECTED — scientific-cost too high; below pre-committed power floor; verdict could only be framed as "directional / inconclusive."
- **ζ (γ + δ-{BR, CO}):** SELECTED — under Rev-5.3.2 (post-fix-up rewrite per RC review) ζ is implemented as `γ + δ-{BR via BCB SGS, CO via the existing DANE table}`; this is the only disposition that has any plausible path to the original Rev-5.3.1 `N_MIN = 75` commitment without further relaxation. **Honesty note:** the projected joint coverage under the documented mix `{EU=Eurostat@2025-12, BR=BCB@2026-03, CO=DANE@2026-03}` is approximately **65 weeks** (RC live-verified at the EU-binding cutoff plus LOCF tail), still **below** the ≥75 gate. The DANE wire-up raises the path-ζ ceiling from 47 → ~65 vs. the gate's 75, but does not by itself clear the gate. The HALT clause at Task 11.N.2d-rev is the protective net for this case: if joint coverage lands < 75 under the actual mix, the orchestrator HALTs to user — never to silent N_MIN drift. Cost: ~1 day of fetcher work (BR + CO wire-up) plus this CORRECTIONS block + 3-way review.

### A. Pre-commitment update — what changes vs. what is preserved

All staleness arithmetic in this section is anchored to the Rev-5.3.2 authoring date **2026-04-25**. "9-month stale" / "2-month stale" / etc. are computed against that date.

| Anchor | Status under Rev-5.3.2 | Source / rationale |
|---|---|---|
| `N_MIN` | **PRESERVED** at `75` | Rev-5.3.1 path α value; no further relaxation under ζ |
| `POWER_MIN` | **PRESERVED** at `0.80` | Rev-4 standard; no change |
| `MDES_SD` | **PRESERVED** at `0.40` | Rev-5.3 v2 fix-pass anchor; no change |
| `MDES_FORMULATION_HASH` | **PRESERVED** byte-exact | sha256 = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (canonical Cohen f²); IMMUTABLE per the §0.3 final-fix-pass anti-fishing guard |
| `PC1_LOADING_FLOOR` | **PRESERVED** at `0.40` | Diagnostic-only threshold; no change |
| Rev-4 `decision_hash` | **PRESERVED** byte-exact | `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` |
| Y₃ design doc §1, §4, §8, §9 | **PRESERVED** byte-exact | Immutable spec at `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` |
| Anti-fishing protocol | **PRESERVED** byte-exact | Halt-disposition-pivot-CORRECTIONS-review chain enforced |
| `PRIMARY_PANEL_START` | **UPDATED** from `date(2024, 9, 1)` → `date(2023, 8, 1)` | The Rev-5.3 v2 fix-pass `SENSITIVITY_PANEL_START` value is **promoted** to primary; ~13 additional months of pre-period folded into the primary panel |
| `PRIMARY_PANEL_END` | **PRESERVED** at `date(2026, 4, 24)` | No change |
| `SENSITIVITY_PANEL_START` semantics | **REFRAMED** | No longer "primary's wider sibling" (γ collapsed it); now functions as an alternative-source single-vendor sensitivity per Task 11.N.2d.1-reframe below |
| BR (Brazil) WC-CPI source | **UPDATED** from IMF IFS via DBnomics → BCB SGS direct API series 433 (IPCA monthly variation %), per the level-series contract consumed by the BR `fetch_country_wc_cpi_components` dispatch | Pre-flight intelligence: IMF IFS is 9-month stale (cutoff 2025-07-01); BCB SGS is 1-month stale (cutoff ≈2026-03); cumulative-index materialization required to satisfy the level-series contract |
| CO (Colombia) WC-CPI source | **UPDATED** from IMF IFS via DBnomics → DANE direct (consume the already-landed `dane_ipc_monthly` DuckDB table) | Pre-flight intelligence (Reality Checker live verification, 2026-04-25): `dane_ipc_monthly` is already populated in the canonical structural-econ DuckDB at `contracts/data/structural_econ.duckdb` with **861 rows current through 2026-03-01** (ingested 2026-04-16; schema `(date, ipc_value, monthly_variation_pct, _ingested_at)`). DANE provides headline-only (no expenditure-component split), so all four component slots populate with the headline level — same broadcast pattern as the existing `_fetch_imf_ifs_headline_broadcast` path per design doc §10 row 2. The IMF IFS via DBnomics path is preserved as the alternative-source comparator under Task 11.N.2d.1-reframe (single-source IMF-IFS-only sensitivity). Earlier "DANE direct paths return 404" framing in this row was authored without DuckDB inspection and is corrected here |
| EU (Eurozone) HICP source | **PRESERVED** | Eurostat HICP via DBnomics already fresh through 2025-12 (~5-month-stale at authoring date — binding country under the Rev-5.3.2 mix; see Task 11.N.2d-rev acceptance arithmetic note for the joint-coverage implication) |
| KE (Kenya) WC-CPI source | **PRESERVED** | Per design §10 row 1 fallback — KNBS Excel-append fragility; Y₃ continues to drop Kenya gracefully when KNBS data is absent |
| Y₃ `source_methodology` tag for the Rev-5.3.2 panel | **NEW** value reflecting the mixed-source pattern (a `source_methodology` value tagging the country source mix `{EU=Eurostat, BR=BCB, CO=DANE, KE=fallback}`; literal string finalized at implementation; the schema is described, not the literal — see footnote a) | Composite PK `(week_start, source_methodology)` admits the new tag without mutating any prior row |
| All-data-in-DuckDB invariant | **REAFFIRMED** | New raw fetches MUST materialize to new DuckDB raw tables before downstream consumption; tables under Rev-5.3.2: `bcb_ipca_monthly` (NEW under Task 11.N.2.BR-bcb-fetcher); `dane_ipc_monthly` (EXISTING and ALREADY POPULATED, consumed by Task 11.N.2.CO-dane-wire — no schema change); `oecd_cpi_monthly` (NEW only if Task 11.N.2.OECD-probe returns GO; diagnostic-only under Rev-5.3.2, NOT consumed) |

**Footnote a (`source_methodology` literal-vs-schema discipline).** The CORRECTIONS block describes the schema of the new tag (a non-`y3_v1` value distinguishing the Rev-5.3.2 mixed-source mix from the prior `y3_v1` panel). The literal string itself is finalized at implementation time and recorded in the Task 11.N.2d-rev verification memo (see Task 11.N.2d-rev acceptance criterion (d) below). Reviewers ack the chosen literal in that memo before any downstream task dispatches.

### B. New / modified plan tasks

The following tasks are **inserted** into Phase 1.5.5 between the existing Task 11.N.2d / 11.N.2d.1 commits and Task 11.O. They preserve the Rev-3.1 task-numbering convention by using compound suffixes; the Rev-5.3.2 task count update is captured in §F below. Existing Tasks 11.N.2d and 11.N.2d.1 are not deleted; their bodies are referenced and supplemented by the reframe-tasks below.

**Dispatch ordering (per RC advisory A4 — `feedback_specialized_agents_per_task` is a sequential orchestrator).** All three Data Engineer tasks (Task 11.N.2.OECD-probe, Task 11.N.2.CO-dane-wire, Task 11.N.2.BR-bcb-fetcher) dispatch to the same Data Engineer subagent under sequential orchestration. Author dispatches them as a serial stream in this order (lightest first, heaviest last):

1. **Task 11.N.2.OECD-probe** (diagnostic-only; ~30 minutes — transcribes RC's already-completed live probe output into the canonical project history).
2. **Task 11.N.2.CO-dane-wire** (~30 minutes per RC's estimate — one-table wire-up; consume-only).
3. **Task 11.N.2.BR-bcb-fetcher** (~half-day — new fetcher + cumulative-index utility + new DuckDB raw table + numpy reproduction witness).

Then Task 11.N.2d-rev dispatches (depends on both Task 11.N.2.CO-dane-wire AND Task 11.N.2.BR-bcb-fetcher landing). Then Task 11.N.2d.1-reframe (depends on Task 11.N.2d-rev). Then Task 11.O-scope-update (depends on Task 11.N.2d-rev clearing the joint-coverage gate, OR routing to user-HALT if the gate does not clear).

#### Task 11.N.2.OECD-probe — Diagnostic-only archival of OECD direct SDMX freshness for CO (NEW; diagnostic-only)

**Subagent:** Data Engineer.

**Deliverable:** `contracts/.scratch/2026-04-25-oecd-sdmx-co-cpi-probe.md` — a single scratch memo codifying the Reality Checker's 2026-04-25 live SDMX probe result (OECD direct SDMX returns CO CPI through 2026-03; ~1-month-stale at the authoring date) and listing per-country (CO / BR / KE) coverage cutoff dates returned by OECD direct SDMX, for completeness.

**Acceptance criteria:**
- Memo lists CO / BR / KE coverage from OECD direct SDMX as observed (cutoff month per country) — RC's 2026-04-25 probe output is the canonical evidence base; memo cites that probe and reproduces the request URL for future verification.
- Memo includes a side-by-side comparison row vs. the IMF IFS via DBnomics cutoffs, the BCB SGS cutoff (BR comparator), and the DANE cutoff (CO comparator) per `dane_ipc_monthly` — i.e., a four-source freshness matrix.
- Memo records the freshness threshold "≥ 2026-01-01 for CO" (anchored to the EU Eurostat HICP cutoff at 2025-12-01 plus a 1-month tolerance) as the diagnostic GO yardstick — but the memo's GO/NO-GO has NO operational dispatch consequence under Rev-5.3.2 (the CO upgrade path is Task 11.N.2.CO-dane-wire, not OECD).
- Memo serves as future-revision intelligence (Rev-5.3.3 or later may consult it if DANE wire-up is later retired); it is NOT a dependency of Task 11.N.2d-rev.

**Reviewer:** Reality Checker (single-pass, archival).

**Dependency:** Rev-5.3.2 CORRECTIONS block landed + 3-way reviewed.

**Status:** Diagnostic-only. Outputs only a `.scratch/` memo for archival. NOT a dispatch dependency for any downstream Rev-5.3.2 task. Implementation effort estimate: ~30 minutes (largely a transcription of RC's already-completed live probe output into the canonical project history).

**Anti-fishing guard:** The probe is exploratory ONLY. If OECD-direct SDMX freshness later motivates a CO source change, that change requires its own CORRECTIONS block + 3-way review (Rev-5.3.3 or later). Probe outcome may not be silently fed into the Task 11.N.2d-rev source mix under Rev-5.3.2.

---

#### Task 11.N.2.CO-dane-wire — Wire existing `dane_ipc_monthly` into the CO branch of `fetch_country_wc_cpi_components` (NEW)

**Subagent:** Data Engineer.

**Deliverable:**
- Modify the CO branch of `fetch_country_wc_cpi_components` (in `scripts/y3_data_fetchers.py`) so it consumes the existing `dane_ipc_monthly` DuckDB table — read via the canonical `econ_query_api` pattern — rather than the IMF IFS via DBnomics path.
- The headline-broadcast substitution per Y₃ design doc §10 row 2 still applies: DANE provides a headline level only (no expenditure-component split), so all four component slots are populated with the headline level — the same broadcast pattern as the existing `_fetch_imf_ifs_headline_broadcast` path. The fetcher dispatch at the CO branch is the only change; the consumer contract `fetch_country_wc_cpi_components` returns is preserved-compatible with all downstream callers.
- The existing `_fetch_imf_ifs_headline_broadcast` path is **retained** as the alternative-source comparator consumed by Task 11.N.2d.1-reframe (single-source IMF-IFS-only sensitivity).
- `contracts/.scratch/2026-04-25-co-dane-wireup-result.md` — a verification memo recording: (a) the new fetcher code path's smoke-test output (cutoff date returned, row count returned over the primary window); (b) the per-week DANE → weekly LOCF tail diagnostic (number of LOCF-extended weeks beyond the DANE monthly cutoff under the project's existing weekly-anchor LOCF rule); (c) confirmation that the existing `_fetch_imf_ifs_headline_broadcast` path remains available as fallback for the IMF-IFS-only sensitivity at Task 11.N.2d.1-reframe.

**Acceptance criteria:**
- Failing-test-first per `feedback_strict_tdd`: a failing test asserting the CO branch of `fetch_country_wc_cpi_components` round-trips DANE rows from the canonical DuckDB through the fetcher and returns a level series with cutoff date ≥ 2026-02-01 (i.e., ≤ 2-month stale at authoring date 2026-04-25).
- Real-data integration test (no DANE-fetch mock — the data is already in DuckDB; per `feedback_real_data_over_mocks`, this is a real-data round-trip).
- Existing tests under `contracts/scripts/tests/inequality/` remain green; `pytest contracts/scripts/tests/` exits 0 (PM-N4 commit-boundary guard).
- The `dane_ipc_monthly` table is **consume-only** — no schema mutation, no re-ingestion, no normalization in this task; the table is treated as authoritative read-side state owned by whichever upstream task ingested it.
- Rev-4 `decision_hash` byte-exact preserved (no schema change to `dane_ipc_monthly`; no new raw tables introduced).
- Y₃ design doc §10 row 2 broadcast pattern preserved byte-exact (headline-only ⇒ all four component slots populated with the headline level).

**Reviewers:** Code Reviewer + Reality Checker + Senior Developer (per `feedback_implementation_review_agents`).

**Dependency:** Rev-5.3.2 CORRECTIONS block landed + 3-way reviewed. (Independent of Task 11.N.2.BR-bcb-fetcher; both consume the same `fetch_country_wc_cpi_components` consumer contract via separate per-country branches and can land in either order. Sequenced serially as a single-Data-Engineer-subagent stream — see Anti-fishing guard below.)

**Anti-fishing guard:** The DANE table is **consume-only**. The fetcher dispatch change is a one-table wire-up; if DANE table contents change in a future re-ingest, that's a separate concern owned by whichever upstream task ingests `dane_ipc_monthly` (NOT this task). The Y₃ aggregation rule from design doc §4 (60/25/15 WC-CPI weights, equal-weight 1/4 country aggregation) is unchanged. The mixed-source pattern is documented in the new `source_methodology` tag (per §A footnote a) for downstream reproducibility.

---

#### Task 11.N.2.BR-bcb-fetcher — Implement BCB SGS/433 fetcher + cumulative-index utility + raw DuckDB table (NEW)

**Subagent:** Data Engineer.

**Deliverable:**
- New fetcher path that lands BCB SGS series 433 (IPCA monthly variation %) rows into a NEW additive DuckDB raw table `bcb_ipca_monthly`.
- New cumulative-index utility that converts the monthly-variation series to a level-series compatible with the existing `fetch_country_wc_cpi_components` contract for BR.
- Failing-test-first per `feedback_strict_tdd`: a failing test asserting (a) the raw table populates from a real BCB SGS HTTP fetch (no mocks except for the documented HTTP-error scenario per `feedback_real_data_over_mocks`); (b) the cumulative-index utility reproduces the BR level series byte-exact under an independent-reproduction-witness numpy path; (c) the BR-source dispatch in `fetch_country_wc_cpi_components` returns a level series with cutoff date ≥ 2026-02-01 (i.e., ≤ 2-month stale at authoring date 2026-04-25).

**Acceptance criteria:**
- The BCB SGS fetcher uses `requests`-only HTTP (no new Python dependencies per the project-wide CR-P2 dependency-discipline rule).
- The raw table `bcb_ipca_monthly` is created via additive schema migration; Rev-4 `decision_hash` byte-exact through migration; primary `onchain_xd_weekly` and `onchain_y3_weekly` rows preserved byte-exact.
- Idempotent UPSERT semantics on the raw table — re-fetching the same window does not mutate prior rows.
- The cumulative-index utility's signature is preserved-compatible with `fetch_country_wc_cpi_components`'s consumer contract; downstream callers see a level series exactly like the IMF-IFS-shaped series they were consuming previously, with no schema change.
- A second-pass numpy reproduction witness check is included in the test (cumulative product of `(1 + variation/100)` reconstructs a level series matching the utility output to within float-comparison tolerance).
- The BR series cutoff lands at ≥ 2026-02-01 when run on 2026-04-25 (the date authoring this CORRECTIONS block); any earlier cutoff means BCB SGS does not solve the staleness problem and HALT triggers.
- The verification memo documents the raw `bcb_ipca_monthly` table CHECK clause (if any — sanity bounds on the variation column to catch BCB SGS API drift returning malformed data), preserving the composite-PK + relaxed-CHECK pattern precedent from commit `a724252c6` (Rev-5.2.1 Task 11.N.1 Step 0); per CR advisory 3, this allows future reviewers to reproduce the schema exactly without recourse to git archaeology.

**Reviewers:** Code Reviewer + Reality Checker + Senior Developer (per `feedback_implementation_review_agents`).

**Dependency:** Rev-5.3.2 CORRECTIONS block landed in this plan + 3-way review of the CORRECTIONS itself converged.

**Anti-fishing guard:** The BR source-swap is a methodology change at the panel-construction layer, not at the response-variable layer. The pre-committed Y₃ aggregation rule in design doc §4 (60/25/15 WC-CPI weights, equal-weight 1/4 country aggregation) is unchanged. The mixed-source pattern is fully documented in the new `source_methodology` tag for downstream reproducibility.

---

#### Task 11.N.2d-rev — Re-execute Y₃ ingest at Rev-5.3.2 primary window with mixed sources (NEW)

**Subagent:** Data Engineer.

**Deliverable:**
- `onchain_y3_weekly` re-populated for the primary window `[2023-08-01, 2026-04-24]` using the mixed-source mix `{EU = Eurostat HICP via DBnomics, BR = BCB SGS series 433 cumulative-index (Task 11.N.2.BR-bcb-fetcher), CO = DANE via the existing `dane_ipc_monthly` DuckDB table (Task 11.N.2.CO-dane-wire), KE = skipped per design §10 row 1 fallback}`.
- The new rows are tagged with the Rev-5.3.2 `source_methodology` value (literal string finalized at implementation per §A footnote a; the schema admits the new tag via the composite PK `(week_start, source_methodology)`).
- `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md` — a verification memo documenting: (a) per-country cutoff dates observed; (b) Y₃ panel row count (per `source_methodology`); (c) joint X_d × Y₃ overlap for each `proxy_kind` in `onchain_xd_weekly`, with primary `carbon_basket_user_volume_usd` highlighted; (d) the methodology tag literal value used (called out explicitly so reviewers can ack the literal before downstream dispatch — per RC advisory A6); (e) a side-by-side row-count comparison vs. the prior Rev-5.3.1 panel state from commit `765b5e203`.

**Acceptance criteria:**
- **Step 0 (`MDES_FORMULATION_HASH` self-test, failing-test-first):** the first failing test in this task computes `sha256sum` over the canonical `required_power(n, k, mdes_sd)` source location (per MEMORY.md `mdes_formulation_pin`) and asserts byte-exact equality with the pinned hash `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (per RC advisory A3). The verification memo records the path checked and the matched hash.
- Y₃ panel weeks ≥ **105 weeks** under the new methodology tag (per the arithmetic note below — revised from the prior "≥ 95" figure to reflect the new mix's binding country EU at 2025-12-01).
- **Joint nonzero X_d × Y₃ overlap for `proxy_kind = "carbon_basket_user_volume_usd"` ≥ 75 weeks** — recovers the pre-committed `N_MIN = 75` from Rev-5.3.1. This is the load-bearing ζ-disposition gate. UNCHANGED from the prior Rev-5.3.2 figure.
- The methodology tag literal value is recorded in the verification memo and is added to the `econ_query_api.load_onchain_y3_weekly()` admitted-set (additive schema-migration test asserts this).
- Rev-4 `decision_hash` byte-exact preserved through the new ingest (the table mutation is additive INSERT under a new `source_methodology` tag — prior rows under `y3_v1` are untouched).
- All prior tests under `contracts/scripts/tests/inequality/` remain green; `pytest contracts/scripts/tests/` exits 0 (PM-N4 commit-boundary guard).
- If joint overlap lands < 75 weeks: HALT — write a NEW disposition memo at `contracts/.scratch/2026-04-25-y3-rev532-coverage-halt.md`; do NOT proceed to Task 11.O-scope-update; do NOT silently re-relax `N_MIN`. The escalation is to user, not to free-tuning.

**Arithmetic note (informational; sanity-check at execution time, not at acceptance time).**

Under the Rev-5.3.2 mix `{EU=Eurostat@2025-12-01, BR=BCB@2026-03-01, CO=DANE@2026-03-01, KE=skip}`, the binding country is **EU at 2025-12-01**. The panel cutoff = min(BR_cutoff, EU_cutoff, CO_cutoff) = 2025-12-01, snapped to the next Friday-anchor (America/Bogota timezone per project convention) and extended by the project's existing weekly-anchor LOCF tail (per Y₃ design doc §7) of up to ~4 weeks. Window `2023-08-01 → 2025-12-01` is approximately 105 Friday-anchored weeks pre-aggregation; with the LOCF tail, the panel may extend to ~109 weeks.

Joint nonzero X_d × Y₃ for `proxy_kind = "carbon_basket_user_volume_usd"` is bounded above by min(Y₃_end, X_d_end) = 2025-12-01-plus-LOCF (X_d already runs to 2026-04-03). RC's live DuckDB query (review report §"Verification trail" Command 3) reports **65 joint nonzero weeks** at cutoff `2025-12-31` for this proxy_kind — i.e., at the EU-binding cutoff plus tail.

**Risk note (transparency, not optimism).** Under the documented mix, the projected joint coverage is approximately **65 weeks** — still below the load-bearing ≥75 gate. The DANE wire-up (Task 11.N.2.CO-dane-wire) raises the ceiling from path-ζ-as-originally-written's 47 weeks to ~65 weeks, but does not by itself reach 75. The HALT clause above is the protective net for this case. If the gate does not clear under the actual landed mix, two follow-up paths are visible at this writing:

- **(a)** A δ-EU upgrade. Eurostat HICP is published by Eurostat with ~1-month lag; the existing fetcher may be consuming a DBnomics mirror with additional staleness. A direct Eurostat REST probe (separate task, separate revision) would test whether EU CPI through 2026-02 or 2026-03 is recoverable. If yes, joint coverage rises to ~76 weeks under `{CO=DANE, BR=BCB, EU=Eurostat-direct}` per RC's Command 3 sensitivity at cutoff `2026-03-31`.
- **(b)** Escalation to user. The user is the next decision-maker if (a) is infeasible or undesirable. Anti-fishing protocol forbids silent N_MIN drift; the HALT clause routes to user, never to free-tuning.

This risk note is informational. The plan's job is to reach the truth, not to promise success. The Rev-5.3.2 acceptance criteria do NOT relax in response to this risk; the gate stays at ≥75; the HALT stays in place.

The Technical Writer reviewer should sanity-check this arithmetic at execution time (NOT at acceptance review of this plan revision) and surface any divergence between projected and landed counts when the verification memo lands.

**Reviewers:** Code Reviewer + Reality Checker + Senior Developer (per `feedback_implementation_review_agents`).

**Dependency:** Task 11.N.2.BR-bcb-fetcher AND Task 11.N.2.CO-dane-wire (both fetcher branches must commit before the re-ingest can consume the BR + CO upgrades).

**Anti-fishing guard:** The window swap (Sep-2024 → Aug-2023 start) is the disposition-memo's path γ change. It IS a pre-committed primary-panel modification; the CORRECTIONS block in §A above documents it explicitly. The new `source_methodology` tag preserves the prior `y3_v1` rows for diagnostic comparison (see Task 11.N.2d.1-reframe). The user has explicitly approved this window change as the ζ-disposition path; the change is not a back-door silent panel extension.

---

#### Task 11.N.2d.1-reframe — Reframe of original 11.N.2d.1 from "wider-window sensitivity" to "single-source-fallback sensitivity" (REFRAME of an existing task)

**Subagent:** Data Engineer.

**Deliverable:**
- A sensitivity Y₃ panel computed against the **IMF-IFS-only** source mix (the pre-Rev-5.3.2 BR source) over the **same primary window** `[2023-08-01, 2026-04-24]`, persisted under a `source_methodology` value with suffix `_imf_only_sensitivity` (literal value finalized at implementation; describe the schema, not the string).
- `contracts/.scratch/2026-04-25-y3-imf-only-sensitivity-comparison.md` — a comparison memo of (a) primary-vs-sensitivity Y₃ value deviation per week; (b) joint X_d × Y₃ overlap for `proxy_kind = "carbon_basket_user_volume_usd"` under the IMF-IFS-only source mix; (c) any Y₃ value drift > 1 standard deviation between the two methodologies, flagged as a finding (informational; not a blocker).

**Acceptance criteria:**
- The IMF-IFS-only sensitivity panel persists in `onchain_y3_weekly` with a distinct `source_methodology` value; the composite PK `(week_start, source_methodology)` admits it without mutating the Task 11.N.2d-rev primary rows.
- Deviation between primary (mixed-source) Y₃ and sensitivity (IMF-only) Y₃ is quantified per week; week-by-week deviation series is included in the comparison memo.
- The original Task 11.N.2d.1 (wider-window Aug-2023 sensitivity) IS NOW REDUNDANT under Rev-5.3.2 because the Aug-2023 start date is the new PRIMARY window. The original 11.N.2d.1 task body is superseded — it was a sensitivity row pointing at the now-primary window. The reframe replaces it with the source-mix sensitivity, which is the analytically meaningful comparison under ζ.
- Rev-4 `decision_hash` byte-exact preserved.

**Reviewers:** Code Reviewer + Reality Checker + Senior Developer.

**Dependency:** Task 11.N.2d-rev (primary panel must commit first to provide the comparison baseline).

**Status note:** The original Task 11.N.2d.1 as written in the Rev-5.3 v2 fix-pass plan body is **superseded-as-applied** by this reframe. The body of the original task (Steps 0-3 covering the Aug-2023 → 2026-04-24 wider-window sensitivity panel) is not deleted from the plan — it is preserved as historical record — but its execution under Rev-5.3.2 is replaced by the reframe above. A future reader following the plan executes Task 11.N.2d.1-reframe in place of the original.

---

#### Task 11.N.2d.2-NEW — RESERVED for user-pre-registered imputation methodology (DELIBERATE NON-TASK)

**Subagent:** *(none — deliberate non-task)*

**Deliverable:** *(none)*

**Status:** RESERVED. NOT AUTHORED in Rev-5.3.2.

**Rationale.** The user raised a question about whether past values can be brought forward to make dates comparable across the source mix (e.g., LOCF extension of stale series, AR(p) nowcast, cross-country bridging). Multiple imputation mechanisms exist:
- **LOCF extension** (last-observation-carried-forward beyond the source cutoff): trivial to implement, but assumes stale-series stationarity over the extension horizon — not warranted for CPI under regime change.
- **AR(p) nowcast** (fit AR(p) to the stale series, project forward): adds modeling-choice surface area on the response variable.
- **Cross-country bridging** (project CO CPI from a regression on EU / BR CPI for the missing months): introduces cross-country information into Y₃ that Y₃'s design doc §1 sign convention does NOT contemplate.
- **Current truncation** (the Rev-5.3.2 primary path under ζ): simple, no imputation, no extra surface area; the panel cutoff IS bounded by the slowest country.
- **γ backward extension** (the Rev-5.3.2 primary path under ζ for the start date): extends the panel backward into pre-existing data, which is methodologically clean.

Each imputation mechanism (LOCF, AR(p), cross-country) carries non-trivial **anti-fishing surface area on the response variable Y₃** — the response variable is the gate target for Task 11.O, and any imputation that affects Y₃ values mid-plan is mid-stream re-tuning of the response. The Rev-5.3.2 primary path deliberately does NOT pre-commit any imputation method.

**If a future revision needs imputation**, it must satisfy the four conditions enumerated canonically in §C below (method-with-citation / sha256 anchor / side-by-side sensitivity / 3-way review pre-approval). The §B placeholder defers to §C for the authoritative condition list to prevent future-maintenance drift between two locations (per TW peer advisory 6).

Until such a revision exists, primary path uses **truncated panel + γ window extension + δ-{BR, CO} source upgrades ONLY** (BR via BCB SGS in Task 11.N.2.BR-bcb-fetcher; CO via the existing `dane_ipc_monthly` table in Task 11.N.2.CO-dane-wire). Imputation is OFF the primary path under Rev-5.3.2.

The four conditions in §C also explicitly forbid relabeling the existing γ-backward-extension or truncation operations as "imputation" — only the EXACT panel-construction operations PERMITTED under Rev-5.3.2 are: γ backward extension into existing-data territory; truncation at min-country cutoff; idempotent UPSERT under the new `source_methodology` tag. ANY operation that materially changes the response variable Y₃ values for any week present in the prior `y3_v1` panel is forbidden by this revision (per RC advisory A5).

---

#### Task 11.O-scope-update — Update Task 11.O acceptance criteria to consume Rev-5.3.2 Y₃ panel (MODIFY existing Task 11.O)

> **Annotation note (post-edit, 2026-04-25):** The upstream Task 11.O body (located near line 1211 of this plan, in the Rev-5 insert section preceding Phase 2b) has been edited in-place per the deliverable below. The updates incorporate (a) the Rev-5.3.2 primary `source_methodology` literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`; (b) the Rev-5.3.2 panel window `[2023-08-01, 2026-04-24]`; (c) the actual landed gate-clearance count of 76 joint nonzero X_d × Y₃ weeks (≥ `N_MIN = 75` from Rev-5.3.1 path α); (d) a pre-registered LOCF-tail-excluded sensitivity row in the Rev-2 spec (RC A3 / SD-RR-A2; expected 65-week FAIL) plus the IMF-IFS-only sensitivity (56-week FAIL); (e) a Step-0 precondition flipping the `load_onchain_y3_weekly` default `source_methodology` to the v2 literal and migrating the Step-7 round-trip test to pass an explicit tag (SD-RR-A1); (f) a future-maintenance note about the admitted-set fold-to-provenance-dict at ~6-tag threshold (SD-A4 from `contracts/.scratch/2026-04-25-y3-reframe-review-senior-developer.md`). The DAG dependency on Task 11.N.2d-rev landing (commits `c5cc9b66b` + fix-up `2a0377057`) is reaffirmed in the upstream Task 11.O body's new banner block. The structural-econometrics-skill invocation methodology and the existing 13-row resolution-matrix discipline are preserved byte-exact — only the panel inputs and pre-commitments have been updated.

**Subagent:** Senior Developer (spec-update authoring; author distinct from reviewer pool per RC advisory A2 to keep Technical Writer as an independent reviewer).

**Deliverable:**
- The existing Task 11.O body (Rev-2 spec authoring via the `structural-econometrics` skill) is updated to (a) reference the new Rev-5.3.2 `source_methodology` literal value as the primary Y₃ source; (b) reference the new primary panel window `[2023-08-01, 2026-04-24]`; (c) update the resolution-matrix MDES-anchor narrative to reflect that the operative `n` for the regression has grown from the prior 56-week-bound (toward the ≥75 gate, conditional on the joint-coverage clearing — see Task 11.N.2d-rev arithmetic note); (d) update the pre-commitment table within the Task 11.O Rev-2 spec to enumerate the BR BCB SGS and CO DANE source upgrades as documented panel-construction methodology choices; (e) preserve the structural-econometrics-skill invocation pattern byte-exact (the spec authoring methodology does not change — only the panel inputs change).
- **In-place superseded-banner edit (per CR advisory A4):** insert a one-sentence header at the top of the original Task 11.N.2d.1 body (around line 1164 in the upstream pre-Rev-5.3.2 plan body, NOT inside this CORRECTIONS block) reading `**Rev-5.3.2 superseded:** this task body is replaced by Task 11.N.2d.1-reframe; do not execute this body.` This is a one-line in-place annotation — it does not modify the original task's prose, only flags it for the top-to-bottom reader. This is the only edit in this Rev-5.3.2 task scope that touches upstream prior-revision plan text; it is permitted because it is a non-mutating annotation pointing forward to the reframe.

**Acceptance criteria:**
- Task 11.O body is updated in-place in this plan file to reference the Rev-5.3.2 panel and methodology tag.
- The superseded-banner annotation is in place at the head of the original Task 11.N.2d.1 body and resolves correctly when followed top-to-bottom.
- Task 11.O remains BLOCKED on Task 11.N.2d-rev landing, NOT on Task 11.N.2d.1-reframe (the source-mix sensitivity is consumed lazily by Task 11.O's downstream sensitivity-cross-validation step, not by the spec authoring itself).
- Three-way review (Code Reviewer + Reality Checker + Technical Writer) is dispatched against the updated Task 11.O body PLUS this Rev-5.3.2 CORRECTIONS block as a single review unit; reviewers verify the Rev-5.3.2 panel is methodologically defensible BEFORE Task 11.O dispatches.

**Reviewers:** Code Reviewer + Reality Checker + Technical Writer (spec-review trio per `feedback_three_way_review`; Technical Writer is independent of authoring per RC advisory A2).

**Dependency:** Task 11.N.2d-rev (primary panel landed and verified to recover `N_MIN ≥ 75` — OR HALT-with-disposition-memo if it does not, per the Task 11.N.2d-rev HALT clause; in the HALT case, Task 11.O-scope-update does not dispatch, the HALT routes to user).

**Anti-fishing guard:** Task 11.O Rev-2 spec authoring may NOT proceed against the Rev-5.3.1 panel (`y3_v1`, 56-week joint coverage) under any circumstance — that would be silent N_MIN tuning. Task 11.O dispatches ONLY after the Rev-5.3.2 panel landed AND verified to recover the joint coverage gate.

---

### C. Imputation discussion (explicit non-decision; canonical four-condition list)

The user raised an important question during disposition selection: can past values be brought forward to make dates comparable across the heterogeneous-staleness source mix? Several candidate mechanisms exist (LOCF extension beyond the source cutoff; AR(p) nowcast; cross-country bridging via a regression of stale countries on fresher ones; γ backward extension into pre-existing data; current truncation accepting the slowest-country cutoff as the panel boundary). All but the last two carry non-trivial **anti-fishing surface area on the response variable Y₃**.

Rev-5.3.2 deliberately does NOT pre-commit any imputation method. The primary path is **truncated panel + γ window extension + δ-{BR, CO} source upgrades ONLY** (BR via BCB SGS in Task 11.N.2.BR-bcb-fetcher; CO via the existing `dane_ipc_monthly` table in Task 11.N.2.CO-dane-wire). The Aug-2023 start date is a backward extension into existing-data territory — no new methodology is invoked, just a wider window over already-available source data. The BR + CO source upgrades are clean source-vendor changes with the same definitional contract; no imputation is involved.

**Canonical four-condition list (authoritative; §B Task 11.N.2d.2-NEW references this list).** If a future plan revision (Rev-5.3.3 or later) needs to introduce imputation to push the panel cutoff beyond the current bound, it MUST satisfy ALL FOUR of the following; failing any one of them blocks the introduction:

- (a) The imputation method is specified in the plan body with literature citation (no "we used a reasonable method" — the citation must be reproducible, peer-reviewed, and pre-existing in the field at the time of the revision).
- (b) A sha256 anchor is committed over the imputation source code (precedent: `MDES_FORMULATION_HASH`); the anchor is recorded in the plan body and verified by the failing-test-first as the first acceptance step (precedent: Task 11.N.2d-rev Step 0).
- (c) A side-by-side sensitivity comparison vs. the truncated baseline is authored (the Task 11.N.2d.1-reframe pattern is the operational template); the comparison must include per-week Y₃ deviation and any Y₃-deviation > 1 standard-deviation between the two methodologies surfaced as a finding (informational; not a blocker).
- (d) 3-way review pre-approves before commit (per `feedback_three_way_review`).

**Anti-fishing tightening (per RC advisory A5).** The four-condition list above forbids relabeling existing operations as "imputation" — i.e., a future revision cannot rebrand the γ-backward-extension or the truncation as "imputation" to bypass the four-condition gate. The exact panel-construction operations PERMITTED under Rev-5.3.2 are exhaustively: (i) γ backward extension into existing-data territory; (ii) truncation at min-country cutoff (whichever country binds the panel cutoff under the source mix); (iii) idempotent UPSERT under the new `source_methodology` tag. ANY operation that materially changes the response variable Y₃ values for any week present in the prior `y3_v1` panel is forbidden by this revision and must escalate to a future revision under the four-condition gate.

Until such a revision exists, the imputation question is OFF the primary path. Task 11.N.2d.2-NEW above is the deliberate placeholder documenting this non-decision.

---

### D. All-data-in-DuckDB invariant — explicit additive-table list

The user reaffirmed the all-data-in-DuckDB invariant during disposition selection. Any new raw fetch under Rev-5.3.2 MUST materialize to a NEW additive DuckDB raw table before downstream consumption. The table list below is the authoritative manifest under Rev-5.3.2:

| Raw table | Status | Source | Used by |
|---|---|---|---|
| `bcb_ipca_monthly` | **NEW under Task 11.N.2.BR-bcb-fetcher** | BCB SGS direct API series 433 (IPCA monthly variation %) | BR `fetch_country_wc_cpi_components` cumulative-index path under Rev-5.3.2 mixed-source mix |
| `dane_ipc_monthly` | **EXISTING and ALREADY POPULATED** (consumed by Task 11.N.2.CO-dane-wire — no schema change, consume-only) | DANE direct ingestion landed 2026-04-16 prior to Rev-5.3.2 authoring; canonical structural-econ DuckDB at `contracts/data/structural_econ.duckdb` holds 861 rows current through 2026-03-01; schema `(date, ipc_value, monthly_variation_pct, _ingested_at)`; Reality Checker live-verified 2026-04-25 | CO `fetch_country_wc_cpi_components` headline-broadcast path under Rev-5.3.2 mixed-source mix |
| `oecd_cpi_monthly` | **NOT CREATED under Rev-5.3.2** | OECD direct SDMX endpoint (CO/BR/KE coverage) | Diagnostic-only: Task 11.N.2.OECD-probe is reclassified as diagnostic-only and produces a `.scratch/` memo, not a DuckDB table. A future Rev-5.3.3 (or later) may introduce this table under its own CORRECTIONS block + 3-way review |
| Existing raw DuckDB tables (Rev-5.3.1 and earlier) | PRESERVED byte-exact | Various (IMF IFS, Eurostat, Banrep, Yahoo, etc.) | Used by Task 11.N.2d-rev's mixed-source dispatch (notably: IMF IFS via DBnomics is preserved as the alternative-source comparator consumed by Task 11.N.2d.1-reframe) |

The additive-only invariant is enforced via the existing schema-migration test pattern (`test_onchain_duckdb_migration.py` — assert Rev-4 `decision_hash` byte-exact through migration; assert all prior table row counts byte-exact through migration; assert new tables are present with the expected schema).

---

### E. Acceptance criteria for the Rev-5.3.2 CORRECTIONS block ITSELF

Before any task in section B above is dispatched, this CORRECTIONS block MUST pass a 3-way review per `feedback_three_way_review`:

- **Code Reviewer:** Verify (a) no code in the plan body — only behavior, data-source, methodology, and acceptance-criteria prose; (b) the Rev-5.3.2 task list is internally consistent (dependency DAG, acceptance criteria, reviewer assignments); (c) all-data-in-DuckDB invariant respected (additive-table list complete); (d) anti-fishing pre-commitments preserved (N_MIN, POWER_MIN, MDES_SD, MDES_FORMULATION_HASH unchanged); (e) the BR source-swap acceptance criteria specify failing-test-first per `feedback_strict_tdd`.
- **Reality Checker:** Verify (a) the disposition memo's path-ζ rationale matches this CORRECTIONS block exactly (no silent path drift); (b) the cutoff-date arithmetic in Task 11.N.2d-rev acceptance criteria is reproducible from public BCB SGS / Eurostat / IMF IFS observation (a probe at execution time should not surprise the reviewer); (c) the joint-coverage target of ≥ 75 weeks is consistent with the disposition-memo math (window swap + BR source upgrade → ~80+ weeks per memo §3 ζ row); (d) the imputation discussion in §C explicitly excludes imputation from the primary path and documents the four conditions for any future imputation revision.
- **Technical Writer:** Verify (a) imputation is explicitly excluded from primary; (b) the new tasks are clearly distinguished from the original Task 11.N.2d / 11.N.2d.1 (no reader confusion about which body executes under Rev-5.3.2); (c) the `source_methodology` literal-value-vs-schema distinction is consistently maintained (the schema is described, not the literal); (d) all data lands in DuckDB per the §D manifest; (e) the prose voice is consistent with the Rev-5.3.1 CORRECTIONS block precedent (second person where directives apply, present tense, precise about preserved-vs-updated anchors).

If any reviewer returns BLOCK: dispatch the orchestrator to address findings; re-dispatch the offending reviewer; bound by Rule 13's 3-cycle cap. Until 3-way convergence, NO task in section B may dispatch.

---

### F. Task count + status reconciliation under Rev-5.3.2

Rev-5.3.1 active task count (per the existing reconciliation block above): **63** active tasks (or **64 total headers** including 4 retired-as-audit). Rev-5.3.2 introduces the following changes:

- **+5 new task IDs with new bodies** (Task 11.N.2.OECD-probe — diagnostic-only; Task 11.N.2.CO-dane-wire — NEW per Rev-5.3.2 fix-up rewrite; Task 11.N.2.BR-bcb-fetcher; Task 11.N.2d-rev; Task 11.N.2d.1-reframe).
- **+1 new task ID with MODIFY-target deliverable** (Task 11.O-scope-update — modifies the upstream Task 11.O body in-place; not a wholly new body — per TW peer advisory 1).
- **+1 deliberate non-task** (Task 11.N.2d.2-NEW — RESERVED placeholder; not a dispatched task; it documents an explicit non-decision).
- **0 retired tasks.** The original Task 11.N.2d.1 is REFRAMED-AS-APPLIED (its body is preserved as historical record with a one-line in-place superseded-banner annotation per Task 11.O-scope-update deliverable; Task 11.N.2d.1-reframe is the operative replacement under Rev-5.3.2).
- **0 modified tasks at the body level besides Task 11.O.** Task 11.O acceptance criteria are updated in-place per Task 11.O-scope-update; the structural-econometrics-skill invocation methodology is unchanged.

Rev-5.3.2 active task count: **63 + 6 = 69** (excluding the deliberate non-task placeholder); total headers: **64 + 6 + 1 (placeholder) = 71**. Note that the 63-baseline figure inherits a previously-acknowledged +3 accounting drift documented at line 1739 (Rev-5.3.1's banner figure was preserved as-such pending a row-by-row rebuild); per CR advisory 1, Rev-5.3.2 propagates the prior accepted drift unchanged and resolves at the future Rev-5.4 row-by-row refresh per amendment-rider A8 (unchanged by this revision).

---

### G. Reference paths

- Disposition memo (path-ζ user selection): `contracts/.scratch/2026-04-25-y3-coverage-halt-disposition.md`
- Rev-5.3.2 3-way review reports (BLOCK trigger for fix-up rewrite): Reality Checker `contracts/.scratch/2026-04-25-rev532-review-reality-checker.md` (load-bearing — cited in Trigger paragraph and §A CO-row corrected framing); Code Reviewer `contracts/.scratch/2026-04-25-rev532-review-code-reviewer.md` (PASS-with-advisories); Technical Writer peer `contracts/.scratch/2026-04-25-rev532-review-technical-writer.md` (PASS-with-advisories)
- Rev-5.3.1 CORRECTIONS block (precedent format): inline above at Task 11.N.2c body, 2026-04-25, commit `7afcd2ad6`
- Y₃ design doc (immutable; preserved byte-exact): `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` (commit `23560d31b`)
- X_d design doc (immutable; preserved byte-exact): `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`
- Rev-5.3.1 N_MIN-relaxation rationale memo: `contracts/.scratch/2026-04-25-carbon-basket-calibration-result-rev2.md`
- Last clean commit before Rev-5.3.2 dispatch: `765b5e203` (Task 11.N.2d primary panel landing)
- Prior HALT memo (informational): `cefec08a7`
- MDES_FORMULATION_HASH (immutable, sha256): `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`
- Rev-4 decision_hash (immutable through Rev-5.3.2): `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`

---

## CORRECTIONS — Rev-5.3.3 (2026-04-25, post-Phase-5b gate-FAIL — α + β parallel-track pivot, notebook migration)

**Trigger.** Rev-5.3.2 Task 11.O Rev-2 Phase 5b shipped the Analytics Reporter primary-estimation deliverable at commit `799cbc280` with **gate verdict T3b = FAIL**: β̂_X_d = `−2.799 × 10⁻⁸` (sign-flipped from the pre-registered `β > 0`); 90% one-sided lower bound = `−4.621 × 10⁻⁸` (≤ 0 ⇒ T3b FAIL); T1 exogeneity REJECTS (the published β̂ is a *predictive-regression* coefficient, not a structural causal estimand); a single observation at `2026-03-06` (Cook's D = 0.888, studentized residual = −3.13) drives ~50% of |β̂|, with the sign-flip robust to drop-one removal. The 4-reviewer gate (Code Reviewer + Reality Checker + Senior Developer + Model QA Specialist) all returned PASS-class verdicts at commits `6b1200dcb` (RC + Model QA) and `f38f1aad3` (CR + SD), closing the Rev-2 mean-β estimation cleanly with the FAIL standing on the analytical merits — the same analytical-discipline-vindication pattern as the closed `project_fx_vol_cpi_notebook_complete` (FX-vol-CPI Colombia notebook). Per `feedback_pathological_halt_anti_fishing_checkpoint`, the orchestrator HALTed and authored the disposition memo at `contracts/.scratch/2026-04-25-task110-rev2-gate-fail-disposition.md` (commit `c1eec8da5`) enumerating five pivot paths (α / β / γ / δ / ε); user selected **α + β parallel tracks** with two binding clarifications carried over into this Rev-5.3.3 block:

- **α = Rev-3 ζ-group convex-payoff extensions** (per Rev-2 spec §10.6: ζ.1 quantile β̂(τ); ζ.2 GARCH(1,1)-X conditional-variance; ζ.3 lower-tail conditional regression; ζ.4 option-implied volatility surface). The convex-payoff insufficiency caveat from Rev-2 spec §11.A REMAINS LOAD-BEARING: mean-β was always *necessary-but-insufficient* for convex-instrument pricing, and the Rev-2 FAIL is **orthogonal** (not antagonistic) to the convex-payoff fitness test that ζ-group is designed to run. Rev-3 spec authoring is the analytically-correct path forward IF the convex-instrument product purpose holds.
- **β = brainstorm-α reframed as a payments / consumption pivot grounded in actual Mento user-base evidence** — NOT a speculative hypothesis sweep. Per user clarification, β must be GROUNDED IN ACTUAL Mento user-base documentation (MiniPay, Valora, GoodDollar, peer-to-peer payments corridors, retail-consumption use cases, etc.) BEFORE any structural-econometric spec is authored. No spec authored against speculation; no data exploration on candidate X_d variables before the user-base evidence is in hand. This is anti-fishing discipline at the hypothesis-formation stage. The Trend Researcher subagent has been dispatched (background `agentId = a7cd002b89b23e0ac`) to gather and synthesize Mento ecosystem usage evidence; the deliverable is an evidence-grounded report under `contracts/.scratch/2026-04-25-mento-userbase-research.md`.

**Notebook-migration directive.** Per user instruction, ALL future analytical work in both tracks (α and β) is migrated to a 3-notebook structure under `notebooks/abrigo_y3_x_d/` following the FX-vol-CPI Colombia precedent: NB1 data EDA + panel fingerprint, NB2 primary estimation, NB3 specification tests + sensitivity analysis. The discipline is the citation-block + trio-checkpoint pattern enforced by `feedback_notebook_citation_block` (every test / decision / spec-choice preceded by a 4-part markdown block: reference / why used / relevance to results / connection to product) and `feedback_notebook_trio_checkpoint` (Analytics Reporter HALTs after every (why-markdown, code-cell, interpretation-markdown) trio for human review; bulk authoring is forbidden). This Rev-5.3.3 block is the user-approved CORRECTIONS payload that adds the super-task pointers for both tracks, reaffirms anti-fishing invariants, and updates the task-count tally. Reference commits: `799cbc280` (Phase 5b primary estimates); `6b1200dcb` + `f38f1aad3` (4-reviewer gate close-out); `c1eec8da5` (disposition memo).

### Why α + β parallel over α-only or β-only (succinct)

- **α-only (Rev-3 ζ-group only):** REJECTED as sole path — runs convex-payoff identification against the **same X_d hypothesis** that just FAILed at the mean-β level with T1 exogeneity REJECTed. The ζ-group is product-correct in scope (convex pricing requires distributional evidence) but it inherits the predictive-not-structural diagnostic from Rev-2 unless the X_d hypothesis is independently re-grounded. Running ζ-group alone is product-incomplete.
- **β-only (payments / consumption pivot only):** REJECTED as sole path — abandons the convex-payoff calibration roadmap that the §10.6 ζ-group precisely enumerates. Rev-2 §11.A is explicit that mean-β identification is *first-stage*; closing the convex-instrument gap requires the ζ-group regardless of what the next-generation X_d hypothesis turns out to be. β-only would forfeit the calibration handoff that is already pre-registered.
- **α + β parallel (SELECTED):** Rev-3 ζ-group exercises the convex-payoff calibration machinery against the existing (Rev-2) X_d while β re-grounds the next-generation X_d hypothesis in actual Mento user-base evidence. Results inform each other: ζ-group's distributional findings constrain what convex-payoff product the β-grounded X_d eventually feeds; β's user-base evidence constrains what hypothesis the ζ-group is ultimately calibrated against. Neither track blocks the other; both surface independent analytical evidence.
- **γ / δ / ε (rejected):** γ (per-currency Mento focus) was anti-fishing-flagged MEDIUM-HIGH in the disposition memo — switching to per-currency AFTER seeing the basket-aggregate FAIL is suggestive of cherry-picking; admitted only with explicit per-currency pre-commitment which user did not select. δ (EXIT) was rejected on the merits: convex-payoff calibration roadmap is too valuable to abandon. ε (interactive structural-econometrics skill flow) is partially folded INTO α and β as the spec-authoring methodology — see §C super-task constraints.

### A. Trigger + path-α+β rationale

This Rev-5.3.3 block is authored on **2026-04-25** (same calendar day as the Phase 5b FAIL verdict commit `799cbc280` and the disposition memo commit `c1eec8da5`). All staleness arithmetic in subsequent sections is anchored to this authoring date. The disposition memo's Option α is implemented under §C as Task 11.O.ζ-α (Rev-3 ζ-group super-task pointing to a sub-plan); Option β is implemented under §C as Tasks 11.P.MR-β (Mento user-base research, COMPLETED), 11.P.MR-β.1 (cCOP-vs-COPM provenance audit + memory corrigendum, NEW), 11.P.spec-β (β hypothesis spec authoring), and 11.P.exec-β (β analytical execution), each pointing to its own sub-plan. The notebook-migration directive is implemented under §C as Task 11.O.NB-α (Rev-2 analytical work migrated to notebooks) and is reaffirmed across all execution super-tasks via §D's notebook discipline.

The Rev-5.3.2 mean-β regression at the 14-row resolution-matrix scope IS the published baseline for the major plan and it does NOT change under Rev-5.3.3 — Rev-5.3.2 shipped a clean FAIL verdict with full reviewer convergence; that is the analytical close-out for the mean-β scope. Rev-5.3.3 ADDS the next-stage tracks; it does not retroactively alter Rev-5.3.2's published estimates, panel, or methodology tag.

**Trend Researcher findings landed (post-original-Rev-5.3.3-author).** The Trend Researcher subagent completed dispatch and returned its evidence-grounded report at `contracts/.scratch/2026-04-25-mento-userbase-research.md`. Four headline findings reframe both tracks of this CORRECTIONS block and are load-bearing on the Task 11.O.ζ-α and Task 11.P.spec-β scope updates below: **(Finding 1)** MiniPay (12.6M-15M wallets) is a SWAP RAIL not a USDm holdings story — 87% of MiniPay P2P transactions are < $5; USDt dominates the swap rail; the macro-hedge signal in MiniPay aggregate ≈ zero; **(Finding 2)** Carbon DeFi protocol contracts account for ~52% of cCOP Transfer events and exhibit a UTC 13-17 diurnal signature consistent with PROFESSIONAL NA-HOURS MARKET-MAKER ACTIVITY, not Colombian retail hedge demand — the Rev-2 X_d series was measuring global-liquidity-sensitive arbitrage, NOT retail hedge demand, and the FAIL verdict (β̂ < 0; T1 exogeneity REJECTS; ρ(X_d, fed_funds) = `−0.614`) is fully consistent with the macro-substitution literature (BIS WP 1219 / WP 1340); **(Finding 3)** cCOP and COPM are DIFFERENT TOKENS with DIFFERENT ISSUERS — the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` referenced throughout the Rev-2 X_d series is **Mento-native cCOP** (per Celo forum source), which is what the `onchain_copm_transfers` DuckDB table actually tracks; project memory `project_mento_canonical_naming_2026` carries a NAMING error on the COPM entry, while the underlying data is correct (and Mento-native, matching the new scope); **(Finding 4)** Trend Researcher observed three prompt-injection attempts in WebFetch / WebSearch output and correctly ignored them — defensive behavior recorded as audit-trail disclosure for the Rev-5.3.3 record.

**User scope-tightening directive (2026-04-25).** Per user statement received the same calendar day as the TR report landing: "We're not taking into account [Minteo COPM] anymore. We're only focusing on Mento and what kind of hedges we can build from Mento. That's it." This directive is recorded as a NEW pre-commitment in §B (item 6 below) and constrains BOTH Track α (Task 11.O.ζ-α) and Track β (Task 11.P.spec-β / Task 11.P.exec-β) to **Mento-native stablecoins ONLY** (cCOP, USDm, EURm, BRLm, KESm, XOFm). The Minteo-fintech COPM (a separate B2B/API/BDO-audited fiat-backed token issued outside the Mento system) is OUT OF SCOPE for Abrigo as of this revision. Memory anchor: `project_abrigo_mento_native_only.md` at `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/`. Combined with TR Finding 3, the directive is consistent with what the Rev-2 X_d data was actually measuring (Mento-native cCOP); Rev-5.3.3 closes the naming ambiguity and constrains forward scope to Mento-native instruments only.

### B. Pre-commitment update (no relaxations; all extensions)

| Anchor | Status under Rev-5.3.3 | Source / rationale |
| --- | --- | --- |
| `N_MIN` | **PRESERVED** at `75` | Rev-5.3.1 path-α value; preserved through Rev-5.3.2; preserved through Rev-5.3.3 |
| `POWER_MIN` | **PRESERVED** at `0.80` | Identical anchor through all revisions |
| `MDES_SD` | **PRESERVED** at `0.40` | Identical anchor; free-tuning upward to chase target power is anti-fishing-banned per `project_mdes_formulation_pin` |
| `MDES_FORMULATION_HASH` | **PRESERVED** byte-exact at sha256 `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` | Pinned per `project_mdes_formulation_pin`; immutable through Rev-5.3.3 |
| Rev-4 `decision_hash` | **PRESERVED** byte-exact at `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` | Immutable through Rev-5.3.3 |
| Rev-2 spec invariants (functional form, control set, methodology literals) | **PRESERVED** byte-exact | Rev-2 spec §3-§9 untouched; Rev-3 ζ-group extensions are NEW spec content authored under their own pre-registration in a sub-plan, not amendments to Rev-2 |
| 14-row resolution-matrix scope (Rev-2 mean-β regression) | **PRESERVED** as published baseline | Rev-5.3.2 Phase 5b deliverable at commit `799cbc280` is the analytical close-out for mean-β scope; Rev-5.3.3 does not retroactively re-litigate any 14-row estimate |
| Anti-fishing protocol (HALT → disposition memo → user-enumerated pivot → CORRECTIONS block → post-hoc 3-way review) | **PRESERVED** byte-exact | Halt-disposition-pivot-CORRECTIONS-review chain enforced for both Rev-3 ζ-group authoring and β hypothesis authoring |
| Convex-payoff insufficiency caveat (Rev-2 spec §11.A) | **REAFFIRMED LOAD-BEARING** | Mean-β identification was always *necessary-but-insufficient* for convex-instrument pricing; the §10.6 ζ-group roadmap is where convex-payoff calibration fitness gets tested; Rev-3 authoring under Task 11.O.ζ-α executes that pre-registered handoff |
| All-data-in-DuckDB invariant | **REAFFIRMED** | Any new raw fetches under Rev-5.3.3 (notably any Mento user-base research data that materializes into a queryable form) MUST land in a new additive DuckDB raw table before downstream consumption; sub-plans MUST enumerate any new tables in their own §D-equivalent manifests |
| Notebook discipline (`feedback_notebook_citation_block` + `feedback_notebook_trio_checkpoint`) | **NEWLY ADOPTED** as binding for ALL Rev-5.3.3 analytical work in both α and β tracks | Migration of analytical work from script-form to 3-notebook-form per FX-vol-CPI Colombia precedent; trio-checkpoint forbids bulk authoring |

**Pre-commitment ADDITIONS (not relaxations):**

1. **Notebook migration is binding for both tracks.** All analytical work (α and β) is authored in the 3-notebook structure under `notebooks/abrigo_y3_x_d/` (or sub-track-namespaced subdirectories where appropriate). Script-form authoring is forbidden for any new analytical deliverable under Rev-5.3.3 except for tightly-scoped Data Engineer helpers (data fetchers, DuckDB ingest functions) where notebook-form is operationally inappropriate.
2. **Track α and Track β are PARALLEL.** Neither blocks the other; results inform each other. The Rev-3 ζ-group (α) and the β hypothesis (β) can converge in any order; sub-plans MUST NOT introduce cross-track blocking dependencies.
3. **β hypothesis MUST be grounded in actual Mento user-base evidence BEFORE spec authoring.** No structural-econometric spec is authored against a speculative X_d hypothesis. Trend Researcher's report (Task 11.P.MR-β) is the upstream blocker for Task 11.P.spec-β. The β hypothesis spec authoring follows the user-driven structural-econometrics skill flow (the Option ε pattern from the disposition memo, folded into the β track here).
4. **Rev-3 ζ-group spec authoring is INTERACTIVE per the user's earlier deferral.** The Rev-3 spec is authored via the user-driven structural-econometrics skill flow (the Option ε pattern), NOT autonomously by an agent. Task 11.O.ζ-α's sub-plan documents the interactive authoring methodology; the orchestrator dispatches the agent for Phase 5a/5b execution per ζ row only AFTER the user closes the spec authoring loop with three-way review convergence.
5. **Convex-payoff caveat (Rev-2 §11.A) governs Rev-3 product claims.** Until the ζ-group ships PASS verdicts on the convex-payoff identification rows, Abrigo's product framing CANNOT make convex-instrument pricing claims grounded in any Rev-3 evidence. The Rev-2 §11 product-pivot map (linear-hedge-only at PASS; pivot at FAIL) governs Rev-2 scope; the equivalent Rev-3 product-pivot map is authored in the Rev-3 ζ-group sub-plan.
6. **Abrigo scope is Mento-native stablecoins ONLY.** Per the user scope-tightening directive recorded above and the project memory anchor `project_abrigo_mento_native_only.md`, Abrigo's product scope is restricted to Mento-native stablecoins: cCOP, USDm, EURm, BRLm, KESm, XOFm (and any future Mento-issued stablecoin asset). Minteo-fintech COPM and other third-party fiat-backed tokens issued outside the Mento system are OUT OF SCOPE for hedge-instrument design, X_d hypothesis formation, ζ-group convex-payoff testing, and β-track payments / consumption hypothesis authoring. This pre-commitment is byte-exact and immutable through Rev-5.3.3; relaxation requires its own CORRECTIONS block with explicit user authorization.
7. **Rev-2 X_d series identity is formally Mento-native cCOP, NOT Minteo-fintech COPM.** Per TR Finding 3, the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` referenced as the Rev-2 X_d series root is **Mento-native cCOP** (Celo forum source). The DuckDB table `onchain_copm_transfers` is misnamed in the project memory `project_mento_canonical_naming_2026` (its COPM entry carries a NAMING error); the underlying data is CORRECT — it tracks Mento-native cCOP, which matches the Rev-5.3.3 Mento-native-only scope. A memory corrigendum is required to align project memory with the data; the corrigendum work is scoped under NEW Task 11.P.MR-β.1 below. No data changes are required (the Rev-5.3.2 published estimates remain byte-exact); only naming clarification.

### C. New super-tasks added to the major plan (with sub-plan pointers)

Per user directive, substantial work goes into super-tasks that POINT TO SUB-PLANS rather than authored inline in the major plan. Each super-task entry below records ID, deliverable summary, sub-plan pointer (where the full task body / acceptance criteria live), high-level acceptance summary, reviewer assignments, and dependencies. Sub-plans are authored separately under `contracts/docs/superpowers/sub-plans/` and follow the same `feedback_three_way_review` discipline (CR + RC + TW for spec; CR + RC + Senior Developer for execution; Model QA Specialist added for econometric depth on β execution). The six super-tasks below (5 originally drafted + Task 11.P.MR-β.1 added in the post-author fix-up) are inserted into the major plan AFTER the Rev-5.3.2 task chain (post Task 11.O / Task 11.O-scope-update closure at commit `799cbc280`) and BEFORE Phase 2b dispatches in any track.

#### Task 11.O.NB-α — Rev-2 analytical work migrated to notebooks (super-task)

**Deliverable.** The Rev-5.3.2 Phase 5b analytical work currently shipped as script-form (commit `799cbc280`) is re-authored in 3-notebook form under `notebooks/abrigo_y3_x_d/`:

- `01_data_eda.ipynb` — Y₃ inequality-differential panel load + X_d fingerprint + joint-coverage diagnostics (matches FX-vol-CPI Colombia NB1 precedent at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/`).
- `02_estimation.ipynb` — Rev-2 mean-β primary estimation: 14-row resolution-matrix OLS+HAC(4) regression with the published Rev-5.3.2 panel `(source_methodology = y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable, window [2023-08-01, 2026-04-24])`.
- `03_tests_and_sensitivity.ipynb` — Specification tests T1 (exogeneity) / T2 (Levene) / T3a (placebo) / T3b (gate) / T4-T7 + 14-row sensitivity ladder + forest plot + anti-fishing material-mover spotlight gate.

Supporting scaffolding under `notebooks/abrigo_y3_x_d/`: `env.py` (path constants, version pins, seed helper, DuckDB connection helper); `references.bib` (citation-block source-of-truth, unified across α and β); `_nbconvert_template/` (PDF rendering template); `estimates/` (Rev-5.3.2 published JSON outputs cross-referenced from notebook execution); `figures/` (forest plot + diagnostic figures); `pdf/` (rendered notebook PDFs); `README.md` (Jinja2 auto-rendered summary mirroring the FX-vol-CPI Colombia README pattern).

**Sub-plan pointer.** Full task body, sub-task decomposition, citation-block discipline mapping, trio-checkpoint cadence, and acceptance criteria are authored in `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (TO BE AUTHORED — this Rev-5.3.3 block is the forward-pointer; sub-plan authoring happens after this CORRECTIONS block converges 3-way review).

**Acceptance summary.** Three notebooks execute end-to-end via `nbconvert --execute` against the published Rev-5.3.2 DuckDB state and reproduce the published 14-row estimates byte-exact (no re-estimation drift); all decision points carry the `feedback_notebook_citation_block` 4-part markdown block; the README auto-renders from a Jinja2 template fed by `gate_verdict.json` + estimates JSON; the gate verdict displays as **FAIL** consistent with Rev-5.3.2 Phase 5b. No new estimates are introduced under this task — it is a *re-presentation* of the published Rev-5.3.2 deliverable in notebook form.

**Subagent.** Analytics Reporter, per `feedback_notebook_trio_checkpoint`. Bulk authoring is FORBIDDEN; the agent HALTs after every (why-markdown, code-cell, interpretation-markdown) trio for user review before proceeding to the next trio. Data Engineer dispatch is allowed only for the supporting scaffolding (`env.py`, DuckDB helpers, `_nbconvert_template/` setup) where notebook-form is inappropriate.

**Reviewers.** Per-trio human review (user, in-loop) during authoring + post-notebook 3-way review (CR + RC + TW) on the assembled notebook deliverable per `feedback_three_way_review`. The post-notebook 3-way review acceptance is binary (PASS / BLOCK); BLOCK triggers the standard fix-up rewrite with the 3-cycle cap.

**Dependency.** Rev-5.3.3 plan revision landed (this CORRECTIONS block converged 3-way review). No upstream Rev-5.3.2 task is re-opened; the notebook migration consumes the published Rev-5.3.2 estimates and DuckDB state as fixed inputs.

#### Task 11.O.ζ-α — Rev-3 ζ-group convex-payoff extensions (super-task)

**Deliverable.** Rev-3 ζ-group spec + execution artifacts covering the four ζ rows enumerated in Rev-2 spec §10.6:

- ζ.1 — Quantile regression β̂(τ) at τ ∈ {0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95} (Koenker-Bassett 1978).
- ζ.2 — GARCH(1,1)-X with X_d in the conditional-variance equation; estimating `σ²_t(Y₃) = ω + α·ε²_{t-1} + β·σ²_{t-1} + δ·X_d,t`.
- ζ.3 — Lower-tail conditional moment regression `E[Y₃ | Y₃ < q_τ, X_d]` at τ ∈ {0.05, 0.10}.
- ζ.4 — Option-implied volatility surface fitting linking β̂ from this Rev-2 to actual / synthetic option premia under Black-Scholes basics + Heston / Bates extensions.

Each ζ row gets pre-registration discipline equivalent to Rev-2's 14-row matrix: pre-committed sign hypothesis, pre-committed FAIL sensitivities, anti-fishing-locked thresholds, CORRECTIONS-block discipline on any threshold modification. Execution artifacts are authored in the 3-notebook structure (NB1 data EDA + ζ-row fingerprint; NB2 ζ-row primary estimation; NB3 ζ-row specification tests + sensitivity).

**Sub-plan pointer.** Full Rev-3 spec authoring methodology (interactive structural-econometrics skill flow), per-ζ-row task decomposition, pre-registration discipline, Phase 5a/5b dispatch cadence, acceptance criteria, and reviewer assignment are authored in `contracts/docs/superpowers/sub-plans/2026-04-25-rev3-zeta-group.md` (TO BE AUTHORED).

**Authoring constraint.** The Rev-3 spec is authored INTERACTIVELY per the user's earlier deferral (the Option ε pattern from the disposition memo): user runs the structural-econometrics skill flow with the orchestrator; the spec is authored under `contracts/docs/superpowers/specs/2026-04-25-rev3-zeta-group-spec.md` (path finalized in the sub-plan). Autonomous-A spec authoring by an agent is FORBIDDEN for the Rev-3 spec; the user-driven flow is the binding methodology.

**Acceptance summary.** Each ζ row passes its own pre-committed gate at execution time (e.g., ζ.1 quantile sign-hypothesis gate at the relevant τ; ζ.2 δ̂ > 0 with HAC-bootstrap CI excluding zero; ζ.3 lower-tail compression gate; ζ.4 surface-fit RMSE bound). Convex-payoff insufficiency caveat (Rev-2 §11.A) is the load-bearing context: ζ-group results determine whether Abrigo can make convex-payoff product claims, NOT whether the mean-β FAIL is rescued. The mean-β FAIL stands; ζ-group is a separate stage of product validity.

**Scope constraint under Rev-5.3.3 — Mento-native ONLY.** Per pre-commitment 6 (§B), the ζ-group convex-payoff testing is scoped to **Mento-native stablecoins ONLY** (cCOP, USDm, EURm, BRLm, KESm, XOFm). Mixed Mento + non-Mento basket constructions are OUT OF SCOPE; ζ-group hypotheses, gate definitions, and sensitivity rows MUST be expressed against Mento-native instruments. The Rev-3 spec authoring under this task MUST cite pre-commitment 6 explicitly in its scope section.

**Reframe foundation under Rev-5.3.3 — TR Finding 2.** Per TR Finding 2 (Carbon DeFi protocol contracts ≈ 52% of cCOP Transfer events; UTC 13-17 NA-hours diurnal signature consistent with professional MM activity; ρ(X_d, fed_funds) = `−0.614`), the Rev-2 mean-β FAIL is fully consistent with the Carbon-DeFi-MM-as-X_d interpretation rather than retail-hedge-demand-as-X_d. The ζ-group is therefore now testing whether **tail-only hedge demand exists in Mento-native cCOP / USDm / etc.** — i.e., whether convex-payoff demand is observable in the residual signal AFTER the Carbon-DeFi-MM partition is acknowledged. The Rev-3 spec MUST acknowledge TR Finding 2 in its hypothesis-formation section and pre-register whether ζ rows operate against the unpartitioned Rev-2 X_d (testing tail behavior of the same global-liquidity-sensitive series) or against a Carbon-DeFi-MM-residualized X_d (testing tail behavior of the retail-only residual). The choice is a spec-level pre-commitment; Rev-5.3.3 does NOT pre-empt it but flags TR Finding 2 as the load-bearing analytical-framing input.

**Subagent.** TW or Senior Developer for spec authoring per the structural-econometrics skill flow (user-in-loop); Analytics Reporter for ζ-row execution per `feedback_notebook_trio_checkpoint` (HALT every trio).

**Reviewers.** CR + RC + TW for the Rev-3 spec per `feedback_three_way_review`; CR + RC + Senior Developer + Model QA Specialist for ζ-row execution (Model QA added for econometric depth on quantile regression / GARCH-X / conditional-moment estimation).

**Dependency.** Rev-5.3.3 plan revision landed. User direction on starting the interactive ε-flow (the structural-econometrics skill invocation) is the upstream gate; orchestrator does NOT pre-emptively author the Rev-3 spec. Independent of Track β; either track may converge first.

#### Task 11.P.MR-β — Mento user-base research (super-task — COMPLETED)

**Deliverable.** Evidence-grounded report on the actual Mento ecosystem user base — MiniPay, Valora, GoodDollar, peer-to-peer payments corridors, retail-consumption use cases, geography, transaction patterns, principal counterparties, observed user motives where documented. The report enumerates concrete signals (with sources) that constrain what an honest payments / consumption X_d hypothesis can be: who is actually using Mento basket assets on Celo, in what volumes, for what purposes, and what the on-chain signature of those uses looks like at the Carbon DeFi `carboncontroller` event log and adjacent contracts.

**Output path.** `contracts/.scratch/2026-04-25-mento-userbase-research.md` (delivered).

**Subagent.** Trend Researcher (`agentId = a7cd002b89b23e0ac`). The research is upstream of any β spec authoring; no spec is authored against speculation.

**Acceptance summary.** Report cites primary sources (Mento Labs documentation, MiniPay analytics, Valora analytics, GoodDollar analytics, on-chain analytics dashboards, Mento community channels where applicable) and synthesizes the user-base evidence into a finite list of hypotheses that the β spec can pre-commit to. Speculative claims are flagged as such; evidence-grounded claims are explicitly marked with citation. Reality Checker performs a single-pass advisory review (non-blocking, archival) verifying citation fidelity and identifying any uncited speculation that leaked into the report.

**Reviewers.** Reality Checker (single-pass advisory; non-blocking; archival). The Trend Researcher is the authoring subagent and the report is treated as a research input to Task 11.P.spec-β, not as an authoritative spec or plan artifact in its own right.

**Dependency.** None at the dispatch level. β spec authoring (Task 11.P.spec-β) is gated on this report's completion + the downstream provenance audit (Task 11.P.MR-β.1) below.

**Status.** **COMPLETED** — research output landed at `contracts/.scratch/2026-04-25-mento-userbase-research.md`. Four headline findings (summarized in §A above) reframe both Track α and Track β scope; downstream Task 11.P.MR-β.1 (NEW; provenance audit + memory corrigendum) is now BLOCKING for Task 11.P.spec-β.

#### Task 11.P.MR-β.1 — cCOP-vs-COPM provenance audit + memory corrigendum (super-task — NEW under Rev-5.3.3)

**Deliverable.** Three artifacts addressing the cCOP-vs-COPM naming clarification surfaced by TR Finding 3:

- **(a)** A formal audit of the DuckDB table `onchain_copm_transfers` documenting which contract address it tracks at the schema level (it tracks `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`, which is **Mento-native cCOP** per Celo forum source — NOT Minteo-fintech COPM as the table name suggests). The audit deliverable either renames the table to a Mento-native-aligned identifier (preferred) or adds explicit schema-doc comments clarifying that the table tracks Mento-native cCOP and that the historical "COPM" naming was a project-memory error. Decision between rename vs. doc-only is left to the Data Engineer subagent and the spec-review trio per the sub-plan.
- **(b)** A memory corrigendum at `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md` correcting the COPM entry. The corrigendum cites TR Finding 3 + the Celo forum source + the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` and explicitly states that the address resolves to Mento-native cCOP, not Minteo-fintech COPM.
- **(c)** Spec-doc updates noting the naming clarification in the X_d design doc at `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` (immutable in body; clarification adds an addendum-style note WITHOUT modifying the byte-exact pre-registered content) and any other plan / spec docs that reference COPM in a way that suggests Minteo-fintech rather than Mento-native cCOP. NO data changes are introduced by this task; the Rev-5.3.2 published estimates and DuckDB table contents remain byte-exact.

**Sub-plan pointer.** Full task body, audit methodology, table-rename-vs-doc decision criteria, corrigendum text, and spec-doc-addendum scope are authored in `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (TO BE AUTHORED, after this Rev-5.3.3 block converges 3-way review).

**Acceptance summary.** Audit deliverable (a) explicitly documents at the schema level which contract address `onchain_copm_transfers` tracks, with citation to TR Finding 3 + the Celo forum source. Corrigendum (b) lands in project memory with explicit cross-reference to the address and the source. Spec-doc updates (c) are addendum-style only (no byte-exact modification of pre-registered content); the Rev-2 published estimates and the `decision_hash` remain byte-exact. The downstream β spec (Task 11.P.spec-β) MUST cite this corrigendum in its hypothesis-formation section.

**Subagent.** Data Engineer (DuckDB schema audit + naming clarification + memory corrigendum text). No analytical / econometric work is involved; this is a naming / documentation / schema-doc clarification task.

**Reviewers.** CR + RC + Senior Developer per `feedback_implementation_review_agents` (the corrigendum is implementation-adjacent rather than spec-authoring; it touches schema docs, memory, and addendum-style spec doc updates without altering pre-registered analytical content).

**Dependency.** Task 11.P.MR-β COMPLETED (already done; see status above). This task is BLOCKING for Task 11.P.spec-β (the β spec cannot author a Mento-native-only hypothesis grounded in `project_mento_canonical_naming_2026` until the corrigendum lands and the table-naming clarification ships).

**Status.** PENDING — to be dispatched after this Rev-5.3.3 CORRECTIONS block converges 3-way review.

#### Task 11.P.spec-β — β hypothesis spec authoring (super-task)

**Deliverable.** Structural-econometric spec for the reframed payments / consumption X_d hypothesis. The spec is authored AFTER Task 11.P.MR-β returns; the X_d hypothesis pre-registered in the spec is GROUNDED in the Trend Researcher's evidence-cited findings (one of the finite hypothesis options enumerated in the research report, or an explicit synthesis of multiple). Spec follows the same structural-econometric pattern as Rev-2 (functional form, control set, identification claims, gate definitions, sensitivity ladder, anti-fishing pre-registration, acceptance criteria) but with a NEW X_d definition grounded in Mento user-base evidence rather than the Carbon DeFi basket-volume X_d.

**Sub-plan pointer.** Full β spec authoring methodology (interactive structural-econometrics skill flow per Option ε), pre-registration discipline, sensitivity matrix design, gate definitions, and reviewer assignment are authored in `contracts/docs/superpowers/sub-plans/2026-04-25-beta-spec.md` (TO BE AUTHORED, after Task 11.P.MR-β completes).

**Authoring constraint.** GROUNDED in the Mento user-base evidence (NOT speculation). User-driven structural-econometrics skill flow per the ε deferral; autonomous-A spec authoring by an agent is FORBIDDEN. The spec MUST cite the Trend Researcher's evidence-grounded findings explicitly in its hypothesis-formation section; speculative or evidence-thin hypotheses are anti-fishing-banned at the spec stage.

**Acceptance summary.** Spec passes 3-way review (CR + RC + TW) per `feedback_three_way_review`; pre-registration is byte-exact and immutable post-converge; gate definitions are explicit; sensitivity matrix is pre-committed before any data exploration on the new X_d variables.

**Scope constraint under Rev-5.3.3 — Mento-native ONLY.** Per pre-commitment 6 (§B), the β spec is constrained to **Mento-native stablecoins ONLY** (cCOP, USDm, EURm, BRLm, KESm, XOFm). Candidate retail-only X_d proxies the spec MAY pre-commit to (subject to TR-evidence grounding and the spec-review trio) include: cCOP holder-count delta on Celo; cCOP merchant transaction count POST-Carbon-DeFi-MM-filter (using the partition rule from `project_carbon_user_arb_partition_rule`); MiniPay Mento-Broker swap volume into Colombian / Brazilian / Kenyan / Eurozone / West-African corridors. Mixed Mento + non-Mento basket constructions are OUT OF SCOPE. Mixed Mento-fintech (Minteo COPM) instruments are OUT OF SCOPE.

**Reframe foundation under Rev-5.3.3 — TR Findings 1, 2, 3.** The β spec's hypothesis-formation section MUST explicitly cite TR Findings 1, 2, and 3 (summarized in §A above). The two candidate β-track hypothesis families surfaced by TR are: **(H1)** the retail-hedge thesis is FALSIFIED at the basket-aggregate level — X_d as currently constructed is an inverse-fed-funds proxy for NA-hours MM capacity (per Finding 2); the β spec might pre-register a STRUCTURAL-RECOGNITION test for H1 with appropriate gate definition; **(H2)** the retail-hedge thesis is PRESERVED with partition surgery — replace the current X_d with retail-only proxies (cCOP holder-count delta; cCOP merchant tx count post-Carbon-DeFi-MM filter; MiniPay Mento-Broker corridor swap volume per Finding 1); the β spec pre-registers a fresh sign hypothesis on the partitioned X_d. The spec MAY pre-commit to H1, H2, or an evidence-grounded synthesis; the choice is a spec-level pre-registration that the spec-review trio gates. Finding 1's ≈zero-aggregate-signal observation is the DOWNWARD adjustment the β spec MUST internalize on the MiniPay-aggregate-as-X_d hypothesis path; corridor-disaggregated MiniPay flows remain available as a partitioned candidate.

**Subagent.** TW or Senior Developer for spec authoring per the structural-econometrics skill flow (user-in-loop); Analytics Reporter for any preliminary EDA *only after the spec converges 3-way review* (no pre-spec exploration on candidate X_d variables — that would be p-hacking on the new hypothesis).

**Reviewers.** CR + RC + TW per `feedback_three_way_review` (spec-review trio).

**Dependency.** Task 11.P.MR-β COMPLETED + Task 11.P.MR-β.1 (cCOP-vs-COPM provenance audit + memory corrigendum) COMPLETED. The β spec cannot author a Mento-native-only retail-only hypothesis grounded in correctly-named DuckDB tables until the provenance-audit-and-corrigendum task lands.

#### Task 11.P.exec-β — β analytical execution (super-task)

**Deliverable.** Notebook-form execution of the β spec under `notebooks/abrigo_y3_x_d/beta/` (or a parallel namespace finalized in the sub-plan): NB1 data EDA + β-X_d fingerprint + joint-coverage diagnostics; NB2 primary estimation per the β spec's pre-committed regression; NB3 specification tests + sensitivity analysis + gate verdict + forest plot. Supporting scaffolding (any new DuckDB raw tables, fetcher helpers, etc.) is authored under the cross-track `notebooks/abrigo_y3_x_d/` scaffolding where shared, or under the `beta/` sub-namespace where β-specific.

**Sub-plan pointer.** Full β execution task decomposition (NB1 / NB2 / NB3 trio cadence; Phase 5a / 5b dispatch pattern; per-trio acceptance; Data Engineer helper boundaries; integration-test guard set per `feedback_strict_tdd`), reviewer assignments, and acceptance criteria are authored in `contracts/docs/superpowers/sub-plans/2026-04-25-beta-execution.md` (TO BE AUTHORED, after Task 11.P.spec-β converges).

**Acceptance summary.** β spec's pre-committed gate verdict ships in the assembled NB3 with full citation-block discipline; T1-T7-equivalent specification tests run per the β spec; sensitivity ladder is exhausted per pre-registration; forest plot ships; anti-fishing material-mover spotlight gate runs; gate verdict (PASS or FAIL) is the analytical close-out for β scope. β execution is INDEPENDENT of α (Rev-3 ζ-group) execution; results inform each other but neither blocks the other.

**Subagent.** Data Engineer (for fetcher / DuckDB / scaffolding helpers) + Analytics Reporter (for notebook authoring per `feedback_notebook_trio_checkpoint` HALT-every-trio discipline).

**Reviewers.** CR + RC + Senior Developer + Model QA Specialist (Model QA added for panel-econometrics depth on the β specification, especially if the β spec introduces panel structure / cross-currency aggregation / time-series methodology beyond the Rev-2 scope).

**Dependency.** Task 11.P.spec-β converged (3-way review PASS). Independent of Track α; either may converge first.

### D. Notebook discipline reaffirmation

The trio-checkpoint discipline applies to ALL notebook work in α and β tracks, with no exceptions. Specifically:

- **Citation block (4-part) precedes every test / decision / spec-choice.** The four parts are: (1) reference (citation: paper / textbook / project memory / prior decision); (2) why used (the analytical-method-fit rationale for choosing this method here, NOT a generic textbook description); (3) relevance to results (what this method's output specifically contributes to the gate verdict / sensitivity row / specification test outcome); (4) connection to product (how this analytical choice connects to Abrigo's convex-instrument-pricing / inequality-hedge product purpose). Per `feedback_notebook_citation_block`, this block is NON-NEGOTIABLE for estimation and sensitivity notebooks.
- **HALT after every (why-markdown, code-cell, interpretation-markdown) trio.** The Analytics Reporter authoring a notebook stops after each complete trio for explicit user review; the next dispatch only happens after the user closes the loop on the prior trio. Bulk authoring is forbidden per `feedback_notebook_trio_checkpoint`. This applies to NB1 / NB2 / NB3 in both α and β tracks.
- **No bulk authoring.** The Analytics Reporter MUST NOT author multiple trios in one dispatch; sub-plans MUST encode the trio cadence as the agent-dispatch unit.
- **User reviews each trio before next dispatch.** The orchestrator does NOT pre-empt user review; it dispatches the next trio only after explicit user approval of the prior trio.

The 3-notebook structure precedent from FX-vol-CPI Colombia (`contracts/notebooks/fx_vol_cpi_surprise/Colombia/`) is the authoring template:

- **NB1 — data EDA + panel fingerprint.** Load all upstream data inputs from DuckDB; compute panel fingerprint (row counts per `source_methodology` / window / proxy_kind); diagnose joint coverage; produce panel diagnostic plots; emit a panel-fingerprint JSON consumed by NB2 and NB3.
- **NB2 — primary estimation.** Execute the spec's pre-committed primary regression(s); emit per-row estimates JSON consumed by NB3; produce the headline-coefficient table.
- **NB3 — specification tests + sensitivity analysis.** Run T1-T7 specification tests per the spec; exhaust the pre-committed sensitivity ladder; produce the forest plot; run the anti-fishing material-mover spotlight gate; emit the final gate-verdict JSON; auto-render the README from a Jinja2 template fed by the gate-verdict + estimates JSONs.

The README auto-render pattern (Jinja2 template + machine-readable verdict JSON → human-readable summary) is preserved across α and β tracks. Each track's README is authored under its own notebook subdirectory and points back to the top-level major-plan / Rev-5.3.3 cross-references.

### E. Cross-track scaffolding

The shared scaffolding is established at `notebooks/abrigo_y3_x_d/` and consumed by both Track α (Tasks 11.O.NB-α, 11.O.ζ-α) and Track β (Task 11.P.exec-β):

| Scaffolding artifact | Purpose | Cross-track use |
| --- | --- | --- |
| `env.py` | Path constants, version pins, seed helper, DuckDB connection helper, plot-style helper | All α + β notebooks import from this single source-of-truth |
| `references.bib` | BibTeX source-of-truth for all citation blocks | All α + β citation blocks resolve against this single bibliography |
| `_nbconvert_template/` | PDF rendering template (preserves citation blocks + figures with proper LaTeX-style formatting) | Both α + β notebooks render to PDF via this shared template |
| `estimates/` | Per-track JSON outputs from primary estimation + gate verdict | Track-namespaced subdirectories (e.g., `estimates/rev2_meanbeta/`, `estimates/rev3_zeta/`, `estimates/beta_payments/`) |
| `figures/` | Per-track diagnostic + forest-plot figures | Track-namespaced subdirectories |
| `pdf/` | Rendered notebook PDFs | Track-namespaced subdirectories |
| `README.md` (top-level) | Cross-track index pointing to per-track READMEs + major-plan cross-references | Single top-level entry-point auto-rendered from per-track verdict JSONs |

Sub-plans (the six Rev-5.3.3 super-task sub-plans, including Task 11.P.MR-β.1 added in the post-author fix-up) MUST enumerate scaffolding additions / modifications in their own §E-equivalent sections; new scaffolding artifacts MUST be added to the table above in a future Rev-5.3.4 (or later) CORRECTIONS block before consumption by a downstream track.

### F. Task count + status reconciliation under Rev-5.3.3

Rev-5.3.2 active task count (per the existing reconciliation block above): **69** active tasks (excluding the 1 deliberate non-task placeholder from Task 11.N.2d.2-NEW; total headers under Rev-5.3.2 = 71 inclusive of placeholder + retired-as-audit). Rev-5.3.3 introduces the following changes:

- **+6 new task IDs with super-task bodies pointing to sub-plans** (Task 11.O.NB-α — Rev-2 notebook migration; Task 11.O.ζ-α — Rev-3 ζ-group convex-payoff extensions; Task 11.P.MR-β — Mento user-base research, status COMPLETED; Task 11.P.MR-β.1 — cCOP-vs-COPM provenance audit + memory corrigendum, NEW under Rev-5.3.3; Task 11.P.spec-β — β hypothesis spec authoring; Task 11.P.exec-β — β analytical execution).
- **+0 modified tasks at the body level.** The Rev-5.3.2 14-row resolution-matrix scope (mean-β regression) is the published baseline and is not retroactively modified by Rev-5.3.3. Task 11.O / Task 11.O-scope-update / Task 11.O.NB-α form a chain where the Rev-5.3.2 published deliverable (script-form) is the upstream input to the notebook migration (Task 11.O.NB-α); the Rev-5.3.2 task bodies are not re-opened. Scope-amendments to Task 11.O.ζ-α and Task 11.P.spec-β under Rev-5.3.3 are SCOPE-CONSTRAINT additions (Mento-native-only + TR-Findings-grounding) layered onto the existing super-task bodies; they do not modify the super-task IDs or upstream Rev-5.3.2 acceptance criteria.
- **+0 retired tasks.** Rev-5.3.2 task chain is preserved byte-exact.
- **+0 new placeholder non-tasks.** All six new super-tasks are dispatched super-tasks (each points to a sub-plan that decomposes its own sub-tasks; sub-task counts live in the corresponding sub-plans, not in the major plan tally).

Rev-5.3.3 active task count: **69 + 6 = 75** (excluding the deliberate non-task placeholder from Rev-5.3.2); total headers in the major plan: **71 + 6 = 77**. The previously-acknowledged +3 accounting drift documented at line 1739 (Rev-5.3.1's banner figure preserved as-such pending a row-by-row rebuild) propagates unchanged through Rev-5.3.3 and resolves at the future Rev-5.4 row-by-row refresh per amendment-rider A8 (unchanged by this revision). Sub-plan task counts (the per-sub-task decompositions inside each of the six Rev-5.3.3 super-tasks' sub-plans) are accounted for inside those sub-plans and are NOT folded into the major-plan tally — the major plan tracks super-tasks; sub-plans track sub-tasks. This separation is the user-directed structure: "the plans might not be isolated, and there must be a major plan, which is the one that we constructed earlier" — major plan = super-tasks; sub-plans = sub-task detail.

### G. Reference paths

- HALT-disposition memo (path α + β user selection): `contracts/.scratch/2026-04-25-task110-rev2-gate-fail-disposition.md` (commit `c1eec8da5`)
- Rev-2 spec (Phase 5b primary spec; convex-payoff caveat §11.A; ζ-group roadmap §10.6; pivot map §11.C): `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`
- Rev-2 Phase 5b primary estimates commit (gate verdict T3b = FAIL; published baseline): `799cbc280`
- 4-reviewer gate close-out commits: `6b1200dcb` (RC + Model QA PASS-class) + `f38f1aad3` (CR + SD PASS-class)
- Trend Researcher Mento user-base research output (DELIVERED; load-bearing for Tasks 11.P.MR-β.1, 11.O.ζ-α scope-amendment, 11.P.spec-β scope-amendment): `contracts/.scratch/2026-04-25-mento-userbase-research.md`. Four headline findings: (1) MiniPay = swap rail, USDt-dominated, ≈0 macro-hedge signal at aggregate; (2) Carbon DeFi MM ≈ 52% of cCOP Transfer events with NA-hours diurnal signature, BIS-WP-1219/1340-consistent macro-substitution interpretation; (3) cCOP ≠ COPM, address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` is Mento-native cCOP per Celo forum source; (4) audit-trail disclosure — three prompt-injection attempts in WebFetch / WebSearch output observed and correctly ignored by the Trend Researcher subagent.
- Sub-plan forward-pointers (TO BE AUTHORED, post Rev-5.3.3 3-way review convergence):
  - Task 11.O.NB-α sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
  - Task 11.O.ζ-α sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-rev3-zeta-group.md`
  - Task 11.P.MR-β.1 sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md`
  - Task 11.P.spec-β sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-beta-spec.md`
  - Task 11.P.exec-β sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-beta-execution.md`
- Rev-5.3.2 CORRECTIONS block (precedent format; immediately above this block): inline above at 2026-04-25, commit chain `c5cc9b66b` + `2a0377057`
- Rev-3 spec target path (TO BE AUTHORED, post Task 11.O.ζ-α spec authoring): `contracts/docs/superpowers/specs/2026-04-25-rev3-zeta-group-spec.md`
- β spec target path (TO BE AUTHORED, post Task 11.P.spec-β spec authoring): `contracts/docs/superpowers/specs/2026-04-25-beta-spec.md`
- Notebook scaffolding root (TO BE CREATED under Task 11.O.NB-α): `notebooks/abrigo_y3_x_d/`
- FX-vol-CPI Colombia notebook precedent (3-notebook structure + README auto-render pattern): `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` (see project memory `project_fx_vol_cpi_notebook_complete`)
- Project memory anchors load-bearing on Rev-5.3.3:
  - `feedback_no_code_in_specs_or_plans` (code-agnostic body discipline)
  - `feedback_three_way_review` (spec/plan review discipline)
  - `feedback_implementation_review_agents` (CR + RC + SD on implementation-adjacent corrigendum work; Task 11.P.MR-β.1 reviewer assignment)
  - `feedback_specialized_agents_per_task` (every task dispatches a specialized subagent)
  - `feedback_notebook_citation_block` (4-part citation discipline)
  - `feedback_notebook_trio_checkpoint` (HALT every trio; bulk authoring forbidden)
  - `feedback_strict_tdd` (failing-test-first; integration-test guards)
  - `feedback_pathological_halt_anti_fishing_checkpoint` (HALT-disposition-pivot-CORRECTIONS-review chain)
  - `project_fx_vol_econ_complete_findings` (analytical-discipline-vindication pattern; predictive-not-structural diagnostic)
  - `project_abrigo_convex_instruments_inequality` (product purpose: convex (option-like) inequality-hedge instruments)
  - `project_mdes_formulation_pin` (MDES_FORMULATION_HASH immutability; free-tuning anti-fishing-banned)
  - `project_abrigo_mento_native_only` (NEW under Rev-5.3.3 — Abrigo scope is Mento-native stablecoins ONLY; Minteo-fintech COPM out of scope; user scope-tightening directive 2026-04-25; load-bearing for §A trigger paragraph 4 + §B pre-commitment 6 + Tasks 11.O.ζ-α / 11.P.spec-β scope-amendments)
  - `project_mento_canonical_naming_2026` (CORRIGENDUM TARGET under Rev-5.3.3 — the COPM entry of this memory carries a NAMING error; the data the entry references is correct (Mento-native cCOP at address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` per TR Finding 3) but the memory's "COPM" labeling is wrong; corrigendum scoped under NEW Task 11.P.MR-β.1)
  - `project_carbon_user_arb_partition_rule` (load-bearing for the H2 partitioned-X_d candidate hypothesis in Task 11.P.spec-β; partition rule = `trader = 0x8c05ea30…` field)
- Audit-trail disclosure (per TR Finding 4): the Trend Researcher subagent observed three prompt-injection attempts embedded in third-party content returned via WebFetch / WebSearch during Mento-user-base research; the agent correctly ignored the injection attempts and disclosed them in its report. This is recorded here as defensive-behavior audit-trail evidence; no remediation action is required of the Rev-5.3.3 plan.
- MDES_FORMULATION_HASH (immutable through Rev-5.3.3, sha256): `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`
- Rev-4 decision_hash (immutable through Rev-5.3.3): `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`

---

## CORRIGENDUM — Rev-5.3.4 (2026-04-25, post-Rev-5.3.3 token-attribution correction)

**Trigger.** During the Rev-5.3.3 author + fix-up cycle, the Trend Researcher (`a7cd002b89b23e0ac`) returned with Finding 3 stating that *cCOP* is the Mento-native Colombia token and *COPM* is a separate Minteo-fintech B2B/API token. The fix-up TW (`afee8ee7a426a0d4a`) and the foreground orchestrator propagated TR's attribution into Rev-5.3.3 §A / §B / §C / §G + into the new memory note `project_abrigo_mento_native_only`. **The user corrected this attribution 2026-04-25**: "is COPM not cCOP" — i.e., COPM IS the Mento-native Colombia token; cCOP (whatever the TR was identifying) is OUT of scope along with all other non-Mento-native tokens. Pre-existing project memory `project_mento_canonical_naming_2026` ("COPM and XOFm unchanged; address-level identity preserved") was correct all along.

**Scope of correction.** Wherever Rev-5.3.3 cites cCOP as the Mento-native token at address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`, read it as **COPM** (Mento-native). Wherever Rev-5.3.3 §A / §B / §G implies project memory `project_mento_canonical_naming_2026` was wrong about COPM identity, that implication is RETRACTED — the original memory was correct. The Trend Researcher's external-source attribution (Finding 3 in `contracts/.scratch/2026-04-25-mento-userbase-research.md`) had inverted token identity; that file remains in the audit trail but with this corrigendum noted as the authoritative override.

**Substantively unchanged.** The Rev-2 X_d data integrity is unaffected — `onchain_copm_transfers` correctly tracks Mento-native COPM at the cited address. The 14-row resolution-matrix scope, all anti-fishing invariants (N_MIN=75, MDES_FORMULATION_HASH, Rev-4 decision_hash), the 6 super-task plan structure, the BLOCKING relations, and the Track-α / Track-β architecture are all preserved byte-exact. Only the token-identity attribution language is corrected.

**Updated memory state.**
- `project_abrigo_mento_native_only.md` rewritten with the corrigendum as section 1; authoritative content (COPM = Mento-native) as section 2.
- `MEMORY.md` index entry updated to reflect the correction.
- `project_mento_canonical_naming_2026.md` requires NO corrigendum — it was correct all along.

**Implications for Task 11.P.MR-β.1 (cCOP-vs-COPM provenance audit).** Still useful, with rescope: the audit's deliverable changes from "correct the project memory naming error" (no longer needed) to "formally lock the on-chain address registry for the Mento-native basket — COPM at `0xc92e8fc2…` plus the post-rebrand USDm/EURm/BRLm/KESm/XOFm addresses — with a single canonical reference document." The TR's external-source confusion remains a useful artifact: it documents that public Celo-forum / similar third-party content can disagree on token identity, so any future research that cites such sources should cross-check against the on-chain registry the audit will establish.

**Reviewer cycle.** This corrigendum is a 2-paragraph clarification to a published plan revision; per the project's editorial-discipline pattern (cf. `project_carbon_user_arb_partition_rule` corrigendum precedent), it does NOT require a new 3-way review cycle — it is committed by the foreground orchestrator with the scope tightly bounded to "fix attribution language; no substantive plan-content change." If a downstream reviewer disagrees with this scope-bounding, they can raise it in any subsequent Rev-5.3.x review and the corrigendum can be re-reviewed retroactively.

**File anchors corrected.** Rev-5.3.3 §G's `project_mento_canonical_naming_2026` entry should be read as "EXISTING (correct as authored)" not "CORRIGENDUM TARGET". Rev-5.3.3 §A's TR Finding 3 paragraph stands as audit-trail evidence of the (now-overridden) external-source attribution.

---

## CORRECTIONS — Rev-5.3.5 (2026-04-26, post-MR-β.1 sub-task 1 HALT-VERIFY β resolution)

**Trigger.** MR-β.1 sub-task 1 (DE deliverable `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` at commit `3611b0716`) fired a HALT-VERIFY GATE on the canonical Mento-native Colombian-peso address. RC spot-check (commit `3286dfe66`) returned **PASS** with a non-binding β-advisory. Foreground orchestrator ran a Dune empirical probe (query `7378788`, free tier, 0.012 credits) against `celocolombianpeso_celo.stabletokenv2_evt_transfer` to confirm β-track Rev-3 data feasibility. **User picked path β**: adopt `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` as canonical Mento V2 `StableTokenCOP`; classify `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` as Minteo-fintech (out of Mento-native scope per `project_abrigo_mento_native_only`).

**Empirical evidence (Dune probe, 2026-04-26):**

| Address | Project (Dune) | Total transfers | Distinct senders | Distinct receivers | First / last | Weeks active |
|---|---|---|---|---|---|---|
| `0x8A567e2a…` | `celocolombianpeso` (StableTokenV2) | 285,390 | 5,015 | 16,918 | 2024-10-31 → 2026-04-26 (live) | **78** ≥ N_MIN=75 |
| `0xc92e8fc2…` (Rev-2 X_d source) | (Minteo-fintech, no Mento decoder) | 110,253 | (existing) | (existing) | 2024-09-17 → 2026-04-25 | 76 |

The Mento-native address has **2.6× more transfer events** than the Rev-2-ingested address; presence of `evt_exchangeupdated` and `evt_validatorsupdated` events on `0x8A567e2a…` is by itself dispositive of Mento-protocol-native status (these are Mento-specific governance events; a third-party fintech contract would not expose them).

**Scope of correction. Rev-2 closes as scope-mismatch, NOT "tested-and-failed."**

The Rev-2 published estimates (β̂ = −2.7987e−8, n = 76, T3b FAIL, MDES_FORMULATION_HASH `4940360dcd2987…cefa`, Rev-4 decision_hash `6a5f9d1b05c1…443c`) remain **byte-exact immutable** per Rev-5.3.x anti-fishing invariants; they are NOT re-estimated, re-binned, re-thresholded, or otherwise edited. What changes is the **interpretation framing**:

- Wherever Rev-5.3.0–Rev-5.3.4 framed Rev-2 as "Mento-hedge-thesis-tested-and-failed," read as **"Minteo-fintech-X_d-was-scope-mismatched."** The X_d series ingested for Rev-2 was Minteo-fintech volume (out of Mento-native scope under the user's directive); the FAIL verdict therefore reflects scope-mismatch, not a test of the Mento-native hedge thesis.
- The three Rev-2 anomalies surfaced by Phase 5b Model QA + RC adversarial probe (sign-flip β̂ < 0; ρ(X_d, fed_funds) = −0.614 confounder; T1 REJECTS predictive-not-structural) are now cleanly explained by Minteo-fintech being a payments / B2B-API rail rather than Mento-basket hedge volume. The anomalies are NOT "negative evidence on Mento-native hedge demand"; they are "Minteo activity has its own different signature."
- The Rev-2 disposition memo (`contracts/.scratch/2026-04-25-task110-rev2-gate-fail-disposition.md`) gate-FAIL framing is **superseded** by this scope-mismatch framing. The 5 disposition options (α/β/γ/δ/ε) enumerated there are also superseded — under Rev-5.3.5, β-track Rev-3 starts fresh against the correct on-chain address; the prior options were premised on the (now-corrected) interpretation that Rev-2 had tested the Mento-native thesis.

**Cascade — Task 11.P.MR-β.1 sub-plan rescope.**

The MR-β.1 sub-plan (`contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md`) carries an atomic CORRECTIONS block under Rev-5.3.5 reflecting:

1. **Sub-task 1 deliverable** records BOTH addresses: `0x8A567e2a…` as in-scope Mento-native COPm (Mento V2 StableTokenCOP); `0xc92e8fc2…` as out-of-scope Minteo-fintech COPM-Minteo (preserved in audit trail; the 110,253 transfers we ingested for Rev-2 remain in DuckDB unchanged). Provenance fields per address. The DE's existing inventory at commit `3611b0716` is preserved as a research artifact and is consumed (not overwritten) by the rescoped sub-task 1 re-dispatch.
2. **Sub-task 2** every `onchain_*` table sourced from `0xc92e8fc2…` (the entire `onchain_copm_*` family + `carbon_per_currency_copm_volume_usd` proxy_kind) is tagged **DEFERRED-via-scope-mismatch** under the existing DIRECT/DERIVATIVE/DEFERRED scheme. No table is dropped, renamed, or migrated (per consume-only DuckDB invariants). The deferral framing is: these tables hold Minteo-fintech data, which is out of Mento-native scope but preserved as historical research evidence.
3. **Sub-task 3 registry** scopes only `0x8A567e2a…` as canonical Mento-native COPm; documents `0xc92e8fc2…` in an explicit **"out-of-scope third-party tokens (audit-trail preservation)"** appendix section. The registry doc body enumerates only Mento-native tokens (COPm, USDm, EURm, BRLm, KESm, XOFm); the appendix preserves the Minteo entry for traceability.
4. **Sub-task 4 TR corrigendum** is sharpened: Finding 3 had two layers of inversion — the TR's "cCOP-vs-COPM" attribution was inverted (corrected by user 2026-04-25), AND the rescoped Rev-5.3.4 framing of "0xc92e8fc2 = Mento-native COPM" was itself wrong (corrected by user + empirical evidence 2026-04-26). The corrigendum block in the TR research file documents both layers.
5. **Sub-task 5 future-research safeguard** is unchanged in scope but gains a cited-precedent: the Rev-5.3.4 attribution flip + Rev-5.3.5 address-level disambiguation jointly demonstrate that token-identity attribution from third-party sources requires on-chain triangulation (Dune decoded-table catalog + Mento Labs official deployment docs + Celo Token List, all cross-checked).

**Cascade — α-track NB-α sub-plan rescope (interpretation only).**

The NB-α sub-plan (`contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`) 31 dispatch units carry forward unchanged for **byte-exact migration of Rev-2 numbers** (panels, gate verdicts, T1–T7, sensitivity). What changes: every `why-markdown / code-cell / interpretation-markdown` trio under NB-α whose interpretation cell currently frames Rev-2 as "Mento-hedge-thesis-tested-and-failed" must be reframed to **"Minteo-fintech scope-mismatch close-out."** Concretely: NB1 §0 panel-fingerprint validation cells, NB2 estimation-row interpretation cells, NB3 sensitivity-row interpretation cells. Numbers stay byte-exact; framing changes. Authoring scope: minimal interpretation-cell text edit; no panel re-construction, no re-estimation, no gate-verdict re-evaluation. The NB-α sub-plan's CORRECTIONS block under Rev-5.3.5 documents this reframe.

**Cascade — β-track Rev-3 ingestion plumbing (deferred to Task 11.P.spec-β / Task 11.P.exec-β).**

β-track Rev-3 needs new ingestion plumbing pointed at `0x8A567e2a…`. The existing scripts (`econ_pipeline.py`, `econ_schema.py`, `query_api.py`) reference the Minteo address; they are **NOT mutated** under MR-β.1 (consume-only DuckDB invariant). New ingestion plumbing is in scope for Task 11.P.spec-β (spec authoring) + Task 11.P.exec-β (implementation). Both sub-plans remain not-yet-on-disk at Rev-5.3.5 authoring time and will be authored post-MR-β.1 convergence per the existing sub-plan-discipline pattern.

**Cascade — Task 11.O.ζ-α (Rev-3 ζ-group convex-payoff extensions).**

Held for user-driven structural-econometrics interactive flow per ε deferral. Rev-5.3.5 does not re-open this hold; the convex-payoff fitness test under ζ-α can run on either Rev-2 (Minteo-scope) data as a sanity check or on β-track Rev-3 (Mento-native) data once available. The user's prior decision to defer ζ-α stands; this CORRECTIONS block does not modify that.

**Anti-fishing-invariant integrity.**

No invariant is relaxed:

- N_MIN = 75 unchanged.
- POWER_MIN = 0.80 unchanged.
- MDES_SD = 0.40 unchanged.
- MDES_FORMULATION_HASH = `4940360dcd2987…cefa` unchanged.
- Rev-4 decision_hash = `6a5f9d1b05c1…443c` unchanged (binds to Rev-2 published estimates, byte-exact preserved).
- Rev-2 14-row resolution-matrix scope unchanged (byte-exact preserved).

This CORRECTIONS block is a **scope correction**, not a threshold relaxation. β-track Rev-3 starts fresh under all the same anti-fishing thresholds against the correct on-chain address.

**Memory state at Rev-5.3.5 convergence.**

- `project_mento_canonical_naming_2026.md` — appended β-corrigendum block at top; original COPM entry preserved with ⚠️ SUPERSEDED inline marker.
- `project_abrigo_mento_native_only.md` — appended β-corrigendum block at top; "OUT of scope" + "Mento-native canonical names" + "How to apply" sections updated inline to flip the COPM address.
- `MEMORY.md` index — both entries refreshed with β-corrigendum hooks.

**Reviewer cycle.**

Per `feedback_pathological_halt_anti_fishing_checkpoint`: HALT-VERIFY → user-enumerated pivot β → CORRECTIONS block (this section + sub-plan CORRECTIONS) → **post-hoc 3-way review (CR + RC + TW per `feedback_three_way_review`)** on the disposition. The 3-way review is dispatched immediately after this CORRECTIONS block is committed; convergence is required before re-dispatching MR-β.1 sub-task 1 under the rescoped framing.

**File anchors.**
- HALT-VERIFY disposition memo: `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`.
- DE inventory at HALT firing: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (commit `3611b0716`).
- RC spot-check: `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` (commit `3286dfe66`).
- MR-β.1 sub-plan CORRECTIONS: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` §I (Rev-5.3.5 atomic CORRECTIONS block).
- NB-α sub-plan CORRECTIONS: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (Rev-5.3.5 atomic CORRECTIONS block, interpretation-cell-reframe scope).
- Dune query: `7378788` (β-feasibility probe).
- Dune project: `celocolombianpeso_celo.stabletokenv2_*` (24 decoded tables).
- Mento V3 deployments docs (StableTokenCOP canonical address; working URL post-RC-3 verification): https://docs.mento.org/mento-v3/build/deployments/addresses.md . The earlier-cited URL `https://docs.mento.org/mento/protocol/deployments` 404s and is superseded.
- Celo Token List (chainId 42220): https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json .

**Post-trio fix-up (Rev-5.3.5 fix-up commit, 2026-04-26).** All three reviewers converged: CR returned NEEDS-WORK with one blocker (NB-α §B-6 retraction hook, addressed in NB-α CORRECTIONS); RC and TW returned PASS-with-non-blocking-advisories. Bundle fix-up applied: NB-α §B-6 retraction hook added; NB-α grep-deterministic banned/canonical substring sets added per TW-2a; MR-β.1 §G addendum referencing §I CORRECTIONS added per TW-7; disposition memo §4.2 cross-reference tightened to §G-3 per TW-6b; disposition memo + this major plan reference list updated to working Mento V3 docs URL per RC-3 finding; disposition memo §4.2 RC-8 forward-looking joint-coverage note added (β-track Rev-3 joint-N is 73 weeks vs N_MIN=75 — closeable by Y₃ refresh ≥3 weeks before β-spec freeze; deferred to β-spec authoring per `feedback_pathological_halt_anti_fishing_checkpoint` discipline). RC-only single-pass re-review on the fix-up bundle is dispatched post-commit; convergence then unblocks MR-β.1 sub-task 1 re-dispatch.
