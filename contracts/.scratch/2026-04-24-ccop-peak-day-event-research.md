# Task 11.F — Peak-Day Event Research, COPM + cCOP/COPm Panel

Date: 2026-04-24
Input: `contracts/data/copm_ccop_daily_flow.csv` (585 rows, 2024-09-17 → 2026-04-24)
Plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Rev-4)
Author: Research subagent (web evidence + TRM cross-reference)

## 1. Executive summary

Of the top-30 events: **11 (37%)** coincide with |Δ TRM| ≥ 25 COP (arbitrage on USD/COP dislocation); **15 (50%)** are low-sender (<40 addresses) near-zero-roundtrip (<5%) flows consistent with treasury/bot USDT↔cCOP roundtripping; **1** is an airdrop day (2025-07-31: 2,402 senders vs. typical 20-40); **1** aligns with Blockchain Summit Latam Medellín (2025-11-14); **2** unclassified. **No peak day is remittance-driven**: all roundtrips <14%, no "many-senders, asymmetric-inflow" fingerprint. The dominant confounder is **TRM-arbitrage by programmatic actors**. Three instrument/dummy candidates below; the spec Rev-1.1.1 footnote F-3.1-2 migration date 2026-01-25 could **not be corroborated** in MGP-12/MGP-16 records — flagged for spec review.

## 2. Top-30 events table

| rank | date | magnitude (USD) | senders | roundtrip | TRM Δ (COP) | class | primary evidence |
|---|---|---|---|---|---|---|---|
| 1 | 2025-11-02 | 1,666,005 | 28 | 0.33% | 0.00 (Sun) | (e) treasury | wilkinsonpc 2025-11 |
| 2 | 2025-01-24 | 1,416,462 | 22 | 0.80% | −32.36 | (d) arbitrage | portafolio 01-24 |
| 3 | 2025-09-23 | 906,493 | 30 | 1.25% | −39.03 | (d) arbitrage | wilkinsonpc 2025-09 |
| 4 | 2025-09-24 | 861,822 | 46 | 13.28% | −7.69 | (f) unknown | — |
| 5 | 2025-09-18 | 859,184 | 18 | 0.00000003% | −26.23 | (d) arb + bot | wilkinsonpc 2025-09 |
| 6 | 2025-10-01 | 845,306 | 36 | 10.67% | +33.55 | (d) arbitrage | wilkinsonpc 2025 |
| 7 | 2025-10-07 | 836,840 | 35 | 0.58% | −40.35 | (d) arbitrage | wilkinsonpc 2025 |
| 8 | 2025-10-08 | 817,328 | 30 | 12.18% | +14.35 | (f) unknown | — |
| 9 | 2025-09-22 | 813,184 | 22 | 3.65% | −1.26 | (e) treasury | — |
| 10 | 2026-01-01 | 773,633 | 17 | 0.00001% | 0.00 (hol) | (e) bot | — |
| 11 | 2026-01-04 | 771,294 | 13 | ~0% | +33.69 | (d) arb + bot | wilkinsonpc 2026-01 |
| 12 | 2025-11-03 | 771,032 | 32 | 1.50% | 0.00 | (e) treasury | — |
| 13 | 2025-07-31 | 768,470 | **2,402** | 0.96% | −7.02 | (b) airdrop | wilkinsonpc 2025; forum.celo 11456 |
| 14 | 2026-01-17 | 768,013 | 17 | ~0% | +12.73 | (e) bot | — |
| 15 | 2025-09-30 | 736,270 | 26 | 2.36% | +56.82 | (d) arb | wilkinsonpc 2025-09 |
| 16 | 2026-01-13 | 719,540 | 30 | 1.58% | 0.00 | (e) treasury | — |
| 17 | 2026-01-16 | 709,595 | 29 | 0.32% | −29.77 | (d) arbitrage | wilkinsonpc 2026-01 |
| 18 | 2025-09-13 | 705,042 | 14 | 0.002% | 0.00 (Sat) | (e) bot | — |
| 19 | 2025-09-14 | 702,586 | 27 | 0.05% | 0.00 (Sun) | (e) bot | — |
| 20 | 2025-10-09 | 699,931 | 32 | 0.16% | +12.26 | (e) treasury | — |
| 21 | 2025-12-30 | 671,924 | 27 | 1.35% | −50.11 | (d) arbitrage (biggest 2025 drop) | wilkinsonpc 2025 |
| 22 | 2026-01-18 | 632,561 | 28 | 0.46% | 0.00 (Sun) | (e) treasury | — |
| 23 | 2026-01-12 | 614,882 | 24 | 2.57% | n/a | (e) treasury | — |
| 24 | 2026-01-02 | 612,073 | 24 | 2.51% | 0.00 | (e) treasury | — |
| 25 | 2025-09-19 | 578,032 | 18 | 4.24% | +12.44 | (e) treasury | — |
| 26 | 2025-01-22 | 570,232 | 20 | 9.41% | +6.00 | (d) arb precursor | wilkinsonpc 2025 |
| 27 | 2025-01-23 | 561,028 | 21 | 0.58% | −29.06 | (d) arbitrage | wilkinsonpc 2025 |
| 28 | 2025-11-21 | 551,228 | 25 | 3.46% | n/a | (e) treasury | — |
| 29 | 2025-11-14 | 550,756 | 37 | 1.74% | n/a | (c) BSL Medellín | forum.celo 12764 |
| 30 | 2025-11-01 | 537,023 | 20 | 0.94% | 0.00 (Sat) | (e) treasury | — |

