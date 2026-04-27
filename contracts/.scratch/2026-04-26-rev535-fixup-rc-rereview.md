# Reality Checker — Single-Pass Re-Review on Rev-5.3.5 β-Disposition Fix-Up Bundle

**Date:** 2026-04-26
**Commit under review:** `29e2c7710` (post-trio fix-up bundle)
**Predecessor disposition commit (RC PASS-w-adv):** `00790855b`
**Reviewer:** Reality Checker (TestingRealityChecker discipline)
**Scope:** Narrow re-review verifying that the 6 high-value fix-ups land correctly on the trio findings (CR §3.1 BLOCKER + TW-2a + TW-7 + RC-3 + RC-8 + TW-6b) without anti-fishing-invariant regression or scope creep.
**Tool budget used:** 6 calls (5 Bash/Read + 1 WebFetch) — within the 5-9 envelope.

---

## 1. Verdict

**PASS.**

All 6 high-value fix-ups landed correctly. No anti-fishing invariant relaxed. Commit scope file-bounded to the expected 4 modified plan/sub-plan/memo + 3 new trio review files. Working Mento V3 URL re-verified live and still returns the canonical StableTokenCOP entry at `0x8a567e2ae79ca692bd748ab832081c45de4041ea`. No new findings.

This re-review unblocks MR-β.1 sub-task 1 re-dispatch under the rescoped framing.

---

## 2. Per-fix-up findings

### Fix-up 1 — CR §3.1 BLOCKER: NB-α §B-6 retraction hook

**File:** `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
**Verdict:** LANDED CORRECTLY.

Verified at lines 477–483:

- The Rev-5.3.5 CORRECTIONS block now contains an explicit "§B pre-commitment 6 retraction (post-CR-trio-finding §3.1, 2026-04-26)" sub-heading (line 477), grep-discoverable.
- The retraction text at line 479 explicitly identifies `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` as **Minteo-fintech COPM-Minteo** (out of Mento-native scope) and `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` as the in-scope Mento V2 `StableTokenCOP`.
- Line 481 explicitly preserves byte-exact-immutability: *"numbers stay byte-exact (Rev-2 published estimates reproduce against the Phase 5a parquets unchanged); the X_d in this notebook re-presentation IS the published Minteo-fintech series (now correctly classified out-of-Mento-native-scope); the framing rescope to scope-mismatch close-out per the rest of this CORRECTIONS block carries the disposition forward without re-estimating, re-binning, or re-thresholding any Rev-2 row."*
- Line 483 documents the audit-trail preservation discipline: original §B-6 text at line 35 left unchanged; future revisions can replace-in-place under further CORRECTIONS-block discipline OR leave §B-6 + retraction stacked indefinitely (per `feedback_pathological_halt_anti_fishing_checkpoint` append-only-or-section-replace-with-corrigendum).
- Independent confirmation: line 35 (the original §B-6) was inspected and remains literally *"Mento-native cCOP basket-volume series ... 0xc92e8fc2947e32f2b574cca9f2f12097a71d5606"* — unmodified, as required for audit-trail preservation. Reader landing in §B-6 must read line 35 → CR §3.1 finding flagged this as the CR-blocker → Rev-5.3.5 CORRECTIONS retraction is now the overlay that resolves the contradiction without rewriting history.

CR §3.1 BLOCKER cleared.

### Fix-up 2 — TW-2a falsifiability: NB-α grep-deterministic substring sets

**File:** `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
**Verdict:** LANDED CORRECTLY.

Verified at lines 489–493:

