---
title: Technical Writer review — Remittance-surprise spec Rev-1
date: 2026-04-20
reviewer: Technical Writer (independent, parallel to Code Reviewer + Reality Checker)
spec_under_review: contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md
spec_hash: e71044ce0
status: PASS-WITH-FIXES
---

# Executive verdict: PASS-WITH-FIXES

The Rev-1 spec is internally coherent, structurally faithful to the Rev-4 CPI template, and successfully resolves the 13 Phase-0 mandatory inputs enumerated in the parent design doc. A first-time reader with only this document in hand can reconstruct the primary gate, the co-primary, the reconciliation rule, and the sensitivity sweep without guesswork. However, four clarity defects (two near-BLOCK, two FLAG) prevent an unqualified PASS: the design-doc's pre-committed **one-sided** T3b gate was flipped to **two-sided** without a "supersedes" banner; the LOCF protocol in §4.6 is ambiguous about the daily-rollup vs. release-date granularity; terminology drift between `β̂_Rem` / `β_Rem` / `φ̂_Rem` is not disciplined; and four softening modal verbs ("typically", "should", "may") leak rescue room into a pre-committed anti-fishing document. Fix these and the spec is shippable to Task 9.

# 13-row resolution-matrix audit

| Row | Item | Grade | Finding / proposed fix |
|---|---|---|---|
| 1 | Gate direction | PASS | Clean. §4.4 justification (stabilizer vs stress-response) is economically literate and reviewer-auditable. |
| 2 | MDES | NEEDS-CLARIFICATION | Approximation chain (N_eff → MDES → raw-units) uses "≈" four times without stating which SD is used for the `≈ 0.030` raw-unit figure. **Fix:** after `SD ≈ 0.15`, add "(Rev-4 post-control residual SD; panel_fingerprint.json field `rv_residualized_sd`)." |
| 3 | Alternate-LHS | PASS | Row 10 in §6 is cited by number; Bollerslev-Zhou justification is appropriate. |
| 4 | HAC kernel | PASS | Bartlett + Rev-4 continuity is explicit. |
| 5 | Bandwidth | PASS | Formula, citation, and statsmodels call-site are all stated. |
| 6 | Step-interpolation | NEEDS-CLARIFICATION | §4.6 says "most recent monthly release with `release_date ≤ d_w`." But `d_w` is Friday close of week w; no rule states whether a Friday-release-date is included in week w (same-week) or rolls to w+1. **Fix:** add "Releases landing on d_w itself (Friday ≤ 16:00 COT BanRep cutoff) are included in week w; later-than-cutoff releases roll to w+1." |
| 7 | AR order | PASS | Primary + sensitivity cleanly split. |
| 8 | Vintage | NEEDS-CLARIFICATION | "Proxy release date = 15th of the month following the reference-period" contradicts §3's "up to 45-day lag" language. **Fix:** state "~45-day lag ≈ reference-month + 45d; spec rounds to the 15th of the following month for a deterministic surrogate." |
| 9 | Reconciliation | PASS | Three conditions + Rev-4 `reconcile()` import is reviewer-checkable. |
| 10 | Structural break | PASS | Date range, α, and detection → subsample-emit rule are all explicit. |
| 11 | GARCH-X parametrization | PASS | Primary (mean) vs sensitivity (variance) split matches MQ-FLAG-5. |
| 12 | Dec-Jan seasonality | PASS | Row 6 in §6 is cited; n ≈ 789 is checkable. |
| 13 | Event-study co-primary | PASS | Event, window, statistic, and joint-concordance rule are all pre-specified. |

# BLOCK findings (structural clarity)

**None.** No finding rises to structural blocker. The two near-BLOCKs (below) are demotable with small-surface fixes.

# FLAG findings (strongly recommended before Task 9)

**FLAG-1: Gate-direction flip vs. design doc — missing "supersedes" note.** The design doc §Scientific question pre-commits a **one-sided** T3b (`β̂_Rem − 1.28·SE > 0`, α=0.10, critical value 1.28). The Rev-1 spec §4.4 and row 1 of the matrix adopt a **two-sided** gate (|β̂/SE| > 1.645). This is the correct resolution given Model-QA BLOCK-1, but the spec does not say "this supersedes the design-doc one-sided wording." A reader reconciling the two documents will flag an apparent contradiction. **Fix:** in §4.4, add one sentence: "This two-sided resolution supersedes the design-doc §Scientific question one-sided placeholder; the design doc explicitly defers sign-prior resolution to the Rev-1 spec (see design doc Phase-0 mandatory input #1)."

**FLAG-2: LOCF ambiguity re: daily rollup.** §4.6 says "most recent monthly release." The underlying BanRep series is **monthly**, so the current observation is unambiguously the last monthly release. But the parallel phrasing in §2.3 ("market participants observe… BanRep remittance releases (monthly with 45-day lag)") leaves unclear whether the weekly panel uses the release-date's value or a within-month decayed value. **Fix:** §4.6 first sentence → "LOCF from BanRep monthly release value (no within-month decay, no daily rollup); the value is step-held from the release date until the next release date."

**FLAG-3: Terminology inconsistency on the surprise coefficient.** The spec uses four variants: `β_Rem` (§4.1 population), `β̂_Rem` (§4.4 estimator), `φ_Rem` / `φ̂_Rem` (§4.2 GARCH-X), and `β̂_remittance` (none — good, this variant is absent). But §4.3 mixes `β̂_OLS` with `φ̂_GARCH-X` as reconciliation-rule labels while §4.4 uses `β̂_Rem`. **Fix:** add a one-line notation block after §4 heading: "`β_Rem` = OLS population coefficient on `ε^{Rem}_w`; `β̂_Rem` = its estimate; `φ_Rem`, `φ̂_Rem` = GARCH-X mean-equation analogs. The T3b gate is on `β̂_Rem`; reconciliation compares `β̂_Rem` and `φ̂_Rem`."

