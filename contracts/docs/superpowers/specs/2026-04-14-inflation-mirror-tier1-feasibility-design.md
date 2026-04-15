# Tier 1 Literature Feasibility — $\{\pi, C_{\text{remittance}}\}$ Channel Screening

**Status:** Rev 3 (scope-shrunk to literature-only after Rev 2 review)
**Date:** 2026-04-14
**Scope:** Desk literature survey. No regression, no data pull, no code, no on-chain queries, no Solidity, no infrastructure availability check. Infrastructure readiness is a separate sibling spec (TBD; see §12).

**Revision history:**
- Rev 1 (2026-04-14): $\mu(\pi)$-only; reviewed → 8 BLOCKs.
- Rev 2 (2026-04-14): scope expanded to $\{\pi, C_{\text{remittance}}\}$ after research rejected the Mento-savings hypothesis; added §10 operational thresholds, joint cCOP × X gate, `DISCONFIRMED` verdict, normalized labels. Reviewed again.
- Rev 3 (2026-04-14): Rev 2's §10 thresholds combined with §2's own evidence (cCOP peaks ~$7K/day) made the feasibility filter structurally pre-determined — every row pre-failed the $50K/30d cCOP-side gate, collapsing the verdict to `CONFIRMED_NO_INFRASTRUCTURE` regardless of what the literature said. Rev 3 resolves by narrowing Tier 1 to the literature question only; infrastructure availability moves to a sibling spec. Also fixes: Tier-D gaming hole (§9 Step 2 tier gate), paywall-downgrade rule (§10), global-verdict label normalization (§9), named human second reader (§16), expanded glossary, time estimate corrected for 2-channel scope.

---

## 0. Glossary

Symbols and terms used load-bearing across the spec:

- **RAN** — Range Accrual Note. See `contracts/notebooks/ranPricing.ipynb` §Instrument.
- **$U_{\text{RAN}}$** — the RAN's underlying; notebook §Implementation defines it as $\Phi(A(L) \cdot f_n(g^{\text{pool}}(i)) / f_d(g^{\text{pool}}))$.
- **$L, g^{\text{pool}}, g^{\text{pool}}(i)$** — pool liquidity, pool-wide growth accumulator, per-tick growth. Notebook §Observables.
- **$\phi$** — effective Angstrom auction cost bound.
- **$V(P)$** — realized price-variance term in the CPMM LVR identity.
- **LVR** — Loss-Versus-Rebalancing (Milionis, Moallemi, Roughgarden 2022).
- **ERPT** — exchange-rate pass-through.
- **TRM** — Tasa Representativa del Mercado (Colombian official daily COP/USD interbank reference rate).
- **DTF** — Depósito a Término Fijo (Colombian term-deposit reference rate; savings-rate proxy).
- **TES** — Títulos de Tesorería (Colombian sovereign bonds; yield is a policy-rate proxy).
- **DANE** — Departamento Administrativo Nacional de Estadística (Colombian statistics agency; CPI publisher).
- **BanRep** — Banco de la República (Colombian central bank).
- **Quincena** — Colombian mandatory dual payday (15th and last day of month); income-cycle proxy.
- **Prima de servicios** — legally-mandated employer bonus, June 30 and December 20; one month's salary.
- **Angstrom** — hybrid AMM/orderbook on Ethereum L1; bid auction produces $g^{\text{pool}}$.
- **Panoptic** — perpetual-options protocol; Tier 2 tokenization layer. Out of scope here.
- **HITL** — human-in-the-loop; for paywalled-paper retrieval where automated access fails.
- **Differential-form $U_{\text{RAN}}$** — $\Phi$-squashed difference between tail-range and target-range growth; from notebook §Tailoring.
- **Proxy tier (A/B/C/D)** — classification of how close a literature citation is to the operational hypothesis. §7.
- **Confound density** — number of omitted variables in a paper's specification that could independently drive the LHS; used as a verdict tie-break in §9.
- **Specification-distance** — qualitative distance between a paper's regression and the operational hypothesis (LHS, RHS construction, control set, frequency); collapses into the tier assignment.

## 1. Context

