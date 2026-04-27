---
spec_sha256: <to-be-pinned-after-Task-0.3>
plan_verifier_wave1: PASS-WITH-REVISIONS / Reality Checker / agent-id ad0b3d8d2134f0002 / 2026-04-27
plan_verifier_wave2: PASS-WITH-REVISIONS / Senior Project Manager / agent-id ad19cc84a99ce8018 / 2026-04-27
revision_history:
  - v1 2026-04-27 initial draft
  - v2 2026-04-27 integrate RC + SPM verifier defects (RC 2a/2b/3a/3b/6a + SPM D1-D6 + RC OOS-1)
---

# P1 — SN18 Cortex.t Alpha Event Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Per project convention `feedback_no_code_in_specs_or_plans`, this plan is code-agnostic; implementation specifics are deferred to executor sub-agents per task. Per `feedback_specialized_agents_per_task`, each task names the specialist that owns it.

**Goal:** Empirically test whether α_18 (Bittensor Subnet 18 / Cortex.t dTAO subnet token) returns respond to proprietary-AI provider (Anthropic Claude, OpenAI GPT) policy events, producing a falsifiable feasibility verdict (PASS / FAIL / INDETERMINATE) that determines slow-lane Abrigo disposition.

**Architecture:** Pre-registered event study with methodology baseline from Maymin (2026, arXiv:2603.29751). The pre-registered spec (hypothesis, falsification criteria, thresholds, sample selection rules) is committed and sha256-pinned BEFORE any data is pulled or analysis is run. SN64 (Chutes — open-source decentralized inference comparator), aggregate TAO, and ETH serve as controls. Output is a prototype-result memo subject to three-way implementation review regardless of verdict (anti-fishing discipline carries forward from Phase-A.0).

**Tech stack (specialist-side; out-of-plan-scope):** Python notebooks under the existing `contracts/notebooks/` convention with the trio-checkpoint discipline (`feedback_notebook_trio_checkpoint`) and 4-part citation block per decision (`feedback_notebook_citation_block`); DuckDB for panel storage per the existing `contracts/scripts/` ingestion convention; structured event-set JSON; final memo as Markdown.

**Anti-fishing invariants (immutable through P1):**
- Spec sha256-pin set in Phase 0 and quoted in every downstream artifact's frontmatter
- Significance thresholds set in spec, never tuned during analysis
- HALT-disposition memo required if any threshold-tuning impulse arises mid-analysis
- Three-way review of result memo regardless of PASS/FAIL/INDETERMINATE outcome
- All raw data preserved with provenance metadata; no silent re-pulls

**Scope:** 2-3 weeks of dedicated effort per the Bittensor-Claude bridge research. **The 2-3 week claim assumes parallel dispatch per the explicit annotations in Phases 1-2 AND ≤1 HALT-disposition cycle in Phase 3; add 1 calendar week per additional HALT cycle.** NOT a production-grade hedge instrument; a feasibility prototype with falsifiable verdict that informs slow-lane disposition (P2 escalation, P3 escalation, defer 6-12 months, pivot X, kill).

**Source artifacts (read before executing):**
- `contracts/.scratch/2026-04-27-bittensor-claude-bridges-prototype-modeling.md` — P1 design source; substrate hierarchy; canonical SN18 docs quote ("Neither the miner or the validator will function without a valid and working OpenAI API key")
- `contracts/.scratch/2026-04-27-onchain-proxies-for-proprietary-ai-cost.md` — prior signal-research report; documents what failed (broad-basket basis risk dominance) and the substitution-vs-complement directional finding that P1 must respect
- `contracts/.scratch/2026-04-27-x-candidates-latam-wage-to-capital-transition.md` — broader X-research context; AI-cost is Candidate #13 (slow-lane) outside the report's macro-X enumeration
- `.worktree/ranFromAngstrom/CLAUDE.md` — Abrigo Operating Framework section (Y, M, X triples); active iteration block
- Maymin (2026) "Subnet CPMM Size Premium and the Halving" — arXiv:2603.29751 — methodology baseline

