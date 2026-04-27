# CR Review — Rev-5.3.5 β-resolution disposition

**Date.** 2026-04-26
**Reviewer.** Code Reviewer (3-way trio post-hoc review per `feedback_pathological_halt_anti_fishing_checkpoint`)
**Branch / commit.** `phase0-vb-mvp` / disposition commit `00790855b`
**Scope.** disposition memo + major-plan Rev-5.3.5 CORRECTIONS + MR-β.1 §I CORRECTIONS + NB-α CORRECTIONS + project memory β-corrigenda

---

## 1. Verdict

**NEEDS-WORK** — one substantive contradiction (NB-α §B pre-commitment 6 vs. the CORRECTIONS block) requiring an explicit retraction-or-amend resolution; otherwise PASS-with-non-blocking-advisories on the remaining 5 CR concerns.

The disposition's substantive claims (β-pick, scope-mismatch reframe, byte-exact preservation of Rev-2 numbers, no threshold relaxation, address attribution) are internally consistent across the disposition memo, major-plan Rev-5.3.5, MR-β.1 §I, and the two project-memory β-corrigenda. The single failure is editorial-but-load-bearing: the NB-α sub-plan §B pre-commitment 6 (a NON-NEGOTIABLE binding clause) literally calls `0xc92e8fc2…` "Mento-native cCOP" — which is precisely the claim Rev-5.3.5 retracts. The Rev-5.3.5 CORRECTIONS block at end-of-NB-α describes an interpretation-cell reframe but does NOT explicitly retract or amend §B-6, leaving an internal contradiction inside a single sub-plan body. This must be fixed before the NB-α sub-plan can re-dispatch under the rescoped framing.

---

## 2. Findings on the 6 CR concerns

### 2.1 — Scope discipline (scope-mismatch close-out vs. threshold-relaxation rescue)

**CONFIRMED clean** at the disposition + major-plan + MR-β.1 §I level; **PARTIAL CONCERN** at NB-α §B-6 (see §3.1 below).

The disposition memo (file:lines 64-74, 99-110) is unambiguous: Rev-2 published estimates are byte-exact immutable; what changes is interpretation framing; this is a "scope correction, not a threshold relaxation." The three Rev-2 anomalies (sign-flip, ρ(X_d, fed_funds) = −0.614 confounder, T1 REJECTS) are explicitly framed as "consistent with Minteo-fintech being a payments / B2B-API rail rather than Mento-basket hedge volume" — i.e., the X_d wasn't measuring what we thought it was measuring. This is the correct scope-mismatch interpretation and does not constitute silent re-litigation of the gate FAIL.

Major-plan Rev-5.3.5 (lines 2404-2410) and MR-β.1 §I (lines 327, 328-329) carry the same framing byte-aligned. The "scope-mismatch close-out, NOT threshold-relaxation rescue" boundary is explicitly maintained in all three documents.

The user's pick was β. None of the reviewed materials reads like rescue-claim drift toward "Rev-2 actually shows a positive Mento hedge signal once we re-interpret." The framing throughout is "Rev-2 doesn't test Mento-hedge demand at all because the X_d was wrong-scope" — which is the correct disposition.

### 2.2 — Internal consistency (byte-aligned addresses, quantities, hashes)

**CONFIRMED** across all six required documents — with one caveat below.

Cross-document byte-check on the load-bearing strings:

