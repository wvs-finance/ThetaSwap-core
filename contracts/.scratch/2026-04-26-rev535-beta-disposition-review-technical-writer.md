# Rev-5.3.5 β-disposition Review — Technical Writer trio member

**Date:** 2026-04-26
**Reviewer:** Technical Writer (post-hoc 3-way trio per `feedback_pathological_halt_anti_fishing_checkpoint` + `feedback_three_way_review`)
**Scope:** Disposition memo + Rev-5.3.5 CORRECTIONS in major plan + §I CORRECTIONS in MR-β.1 sub-plan + CORRECTIONS in NB-α sub-plan + project memory β-corrigenda + MEMORY.md index.

---

## 1. Verdict

**PASS-with-non-blocking-advisories.**

The β-disposition artifact set is editorially coherent, audit-trail-complete, and consistent in its two-address / two-ticker naming convention. Anti-fishing invariants are explicitly cited by name and by hash; load-bearing claims (Dune query 7378788, both URL anchors, both DE/RC commits) are quoted at fact-check granularity; cross-references resolve. Two substantive non-blocking advisories are flagged below (TW-1 §G/§I-9 reconciliation; TW-3 falsifiability of the NB-α "interpretation cell reframe" criterion) plus four minor editorial advisories. None block convergence.

---

## 2. Findings against the 8 TW concerns

### TW-1 — Code-agnostic discipline — CONFIRMED

All five reviewed files preserve code-agnostic body discipline. The only embedded SQL fragment surviving across the corrigenda is the pre-existing pre-flight enumeration query at MR-β.1 sub-plan line 83 (`SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'onchain_%' ORDER BY 1`), which the original sub-plan §C explicitly permits as a one-line catalog enumeration. The Rev-5.3.5 CORRECTIONS blocks introduce no new Python or SQL bodies; the only code-shaped tokens added are: `proxy_kind` slug strings (`carbon_per_currency_copm_volume_usd`); table names (`onchain_copm_*`); contract addresses; commit hashes; URLs; and quantitative point estimates (β̂ = −2.7987e−8). All are reference identifiers, not implementation bodies. **No finding.**

### TW-2 — Falsifiable acceptance criteria — NEEDS-WORK (non-blocking, advisory)

Most new acceptance criteria are falsifiable (e.g., MR-β.1 §I sub-task 1 rescope: "enumeration of all six in-scope Mento-native tokens + the one out-of-scope Minteo entry; provenance citations preserved" is checkable; sub-task 2: "count of tagged = count of returned" is preserved as an explicit equality assertion).

**Advisory TW-2a: NB-α CORRECTIONS interpretation-reframe criterion is not deterministically auditable.** At NB-α sub-plan line 481, the criterion reads:

> "every `interpretation-markdown` cell whose framing currently states or implies 'Mento-native hedge thesis tested and failed' must be reframed to **'Minteo-fintech X_d was scope-mismatched; Rev-2 closes scope-mismatch (NOT Mento-hedge-fail).'**"

The phrase "states or implies" is the falsifiability gap. A reviewer auditing the migrated notebooks cannot deterministically check whether a given interpretation cell "implies" the old framing. Recommend tightening to a **string-match-grade** acceptance criterion, e.g.:

> "Every interpretation cell whose Rev-2 source contains any of the substrings {'Mento-native hedge', 'hedge thesis', 'tested-and-failed', 'tested and failed', 'Mento-hedge-fail'} must be rewritten to use one of the canonical reframe substrings {'Minteo-fintech scope-mismatch', 'scope-mismatch close-out', 'Rev-2 closes scope-mismatch'}. Reviewer verification: `grep` over migrated notebooks shows zero matches in the banned set and ≥1 match in the canonical set per affected cell."

This converts "states or implies" into a deterministic grep check. Non-blocking — the orchestrator can apply this tightening at NB-α dispatch time without requiring re-convergence on the corrigendum.

