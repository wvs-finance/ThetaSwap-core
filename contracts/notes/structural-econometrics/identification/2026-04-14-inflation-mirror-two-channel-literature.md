# Tier 1 Literature Feasibility — {π, C_remittance} Deliverable

**Spec:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` (Rev 3)
**Plan:** `contracts/docs/superpowers/plans/2026-04-14-inflation-mirror-tier1-literature.md`
**Searcher:** <NAME / AGENT-ID — filled per task>
**Second reader:** JMSBPP (human, distinct from searcher — required per spec §14)
**Search start date:** 2026-04-14
**Search end date:** <YYYY-MM-DD>

## 1. Hypotheses

**Channel π (inflation):** Realized weekly vol of $\log P_{\text{cCOP}/X}$ responds to DANE Colombian CPI surprise with $\operatorname{adj-}R^2 \geq \tau_{\text{lit}} = 0.10$, in a regression with controls for US CPI surprise, BanRep policy-rate surprise, and VIX.

**Channel C_remittance:** Channel's natural observable (transfer-volume residual or flow-based LHS) responds to remittance-flow or income-cycle surprise at $\operatorname{adj-}R^2 \geq \tau_{\text{lit}} = 0.10$.

$\tau_{\text{op}} = 0.15$ (out-of-sample operational). $\tau_{\text{lit}} = 0.10$ (in-sample literature).

## 2. Findings — Channel π

(Filled during T3–T7. Per-citation rows with spec §10 handoff columns.)

| Citation | Sample start | Sample end | Country | Pair | Frequency | LHS | Surprise construction | Control set | Reported adj-R² | Tier (A/B/C/D) | Distance | Portability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 3. Cross-currency signal-strength — Channel π

Strength bucket: `strong` ≥ 0.25 / `moderate` 0.10–0.25 / `weak` < 0.10 / `none` = no citations.

| Counterparty | adj-R² | Sig | Tier | Citations | Strength | Notes |
|---|---|---|---|---|---|---|
| USD | NOT STUDIED | — | — | — | none | a priori: most-studied; US-rate confounds must be netted |
| EUR | NOT STUDIED | — | — | — | none | a priori: strips US-rate channel |
| DXY basket | NOT STUDIED | — | — | — | none | |
| MXN | NOT STUDIED | — | — | — | none | a priori: differencing isolates Colombia-specific |
| BRL | NOT STUDIED | — | — | — | none | |
| XAU | NOT STUDIED | — | — | — | none | a priori: inflation-hedge proxy, global |

## 4. Findings — Channel C_remittance

(Filled during T9–T13.)

| Citation | Sample start | Sample end | Country | Pair | Frequency | LHS | Surprise construction | Control set | Reported adj-R² | Tier (A/B/C/D) | Distance | Portability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 5. Cross-currency signal-strength — Channel C_remittance

| Counterparty | adj-R² | Sig | Tier | Citations | Strength | Notes |
|---|---|---|---|---|---|---|
| USD | NOT STUDIED | — | — | — | none | |
| EUR | NOT STUDIED | — | — | — | none | |
| DXY basket | NOT STUDIED | — | — | — | none | |
| MXN | NOT STUDIED | — | — | — | none | |
| BRL | NOT STUDIED | — | — | — | none | |
| XAU | NOT STUDIED | — | — | — | none | |

## 6. Per-channel verdicts

**Channel π:** `<LABEL>` — `<payload per spec §9>` — `<rationale>` — `<citation list>`

**Channel C_remittance:** `<LABEL>` — `<payload>` — `<rationale>` — `<citation list>`

## 7. Global roll-up

`<GLOBAL LABEL>` — `<payload>` — `<rationale>`

## 8. Gap analysis

Unaddressed questions, close-enough-to-cite, missing.

## 9. Sources consulted

| Source | Channel | Queries tried | Hits | Blocked (why) |
|---|---|---|---|---|

## 10. Confidence level and unresolved leads

Per-channel qualitative confidence (low/medium/high) and leads unresolved at hard-cap.

## 11. Second-reader sign-off

- [ ] Second reader spot-checked ≥ 3 citations' tier assignments.
- [ ] Second reader confirmed no `[CITATION-TODO]` markers remain in spec §18.
- [ ] Second reader confirmed verdicts map correctly via spec §9 decision tree.

Signed: `<NAME>`   Date: `<YYYY-MM-DD>`