- Line 489 introduces the TW-2a-specified rule with explicit grep-verifiable framing: *"with deterministic grep-verifiable acceptance per TW-2a advisory."*
- Line 491 enumerates the **banned substring set** (≥5 entries; required minimum 5 per the dispatch envelope was 'Mento-native hedge', 'hedge thesis', 'tested-and-failed', 'tested and failed', 'Mento-hedge-fail'; the landed set adds a sixth `'Mento-hedge-thesis-tested-and-failed'` for tighter coverage — superset of required, no relaxation).
- Line 492 enumerates the **required canonical reframe substring set** (≥3 entries required per dispatch envelope: 'Minteo-fintech scope-mismatch', 'scope-mismatch close-out', 'Rev-2 closes scope-mismatch'; the landed set adds `'Minteo-fintech X_d'` as a fourth — superset of required).
- Line 493 explicitly cites the falsifiability mechanism: *"`grep -i -F` over migrated notebooks must show **zero** matches in the banned set across the migrated NB-α corpus, and **≥1** match in the canonical set per affected interpretation cell. The 3-way review on NB-α deliverables runs this grep as a falsifiable acceptance criterion; any banned-set match in the migrated corpus fails review."*

The "states or implies" hand-wavable phrasing has been replaced by deterministic, machine-checkable substring criteria. TW-2a falsifiability gap closed.

### Fix-up 3 — TW-7: MR-β.1 §G addendum cross-referencing §I CORRECTIONS

**File:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md`
**Verdict:** LANDED CORRECTLY.

Verified at lines 282–284:

- Line 282 introduces the addendum with grep-discoverable header: *"§G addendum under §I CORRECTIONS (Rev-5.3.5) — TW-7 reconciliation."*
- Line 284 reconciles the apparent contradiction between §G's "does NOT modify project memory" and §I's append-only β-corrigenda by clarifying the discipline: *"The §G first two bullets (\"does NOT modify project_mento_canonical_naming_2026\" / \"does NOT modify project_abrigo_mento_native_only\") are read under §I as **\"does NOT silently modify; corrigenda are append-only and explicitly anchored to the Rev-5.3.5 CORRECTIONS block.\"**"*
- The same paragraph reaffirms byte-exact-immutability of Rev-5.3.2 published estimates (no re-estimation; consume-only DuckDB) and points readers scanning §G in isolation to read §I before concluding the corrigenda are out-of-scope.
- The original §G 9-bullet list above the addendum was sampled (line 148–149 contain the §G structural clauses on Mento-native scope and per-token sections) — unchanged; the addendum is a clean append, not a §G rewrite.

TW-7 reconciliation gap closed.

### Fix-up 4 — RC-3: working Mento V3 URL replaces 404 URL

**Files:** `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` + `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Verdict:** LANDED CORRECTLY.

Verified by `grep -F`:

- Both files now cite the working URL `https://docs.mento.org/mento-v3/build/deployments/addresses.md` (1 hit each).
- Both files explicitly mark the prior URL `https://docs.mento.org/mento/protocol/deployments` as superseded / 404. Disposition memo line 135: *"the prior memo URL `https://docs.mento.org/mento/protocol/deployments` 404s and is superseded."* Major plan tail: *"The earlier-cited URL `https://docs.mento.org/mento/protocol/deployments` 404s and is superseded."*
- WebFetch on the working URL (live, 2026-04-26) returned: *"The contract address for StableTokenCOP on Celo Mainnet is: **0x8a567e2ae79ca692bd748ab832081c45de4041ea**. This is listed in the 'Shared (Mento v2 & v3)' section under the Celo Mainnet tab, with an implementation address of 0x434563B0604BE100F04B7Ae485BcafE3c9D8850E."*
- This independently re-confirms (a) URL still serves the canonical entry as of re-review time, (b) the address byte-aligns with `project_mento_canonical_naming_2026` β-corrigendum and the disposition memo §1 table, (c) the implementation contract `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E` matches RC's earlier "all six Mento StableTokens share implementation" cross-strengthening finding (RC review file finding R-cross).

RC-3 stale-URL finding closed.

### Fix-up 5 — RC-8: forward-looking joint-coverage note

**File:** `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`
**Verdict:** LANDED CORRECTLY.

Verified at line 80 (full disposition memo §4.2 read inline):

