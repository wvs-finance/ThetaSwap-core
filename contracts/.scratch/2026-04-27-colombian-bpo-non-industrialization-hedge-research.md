# Colombian BPO non-industrialization hedge: empirical literature synthesis

**Date:** 2026-04-27
**Author:** Research synthesis (foreground orchestration; arxiv MCP tried first per global preference, then targeted web search across NBER, IDB, World Bank, ECLAC/CEPAL, ILO, OECD, Banrep, Fedesarrollo, Universidad de los Andes, Sociedad y Economía, Springer, ScienceDirect, Cambridge Journal of Economics, ResearchGate, and sector trade press for BPO industry data).
**Purpose:** Empirical-literature grounding step for the (Y, M, X) framework iteration sharpened 2026-04-27 to the Colombian-young-worker-in-US-BPO target population. Tests whether the "non-industrialization risk" thesis is empirically tractable before any Y, M, or instrument design begins.
**Scope constraints:** Colombia primary; Philippines + India BPO comparisons admitted as benchmarks; LATAM literature admitted where Colombia-specific evidence is missing. No instrument design, no payoff structure, no code — research only.

---

## 1. Executive summary

The Colombian-BPO-non-industrialization hedge thesis is **empirically grounded in the canonical structural-transformation literature** but faces a **load-bearing data-frequency gap** at the individual-worker outcome level.

The macro thesis is well-established: Rodrik (2016) and the LATAM-specific extensions (CEPAL "Premature Deindustrialization in Latin America" 2016; Mendieta 2017 "Trade liberalization and premature deindustrialization in Colombia") document that LATAM economies hit peak manufacturing share at GDP per capita of USD 4,400-7,300 versus USD 10,000-15,000 for early industrializers, with Colombia specifically traced to the 1990 Apertura under Gaviria as the structural break. McMillan-Rodrik (2011) quantifies the *direction* of LATAM structural change as labor moving *from* high-productivity *to* low-productivity sectors since 1990 — the inverse of the East Asian success path. This is the mechanism the user identified, with a 35-year published evidence base.

The Colombian BPO sector is the contemporary instantiation of the trap: 600,000-705,000 workers (Glassdoor / ProColombia 2021-2024); 80% young, 67% women (sector trade press); USD 2.6B sector revenue 2021; ranked first in the Offshore BPO Confidence Index. The Philippines benchmark (Errighi-Khatiwada-Bodwell ILO 2017) shows BPO workers earn 53% above same-age peers but face 100%+ annual turnover, near-zero union density, "digital Taylorism" task design, and BPO-as-stepping-stone-to-emigration self-perception (Beerepoot-Hendriks 2013). Career mobility within the sector is empirically weak.

**The cleanest data path** is DANE GEIH (monthly labor force survey; CIIU Rev. 4 industry classification; coverage since 2006; programmatic access) cross-referenced with Banrep's quarterly services-sector value-added series, plus Philippines BPO comparable data (PSA / IBPAP), plus ProColombia BPO sector reports. A direct "Colombian BPO worker outcome" panel does *not* exist as a standing series — the BPO-specific cohort would have to be constructed from GEIH micro-data using CIIU codes 82 (administrative + support) and 62-63 (computer services).

**Prior hedge-design attempts** are mostly tangential. Shiller's "Macro Markets" (2003) proposed *occupation-and-region wage indices* as livelihood-insurance underliers — the closest theoretical precedent. ISAs (Lambda School / Holberton) operationalize income-share contracting but were degraded by adverse-selection and outcome-disclosure failures. US Trade Adjustment Assistance offers wage-insurance evidence for the *inverse* problem (workers displaced *out of* manufacturing). No prior product directly hedges the "absorbed *into* low-productivity sector" risk. This is genuinely novel territory; the Abrigo design would be first-of-kind.

---

## 2. Sub-area 1: Premature deindustrialization — canonical literature

### Rodrik (2016) "Premature Deindustrialization" — the foundational paper

Rodrik's 2016 paper (NBER WP 20935, *Journal of Economic Growth* 21(1)) documents two empirical regularities for developing countries since 1990:

**Regularity 1 (lower peak income).** The hump-shaped relationship between the manufacturing employment share and per-capita GDP has shifted *downward* and *closer to the origin* over time. Early industrializers (Western Europe, US, Japan, Korea) reached peak manufacturing share at GDP per capita ~USD 10,000-15,000 (PPP, current). Recent industrializers in LATAM and SSA peak at materially lower income levels:

- Argentina: peak manufacturing share at USD 5,461 GDP per capita
- Brazil: peak at USD 5,202
- Chile: peak at USD 4,392
- Mexico: peak at USD 7,275
- (Colombia not separately tabulated by Rodrik but tracks the LATAM cluster — multiple Colombia-specific follow-ups locate the manufacturing-employment-share peak in the late 1970s / early 1980s at ~USD 5,000-6,000 GDP per capita.)

**Regularity 2 (lower peak share).** The peak manufacturing employment share itself has fallen — early industrializers peaked at 30-40% manufacturing employment; LATAM economies peaked at 15-25%; recent African economies are peaking at <15%.

The interpretation: countries are "running out of industrialization opportunities sooner and at much lower levels of income compared to the early industrializers." The trap closes before the structural transformation completes.