| Field | Disposition memo | Major plan Rev-5.3.5 | MR-β.1 §I | NB-α CORRECTIONS | `mento_canonical_2026` | `abrigo_mento_native_only` |
|---|---|---|---|---|---|---|
| In-scope Mento-native | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` | same | same | same | same | same |
| Out-of-scope Minteo | `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | same | same | same | same | same |
| Total transfers (Mento-native) | 285,390 | 285,390 | implicit via cross-ref | not stated (not needed) | 285,390 | 285,390 |
| Distinct senders | 5,015 | not restated | not restated | n/a | not stated | not stated |
| Weeks active (Mento-native) | 78 | 78 ≥ N_MIN=75 | 78 ≥ N_MIN=75 | not stated | 78 | 78 |
| First transfer | 2024-10-31 16:35:48 UTC | 2024-10-31 → 2026-04-26 | 2024-10-31 → 2026-04-26 (live) | n/a | 2024-10-31 → 2026-04-26 | 2024-10-31 → 2026-04-26 |
| N_MIN | 75 unchanged | 75 unchanged | 75 unchanged | 75 unchanged (cited verbatim) | n/a | n/a |
| MDES_FORMULATION_HASH | `4940360dcd2987…cefa` unchanged | `4940360dcd2987…cefa` unchanged | `4940360dcd2987…cefa` unchanged | `4940360dcd2987…cefa` unchanged | n/a | n/a |
| Rev-4 decision_hash | `6a5f9d1b05c1…443c` unchanged | `6a5f9d1b05c1…443c` unchanged | `6a5f9d1b05c1…443c` unchanged | `6a5f9d1b05c1…443c` unchanged | n/a | n/a |
| Rev-2 β̂ | `−2.7987e−8` | (not restated; preserved by ref) | (not restated) | `−2.7987e−8` | n/a | `−2.7987e−8` |
| Rev-2 n | 76 | (not restated) | (not restated) | 76 | n/a | 76 |
| Out-of-scope total transfers | 110,253 | 110,253 | 110,253 | 110,253 | 110,253 | 110,253 |

All values byte-aligned. Anti-fishing invariants (N_MIN, POWER_MIN, MDES_SD, MDES_FORMULATION_HASH, decision_hash, 14-row resolution-matrix scope) are preserved unchanged across all documents.

**Caveat (non-blocking).** The disposition memo's Section 3.1 lists 24 decoded Dune tables; the table count "24 decoded tables" appears verbatim in major-plan Rev-5.3.5 (line 2464) and the disposition memo (line 36, 139), but the MR-β.1 §I and the project-memory corrigenda use "24 decoded tables" only via cross-reference; this is acceptable byte-aligned because they reference rather than restate. Not a finding.

### 2.3 — Anti-fishing-invariant adherence

**CONFIRMED** across all reviewed documents.

- `N_MIN = 75` preserved verbatim (disposition memo §5.1; major plan line 2438; MR-β.1 §I line 371; NB-α CORRECTIONS body).
- `POWER_MIN = 0.80` preserved verbatim (disposition memo §5.2; major plan line 2439; MR-β.1 §I line 372; NB-α CORRECTIONS body).
- `MDES_SD = 0.40` preserved verbatim (same locations).
- `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` preserved verbatim and pinned in 3+ documents.
- Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` preserved verbatim and pinned.
- 14-row resolution-matrix scope preserved verbatim ("Rev-2 14-row resolution-matrix scope unchanged (byte-exact preserved)" in major plan line 2443; MR-β.1 §I line 374-375).

The byte-exact-immutability of Rev-2 published estimates is explicitly enumerated in three places and is consistent: numbers are not re-estimated, not re-binned, not re-thresholded; β̂ = −2.7987e−8, n = 76, T3b FAIL all stay frozen. Verified at disposition memo §4.1 (line 66), major plan Rev-5.3.5 (line 2406-2407), MR-β.1 §I `### Anti-fishing-invariant integrity preserved` (lines 368-376), NB-α CORRECTIONS (`Numbers stay byte-exact` and the dispatch-unit-by-dispatch-unit reaffirmation).

DuckDB consume-only invariants confirmed: no row mutation, no schema migration, no table rename, no `econ_pipeline.py`/`econ_schema.py`/`query_api.py` mutation under MR-β.1 (disposition memo §4.2 line 78; major plan line 2428-2429; MR-β.1 §I line 342, 370). The `0xc92e8fc2…`-derived tables are tagged DEFERRED-via-scope-mismatch annotation-only. This is correct and clean.

### 2.4 — Plan-vs-implementation boundary clarity

**CONFIRMED**.