- Sub-paragraph header is grep-discoverable: *"**RC-8 forward-looking note (joint-coverage feasibility, deferred to β-spec).**"*
- The note explicitly states the 78-week activity window is X_d-only-conditioned: *"The 78-week activity window for `0x8A567e2a…` (2024-10-31 → 2026-04-26 live) is X_d-only-conditioned."*
- The note explicitly quantifies the joint-N at ~73 weeks vs N_MIN=75: *"the chronological joint window is approximately **73 weeks — 2 weeks short of N_MIN=75**."*
- The note offers two natural resolutions: *"(a) refresh the Y₃ panel forward by ≥3 weeks before β-spec data freeze, OR (b) document the joint-N shortfall and pre-commit to a relaxation-or-defer disposition under the established `feedback_pathological_halt_anti_fishing_checkpoint` discipline (no silent threshold tuning)."*
- The note explicitly states this does NOT block the disposition: *"This does NOT block this disposition (Rev-2 closes scope-mismatch on byte-exact-immutable estimates; the disposition is independent of β-track Rev-3's joint-N feasibility). It is recorded here as a forward-looking constraint that β-spec MUST address at authoring time."*
- Cross-references the verification provenance: *"RC-8 verified via independent Dune query 7379527 + DuckDB Y₃ panel max-date probe 2026-04-26."*

All 4 dispatch-envelope sub-criteria for RC-8 landed verbatim. Major-plan tail (Rev-5.3.5 fix-up paragraph) also references the RC-8 note for cross-document consistency.

RC-8 forward-looking concern documented and deferred per anti-fishing-on-thresholds discipline.

### Fix-up 6 — TW-6b: cross-reference tightened to §G-3

**File:** `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`
**Verdict:** LANDED CORRECTLY.

Verified at line 78:

- The "scripts NOT mutated" claim now references §G-3 (out-of-scope reaffirmation) verbatim: *"they are **NOT mutated** under MR-β.1 (per §G-3 out-of-scope reaffirmation: \"Author or modify any code, schema-migration script, or notebook\" — the sub-plan body is editorial-only)."*
- The previously-cited §B-2 invariant ("no schema migrations") is no longer referenced for the "scripts NOT mutated" claim. §B-2 still appears elsewhere in the memo for its actual scope (DuckDB schema invariant), but it is no longer mis-anchored on the script-mutation claim.

TW-6b cross-reference scoping fix closed.

---

## 3. Regression check

### Concern 7 — Anti-fishing-invariant load-bearing strings

`grep -F` / `grep -E` over the 4 fix-up files returned the following counts (case-sensitive where the source is case-sensitive):