### McMillan & Rodrik (2011) and McMillan-Rodrik-Verduzco-Gallo (2014) — labor reallocation

McMillan & Rodrik (NBER WP 17143, 2011) decompose aggregate productivity growth into within-sector productivity growth and between-sector labor reallocation. The headline finding: **since 1990, structural change has been growth-*reducing* in both LATAM and SSA**, with the most striking effect in LATAM. Labor flows in LATAM ran *from* higher-productivity manufacturing *into* lower-productivity informal services — the exact opposite of the East Asian pattern. Estimates: between-sector reallocation subtracted 0.3-0.6 percentage points per year from LATAM aggregate productivity growth 1990-2005.

Drivers identified by McMillan-Rodrik: (a) commodity-export specialization (Dutch disease effects on tradables), (b) overvalued real exchange rates, (c) labor-market rigidity preventing rapid sectoral reallocation. Countries with competitive/undervalued currencies and flexible labor markets experienced more growth-enhancing reallocation. LATAM scored poorly on both.

### Colombia-specific evidence

**Mendieta-Muñoz, Ocampo et al. (2017), *Journal of Economic Structures* 6:** "Trade liberalization and premature deindustrialization in Colombia." Koyck-transformation model on Colombian data + fixed-effects panel on eight LATAM countries. Headline: the fall in average effective tariffs (1990 Apertura under Gaviria) is the dominant economic driver of Colombia's premature manufacturing-share reduction. Secondary drivers: foreign-investment flows and Dutch disease from oil (Caño Limón, Cusiana). Associated with measurable inequality increases.

**Sociedad y Economía (Universidad del Valle, 2024) "From Deindustrialization to Tertiarization of the Colombian Economy: Employment as the Main Loser":** Colombian commerce/services value-added has 0.44 employment elasticity vs. manufacturing's 0.71. Tertiarization mechanically reduces job creation per unit of GDP growth — quantifies the trap at the labor-market level.

**ECLAC/CEPAL (2016) "Premature Deindustrialization in Latin America":** canonical regional reference; argues LATAM deindustrialization specialised the region in commodities, resource-based manufactures, and *low-productivity services* (the BPO segment fits here). UNCTAD 2003/2016 + ECLAC 2024 *Panorama of Productive Development Policies* reaffirm the diagnosis.

### Baumol cost disease — applicability

Baumol & Bowen (1966); Baumol macro restatement (NBER WP 12218, 2006). Stagnant labor-intensive services cannot raise productivity to match economy-wide wage growth, so service costs rise. Estache et al. (2021, *Transportation Research A*) find Baumol's-disease evidence in urban transport across 25 cities in AR/CL/CO/PA. **Generalisation to BPO:** labor-cost share is structurally 70-80% (KDCI/Magellan 2024-2025), making BPO the canonical Baumol stagnant sector — productivity bounded by agent-call-volume-per-shift, wages must rise with the broader economy. **Implication for the trap:** the long-run equilibrium is either (a) BPO wage compression, (b) offshoring to lower-cost geographies (Africa, lower-tier LATAM), or (c) AI substitution. All three close the wage→capital ratchet for the worker.

### Cimoli-Dosi-Stiglitz tradition

Cimoli, Dosi, Stiglitz (eds.) *Industrial Policy and Development* (Oxford UP 2009) frames LATAM underdevelopment as a capabilities-accumulation failure; Colombia treated within the LATAM panel. Empirical contribution is institutional/historical rather than econometric — useful framing, not estimation evidence.

---

## 3. Sub-area 2: BPO labor economics — Colombia, Philippines, India

### Colombian BPO sector — the empirical state

*Sector size + demographics (ProColombia / Statista 2021-2024).* 600,000-705,000 employees end-2021; ~19% annual growth (ProColombia); sector revenue USD 2.6-2.7B 2021-2022 (Teleperformance Colombia: USD 2.7B revenue, 35,000 employees; Atento: USD 1.5B, 16,000). 80% young workers, 67% women. Geography: Bogotá, Medellín, Cali, Barranquilla, Bucaramanga. Majors: Teleperformance, Atento, Sitel, Multienlace, Emtelco, Concentrix, Sutherland. Ranked first in the Offshore BPO Confidence Index (2024); 9.4% projected CAGR (Alcor BPO 2025).

*Labor conditions (Nearshore Americas 2023).* Colombia's Ministry of Labor received ~200 complaints from current/former Teleperformance employees: unpaid severance, excessive hours, incomplete wages, unpaid social security, harassment. Feb 2023 Teleperformance/Utraclaro union settlement committed the firm to formal complaint channels. Wage data not separately published at BPO-sub-sector level (CIIU Rev. 4 lumps BPO into 82 + parts of 62/63); entry-level monthly wages 1.0-1.5 minimum wages (~USD 320-500 in 2024) per Computrabajo / Glassdoor scrapes.

**Productivity / career mobility — literature gap.** No published academic study of Colombian-BPO productivity per worker, internal promotion rates, exit-into-non-BPO-careers rates, or wage-trajectory-vs-control-cohort comparisons exists. ProColombia trade press claims "specialized training" and "higher retention than other outsourcing destinations" but Ministry-of-Labor complaint volume suggests retention is materially worse than the marketing line.

### Philippines BPO — the deepest-studied benchmark