β-track Rev-3 ingestion plumbing is explicitly deferred to Task 11.P.spec-β + Task 11.P.exec-β:
- Disposition memo §4.2 line 78: "β-spec sub-plan (Task 11.P.spec-β) and β-execution sub-plan (Task 11.P.exec-β) are the appropriate venues for new ingestion plumbing — those sub-plans have not yet been authored on disk and will be authored post-MR-β.1 convergence."
- Major plan Rev-5.3.5 lines 2426-2429 (`### Cascade — β-track Rev-3 ingestion plumbing (deferred to Task 11.P.spec-β / Task 11.P.exec-β)`).
- MR-β.1 §I sub-task 2 rescope (line 340) explicitly carves out "do the carbon basket queries need to swap `0xc92e8fc2…` → `0x8A567e2a…` for Mento-basket trading attribution? **Out of scope for sub-task 2 acceptance**; in scope for Task 11.P.spec-β identification design."

NB-α reframe is interpretation-only:
- NB-α CORRECTIONS body: "Numbers stay byte-exact. Only interpretation-cell framing changes."
- The dispatch-unit-by-dispatch-unit list (NB1 §0, NB2 estimation rows, NB3 sensitivity, README auto-render) is consistent: every change is a markdown-text reframe.
- Out-of-scope reaffirmation explicitly enumerates: no re-estimation, no re-binning, no re-thresholding, no β-track Rev-3 X_d ingestion, no DuckDB row mutation, no Solidity / Python / schema-migration authoring.

No Solidity contract / no DuckDB schema migration / no test mutation appears anywhere in the reviewed CORRECTIONS bodies. Boundary is clean.

### 2.5 — Cascade-claim correctness (interpretation reframe vs. rescue claim)

**CONFIRMED** as interpretation reframe, not rescue claim.

The disposition memo §4.1 (lines 70-74) frames the three Rev-2 anomalies as:

> - **Sign-flip (β̂ < 0)** — consistent with Minteo-fintech being a payments / B2B-API rail rather than Mento-basket hedge volume.
> - **ρ(X_d, fed_funds) = −0.614 confounder** — consistent with Minteo's user base being FX-payments-driven (sensitive to US monetary cycle via remittance corridors), not macro-hedge-driven.
> - **T1 REJECTS predictive-not-structural** — consistent with Minteo activity being a payments-cycle predictor, not a structural hedge-demand signal.

The language is rigorously the **right** disposition: "Rev-2 doesn't test Mento-hedge demand at all because the X_d was wrong-scope." There is NO drift toward "Rev-2 actually shows a positive Mento hedge signal once we re-interpret." Major-plan Rev-5.3.5 line 2409 reinforces this:

> The anomalies are NOT "negative evidence on Mento-native hedge demand"; they are "Minteo activity has its own different signature."

This is the correct framing. The cascade is bounded — three diagnostic findings get re-attached to a different X_d entity, with no claim that the FAIL verdict on the (now-renamed-as-Minteo) X_d is somehow recovered as a PASS for the Mento-native X_d.

NB-α CORRECTIONS body line under "For NB2 estimation-row interpretation cells" carries the same discipline: "the gate FAIL on T3b reflects Minteo-fintech-X_d's predictive-not-structural relationship with Y₃, NOT a test of Mento-native hedge demand." This is consistent and clean.

### 2.6 — Sub-plan structural coherence (MR-β.1 §B/§C vs. §I rescope)

**CONFIRMED clean**.

Re-read of MR-β.1 §B pre-commitments 1–7 against §I rescope:

- **§B-1 (consume-only DuckDB invariants).** §I rescope (line 370 "Consume-only DuckDB invariants preserved") matches; no contradiction.
- **§B-2 (no table renames, no schema migrations).** §I rescope (line 342 "No table is dropped, renamed, or migrated; the rescope is annotation-only") matches verbatim; the future-rev rename recommendation for `onchain_copm_ccop_daily_flow` (line 350) is explicitly recorded as a recommendation, not executed — consistent with §B-2.
- **§B-3 (registry as future authoritative source).** §I rescope (line 374-376) preserves "Address registry post-converge byte-exact-immutability invariant" — consistent.
- **§B-4 (anti-fishing on memory edits).** §I rescope effectively triggers append-only β-corrigenda blocks at top of both `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only`; no silent rewrite. Both memory files preserve the prior content with explicit ⚠️ SUPERSEDED markers (verified in `project_mento_canonical_naming_2026` line 37). Consistent.
- **§B-5 (editorial-only deliverable).** §I rescope is purely editorial (sub-task rescopes are documentation amendments + a re-dispatch under rescoped framing). No analytical work, no estimation, no notebook authoring under MR-β.1. Consistent.
- **§B-6 (Rev-5.3.4 RESCOPE supersedes Rev-5.3.3 framing).** §I sub-task 4 (lines 352-357) explicitly handles the "two-layer inversion" precedent: Rev-5.3.4 framing of "0xc92e8fc2 = Mento-native COPM" was itself wrong; corrected by user + Dune evidence 2026-04-26. The §B-6 invariant ("Rev-5.3.4 RESCOPE supersedes Rev-5.3.3") is now itself partially superseded by Rev-5.3.5, but §I documents this transparently. NOT a contradiction; this IS the corrigendum trail working as designed. (CR ADVISORY A1: it would be slightly cleaner if §I explicitly said "§B-6's appeal to Rev-5.3.4 framing is itself overlaid by Rev-5.3.5; Rev-5.3.5 framing is now authoritative" — but the §I body already conveys this via sub-task 4. Non-blocking.)
- **§B-7 (TR research file preserved with corrigendum).** §I sub-task 4 strengthens the corrigendum (two layers) — consistent extension.

**§C sub-task acceptance criteria vs. §I rescopes:**

- **§C sub-task 1.** Original acceptance: "Memo enumerates all six Mento-native tokens (COPM, USDm, EURm, BRLm, KESm, XOFm). Every address matches the addresses recorded in `project_mento_canonical_naming_2026`." §I rescope: now records BOTH addresses (in-scope COPm + out-of-scope COPM-Minteo); rescoped acceptance is explicit (§I line 336 "Sub-task 1's rescoped acceptance: enumeration of all six in-scope Mento-native tokens + the one out-of-scope Minteo entry"). The phrase "Every address matches the addresses recorded in `project_mento_canonical_naming_2026`" in original §C now resolves correctly because `project_mento_canonical_naming_2026` itself carries the β-corrigendum and the COPm address is now `0x8A567e2a…`. NOT a contradiction.
- **§C sub-task 2.** Original acceptance #3: "For DIRECT tables, records the on-chain address(es) and links to sub-task 1's inventory; **any non-Mento address HALTS to the user per the consume-only invariant**." §I rescope tags `0xc92e8fc2…`-derived tables DEFERRED-via-scope-mismatch instead of HALTing. **POTENTIAL CONFLICT** — but resolved by §I's framing: the HALT-VERIFY GATE already fired (DE deliverable `3611b0716`), the user's β disposition is the resolution, and the DEFERRED tag is the post-disposition annotation-only handling (no row mutation per consume-only invariant; the tables are not deleted, just re-tagged in audit). The original §C-2-#3 acceptance criterion was authored under Rev-5.3.4 framing where `0xc92e8fc2…` was assumed Mento-native; under Rev-5.3.5 the address is now classified out-of-scope, the HALT already fired and was resolved by user disposition, so the DEFERRED tag is the correct post-disposition state. NOT a live contradiction; the §C-2-#3 invariant fired and was satisfied as designed.
- **§C sub-tasks 3, 4, 5.** §I rescopes are extensions, not contradictions. Sub-task 3 registry now explicitly excludes `0xc92e8fc2…` from per-token body (correct under β); sub-task 4 strengthens the TR corrigendum to document both inversion layers (correct); sub-task 5 strengthens the safeguard memo with the two-layer-inversion precedent (correct).

Overall §B / §C / §I structural coherence: **clean**. No live contradictions inside MR-β.1.

---

## 3. Additional findings outside the 6 listed concerns

### 3.1 — NB-α §B pre-commitment 6 is contradicted by Rev-5.3.5 and not explicitly retracted in the CORRECTIONS block (NEEDS-WORK; the only blocker)