**FLAG-4: Softening modal verbs in a pre-committed spec.** Four instances of rescue-enabling modals in a document that is supposed to pre-commit outcomes:
- §4.2: "surprise enters the **mean equation**" — OK, indicative.
- §5 T1: "AR(1) surprise **should** be orthogonal to controls" → **must be orthogonal**, or frame as testable null (the current wording reads like an expectation, not a falsifiable test).
- §5 T5: "Normality… robustness implication flagged but not blocking" — acceptable, but the phrase "flagged" is vague. **Fix:** "reported in NB3 as diagnostic output; does not gate verdict."
- §4.6: "release date = actual BanRep publication date" — OK.
- §2.3: "Remittance releases are **typically** low-salience" → **are** low-salience (citation present, no need to hedge).
- §3 v-error: "monthly→weekly step-interpolation artifact" — OK.

Replace "should" / "typically" with "does" / "is" (three sites) to close rescue room.

# NIT findings (style/polish)

- **NIT-1:** §1 end says "see §4.6 for interpolation protocol" — correct, but §2.3 and §3 also cite interpolation without forward-reference. Add `(see §4.6)` in both.
- **NIT-2:** §6 row numbering uses Arabic numerals 1–13 but the gating-matrix §12 also uses 1–13 for different items. A reader cross-referencing "row 10" could hit either list. **Fix:** label §6 rows "S1–S13" (sensitivity) and keep §12 at 1–13 (resolution).
- **NIT-3:** §11 lists deliverables at a phase granularity (NB1, NB2, NB3) but the parent plan has Tasks 9–30c with finer artifact-per-task grain. Add a one-line pointer: "Per-task artifact mapping is enumerated in the Phase-A.0 implementation plan (Tasks 9–30c)."
- **NIT-4:** §9 references `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` — good, but no pointer to the source-of-truth file. **Fix:** add "(authoritative source: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`)."
- **NIT-5:** §13 references include Adrian et al. 2026 "IMF Working Paper 2025/141" — mixed year. Verify and align (this is a factual check RC should confirm; flagging as clarity issue because dual-year confuses readers).
- **NIT-6:** §5 table uses "|β̂/SE|" in T3a but `|β̂_Rem / SE(β̂_Rem)|` in §4.4. Unify to the subscripted form.

# Narrative → matrix alignment check

§§4.1–4.9 map to matrix rows as follows, and each section has a corresponding row (no drift):
- §4.1 (primary OLS) → row 1 + row 4 + row 5 + row 9 (composite; acceptable).
- §4.2 (GARCH-X) → row 11.
- §4.3 (reconciliation) → row 9.
- §4.4 (T3b gate) → row 1.
- §4.5 (MDES) → row 2.
- §4.6 (LOCF) → row 6.
- §4.7 (AR order) → row 7.
- §4.8 (vintage) → row 8.
- §4.9 (HAC) → rows 4 + 5.
- §6 → rows 3, 11, 12.
- §7 → row 13.
- §8 → row 10.

**No drift detected.** Every matrix row is traceable to at least one narrative section.

# Cross-reference integrity

All 14 internal section references checked (§1.2, §2.3, §3, §4.1–4.9, §5, §6, §7, §8, §9, §10, §11, §12, §13). All point to real sections. One minor gap: §4.5 references "Rev-4 CPI exercise effective DOF" without a citation to the specific Rev-4 file; recommend NIT-7 addition: `(see contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb3_forest.json field 'n_eff' ≈ 200)`.

# Anti-fishing framing consistency

§10 asserts anti-fishing discipline. Cross-check: §4.4 two-sided gate is pre-registered, §4.5 MDES+INCONCLUSIVE verdict is pre-registered, §6 sensitivity rows are enumerated 1–13 before any β̂ is computed, §7 event-study has pre-specified window and joint-concordance rule, §10 explicitly declines post-hoc §9 spotlights under FAIL/INCONCLUSIVE. **Consistent.** No rescue language detected. FLAG-4 softening-modal fixes will strengthen this further.

# Positive findings

1. **13-row resolution matrix (§12) is exemplary** — each row has resolution + justification + reviewer-checkable condition in a scannable table. This is the reader-auditability artifact the Rev-4 process was missing at the equivalent stage.
2. **Anti-fishing framing (§10) is structurally separate from estimation strategy (§4)** — the reader is not left inferring commitment discipline from buried sentences.
3. **Provenance argument (§10 bullet 4)** — citing `REMITTANCE_VOLATILITY_SWAP.md` mtime 2026-04-02 as pre-FAIL evidence is a concrete, filesystem-verifiable anti-rescue claim.
4. **MDES + three-valued verdict enum (§4.5)** — distinguishing FAIL from INCONCLUSIVE is a substantive methodological upgrade over Rev-4's binary PASS/FAIL.
5. **Vintage-discipline concession (§4.8)** — honestly scoped to post-2015 without concealing the pre-2015 proxy compromise; reviewer-friendly.
6. **GARCH-X dual placement (§4.2 + row 11)** — resolving MQ-FLAG-5 via pre-registered sensitivity rather than primary change preserves continuity with Rev-4 while acknowledging the vol-of-vol alternative.

# Summary

Ship after FLAG-1 through FLAG-4 fixes. The four NEEDS-CLARIFICATION matrix rows are one-line additions, not rewrites. No BLOCK. The spec is ready for Task 9 once the modal-verb pass, the terminology notation block, and the "supersedes design-doc" note are inserted.

Report absolute path: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-spec-rev1-review-technical-writer.md`