**Advisory TW-2b: MR-β.1 §I sub-task 3 registry-doc disambiguation criterion (line 350) is partially falsifiable.** The clause "drop the `_ccop_` fragment and re-slug as `onchain_copm_minteo_daily_flow` (NOT executed under this sub-plan; recorded for future rev)" is fine as a forward-pointer but does not specify acceptance for the **current** sub-task 3 deliverable. Recommend appending: "Acceptance for the present sub-plan: registry doc carries an explicit per-table entry naming `onchain_copm_ccop_daily_flow`, recording that the table tracks Minteo-COPM (out-of-scope), and recording the future-rev rename recommendation verbatim. Falsifiable via section-presence + name-match in the registry doc." Non-blocking.

### TW-3 — Naming consistency — CONFIRMED with one minor advisory

The two-address / two-ticker convention is applied consistently across all five files:

| File | `0x8A567e2a…` label | `0xc92e8fc2…` label |
|---|---|---|
| Disposition memo | "Mento V2 `StableTokenCOP`" / "Mento-native COPm" | "Minteo-fintech" / "COPM-Minteo" / "Minteo-COPM" |
| Major plan Rev-5.3.5 | "canonical Mento V2 `StableTokenCOP` (Mento-native COPm)" | "Minteo-fintech COPM-Minteo" |
| MR-β.1 §I CORRECTIONS | "canonical Mento-native COPm" / "Mento V2 StableTokenCOP" | "Minteo-fintech COPM-Minteo" |
| NB-α CORRECTIONS | "Mento-native COPm address" / "`0x8A567e2a…`" | "Minteo-fintech `0xc92e8fc2…`" |
| `project_mento_canonical_naming_2026` β-corrigendum | "COPm (lowercase-m)" | "COPM-Minteo (uppercase-M)" |
| `project_abrigo_mento_native_only` β-corrigendum | "COPm (lowercase-m)" | "COPM-Minteo (uppercase-M)" |
| MEMORY.md index | "Mento-native COPm = `0x8A567e2a…`" | "`0xc92e8fc2…` is Minteo-fintech, OUT of scope" |

The lowercase-m/uppercase-M disambiguation is held throughout. The disposition memo uses the address `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` and `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` at first mention with abbreviated forms thereafter — fine.

**Advisory TW-3a (minor):** The original-content section of `project_mento_canonical_naming_2026.md` line 37 still reads "COPM (Minteo, unchanged)" with a trailing ⚠️ SUPERSEDED inline marker. The marker is correct and visible, but the parenthetical "(Minteo, unchanged)" on a line whose main label is "COPM" could mislead a quick reader scanning the bullet list before reading the inline warning. Recommend an additional bracket in the marker: "⚠️ SUPERSEDED — this is the **Minteo-fintech** address (out of Mento-native scope), NOT canonical Mento-native COPm; see β-corrigendum at top." Non-blocking — the corrigendum block at the top of the file already discloses this in plain language.

### TW-4 — Cross-reference completeness — CONFIRMED

Verified resolves:

- Rev-5.3.5 major-plan CORRECTIONS line 2458 cites the disposition memo path → file exists at `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`. ✓
- MR-β.1 §I CORRECTIONS line 325 cites the major-plan Rev-5.3.5 anchor → major-plan file contains the Rev-5.3.5 CORRECTIONS block at lines 2391-2466. ✓
- NB-α CORRECTIONS line 473 cites the disposition memo + major-plan Rev-5.3.5 anchor. Both resolve. ✓
- Disposition memo §8 references all five sub-plan corrigenda paths and the DE/RC artifact paths. All five paths resolve. The DE inventory commit `3611b0716` and RC spot-check commit `3286dfe66` are both quoted; the orchestrator's atomic commit hash is not yet in the memo (the memo predates the corrigenda commit) — acceptable because §8 is a forward-pointer references list, not a post-hoc audit log.
- Project memory β-corrigenda both cite the disposition memo path correctly (at `project_mento_canonical_naming_2026.md` line 22 and `project_abrigo_mento_native_only.md` line 22). ✓
- MEMORY.md index entries (lines 48 + 54) reflect β-corrigendum status with the two-address disambiguation. ✓

**No broken or stale reference.**

### TW-5 — Audit-trail completeness — CONFIRMED