**File.** `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
**Line.** 35 (§B pre-commitment 6, NON-NEGOTIABLE binding clause).

**Quoted exact language flagged for change (current text, line 35):**

> 6. **Mento-native ONLY.** Per `project_abrigo_mento_native_only` and Rev-5.3.3 pre-commitment 6, the X_d in this Rev-2 re-presentation is the published Mento-native cCOP basket-volume series (address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`). The cCOP-vs-COPM provenance audit (Task 11.P.MR-β.1) is a separate sub-plan and does NOT block this Rev-2 re-presentation; the Rev-2 published estimates remain byte-exact regardless of how the table-naming clarification lands.

**The contradiction.** This pre-commitment, which the sub-plan itself flags as "Pre-commitment (binding)", literally calls `0xc92e8fc2…` "Mento-native cCOP basket-volume series." Under Rev-5.3.5 this is exactly the attribution being retracted: `0xc92e8fc2…` is Minteo-fintech (out of Mento-native scope); the in-scope Mento-native COPm address is `0x8A567e2a…`. The CORRECTIONS block at the end of NB-α describes interpretation-cell reframes but does not explicitly retract or amend pre-commitment 6. A reader landing in §B will see a binding pre-commitment that contradicts the Rev-5.3.5 disposition, and a reader of §I CORRECTIONS will see no explicit "§B-6 is hereby retracted / amended" hook.

