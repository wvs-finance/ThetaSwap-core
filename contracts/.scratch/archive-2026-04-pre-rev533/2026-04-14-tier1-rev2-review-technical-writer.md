# Technical Writer Rev 2 Review — Tier 1 Feasibility Filter Spec

**Spec under review (Rev 2):** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
**Rev 1 review:** `contracts/.scratch/2026-04-14-tier1-review-technical-writer.md`
**Review date:** 2026-04-14
**Scope:** Verify Rev 1 BLOCK fixes; 11 fresh angles.

---

## OVERALL VERDICT: APPROVE_WITH_MINOR_CHANGES

All three Rev 1 BLOCKs are substantively resolved. Rev 2 expands scope (two channels), adds a glossary, normalizes verdict labels, and ships a References section. It is now executable by a cold reader with domain context.

Four residual issues are `FLAG` (global-roll-up label format drift, three undefined terms still in use, `[citation to confirm]` placeholder weak, tier-assignment procedural ambiguity). Remaining items are `NIT`. No BLOCK.

---

## Verification of Rev 1 BLOCKs

### BLOCK 7.1 — Strength column unit — **FIXED**

§7 now specifies cell format `adj-R² | significance | tier | citation(s)` and a separate `Strength bucket` column with explicit thresholds (strong ≥ 0.25 ✦ / moderate 0.10–0.25 ✧ / weak < 0.10 ✧· / none `NOT STUDIED`). Unit is sensible: adj-R² is the correct operationalization given §1's definition. Buckets align with $\tau_{\text{op}} = 0.15$ and $\tau_{\text{lit}} = 0.10$. Resolved.

