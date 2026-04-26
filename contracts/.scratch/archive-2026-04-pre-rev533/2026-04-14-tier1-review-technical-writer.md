# Technical Writer Review — Tier 1 Feasibility Filter Spec

**Spec under review:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
**Review date:** 2026-04-14
**Reviewer role:** Technical Writer (clarity, structure, completeness, internal consistency)
**Out of scope for this review:** whether the econometric methodology or feasibility logic is correct.

---

## OVERALL VERDICT: APPROVE_WITH_CHANGES

The spec is well-organized, internally coherent, and written in disciplined prose. A reader with domain context (econometrics, DeFi, the RAN thesis) can pick it up and execute it. However, it fails the "stands alone or links to prerequisites explicitly" test for a reader arriving cold — several load-bearing terms are undefined, one table has an under-specified column that will produce inconsistent fills, and the four verdict labels use inconsistent naming that will create confusion when grepped or referenced downstream.

Three issues are `BLOCK` for a cold reader because they make the spec literally unexecutable-as-written (ambiguous fill unit in §7, mismatched verdict labels in §9, absent References section despite heavy name-dropping). The rest are `FLAG` / `NIT`.

---

## Issue Inventory

### Section 1 — Context

**Issue 1.1 — `FLAG` — Undefined core variables**
The first paragraph introduces $U_{\text{RAN}}$, $L$, $g^{\text{pool}}$, $g^{\text{pool}}(i)$ with no gloss. Since §2 then casually asserts "$g^{\text{pool}}$ is approximately $\phi^2 V(P)/(8L)$," the reader is expected to follow an algebraic identity before any symbol has been named.
**Change:** Add a one-line glossary after the first paragraph.

**Issue 1.2 — `FLAG` — "Differential construction" used as a noun with no referent**
Appears in §1 and §12, never defined.
**Change:** Add a parenthetical gloss or cite the brainstorming artifact by path.

**Issue 1.3 — `NIT` — LVR acronym not expanded**
First use → "integrated realized LVR (Loss-Versus-Rebalancing) series".

**Issue 1.4 — `NIT` — Angstrom / Panoptic not introduced**

---

### Section 2 — Why a literature-first Tier 1

**Issue 2.1 — `FLAG` — Factual assertions with no citation hook**
"25 years of inflation-targeting data under BanRep" and "pass-through literature is mature" asserted without citation.

**Issue 2.2 — `NIT` — ERPT not expanded at first use (§4)**

**Issue 2.3 — `NIT` — Mento vAMM inconsistent naming**

---

### Section 3 — Objective

**Issue 3.1 — `NIT` — Threshold inconsistency signal**
$\tau = 0.15$ (§1) vs $\geq 0.10$ (§3, §9). Surface both once as $\tau_{\text{op}}$ and $\tau_{\text{lit}}$.

---

### Section 5 — Sources and search order

**Issue 5.1 — `NIT` — URL asymmetry**
BanRep has a URL; no other source does.

---

### Section 7 — Cross-currency signal-strength table — **BLOCKING**

**Issue 7.1 — `BLOCK` — "Literature $\beta_{\text{CPI}_{\text{COL}}}$ strength" column is under-specified**
Fill unit is ambiguous. Two researchers will fill it differently.
**Change:** Split into two columns: `Reported adj-R² (or closest analog)` + `Qualitative strength (strong ≥ 0.25 / moderate 0.10–0.25 / weak < 0.10 / none)`.

**Issue 7.2 — `FLAG` — `NOT STUDIED` vs empty dash confusion**

**Issue 7.3 — `NIT` — "Rationale from literature" column misnamed**
The stubs are *a priori* rationale, not literature findings.

---

### Section 8 — On-chain X availability matrix

**Issue 8.1 — `FLAG` — `△` symbol unexplained**
**Change:** Legend: "`✓` deep, `△` thin/partial (simulation-usable, not live-deployable), `✗` no usable wrapper".

**Issue 8.2 — `NIT` — "etc." in table row**

**Issue 8.3 — `NIT` — Date provenance imprecise**
"as of 2026-04" → "per 2026-04-02 audit".

---

### Section 9 — Verdict rules — **BLOCKING**

**Issue 9.1 — `BLOCK` — Verdict labels inconsistent and ungreppable**
`CONFIRMED_WITH_X=<token>`, `CONFIRMED_WITHOUT_X`, `GAP`, `MIXED` — mixed prefix + payload conflation.
**Change:** Normalize:
- `CONFIRMED` + field `target_counterparty=<token>`
- `CONFIRMED_NO_INFRASTRUCTURE` + field `target_counterparty=<token>`
- `NO_LITERATURE_SUPPORT` (was `GAP`)
- `PARTIAL_SUPPORT` + field `which_dimension=<level|vol|basket>` (was `MIXED`)

