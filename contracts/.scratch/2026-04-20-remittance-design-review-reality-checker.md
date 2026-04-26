# Remittance-Surprise → TRM RV Design — Reality Checker Review

**Reviewer**: TestingRealityChecker (Reality Checker discipline)
**Target**: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md`
**Date**: 2026-04-20
**Scope**: factual-claim verification only; methodology and internal consistency deferred to peer reviewers.

---

## 1. Executive verdict

**PASS-WITH-FIXES** (leaning BLOCK on one data-availability claim).

The design is honest about inheritance, pre-commitment, and the anti-fishing frame, and the most load-bearing citations (CPI-FAIL verdict, inherited scripts, memory rules, corpus painkiller evidence) survive audit. However, one **BLOCK-severity** factual claim — that the BanRep **US-corridor monthly** remittance series is publicly available at monthly frequency via `datos.gov.co` — is contradicted by the corpus on a file the design itself cites. If this goes into the Rev-1 spec uncorrected, Phase-1 data ingestion will stall on day one. Two further claims (Y×X matrix winner and engine-integration sketch) overstate what the source reports actually support.

---

## 2. BLOCK-severity findings

### B1. "BanRep US-corridor monthly remittance via datos.gov.co" is not what the corpus says

Design line 118 claims Phase-1 "acquires BanRep remittance monthly aggregate (US-corridor subset) via public `datos.gov.co` Socrata endpoint." Design §3 (line 45) grounds the whole primary RHS on this US-corridor subset.

Corpus contradicts directly at `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` lines 113-115:

> **Monthly**: Family remittance totals (crossed $1B/month threshold June 2024)
> **Corridor breakdown**: Available in Monetary Policy Reports and special blog posts, but NOT as a downloadable monthly time series by country of origin

Agent 3 (`.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md` line 35) confirms: BanRep publishes "country-of-origin breakdown quarterly; corridor-level monthly not as a single CSV but reconstructible from Monetary Policy Report tables." Row 1 of the ranked table also says "BanRep monthly aggregates + corridor quarterly."

**Fix required before plan phase 1**: either (a) drop "US-corridor subset" and run the primary on the all-country monthly aggregate, documenting the loss of corridor-specificity, or (b) pre-commit a reconstruction procedure (Monetary Policy Report table scraping + Basco-Ojeda-Joya Borrador 1273) with an explicit vintage-hash and accept quarterly→monthly temporal disaggregation inside the LockedDecisions. Option (a) is strictly cleaner; option (b) introduces a reconstruction-SE term that must be priced into T3b.

Severity: BLOCK — this is the RHS column.

### B2. Y×X "unambiguous winner A1" overstates the source reports

Design line 18 says the matrix produced "a single unambiguous winner: remittance-flow surprise → TRM weekly realized volatility (row A1)."

The source reports disagree:
- Agent 3 (`next-primary-candidate-ranked.md` §3) picks **Colombia-side remittance surprise** as #1 for Y₁ TRM RV.
- Agent 4 (`Y2-CPI-Y3-remittance-X-ranking.md` §5) picks **US Hispanic-employment surprise** as #1 for Y₃.
- Agent 5 (`fixed-X-vary-Y-ranking.md` §4 + §6) picks **(COPM mint/burn, Y₃)** as the triangulated flagship SHIP cell.
- Y×X memory `project_colombia_yx_matrix.md` lines 55-61 presents **three option sets (α/β/γ)** to the user, "awaiting selection as of this memory write." A1 is in all three but never called unambiguous; the foreground actually recommended **β (A1+A3+B1+B3)**.

A1 is defensible as the off-chain-calibration anchor; it is not a unanimous winner. Calling it "unambiguous" is the rhetorical move the anti-fishing protocol is supposed to resist. Recommend: reword to "chosen off-chain calibration anchor; A3 (Hispanic-emp) and B1 (COPM mint/burn) remain triangulated companions deferred to Phase-A.1."

Severity: BLOCK — frames the pre-commitment dishonestly.

---

## 3. FLAG-severity findings

### F1. Engine-integration sketch for A1 proposes different controls than the design

Agent 3 (`next-primary-candidate-ranked.md` §4 sketch #1) says "drop Oil" and "add US BLS Hispanic employment share monthly" for the remittance-surprise row. The design §3 (line 52) keeps the six Rev-4 controls verbatim (including Oil) and adds only the one new RHS column. The source-cited rationale is not applied. Either adopt Agent 3's control-set change and justify, or explicitly override it with a preservation-of-Rev-4-hash argument. Currently silent on the deviation.

### F2. "Revision-resistant rolling-averaged" is asserted but not defined

Design §3 line 45 says the surprise is built from "real-time vintage, revision-resistant rolling-averaged" data. Agent 3 §6 risk #3 and design §Risks #1 both flag the 3-month revision window. Unclear which: real-time-vintage OR rolling-averaged. These are different constructions. Spec-time decision required.

### F3. Novelty claim relies on a single agent's two web queries

Design (implicit via memory citation) rests "no prior DeFi variance swap on stablecoin flow volume" on `LITERATURE_PRECEDENTS.md` §9 + Agent 5 queries 1-2. The claim is defensible for on-chain *flow-volume* variance but the current design's LHS is **TRM realized vol** (an asset-price variance on an FX series), for which substantial prior literature exists (Ghysels-Sohn, Andersen-Bollerslev et al. on FX RV). The novelty claim should be scoped: "novel on Colombia-specific remittance-surprise → FX-vol identification," not "novel on FX-vol derivative." Minor rhetorical inflation.

### F4. Anti-fishing defense is correct but under-cited

Design line 92 asserts remittance is a distinct mechanism, not a CPI rescue. Supporting evidence exists and should be cited inline: `REMITTANCE_VOLATILITY_SWAP.md` is dated **2026-04-02** (mtime verified), seventeen days before CPI-FAIL on 2026-04-19. The entire `REMITTANCE_VOLATILITY_SWAP/` corpus and the pre-committed-but-unrun Reiss-Wolak spec at `notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` are pre-FAIL artifacts. This is the single strongest defense against rescue-framing and deserves a one-sentence citation in §Pre-commitment point 11.

---

## 4. NIT-severity findings

### N1. "100K Littio users" (design Risks §4) conflates two figures

`COPM_MINTEO_DEEP_DIVE.md` §1.5: "Over 200,000 Colombians use Littio"; "100K figure specifically refers to Colombians using COPM via the Littio platform." Design should write "100K COPM-via-Littio users, $200M/mo COPM volume."

### N2. "Jan 2025 Trump-Petro +100%/48h" — source says Littio account growth

`OFFCHAIN_COP_BEHAVIOR.md` §1 line 17: "Littio reported 100%+ growth in 48 hours." The source is Littio's self-report relayed through Colombia-One reporting, not a primary dataset. Design should say "Littio self-reported 100%+ account growth" to preserve the reporting-layer caveat.

### N3. `gate_verdict.json` does not contain β̂

Design line 10 points to the verdict file; that file carries only verdict booleans. The β̂ = −0.000685 + CI come from `project_fx_vol_cpi_notebook_complete.md` "Primary OLS Column 6" block. Cite both.

### N4. Y×X memory path format

Design cites `~/.claude/projects/.../memory/project_colombia_yx_matrix.md`. The actual absolute path is `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_colombia_yx_matrix.md`. The `...` obscures a specific path that a future-agent needs.

---

## 5. Fact-audit table

| # | Claim | Verified in | Verdict |
|---|---|---|---|
| 1 | CPI gate_verdict=FAIL | `notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` L3, `memory/project_fx_vol_cpi_notebook_complete.md` L16-33 | TRUE |
| 2 | β̂_CPI=−0.000685, 90% CI contains 0 | `memory/project_fx_vol_cpi_notebook_complete.md` L36-42 | TRUE (but not in gate_verdict.json directly — NEEDS-CAVEAT) |
| 3 | Three-agent Y×X on 2026-04-20 | 5 files under `.scratch/2026-04-20-*.md`, `memory/project_colombia_yx_matrix.md` | TRUE |
| 4 | A1 = "unambiguous winner" | Source reports present option set α/β/γ, not a unanimous winner | FALSE (see B2) |
| 5 | Inherited Rev-4 artifacts exist | `notebooks/fx_vol_cpi_surprise/Colombia/{01,02,03}*.ipynb`, `scripts/{cleaning,nb2_serialize,gate_aggregate,render_readme,panel_fingerprint}.py` all present | TRUE |
| 6 | BanRep US-corridor monthly, public, free on datos.gov.co | `COLOMBIAN_ECONOMY_CRYPTO.md` L113-115 + Agent 3 query #10 | FALSE (see B1) |
| 7 | 13 cited memory files exist | `memory/MEMORY.md` L1-33; all 13 verified line-by-line | TRUE |
| 8 | 5-instance silent-test-pass pattern | `memory/project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md` L12 "five silent-test-pass patterns" | TRUE |
| 9 | Remittance channel pre-dates CPI-FAIL | `REMITTANCE_VOLATILITY_SWAP.md` mtime 2026-04-02; CPI-FAIL 2026-04-19 | TRUE (under-cited, see F4) |
| 10 | 100K Littio users + $200M/mo COPM | `COPM_MINTEO_DEEP_DIVE.md` §1.5, §2 tables | TRUE-WITH-CAVEAT (N1) |
| 11 | Jan 2025 Trump-Petro +100%/48h | `OFFCHAIN_COP_BEHAVIOR.md` L17, L101 | TRUE-WITH-CAVEAT (N2: Littio self-report) |
| 12 | Novelty: no prior DeFi variance swap on stablecoin flow volume | `LITERATURE_PRECEDENTS.md` §9 L416-420, Agent 5 queries 1-2 | TRUE (under-scoped, see F3) |
| 13 | Remittance monthly pull simpler than alternatives (feasibility rank) | Agent 3 §2 L52 + query #10 | UNVERIFIABLE as "simpler"; TRUE that it is free; NEEDS-CAVEAT that it requires Monetary-Policy-Report scraping for corridor breakdown |

---

## 6. Positive findings (preserve in Tech-Writer fix pass)

- Anti-fishing discipline is articulated correctly (§Pre-commitment 11, Risks §5) and the remittance channel genuinely pre-dates the CPI-FAIL exercise — this is a real, not rhetorical, distinction.
- All seven inherited Rev-4 script/notebook citations (§Methodology inheritance) are verified on disk.
- All 13 memory-rule citations correspond to files catalogued in `memory/MEMORY.md`.
- Scripts-only scope (§Scope line 40) correctly carries over `feedback_scripts_only_scope.md`.
- Integration-test guard citation (§Pre-commitment 9) correctly invokes the 3-notebook nbconvert-execute pattern from the silent-test-pass lessons memo.
- Revision-vintage risk (§Risks #1), regime-change 2015 (§Risks #3), and Petro-Trump event-dummy registration (§Risks #4) are all grounded in explicit corpus lines.
- Decision-hash extension (§Methodology L76, §Risks #7) is the right additive pattern for preserving the frozen Rev-4 panel without invalidation.

---

**End. Word count ≈ 1,175.**
