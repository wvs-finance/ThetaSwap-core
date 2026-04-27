# Plan Rev-5 Review — Senior PM Lens

**Target:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `8db00fe74`
**Focus:** scope / execution / task-granularity / dependency-graph / convergence-bounds.

## 1. Verdict

**ACCEPT-WITH-FIXES.** New Phase-1.5.5 block (11.L–Q + 11.M.5) is well-scoped task-by-task, but downstream Phases 2b/3/4 and the spec-coverage self-check still read as remittance-scoped. Two blocking findings; five QoL.

## 2. Findings

**PM-P1 (HIGH, blocking) — Phase 2b/3/4 not rescoped.**
Tasks 12–15 use `CleanedRemittancePanelV1/V2/V3` while 11.Q introduces `CleanedInequalityPanelV1`. Tasks 13 (a1r-bridge aux), 14 (corridor), 17a–c (remittance-AR(1) surprise), 27/28 (Rev-1 spec inputs), 30a (β̂_remittance / `gate_verdict_remittance.json`) still target the retired scope. **Fix:** Rev-3.1-style rider block at Phase 2b/3/4 head: rename panel dataclass, primary X, artifact paths; RETIRE Task 13 a1r-bridge aux and Task 14 corridor-reconstruction.

**PM-P2 (HIGH, blocking) — Spec-coverage self-check stale.**
Lines 1174–1210 reference Rev-1.1 §4.x, Task 11.D, A1-R-bridge, corridor, Dec-Jan seasonality. Under Rev-5, the 13-input matrix is re-derived at Task 11.O, not 11.D. Arithmetic claims "46 tasks" while the banner says 54. **Fix:** rewrite the self-check with 11.O/11.Q hand-offs per row; reconcile count to 54.

**PM-P3 (MEDIUM) — 11.M.5 naming.**
"M.5" is visually ambiguous with Rev-1.1 / Rev-3.1 minor-rev notation. Recommend rename to 11.MM (doubled-letter) or renumber L–Q → M–R. Pragmatic cost low; flag but acceptable if user prefers.

**PM-P4 (MEDIUM) — 11.M stall path missing.**
Agent `aa0bf238c4ca1b501` is critical-path (→ M.5 → N → O → P → Task 12). No timeout, ETA, or escalation. **Fix:** Step 4 "if missing CSVs at T+6h re-dispatch; at T+12h escalate to user; partial-data pivot = 11.N downgrades to mint+burn-only."

**PM-P5 (LOW) — 11.O Step 4 cycle-cap.**
"Targeted lit re-check" after equation drafted — no bound. If 11.L contradicts equation, silent iteration inside 11.O is possible. **Fix:** cap at 1 re-read round; on material conflict, escalate as "return-to-11.L" not in-task iteration. Rule 13 already covers 11.P.

**PM-P6 (LOW) — Non-stop policy silence.**
Rev-4.1 non-stop filter loop retired with 11.H/I. Rev-5 replaces it with deterministic pre-commitment (11.N Step 1) + literature-grounded design (11.O). Correct, but unstated. **Fix:** one sentence in Phase-1.5.5 rationale: "under Rev-5, iteration-until-threshold is retired; iteration gating moves entirely to Rule 13 at 11.P."

**PM-P7 (LOW) — Tier-2 consumption-leg orphaned.**
Deferred work with no plan file, no memory marker, no owner. **Fix:** Execution-handoff note scheduling `docs/plans/YYYY-MM-DD-abrigo-consumption-leg.md` after 11.Q, OR commit `project_abrigo_consumption_leg_deferred.md`.

## 3. Dependency DAG

```
11.L ─────────────────────────────────┐
                                      │
11.M ──► 11.M.5 ──► 11.N ─────────────┴──► 11.O ──► 11.P ──► Phase-2b T12
                      │                                         ▲
                      └──────────► 11.Q ─────────────────────────┘
```

Parallelism: (11.L ∥ 11.M), (11.P ∥ 11.Q). Critical path: 11.M → M.5 → N → O → P → T12. 11.L gates 11.O dispatch only (not 11.M/N). 11.O Step-4 re-reads 11.L — requires 11.L landed.

## 4. Amendment Riders Needed

- **Goal / Architecture (line 18):** verify or rename `fx_vol_remittance_surprise/Colombia/` notebook dir.
- **Task 12:** seam → `CleanedInequalityPanelV1`.
- **Task 13:** RETIRE (aux-cols are remittance-specific); or rewrite with 11.O aux-col list.
- **Task 14:** RETIRE corridor-reconstruction.
- **Task 15:** assert `CleanedInequalityPanelV1` shape.
- **Phase 3 header + Tasks 16–24c:** rename "remittance-AR(1) surprise" → "X_d / Rev-2 spec primary X".
- **Task 27/28:** input spec is Rev-2 (11.O output).
- **Task 30a:** β̂_remittance → β̂_inequality; remittance→inequality artifact paths.
- **Spec-coverage self-check:** full rewrite per 11.O row-matrix; count → 54.

## 5. Risk Register

1. **Inherited-inconsistency trap (HIGH / HIGH).** Without PM-P1/P2, implementer at Task 12 reloads retired panel; wastes 10+ downstream tasks before Task-15 integration surfaces it. **Mitigation:** riders applied pre-dispatch + Phase-2b opening retirement banner.

2. **11.M stall (MEDIUM / HIGH).** Critical-path agent with no detection mechanism. **Mitigation:** PM-P4 timeout.

3. **Tier-2 consumption-leg indefinite defer (MEDIUM / MEDIUM).** Rev-5 gate test is single-leg asset-only — intermediate calibration, NOT full inequality-differential product thesis. Merging to `main` without tier-2 scheduled risks product narrative drifting to asset-carry-only. **Mitigation:** PM-P7 plan-file or memory-marker now.

---

**Summary (3 sentences).** Rev-5's new Phase-1.5.5 block (11.L–Q + 11.M.5) is internally coherent with correct pre-commitment and DuckDB migration hygiene, but two execution-blocking inherited-inconsistency defects remain: Phase 2b/3/4 tasks and the spec-coverage self-check still read as remittance-scoped, so an implementer reaching Task 12 reconstitutes the retired target. Rev-3.1-pattern amendment riders across Phases 2b/3/4 and a self-check rewrite are required before ACCEPT. Five QoL findings address M.5 naming, 11.M timeout, 11.O Step-4 cap, non-stop retirement clarification, and tier-2 governance.