**Errighi, Khatiwada, Bodwell (ILO 2017) "BPO in the Philippines: Challenges for Decent Work" — canonical reference.**
BPO compensation USD 9,297/yr vs USD 2,580 country-wide (3.6× premium); BPO workers earn 53% above same-age peers; 50%+ female workforce concentrated in low-paid tier; trade union activity "almost non-existent"; annual turnover up to 100%+; widespread health concerns (stress, eye strain, voice loss, rising HIV/AIDS); skills-shortage paradox (employers struggle to find *and retain* trained workers).

**Beerepoot & Hendriks (2013), *Service Industries Journal* 33(11), "Employability of offshore service-sector workers in the Philippines: dead-end jobs?"** Examines Manila/Cebu BPO firms: mainstream BPO work offers limited career advancement (flat hierarchies, task non-variation); "digital Taylorism" — call-centre cubicle rows like assembly lines; "highly educated workers performing low-skilled jobs" paradox; workers self-perceive BPO as a *stepping stone to overseas employment*, not a long-term career; "paradox of geography in offshoring" (employment in-place, limited mobility in-place). **Direct empirical confirmation of the user's mechanism: BPO absorbs young educated workers without enabling the wage→capital transition; the worker's escape is migration, not capital accumulation.**

**Recent updates (2020-2024).** 1.7-1.8M Filipino BPO workers as of 2024, ~7% of GDP; continued attrition; Beerepoot 2022 examines online-freelancing variants with mixed mobility outcomes.

### India IT-BPM — the largest comparative case

- 5.4M+ IT-BPM employees in 2023; India tech pay *plunged ~40%* per CIO 2024 reporting, suggesting a Baumol ceiling and/or AI substitution biting.
- Bangalore software engineer earns 50-70% less than NYC/SF peer (cost-arbitrage shrinking from the bottom, not the top).
- IT-BPM shifting from commodity services to engineering/legal/R&D — captures only a small fraction of lower-tier voice-BPO workforce.
- Aspray-Mayadas-Vardi (ACM 2008) frames labor-supply-side dynamics; Park (2024 *Bulletin of Economic Research*) finds service-offshoring-to-India reduced US employment 2000-2006 then turned positive for college-educated workers 2006-2016.

### Wage-arbitrage compression mechanism

Triangulating Errighi-Bodwell + Beerepoot-Hendriks + India recent data: as Philippines/India BPO wages rose with their broader labor markets (Baumol drag), the *cost-arbitrage gap with the US* compressed. US clients responded by (a) shifting to lower-cost geographies (Colombia, Costa Rica, Kenya, Egypt), (b) introducing AI substitution above human agents, or (c) accepting higher prices. Colombia is currently in phase (a) — a *destination* of compression-driven migration. The thesis question: how long does Colombia stay in (a) before becoming itself the *origin* of further offshoring?

### Young-worker outcomes — the critical gap

No Colombian study comparable to Errighi-Bodwell exists. Familias en Acción long-term studies (Báez & Camacho 2011; Attanasio et al. 2021) examine CCT effects on rural-urban schooling/labor but do not separately track BPO-vs-industrial-vs-informal sectoral assignment. Banrep labor-market reports track aggregate salaried-employment but not BPO. **A Colombian BPO-cohort study — comparing wage trajectory, household-formation, asset-accumulation, and capital-ownership outcomes for BPO entrants vs. counterfactual cohort — does not exist and is the single biggest empirical gap blocking a sharp Y-design.**

---

## 4. Sub-area 3: Existing hedge / insurance attempts

This is the load-bearing section. The Abrigo product is novel; most prior attempts hedge adjacent risks. The taxonomy:

### 4.1 Income Share Agreements (ISAs) — the closest contracting precedent

ISAs convert education financing into a percentage-of-future-income obligation. The student pays nothing up-front; if they get a job above a salary threshold, they remit (typically) 10-17% of income for 24-48 months, capped at some multiple of nominal tuition.

**Mechanism analogy to Abrigo.** ISAs *short* the worker's future labor income and *long* the school's training-quality investment. Symmetric to Abrigo's framing of "the worker's wage is exposed to non-industrialization risk; we can hedge that by ratcheting wage premiums into capital exposure."

**Empirical record (mostly negative):**
- Lambda School (now BloomTech): claimed 86% within-6-months job placement at $50K+; leaked May 2019 investor memo revealed actual 50% placement at 6 months. Class Central analysis estimates effective interest rate of 87% for placed students. Time magazine 2022 documented the gap between marketing and outcomes.
- Holberton School: claims 100% placement within 6 months at avg USD 108K, but no independent verification. Joined the Edly ISA-secondary marketplace in 2019 with USD 2M initial trades.
- Aspen Institute / RAND (2020) "Income Share Agreements: Market Structure, Communication, and Equity Implications": critical of the asymmetric-information dynamics; bootcamps are 64% of US/Canada ISA market value.
- General Assembly Catalyst ISA (UNESCO-recognised) and various LATAM-aimed bootcamps exist but no rigorous empirical evaluation of LATAM ISA outcomes was located.

**What ISAs got right.** They successfully securitised individual labor income at scale (Edly marketplace exists; secondary trading happens).

