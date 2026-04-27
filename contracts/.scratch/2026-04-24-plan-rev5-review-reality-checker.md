# Rev-5 Plan — Reality Checker Review

**Target:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `8db00fe74`  
**Reviewer:** Reality Checker (empirical + feasibility lens)  
**Date:** 2026-04-24  
**Verdict:** **NEEDS WORK** (2 BLOCKs, 4 FLAGs, 2 NITs)

## 1. Feasibility table

| ID | Claim (plan line) | Evidence path | Pass? | Required fix |
|---|---|---|---|---|
| RC-P1 | `Y_asset_leg = (Banrep_rate − Fed_funds)/52 + ΔTRM/TRM` is computable from "Rev-4 panel controls already in hand" (L9, L22, L133). | `contracts/scripts/econ_schema.py:73` `fred_daily` CHECK constraint: `series_id IN ('VIXCLS','DCOILWTICO','DCOILBRENTEU')`. Neither DFF nor FEDFUNDS is allowed. `econ_panels.py` LEFT JOIN on fred_daily is only for VIXCLS + DCOILWTICO. | **FAIL (BLOCK)** | Fed funds rate is NOT in the DuckDB store and is schema-rejected. Rev-5 must (a) extend `econ_schema.py` CHECK constraint to include DFF (or FEDFUNDS/EFFR — pick one and justify), (b) add a FRED ingestion task, (c) extend `build_weekly_panel` to weekly-aggregate Fed funds. This is NEW off-chain data work, not "already in hand." |
| RC-P2 | `banrep_rate` level is available. | `econ_panels.py:143–148` — what's stored is `banrep_rate_surprise` (event-study daily Δ-IBR summed over the week), NOT the policy rate level. IBR daily is in `banrep_ibr_daily` but panel projects only the event-study delta. | **FAIL (BLOCK)** | Plan conflates `banrep_rate` (level) with `banrep_rate_surprise` (event-study delta). Y_asset_leg needs the level. Add a separate `ibr_level_weekly` column in `econ_panels.build_weekly_panel`, or explicitly use `intervention_rate` — either way, a new panel column is required. Flag as Phase 2b prerequisite, not additive. |
| RC-P3 | `/52` annualized-to-weekly conversion. | Plan line 22, 133 — no justification given for linear `/52` vs geometric `(1+r)^{1/52}-1`. | **FLAG** | For weekly diffs of annualized rates below 15% p.a., the approximation error is <1 bp — acceptable. But pre-commit the choice in Task 11.O Step 1 and cite a textbook reference (Hull, Ch 4, or Bodie-Kane-Marcus). Do NOT leave it implicit — the sensitivity analysis in NB3 should include a `geometric_weekly_conversion` row. |
| RC-P4 | `ΔTRM/TRM_{t-1}` simple return interpretation of "carry return". | Plan L9, L22, L133. | **FLAG** | For weekly TRM the COP/USD realized range is up to ±5% → log vs simple deviation ≥ 12 bp per observation — compounds over a 947-obs panel. Either use log-returns `ln(TRM_t/TRM_{t-1})` (matches Rev-4 NB1 RV construction, which is cube-rooted log-RV) or justify simple returns with a citation. Task 11.O Step 1 must pre-commit. |
| RC-P5 | 11.M.5 claim: `varbinary for addresses` (plan L98). | `contracts/data/copm_per_tx/copm_mints.csv:2` shows addresses as hex strings `0x...`. Existing `econ_schema.py` uses `VARCHAR` for all string-like fields (see `meeting_type VARCHAR`, `series_id VARCHAR`). No VARBINARY precedent in the codebase. | **FLAG** | Use `VARCHAR` (or `CHAR(42)`) for addresses to match codebase convention and preserve CSV lossless-load property. VARBINARY forces hex-string→bytes conversion at ingest — a conversion-layer bug surface with no performance payoff for a ≤100k-row table. Fix Task 11.M.5 Step 2 wording. |
| RC-P6 | 11.L arxiv MCP availability. | `~/.arxiv-mcp-server` directory exists; `~/.cache/uv/archive-v0/.../arxiv_mcp_server-0.4.11.dist-info` present; `~/.claude/CLAUDE.md`: "When researching academic papers, prioritize the arxiv MCP server over web search." Global rule honored by plan. | **PASS** | None. |
| RC-P7 | 11.L arxiv coverage for Colombian labor-vs-capital / Atkinson-Piketty-Saez. | Not locally verifiable. Latin-American macro inequality literature is concentrated in Banrep Borradores de Economía, DANE publications, and CEPAL in Spanish — mostly NOT on arxiv. Piketty/Solt/Campbell-Cochrane have extensive arxiv coverage. | **FLAG (LIT_SPARSE_Colombia)** | Task 11.L Step 1 is realistic for Piketty-r>g, Campbell-Cochrane, Lettau-Ludvigson (arxiv-rich). Colombia-specific macro and consumption-growth research is sparse on arxiv; the "flag `LIT_SPARSE_<topic>` and expand WebSearch" fallback (L62) correctly anticipates this. Tighten by pre-listing: Banrep Borradores de Economía URL (https://www.banrep.gov.co/es/publicaciones-investigaciones/borradores-economia), DANE microdata portal, CEPAL Serie Macroeconomía del Desarrollo. |
| RC-P8 | 11.O MDES scipy.stats.ncf correctness (plan L135). | Independent root-find: `brentq(lambda lam: 1 - ncf.cdf(f.ppf(0.90,6,72), 6, 72, lam) - 0.80, 0.1, 50)` → **λ = 11.9678**. At df₂=65 → λ = 12.0602. Spec λ≈13 is overstated by ~8%. | **PASS** | None. The Rev-5 MDES-correction pre-commitment (Task 11.O Step 3) is arithmetically vindicated. |
| RC-P9 | `decision_hash = 6a5f9d1b05c1…443c` preserved byte-exact (Task 11.Q Step 1, plan L167). | `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23` confirms exact hash. | **PASS** | None. |
| RC-P10 | 11.M background agent `aa0bf238c4ca1b501` "in flight" (plan L66, L72). | File mtimes: `copm_mints.csv` 2026-04-24 07:31:50; `copm_burns.csv` 07:37:26. Current system time 09:27:08. **Agent has been silent for 1h 50m.** Only 2/4 deliverables landed; transfers + freeze_thaw CSVs absent; provenance README absent; structural-profile .scratch absent. | **FAIL (BLOCK)** | `AGENT_STALLED` signal — 1h 50m idle exceeds any reasonable Dune-MCP polling latency. Plan Rev-5 is executing downstream tasks (11.N depends on `load_onchain_copm_transfers()`) on a dependency that has not arrived. Add Task 11.M Step 0: "verify agent liveness; if silent >1h, escalate or relaunch before dispatching 11.N." 11.N MUST NOT dispatch until 11.M CSVs + README all present (explicit gate). |
| RC-P11 | 11.N depends on 11.M transfers CSV (plan L108). | 11.M deliverable list (plan L73-L76) shows transfers CSV "in flight." 11.N Step 1 classifies B2B/B2C via role-graph from transfers + `tokenv1_evt_rolegranted`. | **FAIL (was PASS pre-stall, now BLOCK)** | With 11.M stalled, 11.N has a missing-input dependency. Add explicit ordering assertion in plan L108 or 11.M Step 3: "Task 11.N MUST NOT dispatch until all 4 CSVs + `copm_per_tx/README.md` + `2026-04-24-copm-per-tx-profile.md` are committed." Currently this is implicit. |
| RC-P12 | Tier-2 consumption leg (DANE EMMV + BanRep HDS) deferred "out of scope" (plan L9, L171). | DANE EMMV: manually queryable via `https://www.dane.gov.co/index.php/estadisticas-por-tema/comercio-interno/encuesta-mensual-de-comercio-emc` — monthly series, zip-based microdata releases, NO stable API. BanRep HDS: series `IPEC_HOGARES` on suameca; quarterly only. | **PASS (with NIT)** | Deferral is correct. NIT: the plan should mention that DANE EMMV has no API and BanRep HDS is quarterly — same cadence issue that killed the remittance plan. The tier-2 work-stream will face a cadence-bridge problem (monthly → weekly or quarterly → weekly) identical to the remittance-exercise bridge that failed. Flag in 11.Q tier-2 footnote. |
| RC-P13 | 11.M.5 CSV column-hash test (Step 1 a/b). | CSVs have stable column order by construction (CSV headers are ordered); DuckDB `CREATE TABLE` preserves insert order; per-column checksum via `md5(column)` is deterministic IF (i) CSV row-order is stable, (ii) DuckDB does not re-sort on INSERT (it doesn't by default). | **PASS (with NIT)** | Tighten test: pin insertion-order via `ORDER BY` on a unique key (e.g., `call_tx_hash`) to avoid non-deterministic ingest ordering if the CSV is ever regenerated. Currently the test is order-dependent on the CSV file bytes, not the underlying tx-set. Add `ORDER BY call_block_number, call_tx_hash` in the round-trip assertion. |
| RC-P14 | `CREATE TABLE IF NOT EXISTS` idempotent pattern (plan L99). | `econ_schema.py:31,39,47,62,72,81,90,99,108,120,130` all use `CREATE TABLE IF NOT EXISTS`. | **PASS** | None. Task 11.M.5 follows precedent. |

## 2. Numerical verifications (paste)

**λ root-find (Task 11.O MDES claim):**
```
scipy.stats.ncf / scipy.stats.f root-find (df1=6, α=0.10, power=0.80):
  df2=72 → λ = 11.9678
  df2=65 → λ = 12.0602
Spec Rev-1.1.1 claim: λ ≈ 13 → overstates by ~8%.
Rev-5 Task 11.O Step 3 correction: VALIDATED.
```

**Decision-hash preservation (Task 11.Q claim):**
```
$ sed -n '23p' contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json
  "decision_hash": "6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c",
MATCH — plan L167 citation exact.
```

**Schema CHECK constraint (BLOCK RC-P1):**
```
$ sed -n '73p' contracts/scripts/econ_schema.py
  series_id VARCHAR NOT NULL CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU')),
Fed funds rate NOT in allowed set.
```

**Agent stall (BLOCK RC-P10):**
```
Now:               2026-04-24 09:27:08 EDT
copm_mints.csv:    2026-04-24 07:31:50 (1h 55m idle)
copm_burns.csv:    2026-04-24 07:37:26 (1h 50m idle)
copm_transfers.csv, copm_freeze_thaw.csv, README.md, profile.md: MISSING
```

## 3. Sparse-claim flags

- **LIT_SPARSE_Colombia** (RC-P7): Colombia-specific macro-inequality literature is not arxiv-native; plan fallback exists but should enumerate Banrep Borradores / CEPAL explicitly.
- **DANE_EMMV_NO_API** (RC-P12 NIT): tier-2 acknowledgment should note the monthly→weekly cadence bridge will require a design process analogous to the failed remittance exercise.
- **WEEKLY_RATE_CONVENTION_UNPINNED** (RC-P3, RC-P4): `/52` and `ΔTRM/TRM` conventions unpinned — must pre-commit in Task 11.O Step 1.

## 4. Summary

Rev-5 plan's **scientific arithmetic** (λ correction, decision-hash, idempotent schema) is verified correct. The plan's **feasibility premise** — that Y_asset_leg is computable from existing Rev-4 panel — is WRONG: Fed funds is schema-rejected and Banrep rate level is not a materialized panel column (only the event-study surprise is). This is a BLOCK that inflates Rev-5's task count beyond the claimed "additive-only, no new off-chain fetch." Secondary BLOCK: background agent 11.M is stalled at 1h 50m idle; 11.N has a missing dependency. 4 FLAGs on dtype convention (varbinary→varchar), rate-conversion pre-commitment, literature sparsity escape hatch, and column-hash test ordering.

Fix the 2 BLOCKs + 4 FLAGs; plan is then production-worthy. Recommend Rev-5.1 patch with: (i) new Task 11.R for Fed-funds + Banrep-rate-level panel extension (dependency of 11.O/11.Q), (ii) explicit 11.M liveness gate before 11.N dispatch, (iii) VARCHAR address dtype in 11.M.5, (iv) pre-committed `/52` + simple-vs-log-return choice in 11.O Step 1 with sensitivity row in NB3.

---

**Report path:** `contracts/.scratch/2026-04-24-plan-rev5-review-reality-checker.md`