---

## File Structure

**Created by this plan:**

```
contracts/docs/superpowers/specs/2026-04-27-p1-sn18-event-study-design.md
  Pre-registered spec. Hypothesis, falsification criteria, methodology,
  thresholds, sample-selection rules, sha256-pinned formulation.

contracts/.scratch/p1-sn18-event-study/
  events/
    anthropic_events.json    Anthropic policy events 2024-2026, with
                             timestamp + event-type + URL + brief
    openai_events.json       Same for OpenAI
    events_panel.json        Merged + de-duplicated event panel
    EVENTS_PROVENANCE.md     Source attribution + assembly methodology
  data/
    alpha_18_ohlcv.parquet   SN18 dTAO α_18 OHLCV from taostats.io
    alpha_64_ohlcv.parquet   SN64 (Chutes) α_64 OHLCV — open-source comparator
    tao_ohlcv.parquet        Aggregate TAO price (control)
    eth_ohlcv.parquet        ETH price (broader risk-on/off control)
    DATA_PROVENANCE.md       Source URLs, pull timestamps, schema
  notebooks/
    01_eligibility.ipynb     Event-eligibility filter per spec
    02_event_panel.ipynb     Final event panel construction + visualization
    03_event_study.ipynb     Primary event-window analysis per spec
    04_robustness.ipynb      Robustness checks per spec (windows, controls)
  output/
    PRIMARY_RESULTS.md       Primary result table + significance
    ROBUSTNESS_RESULTS.md    Robustness result table
    MEMO.md                  Final prototype-result memo with verdict
    gate_verdict.json        Machine-readable verdict (PASS/FAIL/INDETERMINATE)
```

**Modified by this plan:**

```
.worktree/ranFromAngstrom/CLAUDE.md
  "Active iteration" block updated post-Phase 4 with verdict + slow-lane
  disposition pointer.
```

---

## Phase 0: Pre-Registration

Goal: produce a sha256-pinned spec that fixes the hypothesis, methodology, thresholds, and sample-selection rules BEFORE any data is touched. Anti-fishing discipline.

### Task 0.1: Author pre-registered spec

**Owner:** Model QA Specialist (drafts), with Foreground Orchestrator (oversight)

**Files:**
- Create: `contracts/docs/superpowers/specs/2026-04-27-p1-sn18-event-study-design.md`

- [ ] **Step 1: Specialist drafts the spec.** Sections required: (1) Background and motivation; (2) Hypothesis statement (H₀ / H₁); (3) Falsification criteria — what observations would force PASS, FAIL, INDETERMINATE; (4) Sample-selection rules (event eligibility, exclusion criteria, time window, **N_MIN_EVENTS — minimum count of in-window events required for the analysis to proceed; HALT triggered if not met after data pull**); (5) Methodology (event-window length, abnormal-return calculation, control-series choice, multiple-testing correction); (6) Pre-registered significance thresholds (one-sided / two-sided, α level, multiple-testing-adjusted); (7) Robustness checks pre-committed (alternative windows, alternative controls, sub-sample splits, **explicit treatment of the Dec 2025 Bittensor halving as in-sample shock per Maymin 2026 — its 1.17%→0.51% size-premium effect (p=0.044) is the largest known non-event-set shock and must be controlled for**); (8) Verdict-decision tree mapping result to PASS / FAIL / INDETERMINATE; **the tree MUST address the (verdict × robustness_consistency) cross-product — in particular, a primary PASS with DISAGREE robustness must be downgraded to INDETERMINATE unless the spec pre-commits a tie-break rule**; (9) Anti-fishing invariants (no threshold tuning, no event-set re-curation post-data, HALT-disposition path).