**What ISAs got wrong / missed.** (a) Adverse selection — the worst students with the worst expected outcomes preferentially picked ISAs; (b) hidden costs / non-transparent cap structures; (c) the contracting was *individual-level* not *cohort-level*, so the school's incentive to invest in placement quality was weak; (d) the trigger condition was "job placement" not "structural-transformation outcome" — so ISAs would *not* fire on the user's specific risk (Colombian BPO worker placed in a job is "successfully placed" by ISA criteria even though they remain locked in the trap).

### 4.2 Shiller's "Macro Markets" — the closest theoretical precedent

Robert Shiller (2003) *Macro Markets: Creating Institutions for Managing Society's Largest Economic Risks* (Clarendon Lectures in Economics, OUP) is the deepest theoretical proposal for hedging large-scale labor-income risks.

**Core proposal — "livelihood insurance":** a private insurer pays a stream of income to a policyholder if an *index of average income in the policyholder's occupation and region* declines substantially. Premiums are set higher in occupations/regions believed by the market to be exposed to outsourcing or technical change. This *is* the conceptual ancestor of the Abrigo BPO-worker hedge — Shiller named the exact mechanism.

**Why it didn't get built.** Shiller proposed it pre-2008-GFC, before deep options markets and pre-blockchain. The contracting infrastructure (continuous indices for Colombian-BPO-worker wage; trustless settlement; permissionless access for low-net-worth wage earners) didn't exist. Insurers couldn't price the basis risk against any individual policyholder cleanly. Adverse selection and moral hazard were considered too acute.

**What Shiller got right.** (a) Identified that *occupation × region* was the right granularity; (b) framed it as macro-risk-sharing across populations not individual idiosyncrasy; (c) recognised that the market premium itself would carry valuable information about future risk.

**What Shiller didn't address.** (a) The *trustless / permissionless* requirement — his model assumed a regulated insurer; (b) the *convex-payoff* preference for tail events (his stream-of-income payment is roughly linear); (c) the *premium-funded ratchet* mechanism — the holder doesn't accumulate productive capital from the premium, they just smooth income.

### 4.3 US Trade Adjustment Assistance (TAA) — wage-insurance evidence for the *inverse* problem