Disposition memo records:
- Dune query ID `7378788` ✓ (§3.2 + §8)
- Free-tier execution + 0.012-credit cost ✓ (§3.2: "free tier, 0.012 credits"; §8: "~0.012 credits free-tier")
- Mento V3 docs URL verbatim ✓ (§8: `https://docs.mento.org/mento/protocol/deployments`)
- Celo Token List URL verbatim ✓ (§8: `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json`)
- DE deliverable commit `3611b0716` ✓ (header + §8)
- RC spot-check commit `3286dfe66` ✓ (header + §8)
- Dune project name `celocolombianpeso` decoded as `StableTokenV2` ✓ (§3.1)
- All six Mento-specific governance event names (`evt_exchangeupdated`, `evt_validatorsupdated`) are quoted verbatim ✓ (§3.1)
- Quantitative load-bearing facts table at §3.2 (285,390 / 5,015 / 16,918 / 78 weeks / 534 days / first + last UTC timestamps) ✓
- Anti-fishing invariant hashes (MDES_FORMULATION_HASH `4940360dcd2987…cefa`, decision_hash `6a5f9d1b05c1…443c`) cited at §4.1 + §5 ✓

The major-plan Rev-5.3.5 CORRECTIONS block re-cites all the same audit-trail facts at the plan-anchor level (lines 2393, 2399-2400, 2441-2442, 2458-2466). The redundancy is appropriate — it lets a future reviewer verify the disposition without needing to round-trip to the disposition memo.

**Audit trail is sufficient for independent post-cache-eviction re-verification. No finding.**

### TW-6 — Author voice / tone — CONFIRMED with one minor advisory

Voice across all five files is specific, anti-fishing-aware, audit-trail-aware, and code-agnostic. Quantitative claims are quoted at point-estimate precision (β̂ = −2.7987e−8 not "negative"; n = 76 not "small sample"; ρ(X_d, fed_funds) = −0.614 not "moderate"). Anti-fishing invariants are cited by name and hash. Every load-bearing empirical claim has a citation.

**Advisory TW-6a (minor):** In the major-plan Rev-5.3.5 CORRECTIONS at line 2402, the prose describes the 285,390 vs. 110,253 transfer-count comparison as "**2.6× more transfer events**." 285,390 / 110,253 = 2.588… — accurate to one decimal. Fine. Disposition memo §3.2 line 60 makes the same claim ("**2.6× larger** than the `0xc92e8fc2…` series we ingested for Rev-2 (285K vs. 110K transfers)") — also fine. Consistent and accurate.

**Advisory TW-6b (minor):** Disposition memo §4.2 line 78 says the existing scripts "are **NOT mutated** under MR-β.1 (per §B-2 invariant: no schema migrations under this sub-plan)." The reference is to MR-β.1 §B invariant 2, but the cited language ("No table renames; no schema migrations") is technically distinct from "scripts are not mutated." A reader could ask: does §B-2 actually forbid script edits, or just schema migrations? Recommend tightening to: "are NOT mutated under MR-β.1 (per §G-3 'Author or modify any code, schema-migration script, or notebook' out-of-scope reaffirmation)." Non-blocking.

### TW-7 — Out-of-scope reaffirmation reconciliation (§G vs §I) — NEEDS-WORK (non-blocking, advisory)

This is the most substantive editorial finding.

MR-β.1 sub-plan §G "Out-of-scope reaffirmation" (lines 266-280) declares:

> "This sub-plan does NOT:
> - Modify `project_mento_canonical_naming_2026` (correct as authored).
> - Modify `project_abrigo_mento_native_only` (already carries internal corrigendum).
> - Re-open the Rev-5.3.2 published estimates or the Rev-5.3.2 14-row resolution-matrix scope."

§I CORRECTIONS (post-HALT) **does** modify the framing of all three:
- `project_mento_canonical_naming_2026` carries a NEW β-corrigendum block (line 8 onward) — the COPM-address claim of the original entry is SUPERSEDED.
- `project_abrigo_mento_native_only` carries a NEW β-corrigendum block (line 8 onward) — the prior in-scope COPM address is now flipped.
- The Rev-5.3.2 published estimates remain byte-exact, but their **interpretation framing** is replaced (FAIL → scope-mismatch close-out). This is an interpretive re-opening of the Rev-5.3.2 disposition memo even though the numbers are immutable.