- [ ] **Step 2: Orchestrator reviews draft for code-agnosticism + completeness.** Spec must reference Maymin 2026 methodology with explicit divergences noted. No placeholder text; no "TBD". Verdict-decision tree must be deterministic given any (test-statistic, p-value, robustness_consistency) input. **Verify the Maymin (2026) arXiv ID — `2603.29751` may be a typo for `2503.29751` (March 2025); orchestrator confirms the correct ID before sha256 pin.**

- [ ] **Step 3: Compute spec sha256.** Hash the spec file content; record in spec frontmatter as `decision_hash`. This pins the spec — future references quote this hash.

### Task 0.2: 2-wave verification on spec

**Owner:** Foreground Orchestrator dispatches; Reality Checker + Model QA Specialist execute

**Files:**
- Read: `contracts/docs/superpowers/specs/2026-04-27-p1-sn18-event-study-design.md`

- [ ] **Step 1: Dispatch Reality Checker (Wave 1) on spec.** Charge: verify hypothesis claims are evidence-grounded; flag any unsupported assertion about SN18 economics or proprietary-AI event impact; demand citation for every claim about prior empirical work.

- [ ] **Step 2: Dispatch Model QA Specialist (Wave 2) on spec.** Charge: verify methodology is statistically sound; check for spec-leakage (event set defined post-hoc), multiple-testing under-correction, control-series confounds, sample-period cherry-picking. The spec's anti-fishing invariants must hold against the specialist's adversarial reading.

- [ ] **Step 3: Integrate findings.** PASS / PASS-WITH-REVISIONS / BLOCK per the v2 verdict-combination rule. Revisions applied inline; spec sha256 re-computed if revisions change normative content.

### Task 0.3: Commit spec

**Owner:** Foreground Orchestrator

**Files:**
- Modify: spec file (frontmatter sha256 + verifier verdict refs)

- [ ] **Step 1: Update spec frontmatter** with final sha256, both verifier verdicts, and verifier-agent IDs.

- [ ] **Step 2: Commit spec.** Commit message includes the `Doc-Verify:` trailer per the user-intended v2 audit-trail rule (spirit-over-letter discipline; v2 itself is paused but its intent governs all in-scope doc writes within this plan).

- [ ] **Step 3: Quote spec sha256 in this plan's frontmatter.** This plan now references the pinned spec immutably.

---

## Phase 1: Event set assembly

Goal: produce a defensible, pre-registered event panel of proprietary-AI policy events 2024-2026 with timestamps + types + URLs + brief.

### Task 1.1: Eligibility-criteria filter

**Owner:** Trend Researcher (drafts criteria); Orchestrator (approves)

**Files:**
- Read: `contracts/docs/superpowers/specs/2026-04-27-p1-sn18-event-study-design.md` §4 (sample-selection rules)

- [ ] **Step 1: Specialist extracts eligibility criteria from the spec** verbatim. Output: a one-page criteria summary that the event-assembly tasks will apply mechanically.

- [ ] **Step 2: Orchestrator confirms criteria are unambiguous AND that Trend Researcher's tool capabilities cover all source classes named in Tasks 1.2 / 1.3 source lists.** If a source class is uncovered (e.g., status.openai.com requires structured incident scraping, X/Twitter requires API access Trend Researcher lacks), dispatch general-purpose agent for that class only, with Trend Researcher merging output. Any judgment call in eligibility itself is a defect — return to spec authors for tightening.

> **Parallel-dispatch annotation:** Tasks 1.2 (Anthropic) and 1.3 (OpenAI) operate on independent data sources with the same specialist class. Dispatch them as two distinct parallel Trend Researcher subagent instances per `superpowers:dispatching-parallel-agents`. Each writes its own JSON; Task 1.4 merges.

### Task 1.2: Anthropic event panel

**Owner:** Trend Researcher

**Files:**
- Create: `contracts/.scratch/p1-sn18-event-study/events/anthropic_events.json`

