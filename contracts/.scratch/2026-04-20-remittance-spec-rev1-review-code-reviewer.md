---
title: Code Reviewer — Rev-1 Remittance-surprise Spec Review
date: 2026-04-20
reviewer: Code Reviewer (agent dispatch, Task 2 of Phase-A.0 remittance plan)
target: contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md (commit e71044ce0)
parent_design: contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md (commit 437fd8bd2)
---

# Executive verdict: PASS-WITH-FIXES

The Rev-1 spec is structurally sound, internally consistent on all high-stakes decision cells (gate direction, MDES, HAC kernel/bandwidth, interpolation side, vintage), and cross-references the Rev-4 template faithfully. All 13 matrix rows have non-null resolutions with reviewer-checkable conditions. Six FLAG-severity fixes are recommended before implementation begins (most critically: the decision-hash extension formula in §9 under-specifies the input sort key domain; the MDES arithmetic in §4.5 has a visible rounding-consistency issue; the design-doc → Rev-1 gate-direction pivot deserves a one-line reconciliation note). No BLOCK findings. The spec enables Tasks 9–14 / 19–24 / 27 to proceed without further clarification, provided the six FLAGs are resolved.

## 1. 13-row matrix row-by-row audit

| # | Item | Verdict | Reasoning |
|---|---|---|---|
| 1 | Economic sign prior → two-sided gate | **VERIFIED** | §4.4 states `|β̂/SE|>1.645` at α=0.10 two-sided; three competing economic hypotheses enumerated; ties back to Model-QA BLOCK-1. Reviewer-checkable. |
| 2 | MDES pre-commitment | **NEEDS-REVISION** | §4.5 formula correct in shape (`2.80/√200 ≈ 0.198`), but the chained "≈ 0.20" then "≈ 0.030" rounds aggressively. FLAG-2 below. Verdict enum {PASS, FAIL, INCONCLUSIVE} is well-defined. |
| 3 | Alternate-LHS sensitivity | **VERIFIED** | Row 10 of §6 names `log(RV_w)`; reviewer-checkable in forest output. |
| 4 | HAC kernel | **VERIFIED** | §4.9 names Bartlett + Newey-West 1987; implementation string given. |
| 5 | Andrews bandwidth rule | **VERIFIED** | §4.9 gives exact formula `1.1447·(α_2·T)^{1/3}` + citation. Matches design-doc §Mandatory-inputs item 5 (plug-in variant). |
| 6 | Step-interpolation direction | **VERIFIED** | §4.6 specifies LOCF anchored on release dates with the exact decision rule "most recent release_date ≤ d_w". Kuttner/GSS citations. |
| 7 | AR order | **VERIFIED** | §4.7 primary AR(1), sensitivity SARIMA(1,0,0)(1,0,0)_12, row 7 of §6. |
| 8 | Vintage discipline | **VERIFIED** | §4.8 primary = real-time, sensitivity = current-vintage, pre-2015 proxy concession named. Size of affected sample (~382 obs) is quantified. |
| 9 | Reconciliation rule | **VERIFIED** | §4.3 lists three conditions verbatim; "import Rev-4 reconcile()" binds it to the existing codebase. |
| 10 | Structural-break test | **VERIFIED** | §8 specifies Quandt-Andrews sup-Wald over [2013-01-01, 2017-12-31] at α=0.05; break → subsample sensitivity rows. |
| 11 | GARCH(1,1)-X parametrization | **VERIFIED** | §4.2 primary = mean-equation; row 11 of §6 = variance-equation sensitivity. Addresses MQ-FLAG-5. |
| 12 | Dec-Jan seasonality | **VERIFIED** | Row 6 of §6, `n ≈ 789`, exclusion rule stated. |
| 13 | Event-study co-primary | **VERIFIED** | §7 fixes event date 2025-01-24, window [-1,+5], cumulative-abnormal-RV test statistic, three-branch joint-concordance rule. Campbell-Lo-MacKinlay cited. |

All 13 rows populated. Only row 2 (MDES) requires revision; the remaining twelve are reviewer-checkable and unambiguous.

## 2. BLOCK-severity findings

**None.** The spec contains no structural defect that prevents implementation.

## 3. FLAG-severity findings (should fix before Task 5 approval)

### FLAG-1 — Design-doc vs Rev-1 gate-direction pivot is not reconciled in narrative

