# Rev-5.3.3 Re-Review — Reality Checker (Adversarial)

**Date:** 2026-04-26 (post-fix-up rewrite by TW agent `afee8ee7a426a0d4a`)
**Scope:** Rev-5.3.3 CORRECTIONS block (lines 2114-2366) of
`/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
(uncommitted as of this review).
**Default verdict:** NEEDS-WORK. Promotion requires overwhelming evidence the revision is internally consistent + factually accurate.

---

## Verdict: **PASS-with-advisories**

Three of seven items pass cleanly; three pass with one minor advisory each; one item carries a substantive internal-inconsistency advisory (item 3) that I judge to be a single-character-class typo, NOT a rewrite trigger. None of the findings rise to the BLOCK threshold (no fabricated facts, no anti-fishing breach, no broken pre-commit, no dangling reference to a non-existent prior artifact). The CORRECTIONS block is internally consistent on the load-bearing claims (anti-fishing invariants byte-exact preserved; address provenance correctly attributed; memory anchors all exist; TR research file exists; BLOCKING relation explicit; sub-plan paths collision-free).

The single substantive advisory is an arithmetic-vs-prose mismatch in §C/§F (the prose preamble at line 2168 says "five super-tasks below" but six super-task `#### Task` headers actually follow, and §F line 2324 correctly enumerates **+6** new task IDs). This is a vestige of the original Rev-5.3.3 author having drafted §C with five super-tasks before the post-author TR-Finding-3 insertion of Task 11.P.MR-β.1 — the §C preamble was not updated to "six". Recommend fix in a single-line sed-splice rather than a full rewrite.

---

## Item-by-item evidence

### Item 1: Address resolution — `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` → cCOP (Mento-native)

**Verdict: PASS** (with one advisory on schema-vs-script attribution).

Evidence:

1. **TR research file** at `contracts/.scratch/2026-04-25-mento-userbase-research.md` line 18 cites the Celo forum H1 2025 report attributing the address to Mento-native cCOP and reports cCOP H1 2025 stats: 82,500 lifetime transactions, 11,058 holders, 270M units circulating, 4 native merchants + BucksPay payment-rail wrap. TR also flags this is `HIGH` confidence with explicit *Recommend verifying address vs. ticker before locking the next X_d hypothesis*.
2. **Ingest source provenance** verified at `contracts/scripts/dune_onchain_flow_fetcher.py:128`:
   `COPM_TOKEN_ADDRESS: Final[str] = "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606"` — i.e., the Dune fetcher that lands rows into the `onchain_copm_transfers` DuckDB table is parameterized by exactly this address. So the Rev-5.3.3 claim that the table tracks transfers *at* this address is operationally true — the fetcher script's hardcoded constant is the source-of-truth, and the table is the result of that fetcher.