The `ranPricing.ipynb` notebook proposes a RAN whose underlying reads from pool observables. The §Applications cell frames the use case as a CES basket $Y = ((X/\mu(C))^{\eta_C} + (X/\mu(I))^{\eta_I} + (X/\mu(S))^{\eta_S} + X/\mu(\pi) + (X/\mu(XN))^{\eta_{XN}})^{1/\eta}$ over five macro factors. The statistical operationalization of "$X$ mirrors channel $\mu$" agreed in prior brainstorming:

> $X$ mirrors $\mu$ $\iff$ $\operatorname{adj-}R^2_{\beta_\mu} \geq \tau_{\text{op}} = 0.15$

in a weekly realized-vol (or channel's natural observable) regression of $\log P_{\text{cCOP}/X}$ on the channel's surprise series plus standard controls.

Tier 1 does **not** consume the identity $\Delta g^{\text{pool}} \approx \phi^2 V(P) / (8L)$ or any other derivation from the notebook. That identity motivates downstream relevance but is not an input to a literature search. Independent review of the notebook derivation is a Tier 2 prerequisite and out of scope here.

The cCOP on-chain thin-liquidity reality (~$7K/day peak; Celo-only; Mento vAMM primary venue) documented in the 2026-04-02 research package at `/home/jmsbpp/apps/liq-soldk-dev/notes/` remains important context for the product thesis but is **not** a Tier 1 input. Tier 1 asks whether the economic signal exists in published work; whether on-chain infrastructure can read it is a separate question, answered by the sibling infra-feasibility spec (§12).

## 2. Why literature-only

Rev 2 attempted to fold infrastructure-availability into Tier 1 via numeric liquidity gates. Review found that the spec's own evidence (cCOP peaks ~$7K/day, §10's gate required $50K) made every row pre-fail, collapsing the verdict to a known outcome. That's not filtering; it's theater.

Two questions cleanly separate:

1. **Economic question (Tier 1, this spec)**: does the literature establish that realized FX vol — or the channel's natural observable — responds to the channel's macro surprise with $\operatorname{adj-}R^2 \geq \tau_{\text{lit}} = 0.10$? The $\tau$ gap from $\tau_{\text{op}}$: published adj-$R^2$ is typically in-sample and overstates out-of-sample; the literature bar is held weaker to avoid rejecting a real signal on sampling-noise grounds. A marginal CONFIRMED at $\tau_{\text{lit}}$ is provisional; Tier 2 re-verifies at $\tau_{\text{op}}$.

2. **Infrastructure question (sibling spec)**: does a tokenized on-chain counterparty exist with joint cCOP × X liquidity sufficient for the RAN's observation requirements? Gated by numeric thresholds; answered when the sibling spec is scoped.

Tier 1 = economic. Sibling = infrastructure. No interaction until both emit verdicts.

## 3. Objective

Per-channel literature verdict and cross-currency signal strength for $\mu \in \{\pi, C_{\text{remittance}}\}$. For each $\mu$:

- Is the signal present at $\tau_{\text{lit}} \geq 0.10$ in at least one Tier-A/B/C citation?
- Which counterparty currency does the literature identify as carrying the signal most cleanly?
- Is there a credible Tier-A/B null (adj-$R^2 < 0.05$, tight CIs, specification close to operational)?

Global roll-up combines per-channel verdicts into a routing decision for downstream work.

## 4. Scope

**In:**
- Per-channel literature survey for $\{\pi, C_{\text{remittance}}\}$.
- Cross-currency signal-strength extraction per channel.
- Proxy-tier classification per citation.
- Per-channel and global verdicts.

**Out:**
- On-chain availability matrix, usable-today gates, liquidity thresholds, joint cCOP × X checks. Moved to sibling spec.
- Any regression, data pull, Python, SQL, RPC, Dune.
- Any Solidity work or modification to `contracts/src/`, `contracts/test/`, `contracts/foundry.toml`.
- Any Tier 2 design, $U_{\text{RAN}}$ filter choices, Panoptic tokenization.
- Meta-analysis or weighted-pooling of partial studies.
- Paraphrased re-running of cited specifications on our data.
- Infrastructure-build scoping for missing wrappers.
- Any write operation to `/home/jmsbpp/apps/liq-soldk-dev/` (read-only).
- Channels $\mu(I), \mu(XN), \mu(S)$ — deferred to future sibling specs.