**This is not a contradiction at the substantive level** — both memory edits are append-only β-corrigenda (consistent with §B-4 anti-fishing-on-memory-edits discipline), and the published estimates are byte-exact preserved (consistent with §B-1 consume-only DuckDB). But the **§G text is now stale relative to §I** without an explicit reconciliation note.

**Recommended fix.** §G should carry a forward-pointer footnote to §I, e.g., a short paragraph appended after §G's last bullet:

> "**§G addendum under §I CORRECTIONS (Rev-5.3.5).** The HALT-VERIFY β-resolution required append-only β-corrigenda to both `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only` (per §B-4 anti-fishing-on-memory-edits discipline). The §G first two bullets ('does NOT modify') are read as 'does NOT silently modify; corrigenda are append-only and explicitly anchored.' The Rev-5.3.2 published estimates remain byte-exact (no re-estimation); only their interpretation framing is rescoped under §I, consistent with §B-1 consume-only invariants. The §G out-of-scope discipline is preserved; §I is the venue where the disposition's append-only memory edits + interpretation reframing are formally documented."

Non-blocking because the substantive consistency is intact and §I is the authoritative venue for the disposition; but a reader scanning §G in isolation could mistakenly conclude the corrigenda are out-of-scope when they are not. The fix is purely a cross-reference tightening.

### TW-8 — Length and prose discipline — CONFIRMED

- Disposition memo: 142 lines, 8 sections, every section load-bearing (HALT trigger / RC corroboration / Dune empirical probe / cascade implications / anti-fishing integrity / open question deferred / action plan / references). No padding.
- Major-plan Rev-5.3.5 CORRECTIONS: ~76 lines (2391-2466). The cascade enumeration (Rev-2 close-out, MR-β.1, NB-α, β-track, ζ-α, anti-fishing, memory state, reviewer cycle, file anchors) is purposeful — each cascade target gets exactly one paragraph; no section could be cut to half its length without losing a load-bearing pointer.
- MR-β.1 §I CORRECTIONS: ~57 lines. Sub-task rescope structure (1/2/3/4/5) parallels the original §C structure, which is appropriate — the reader who has §C internalized can map it 1:1 onto §I. No padding.
- NB-α CORRECTIONS: ~43 lines. Tightly bounded to interpretation-cell rescope; the four cell-class enumeration (NB1 §0 / NB2 estimation / NB3 sensitivity / README auto-rendered) is the minimum sufficient enumeration. No padding.

**No section could be cut to half its length without losing falsifiability anchors, audit-trail anchors, or invariant-preservation citations.**

---

## 3. Additional editorial findings outside the 8

### TW-9 (minor) — "open question deferred to β-spec" framing in disposition memo §6

Disposition memo §6 line 114 states:

> "**Whether `0x8A567e2a…` activity represents retail / consumer demand for Mento-native COPm versus Mento basket internal flows / arbitrage / governance.** This question is the structural-econometric identification challenge that β-spec must address."

This is editorially correct but underspecifies the question handoff. The Carbon partition rule in `project_carbon_user_arb_partition_rule` is cited (good) but the `0x8A567e2a…`-side analog is not yet defined. Recommend appending one sentence:

> "Specifically, β-spec must define a `trader = ?` partition rule for `0x8A567e2a…` activity analogous to `trader = 0x8c05ea30…` for Carbon DeFi, OR establish a different identification strategy (e.g., a sender / receiver clustering on the 5,015 distinct senders) if no single counter-side address dominates the activity."

Non-blocking (the question handoff is correctly scoped to Task 11.P.spec-β); a follow-on enrichment for the β-spec author's reference.

### TW-10 (very minor) — disposition memo §8 ordering

The references list at §8 puts Mento V3 docs URL **after** the Dune query ID and Dune project name. For a future reader trying to re-verify the canonical-StableTokenCOP claim (the load-bearing assertion), the Mento V3 docs URL is the primary citation and should appear earlier in the list. Suggest re-ordering: official Mento docs URL first → Celo Token List URL second → Dune query/project third. Non-blocking; current order is sequential-by-discovery, which is also defensible.

---

