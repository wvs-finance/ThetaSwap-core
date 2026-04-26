---
title: Rev-1 Remittance-surprise Spec — Three-Way Review Fix Log
date: 2026-04-20
task: Phase-A.0 Task 5
target: contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md
word_delta: 2829 → 3847 (+1018; over +600 target, driven by §4.8 Phase-1 pre-2015 protocol + §9 concatenation pseudocode)
---

# Reality Checker

| # | Finding | Disposition |
|---|---|---|
| RC FLAG-1 | IMF cite Adrian 2025/141 → Aldasoro WP/26/056 | APPLIED §4.4, §13 (verified in `LITERATURE_PRECEDENTS.md` lines 44–47). |
| RC FLAG-2 | Basco & Ojeda-Joya 1273 zero corpus trace | APPLIED (methodology-escalation downgrade per Task 5 protocol). §2.3, §6 S9, §9, §13 reframed to "BanRep Borradores de Economía series, methodology placeholder — Borrador number and authors to be confirmed during Phase-1." S9 SKIPPED-if-unverifiable. |
| RC FLAG-3 | Pre-2015 archive claim unverified | APPLIED (methodology-escalation rewrite). §4.8 replaced with three-step Phase-1 protocol: (1) attempt actual-release-date recovery; (2) tag unrecovered as `proxy`; (3) if proxy > 20% of 947 obs, primary restricts to vintage-strict subsample, full-window demoted. The 382/947 claim removed; subsample sizes are pre-registered Phase-1 empirical outputs. |
| RC NIT-1 | Panel end-date | APPLIED — §4.1 corrected to 2008-01-07 to 2026-02-23 per `nb1_panel_fingerprint.json`. |
| RC NIT-2 | Petro-Trump date framing | APPLIED — §7 frames 2025-01-26 Sunday standoff with 2025-01-24 Friday trading-week boundary; citations to `COPM_MINTEO_DEEP_DIVE.md` + `LITERATURE_PRECEDENTS.md`. |
| RC NIT-3 | Venezuelan-migration onset uncited | APPLIED — §8 anchors `COLOMBIAN_ECONOMY_CRYPTO.md` §1.5 with conservative-flanking acknowledgment. |

# Code Reviewer

| # | Finding | Disposition |
|---|---|---|
| CR FLAG-1 | Supersedes banner one-sided→two-sided | APPLIED §4.4. |
| CR FLAG-2 | MDES 0.198/0.20 rounding | APPLIED §4.5 threshold = exactly 0.20 with "(rounded up from 0.198 for audit simplicity)"; 0.030 illustrative only. |
| CR FLAG-3 | §9 sort-key | APPLIED: lexicographic ascending on column-name (UTF-8 byte comparison), NOT hex. |
| CR FLAG-4 | §9 `||` concat semantics | APPLIED pseudocode: 32-byte raw digests, `buf += col_hash`, single final `sha256(buf).digest()`. |
| CR FLAG-5 | β̂_Rem / φ̂_Rem / ψ̂_Rem drift | APPLIED new §4.0 Notation block; §4.4 pins `β̂_Rem` = OLS; §12 rows 3/11/12 subscripted. |
| CR FLAG-6 | Event-study SD denominator | APPLIED §7: 52-week window preceding event date (w ∈ [2024-01-26, 2025-01-17]) with regime-drift rationale. |
| CR NIT-1 | Raw-unit exactness | APPLIED (illustrative framing). |
| CR NIT-2 | mtime → git SHA | APPLIED §10 item 4 adds git-blame cryptographic-provenance note. |
| CR NIT-3 | Adrian year mismatch | SUPERSEDED by RC FLAG-1. |
| CR NIT-4 | §6 S7 back-reference | APPLIED. |

# Technical Writer

| # | Finding | Disposition |
|---|---|---|
| TW FLAG-1 | Supersedes note | APPLIED (merged with CR FLAG-1). |
| TW FLAG-2 | LOCF daily-rollup / Friday-cutoff | APPLIED §4.6: "no within-month decay, no daily rollup"; Friday 16:00 COT cutoff; ties → earlier reference-period. |
| TW FLAG-3 | Terminology drift | APPLIED (merged with CR FLAG-5). |
| TW FLAG-4 | Softening modal verbs | APPLIED — Grep verified zero remaining instances. |
| TW Row 2 | MDES SD source | APPLIED §4.0 Notation pins residualized-SD as NB2-emitted. |
| TW Row 6 | Friday-cutoff | APPLIED via TW FLAG-2. |
| TW Row 8 | 45-day vs 15th | APPLIED §4.6: "15th of month following reference-period (approximates ~45-day rhythm)." |
| TW NIT-1 | Forward-reference polish | DEFERRED — cosmetic; §4.0 Notation + §4.6 anchor suffice. |
| TW NIT-2 | §6 row labels S1–S13 | APPLIED; §12 cross-refs updated. |
| TW NIT-3 | Deliverables → plan pointer | APPLIED §11. |
| TW NIT-4 | §9 authoritative-source pointer | APPLIED. |
| TW NIT-5 | Adrian year mismatch | SUPERSEDED by RC FLAG-1. |
| TW NIT-6 | T3a subscripted form | APPLIED. |

# Preserved positives (verified intact)

Three-way verdict enum {PASS, FAIL, INCONCLUSIVE} §4.5; `reconcile()` import §4.3; event-study REPORT-BOTH §7; decision-hash byte match §9; 947 row-count. **Strengthened**: §4.8 pre-2015 Phase-1 protocol; §10 git-SHA provenance note.

# Methodology-escalation invocations

Two items downgraded rather than silently patched, per Task 5 protocol:
1. **Basco & Ojeda-Joya 1273** — methodology placeholder; S9 SKIPPED-if-unverifiable.
2. **Pre-2015 BanRep archive** — Phase-1 empirical-recovery protocol with 20%-proxy subsample-restriction trigger.

Both flagged "deferred to Phase-1 acquisition evidence."

# Final status

13 FLAGs applied; 13 NITs applied or superseded; 1 deferred as cosmetic. No BLOCKs. Frontmatter → "REV-1 (reviewed CR+RC+TW 2026-04-20, fixes applied)". Ready for Task 6 handoff.