## 5. Sources and search order

Reordered from Rev 1 per the `NBER+SSRN → BanRep → IMF → Scholar → arxiv` priority:

1. **NBER + SSRN** — Andersen-Bollerslev-Diebold-Vega (2003) template and EM extensions; fastest first-cut on announcement-effect FX-vol.
2. **BanRep Borradores de Economía** — Colombia-specific ERPT and income-cycle work; Spanish-language.
3. **IMF Working Papers** filtered to Colombia.
4. **Google Scholar** — residual; forward-citation walks from closest hits in 1–3.
5. **arxiv MCP** — low prior for macro-econ; query only for completeness, no-penalty skip.

## 6. Search query set per channel

**Channel $\pi$ (inflation):**
- `"Colombia" (inflation OR CPI) (surprise OR announcement) (exchange rate OR FX) (volatility OR "realized vol")`
- `"pass-through" Colombia (variance OR volatility OR GARCH)`
- `"announcement effect" (Latin America OR "emerging market") (peso OR COP) volatility`
- Spanish: `(inflación OR IPC) (sorpresa OR anuncio) (tipo de cambio OR TRM) (volatilidad OR varianza)`
- Author seeds: Rincón-Castro, González-Gómez, Hamann-Salcedo, Choudhri, Hakura, Ca'Zorzi.

**Channel $C_{\text{remittance}}$:**
- `remittance Colombia "exchange rate" (volatility OR variance OR shock)`
- `"income cycle" OR quincena Colombia "exchange rate"`
- `remittance "emerging market" "FX volatility"`
- Spanish: `(remesas OR giros) Colombia (tipo de cambio OR volatilidad OR choque)`
- Author seeds: Orozco, Mora-Ruiz, Gomez-Oviedo, IDB Colombia team.

## 7. Proxy-closeness tier hierarchy (pre-registered)

Tier classification is load-bearing for verdict determination. Assigned per citation before recording the coefficient. Tier B/C boundary admittedly requires full-text judgment — "pre-registered" is a contract on the classification schema, not on abstract-only automation.