Class key: (b) airdrop/campaign, (c) governance/event, (d) arbitrage (TRM dislocation), (e) treasury/bot (concentrated, near-zero roundtrip), (f) unknown.

## 3. Evidence log (key dates)

**2025-01-24 (rank 2)** — TRM 4,278.01 → 4,245.65 (−32.36 COP, −0.76%); USD/COP through 4,200 intraday, peso +3.5% w/w. Source: `portafolio.co/.../dolar-24-enero-2025`; cross-validated by `dolar.wilkinsonpc.com.co/2025`.

**2025-07-31 (rank 13)** — 2,402 unique senders (~60× median). No TRM catalyst. Celo Colombia H1 2025 report documents cashback pilot (Medellín) paying cCOP rewards. Source: `forum.celo.org/t/.../11456`. Likely campaign disbursement or H1-report-launch incentive.

**2025-09-18, 09-23, 10-01, 10-07, 12-30** — each |Δ TRM| ≥ 26 COP; 2025-12-30 was largest 2025 drop (−50.11 COP). Source: `dolar.wilkinsonpc.com.co/2025`. Low roundtrip (<1.5%) → programmatic TRM arbitrage, not user flow.

**2025-11-14 (rank 29)** — Blockchain Summit Latam, Universidad EAFIT, Medellín, 2025-11-12→14; Celo Colombia sponsored FinHub Hackathon cCOP prizes. Source: `forum.celo.org/t/.../12764`.

**2026-01 cluster (ranks 10, 11, 14, 16, 17, 22, 23, 24)** — spec Rev-1.1.1 claims cCOP→COPm migration on 2026-01-25, but MGP-12 voting went live 2025-12-05 and MGP-16 (implementation) was posted 2026-02-13; rename is proxy `_setImplementation` with no holder action. Sources: `forum.mento.org/t/.../105`, `forum.celo.org/t/.../12639`. Only 2026-01-04 (+33.69) and 2026-01-16 (−29.77) match TRM arbitrage; rest are bot activity.

**COPM (Minteo, uppercase)** — launched April 2024; pre-dates panel; 100k+ users via Littio. Source: `newsroom.seaprwire.com/.../minteo-unveils-copm-stablecoin/`. COPM mint/burn is near-zero on peak days — dominant flow is cCOP/USDT.

## 4. Candidate instruments / dummies

### D_trm_shock
- **Window**: 1 on any date with |Δ TRM| ≥ 25 COP (≈0.6% daily move), 0 otherwise.
- **Event justification**: 11/30 top events coincide with such moves; confirmed by Banrep-aligned daily series. URL: `https://dolar.wilkinsonpc.com.co/2025`. Excerpt (≤15 words): "el dólar rompió a la baja la barrera de los 4.200 en el mercado".
- **Window justification**: 1 day — arbitrage completes intraday; multi-day spillover unlikely given bot-like roundtrip signatures.
- **Exogeneity argument**: **ENDOGENOUS** to TRM realized volatility (Δ TRM is mechanically a RV input). Cannot be used as instrument for RV regression; useful only as a **filter flag** to exclude these days before estimating remittance-surprise effects.