Design-doc §Scientific-question pre-commits a **one-sided** T3b (`null: β̂_Rem ≤ 0`, gate `β̂ − 1.28·SE > 0`). The Rev-1 spec §4.4 pivots to **two-sided** per Model-QA BLOCK-1. The §10 "Why this is a fresh pre-commitment" section (item 2) acknowledges "two-sided T3b (remittance, with MDES rule)" in passing, but never states that this contradicts the design-doc and explains why the design-doc phrasing is superseded. Reviewer risk: reader of the chain "design → spec" may infer the spec is inconsistent. Fix: one sentence in §4.4 explicitly saying "supersedes design-doc §Scientific-question one-sided phrasing per Model-QA BLOCK-1 resolution." (Absolute path: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`.)

### FLAG-2 — MDES rounding arithmetic visibly inconsistent

§4.5: "`MDES ≈ 2.80 / √N_eff ≈ 0.198`" then "`MDES ≈ 0.20 · SD(RV^{1/3}_w,residualized) ≈ 0.030`". The value 0.198 is the MDES in SD-units; the 0.20 in the second line is the same number rounded. But row 2 of §12 also asserts "0.20 SD of residualized RV^{1/3}" as a pre-committed MDES, which is then used in the verdict rule `|β̂/SD_Y| < 0.20`. The verdict threshold (0.20) does not equal the actual computed MDES (0.198). At α=0.10, 80% power, N_eff=200, the reviewer cannot tell whether the pre-committed threshold is 0.198 or 0.20, and this affects any β̂ near the boundary. Fix: pick one value (0.20 is fine for pre-commitment), state it as the threshold, and remove the 0.198 floating-point variant from the verdict rule. Same for the `0.030` raw-units figure — underlying SD assumption (0.15) should be either frozen from a cited Rev-4 artifact or treated as post-hoc.

### FLAG-3 — §9 `sort(remittance_col_spec_hashes)` under-specifies sort key

The decision-hash extension formula is `SHA256(decision_hash_rev4 || sort(remittance_col_spec_hashes))`. The enumerated set — "primary-RHS hash, A1-R hash, regime-dummy hash, event-dummy hash, release-day-indicator hash, LOCF-surrogate flag, AR(1) params hash, SARIMA params hash, Basco-reconstruction recipe hash" — is 9 items, but `sort()` is meaningless without specifying the key (lexicographic on the hex hash? on the column name? on a canonical enum order?). Two implementations that differ in sort-key choice produce different decision hashes, defeating reproducibility. Fix: specify "sort = lexicographic on hex digest, ASCII byte-order, ascending" (or whichever canonical rule matches the Rev-4 `cleaning.py::_compute_decision_hash` implementation).

### FLAG-4 — §9 does not define serialization between `decision_hash_rev4` and sorted list

`SHA256(a || b)` requires `||` to be bytewise concatenation, but `b` is a *list of hashes*. The spec should specify: does `||` mean `decision_hash_rev4_bytes ++ concat(sorted_list_bytes)`? Or `+ joiner byte`? This is the same class of bug that PGP-signature bypass vulnerabilities rely on. Fix: one line of pseudocode, e.g. "concatenate raw 32-byte hash of Rev-4 with raw 32-byte hash of each column spec, in sorted lex order, then apply SHA-256 once."

### FLAG-5 — §4.2 GARCH-X mean-equation β-coefficient symbol mismatch with OLS

OLS uses `β_Rem` (§4.1). GARCH-X mean-equation uses `φ_Rem` (§4.2). This is fine. But the reconciliation rule §4.3 compares "sign(β̂_OLS) == sign(φ̂_GARCH-X)" — good. Only nit: §4.4 says "|β̂_Rem / SE(β̂_Rem)| > 1.645" which is ambiguous whether Rem refers to OLS or GARCH-X. From context (T3b is explicitly the OLS gate) this is obviously β̂_OLS, but a subscript (e.g. `β̂^OLS_Rem`) eliminates ambiguity.

### FLAG-6 — §7 event-study denominator definition

"cumulative abnormal RV^{1/3} over window, standardized by panel-pre-event SD" — "panel-pre-event SD" is not defined. Is it the full-panel-up-to-2025-01-23 SD of RV^{1/3}, or the panel-wide SD of weekly abnormal RV^{1/3} residualized by the OLS controls? The distinction matters because the raw RV^{1/3} SD and residualized-RV^{1/3} SD can differ by a factor of ~2 at the Rev-4 panel. Fix: one sentence specifying "SD = sample standard deviation of OLS-residualized RV^{1/3} over weeks w ∈ [2008-01-04, 2025-01-17]" (or the alternative if preferred).

## 4. NIT-severity findings

- **NIT-1**: §4.5 "approximate raw units: `MDES ≈ 0.030`" uses `≈` but could be stated as an exact computation given the SD assumption.
- **NIT-2**: §10 item 4 — "`REMITTANCE_VOLATILITY_SWAP.md` file-modification-time 2026-04-02 predates CPI-FAIL verdict (2026-04-19)" — mtime is filesystem metadata that can be altered by `touch`; cite the git blame/commit SHA instead for audit-grade provenance.
- **NIT-3**: References §13 — citation "Adrian, T. et al. (2026). 'Stablecoin inflows and FX markets.' IMF Working Paper 2025/141" — year mismatch (2026 paper, 2025 WP number). Likely intentional (publication lag), but add a publication-date qualifier for clarity.
- **NIT-4**: §4.7 says SARIMA is sensitivity row in §6, but §6 row 7 says "SARIMA(1,0,0)(1,0,0)_12 surprise". Good match; could add a back-reference "(see §4.7)" in row 7 of §6 for navigation.

## 5. Reference integrity spot-check

- **Andrews 1991 Econometrica 59(3)** — verified; HAC-covariance paper, the canonical citation for the AR(1) plug-in bandwidth formula. ✓
- **Newey-West 1987 Econometrica 55(3)** — verified; the original PSD-HAC paper, correctly cited as the Bartlett-kernel originator. ✓
- **Reiss-Wolak 2007 Handbook of Econometrics Vol 6A Ch. 64** — verified; this is the structural-econometrics chapter with the η/u/v error-decomposition framework invoked in §3. ✓
- **Andrews 1993 Econometrica 61(4)** — verified; the "Tests for parameter instability..." paper is the canonical sup-Wald structural-break reference used in §8. ✓
- **Campbell-Lo-MacKinlay 1997 Ch. 4** — verified; Princeton textbook, Ch. 4 is event-study methodology. ✓
- **Kuttner 2001, Gürkaynak-Sack-Swanson 2005** — both verified; canonical surprise-construction references. ✓

All spot-checked citations correspond to real works with correct journal/volume/year metadata.

## 6. Positive findings (preserve during any fix pass)

1. **§12 matrix is complete (13/13) with reviewer-checkable conditions.** This is exactly the gating deliverable named in the design doc §Mandatory-inputs; the spec delivers it in full. Under no fix should any row be collapsed or left as a narrative statement only.
2. **§4.3 reconciliation binds to the Rev-4 `reconcile()` implementation** — "verbatim from `scripts/nb2_serialize.py::reconcile()`" — this is the right architectural move: it makes the additive-only claim testable and avoids divergent re-implementation. Preserve verbatim.
3. **§4.5 three-way verdict enum {PASS, FAIL, INCONCLUSIVE}** is a material improvement over the Rev-4 two-way {PASS, FAIL}; the INCONCLUSIVE state is scientifically honest about power limitations. Preserve.
4. **§10 anti-fishing framing** distinguishes Rev-1 from a CPI-rescue attempt across four dimensions (mechanism, gate direction, sensitivity composition, provenance timestamp). Preserve verbatim; this is the discipline that vindicated the CPI FAIL.
5. **§4.8 pre-2015 vintage concession is transparent**: the spec openly names that ~382 of 947 observations use a proxy release date, rather than hiding the limitation. Preserve.
6. **§7 event-study co-primary uses REPORT-BOTH (not a synthetic verdict) under disagreement** — this is correct scientific practice and matches the Rev-4 reconciliation philosophy. Preserve.
7. **§4.2 explicit callout that `arch` library lacks exogenous variance support** — forces the implementation to use custom scipy L-BFGS-B likelihood. Preserve; prevents silent method drift at implementation time.

## Handoff readiness

The spec enables:
- **Tasks 9–14 (data ingestion)**: §4.6 (LOCF protocol), §4.7 (AR(1)), §4.8 (real-time vintage + pre-2015 proxy), §9 (decision-hash) all have enough detail for scripts-only implementation — *pending FLAG-3 and FLAG-4 resolution on the hash formula*.
- **Tasks 19–24 (notebook authoring)**: §4.1-4.5 (OLS + gate), §4.2 (GARCH-X), §4.3 (reconcile), §5 (T1-T7), §6 (13 sensitivity rows), §7 (event-study), §8 (break test) all have sufficient specificity — *pending FLAG-2 MDES arithmetic fix and FLAG-6 event-study denominator*.
- **Task 27 (Model QA review)**: the 13-row matrix gives the reviewer a structured PASS/FAIL instrument. No further Model-QA-facing clarification is needed from the CR perspective.

No BLOCK. Six FLAGs to fix. Matrix row 2 needs revision; rows 1, 3–13 are verified.

---

**End of Code Reviewer report.** Co-reviewers (Reality Checker, Technical Writer) dispatched independently; no cross-review overlap assumed.