| String | Hits | Verdict |
|---|---|---|
| `N_MIN = 75` (with surrounding "= 75" or "=75") | 17 across 4 files (1 ccop-provenance, 12 major plan, 3 disposition memo, 1 NB-α) | UNCHANGED — never relaxed to "≥75" or higher |
| `4940360dcd2987` (MDES_FORMULATION_HASH prefix) | 5 hits across files (NB-α §C-2-#1, disposition memo §4.1 + §5, major plan Rev-5.3.5 + earlier revs) | UNCHANGED |
| `6a5f9d1b05c1` (decision_hash prefix) | 4 hits (disposition memo §4.1 + §5, major plan Rev-5.3.5 + earlier revs) | UNCHANGED |
| `−2.7987e−8` (Rev-2 β̂; en-dash unicode form) | Multiple hits (NB-α §A, disposition memo §4.1, major plan Rev-5.3.5 cascade) | UNCHANGED |
| `0x8A567e2a` (in-scope Mento V2 StableTokenCOP) | Present in all 4 fix-up files | UNCHANGED, in-scope |
| `0xc92e8fc2` (out-of-scope Minteo-fintech COPM-Minteo) | Present in all 4 fix-up files | UNCHANGED, out-of-scope |

Combined with the major plan §"Anti-fishing-invariant integrity" block (read inline above) which explicitly enumerates `N_MIN = 75 unchanged. POWER_MIN = 0.80 unchanged. MDES_SD = 0.40 unchanged. MDES_FORMULATION_HASH = 4940360dcd2987…cefa unchanged. Rev-4 decision_hash = 6a5f9d1b05c1…443c unchanged. Rev-2 14-row resolution-matrix scope unchanged.`

**Verdict: PASS.** No threshold tuning, no silent rewrite of any anti-fishing fact, no in-scope / out-of-scope address swap.

### Concern 8 — Commit scope file-bounded

`git diff 29e2c7710~1 29e2c7710 --name-only` returned exactly 7 files:

1. `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (modified, +28/-?)
2. `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-code-reviewer.md` (NEW, 187 lines)
3. `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-reality-checker.md` (NEW, 316 lines)
4. `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-technical-writer.md` (NEW, 174 lines)
5. `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (modified, +4)
6. `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (modified, +4)
7. `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (modified, +14)

Total: 715 insertions, 12 deletions across 7 files.

- 0 `.duckdb` file changes ✓
- 0 `.sol` (Solidity) changes ✓
- 0 `.ipynb` (notebook) changes ✓
- 0 `.py` (Python) changes ✓
- 0 `econ_schema.py` / `econ_pipeline.py` / `query_api.py` changes ✓ (consume-only DuckDB invariant preserved)
- 0 `foundry.toml` / `test/*.sol` / `src/*.sol` changes ✓ (scripts-only scope unchanged; this is a docs-only commit)

**Verdict: PASS.** Commit scope is exactly the 6 high-value fix-ups + the 3 trio review-file audit-trail bundle. No regression on consume-only DuckDB or scripts-only scope discipline.

---

## 4. New findings

**None.**

The 5 deferred non-blocking advisories called out in the dispatch envelope (TW-2b sub-task 3 acceptance, TW-3a memory marker tightening, TW-9 partition-rule guidance for β-spec author, TW-10 §8 references ordering, CR §3.2 11-table enumeration) remain explicitly deferred. Each has a recorded surface point (next sub-task dispatch / β-spec authoring time / Rev-5.4 housekeeping CORRECTIONS), and none meets the criteria for surfacing as a new RC blocker.

The Mento V3 URL working-status was independently re-verified live; if it were to 404 in the future, the disposition memo and major plan both flag the prior URL as superseded already, so a future URL-drift would be remediable by the same RC-3 mechanism.

---

## 5. Re-review summary

**Verdict: PASS.**

| Concern | Status |
|---|---|
| CR §3.1 BLOCKER (NB-α §B-6 retraction) | LANDED CORRECTLY |
| TW-2a (NB-α grep-deterministic substring sets) | LANDED CORRECTLY |
| TW-7 (MR-β.1 §G addendum) | LANDED CORRECTLY |
| RC-3 (working Mento V3 URL replaces 404) | LANDED CORRECTLY (URL re-verified live) |
| RC-8 (forward-looking joint-coverage note) | LANDED CORRECTLY |
| TW-6b (§G-3 cross-reference tightening) | LANDED CORRECTLY |
| Anti-fishing-invariant load-bearing strings | UNCHANGED (PASS) |
| Commit scope file-bounded | PASS (7 files; 0 code/notebook/DuckDB changes) |
| New findings | None |

**Convergence:** RC re-review PASS. CR + TW already at PASS-with-non-blocking-advisories on the trio convergence. The disposition is fully converged on the fix-up bundle.

**Unblocks:** MR-β.1 sub-task 1 re-dispatch under the rescoped framing (sub-task 1 deliverable rewritten to record both addresses; `0x8A567e2a…` as in-scope Mento V2 `StableTokenCOP`; `0xc92e8fc2…` preserved in audit-trail as out-of-scope Minteo-fintech).

**Next checkpoint:** Sub-task 2 dispatch (DEFERRED-via-scope-mismatch tagging across the `onchain_copm_*` table family). The 5 deferred non-blocking advisories surface naturally at sub-task 3 (TW-2b) / β-spec authoring (TW-9 + RC-8) / Rev-5.4 housekeeping (TW-3a, TW-10, CR §3.2).

---

**Reality Checker discipline note.** This was a single-pass narrow re-review on a fix-up commit, dispatched per `feedback_pathological_halt_anti_fishing_checkpoint` post-fix-up convergence protocol. No rubber-stamping; every claim was evidence-grounded against the file contents (Read + grep) and one independent live external probe (Mento V3 URL re-fetch). The trio's prior PASS-with-non-blocking-advisories status from commit `00790855b` review files was treated as the established baseline; this re-review verifies only the delta in commit `29e2c7710`.