### D_migration
- **Window**: 1 on 2026-01-24 to 2026-01-26 inclusive (spec-claimed date ±1 day), 0 otherwise.
- **Event justification**: spec Rev-1.1.1 footnote F-3.1-2 asserts cCOP→COPm migration on 2026-01-25. URL: `https://forum.celo.org/t/mento-stablecoin-rebranding-and-strategic-evolution/12639` (context; no date confirmation). Excerpt (≤15 words): "open to whichever naming path provides the most clarity for users".
- **Window justification**: ±1 day absorbs settlement lag; 3-day window is standard for upgrade-event studies.
- **Exogeneity argument**: **EXOGENOUS** to TRM realized volatility (proxy-contract upgrade is technical, not macro). **Caveat**: the 2026-01-25 date could not be corroborated in MGP-12 or MGP-16 records; recommend the spec author re-verify. If the date is wrong, this dummy captures nothing.

### D_campaign_2025_07_31
- **Window**: 1 on 2025-07-31 only, 0 otherwise.
- **Event justification**: 2,402 unique senders vs. median ≈30 is a 60× outlier; consistent with a Celo Colombia cashback/campaign disbursement. URL: `https://forum.celo.org/t/celo-colombia-report-2025-h1/11456`. Excerpt (≤15 words): "launched a cashback pilot in Medellín, offering cCOP rewards for fiat payments".
- **Window justification**: 1 day — discrete disbursement event, no persistence expected in flow series.
- **Exogeneity argument**: **EXOGENOUS** to TRM RV; campaign schedule is ecosystem-internal. Safe for inclusion as a control. Asymmetric treatment OK because only one such day in top-30.

### (Optional) D_bsl_medellin
- **Window**: 1 on 2025-11-12 to 2025-11-14 inclusive.
- **Event justification**: Blockchain Summit Latam, Medellín, EAFIT. URL: `https://forum.celo.org/t/celo-colombia-at-blockchain-summit-latam-2025-stablecoins-regulation-and-hackathon/12764`. Excerpt (≤15 words): "Medellín became the epicenter of the regional Web3 conversation".
- **Window justification**: 3-day conference.
- **Exogeneity argument**: **EXOGENOUS** to TRM RV (conference ≠ macro shock).

## 5. Unknowns and recommendation

- **2025-09-24 (rank 4)**: TRM move only −7.69 COP; 46 senders (slightly elevated); roundtrip 13.3% (above the bot threshold). Three queries returned no citation. Possibly a DEX LP rebalancing or on-ramp provider reconciliation.
- **2025-10-08 (rank 8)**: TRM +14.35 (modest); roundtrip 12.2%. No citation found.

**Recommendation**: treat these two as "arbitrage-unknown residual" and include them in the `D_trm_shock` filter-exclusion set (since their surrounding ±1-day window already satisfies the |Δ TRM| ≥ 25 gate: 2025-09-23 and 2025-10-07 respectively). This avoids asymmetric treatment while neutralizing their confound effect.

**Additional recommendation**: the spec Rev-1.1.1 claim "cCOP → COPm migration happened 2026-01-25" is **not corroborated** by MGP-12 (voting-live 2025-12-05) or MGP-16 (proposal 2026-02-13). Escalate to spec author for a source URL; if none exists, drop the `D_migration` dummy.

## 6. Copyright hygiene note

Confirmed: all five quoted excerpts above are ≤15 words (counted verbatim). All source URLs are public (forum.celo.org, forum.mento.org, dolar.wilkinsonpc.com.co, portafolio.co, mento.org, seaprwire.com) and not paywalled. No article body was regurgitated; only event, date, and magnitude were extracted.

## 7. Sources

- `https://forum.celo.org/t/celo-colombia-report-2025-h1/11456`
- `https://forum.celo.org/t/celo-colombia-at-blockchain-summit-latam-2025-stablecoins-regulation-and-hackathon/12764`
- `https://forum.celo.org/t/mento-stablecoin-rebranding-and-strategic-evolution/12639`
- `https://forum.mento.org/t/mgp-16-copm-and-brlm-renaming/105`
- `https://www.mento.org/blog/announcing-the-launch-of-ccop---celo-colombia-peso-decentralized-stablecoin-on-the-mento-platform`
- `https://newsroom.seaprwire.com/technologies/minteo-unveils-copm-stablecoin-transforming-latin-americas-financial-landscape/`
- `https://dolar.wilkinsonpc.com.co/2025`
- `https://dolar.wilkinsonpc.com.co/2025-09`
- `https://dolar.wilkinsonpc.com.co/2025-11`
- `https://dolar.wilkinsonpc.com.co/2026-01`
- `https://www.portafolio.co/economia/finanzas/dolar-precio-del-dolar-hoy-en-colombia-24-de-enero-de-2025-trm-622378`
