# Tier 1 Literature Feasibility — {π, C_remittance} Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the Rev 3 Tier 1 feasibility spec. Produce one markdown deliverable with per-channel literature verdicts for $\mu \in \{\pi, C_{\text{remittance}}\}$ and a global roll-up. No code, no regression, no on-chain queries — desk research only.

**Architecture:** Two-channel × five-source matrix. For each of $\{\pi, C_{\text{remittance}}\}$, run query patterns across NBER+SSRN → BanRep → IMF → Google Scholar → arxiv MCP, capturing each citation with proxy tier (A/B/C/D) and per-column handoff metadata. Apply §9 decision tree per channel; combine into global roll-up.

**Tech Stack:** Web search via WebFetch / WebSearch / arxiv MCP; markdown for the deliverable; git for commits. No Python, no SQL, no Solidity.

**Spec reference:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` (Rev 3).

**Deliverable path:** `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md`

**Assumed searcher:** human (JMSBPP) or a dispatched research subagent. Second reader: JMSBPP (must be human per spec §14); searcher and second reader must be distinct.

**Memory-mandated constraints:**
- No code in plan or deliverable.
- Research output under `contracts/.scratch/` for transient artifacts; final deliverable under `contracts/notes/structural-econometrics/identification/`.
- Pipeline work touches only `scripts/`, `data/`, `.gitignore` if any — NOT `src/`, `test/*.sol`, `foundry.toml`, or any Solidity. (This plan touches `contracts/notes/` and `contracts/docs/` only — both out of the Solidity-forbidden set.)

---

## Task 1: Pre-flight — prerequisites and directory

**Files:**
- Read: `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
- Read: `contracts/notebooks/ranPricing.ipynb`
- Read: `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/` (optional context only)
- Create: `contracts/notes/structural-econometrics/identification/` (if missing)

- [ ] **Step 1.1 — Confirm the spec is Rev 3 (literature-only, no §10 infrastructure thresholds).**

Run: `head -20 contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
Expected: header says `**Status:** Rev 3 (scope-shrunk to literature-only after Rev 2 review)`.

- [ ] **Step 1.2 — Create the deliverable directory if missing.**

Run: `mkdir -p contracts/notes/structural-econometrics/identification`
Expected: directory exists, no error.

- [ ] **Step 1.3 — Confirm the 2026-04-02 context is optional, not a hard dependency.**

Run: `ls /home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/ 2>/dev/null | head -5`
Expected: either directory listing OR empty (both acceptable per spec §14; if empty, proceed without the context excerpts).

---

## Task 2: Create deliverable skeleton

**Files:**
- Create: `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md`

- [ ] **Step 2.1 — Write the deliverable skeleton with all required sections from spec §11.**

Template (drop verbatim; fill during subsequent tasks):

```markdown
# Tier 1 Literature Feasibility — {π, C_remittance} Deliverable

**Spec:** contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md (Rev 3)
**Searcher:** <NAME / AGENT-ID>
**Second reader:** JMSBPP
**Search start date:** <YYYY-MM-DD>
**Search end date:** <YYYY-MM-DD>

## 1. Hypotheses

**Channel π (inflation):** Realized weekly vol of log(P_cCOP/X) responds to DANE Colombian CPI surprise with adj-R² ≥ τ_lit = 0.10, in a regression with controls for US CPI surprise, BanRep policy-rate surprise, and VIX.

**Channel C_remittance:** Channel's natural observable (transfer-volume residual or flow-based LHS) responds to remittance-flow or income-cycle surprise at adj-R² ≥ τ_lit = 0.10.

τ_op = 0.15 (out-of-sample operational). τ_lit = 0.10 (in-sample literature).

## 2. Findings — Channel π

(Filled in Task 8. Per-citation rows with §10 handoff columns.)

| Citation | Sample start | Sample end | Country | Pair | Frequency | LHS | Surprise construction | Control set | Reported adj-R² | Tier (A/B/C/D) | Distance | Portability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 3. Cross-currency signal-strength — Channel π

(Per spec §8. Strength bucket: strong ≥ 0.25 / moderate 0.10–0.25 / weak < 0.10 / none.)

| Counterparty | adj-R² | Sig | Tier | Citations | Strength | Notes |
|---|---|---|---|---|---|---|
| USD | NOT STUDIED | — | — | — | none | |
| EUR | NOT STUDIED | — | — | — | none | |
| DXY basket | NOT STUDIED | — | — | — | none | |
| MXN | NOT STUDIED | — | — | — | none | |
| BRL | NOT STUDIED | — | — | — | none | |
| XAU | NOT STUDIED | — | — | — | none | |

## 4. Findings — Channel C_remittance

(Filled in Task 14.)

| Citation | Sample start | Sample end | Country | Pair | Frequency | LHS | Surprise construction | Control set | Reported adj-R² | Tier (A/B/C/D) | Distance | Portability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 5. Cross-currency signal-strength — Channel C_remittance

| Counterparty | adj-R² | Sig | Tier | Citations | Strength | Notes |
|---|---|---|---|---|---|---|
| USD | NOT STUDIED | — | — | — | none | |
| EUR | NOT STUDIED | — | — | — | none | |
| DXY basket | NOT STUDIED | — | — | — | none | |
| MXN | NOT STUDIED | — | — | — | none | |
| BRL | NOT STUDIED | — | — | — | none | |
| XAU | NOT STUDIED | — | — | — | none | |

## 6. Per-channel verdicts

**Channel π:** `<LABEL>` — `<payload per §9>` — <rationale> — <citation list>

**Channel C_remittance:** `<LABEL>` — `<payload>` — <rationale> — <citation list>

## 7. Global roll-up

`<GLOBAL LABEL>` — `<payload>` — <rationale>

## 8. Gap analysis

Unaddressed questions, close-enough-to-cite, missing.

## 9. Sources consulted

| Source | Channel | Queries tried | Hits | Blocked (why) |
|---|---|---|---|---|

## 10. Confidence level and unresolved leads

Searcher's qualitative confidence (low/medium/high) per channel, plus any leads unresolved at hard-cap time.

## 11. Second-reader sign-off

- [ ] Second reader spot-checked ≥ 3 citations' tier assignments.
- [ ] Second reader confirmed no `[CITATION-TODO]` markers remain.
- [ ] Second reader confirmed verdicts map correctly via spec §9 decision tree.

Signed: <NAME>  Date: <YYYY-MM-DD>
```

- [ ] **Step 2.2 — Commit the skeleton.**

Run:
```
git add contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md
git commit -m "docs(tier1): add literature-deliverable skeleton for {π, C_rem} channels"
```
Expected: commit succeeds.

---

## Task 3: Channel π — NBER + SSRN pass

**Files:**
- Modify: deliverable §2 (findings rows) and §9 (sources-consulted row).

- [ ] **Step 3.1 — Query NBER search with each pattern from spec §6.**

Queries to run against `nber.org/papers` search and `papers.ssrn.com` search:
- `"Colombia" (inflation OR CPI) (surprise OR announcement) (exchange rate OR FX) (volatility OR "realized vol")`
- `"pass-through" Colombia (variance OR volatility OR GARCH)`
- `"announcement effect" (Latin America OR "emerging market") (peso OR COP) volatility`

Use WebSearch or WebFetch. For each hit within the first 2 pages of results, capture: title, author(s), year, abstract URL.

- [ ] **Step 3.2 — For each hit, tier-classify per spec §7.**

Open the abstract + intro + methodology (full text if reachable). Assign Tier A/B/C/D using the §7 criteria. Tier B/C boundary requires full-text judgment — err toward the farther tier if ambiguous.

Apply the full-text-blocked downgrade (spec §10) for any paywalled paper where HITL retrieval isn't possible.

- [ ] **Step 3.3 — For each qualifying hit, add a row to deliverable §2.**

Row template (fill all columns; use `—` only when the paper itself does not report the column):

```
| <Author Year> | <sample-start-year> | <sample-end-year> | <country> | <pair> | <freq> | <LHS> | <surprise construction> | <control set> | <adj-R²> | <Tier> | <distance note> | <portability-to-cCOP caveat> |
```

- [ ] **Step 3.4 — Record the search in deliverable §9.**

Append row:
```
| NBER + SSRN | π | <patterns tried> | <N hits captured> | <N blocked / reason> |
```

- [ ] **Step 3.5 — Commit.**

```
git add contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md
git commit -m "docs(tier1): channel π NBER+SSRN pass — <N> citations, <N> rejected"
```

---

## Task 4: Channel π — BanRep Borradores de Economía pass (Spanish)

**Files:**
- Modify: deliverable §2, §9.

- [ ] **Step 4.1 — Query BanRep Borradores de Economía with Spanish and English patterns.**

Target URL: `https://www.banrep.gov.co/en/research-papers`

Queries:
- `(inflación OR IPC) (sorpresa OR anuncio) (tipo de cambio OR TRM) (volatilidad OR varianza)`
- `inflation surprise exchange rate volatility Colombia`
- Author-seeded searches: `Rincón-Castro`, `González-Gómez`, `Hamann-Salcedo`.

- [ ] **Step 4.2 — For each hit, read abstract (Spanish full text if needed); tier-classify per §7.**

- [ ] **Step 4.3 — Add qualifying rows to deliverable §2 (same row template as Task 3).**

- [ ] **Step 4.4 — Record in §9.**

Append: `| BanRep | π | <patterns> | <N> | <blocked> |`

- [ ] **Step 4.5 — Commit.**

```
git add contracts/notes/...
git commit -m "docs(tier1): channel π BanRep pass — <N> citations"
```

---

## Task 5: Channel π — IMF Working Papers pass

**Files:**
- Modify: deliverable §2, §9.

- [ ] **Step 5.1 — Query IMF WP database filtered to Colombia.**

Target URL: `https://www.imf.org/en/publications/wp` with Colombia filter.

Queries:
- `Colombia inflation exchange rate pass-through volatility`
- `Colombia monetary policy exchange rate announcement`
- `emerging market FX volatility inflation surprise`

- [ ] **Step 5.2 — Tier-classify each hit per §7.**

- [ ] **Step 5.3 — Add qualifying rows to deliverable §2.**

- [ ] **Step 5.4 — Record in §9.**

- [ ] **Step 5.5 — Commit.**

---

## Task 6: Channel π — Google Scholar + forward-citation walks

**Files:**
- Modify: deliverable §2, §9.

- [ ] **Step 6.1 — Query Google Scholar with residual patterns.**

Use the patterns not already executed. Additionally, for each Tier-A-or-B hit from Tasks 3–5, forward-walk citations (papers that cite it) via Scholar's "Cited by" link. Depth cap: 1 (citations of citations not pursued unless the hit is a Tier-A-boundary case).

- [ ] **Step 6.2 — Tier-classify new hits per §7.**

- [ ] **Step 6.3 — Add qualifying rows to deliverable §2.**

- [ ] **Step 6.4 — Record in §9.**

- [ ] **Step 6.5 — Commit.**

---

## Task 7: Channel π — arxiv MCP pass (no-penalty skip allowed)

**Files:**
- Modify: deliverable §9 only (arxiv hits uncommon for macro-econ).

- [ ] **Step 7.1 — Attempt arxiv search via `mcp__arxiv__search_papers` with the same query set.**

Expected: 0–2 hits. Macro-econ is rare on arxiv; this is a completeness check.

- [ ] **Step 7.2 — If any Tier-A/B hits appear, add to deliverable §2.**

- [ ] **Step 7.3 — Record in §9; if no hits, mark `| arxiv MCP | π | <patterns> | 0 | skipped (empty) |`.**

- [ ] **Step 7.4 — Commit.**

---

## Task 8: Channel π — tier-classify aggregate + fill cross-currency table + emit verdict

**Files:**
- Modify: deliverable §3 (signal-strength table), §6 (per-channel verdict).

- [ ] **Step 8.1 — Aggregate all Task-3-through-7 citations by counterparty currency.**

For each counterparty row in §3, pick the citation with the highest adj-R² and the closest tier (A > B > C > D). Fill: reported adj-R², significance, tier, citations, strength bucket, notes.

If zero citations for a counterparty: leave `NOT STUDIED` / `none`.

- [ ] **Step 8.2 — Apply spec §9 per-channel decision tree to emit verdict for channel π.**

Decision tree:
1. IF any Tier-A-or-B citation reports β ≈ 0 / adj-R² < 0.05 with tight CIs → `DISCONFIRMED` with payload `channel=pi null_tier=<A|B> citations=<N>`.
2. ELSE IF any Tier-A-or-B-or-C citation meets adj-R² ≥ 0.10 → `CONFIRMED` with payload `channel=pi target_counterparty=<token> tier=<A|B|C> citations=<N>`. Tie-break: highest adj-R² → lowest confound density → closest tier to A.
3. ELSE IF any Tier-A-or-B-or-C citation below threshold OR any Tier-D hit above threshold OR specification-distance flagged → `PARTIAL_SUPPORT` with payload `channel=pi which_dimension=<…>`.
4. ELSE → `NO_LITERATURE_SUPPORT` with payload `channel=pi citations_considered=<N>`.

- [ ] **Step 8.3 — Write the verdict to deliverable §6 with label, payload, rationale, citation list.**

- [ ] **Step 8.4 — Commit.**

```
git commit -m "docs(tier1): channel π verdict — <LABEL>"
```

---

## Task 9: Channel C_remittance — NBER + SSRN pass

**Files:**
- Modify: deliverable §4, §9.

- [ ] **Step 9.1 — Query NBER and SSRN with Channel C patterns from spec §6:**

- `remittance Colombia "exchange rate" (volatility OR variance OR shock)`
- `"income cycle" OR quincena Colombia "exchange rate"`
- `remittance "emerging market" "FX volatility"`

Author seeds: Orozco, Mora-Ruiz, Gomez-Oviedo, IDB Colombia team.

- [ ] **Step 9.2 — Tier-classify per §7 with channel-specific LHS interpretation.**

For Channel C_remittance, "natural observable" can be transfer volume residual, remittance flow series, or FX-vol conditional on remittance-surprise days. The LHS column distinguishes.

- [ ] **Step 9.3 — Add rows to deliverable §4.**

- [ ] **Step 9.4 — Record in §9.**

- [ ] **Step 9.5 — Commit.**

---

## Task 10: Channel C_remittance — BanRep pass

**Files:**
- Modify: deliverable §4, §9.

- [ ] **Step 10.1 — Query BanRep Borradores with:**

- `(remesas OR giros) Colombia (tipo de cambio OR volatilidad OR choque)`
- `ciclo de ingreso quincena (tipo de cambio OR TRM)`
- `remittance inflow volatility`

- [ ] **Step 10.2 — Tier-classify per §7.**

- [ ] **Step 10.3 — Add rows to §4.**

- [ ] **Step 10.4 — Record in §9.**

- [ ] **Step 10.5 — Commit.**

---

## Task 11: Channel C_remittance — IMF pass

**Files:**
- Modify: deliverable §4, §9.

- [ ] **Step 11.1 — Query IMF WPs filtered to Colombia:**

- `Colombia remittance volatility`
- `emerging market remittance flow shock FX`

- [ ] **Step 11.2 — Tier-classify per §7.**

- [ ] **Step 11.3 — Add rows.**

- [ ] **Step 11.4 — Record in §9.**

- [ ] **Step 11.5 — Commit.**

---

## Task 12: Channel C_remittance — Google Scholar + forward-citation

**Files:**
- Modify: deliverable §4, §9.

- [ ] **Step 12.1 — Google Scholar query residuals + forward-cite from any Tier-A/B Task-9-through-11 hits.**

- [ ] **Step 12.2 — Tier-classify per §7.**

- [ ] **Step 12.3 — Add rows.**

- [ ] **Step 12.4 — Record in §9.**

- [ ] **Step 12.5 — Commit.**

---

## Task 13: Channel C_remittance — arxiv MCP pass

**Files:**
- Modify: deliverable §9.

- [ ] **Step 13.1 — arxiv search (no-penalty skip if empty).**

- [ ] **Step 13.2 — Record in §9.**

- [ ] **Step 13.3 — Commit.**

---

## Task 14: Channel C_remittance — aggregate + table + verdict

**Files:**
- Modify: deliverable §5, §6.

- [ ] **Step 14.1 — Fill §5 signal-strength table from aggregated citations.**

For each counterparty row in deliverable §5, select from Tasks 9–13 the citation(s) with the highest reported adj-R² and closest tier (A > B > C > D) for this channel. Fill columns: reported adj-R², significance, tier, citation(s), strength bucket (`strong` ≥ 0.25 / `moderate` 0.10–0.25 / `weak` < 0.10 / `none` = no citations), notes.

For counterparties with zero qualifying citations, leave the row as `NOT STUDIED | — | — | — | none |`.

- [ ] **Step 14.2 — Apply spec §9 decision tree; emit verdict.**

- [ ] **Step 14.3 — Write verdict to §6 (second row) with label + payload + rationale + citation list.**

- [ ] **Step 14.4 — Commit.**

```
git commit -m "docs(tier1): channel C_rem verdict — <LABEL>"
```

---

## Task 15: Validate §10 handoff columns are complete for every cited paper

**Files:**
- Modify: deliverable §2 and §4 rows where columns are incomplete.

- [ ] **Step 15.1 — For every row in §2 and §4, confirm all 13 handoff columns from spec §10 are populated.**

Columns required: citation, sample start, sample end, country, pair, frequency, LHS, surprise construction, control set, reported adj-R², tier, distance, portability.

If a column is blank and the paper is accessible, read the paper and fill.

If a column is blank because the paper is paywalled and HITL failed, apply spec §10 full-text-blocked downgrade rule: downgrade the row's tier by one (A→B, B→C, C→D). Update the tier cell. If the downgrade takes a Tier-D row below threshold-supportability, mark the row `DOWNGRADED_BELOW_SUPPORT` in the Distance column.

- [ ] **Step 15.2 — Re-apply the §9 decision tree to both channels if any tier changed.**

If any tier downgrade causes a verdict change (e.g., previous CONFIRMED now has no Tier-A-B-C support), update the §6 verdict and note the change in rationale.

- [ ] **Step 15.3 — Commit.**

```
git commit -m "docs(tier1): apply §10 full-text-blocked downgrade rule"
```

---

## Task 16: Global roll-up

**Files:**
- Modify: deliverable §7.

- [ ] **Step 16.1 — Apply spec §9 global roll-up rules.**

Rules:
- `PROCEED` if at least one channel emits `CONFIRMED`. Payload: `survivor_channel=<π|C_rem> target_counterparty=<token> tier=<A|B|C>`.
- `PIVOT_TO_TIER_1B` if all channels emit `NO_LITERATURE_SUPPORT` or `PARTIAL_SUPPORT` only. Payload: `candidate_channel=<channel with strongest partial evidence> rationale=<…>`.
- `RETIRE_THESIS` if all channels emit `DISCONFIRMED`. Payload: `channels_disconfirmed=<list>`.
- `MIXED` for heterogeneous outcomes not fitting the three above. Payload: `per_channel=<list>`.

- [ ] **Step 16.2 — Write the global verdict to §7 with label + payload + rationale.**

- [ ] **Step 16.3 — Commit.**

```
git commit -m "docs(tier1): global roll-up — <LABEL>"
```

---

## Task 17: Gap analysis + confidence + unresolved leads

**Files:**
- Modify: deliverable §8, §10.

- [ ] **Step 17.1 — Write gap analysis in §8.**

Cover: unaddressed questions (e.g., vol-response for specific counterparty not studied), close-enough-to-cite (Tier-C/D hits that motivate Tier 1b without justifying CONFIRMED), missing (what would need to be run in-house to close each gap).

- [ ] **Step 17.2 — Write confidence level and unresolved leads in §10.**

Qualitative confidence per channel (low/medium/high) + any leads unresolved at time cap.

- [ ] **Step 17.3 — Commit.**

```
git commit -m "docs(tier1): gap analysis + confidence"
```

---

## Task 18: Resolve `[CITATION-TODO]` markers in spec References

**Files:**
- Modify: `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` §18 References.

- [ ] **Step 18.1 — For every `**[CITATION-TODO]**` marker in the spec §18, resolve to a full bibliographic entry OR remove the entry.**

If the author was cited inline but no paper was found to back the citation, remove the entry and note in the deliverable §8 gap analysis.

- [ ] **Step 18.2 — Verify zero `[CITATION-TODO]` markers remain.**

Run: `grep -c 'CITATION-TODO' contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
Expected: `0`.

- [ ] **Step 18.3 — Commit.**

```
git commit -m "docs(tier1): resolve all [CITATION-TODO] markers in spec §18"
```

---

## Task 19: Self-check against spec §16 success criterion

**Files:**
- Modify: deliverable (if any gap is found during check).

- [ ] **Step 19.1 — Verify spec §16(a): all four primary sources queried with ≥3 of 4 patterns per channel.**

Count rows in §9 table; confirm coverage. If a source was skipped under hard block, confirm timestamp + reason are captured and the relevant channel's verdict is downgraded one tier.

- [ ] **Step 19.2 — Verify §16(b): ≥3 citations per channel (≥6 total) OR explicit exhaustive-search failure OR DISCONFIRMED with ≥1 Tier-A/B citation.**

- [ ] **Step 19.3 — Verify §16(c): per-channel verdicts and global roll-up present; tier claims auditable against §7.**

- [ ] **Step 19.4 — Verify §16(e): zero `[CITATION-TODO]` in the spec References.**

Re-run: `grep -c 'CITATION-TODO' contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
Expected: `0`.

- [ ] **Step 19.5 — If any criterion fails, loop back to the relevant task and fix; else proceed to Task 20.**

- [ ] **Step 19.6 — Commit if any fix was made.**

---

## Task 20: Second-reader review gate (PAUSES EXECUTION)

**Files:**
- Modify: deliverable §11 sign-off section.

- [ ] **Step 20.1 — Notify JMSBPP that the deliverable is ready for second-reader review.**

The searcher MUST NOT be the second reader. If the searcher is JMSBPP, pause and identify another human reviewer (project co-owner or designated reviewer). An AI agent (this plan's executor or any sibling LLM) is not acceptable per spec §14.

- [ ] **Step 20.2 — Second reader spot-checks ≥ 3 citations' Tier A/B/C/D classifications against the papers' actual specifications.**

- [ ] **Step 20.3 — Second reader confirms the per-channel and global verdicts map correctly via spec §9 decision tree given the filled §3, §5, §6, §7 content.**

- [ ] **Step 20.4 — Second reader fills §11 with name + date.**

If the second reader finds any misclassification or verdict-mapping error, they MUST return the deliverable to the searcher for fix. Do not proceed to Task 21 until the sign-off is filled.

---

## Task 21: Final commit + push

**Files:**
- Committed files: deliverable + spec (if §18 updated).

- [ ] **Step 21.1 — Final commit with the second-reader sign-off.**

```
git add contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md
git commit -m "docs(tier1): finalize — <global-verdict> signed off by <second-reader>"
```

- [ ] **Step 21.2 — Push to `thetaswap/ran-v1a`.**

```
git push thetaswap phase0-vb-mvp:ran-v1a
```

Expected: push succeeds.

- [ ] **Step 21.3 — Route downstream per spec §12:**

- `PROCEED` → start Tier 2 brainstorm (separate session).
- `PIVOT_TO_TIER_1B` → start Tier 1b brainstorm for the strongest-partial channel.
- `RETIRE_THESIS` → notify product owner; no Tier 2, no Tier 1b.
- `MIXED` → surface per-channel verdicts; user decides routing.

---

## Time budget

Per spec §15 (Rev 3): hard cap 2 days / ~12–16 hours of effective work.

Decomposition:
- Task 1–2: 30 min.
- Tasks 3–7 (Channel π search × 5 sources): ~3–4 h.
- Task 8 (Channel π aggregate + verdict): 1 h.
- Tasks 9–13 (Channel C_rem search × 5 sources): ~3–4 h.
- Task 14 (Channel C_rem aggregate + verdict): 1 h.
- Task 15 (handoff validation + possible tier downgrades): 1–2 h.
- Task 16–17 (global + gap/confidence): 1 h.
- Task 18 (resolve citation-TODOs): 30 min–1 h.
- Task 19 (self-check): 30 min.
- Task 20 (second-reader review): blocking on human; 30 min–1 h wall time.
- Task 21 (commit + push + route): 15 min.

Total: 12–16 h effective. If trending above 2 days of wall time, escalate to a Rev 4 rescope per spec §13.

---

## Non-goals (memory-reinforced, repeated for executor)

- No Python, SQL, RPC, Dune queries, or any regression code.
- No modification to `contracts/src/`, `contracts/test/`, `contracts/foundry.toml`, or any Solidity artifact.
- No write access to `/home/jmsbpp/apps/liq-soldk-dev/`.
- No Tier 2 design work, $U_{\text{RAN}}$ filter choices, or Panoptic tokenization.
- No on-chain availability check, liquidity threshold application, or infra sibling-spec scoping.
- No meta-analysis or synthetic adj-R² pooling.
- No paraphrased-rerunning of cited specifications on our data.
- No scope expansion to $\mu(I), \mu(XN), \mu(S)$ during execution.
- No mid-execution re-scoping. If execution hits a structural problem, pause and escalate to a Rev 4 brainstorm.