**Issue 9.2 — `FLAG` — Multiple-counterparty tie case unhandled**
**Change:** Tie-break: rank by (1) highest adj-$R^2$, (2) deepest on-chain liquidity, (3) lowest confound density.

**Issue 9.3 — `FLAG` — `MIXED` conflates two sub-cases**
"level-not-vol" vs "basket-not-isolated" need different Tier 1b scopings.

---

### Section 10 — Deliverable

**Issue 10.1 — `NIT` — Deliverable sub-section 2 is paragraph-as-table**
Render as a skeleton table.

**Issue 10.2 — `NIT` — Deliverable path may not exist**
Add: "Create `contracts/notes/structural-econometrics/identification/` if it does not exist."

---

### Section 12 — Non-goals

**Issue 12.1 — `NIT` — "memory-reinforced" opaque to cold reader**

**Issue 12.2 — `NIT` — Redundancy with §4 "Out"**

---

### Section 13 — Dependencies & prerequisites

**Issue 13.1 — `NIT` — "neighboring repo" is anonymous**
**Change:** "The 2026-04-02 prior research lives at `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/` (read-only)."

---

### Section 15 — Success criterion

**Issue 15.1 — `FLAG` — Criterion is structural, not semantic**
All bullets are "have you done X?" — none are "is the verdict well-grounded?". A researcher could tick every box and deliver a verdict supported by one weak paper.
**Change:** Add: "The verdict is supported by either (a) at least one citation with adj-R² ≥ 0.10 on the specification closest to the hypothesis, or (b) an explicit negative statement 'no such citation found after exhaustive search per §5 and §6,' signed by the searcher."

**Issue 15.2 — `NIT` — Section ordering**
Proposed re-order: §10 Deliverable → §15 Success criterion → §11 Integration → §12 Non-goals → §13 Dependencies → §14 Time → §16 Risks.

---

## Cross-cutting Issues

**Issue X.1 — `BLOCK` — No References section despite 8+ name-drops**
Add §17 References with seed citations for Rincón-Castro, González-Gómez, Hamann-Salcedo, Andersen-Bollerslev-Diebold-Vega 2003, Cai-Joutz, Lahaye-Laurent-Neely, Choudhri-Hakura, Ca'Zorzi-Hahn-Sánchez.

**Issue X.2 — `NIT` — No anchor cross-links**

**Issue X.3 — `NIT` — LaTeX rendering target unstated**

---

## Summary Table

| ID | Severity | Section | Issue |
|---|---|---|---|
| 1.1 | FLAG | §1 | Undefined symbols $U_{\text{RAN}}$, $L$, $g^{\text{pool}}$ |
| 1.2 | FLAG | §1 | "Differential construction" has no referent |
| 1.3 | NIT | §1 | LVR not expanded |
| 1.4 | NIT | §1 | Angstrom / Panoptic not introduced |
| 2.1 | FLAG | §2 | Uncited factual claims |
| 2.2 | NIT | §4 | ERPT not expanded at first use |
| 2.3 | NIT | §2 | Mento vAMM inconsistent naming |
| 3.1 | NIT | §3 | Threshold inconsistency (τ_op vs τ_lit) |
| 5.1 | NIT | §5 | URL asymmetry |
| **7.1** | **BLOCK** | **§7** | **Strength column has no unit** |
| 7.2 | FLAG | §7 | `NOT STUDIED` vs `—` confusion |
| 7.3 | NIT | §7 | "Rationale from literature" column misnamed |
| 8.1 | FLAG | §8 | `△` symbol not legended |
| 8.2 | NIT | §8 | "etc." in table row |
| 8.3 | NIT | §8 | Date provenance imprecise |
| **9.1** | **BLOCK** | **§9** | **Verdict labels inconsistent** |
| 9.2 | FLAG | §9 | Multi-counterparty tie unhandled |
| 9.3 | FLAG | §9 | MIXED conflates two sub-cases |
| 10.1 | NIT | §10 | Deliverable column list as prose |
| 10.2 | NIT | §10 | Deliverable path may not exist |
| 12.1 | NIT | §12 | "memory-reinforced" opaque |
| 12.2 | NIT | §12 | Redundancy with §4 |
| 13.1 | NIT | §13 | "Neighboring repo" not pathed |
| 15.1 | FLAG | §15 | Success criterion structural, not semantic |
| 15.2 | NIT | §§10–16 | Section ordering could improve |
| **X.1** | **BLOCK** | cross | **No References section** |
| X.2 | NIT | cross | No anchor links |
| X.3 | NIT | cross | LaTeX rendering target unstated |

**Totals:** 3 BLOCK, 9 FLAG, 16 NIT.

---

## Recommended Minimum Edits Before Execution

1. **§7:** Split the strength column or add a legend footnote defining the unit.
2. **§9:** Normalize the four verdict labels to consistent bare `UPPER_SNAKE_CASE`; separate payload from label.
3. **Cross:** Add a §17 References section with seed citations for all eight named authors.
