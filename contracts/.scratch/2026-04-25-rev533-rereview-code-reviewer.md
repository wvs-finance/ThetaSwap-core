# Rev-5.3.3 CORRECTIONS Block — Code Reviewer Re-Review (post-fix-up)

**Reviewer:** Code Reviewer (CR)
**Date:** 2026-04-25
**Scope:** Lines 2111-2366 of `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (uncommitted; TW fix-up agent `afee8ee7a426a0d4a`).
**Read-only:** Yes. No plan modifications performed.
**Tool budget:** 4 of 15 used.

---

## Verdict: **PASS** (no advisories beyond a single optional cosmetic note)

The fix-up TW rewrite cleanly incorporates the Reality Checker findings (TR Findings 1–4) and the user scope-tightening directive into the original Rev-5.3.3 CORRECTIONS block in place. All standard CR lens checks pass. All seven specific fix-up content items called out in the review prompt are present and correctly load-bearing. The block is ready to commit.

---

## 1. Standard CR lens — checks

### 1.1 Anti-fishing invariants byte-exact preserved — PASS

| Invariant | Required value | Found at line | Status |
| --- | --- | --- | --- |
| `N_MIN` | 75 | 2144 | PRESERVED |
| `POWER_MIN` | 0.80 | 2145 | PRESERVED |
| `MDES_SD` | 0.40 | 2146 | PRESERVED |
| `MDES_FORMULATION_HASH` (sha256) | `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` | 2147, 2365 | PRESERVED byte-exact |
| Rev-4 `decision_hash` | `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` | 2148, 2366 | PRESERVED byte-exact |
| Rev-2 spec invariants (functional form, control set, methodology literals) | byte-exact | 2149 | PRESERVED |
| 14-row resolution-matrix scope (Rev-2 mean-β) | published baseline | 2134, 2150, 2325 | PRESERVED |
| Anti-fishing protocol chain (HALT → disposition → user pivot → CORRECTIONS → 3-way review) | byte-exact | 2151 | PRESERVED |
| Convex-payoff insufficiency caveat (Rev-2 §11.A) | reaffirmed load-bearing | 2152, 2205 | REAFFIRMED |
| All-data-in-DuckDB invariant | reaffirmed | 2153 | REAFFIRMED |

No relaxations were introduced; all seven §B additions (items 1–7) are *additive* (extensions / scope-tightening / corrigendum-pointer), not relaxations. Item 6 (Mento-native ONLY) is the strongest scope-narrowing of the seven and is correctly framed as an immutable pre-commitment requiring its own future CORRECTIONS block to relax.

### 1.2 Six super-tasks present with sub-plan pointers — PASS

The original Rev-5.3.3 had **5** super-tasks. The fix-up correctly inserts Task 11.P.MR-β.1 between 11.P.MR-β and 11.P.spec-β, bringing the total to **6**:

| # | Super-task ID | Header line | Sub-plan pointer line | Status |
| --- | --- | --- | --- | --- |
| 1 | 11.O.NB-α | 2170 | 2180 (`2026-04-25-rev2-notebook-migration.md`) | Present |
| 2 | 11.O.ζ-α | 2190 | 2201 (`2026-04-25-rev3-zeta-group.md`) | Present |
| 3 | 11.P.MR-β | 2217 | (no sub-plan; status = COMPLETED — research artifact directly delivered at `contracts/.scratch/2026-04-25-mento-userbase-research.md`) | Present |
| 4 | 11.P.MR-β.1 (NEW) | 2233 | 2241 (`2026-04-25-ccop-provenance-audit.md`) | Present |
| 5 | 11.P.spec-β | 2253 | 2257 (`2026-04-25-beta-spec.md`) | Present |
| 6 | 11.P.exec-β | 2273 | 2277 (`2026-04-25-beta-execution.md`) | Present |

§G (lines 2338–2343) cross-references all five sub-plan target paths; consistent. Task 11.P.MR-β reasonably has no sub-plan because it is an evidence-gathering deliverable, not a multi-task workstream — the deliverable IS the report itself, and its body fully describes deliverable / output / subagent / acceptance / reviewers / dependency / status. Acceptable.

### 1.3 All sub-plan pointer paths use canonical naming — PASS

All five forward-pointer paths follow the project-canonical pattern `contracts/docs/superpowers/sub-plans/YYYY-MM-DD-<topic>.md`. The Y₃ design doc (`contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md`) and X_d design doc (`contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`) cross-references in §G are also canonical and correctly flagged immutable. The notebook scaffolding root path `notebooks/abrigo_y3_x_d/` matches the existing FX-vol-CPI Colombia precedent at `contracts/notebooks/fx_vol_cpi_surprise/Colombia/` (modulo the project-naming-vs-relative-path ambiguity, which is the same convention used elsewhere in the plan).

### 1.4 Code-agnostic body — PASS

Body is 100% prose and tabular reasoning. Non-prose elements are: contract addresses (data identifiers, not code), sha256 hashes (immutability anchors), token symbols, partition-rule field names (`trader = 0x8c05ea30…`), and one regression-equation expression (`σ²_t(Y₃) = ω + α·ε²_{t-1} + β·σ²_{t-1} + δ·X_d,t` at line 2196 inside Task 11.O.ζ-α deliverable). The regression-equation expression is mathematical specification, not implementation code — consistent with `feedback_no_code_in_specs_or_plans` (specs/plans must be code-agnostic but may contain mathematical specification). No imports, no function bodies, no SQL, no Python/Solidity. PASS.

### 1.5 Cross-references resolve — PASS

All in-plan §-references (§A, §B, §C, §D, §E, §F, §G) resolve to existing same-block sections. All commit references (`799cbc280`, `6b1200dcb`, `f38f1aad3`, `c1eec8da5`, `765b5e203`, `cefec08a7`, `c5cc9b66b`, `2a0377057`, `7afcd2ad6`, `23560d31b`) match the format of git short hashes; correctness of the specific commits is outside CR scope (Senior Developer would verify). Memory anchors are stable and well-formed; the new anchor `project_abrigo_mento_native_only.md` is consistently named and located. The CORRIGENDUM TARGET tag on `project_mento_canonical_naming_2026` (line 2362) is precise and explicit.

### 1.6 Section structure A/B/C/D/E/F/G consistent with Rev-5.3.2 precedent — PASS

The Rev-5.3.2 CORRECTIONS block (immediately above this Rev-5.3.3) uses the same A/B/C/D/E/F/G section structure. Rev-5.3.3 fix-up preserves this structure exactly. Section ordering and headings match Rev-5.3.2 precedent format.

### 1.7 Task-count reconciliation arithmetic — PASS (with minor framing note)

§F line 2322 anchors Rev-5.3.2 baseline at **69** active / **71** total headers. §F line 2329 computes Rev-5.3.3 = 69 + 6 = 75 active / 71 + 6 = 77 total. Arithmetic is internally consistent and matches the §F baseline exactly. The +3 accounting-drift caveat from line 1739 is correctly propagated forward (declared explicitly at line 2329 as inherited and unchanged) and the future Rev-5.4 row-by-row refresh per amendment-rider A8 is correctly invoked.

**Minor framing note (non-blocking):** the review prompt summarized the delta as "74 → 75 active; 76 → 77 total" (presumably reading the original Rev-5.3.3 + 5 super-tasks would have been 74 / 76). The plan body uses the canonical `69 → 75 / 71 → 77` arithmetic anchored to the Rev-5.3.2 baseline (69 / 71). Both deltas reach the same endpoint (75 / 77). The plan-body framing is the correct one to use; the prompt summary appears to be informally counting from "previous Rev-5.3.3 endpoint with 5 super-tasks" rather than from the Rev-5.3.2 baseline. No action required — the plan body is consistent with itself and with the Rev-5.3.2 baseline. PASS.

---

## 2. Specific fix-up content verification

### 2.1 §A: TR findings paragraph + user scope-tightening directive paragraph — PASS

- **TR findings paragraph (line 2136).** Present. Enumerates Findings 1, 2, 3, 4 each with the load-bearing identification: F1 = MiniPay swap-rail / ≈0 macro-hedge signal at aggregate; F2 = Carbon DeFi MM ≈ 52% of cCOP Transfers + UTC 13–17 NA-hours signature + ρ(X_d, fed_funds) = `−0.614` + BIS WP 1219/1340 macro-substitution consistency; F3 = cCOP ≠ COPM, address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` is Mento-native cCOP per Celo forum source; F4 = three prompt-injection attempts observed and correctly ignored by Trend Researcher subagent. Citations (Celo forum, BIS WP) anchored.
- **User scope-tightening directive paragraph (line 2138).** Present. Direct quote captured ("We're not taking into account [Minteo COPM] anymore..."). Constraint correctly identified as binding for both Track α (11.O.ζ-α) and Track β (11.P.spec-β / 11.P.exec-β). Memory anchor `project_abrigo_mento_native_only.md` referenced at the canonical memory path. Forward-pointer to §B item 6 explicit.