**This matters because** §B is labeled "Pre-commitment (binding)" and pre-commitment 6 carries a substantive scope claim (which token's data the notebook represents). The CORRECTIONS block discipline (per `feedback_pathological_halt_anti_fishing_checkpoint`) requires that retracted pre-commitments be explicitly retracted, not silently superseded by an interpretation-only reframe. The NB-α CORRECTIONS body explicitly says "Numbers stay byte-exact. Only interpretation-cell framing changes" — but pre-commitment 6 is not an interpretation cell; it is a binding scope-claim line in the §B pre-commitment block that the §I CORRECTIONS does not touch.

**Suggested resolution (NEEDS-WORK fix-up).** Add an explicit retraction inside the NB-α CORRECTIONS block, e.g.:

> **§B pre-commitment 6 retraction.** Pre-commitment 6's claim that `0xc92e8fc2…` is "Mento-native cCOP basket-volume series" is RETRACTED under Rev-5.3.5. The address is Minteo-fintech (out of Mento-native scope per the major-plan Rev-5.3.5 CORRECTIONS block + `project_abrigo_mento_native_only` β-corrigendum). The Rev-2 X_d ingested for this notebook re-presentation is the Minteo-fintech series. The notebook's analytical content is unchanged — it byte-exact reproduces the Rev-5.3.2 published estimates against this (now-correctly-classified) X_d series. The pre-commitment's "no block on Rev-2 re-presentation" clause is honored: numbers stay byte-exact; framing is now scope-mismatch close-out per the rest of this CORRECTIONS block.

This is editorial work (≤ 10 lines of markdown). Once added, the sub-plan becomes internally consistent.

### 3.2 — Disposition memo §4.4 vs. major-plan Rev-5.3.5 cascade — minor wording asymmetry (non-blocking)

The disposition memo §4.4 (line 88) lists eleven `onchain_*` tables on `0xc92e8fc2…` enumerated by name (`onchain_copm_transfers`, `onchain_copm_daily_transfers`, ..., `onchain_copm_ccop_daily_flow`, plus the `carbon_per_currency_copm_volume_usd` proxy). MR-β.1 §I sub-task 2 (line 338) restates the same eleven tables verbatim. Major-plan Rev-5.3.5 (line 2417) describes the cascade in narrative form ("the entire `onchain_copm_*` family + `carbon_per_currency_copm_volume_usd` proxy") without enumerating the eleven names. This is acceptable cross-reference style and not a finding, but flagging as non-blocking advisory: a future TR-style consistency advisory could ask the major-plan body to either enumerate or explicitly cross-reference the disposition memo §4.4 / MR-β.1 §I sub-task 2. Strictly editorial.

### 3.3 — `onchain_carbon_*` follow-up question (non-blocking, correctly deferred)

MR-β.1 §I sub-task 2 line 340 raises a sharp follow-up: "do the carbon basket queries need to swap `0xc92e8fc2…` → `0x8A567e2a…` for Mento-basket trading attribution?" and explicitly defers this to Task 11.P.spec-β. CR notes this is a real downstream question (the `onchain_carbon_arbitrages` and `onchain_carbon_tokenstraded` tables include `0xc92e8fc2…` as one of the basket counter-side addresses under Rev-5.3.4 framing, and that attribution may now be wrong if Carbon DeFi MM is actually trading `0x8A567e2a…`-side rather than `0xc92e8fc2…`-side). The deferral to Task 11.P.spec-β is correct — it's a structural-econometric identification question, not an MR-β.1 question. Non-blocking advisory: when β-spec is authored, this question must surface as an explicit identification-design line (not silently absorbed). The deferral framing in §I is correct and clean.

### 3.4 — Disposition memo §6 "Open question deferred to β-spec" is appropriately scoped (PASS)

Disposition memo §6 (line 114) raises the right question — "Whether `0x8A567e2a…` activity represents retail / consumer demand for Mento-native COPm versus Mento basket internal flows / arbitrage / governance" — and correctly scopes it OUT of the disposition and INTO Task 11.P.spec-β. This is the structural-econometric identification challenge that β-spec must address; the 285K-transfer / 5K-sender / 16K-receiver headcount being "necessary but not sufficient" is the correct epistemic posture. CR endorses this deferral; no rescue-claim drift.

### 3.5 — Project memory β-corrigenda land at top with original preserved (PASS)

Both `project_mento_canonical_naming_2026.md` and `project_abrigo_mento_native_only.md` carry β-corrigendum blocks at top with the original content preserved below under explicit "Original content (pre-β-corrigendum, preserved for audit trail)" headers. The ⚠️ SUPERSEDED inline marker on the COPM line in `project_mento_canonical_naming_2026.md` (line 37) is a correct application of the append-only-or-section-replace-with-corrigendum discipline (`feedback_pathological_halt_anti_fishing_checkpoint` anti-fishing-on-memory-edits). MEMORY.md index entries (lines 48 and 54) carry refresh hooks pointing to the β-corrigenda. Clean.

---

## 4. Summary of language flagged for change

**BLOCKING (NEEDS-WORK, must-fix before re-dispatch):**

`contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` line 35 (§B pre-commitment 6) — add explicit retraction inside the NB-α CORRECTIONS block (see §3.1 above for suggested language).

**NON-BLOCKING (advisory, may defer):**

- Major-plan Rev-5.3.5 line 2417 — consider enumerating the eleven `onchain_copm_*` tables by name OR adding a cross-reference to disposition memo §4.4 / MR-β.1 §I sub-task 2 line 338. Strictly editorial.
- MR-β.1 §I optional clarifier (CR ADVISORY A1 in §2.6 above) — could add an explicit "§B-6's appeal to Rev-5.3.4 framing is itself overlaid by Rev-5.3.5; Rev-5.3.5 framing is now authoritative" hook. Non-blocking; the §I body already conveys this via sub-task 4.

---

## 5. Recommended next-step disposition

1. Apply the §3.1 fix-up (add §B-6 retraction inside NB-α CORRECTIONS block).
2. RC + TW peers will return their reviews; converge as a trio.
3. Once converged, re-dispatch MR-β.1 sub-task 1 under the rescoped framing per disposition memo §7 step 8.
4. The two non-blocking advisories (§3.2, §2.6 advisory A1) can be batched into the next Rev-5.3.x or Rev-5.4 housekeeping CORRECTIONS block if desired; they are not blockers for re-dispatch.

The disposition itself (β-pick + scope-mismatch close-out + byte-exact preservation + anti-fishing-invariant integrity + interpretation-only reframe of NB-α + deferral of new ingestion plumbing to Task 11.P.spec-β / Task 11.P.exec-β) is structurally sound and matches the user's pick. The single editorial gap in NB-α §B-6 is the only thing standing between this disposition and PASS-with-non-blocking-advisories.