- [ ] **Step 1: Specialist surveys Anthropic's public communication channels** (anthropic.com news, anthropic.com pricing changelog, X/Twitter @AnthropicAI, status.anthropic.com incident history, public press) for the period spec-defined (typically 2024-01-01 through 2026-04-27).

- [ ] **Step 2: Specialist applies eligibility criteria from Task 1.1** to each candidate event; rejects ineligible events with one-line reason.

- [ ] **Step 3: Specialist outputs structured JSON** with one record per event: timestamp (UTC, ISO-8601), event_type (price_change | rate_limit_change | model_launch | model_deprecation | tos_change | capacity_event | other), one-line description, source URL.

- [ ] **Step 4: Specialist writes the assembly methodology section** of `EVENTS_PROVENANCE.md` documenting which sources were checked, which were excluded, and any judgment calls invoked.

### Task 1.3: OpenAI event panel

**Owner:** Trend Researcher

**Files:**
- Create: `contracts/.scratch/p1-sn18-event-study/events/openai_events.json`

- [ ] **Step 1-4: Same as Task 1.2 but for OpenAI.** Sources: openai.com pricing changelog, openai.com blog, X/Twitter @OpenAI / @sama, platform.openai.com docs revision history, status.openai.com.

### Task 1.4: Merged panel + de-duplication

**Owner:** Trend Researcher

**Files:**
- Read: `anthropic_events.json`, `openai_events.json`
- Create: `contracts/.scratch/p1-sn18-event-study/events/events_panel.json`

- [ ] **Step 1: Specialist merges the two event JSONs into a single panel.** Adds `provider` field (anthropic | openai). Sorts chronologically.

- [ ] **Step 2: Specialist de-duplicates near-coincident events** (same day, same provider, same event_type) per spec rules.

- [ ] **Step 3: Specialist flags clustered events** (multiple events in a short window per spec) — these may need joint-event-window treatment in Phase 3.

- [ ] **Step 4: Specialist appends to `EVENTS_PROVENANCE.md`** the merge methodology, de-duplication decisions, and cluster-flag listing.

- [ ] **Step 5: Reality Checker review** of the panel. Charge: verify each event's source URL resolves and the event description matches the source. No fabricated events.

- [ ] **Step 6: Commit events directory** with provenance attribution.

---

## Phase 2: Data acquisition

Goal: pull all price/return series required by the spec, with clean schema, provenance metadata, and verified data quality.

> **Parallel-dispatch annotation:** Tasks 2.1 (α_18 pull) and 2.2 (control series pulls — α_64, TAO, ETH) operate on independent data sources with the same specialist class. Dispatch them as two distinct parallel Data Engineer subagent instances per `superpowers:dispatching-parallel-agents`. Tasks 2.3 + 2.4 are sequential after both parallel pulls land.

### Task 2.1: α_18 OHLCV from taostats.io

**Owner:** Data Engineer

**Files:**
- Create: `contracts/.scratch/p1-sn18-event-study/data/alpha_18_ohlcv.parquet`
- Create section in `DATA_PROVENANCE.md`

- [ ] **Step 1: Specialist identifies the taostats.io API endpoint** for SN18 dTAO α_18 OHLCV. Confirms historical depth (dTAO launched in late 2025; α_18 series begins at that boundary).

- [ ] **Step 2: Specialist pulls the full available range** at the highest frequency the API supports (target: hourly; fallback: daily). Logs API request URLs + response timestamps to `DATA_PROVENANCE.md`.

- [ ] **Step 3: Specialist persists to parquet** with a strict schema documented in provenance: `(timestamp_utc, open, high, low, close, volume_tao, volume_usd)`. Timestamps tz-aware UTC.

- [ ] **Step 4: Reality Checker spot-check** — pull a known recent day from the API independently and confirm row matches the parquet. No silent data corruption.

### Task 2.2: Control series

**Owner:** Data Engineer