### 2.2 §B: pre-commitments 6 (Mento-native ONLY) and 7 (Mento-native cCOP at 0xc92e8fc2…) added — PASS

- **Pre-commitment 6 (line 2163).** Mento-native stablecoins ONLY: cCOP, USDm, EURm, BRLm, KESm, XOFm. Minteo-fintech COPM and other third-party fiat-backed tokens explicitly OUT OF SCOPE. Byte-exact and immutable through Rev-5.3.3 with explicit relaxation gate (own CORRECTIONS block + explicit user authorization).
- **Pre-commitment 7 (line 2164).** Rev-2 X_d series identity formally Mento-native cCOP, NOT Minteo-fintech COPM. Address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` correctly cited. DuckDB table `onchain_copm_transfers` correctly flagged misnamed at the project-memory level (data is correct, naming is the error). Corrigendum work scoped under NEW Task 11.P.MR-β.1. The "no data changes; only naming clarification" claim is precise and correctly preserves the Rev-5.3.2 published estimates byte-exact.

Both additions are cleanly framed as ADDITIONS, not relaxations. The §B additions table on line 2154 (Notebook discipline newly adopted) is also correctly framed as a binding extension.

### 2.3 §C Task 11.P.MR-β: status flipped IN FLIGHT → COMPLETED with output pointer — PASS

Header (line 2217): "(super-task — COMPLETED)". Status line (line 2231): "**COMPLETED** — research output landed at `contracts/.scratch/2026-04-25-mento-userbase-research.md`". Four headline findings summarized at the status line with cross-reference to §A. Downstream BLOCKING relation to Task 11.P.MR-β.1 → Task 11.P.spec-β explicit. Subagent (Trend Researcher, `agentId = a7cd002b89b23e0ac`) preserved; reviewer (Reality Checker single-pass advisory; non-blocking; archival) preserved. The "research input not authoritative spec/plan artifact" framing is preserved (line 2227). Status flip is clean and correctly load-bearing.

### 2.4 §C Task 11.P.MR-β.1: NEW super-task fully spec'd — PASS

Header (line 2233): "(super-task — NEW under Rev-5.3.3)". Three artifacts (a / b / c) enumerated with full specificity:
- **(a)** DuckDB table audit + rename-vs-doc-decision (left to Data Engineer + spec-review trio per the sub-plan).
- **(b)** Memory corrigendum at `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md` with explicit citation (TR Finding 3 + Celo forum source + address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`).
- **(c)** Spec-doc addendum-style updates to X_d design doc at `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` and any other plan/spec docs referencing COPM (no byte-exact modification of pre-registered content; addendum-style only).