## 4. Specific quotable language flagged for change

Repeated here for the trio convergence record:

| File | Line | Current text | Recommended replacement (advisory) | Status |
|---|---|---|---|---|
| `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` | 481 | "every `interpretation-markdown` cell whose framing currently states or implies 'Mento-native hedge thesis tested and failed' must be reframed to…" | Replace "states or implies …" with grep-deterministic substring sets {banned: 'Mento-native hedge', 'hedge thesis', 'tested-and-failed', 'tested and failed', 'Mento-hedge-fail'} and {required canonical: 'Minteo-fintech scope-mismatch', 'scope-mismatch close-out', 'Rev-2 closes scope-mismatch'} per Advisory TW-2a. | Non-blocking |
| `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` | 350 | "future-revision rename recommendation = drop the `_ccop_` fragment and re-slug as `onchain_copm_minteo_daily_flow` (NOT executed under this sub-plan; recorded for future rev)." | Append acceptance clause for the present sub-task 3 (registry-doc must carry the per-table entry naming `onchain_copm_ccop_daily_flow` + Minteo-COPM out-of-scope tag + verbatim future-rev rename recommendation; falsifiable via section-presence) per Advisory TW-2b. | Non-blocking |
| `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` | 266-280 (§G) | The 9-bullet out-of-scope list including "does NOT modify `project_mento_canonical_naming_2026`" + "does NOT modify `project_abrigo_mento_native_only`" + "does NOT re-open the Rev-5.3.2 published estimates …" | Append §G addendum paragraph cross-referencing §I CORRECTIONS for the append-only β-corrigenda + interpretation-framing rescope, per finding TW-7. | Non-blocking |
| `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` | 78 | "are **NOT mutated** under MR-β.1 (per §B-2 invariant: no schema migrations under this sub-plan)." | "are **NOT mutated** under MR-β.1 (per §G-3 out-of-scope reaffirmation: 'Author or modify any code, schema-migration script, or notebook')." per Advisory TW-6b. | Non-blocking |
| `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md` | 37 | "COPM (Minteo, unchanged) — `0xc92e8fc2…` ⚠️ SUPERSEDED by β-corrigendum above; this address is Minteo-fintech, NOT Mento-native. The Mento-native COPm address is `0x8A567e2a…`." | Tighten the inline marker to bracket the parenthetical, e.g., "**[SUPERSEDED — Minteo-fintech, OUT of Mento-native scope]** COPM-Minteo — `0xc92e8fc2…` ⚠️ The Mento-native COPm address is `0x8A567e2a…`; see β-corrigendum at top." per Advisory TW-3a. | Non-blocking |
| `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` | 114 (§6) | "Whether `0x8A567e2a…` activity represents retail / consumer demand for Mento-native COPm versus Mento basket internal flows / arbitrage / governance." | Append: "Specifically, β-spec must define a `trader = ?` partition rule for `0x8A567e2a…` activity analogous to `trader = 0x8c05ea30…` for Carbon DeFi, OR establish a different identification strategy (e.g., sender / receiver clustering on the 5,015 distinct senders) if no single counter-side address dominates the activity." per finding TW-9. | Non-blocking |

---

## 5. Convergence recommendation

**PASS-with-non-blocking-advisories.**

Convergence is recommended without further author-fix-up cycle. The orchestrator may apply any subset of the seven advisories at convenience (most naturally: TW-7 §G addendum + TW-2a NB-α grep-deterministic criterion at NB-α dispatch time + TW-3a marker tightening at next memory edit; the remaining four can defer indefinitely without weakening the audit trail).

The disposition's load-bearing claims (Dune query 7378788; both URL anchors; both DE/RC commits; the byte-exact-immutability of Rev-2 estimates; the anti-fishing-invariant preservation) are independently re-verifiable by a future reviewer post-cache-eviction. The two-address / two-ticker naming convention is internally consistent across all five reviewed files plus the MEMORY.md index. The audit-trail-completeness gate (TW-5) is met. The code-agnostic discipline gate (TW-1) is met. The naming-consistency gate (TW-3) is met.

MR-β.1 sub-task 1 may re-dispatch under the rescoped framing once CR + RC peer reviews converge.