3. **DuckDB row count** verified: `SELECT COUNT(*) FROM onchain_copm_transfers` returns `110,253` rows. The TR-claimed 82.5K cCOP H1-2025 transaction count is consistent with 110K rows over a wider window (TR's window is bounded H1 2025 only; the DuckDB ingest covers a wider date range — see `evt_block_date` from 2024-10-10 forward).
4. **DuckDB schema check** (`DESCRIBE onchain_copm_transfers`): the table has columns `evt_block_date, evt_block_time, evt_tx_hash, from_address, to_address, value_wei, evt_block_number, log_index, _ingested_at`. Notably, **NO `contract_address` or `token_address` column.** The address is implicit in the ingest (one Dune query, parameterized by `COPM_TOKEN_ADDRESS`).

Advisory (non-blocking): Rev-5.3.3 Task 11.P.MR-β.1 deliverable (a) says the audit must "explicitly document at the schema level which contract address it tracks." Because the schema has no `contract_address` column, the audit cannot literally add that documentation at the column level — it must go in either a `COMMENT ON TABLE` statement (DuckDB supports table comments) or in the `econ_query_api.load_onchain_copm_transfers_full` docstring, OR the column needs to be added (which would be an additive schema migration). The Rev-5.3.3 block already says "Decision between rename vs. doc-only is left to the Data Engineer subagent and the spec-review trio per the sub-plan" so this is correctly deferred — but the sub-plan SHOULD make explicit which of {table-comment, docstring, additive `contract_address` column} is the schema-doc target. Not blocking; flagged as a sub-plan-authoring constraint.

### Item 2: Anti-fishing invariants byte-exact preserved

**Verdict: PASS.**

Verified at lines 2144-2148:

- `N_MIN = 75` ✓
- `POWER_MIN = 0.80` ✓
- `MDES_SD = 0.40` ✓
- `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` ✓ (full 64-hex sha256 byte-exact, matches `project_mdes_formulation_pin` memory anchor)
- Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` ✓ (full 64-hex byte-exact)
- All marked **PRESERVED** with explicit anti-fishing-banned framing on MDES_SD upward tuning.

Cross-reference: invariants table mirrors Rev-5.3.2 byte-exact + adds the new "Notebook discipline" row (NEWLY ADOPTED), the "Convex-payoff insufficiency caveat" row (REAFFIRMED LOAD-BEARING), and the "All-data-in-DuckDB invariant" row (REAFFIRMED). No silent threshold tuning. CORRECTIONS-block discipline preserved.

### Item 3: Task-count arithmetic in §F

**Verdict: PASS-with-advisory.**

§F line 2324 correctly enumerates `+6 new task IDs`:
1. Task 11.O.NB-α
2. Task 11.O.ζ-α
3. Task 11.P.MR-β (status COMPLETED)
4. Task 11.P.MR-β.1 (NEW under Rev-5.3.3)
5. Task 11.P.spec-β
6. Task 11.P.exec-β

§F line 2329 arithmetic: `Rev-5.3.3 active task count: 69 + 6 = 75; total headers: 71 + 6 = 77`. Verified directly:
- `grep -E "^#### Task " | sed -n '/CORRECTIONS — Rev-5.3.3/,$p'` returns exactly 6 super-task headers (lines 2170, 2190, 2217, 2233, 2253, 2273). ✓
- The user-supplied "5→6 / 74→75 / 76→77" tally implies the prior-Rev-2 baseline was 69+5=74 active and 71+5=76 total (i.e., the original Rev-5.3.3 had 5 super-tasks before 11.P.MR-β.1 was inserted). After the post-author insertion, the published numbers are 69+6=75 active and 71+6=77 total. **Arithmetic is correct.**

**Advisory (substantive but non-blocking):** §C preamble at line 2168 still reads *"The five super-tasks below are inserted into the major plan AFTER the Rev-5.3.2 task chain..."* — this is a vestige of the pre-insertion draft and is now inconsistent with the **six** super-task headers that follow. Similarly §E line 2318 reads *"Sub-plans (the five Rev-5.3.3 super-task sub-plans) MUST enumerate scaffolding additions..."* — also stale. §F line 2329 reads *"the per-sub-task decompositions inside each of the six Rev-5.3.3 super-tasks' sub-plans"* — correctly says "six". So the inconsistency is localized to two prose mentions ("five" at lines 2168 and 2318) that need to read "six". This is a single-character-class typo fix, not a rewrite trigger.

Recommend: TW fix-up agent issues a 2-line sed-splice changing "five super-tasks" → "six super-tasks" at line 2168 and "the five Rev-5.3.3 super-task sub-plans" → "the six Rev-5.3.3 super-task sub-plans" at line 2318. No other structural changes required.

### Item 4: Sub-plan path collisions

**Verdict: PASS.**

Verified `ls /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/`: directory contains only `plans/` and `specs/` — `sub-plans/` does NOT exist yet (it will be created when the first sub-plan is authored). All five forward-pointers therefore have zero collision risk:
- `2026-04-25-rev2-notebook-migration.md` ✓ (no existing file)
- `2026-04-25-rev3-zeta-group.md` ✓
- `2026-04-25-ccop-provenance-audit.md` ✓
- `2026-04-25-beta-spec.md` ✓
- `2026-04-25-beta-execution.md` ✓

The Rev-5.3.3 block says all five paths are "TO BE AUTHORED, post Rev-5.3.3 3-way review convergence" — consistent with absence of the directory.

### Item 5: TR research file existence

**Verdict: PASS.**

`ls contracts/.scratch/2026-04-25-mento-userbase-research.md` returns the file. File contains all four headline findings cited in §A line 2136 and §G line 2337. Specific verification:
- Finding 1 (MiniPay = swap rail; ≈0 macro-hedge signal) — present
- Finding 2 (Carbon DeFi MM ≈ 52% of cCOP Transfer events; UTC 13-17 NA-hours diurnal) — present at lines summarized in `2026-04-25-mento-userbase-research.md`
- Finding 3 (cCOP ≠ COPM; address `0xc92e8fc2…` resolves to Mento-native cCOP per Celo forum source) — present at file line 18 and line 178 (with table of address comparisons) and line 414 (recommendation to run audit)
- Finding 4 (three prompt-injection attempts in WebFetch / WebSearch correctly ignored) — present (audit-trail disclosure)

The Rev-5.3.3 §A and §G framings match the TR file content faithfully. No fabrication.

### Item 6: Memory anchors all exist

**Verdict: PASS.**

Verified `ls ~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/`:
- `project_abrigo_mento_native_only.md` ✓ exists
- `project_mento_canonical_naming_2026.md` ✓ exists
- `project_carbon_user_arb_partition_rule.md` ✓ exists

All three referenced anchors are present in the project memory store. Note that `project_abrigo_mento_native_only.md` appears in the user's auto-memory transcript at the top of this conversation, confirming it's been promoted to load-on-context. The corrigendum target (`project_mento_canonical_naming_2026`) carries the documented naming error per TR Finding 3 — Rev-5.3.3 §G line 2362 correctly flags it as the corrigendum target under Task 11.P.MR-β.1.

### Item 7: BLOCKING relation between Task 11.P.MR-β.1 and Task 11.P.spec-β

**Verdict: PASS.**

Verified at line 2249 (Task 11.P.MR-β.1 §Dependency):
> *"This task is BLOCKING for Task 11.P.spec-β (the β spec cannot author a Mento-native-only hypothesis grounded in `project_mento_canonical_naming_2026` until the corrigendum lands and the table-naming clarification ships)."*

And reciprocally at line 2271 (Task 11.P.spec-β §Dependency):
> *"Task 11.P.MR-β COMPLETED + Task 11.P.MR-β.1 (cCOP-vs-COPM provenance audit + memory corrigendum) COMPLETED. The β spec cannot author a Mento-native-only retail-only hypothesis grounded in correctly-named DuckDB tables until the provenance-audit-and-corrigendum task lands."*

Both directions are explicit and consistent. No ambiguity. The blocking relation is structural (β spec authoring grounded in corrected memory + corrected schema doc) and the rationale is recorded.

---

## Adversarial counter-checks (skeptical pass)

I deliberately probed for fantasy-approval triggers and found:

1. **No "luxury / production-ready" inflation.** Rev-5.3.3 explicitly preserves the FAIL verdict from Rev-5.3.2 (line 2150: "PRESERVED as published baseline"; line 2182: "the gate verdict displays as **FAIL** consistent with Rev-5.3.2 Phase 5b"). The block is *not* trying to rescue the FAIL via path α + β; it correctly characterizes ζ-group as "a separate stage of product validity" (line 2205) and β as a re-grounded hypothesis (line 2255). No analytical fantasy.
2. **No silent threshold tuning.** All five anti-fishing invariants marked PRESERVED byte-exact. The convex-payoff caveat (Rev-2 §11.A) is REAFFIRMED LOAD-BEARING, not weakened.
3. **No fabricated commits.** Spot-checked `c1eec8da5` (disposition memo), `799cbc280` (Phase 5b primary estimates) — both are referenced consistently across §A trigger and §G reference paths, with self-consistent attribution. Did not exhaustively `git show` each — that's a Code Reviewer responsibility, not Reality Checker.
4. **No phantom blockers.** The BLOCKING relation (item 7) is real and bidirectionally documented. The "Task 11.P.MR-β COMPLETED" status is verified by file existence (item 5).
5. **Address claim is CORRECTLY downgraded from "schema-level" to "ingest-script-level."** The plan claim that `onchain_copm_transfers` "tracks `0xc92e8fc2…`" is true at the fetcher-script level (verified by `dune_onchain_flow_fetcher.py:128`) but NOT at the schema-column level (no `contract_address` column). Rev-5.3.3 Task 11.P.MR-β.1 deliverable (a) explicitly addresses this gap by scoping the audit to "either rename the table to a Mento-native-aligned identifier (preferred) or add explicit schema-doc comments" — i.e., the corrigendum task is correctly scoped to close the schema-vs-script attribution gap. This is the kind of provenance-tightening the rev should do.

The only thing I would have wanted Rev-5.3.3 to flag more explicitly: TR's H1-2025 cCOP transaction count (82,500) vs. DuckDB row count (110,253) — these are NOT in conflict (different windows: TR cites a 6-month bounded window; DuckDB covers a wider range from 2024-10-10 onward). But the rev block does not draw the comparison either way, so there's no inflation claim to refute. Pre-flagged in this review for sub-plan-authoring discipline.

---

## What would push this to BLOCK

None of these triggered:
- A fabricated commit hash
- A fabricated TR finding (TR file independently corroborates all four findings cited in §A)
- A pre-commit silently relaxed (all five preserved byte-exact)
- A dangling forward-pointer (sub-plans don't exist yet, but they're not supposed to per the explicit "TO BE AUTHORED" framing)
- A memory anchor missing from disk
- A BLOCKING relation stated in only one direction (item 7 is bidirectional)
- A retroactive modification to Rev-5.3.2 published estimates (line 2134 explicitly preserves them; line 2164 reaffirms no data changes)

---

## Recommended fix-up scope (NOT a rewrite)

Single 2-line sed-splice the TW fix-up agent (or any next pass) issues:
- Line 2168: change "The five super-tasks below" → "The six super-tasks below"
- Line 2318: change "the five Rev-5.3.3 super-task sub-plans" → "the six Rev-5.3.3 super-task sub-plans"

After this fix-up the block is internally consistent on its own arithmetic. No other corrections required from a Reality Checker perspective.

---

## Final verdict: **PASS-with-advisories**

The Rev-5.3.3 CORRECTIONS block (post-fix-up rewrite by `afee8ee7a426a0d4a`) correctly reflects current project state: the TR Mento user-base research is delivered and faithfully summarized; the cCOP-vs-COPM naming error is correctly scoped under a NEW dedicated super-task with bidirectional BLOCKING relation to spec-β; all anti-fishing invariants are PRESERVED byte-exact; sub-plan paths are collision-free; memory anchors exist; the FAIL verdict from Rev-5.3.2 is preserved without rescue framing; the parallel-track rationale (α + β) is justified analytically. The single arithmetic-vs-prose typo at lines 2168 + 2318 ("five" should read "six") is a single-character-class fix and does NOT trigger a rewrite — recommend a 2-line sed-splice fix-up.

**Reviewer:** TestingRealityChecker (adversarial Reality Checker)
**Tool uses consumed:** ~13/15
**Output path:** `contracts/.scratch/2026-04-25-rev533-rereview-reality-checker.md`
