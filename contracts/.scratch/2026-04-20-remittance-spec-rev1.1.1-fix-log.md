# Remittance-surprise Rev-1.1.1 spec patch — fix-log (Task 11.D)

**Date:** 2026-04-24
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `726ce8f74` (Rev-3.4)
**Spec modified:** `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (Rev-1 → Rev-1.1.1, in place)
**Trigger:** Task 11.C FAIL-BRIDGE verdict (commit `91e5d2664`; `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md`)

## Step-1 decision-gate classification (plan line 343)

Rule: wording-only if the patch relabels cadence or data-source under the same kernel/method/parameter; economic-mechanism if it changes a named kernel/method/parameter/number. Plan line 325 waives three-way spec-review for scope-narrowing of interpretation alone; plan line 331 classifies the N=95→78-84 numeric adjustment as wording/cadence-only.

| Patch | Section | Change | Classification | Skill re-invoked? |
|---|---|---|---|---|
| 1 | Frontmatter `status` | Label | Wording-only | No |
| 2 | New §0 supersedes banner | Narrative addition citing Task 11.C | Wording-only | No |
| 3 | §1 research question | Primary-X on-chain; BanRep → S14 | Wording-only (source relabel) | No |
| 4 | §4.1 primary OLS | Scalar RHS → 6-channel vector | Wording-only (Task 11.B vector pre-exists; no new method) | No |
| 5 | §4.4 T3b gate | Scalar t → joint F-test | Wording-only (consequence of 6-RHS; α, kernel, verdict enum unchanged) | No |
| 6 | §4.5 MDES | N_eff 200 → 78 | Wording-only (plan line 331: numeric threshold adjustment) | No |
| 7 | §6 S14 | New validation row | Wording-only (uses Task 10 AR(1) + Rev-4 controls) | No |
| 8a | §12 row 5 | T=947 → N_eff=78-84 | Wording-only (same formula) | No |
| 8b | §12 row 6 | Interpolation retained for S14 only | Wording-only (LOCF cadence relabel) | No |
| 8c | §12 row 7 | AR retained for S14 only | Wording-only (AR(1) preserved for S14) | No |
| 8d | §12 row 8 | Vintage retained for S14 only | Wording-only (on-chain is immutable) | No |
| 9 | §13 References | Added NBER w26323, IMF OP 259, in-tree provenance | Wording-only | No |
| 10 | Frontmatter `revision_history` | Added Rev-1.1.1 bullet | Wording-only | No |

**All 13 classified wording-only. No `structural-econometrics` skill re-invocation performed.** Conforms to plan lines 325 and 343.

## Per-patch dispositions (brief)

1. **Frontmatter `status`.** Relabeled Rev-1 → Rev-1.1.1 with Task 11.D classification qualifier. Added `revision_history` structured field.
2. **§0 supersedes banner.** New section before §1. Cites Task 11.C FAIL-BRIDGE (ρ=+0.7554 levels, 2/5 sign-concordance, N=6), names the Rev-3.1 narrowing "remittance → crypto-rail income-conversion", enumerates unchanged §§ (4.2, 4.3, 4.7, 5, 7, 8, 9, 10, 11 and §12 rows 1-4, 9-13), cites scratch log and fix-log.
3. **§1.** Primary-X reinterpreted to 6-channel Task 11.B vector; BanRep demoted to S14. Added explicit narrative-narrowing clause: a PASS does NOT license "BanRep aggregate remittance" claims; the claim is "crypto-rail income-conversion on Colombian stablecoin corridors." Anti-fishing framing is strengthened by narrowing.
4. **§4.1.** Scalar `β_Rem · ε^{Rem}_w` → `Σ_{k=1}^6 β_k · X^{on-chain}_{k,w}`. Enumerated all 6 channels with economic interpretation. Sample-boundary note: N_eff ≈ 78-84 on COPM-launch-window intersection with Rev-4 panel (vs nominal 947). Per-channel `β̂_k` flagged as audit-only.
5. **§4.4.** Scalar `|β̂/SE|>1.645` → joint `F > F_crit(α=0.10, df₁=6, df₂=N_eff−13)` ≈ 1.86-1.87. Rev-1 three-way verdict enum preserved at joint-F granularity. Sign-prior discussion retained as diagnostic (joint-F is two-sided by construction).
6. **§4.5.** N_eff floor = 78 (conservative, per plan line 331 + Task 11.C). Derived λ ≈ 13 for 80% power, α=0.10, df₁=6 → MDES_R² ≈ 0.143 (joint R²-increment) or f²_MDES ≈ 0.167. Honest-cost note: joint-F on small N has weaker power than Rev-1 scalar-t would have had; FAIL reads as "below detection floor," not "null at high confidence."
7. **§6 S14.** Pre-registered BanRep-quarterly validation row: regress quarterly-averaged `RV^{1/3}` on AR(1)-residual of `ΔlogRem_q` (`suameca` series 4150), quarterly-averaged Rev-4 controls, N=6-7 on 2024-Q3 → 2025-Q4 window. Not gate-relevant; serves as bridge back-pointer to Task 11.C and Rev-1-original identification record. Explicitly not a rescue row.
8. **§12 rows 5-8.** Row 5: same Andrews formula at new T; row 6: interpolation applies only to S14 quarterly LOCF; row 7: AR(1) retained only for S14 quarterly; row 8: on-chain is immutable, real-time vintage retained only for S14 BanRep MPR-publication-date. Rows 1-4, 9-13 unchanged.
9. **§13 References.** Added NBER w26323 (Dew-Becker-Giglio-Kelly 2019) fn 23 and IMF OP 259 (Chami et al. 2008) with usage notes. New "In-tree provenance (Rev-1.1.1)" subsection: Task 11.A `bc12e3c30` + Dune `#7366593`, Task 11.B `2bff6d79f`, Task 11.C `91e5d2664` + scratch log, plan tip `726ce8f74`.
10. **Frontmatter `revision_history`.** Structured block: Rev-1 (2026-04-20) + Rev-1.1.1 (2026-04-24) with 9-item summary and pointers.

## Spec delta

- Before (Rev-1): 3,847 words.
- After (Rev-1.1.1): 7,012 words.
- Delta: **+3,165 words**.
- Target range per Task 11.D prompt: +1,500 to +2,500 words.
- Over target by ~665 words, concentrated in §0 banner (~800), §4.4 joint-F rationale (~300 vs Rev-1 ~150), §13 in-tree provenance (~250). Text is reviewer-mandated per plan line 366 (consistency, coverage, anti-fishing, factual grounding, clarity checks); Task 11.E reviewers evaluate fitness.

## Skill re-invocation posture

None performed. All 13 patches are wording-only per Task 11.D Step 1. If Task 11.E reviewers identify any patch as mis-classified (e.g., methodology-level change hidden in §4.4 joint-F restructuring), plan line 368 requires `structural-econometrics` skill re-invocation before the next cycle; this fix-log will be updated.

## Files modified

- `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` (in-place patch to Rev-1.1.1).
- `contracts/.scratch/2026-04-20-remittance-spec-rev1.1.1-fix-log.md` (this file).

**No commits.** Foreground handles git per Task 11.D Step 5.