TAA provides retraining + Reemployment Trade Adjustment Assistance (RTAA, wage-insurance component) to US workers displaced by import competition. Empirical evaluations (Mathematica 2012; D'Amico-Schochet 2012; Census-Wharton WP 2022; CEPR VoxEU): TAA neutral-to-slightly-positive on employment, mixed on wages, participants closed gap with comparison group by year-4. Wage insurance specifically increases short-run reemployment probability and long-run cumulative earnings, self-financing under conservative assumptions, with most gains from *shorter unemployment spells* not retraining quality.

**Relevance.** TAA is the *inverse* problem (workers displaced *out of* high-productivity sector); the Colombian BPO worker is absorbed *into* low-productivity sector and locked there. TAA evidence demonstrates that parametric wage-trigger insurance is technically feasible and self-financing — but the bigger payoff comes from re-employment *speed* not *quality*, which is exactly the wrong dimension for the BPO trap (worker is continuously "employed" while structural outcome deteriorates). A naive wage-trigger insurance would mis-fire on this risk.

### 4.4 Conditional Cash Transfers — Familias en Acción

Familias en Acción (Colombia, since 2002): ~1.5M households; long-term impact (Báez & Camacho 2011 IZA DP 5751; Attanasio et al. 2021) +4-8pp high-school completion, +0.6 grades schooling for rural children; only significant labor-market effect = +2.5pp formal-employment for rural women. **Addresses upstream child-development bottleneck, not the BPO-worker capital-accumulation problem.** Demonstrates Colombian institutional capacity for large-scale conditional transfers; not a hedge product.

### 4.5 UBI / Colombia Mayor / Ingreso Solidario

Subsistence-level transfers; poverty-prevention tools, not hedge instruments. Abrigo explicitly rejects the UBI/charity model in favor of the premium-funded ratchet (per CLAUDE.md).

### 4.6 Catastrophe / parametric insurance with macro triggers

CCRIF SPC (since 2007) + IDB-supported parametric weather-insurance pilots in Central America are operational examples — triggers on weather variables, payouts pre-defined and rapid. **No existing parametric product uses non-industrialization or BPO wage compression as trigger.** CCRIF proves the parametric-trigger architecture works at sovereign scale; adapting to a labor-income index (manufacturing employment share, BPO-vs-industrial wage ratio) is technically straightforward but unprecedented. G20 SFWG / IAIS 2025 explicitly calls for scaling parametric insurance + cat bonds for developing-country labor-income exposures, but LI-trigger products remain conceptual.

### 4.7 Migration as the de-facto current hedge

Beerepoot-Hendriks's "BPO-as-stepping-stone-to-emigration" finding *is* empirical confirmation that workers exercise migration as implicit hedge. Supporting literature: Clemens-Montenegro-Pritchett (NBER, "The Place Premium") measures wage gap between identical workers in home vs. destination — for LATAM BPO-skill levels, place premium is 2-5×. IMF WP/2017/144 quantifies remittance macro-stabilization role; IDB 2023-2025 reports document LAC remittance flows reached USD 156B in 2023, Colombia USD 11.7B (~3% GDP).

**Implication.** Migration *is* the current hedge being exercised — but available only to workers with credit access, language, network, departure-cost tolerance. Abrigo's hedge would be the *in-place* alternative for workers who cannot migrate. The option-value of migration sets the economic upper bound on what a Colombian BPO worker would pay for an in-place hedge.

### Summary of the hedge-design gap

| Prior product | Mechanism | Triggers on | Permissionless | Convex payoff | Premium-funded ratchet |
|---|---|---|---|---|---|
| ISAs (Lambda/Holberton) | Future income share | Job placement | No | No | No |
| Shiller livelihood insurance | Index-based wage support | Occupation×region wage decline | No (theoretical) | No | No |
| TAA wage insurance (US) | Government wage subsidy | Trade-displacement event | No (means-tested) | No | No |
| Familias en Acción | Conditional cash | Child schooling | No | No | No |
| CCRIF parametric weather | Index-based payout | Weather parameter | No (sovereign) | Partial | No |
| Migration as hedge | Self-financed exit | Wage gap exceeds barrier | De-facto yes | Yes (place premium) | Yes (foreign saving = capital accumulation) |
| **Abrigo (proposed)** | **Convex perpetual on macro index** | **Non-industrialization trigger (TBD)** | **Yes** | **Yes** | **Yes** |

The Abrigo proposal occupies a quadrant no prior product has filled: permissionless + convex + premium-funded-ratchet, oracled to a non-industrialization risk. The closest precedent is migration itself, which is what wage earners are already doing — Abrigo would be the in-place financial substitute.

---

## 5. Sub-area 4: Data sources catalog

### Colombian government / central-bank data

- **DANE GEIH.** Monthly labor-force survey since 2006; CIIU Rev. 4 (10-sector A*10 aggregate, finer in micro-data); 2018 redesign expanded geographic granularity. *Gotcha:* BPO is not a stand-alone CIIU code — must be constructed from CIIU 82 (admin/support) + parts of 62 (computer programming) and 63 (data processing/hosting); no published BPO-specific tabulations.

- **DANE ECV.** Annual living-conditions survey; household-asset data (home ownership, durables, productive assets). Sample size limits BPO-cohort subgroup analysis.
- **Banrep labor-market reports + ESPE.** Quarterly aggregate salaried-employment + post-pandemic wage dynamics; ESPE peer-reviewed work on minimum-wage/informality. Sector decomposition stops at broad services; no BPO sub-decomposition.
- **Confecámaras firm-survival series.** Annual; ~99% of formally-registered Colombian firms; ~40% 5-year survival; informal sector excluded.
- **ANIF / Asobancaria Gran Encuesta MIPYME.** Semestral MSME survey; financial-access, growth, mortality variables.

### Sector-specific BPO

- **ProColombia BPO reports.** Marketing-oriented; published numbers (705K jobs, 19% growth) often self-cited; useful as upper bound. **Investincolombia.com.co** sector overview. **MinCIT bulletins** under Programa de Transformación Productiva.

### Comparative international + US counterpart

- **Philippine Statistics Authority LFS + IBPAP** (Philippines BPO benchmark, 2010-present); **NASSCOM Strategic Review** (India IT-BPM); **ILO ILOSTAT Colombia profile + Errighi-Khatiwada-Bodwell 2017**.
- **US BLS OEWS:** SOC 43-4051 Customer Service Reps (~2.7M US employment 2024), 41-2031 Retail Sales subset, 43-3011 Bill/Account Collectors. Annual.
- **US Census Service Annual Survey:** NAICS 561422 Telemarketing Bureaus, 561499 Other Business Support Services. ~1.5yr lag.

### Macro / IOs

- **World Bank WDI** (services + manufacturing value-added shares, employment-by-sector); **IMF WEO + Colombia Article IV (2024)**; **OECD Job Creation and Local Economic Development 2024 Colombia note**; **CEPAL Statistical Yearbook (2025)**.

### Existing on-chain assets (prior Abrigo iterations)

Closed FX-vol-CPI pipeline (COP/USD weekly + Banrep CPI monthly) reusable as covariate. Mento flows + DuckDB `onchain_xd_weekly` (10 proxy_kind × ~80 weeks) persist for cross-iteration use.

### Critical data gaps

1. **No BPO-cohort longitudinal panel for Colombia.** Construction requires linking GEIH waves via DANE's anonymized panel sub-sample and CIIU matching.
2. **No published Colombian-BPO wage series at firm level.** Glassdoor/Computrabajo are noisy scrapes.
3. **No counterfactual industrial control cohort.** Synthetic-control or propensity-matching needed since LATAM industrial sector is itself shrinking.

---

## 6. Synthesis: candidate (Y, X) pairs for the empirical β-estimate

Given the literature review, the question is whether non-industrialization risk admits a positive measurable β on Colombian BPO worker outcomes. Five candidate (Y, X) pairs are proposed, ranked by tractability and Panoptic-eligibility (M-stage downstream filter):

### Pair A — Y = Colombian non-tradable-services-to-manufacturing wage ratio; X = Asian BPO wage compression

Y: monthly Colombian non-tradable-services wage / manufacturing wage from DANE GEIH industry-stratified tabulation (rises when services wages compress vs. manufacturing). X: Philippine + Indian BPO wage compression vs. US BPO (cost-arbitrage gap shrinkage), constructed from PSA LFS + NASSCOM + US BLS OEWS. OLS monthly 2010-2026 (~192 obs), HAC(12): `Y_t = α + β₁·X_t + β₂·Δlog(COP/USD)_t + β₃·CPI_food_t + β₄·oil_t + ε`. **Sign expectation:** β₁ direction is regime-conditional — Asian wage compression first attracts US clients to Colombia (β₁ > 0), then displaces them to Africa/AI (β₁ < 0). Beerepoot post-2020 + Errighi pre-2020 suggest Colombia is currently in the destination phase but transitioning. **Panoptic-eligibility: MEDIUM** — monthly oracle feasible; not high-frequency.

### Pair B — Y = Colombian manufacturing employment share; X = Colombian services FDI / manufacturing FDI ratio

Y: quarterly Colombian manufacturing employment / total non-agricultural employment (DANE GEIH). X: Colombian inward FDI services / FDI manufacturing (Banrep BoP). OLS quarterly 2000-2026 (~104 obs): `Y_t = α + β·X_t + γ·oil_t + δ·trend + ε`. **Sign expectation:** β < 0 per Mendieta 2017 (manufacturing performance negatively related to FDI flows + Dutch disease). **Panoptic-eligibility: LOW** — slow-moving quarterly aggregates. Academic-defense identification, not a settlement trigger.

### Pair C — Y = Colombian services-vs-manufacturing productivity gap; X = US BPO offshorable-occupation employment growth

Y: log(Colombian manufacturing labor productivity / services labor productivity), Banrep National Accounts quarterly (rises when services-sector Baumol drag widens). X: US BLS OEWS employment in offshorable customer-service occupations (SOC 43-4051, 43-3011). OLS quarterly 2010-2026 (~64 obs): `Y_t = α + β·X_t + γ·FDI_services_t + ε`. **Sign expectation:** β > 0 per Baumol + offshoring literature. **Panoptic-eligibility: LOW** — quarterly + annual data; no continuous on-chain reference.

### Pair D — Y = Colombian young-worker (15-28) services-sector employment share; X = COP/USD nominal exchange rate (lagged 6-12 months)

Y: DANE GEIH monthly age-stratified employment by sector — share of young-worker employment in services. X: Banrep COP/USD daily, monthly-averaged; lag tested at 0, 3, 6, 12 months. ARDL(p,q) monthly 2010-2026 (~192 obs): `Y_t = α + Σᵢ βᵢ·X_{t-i} + γ·industrial_capacity_t + δ·school_age_pop_t + ε`. **Sign expectation:** β > 0 at 6-12mo lag — COP depreciation makes Colombian BPO labor cheaper in USD, expanding sector demand at the contracting-cycle horizon; young workers absorbed at higher rate per ProColombia growth dynamics. **Data sources:** DANE GEIH age-stratified; Banrep FX; DANE industrial capacity utilization; DANE demographic projections. **Panoptic-eligibility: MEDIUM-HIGH** — X (COP/USD) is the cleanest on-chain reference, with deep liquidity + oracle infrastructure already in place from the closed FX-vol-CPI pipeline; Y monthly oracleable. A perpetual put on COP/USD with payoff modulated by Colombian young-worker BPO-share translates cleanly to a Panoptic-style instrument. **The candidate most aligned with prior Phase-A.0 infrastructure investment.**

### Pair E — Y = Colombian household productive-asset ownership rate by income decile; X = manufacturing-share-of-GDP deviation from comparator-country trend

Y: DANE ECV annual, share of bottom-5-decile households owning productive assets (firm equity, business real estate, productive equipment) — direct measurement of the wage→capital transition success rate. X: Colombia manufacturing share of GDP minus median trend for Korea/Malaysia/Vietnam comparator. OLS annual 2010-2024 (n=15, bootstrap inference): `Y_t = α + β·X_t + γ·GDPpc_t + δ·gini_t + ε`. **Sign expectation:** β > 0 (the further Colombia falls below comparators, the lower productive-asset ownership for low-income households — the trap binds). **Panoptic-eligibility: VERY LOW** — annual, n=15, not settleable continuously. **Critical for academic defense as the *direct* mechanism test, but useless as a settlement Y.**

### Recommended pair ordering for actual estimation

Given Panoptic-eligibility weighting and prior-infrastructure reuse:

1. **Pair D first** — leverages the closed FX-vol-CPI infrastructure (COP/USD oracle, monthly DANE pipeline); the convex-payoff structure on COP/USD with Y modulated by Colombian-young-worker-BPO-share is the cleanest path from research to instrument. Risk: the FX-Y relationship is conflated by many channels (the user's prior CPI-FX iteration showed mean-β was insignificant — a similar risk applies here).
2. **Pair A second** — most directly tests the wage-arbitrage-compression mechanism from the BPO-comparative literature; better academic defense; weaker on Panoptic-eligibility.
3. **Pair E as academic anchor** — to be used in the spec / pitch to ground the convex-instrument story in the direct wage→capital-transition measurement, even though it can't be the settlement Y.
4. **Pair B and C as background** — confirm the macro story; not load-bearing for instrument design.

---

## 7. Honest caveats and gaps

**What the literature CAN tell us.** Premature deindustrialization in LATAM is empirically well-established (Rodrik, McMillan-Rodrik, Mendieta, ECLAC); Colombia's deindustrialization is post-1990 Apertura / trade-liberalization driven (Mendieta 2017; Sociedad y Economía 2024); Baumol cost disease applies to LATAM service sectors (Estache et al. 2021); Philippines/India BPO worker outcomes are mixed — wage premiums real (53% over peers; Errighi-Bodwell) but career mobility weak ("dead-end jobs"; Beerepoot-Hendriks); ISAs, TAA wage insurance, and parametric catastrophe insurance provide partial precedents but no permissionless + convex + premium-funded-ratchet product exists; migration is the de-facto current hedge.

**What the literature CANNOT tell us:**

1. **No published Colombian BPO worker cohort study.** Single biggest gap. We don't know whether Colombian outcomes mirror Philippines/India or diverge.
2. **No published productivity series for Colombian BPO sector.** Baumol applicability to Colombian BPO is *inferred from cross-country evidence*, not measured directly.
3. **No counterfactual identification of "but-for-BPO-employment."** Synthetic-control methods are feasible but require careful design.
4. **No Colombian young-worker household-asset-trajectory panel.** ECV is cross-sectional; ANIF MIPYME covers firms not workers.
5. **No on-chain proxy for "non-industrialization risk" exists.** Unlike FX, CPI, or commodity prices, this is a structural-aggregate variable at quarterly-to-annual frequency. Continuous settlement requires either (a) a high-frequency proxy (FX, sector-share GEIH) or (b) a parametric quarterly-threshold trigger; both lose mechanism fidelity.
6. **AI substitution risk is a major confounder.** GPT-class models are substituting voice/chat BPO labor at unknown rates. Substitution *accelerates* the trap (workers absorbed into a sector that is itself disappearing). A spec ignoring AI substitution is incomplete.
7. **Data lag.** GEIH ~6wk lag, NA quarterly 2-3mo lag, ECV ~1yr lag. The BPO-specific reference is intrinsically lagged.

**What would have to be true for the empirical β to be conclusive:**

- A monthly or higher-frequency Colombian-BPO-cohort labor outcome series must exist or be constructable from GEIH micro-data;
- The sign and magnitude of β must exceed an MDES threshold pre-registered before estimation (per Phase-A.0 anti-fishing discipline);
- The convex-payoff insufficiency caveat (Phase-A.0 Rev-2 §11.A) implies that mean-β alone is insufficient — quantile regression / GARCH-X / extreme-tail analysis of the BPO-cohort outcome distribution is required;
- The relationship must be robust to AI-substitution accelerations (i.e., the hedge must remain valuable even if the BPO sector shrinks rather than expands);
- Identification must rule out the alternative narrative that Colombian BPO is *reducing* the trap (per ProColombia's own marketing claim that BPO is upskilling young workers and improving career mobility).

**Process recommendation.** Before any spec authoring, commission a Data Engineer dispatch to attempt construction of a panel-quality Colombian BPO-worker cohort outcome series from GEIH micro-data (CIIU 82, 62, 63 codes; age-stratified 18-35; cross-wave matched via DANE longitudinal sub-sample). If that panel cannot be built at adequate sample size and frequency, the (Y, X) pair must downgrade from Pair-D-style direct-BPO measurement to Pair-A-style relative-wage-ratio proxies — a material loss of fidelity that the user should weigh before committing further iteration budget.

---

## 8. References

Aspray, W., Mayadas, F., & Vardi, M. Y. (eds.) (2006). *Globalization and Offshoring of Software*. ACM.
Attanasio, O., Cardona Sosa, L., Medina, C., Meghir, C., & Posso-Suárez, C. M. (2021). Long-term effects of cash transfer programs in Colombia. NBER WP.
Báez, J. E., & Camacho, A. (2011). Assessing the long-term effects of conditional cash transfers on human capital: Evidence from Colombia. IZA DP No. 5751.
Banco de la República (Banrep) (2024-2025). Labor Market Reports series; *Ensayos sobre Política Económica* 103 (2024) on minimum-wage effects.
Baumol, W. J., & Bowen, W. G. (1966). *Performing Arts: The Economic Dilemma*. Twentieth Century Fund.
Baumol, W. J. (2006). Baumol's cost disease: A macroeconomic perspective. NBER WP 12218.
Beerepoot, N., & Hendriks, M. (2013). Employability of offshore service-sector workers in the Philippines: dead-end jobs? *Service Industries Journal* 33(11).
Beerepoot, N., & Oprins, T. (2022). Online freelancing and impact sourcing in the Philippines. *Electronic J. of Information Systems in Developing Countries*.
Cimoli, M., Dosi, G., & Stiglitz, J. E. (eds.) (2009). *Industrial Policy and Development*. Oxford University Press.
Class Central (2019). Are ISAs Affordable? Analysis of Lambda School's ISA Shows an Estimated Interest Rate of 87%.
Clemens, M. A., Montenegro, C. E., & Pritchett, L. (2008+). The Place Premium: Bounding the Price Equivalent of Migration Barriers. NBER WP.
Confecámaras (multi-year). Dinámica empresarial y supervivencia.
DANE Colombia (multi-year). GEIH; ECV. https://www.dane.gov.co.
D'Amico, R., & Schochet, P. Z. (2012). The evaluation of the Trade Adjustment Assistance Program. Mathematica / US DOL ETAOP 2013-08.
ECLAC/CEPAL (2016). *Premature Deindustrialization in Latin America*. Production Development Series.
ECLAC/CEPAL (2024). *Panorama of Productive Development Policies in Latin America and the Caribbean, 2024*; (2025) Statistical Yearbook + Social Panorama.
Errighi, L., Khatiwada, S., & Bodwell, C. (2017). Business Process Outsourcing in the Philippines: Challenges for Decent Work. ILO Asia-Pacific WPS.
Estache, A., Garsous, G., & La Ferrara, V. (2021). Baumol's cost disease and urban transport services in Latin America. *Transportation Research A* 149: 206-225.
G20 SFWG / IAIS (2025). Identify and Address Insurance Protection Gaps.
IDB Migration Blog (2023-2025). Migrant wages and remittances to LAC.
IMF (2017). Migration and Remittances in LAC: Engines of Growth and Macroeconomic Stabilizers? IMF WP/17/144.
ILO (2007). Offshoring and the Labour Market. Economic and Labour Market Paper 2007/11.
McMillan, M. S., & Rodrik, D. (2011). Globalization, Structural Change and Productivity Growth. NBER WP 17143.
McMillan, M., Rodrik, D., & Verduzco-Gallo, Í. (2014). Globalization, Structural Change, and Productivity Growth, with an Update on Africa. *World Development* 63: 11-32.
Mendieta-Muñoz, R. (2017). Trade liberalization and premature deindustrialization in Colombia. *Journal of Economic Structures* 6:24.
Nearshore Americas (2023). Why is Colombia's Labor Ministry Cracking Down on Call Centers?
OECD (2024). Job Creation and Local Economic Development 2024 — Colombia country note.
Park, S. (2024). Outsource to India: The impact of service outsourcing to India on the US labor market. *Bulletin of Economic Research*.
ProColombia / Invierta en Colombia. BPO sector landing page.
RAND Corporation (2022). Income Share Agreements: Market Structure, Communication, and Equity Implications. RR-A2649-1.
Rodrik, D. (2016). Premature deindustrialization. *Journal of Economic Growth* 21(1): 1-33; NBER WP 20935.
Shiller, R. J. (2003). *Macro Markets: Creating Institutions for Managing Society's Largest Economic Risks*. Clarendon Lectures, Oxford University Press.
Shiller, R. J. (2006). Livelihood Insurance proposal commentary.
Sociedad y Economía (Universidad del Valle) (2024). From Deindustrialization to the Tertiarization of the Colombian Economy: Employment as the Main Loser.
Statista (2024); Superstaff (2024); Glassdoor / Computrabajo (2024-2025) — Colombia BPO sector trade-press summaries.
Time Magazine (2022). Tech Boot Camps Dangled Well-Paid Jobs. They Didn't Always Deliver.
UNCTAD (2003, 2016). Premature deindustrialization damaging growth prospects in LATAM.
US BLS (multi-year). Occupational Employment and Wage Statistics (OEWS).
US Census Bureau (multi-year). Service Annual Survey, NAICS 561422 / 561499.
US DOL / ETA (multi-year). TAA Research and Evaluation Reports.
Wharton Mack Institute / Census CES WP 22-05 (2022). Can Displaced Labor Be Retrained? Evidence from Quasi-Experimental Variation in TAA.
World Bank (multi-year). World Development Indicators; Labor Market Adjustment, Reform and Productivity in Colombia.

**Internal Phase-A.0 / Abrigo sources:**

`/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/CLAUDE.md` — Abrigo Operating Framework, active iteration block (2026-04-27).

`/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-27-x-candidates-latam-wage-to-capital-transition.md` — broader X-research; this BPO-specific file refines candidate-2-style risks for the BPO-sector-locked subpopulation.

`/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-27-y-design-fx-x-latam-wage-earners.md` — Y-design literature for the prior FX-X iteration; Y-Cand 1 (RWC-USD) and Y-Cand 6 (NT-EmpLoss) carry forward as plausible diagnostic Ys for Pair D under the BPO refinement.

---

*End of report. Caveats: (a) The arxiv MCP search consistently returned low LATAM-BPO-MSME relevance — the substantive evidence base lives at NBER, World Bank, IDB, ECLAC, ILO, and the field-specialized journals (Journal of Economic Growth, Journal of Economic Structures, Service Industries Journal, World Development) accessed via web search. Per global preference, arxiv was tried first, then web search filled the gap. (b) Several cited works are referenced via abstract / sector-trade-press summary where full-text retrieval was not completed within the research budget; these are flagged inline. (c) The single biggest empirical gap is the absence of a Colombian BPO-cohort longitudinal panel — without one, the most rigorous (Y, X) estimation drops to relative-wage-ratio proxies (Pair A) or aggregate FX-share modulation (Pair D). The user should commission a Data Engineer dispatch to evaluate GEIH micro-data panel feasibility before further iteration on M / instrument design. (d) AI substitution risk is a major confounder noted in §7-Caveat-6; an honest spec must address it explicitly. (e) Per the active CLAUDE.md framework, this report is X-and-Y enumeration only; no instrument design, no Panoptic configuration, no payoff structure specified.*