- **Tier A** — Exact channel: realized-vol LHS (or channel's natural observable), channel-specific surprise RHS, ≥3 of 4 operational controls (other-country surprise, monetary-policy surprise, VIX or global risk, own-country fundamentals).
- **Tier B** — Same channel on COP or cCOP proxy with different surprise construction or fewer controls.
- **Tier C** — Regional-panel study including Colombia, with Colombia-specific coefficient reported separately.
- **Tier D** — Same framework on non-COP EM currency (MXN, BRL, CLP, PEN) sharing Colombia-relevant macro structure.
- **`NOT STUDIED`** — farther than Tier D.

Tier D citations do not support `CONFIRMED` alone (see §9 Step 2 gate); they do support `PARTIAL_SUPPORT` and motivate Tier 1b.

## 8. Cross-currency signal-strength table (per channel, template)

One table filled per $\mu$. Columns split to avoid the Rev 2 `|`-separated cell:

| Counterparty | Reported adj-$R^2$ | Significance | Tier | Citation(s) | Strength bucket | Notes |
|---|---|---|---|---|---|---|
| USD | `NOT STUDIED` | — | — | — | none | (a priori: US-rate confounds must be netted) |
| EUR | `NOT STUDIED` | — | — | — | none | (strips US-rate channel) |
| DXY basket | `NOT STUDIED` | — | — | — | none | |
| MXN | `NOT STUDIED` | — | — | — | none | (differencing isolates Colombia-specific) |
| BRL | `NOT STUDIED` | — | — | — | none | |
| XAU (gold) | `NOT STUDIED` | — | — | — | none | (inflation-hedge proxy, global) |

Strength buckets derived: `strong` ≥ 0.25 / `moderate` 0.10–0.25 / `weak` < 0.10 / `none` = `NOT STUDIED`. Empty `—` is disallowed for the numeric columns; default text is `NOT STUDIED` across the row if no citation was found.

## 9. Verdict rules (literature-only; normalized labels)

Labels are bare `UPPER_SNAKE_CASE`; payload on a separate line in the deliverable. Single-regex-matchable at per-channel and global layers.

### Per-channel verdicts

Applied independently for each $\mu \in \{\pi, C_{\text{remittance}}\}$:

- `CONFIRMED` — payload: `channel=<pi|C_rem> target_counterparty=<token> tier=<A|B|C> citations=<N>`
- `PARTIAL_SUPPORT` — payload: `channel=<…> which_dimension=<level_not_vol|basket_not_isolated|surprise_not_announcement|tier_D_only|other>`
- `DISCONFIRMED` — payload: `channel=<…> null_tier=<A|B> citations=<N>`. Requires ≥1 credible Tier-A-or-B citation reporting $\beta \approx 0$ or $\operatorname{adj-}R^2 < 0.05$ with tight CIs.
- `NO_LITERATURE_SUPPORT` — payload: `channel=<…> citations_considered=<N>`. Replaces Rev 1's `GAP`.

### Per-channel decision tree (evaluate top-down, first-match wins)

For each channel:

1. IF ≥1 Tier-A-or-B citation reports $\beta \approx 0$ / $\operatorname{adj-}R^2 < 0.05$ with tight CIs → `DISCONFIRMED`.
2. ELSE IF ≥1 Tier-A-or-B-or-C citation meets $\tau_{\text{lit}} \geq 0.10$ → `CONFIRMED`. Tier-D citations alone cannot CONFIRM (closes Rev 2's gaming hole). Tie-break on multiple qualifying counterparties: (i) highest reported adj-$R^2$, (ii) lowest confound density, (iii) closest tier to A.
3. ELSE IF ≥1 Tier-A-or-B-or-C citation below threshold OR ≥1 Tier-D citation above threshold OR specification-distance flagged → `PARTIAL_SUPPORT`.
4. ELSE → `NO_LITERATURE_SUPPORT`.

### Global roll-up

Normalized labels with explicit payload fields (not inline-parenthetical):

- `PROCEED` — payload: `survivor_channel=<…> target_counterparty=<…> tier=<A|B|C>`. At least one channel emits `CONFIRMED`; Tier 2 is scoped with this channel-counterparty pair.
- `PIVOT_TO_TIER_1B` — payload: `candidate_channel=<…> rationale=<…>`. All channels emit `NO_LITERATURE_SUPPORT` or `PARTIAL_SUPPORT` only. Tier 1b (in-house regression) scoped on the channel with strongest partial evidence.
- `RETIRE_THESIS` — payload: `channels_disconfirmed=<list>`. All channels emit `DISCONFIRMED`. Economic-layer thesis retired; no Tier 2, no Tier 1b.
- `MIXED` — payload: `per_channel=<list of (channel, verdict)>`. Heterogeneous outcomes not fitting the three above. Surface and route to user.

### Prior calibration

Expected outcome distribution over a 1–2 day execution:

- Channel $\pi$: moderate prior on `PARTIAL_SUPPORT` or `NO_LITERATURE_SUPPORT`. Classical ERPT is on levels, not vol. Prior on `CONFIRMED` ≈ 15–25%.
- Channel $C_{\text{remittance}}$: moderate prior on `NO_LITERATURE_SUPPORT`. Flow-based remittance-surprise regressions are not a canonical literature. Prior on `CONFIRMED` ≈ 10–20%.
- **Prior on global `RETIRE_THESIS` is low** — requires `DISCONFIRMED` on both channels. `DISCONFIRMED` is publication-biased against firing: a study that looks for an FX-vol ↔ macro-surprise link and finds null is less likely to reach publication than one that finds the link. Expect `DISCONFIRMED` to fire < 5% per channel. Pivot protocol exists for completeness but is not the modal path.
- **Modal expected outcome: `PIVOT_TO_TIER_1B`.** That is a successful gate — it narrows the in-house regression scope and justifies the Tier 1b spec, rather than leaving the economic question unexamined.

## 10. Tier 2 / Tier 1b handoff columns (per-citation, required in deliverable)

For each row in the findings table: citation, sample start year, sample end year, country, counterparty pair, frequency (daily / weekly / monthly), LHS (vol / level / basket / flow), surprise construction (release − consensus / AR residual / oracle / rolling mean / other), control set, reported adj-$R^2$ (or closest analog), proxy tier (A/B/C/D), distance-from-hypothesis note, portability-to-cCOP caveat.

**Full-text-blocked downgrade rule:** 4 of these 13 columns (`frequency`, `surprise construction`, `control set`, `reported adj-$R^2$`) typically require reading methodology/results, not abstract. If the paper is paywalled and HITL retrieval is unavailable, the citation is automatically downgraded one tier (A → B, B → C, C → D). A Tier-D-downgraded citation cannot anchor `CONFIRMED` per §9 Step 2.

## 11. Deliverable

Single file: `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md`

Create the directory if it does not exist.

Sections:
1. Header — per-channel hypothesis statements, $\tau_{\text{op}} = 0.15$, $\tau_{\text{lit}} = 0.10$, search dates, searcher identity, second-reader identity (§16).
2. Findings table, per channel (§10 columns).
3. Cross-currency signal-strength table, per channel (§8).
4. Per-channel verdicts (label + payload + rationale + citation list).
5. Global roll-up (label + payload + rationale).
6. Gap analysis — unaddressed questions, close-enough-to-cite, missing.
7. Sources consulted, queries tried per source, confidence level, unresolved leads.
8. Second-reader sign-off block (§16).

Supporting artifacts (optional, not load-bearing): cCOP-context excerpts from the 2026-04-02 research package may be copied to `contracts/.scratch/` for the deliverable's Context section, but are no longer a dependency.

## 12. Integration & downstream

- `PROCEED` → spawn Tier 2 brainstorm. The sibling infra-feasibility spec must also emit a green verdict before Tier 2 execution starts (the two run in parallel or sequentially per product-owner choice).
- `PIVOT_TO_TIER_1B` → spawn Tier 1b spec for the channel with strongest partial evidence. Tier 1b runs the in-house regression using 2026-04-02 data-pipeline conventions. Sibling infra-feasibility spec runs in parallel (it's cheap).
- `RETIRE_THESIS` → no Tier 2, no Tier 1b on these channels. Separate spec proposes structurally different hedge target or retires the line.
- `MIXED` → each channel routed independently per its per-channel verdict.

Sibling infra-feasibility spec (to be scoped separately) holds §10-style numeric gates, 2026-04-02 availability matrix, snapshot-date anchoring, joint cCOP × X liquidity checks.

## 13. Non-goals

- [strict] No code in this spec or its deliverable.
- [strict] No regression, data pull, Dune queries, RPC calls.
- [strict] No Solidity modification.
- [strict] No write to `/home/jmsbpp/apps/liq-soldk-dev/`.
- No Tier 2 work, $U_{\text{RAN}}$ choices, Panoptic design.
- No on-chain availability check, liquidity threshold application, infra sibling-spec scoping.
- No meta-analysis, synthetic adj-$R^2$ pooling.
- No paraphrased-rerunning of cited specifications.
- No scope expansion to $\mu(I), \mu(XN), \mu(S)$ during Tier 1 execution.
- No Rev 3 mid-execution re-scoping. If execution hits a structural problem, escalate to a Rev 4 brainstorm.

## 14. Dependencies & prerequisites

- Read access to `contracts/notebooks/ranPricing.ipynb` for cross-referencing symbols and derivations.
- Read access to `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/` is *optional* (used for cCOP thesis context only; the infra-availability question moved to the sibling spec).
- Named human second reader: **JMSBPP (project owner)** unless the product owner designates a different human reviewer in writing before execution. An AI agent (including the searcher itself or any sibling LLM instance) is NOT an acceptable second reader — the countermeasure targets searcher bias, and a peer LLM does not provide independent attention.

## 15. Time estimate

- **Typical** (2 channels, moderate paywall friction, Spanish-language BanRep passes): 1 full day of focused search, ≈ 6–8 h effective work.
- **High** (multiple citation walks, paywall HITL blockers on 2+ sources): 1.5 days.
- **Hard cap**: 2 days. If execution trends above 2 days, escalate to a Rev 4 rescope — do not silently extend.

This is larger than Rev 1's "~one day" because the channel count doubled. Rev 1's estimate was single-channel.

## 16. Success criterion (outcome-based, tier-gated)

All must hold for the deliverable to be considered complete:

- a. All four primary sources (§5 items 1–4) queried with ≥3 of 4 channel-specific query patterns each. §5 item 5 (arxiv) may be skipped without penalty. Skipping any other source requires a documented hard block (paywall, outage, language) with timestamp AND downgrades the relevant channel's verdict by one strength tier.
- b. Per-channel findings tables contain ≥3 distinct citations *per channel* (total ≥6 across both channels) OR an explicit exhaustive-search failure statement signed by the searcher OR a `DISCONFIRMED` verdict supported by ≥1 Tier-A-or-B citation. A deliverable with only Tier-D citations cannot emit `CONFIRMED` for any channel per §9 Step 2.
- c. Per-channel verdicts emitted per §9 decision tree; global roll-up emitted; each verdict's tier claim auditable against §7.
- d. Deliverable reviewed by the named human second reader (§14). Second reader spot-checks that at least 3 citations actually support the Tier A/B/C/D classification claimed; signs off in §11 section 8.
- e. Zero `[CITATION-TODO]` markers remain in §17 References after execution. Every seed citation is either resolved to a full entry or removed.

## 17. Risks

- **DISCONFIRMED publication bias** — §9 prior-calibration section acknowledges this; `DISCONFIRMED` is unlikely to fire, meaning `RETIRE_THESIS` as a global outcome is effectively unreachable via Tier 1 alone. Retiring the thesis on strong prior grounds must go through a separate product decision.
- **Tier B/C boundary subjectivity** — full-text judgment; second reader (§14) is the countermeasure.
- **BanRep Spanish-language full-text** — may slow review; query set has Spanish equivalents; escalation to HITL translation allowed.
- **Paywalled journal content** — HITL retrieval may be needed; §10 full-text-blocked downgrade rule applies.
- **Rendering target** — inline LaTeX renders with MathJax/KaTeX; GitHub preview shows raw.
- **Searcher bias toward CONFIRMED** — second-reader countermeasure (§14, §16.d); §9 Step 2 tier gate; prior-calibration note.

## 18. References

Seed bibliography for searchers; full references compiled into the deliverable on execution. Placeholder markers are `**[CITATION-TODO]**` (upper-case for visibility); §16(e) gates on zero remaining.

- Andersen, T., Bollerslev, T., Diebold, F. X., Vega, C. (2003). "Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange." *American Economic Review* 93(1).
- Milionis, J., Moallemi, C. C., Roughgarden, T., Zhang, A. L. (2022). "Automated Market Making and Loss-Versus-Rebalancing." arXiv:2208.06046.
- Choudhri, E. U., Hakura, D. S. (2006). "Exchange Rate Pass-Through to Domestic Prices: Does the Inflationary Environment Matter?" *Journal of International Money and Finance* 25(4). **[CITATION-TODO]** volume/page.
- Ca'Zorzi, M., Hahn, E., Sánchez, M. (2007). "Exchange Rate Pass-Through in Emerging Markets." ECB Working Paper 739.
- Cai, F., Joutz, F. **[CITATION-TODO]**: EM announcement-effect FX-vol paper.
- Lahaye, J., Laurent, S., Neely, C. J. (2011). "Jumps, Cojumps and Macro Announcements." *Journal of Applied Econometrics* 26(6). **[CITATION-TODO]** volume confirmation.
- Rincón-Castro, H. **[CITATION-TODO]**: Borradores de Economía number, Colombian ERPT series.
- González-Gómez, A. **[CITATION-TODO]**: Colombian macro author.
- Hamann-Salcedo, F. **[CITATION-TODO]**: Colombian macro author.
- Orozco, M. **[CITATION-TODO]**: remittance macroeconomics.
- Mora-Ruiz, M., Gomez-Oviedo, R. **[CITATION-TODO]**: Colombian income cycle.
- Panoptic protocol whitepaper — `paper.panoptic.xyz`.
- Angstrom whitepaper v1 — `app.angstrom.xyz/whitepaper-v1.pdf`.
- Clark, J. (2022). SSRN `abstract_id=4317072` (cited in notebook §Instrument).
- K. Pap (2022). Range Accrual Note MSc thesis. `math.elte.hu/thesisupload/thesisfiles/2022msc_actfinmat2y-t0zf7f.pdf`.