Residual: the four-field `|`-separated cell string (§8 line 118) is dense and hard to grep for a single field (see Fresh #9).

### BLOCK 9.1 — Verdict labels inconsistent — **FIXED (per-channel); PARTIAL (global)**

Per-channel labels are now clean `UPPER_SNAKE_CASE` with separated payload lines (`CONFIRMED`, `CONFIRMED_NO_INFRASTRUCTURE`, `PARTIAL_SUPPORT`, `DISCONFIRMED`, `NO_LITERATURE_SUPPORT`). Grep-friendly. Useable as-is.

Global roll-up labels (§11) reintroduce the exact format drift Rev 1 flagged — see Fresh #6.

### BLOCK X.1 — References section absent — **FIXED (with caveat)**

§20 exists with seed citations. Resolved structurally.

Caveat: 8 of 14 entries carry `[citation to confirm]`. This is honest but the marker is easy to miss in prose — see Fresh #10.

---

## Fresh Angles

### #1 — Glossary completeness

§0 defines RAN, $U_{\text{RAN}}$, $L$, $g^{\text{pool}}$, $g^{\text{pool}}(i)$, $\phi$, $V(P)$, LVR, ERPT, Angstrom, Panoptic, Mento vAMM, differential-form $U_{\text{RAN}}$. Strong coverage.

**`FLAG` — three load-bearing terms still unglossed:**
- **"unit of account"** — not used in Rev 2 text (previously §1); not an issue now, withdraw.
- **"confound density"** — §11 decision tree line 177 uses it as a tie-break criterion; never defined. What does the searcher measure? Number of omitted controls? Overlap with other macro releases in the event window? Load-bearing because it's a deterministic tie-break.
- **"infra_block"** — §11 payload `infra_block=<cCOP_side|X_side|both>`. Inferrable but not defined.
- **"specification-distance"** — §11 line 179 ("specification-distance flagged beyond Tier D"). Term is distinct from tier name; is it the same as "farther than Tier D" in §7 line 112, or a separate dimension?

**Change:** Add three entries to §0.

### #2 — Revision history informativeness

§Revision history (lines 7–9) is load-bearing, not self-congratulatory. It enumerates Rev 2 changes (expanded scope, proxy tiers, thresholds, joint gate, DISCONFIRMED, pivot protocol, labels, outcome criterion, References) and references the Rev 1 review count ("8 BLOCK items"). A cold reader can reconstruct what changed.

**`NIT`:** "8 BLOCK items" overstates — Rev 1 tallied 3 BLOCK, 9 FLAG, 16 NIT. Either say "8 top-priority items" or cite the actual 3 BLOCK + 5 FLAG it addressed.

### #3 — Verdict taxonomy over-engineering

Five per-channel labels + four global = nine. For a **feasibility filter** whose job is gate-open / gate-closed / pivot, this is close to the edge.

Defense of five per-channel: `DISCONFIRMED` vs `NO_LITERATURE_SUPPORT` is a real distinction (negative evidence vs no evidence) and drives different downstream routes (`RETIRE_THESIS` vs `PIVOT_NEEDED`). `CONFIRMED` vs `CONFIRMED_NO_INFRASTRUCTURE` is a real distinction (Tier 2 vs separate infra spec). `PARTIAL_SUPPORT` is the catch-all. Cutting to three (CONFIRMED / PARTIAL / NONE) collapses the DISCONFIRMED → RETIRE_THESIS route that §11 explicitly wants. Five is defensible.

`MIXED_GLOBAL` is the weakest global label — it's "fallback to manual routing," and the current §11 decision tree at the global layer covers only 3 of 2⁵ = 32 per-channel label pairs explicitly. Most realistic combinations fall through to `MIXED_GLOBAL`.

**`NIT`:** Consider dropping `MIXED_GLOBAL` and making the global roll-up a function over the per-channel labels with a precedence table (confirmed > partial > disconfirmed > gap). As written it is not over-engineered, but the global layer is under-specified while the per-channel layer is precise.

### #4 — Tier A/B/C/D determinism

§7 classifies papers against four axes: LHS (realized-vol?), RHS (channel-specific surprise?), control count (≥3 of 4?), currency match (COP/cCOP? regional peer? non-COP EM?).

**`FLAG` — tier assignment requires full-text judgment, not abstract-level.** A paper's abstract rarely reports control count or surprise construction method. The pre-registered tier hierarchy is sound as a *classification rubric*, but "pre-registered" implies reproducibility; two searchers given the same paper will agree on Tier A/D but disagree at Tier B vs C boundary (does a single COP paper with 2 controls belong in B-with-demerit or C?).

**Change:** Either (a) add a tiebreak rule (e.g., "if controls count is the only shortfall, downgrade by one tier"), or (b) weaken the "pre-registered" claim to "searcher-classified against a pre-registered rubric; ambiguous cases resolved by second-reader in §18(f)."

### #5 — Inline thresholds markedness

§10 inline values: **$50,000** and **$5,000** USD-equivalent; **1% slippage**; **30-day average**.

Rationale for $50,000 is present and load-bearing-looking ("a 1% daily move produces < $500 of bid-cost, economically indistinguishable from noise under typical Angstrom bid discretization"). $5,000 has no rationale inline. The 1% and 30-day choices have no rationale.

**`FLAG` — thresholds do not visually signal tunability.** A reader may read them as final, the way $\tau_{\text{op}} = 0.15$ and $\tau_{\text{lit}} = 0.10$ are final. But these are operational knobs, not pre-registered econometric bars; a Rev 3 may want to tighten them as on-chain conditions evolve.

**Change:** Add one sentence to §10: "Thresholds (b), (c), and the 1% / 30-day windows are operational and revisable in a sibling spec; $\tau_{\text{op}}$ and $\tau_{\text{lit}}$ are pre-registered bars and revisions require a Rev 3 of this spec." Also give $5,000 and 1% / 30-day their one-line rationales.

### #6 — Global roll-up label grepability

Rev 1 BLOCKed on per-channel label inconsistency. Rev 2 fixed it there. §11 global labels: `PROCEED_WITH(μ*, X*)`, `PIVOT_NEEDED`, `RETIRE_THESIS`, `MIXED_GLOBAL`.

**`FLAG` — same grepability issue, different layer.** `PROCEED_WITH(μ*, X*)` carries payload inline parens, the other three are bare. A searcher running `grep -E '^(PROCEED_WITH|PIVOT_NEEDED|...)' deliverable.md` will miss `PROCEED_WITH` if the payload wraps. Also: `PIVOT_NEEDED` and `MIXED_GLOBAL` have no payload field, which is inconsistent with `RETIRE_THESIS` (which could legitimately carry `channels_retired=π,C_rem`).

**Change:** Apply the same per-channel treatment at the global layer. Bare label on one line, `payload:` line below:
```
PROCEED_WITH
  payload: mu=π target_counterparty=USDT tier=B
```

### #7 — New undefined acronyms

User flagged DTF, TES, GFCF, ToT, OIS. Searching the spec:
- **DTF, TES, GFCF, ToT, OIS** — none present in Rev 2. No new acronym debt introduced.
- **TRM** (line 47) — Tasa Representativa del Mercado; the COP/USD reference rate. Unglossed. Domain-obvious to Colombian-macro readers but not to Angstrom engineers.
- **IDB** (line 102) — Inter-American Development Bank. Unglossed.
- **VIX** (§7 line 108) — CBOE Volatility Index. Unglossed; near-universal but worth one line.
- **AR residual, GARCH** (§12, §6) — standard econometric terms; acceptable.
- **HITL** (§17, §19) — Human-In-The-Loop. Unglossed.
- **quincena, prima** (§2 line 47) — Colombian semi-monthly payday and year-end bonus cycles. Unglossed; load-bearing because they appear in §6 query set and §12 as surprise-construction candidates.

**`FLAG`:** Add TRM, HITL, quincena, prima to §0. VIX and IDB are optional.

### #8 — Deliverable §13 section 7 "merged" clarity

Line 216: "Verdict and gap analysis, merged into one section to force reconciliation."

A reader familiar with Rev 1 knows what this means (Rev 1 had separate verdict and gap sections; Rev 2 forced merger so verdict and its caveats travel together). A cold reader sees "merged" and asks "merged from what?"

**`NIT`:** Rewrite as: "Per-channel verdict, rationale, and gap analysis in one section per channel (no separate gap section — caveats must accompany the verdict that carries them)."

### #9 — §8 cell format grepability

Format: `adj-R² | significance | tier | citation(s)` in one cell (e.g., `0.18 * B Rincón 2019`).

**`FLAG` — grepping for tier alone is painful.** A filter like "show all Tier A findings" requires regex against position-in-cell, which is brittle. Either (a) split to separate columns, or (b) use key=value in the cell (e.g., `adj_R2=0.18 sig=* tier=B cite=Rincón_2019`).

Separate columns is marginally better for table width in the deliverable template; the template has 4 columns now and could have 7 without becoming unreadable.

**Change:** Split §8 column 2 into four columns: `adj-R²`, `significance`, `tier`, `citation`. Keep `Strength bucket` and `Notes` as-is.

### #10 — `[citation to confirm]` visibility

§20 uses `[citation to confirm]` as a placeholder on 8 of 14 entries.

**`FLAG` — visibility is weak.** `[citation to confirm]` reads like prose in a bulleted list and does not stand out. Three searchers in a row could miss it. Common failure modes:
- Reader assumes "Rincón-Castro. Borradores de Economía" is the citation and searches for those exact words.
- Reviewer signs off without noticing half the bibliography is unresolved.

**Change:** Flag with a prominent marker. Options:
- Prefix: `TODO[searcher]: Rincón-Castro…`
- All-caps sentinel: `**[CITATION-TODO]** Rincón-Castro…`
- Table format with a "Status" column: `draft | confirmed | paywalled`.

Also: §18 success criterion should require "no `[citation to confirm]` remaining in deliverable §20."

### #11 — Cold-reader stumbles

- **Line 33** — `$\operatorname{adj-}R^2_{\beta_{\mu}}$` notation. The subscript $\beta_\mu$ suggests "adj-R² of the coefficient on $\mu$," which is non-standard (adj-R² is a regression-level statistic, not coefficient-level). A reader will pause. Likely means "adj-R² in the regression whose regressor of interest is $\beta_\mu$" — worth a one-line clarification.
- **§2 line 43** — three file paths in one breath, all under `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/`. Acceptable because §2 ends with "copied to `contracts/.scratch/` on Tier 1 execution start," but a cold reader doesn't know this on first pass. Consider forward-reference to §13 supporting-artifacts line.
- **§11 line 191** — "The pivot you triggered in Rev 2" — direct second-person address to the user. Fine as authorial voice but unusual in a spec. Non-blocking.
- **§15 line 241** — "No scope expansion to channels $\mu(I)$, $\mu(XN)$, $\mu(S)$" — $\mu(S)$ is the rejected Mento-savings channel per §2 Finding 2. Listing it as a non-goal alongside unvisited channels (I, XN) conflates "rejected" with "deferred." Small inconsistency.
- **§17 Risks** — "spec uses inline LaTeX; render with MathJax/KaTeX. GitHub preview shows raw." Useful, but belongs near the top of the spec (after Revision history) so the reader picks the right renderer *before* reading.

---

## Summary Table

| # | Severity | Location | Issue |
|---|---|---|---|
| BLOCK-7.1 | FIXED | §7 | Strength column now has adj-R² + bucket |
| BLOCK-9.1 | FIXED (per-channel); FLAG (global) | §11 | Global roll-up labels drift in format |
| BLOCK-X.1 | FIXED | §20 | References section exists; placeholders flagged below |
| F1 | FLAG | §0 | "confound density", "infra_block", "specification-distance" unglossed |
| F2 | NIT | Revision history | "8 BLOCK" mis-counts Rev 1 tally |
| F3 | NIT | §11 global | `MIXED_GLOBAL` is under-specified catch-all |
| F4 | FLAG | §7 | Tier assignment requires full-text judgment, weakening "pre-registered" |
| F5 | FLAG | §10 | Operational thresholds unmarked as tunable; $5,000 and 1%/30d unrationaled |
| F6 | FLAG | §11 | Global labels same grepability issue as Rev 1 per-channel labels |
| F7 | FLAG | §0 | TRM, HITL, quincena, prima unglossed |
| F8 | NIT | §13 | "merged into one section" semantically underspecified for cold reader |
| F9 | FLAG | §8 | Four-field `|`-separated cell is not greppable per-field |
| F10 | FLAG | §20 | `[citation to confirm]` placeholder insufficiently visible |
| F11a | NIT | §1 | $\operatorname{adj-}R^2_{\beta_\mu}$ notation non-standard |
| F11b | NIT | §15 | $\mu(S)$ listed as deferred but is actually rejected |
| F11c | NIT | §17 | Renderer note belongs near top, not in Risks |

**Totals:** 0 BLOCK, 7 FLAG, 6 NIT.

---

## Recommended Minimum Edits Before Execution

1. **§0 Glossary:** add `confound density`, `infra_block`, `specification-distance`, `TRM`, `HITL`, `quincena`, `prima`. (F1, F7)
2. **§8 table:** split the four-field cell into four columns (`adj-R²`, `significance`, `tier`, `citation`). (F9, BLOCK-7.1 residual)
3. **§11 global labels:** apply same bare-label-plus-payload treatment as per-channel; drop `MIXED_GLOBAL` or promote it to a precedence function. (F6, F3)
4. **§20:** change `[citation to confirm]` to `**[CITATION-TODO]**` or add a Status column; add §18 criterion "no CITATION-TODO remaining." (F10)
5. **§10:** mark thresholds (b), (c), 1%, 30d as operational/tunable vs $\tau$ pre-registered. (F5)

Rev 3 not required for these; apply inline and execute.
