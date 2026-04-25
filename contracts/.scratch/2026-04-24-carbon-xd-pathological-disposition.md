# Carbon-Basket X_d — Pathological-HALT Disposition Memo

**Date:** 2026-04-25T10:26Z (filed by Task 11.N.2c)
**Plan reference:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2c Step 5 + Recovery Protocols Case 2 (lines 1080-1083).
**Design doc:** `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §4 row 4 ("structurally pathological" branch).
**Companion memo:** `contracts/.scratch/2026-04-25-carbon-basket-calibration-result.md` (per-currency stats + PCA diagnostic).

---

## 1. The verdict

**Pathological-HALT.** The basket-aggregate `carbon_basket_user_volume_usd` series has **77 weekly non-zero observations** across the 82-Friday panel (2024-08-30 → 2026-04-03). The pre-committed gate is **N_MIN = 80**. The shortfall is **3 weeks**.

Per design doc §4 row 4 + plan §1015 + plan §1082, the calibration **does NOT silently set arb-only as primary** — that would conflate stress-detection (`carbon_basket_arb_volume_usd`) with capital-flow magnitude (the user-only X_d the design doc commits to). Instead the calibration raises `CalibrationStructurallyPathological`, this disposition memo is filed, and the user decides next-step pivot.

---

## 2. Why the gate fired

| measure | value |
|---|---|
| Panel coverage | 82 Fridays (2024-08-30 → 2026-04-03) |
| Active currencies (≥ 30 non-zero weeks each) | EURm (41), BRLm (44), KESm (30), COPM (47) |
| Sparse currencies | USDm (2 weeks), XOFm (0 weeks) |
| **Basket-aggregate non-zero weeks** | **77** |
| **Pre-committed N_MIN** | **80** |
| Shortfall | 3 weeks |

The 5 zero-volume basket-weeks are **not seasonal artefacts** — they reflect periods when none of the six Mento stablecoins crossed the basket boundary in user-initiated trades. The Carbon DeFi protocol's overall event volume is 2.23M (gate memo §2.2), but the user-only filter restricted to the basket boundary lands 123,511 events (corrigendum §4) — sufficient to populate most weeks but not all 80.

This is not a data-pipeline regression. The 11.N.2b.2 ingestion is byte-exact against the Dune query `7372282` execution `01KQ1ZZGYYMFKADNZDB8Z4ECDY` (provenance: `contracts/data/carbon_celo/README.md`). The shortfall is **structural**.

---

## 3. Anti-fishing posture

The pre-committed thresholds are **not relaxed** in response to the shortfall:

- `N_MIN = 80` stays at 80 (not reduced to 77 to re-enter PASS branch).
- `MDES_SD = 0.40` stays at 0.40 (not relaxed to 0.50 to recover power).
- `POWER_MIN = 0.80` stays at 0.80 (Rev-4 standard).
- `MDES_FORMULATION_HASH` integrity check passes; the pinned Cohen f² formulation is unmodified.

Per the §0.3 anti-fishing guard ("Modification of `MDES_SD` or `N_MIN` after Step 0 commits requires (a) full design-doc revision; (b) CORRECTIONS block in the next plan revision; (c) full 3-way review cycle"), this memo does **not** propose threshold relaxation. The Carbon-basket X_d thesis is empirically failing at the basket-wide level, and the architecture's anti-fishing guarantee (design doc §1) requires HALT, not retroactive threshold tuning.

---

## 4. Decision options for the user

Per plan §1065 + Recovery Protocol Case 2:

### (a) Abandon the X_d source

Drop the Carbon-basket X_d thesis entirely. Phase-A.0 brainstorm options α/β/γ remain on the table; revisit the `project_colombia_yx_matrix` per-Y triangulation and select a different cell. This is the most extreme pivot.

### (b) Pivot to a completely different X

Resume Phase-A.0 brainstorm-α/β/γ. The user's prior memos
(`project_phase_a0_remittance_execution_state`, `project_phase_a0_exit_verdict`,
`project_abrigo_inequality_hedge_thesis`) catalogued multiple candidate X_d
cells; pick a different one and re-enter the X_d-design pipeline at the
specs/plan stage.

### (c) Drop the Mento↔global boundary constraint and re-formulate

Loosen the boundary filter from "Mento↔global" to e.g. "any basket touch" or
"any Carbon DeFi event involving a Mento stablecoin". This relaxation would
expand the candidate event population from 175,005 to ≈ 1M+ events
(per gate memo §2.2 cardinalities), almost certainly clearing N_MIN. **However**,
this changes the X_d definition mid-stream, which is **anti-fishing-banned**
per design doc §1 ("Once primary X_d is chosen, downstream tasks consume it
without re-selection; mid-stream re-tuning of the primary measure is banned").
The relaxation would require a new design-doc revision + new 3-way review
cycle before adoption — i.e., it's pivot (b) restated.

### (d) Extend the panel into the future

Wait. The 82-Friday panel ends 2026-04-03; the current date is 2026-04-25. Three
additional Fridays (2026-04-10, 2026-04-17, 2026-04-24) have already accumulated.
Re-running the 11.N.2b.2 ingestion at a later date might bring the basket-
aggregate non-zero count above 80 organically. **However**, this is a thin
margin — even with three new weeks the result depends on whether each new
week has at least one basket-boundary user trade. Forecasting Carbon protocol
activity from 2026-04-04 onward is itself speculative.

A **principled variant** of (d) is to re-run 11.N.2c on a re-ingested panel
(say) 90 days from now, accepting the resulting verdict at that time. This
preserves the anti-fishing guard (the gate fires the same way against the same
threshold; only the data window has expanded) — but parallel work cannot
proceed in the interim.

### (e) Pivot to a different Y while keeping X_d in the diagnostic-only role

The Y₃ inequality-differential design (`contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md`) was authored on the assumption that Carbon-basket X_d would clear calibration and pair cleanly with regional pan-EM Y₃. If the X_d direction is abandoned but the Y₃ panel is still scientifically useful, Tasks 11.N.2d / 11.N.2d.1 could still be executed against an alternative X (option b) — preserving the Y₃ work-product even if the Carbon X dies.

---

## 5. Recommendation (no auto-action)

The orchestrator does **not** auto-select an option. Per plan §1065, the user
decides. The structured payload from `CalibrationStructurallyPathological`
is recorded here so any pickup agent can reconstruct the verdict without
re-running the calibration.

In the absence of user input, the next agent picking up the thread should:

1. Read this memo + the companion calibration-result memo.
2. NOT proceed to Task 11.N.2d (Y₃ panel construction) — Task 11.N.2d's plan §1158 DAG explicitly blocks on Task 11.N.2c's PASS verdict.
3. NOT silently set arb-only as primary — even though `carbon_basket_arb_volume_usd` has 45 non-zero weeks (still under N_MIN=80) and a different semantic interpretation (stress-detection vs capital-flow magnitude).
4. Open a fresh /superpowers:brainstorming session with the user to triage options (a)-(e) above.

---

## 6. Provenance integrity

| guard | value |
|---|---|
| Rev-4 `decision_hash` | `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` (byte-exact preserved) |
| `MDES_FORMULATION_HASH` | `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (live SHA256 of `required_power` source matches) |
| Canonical DB checksum | unchanged (calibration is READ-only) |
| 11.N.2b.2 row counts | 8 carbon `proxy_kind` series × 82 weeks each; byte-exact preserved |

---

## 7. References

- Plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2c Step 5 + Recovery Protocols
- Design doc: `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` §4 row 4
- Calibration result: `contracts/.scratch/2026-04-25-carbon-basket-calibration-result.md`
- Gate memo: `contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md`
- Corrigendum: `contracts/.scratch/2026-04-25-carbon-basket-gate-memo-corrigendum.md`
- Pre-aggregation provenance: `contracts/data/carbon_celo/README.md`

— end of disposition memo —