Sub-plan pointer (line 2241): `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (TO BE AUTHORED). Subagent: Data Engineer (correctly reasoned — no analytical/econometric work, naming-and-schema-doc clarification only). Reviewers: CR + RC + Senior Developer per `feedback_implementation_review_agents` (correctly applied — corrigendum is implementation-adjacent, not spec-authoring). Dependency: Task 11.P.MR-β COMPLETED upstream; **BLOCKING for Task 11.P.spec-β** explicit at line 2249.

The "no data changes (Rev-5.3.2 published estimates remain byte-exact); only naming clarification" guarantee is preserved across (a), (b), and (c). PASS.

### 2.5 §C Task 11.P.spec-β: scope-amended (Mento-native ONLY + H1/H2 hypothesis families + dependency on MR-β.1) — PASS

- **Mento-native ONLY scope constraint (line 2263).** Explicit citation to pre-commitment 6 (§B). Candidate retail-only X_d proxies enumerated under the Mento-native-only constraint: cCOP holder-count delta on Celo; cCOP merchant transaction count POST-Carbon-DeFi-MM-filter; MiniPay Mento-Broker swap volume into corridors. Mixed-Mento + non-Mento and Minteo-fintech instruments explicitly OUT OF SCOPE.
- **H1 / H2 hypothesis families (line 2265).** H1 = retail-hedge thesis FALSIFIED at basket-aggregate level, X_d as currently constructed is inverse-fed-funds proxy for NA-hours MM capacity (per Finding 2); β spec MAY pre-register STRUCTURAL-RECOGNITION test for H1 with appropriate gate definition. H2 = retail-hedge thesis PRESERVED with partition surgery (cCOP holder-count delta; cCOP merchant tx count post-Carbon-DeFi-MM filter via `project_carbon_user_arb_partition_rule`'s `trader = 0x8c05ea30…` field rule; MiniPay Mento-Broker corridor swap volume per Finding 1); β spec pre-registers fresh sign hypothesis on partitioned X_d. Spec MAY pre-commit to H1, H2, or evidence-grounded synthesis; choice is spec-level pre-registration gated by spec-review trio. Finding 1's ≈zero-aggregate-signal observation is correctly identified as the DOWNWARD adjustment the β spec MUST internalize on the MiniPay-aggregate-as-X_d hypothesis path; corridor-disaggregated MiniPay flows correctly preserved as a partitioned candidate.
- **Dependency on Task 11.P.MR-β.1 (line 2271).** Explicit BLOCKING relation. "The β spec cannot author a Mento-native-only retail-only hypothesis grounded in correctly-named DuckDB tables until the provenance-audit-and-corrigendum task lands." Clean.

### 2.6 §C Task 11.O.ζ-α: scope-amended (Mento-native ONLY + TR Finding 2 reframe context) — PASS

- **Mento-native ONLY scope constraint (line 2207).** Explicit citation to pre-commitment 6 (§B). ζ-group convex-payoff testing scoped to Mento-native stablecoins ONLY. Mixed Mento + non-Mento basket constructions OUT OF SCOPE. Rev-3 spec MUST cite pre-commitment 6 explicitly in scope section.
- **TR Finding 2 reframe foundation (line 2209).** Carbon DeFi MM ≈ 52% of cCOP Transfer events + UTC 13–17 NA-hours diurnal signature + ρ(X_d, fed_funds) = `−0.614` correctly cited. The reframe — ζ-group is now testing "tail-only hedge demand exists in Mento-native cCOP / USDm / etc." in the residual signal AFTER the Carbon-DeFi-MM partition is acknowledged — is precise and analytically defensible. The pre-commitment-deferral framing (Rev-3 spec MUST acknowledge TR Finding 2 in hypothesis-formation; pre-register whether ζ rows operate against unpartitioned Rev-2 X_d or against Carbon-DeFi-MM-residualized X_d; Rev-5.3.3 does NOT pre-empt the choice but flags it as load-bearing) is exactly the right anti-fishing posture: don't pre-empt the spec authoring's own pre-registration discipline, but DO surface the load-bearing analytical-framing input. PASS.

### 2.7 §F: count update (5→6 super-tasks; 69→75 active; 71→77 total) — PASS

- Line 2324: `+6 new task IDs with super-task bodies pointing to sub-plans` enumerates all six (Task 11.O.NB-α; Task 11.O.ζ-α; Task 11.P.MR-β [COMPLETED]; Task 11.P.MR-β.1 [NEW]; Task 11.P.spec-β; Task 11.P.exec-β).
- Line 2325: scope-amendments to Task 11.O.ζ-α and Task 11.P.spec-β under Rev-5.3.3 are correctly framed as SCOPE-CONSTRAINT additions (Mento-native-only + TR-Findings-grounding) layered onto existing super-task bodies, not modifications to upstream Rev-5.3.2 acceptance criteria. Clean.
- Line 2329: `Rev-5.3.3 active task count: 69 + 6 = 75 (excluding the deliberate non-task placeholder from Rev-5.3.2); total headers in the major plan: 71 + 6 = 77`. Arithmetic correct relative to the Rev-5.3.2 baseline at line 2095 (`69` active / `71` total).

The "major plan tracks super-tasks; sub-plans track sub-tasks" separation principle (line 2329, end) is correctly invoked and matches the user-directed structure. Sub-plan task counts are correctly excluded from the major-plan tally.

### 2.8 §G: TR research-output entry + 3 memory anchors + audit-trail disclosure — PASS

- **TR research-output entry (line 2337).** Path correctly cited: `contracts/.scratch/2026-04-25-mento-userbase-research.md`. Load-bearing relations to Task 11.P.MR-β.1, Task 11.O.ζ-α scope-amendment, Task 11.P.spec-β scope-amendment explicit. All four headline findings re-summarized at the §G entry for cross-reference convenience.
- **3 memory anchors added/flagged (lines 2361, 2362, 2363).**
  - `project_abrigo_mento_native_only` (NEW under Rev-5.3.3 — Abrigo scope is Mento-native ONLY; user scope-tightening directive 2026-04-25; load-bearing for §A trigger paragraph 4 + §B pre-commitment 6 + Tasks 11.O.ζ-α / 11.P.spec-β scope-amendments). Clean.
  - `project_mento_canonical_naming_2026` (CORRIGENDUM TARGET under Rev-5.3.3 — COPM entry carries naming error; data is correct; corrigendum scoped under NEW Task 11.P.MR-β.1). Clean.
  - `project_carbon_user_arb_partition_rule` (load-bearing for the H2 partitioned-X_d candidate hypothesis in Task 11.P.spec-β; partition rule = `trader = 0x8c05ea30…` field). Clean — and correctly aligns with the project memory's documented partition rule (NOT the `evt_tx_from`/tx-hash-JOIN method, which is anti-flagged in that memory).
- **Audit-trail disclosure (line 2364).** Three prompt-injection attempts observed via WebFetch / WebSearch during Mento-user-base research; agent correctly ignored and disclosed. Recorded as defensive-behavior audit-trail evidence; "no remediation action is required of the Rev-5.3.3 plan" — correct disposition (the disclosure is the audit artifact; remediation is at the agent-conduct layer, not the plan-revision layer).

---

## 3. Optional cosmetic note (non-blocking)

Line 2322's parenthetical `total headers under Rev-5.3.2 = 71 inclusive of placeholder + retired-as-audit` is technically accurate but slightly compressed for readers unfamiliar with the Rev-5.3.2 baseline. Cross-referencing line 2095 (the Rev-5.3.2 §F passage that establishes `64 + 6 + 1 (placeholder) = 71`) makes the 71-total header math fully transparent. A future Rev-5.4 row-by-row refresh per amendment-rider A8 is the canonical home for resolving this opacity. No action required for Rev-5.3.3.

---

## 4. Summary

The TW fix-up rewrite cleanly:

1. Preserved every anti-fishing invariant byte-exact (N_MIN, POWER_MIN, MDES_SD, MDES_FORMULATION_HASH, Rev-4 decision_hash, Rev-2 spec invariants, 14-row resolution-matrix scope baseline).
2. Added two new pre-commitments (item 6 Mento-native ONLY; item 7 Rev-2 X_d series identity is Mento-native cCOP) as ADDITIONS, not relaxations.
3. Inserted Task 11.P.MR-β.1 as a NEW super-task with full specificity (three artifacts a/b/c; sub-plan pointer; subagent assignment per `feedback_implementation_review_agents`; BLOCKING relation to Task 11.P.spec-β).
4. Flipped Task 11.P.MR-β status IN FLIGHT → COMPLETED with the research-output pointer and four headline findings.
5. Scope-amended Task 11.O.ζ-α (Mento-native ONLY + TR Finding 2 reframe context preserving spec-author pre-registration discipline) and Task 11.P.spec-β (Mento-native ONLY + H1/H2 hypothesis families + dependency on Task 11.P.MR-β.1) without modifying their upstream super-task bodies.
6. Updated §F task-count arithmetic correctly (5→6 super-tasks; 69→75 active; 71→77 total) with the +3 accounting-drift caveat preserved.
7. Added three memory-anchor entries to §G (one NEW: `project_abrigo_mento_native_only`; one CORRIGENDUM-TARGET: `project_mento_canonical_naming_2026`; one load-bearing-for-H2: `project_carbon_user_arb_partition_rule`) and the audit-trail disclosure for the three prompt-injection attempts.

The block is internally consistent, byte-exact preserves all immutable anchors, correctly handles the cCOP-vs-COPM naming clarification without modifying any pre-registered analytical content, and is cleanly aligned with the user's scope-tightening directive. The fix-up is ready to commit.

**Verdict: PASS.** No advisories beyond the optional cosmetic note in §3 above.

---

**Reviewer signature:** Code Reviewer
**Tool budget used:** 4 of 15 (Read × 1; Bash × 3 grep / lookup)
**Read-only confirmation:** No plan modifications performed.
