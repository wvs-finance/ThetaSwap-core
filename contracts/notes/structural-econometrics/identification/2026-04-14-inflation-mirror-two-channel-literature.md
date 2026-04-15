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
| Fuentes, Pincheira, Julio, Rincón et al. 2014 (BIS WP 462) | 2000 | 2012 | CL, CO, MX, PE (Colombia reported separately) | local/USD | intraday | FX returns + FX realized vol | macro surprises (release vs consensus) + intervention dummies [full-text-blocked] | intervention events, macro surprises basket [full-text-blocked] | not in abstract | C | FX-vol LHS with macro-surprise RHS on Colombia specifically is very close, but the "macro surprises" basket pools CPI, activity, rates — channel-π-specific CPI coefficient not isolable from abstract; tier downgraded from B under spec §10 full-text-blocked | Most transferable published result: Colombia/USD intraday event-study infrastructure matches cCOP/X structure if a CPI-only surprise can be recovered from their replication files |
| Berganza & Broto 2012 (JIMF; SSRN 1853310) | 1995-Q1 | 2010-Q1 | CL, CO, MX, PE + 4 non-LatAm EM (Colombia is a panel member with separate GARCH) | local/USD | daily | FX conditional variance (GARCH) | NO CPI surprise — RHS is intervention dummy + IT-regime dummy [full-text-blocked on exact spec] | intervention dummy, IT dummy, lagged vol | not in abstract | NOT STUDIED | NO CPI surprise RHS — IT-regime dummy is not a surprise construction per spec §7. Moved from Tier C to NOT STUDIED on stricter reading. | GARCH infrastructure portable, but their RHS does not estimate the channel-π β directly; cannot cite as lemma for adj-R² ≥ τ_lit |
| Clarida & Waldman 2007 (NBER w13010; SSRN 913306) | 2001-07 | 2005-03 | AU, CA, EZ, JP, NZ, NO, SE, CH, UK, US (G10; NO Colombia) | 10 local/USD pairs | intraday (10-min windows) | FX level (log-return around announcement) | CPI release minus Bloomberg consensus | IT-regime dummy | R² > 0.25 pooled on core CPI | NOT STUDIED | G10 currencies only — spec §7 Tier D requires non-COP EM currency sharing Colombia-relevant macro structure. G10 IT-regime prior is portable as direction (bad CPI news → appreciation) but does not qualify for any literature tier. Moved from D to NOT STUDIED. | Coefficient direction (bad-CPI-news → appreciation under credible IT) is portable priors; magnitude not portable to cCOP/X |

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
| NBER + SSRN | π | (1) `"Colombia" (inflation OR CPI) (surprise OR announcement) (exchange rate OR FX) (volatility OR "realized vol")`; (2) `"pass-through" Colombia (variance OR volatility OR GARCH)`; (3) `"announcement effect" (Latin America OR "emerging market") (peso OR COP) volatility` — executed on both NBER search (via Google site:nber.org fallback; direct NBER search returned landing page only) and SSRN (via Google site:papers.ssrn.com fallback; direct SSRN abstract pages returned HTTP 403, forcing §10 full-text-blocked downgrade on all SSRN-only candidates) | 1 qualifying row (Tier C only): BIS WP 462 (co-indexed on SSRN 2495031). 2 rows reclassified to NOT STUDIED after spec-compliance review flagged Tier-D G10 and Tier-C no-surprise-RHS as outside spec §7 (Berganza-Broto SSRN 1853310 and Clarida-Waldman NBER w13010 / SSRN 913306 retained in table as negative evidence / portable-direction prior) | ~16 rejected or NOT STUDIED: the 2 reclassified rows above plus ~14 farther-than-Tier-D rejections — Clavijo SSRN 878991, Edwards SSRN 975215 / NBER w1570, Urrutia-Hofstetter-Hamann SSRN 2407367, Keefe-Rengifo SSRN 2494821, Vargas-González-Rodríguez SSRN 2473994, Lanau-Robles-Toscani SSRN 3221125, Nuñez SSRN 927770, McCarthy SSRN 856284, Broto SSRN 1311813 (inflation-vol LHS, wrong channel), Miyajima SSRN 3523150 / IMF WP 19/277 (South Africa + wrong direction FX→CPI), Fuentes-BIS-462 descriptive pieces, Kalemli-Özcan-Unsal NBER w32329 (Fed hikes, no local CPI surprise RHS), Kaminsky-Reinhart NBER w8569 (financial stress, not CPI surprise RHS), Borrallo-Hernando-Vallés SSRN 2752888 (US unconventional policy, not CPI-surprise RHS), Ilzetzki NBER w29347 (FX regimes, not CPI-surprise RHS); SSRN direct-abstract 403-blocking means several hits' surprise-construction detail could not be verified from abstract alone and were conservatively rejected rather than downgraded |

## 10. Confidence level and unresolved leads

Per-channel qualitative confidence (low/medium/high) and leads unresolved at hard-cap.

## 11. Second-reader sign-off

- [ ] Second reader spot-checked ≥ 3 citations' tier assignments.
- [ ] Second reader confirmed no `[CITATION-TODO]` markers remain in spec §18.
- [ ] Second reader confirmed verdicts map correctly via spec §9 decision tree.

Signed: `<NAME>`   Date: `<YYYY-MM-DD>`