**Files:**
- Create: `contracts/.scratch/p1-sn18-event-study/data/alpha_64_ohlcv.parquet`
- Create: `contracts/.scratch/p1-sn18-event-study/data/tao_ohlcv.parquet`
- Create: `contracts/.scratch/p1-sn18-event-study/data/eth_ohlcv.parquet`

- [ ] **Step 1: Specialist pulls SN64 (Chutes) α_64 OHLCV** from taostats.io with same schema as Task 2.1. SN64 is the structurally-clean substitute comparator (open-source decentralized inference).

- [ ] **Step 2: Specialist pulls aggregate TAO price** from CoinGecko or comparable source. This isolates SN18-specific moves from broader Bittensor-network moves.

- [ ] **Step 3: Specialist pulls ETH price** from CoinGecko / Pyth / Chainlink. This isolates from broader crypto-risk-on/off moves.

- [ ] **Step 4: Specialist documents each pull** in `DATA_PROVENANCE.md`.

### Task 2.3: Panel construction

**Owner:** Data Engineer

**Files:**
- Modify: `DATA_PROVENANCE.md` to document panel construction
- (Panel may be persisted as DuckDB table or as a wide parquet — specialist's call within the existing contracts/scripts convention)

- [ ] **Step 1: Specialist aligns all four series** to common timestamps using the highest available common frequency.

- [ ] **Step 2: Specialist computes log returns** for each series and persists alongside levels.

- [ ] **Step 3: Specialist documents alignment choices** (forward-fill, missing-day handling, dTAO-launch boundary truncation) in `DATA_PROVENANCE.md`.

### Task 2.4: Data quality verification

**Owner:** Reality Checker (independent of Data Engineer)

**Files:**
- Read: all data files; create `DATA_QC.md` in same directory

- [ ] **Step 1: Reality Checker independently spot-checks** five random days per series against the source API. Documents any divergence.

- [ ] **Step 2: Reality Checker scans for missing days, outlier returns** (e.g., ±50% in a single bar) and writes a one-page QC summary noting any anomalies the analysis must handle.

- [ ] **Step 3: Reality Checker verifies the dTAO-launch boundary** is consistently treated across α_18 and α_64 series.

- [ ] **Step 4: Reality Checker computes count of Phase-1 events that fall within the α_18 data window.** If count `< N_MIN_EVENTS` (set in spec §4 per Task 0.1), HALT and dispatch spec amendment via the 2-wave rule before any Phase 3 work begins. The dTAO launch boundary truncates the sample window severely; this gate is non-negotiable per anti-fishing discipline.

- [ ] **Step 5: Commit data directory** with all provenance + QC files.

---

## Phase 3: Event study execution

Goal: execute the pre-registered event study mechanically, producing primary and robustness result tables. Trio-checkpoint discipline per `feedback_notebook_trio_checkpoint` — Analytics Reporter HALTS after every (why-markdown, code-cell, interpretation-markdown) trio for orchestrator review.

### Task 3.1: Notebook scaffolding

**Owner:** Analytics Reporter

**Files:**
- Create: notebooks/01_eligibility.ipynb, 02_event_panel.ipynb, 03_event_study.ipynb, 04_robustness.ipynb (skeletons only)
- Create: notebooks/env.py (paths, dependencies, citation-block template)
- Create: notebooks/references.bib (Maymin 2026 + spec references)

- [ ] **Step 1: Specialist sets up the env module** following the existing `contracts/notebooks/abrigo_y3_x_d/env.py` pattern (parents-fix landed at commit `865402c2c` per CLAUDE.md). Paths point to the p1 .scratch directory.

- [ ] **Step 2: Specialist creates references.bib** with at minimum: Maymin (2026, arXiv:2603.29751); the SN18 / Cortex.t / Corcel project documentation; the Abrigo P1 spec (with sha256 pin); any prior subnet-economics references the spec cites.

- [ ] **Step 3: Specialist creates notebook skeletons** with section headers matching the spec's analysis sections. Each notebook starts with the 4-part citation block (`feedback_notebook_citation_block`) for its first decision.

- [ ] **Step 4: Commit scaffolding only.** No analysis content yet.

### Task 3.2: Notebook 03 — primary event study

**Owner:** Analytics Reporter (with mandatory trio-checkpoint HALTs)

**Files:**
- Modify: notebooks/03_event_study.ipynb

- [ ] **Step 1: First trio — event-window construction.** Markdown why-block (citation block per spec); code cell that constructs (event, time-relative-to-event, return-window) panel per spec; markdown interpretation-block. **HALT for orchestrator review before next trio.**

- [ ] **Step 2: Second trio — abnormal return calculation.** Markdown why-block referencing Maymin 2026 methodology + spec divergences; code cell that computes AR / CAR per spec formulas; markdown interpretation-block. **HALT.**

- [ ] **Step 3: Third trio — primary statistical tests.** Markdown why-block referencing pre-registered tests in spec (t-test, sign-test, or other per spec); code cell that runs each test with spec-pinned thresholds; markdown interpretation-block reporting test-statistic + p-value vs. threshold. **HALT.**

- [ ] **Step 4: Fourth trio — primary result table.** Markdown why-block on table structure; code cell producing `output/PRIMARY_RESULTS.md` (machine-readable + human-readable); markdown interpretation-block summarizing what the table says. **HALT.**

- [ ] **Step 5: Orchestrator reads PRIMARY_RESULTS.md** and confirms the verdict-decision tree from the spec maps the observed (test-statistic, p-value) to PASS / FAIL / INDETERMINATE deterministically.

- [ ] **Step 6: Commit notebook 03 + PRIMARY_RESULTS.md.**

### Task 3.3: Notebook 04 — robustness

**Owner:** Analytics Reporter (trio-checkpoint discipline)

**Files:**
- Modify: notebooks/04_robustness.ipynb

> **Trio anatomy reminder (NON-NEGOTIABLE per `feedback_notebook_trio_checkpoint`):** Each trio in this task follows the same `(why-markdown → code-cell → interpretation-markdown)` anatomy as Task 3.2; HALT for orchestrator review after each trio. Do NOT collapse to code-only cells.

- [ ] **Step 1: First trio — alternative event windows** per spec (e.g., (-5, +5) vs. (-1, +3) vs. (-10, +30) days). Each window produces a row in the robustness table. HALT.

- [ ] **Step 2: Second trio — alternative controls** per spec (TAO alone, SN64 alone, ETH alone, joint regression). HALT.

- [ ] **Step 3: Third trio — sub-sample splits** per spec (Anthropic-only events, OpenAI-only events, pre-vs-post halving, pre-vs-post Taoflow regime change). HALT.

- [ ] **Step 4: Fourth trio — robustness summary table.** Output: `output/ROBUSTNESS_RESULTS.md`. HALT.

- [ ] **Step 5: Orchestrator confirms** any deviation from primary is documented as expected vs. unexpected per the spec's robustness expectations. Unexpected divergence requires spec-anticipated discussion in the memo (Phase 4), not threshold tuning.

- [ ] **Step 6: Commit notebook 04 + ROBUSTNESS_RESULTS.md.**

---

## Phase 4: Memo + verdict

Goal: synthesize results into a stakeholder memo with deterministic verdict, then run mandatory three-way review per `feedback_implementation_review_agents` (Code Reviewer + Reality Checker + Senior Developer), then commit.

### Task 4.1: Draft prototype-result memo

**Owner:** Analytics Reporter

**Files:**
- Create: `contracts/.scratch/p1-sn18-event-study/output/MEMO.md`
- Create: `contracts/.scratch/p1-sn18-event-study/output/gate_verdict.json`

- [ ] **Step 1: Specialist drafts memo** with sections: (1) Spec sha256 pin (quoted from Phase 0); (2) Hypothesis recap; (3) Event panel summary (count by provider × type); (4) Primary result + verdict per spec decision-tree; (5) Robustness summary; (6) Honest interpretation including basis-risk read against the broader slow-lane signal-research finding: did the narrower SN18 substrate produce a different verdict than the broad-basket failure, and if so, what mechanism is responsible? (7) Verdict statement (PASS / FAIL / INDETERMINATE) with one-paragraph defense; (8) Implications for slow-lane disposition (P2 escalation, P3 escalation, defer 6-12mo, pivot X, kill).

- [ ] **Step 2: Specialist writes machine-readable `gate_verdict.json`** with: spec_sha256, primary_test_statistic, primary_p_value, primary_threshold, verdict ∈ {PASS, FAIL, INDETERMINATE}, robustness_consistency ∈ {AGREE, DISAGREE, MIXED}, recommended_next_step.

### Task 4.2: Three-way implementation review

**Owner:** Foreground Orchestrator dispatches; Code Reviewer + Reality Checker + Senior Developer execute in parallel

**Files:**
- Read: MEMO.md, gate_verdict.json, all upstream artifacts

- [ ] **Step 1: Dispatch Code Reviewer** on the notebook code (notebooks 01-04). Charge: verify implementation matches spec methodology; check for silent-test-pass patterns (`feedback_three_way_review` lessons); verify no threshold tuning post-data; confirm citation blocks present per `feedback_notebook_citation_block`.

- [ ] **Step 2: Dispatch Reality Checker** on the memo + verdict JSON. Charge: verify every claim in the memo is supported by a result-table cell; flag any narrative softening of a FAIL verdict; verify the next-step recommendation maps cleanly from the verdict per the spec decision-tree.

- [ ] **Step 3: Dispatch Senior Developer** on notebook + memo together. Charge: production-readiness check — could this analysis be re-run by a fresh engineer with only the spec + this notebook + the data? If not, what's missing?

- [ ] **Step 4: Integrate findings.** Per `feedback_pathological_halt_anti_fishing_checkpoint`, any reviewer flag of threshold-tuning or event-set re-curation triggers HALT-disposition memo before any revision lands.

### Task 4.3: Final memo commit + CLAUDE.md update

**Owner:** Foreground Orchestrator

**Files:**
- Modify: MEMO.md, gate_verdict.json (post-review revisions)
- Modify: `.worktree/ranFromAngstrom/CLAUDE.md` Active iteration block

- [ ] **Step 1: Apply review revisions** that do not tune thresholds, change the verdict, or re-curate the event set. Any such revision triggers HALT-disposition per Task 4.2 Step 4 — there is no path to apply it inline.

- [ ] **Step 2: Commit final memo** with `Doc-Verify:` trailer per the user-intended v2 rule (spirit-over-letter discipline; v2 itself paused but its intent governs all in-scope doc writes within this plan; trailer carries Code Reviewer / Reality Checker / Senior Developer agent IDs).

- [ ] **Step 3: Update CLAUDE.md Active iteration block** with verdict + slow-lane disposition pointer. This CLAUDE.md edit ITSELF triggers the 2-wave rule (spirit-over-letter discipline; RC + Workflow Architect per v2 default for governance writes); dispatch them on the diff before commit.

- [ ] **Step 4: Save a memory entry** at `~/.claude/.../memory/project_p1_sn18_event_study_complete.md` summarizing verdict + key findings + path forward. Memory writes are out of scope for the 2-wave rule.

---

## Phase 5: Disposition

Goal: surface verdict to user; user decides slow-lane next step.

### Task 5.1: User decision on slow-lane next step

**Owner:** Foreground Orchestrator

- [ ] **Step 1: Surface MEMO.md verdict + gate_verdict.json to user** with concise decision-frame: PASS → escalate to P2 (SUR triangulation) or P3 (SN18-vs-SN64 cointegrated pair-trade); FAIL → defer slow lane 6-12 months and concentrate on fast lane; INDETERMINATE → identify what additional data/methodology would resolve.

- [ ] **Step 2: User chooses next step.**

- [ ] **Step 3: If escalation chosen, invoke writing-plans for P2 or P3.** If defer/kill, update CLAUDE.md Active iteration block accordingly.

- [ ] **Step 4: Persist user decision to `contracts/.scratch/p1-sn18-event-study/output/DISPOSITION.md`** with timestamp + chosen-next-step + verbatim user-rationale paragraph. Commit with `Doc-Verify:` trailer (spirit-over-letter discipline). This file is the auditable handoff into P2 / P3 / defer / kill — mirrors the Phase-A.0 `EXIT_NON_REMITTANCE` paper-trail pattern and closes the orchestrator's acceptance criterion for Phase 5 (without it, Phase 5 has no verifiable deliverable).

---

## Self-review checklist (run by orchestrator before commit of THIS plan)

- **Spec coverage:** does every section of the P1 design source (`contracts/.scratch/2026-04-27-bittensor-claude-bridges-prototype-modeling.md` §6 P1 design) map to a task here? In particular: SN18-specific scope, Maymin 2026 methodology baseline, 2-3 week timeline, falsifiable hypothesis. **Verified — Phase 0 produces the spec, Phase 3 executes the methodology, Phase 4 produces the falsifiable verdict.**

- **Placeholder scan:** zero "TBD" / "TODO" / "fill in details" / "similar to Task N" / "implement appropriate handling". **Verified — all steps name a deliverable or a specialist dispatch with explicit charge.**

- **Code-agnosticism:** zero executable code blocks per `feedback_no_code_in_specs_or_plans`. **Verified — all steps describe behavior or specialist deliverables; tech-stack notes are advisory not prescriptive.**

- **Specialist coverage:** every task names an owner specialist per `feedback_specialized_agents_per_task`. **Verified — Trend Researcher (event sets), Data Engineer (data pulls), Analytics Reporter (notebooks + memo), Reality Checker / Code Reviewer / Senior Developer / Model QA Specialist / Workflow Architect (reviews).**

- **Anti-fishing discipline:** spec sha256 pin, threshold-pre-registration, HALT-disposition path, 3-way memo review regardless of verdict. **Verified — Phase 0 + Task 4.2 + Task 4.3 cover all four.**

- **2-wave doc verification:** spec write triggers RC + Model QA Specialist (Task 0.2); plan write (this file) triggers RC + Senior Project Manager (orchestrator dispatches before commit); memo write triggers RC + Analytics Reporter or specialist matched to the result content; CLAUDE.md update triggers RC + Workflow Architect. **Verified — all four document-write events have an explicit 2-wave dispatch step.**

- **Type / name consistency:** prose uses `α_n` (Greek alpha with subnet index); file paths use `alpha_n` (ASCII per filesystem convention); spec → notebooks → memo path consistent; `gate_verdict.json` schema fields (`spec_sha256`, `primary_test_statistic`, `primary_p_value`, `primary_threshold`, `verdict`, `robustness_consistency`, `recommended_next_step`) named consistently across Phase 4 references. **Verified — convention codified.**

---

## Execution handoff

Plan complete and ready for commit (pending 2-wave verification per the user-intended v2 rule).

**Two execution options:**

1. **Subagent-Driven (recommended)** — orchestrator dispatches a fresh specialist per task per the named owners, reviews between tasks, fast iteration, mandatory trio-checkpoint HALTs in Phase 3.

2. **Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Higher context burn; harder to enforce specialist discipline.

**Recommended: Subagent-Driven**, given the trio-checkpoint discipline mandated by `feedback_notebook_trio_checkpoint` and the multi-specialist design of the plan.
