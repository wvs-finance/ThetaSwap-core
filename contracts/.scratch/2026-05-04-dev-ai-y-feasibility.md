---
artifact_kind: dev_ai_cost_y_feasibility_memo
parent_iteration_pin: dev-AI-cost iteration (CORRECTIONS-θ 2026-05-04, parent CLAUDE.md "Abrigo Operating Framework"; Pair D = Y₁ closed PASS 2026-04-28)
emit_timestamp_utc: 2026-05-04
methodology: free-tier WebSearch + WebFetch survey of LATAM national-statistics-agency, central-bank-BoP, and developer-survey data sources; mirrors structure of `2026-04-27-dane-geih-y-feasibility.md` Pair D precedent; six-dimension evaluation (canonicality / free-tier / window / cadence / N_obs / methodology breaks); no β regression run; no implementation; pre-pin only
companion_dispatches: 2026-05-04-superfluid-for-ai-cost-cpo-research.md (in flight); 2026-05-04-x402-for-ai-cost-cpo-research.md (in flight)
---

# Dev-AI-Cost Iteration — Off-Chain Y Feasibility Assessment

**Iteration context.** User pivoted 2026-05-04 to focus the a_s population on **LATAM developers paying USD-denominated AI APIs / AI tooling** (Colombia primary; Mexico, Brazil, Argentina, Peru, Chile broader). User confirmed hypothesis: LATAM developers pay AI APIs predominantly via **fiat rails** (Visa/Mastercard → local-currency debit card → bank FX spread), NOT crypto rails. Per CORRECTIONS-θ (`contracts/.scratch/path-b-stage-2/phase-1/corrections_theta_substrate_scope_clarification.md`), the v1.5-data on-chain substrate panel does NOT serve as Stage-1 empirical input for this iteration — Y data must come from **off-chain** sources, parallel to Pair D's DANE GEIH approach.

**X side is fixed and out of scope here.** USD/COP (or USD/MXN, USD/BRL, USD/ARS, USD/PEN, USD/CLP) lagged 6–12 mo via central-bank reference rates is feasible via Banrep TRM / Banxico SIE / BCB SGS / BCRA / BCRP / BCC public APIs (Pair D already validated the Banrep TRM piece). **This memo addresses Y candidates only.**

---

## §1. Executive Summary

### Verdict

**FEASIBLE.** The dev-AI-cost iteration's Stage-1 β regression has at least three workable Y constructions. The strongest mirrors the Pair D DANE GEIH pattern using a different CIIU section cut (J = Information & Communications) on the same 2015-01 → 2026-03 window, with sample N≈134 post-lag-12. The next-strongest pivots to **DANE EMS Section J monthly index** (employment + income; 2018-01 onward) for activity-side rather than employment-share Y. A cross-LATAM panel using **UNCTADstat annual EBOPS-9 computer services imports** is feasible but cadence-mismatched (annual only), best as sensitivity rather than primary.

### PRIMARY recommendation

**Y_p = Colombian young-worker (14–28) employment share in CIIU Rev. 4 Section J ("Información y Comunicaciones") relative to total 14–28 employed**, sourced from **DANE GEIH micro-data** at monthly cadence, restrict-to-clean-window 2015-01 → 2026-03 per Pair D Option-α' precedent (Marco-2018 frame throughout; no Marco-2005 → Marco-2018 break; no CIIU Rev.3.1 → Rev.4 break).

- **Sign expectation pre-pinned**: β > 0 at conventional significance.
- **Mechanism**: Currency depreciation (USD/COP↑ at lag 6–12mo) → USD-denominated AI tooling becomes more expensive in COP terms → marginal pressure on local-currency-paid developers; absent a domestic substitute, Colombian ICT-section labor demand is structurally *increased* on the export side (US firms offshoring more dev work to Colombia for the same dollar reasons US service-wage arbitrage drives BPO offshoring per Pair D's Baumol-channel mechanism), producing higher Section J youth employment share at lag.
- **N_observations expected**: 134 monthly (Jan-2015 → Mar-2026 minus lag-12 cells), comfortably above `N_MIN = 75`.
- **Cadence**: monthly.
- **Transformation**: logit-Y (analog to Pair D since Y_p ∈ [~0.04, ~0.10]; bounded → logit technically correct).

### SENSITIVITY recommendations (3, pre-registered, no post-hoc promotion)

1. **Y_s1 = DANE EMS Section J nominal income index (Información y Comunicaciones)**, monthly, base 2018=100, cadence aligns with Pair D anchor; window 2018-01 → present, N≈99-lag-12 = 87 monthly observations.
2. **Y_s2 = Colombian young-worker employment share in CIIU Rev. 4 Section M ("Actividades profesionales, científicas y técnicas")**, GEIH micro-data, same monthly cadence + 2015-01 → 2026-03 window, N=134. Captures the broader "developer-as-knowledge-worker" cell rather than ICT-narrow Section J.
3. **Y_s3 = Cross-LATAM panel: UNCTADstat annual EBOPS-9 (Telecommunications, computer & information services) IMPORTS**, 6 countries (CO/MX/BR/AR/PE/CL), 2008-2024 annual, N_per_country = 17 → N_pooled (unweighted, fixed-effects) ≈ 102. Cadence-mismatched relative to Pair D's monthly anchor — secondary by design.

### N_expected per candidate

| Candidate | Cadence | Window | N_obs (post-lag-12) | Above N_MIN=75? |
|-----------|---------|--------|---------------------|------------------|
| **Y_p** (GEIH Section J share, CO) | monthly | 2015-01 → 2026-03 | 134 | YES |
| Y_s1 (EMS Section J nominal income, CO) | monthly | 2018-01 → 2026-03 | 87 | YES |
| Y_s2 (GEIH Section M share, CO) | monthly | 2015-01 → 2026-03 | 134 | YES |
| Y_s3 (UNCTAD EBOPS-9 imports, 6 LATAM) | annual | 2008-2024 | 102 (panel) | YES (panel-equivalent) |

---

## §2. Per-Candidate Inventory

### Category 1 — National Statistics Agency ICT-Sector Data

#### 1.1. **Colombia / DANE GEIH micro-data, Section J share** — PRIMARY anchor

- **Canonicality**: Highest. DANE is the official national statistical authority (Resolution 066 of 2012-01-31 adopting CIIU Rev. 4 A.C.; Ley 1622 de 2013 establishing 14-28 youth band). GEIH = `Gran Encuesta Integrada de Hogares`, the same instrument that powered Pair D Y₁ at PASS verdict 2026-04-28.
- **Free-tier**: Plain CSV/DTA/SAV ZIP downloads from `https://microdatos.dane.gov.co/index.php/catalog/<id>`. No registration, no auth, no rate limit (per Pair D feasibility memo §7). Per-year catalog IDs verified for 2015-2026 in Pair D memo.
- **Sample window**: 2015-01 → 2026-03 (CORRECTIONS-α' Option-α' window — DANE-canonical Rev.4 throughout via `RAMA4D_R4`; Marco-2018 frame applied via DANE empalme factor consistent with Pair D Y₁ pipeline).
- **Cadence vs Pair D's monthly anchor**: **Native monthly** — perfect alignment.
- **N_observations expected**: 134 (= 11.25 yrs × 12 mo − 12 lag cells).
- **Methodology breaks**: Same as Pair D — handled by Option-α' window. The 2021 Marco-2005 → Marco-2018 frame change is the headline issue, but Pair D's 2015-01 → 2026-03 window crosses it; the DANE empalme factor is applied operationally in the existing pipeline (per `project_pair_d_phase2_pass` memory). Section J specifically: confirmed live in CIIU Rev. 4 A.C. (`https://clasificaciones.dane.gov.co/ciiu4-0/ciiu4_dispone`); Section J coverage in GEIH is captured via the `RAMA4D_R4` field at the 4-digit level, with section recoding to J via DANE's correspondence table.
- **Caveat (specific to Section J cell-size)**: Section J is structurally smaller than Pair D's Section G–T broad-services aggregate. Per Pair D estimates (~7,000–9,000 14-28 employed total per month), the Section J cell is ~700–1,200 per month — borderline for monthly stability, but a 3-month rolling average or quarterly aggregation is a pre-registered fallback if monthly-Y volatility blows up Newey-West HAC standard errors. The same caveat triggered the BPO-narrow J+M+N sensitivity in Pair D Y₁ design.

#### 1.2. **Colombia / DANE EMS Section J monthly index** — Y_s1 sensitivity

- **Canonicality**: High. EMS = `Encuesta Mensual de Servicios` is DANE's official short-cycle services-sector monthly indicator, redesigned 2018-01 with monthly cadence (predecessor MTS was quarterly from 2007). EMS uses CIIU Rev. 4 A.C. and publishes 18 sub-sectors. Section J ("Información y Comunicaciones") is a published sub-sector with `Formulario Telecomunicaciones` documented as a separate survey form per WebFetch findings.
- **Free-tier**: Yes. Bulletins follow URL pattern `/files/operaciones/EMS/bol-EMS-<mmm><yyyy>.pdf` and Excel annexes at `/files/operaciones/EMS/anex-EMS-<mmm><yyyy>.xlsx`. Aggregate index series (NOT micro-data) downloadable; no auth required.
- **Sample window**: **2018-01 → 2026-03** (EMS monthly cadence does not extend back to 2008 — predecessor MTS was quarterly, not monthly, and would require separate splice). This is a HARD CONSTRAINT relative to Pair D's 2015-01 anchor.
- **Cadence**: monthly.
- **N_observations expected**: 99 monthly observations (Jan-2018 → Mar-2026) − 12-month lag = **87**. Above `N_MIN = 75` but tight.
- **Methodology breaks**: Single break in 2020-01 ("methodological improvements" per DANE — sampling change to lower threshold and additional disaggregation including the Section N call-center split-out). For Section J specifically the 2020-01 change appears as a sample-redesign discontinuity; Y_s1 must pre-commit to either (a) pre/post-2020 dummy, (b) restrict-to-2020+ window (loses 24 mo and N drops to 75-12=63 — BELOW N_MIN, UNVIABLE), or (c) accept the break as noise. Recommendation: option (a) dummy.

#### 1.3. **Mexico / INEGI ENOE micro-data + EMS Section J index** — out-of-scope as primary, in-scope for cross-LATAM panel

- **Canonicality**: Highest national authority. ENOE = `Encuesta Nacional de Ocupación y Empleo`, quarterly micro-data; Mexican Banco de Información Económica (BIE) hosts INEGI EMS Series 2018 base 2018=100 with monthly cadence going back to 2008 in the 2013-base-year series (and 2018-base-year from 2018-01). Both `Sector 51 (Información en medios masivos)` and `Sector 54 (Servicios profesionales, científicos y técnicos)` are published.
- **Free-tier**: ENOE micro-data: free CSV at INEGI catalog (`https://www.inegi.org.mx/programas/enoe/15ymas/`). EMS via BIE: requires a free API token (request via email; INEGIpy / inegiR libraries available). Note: token requirement is FRICTION above DANE GEIH zero-friction.
- **Sample window**: ENOE quarterly from 2005-Q1 → 2026-Q1. EMS monthly base 2013 from 2008-01; base 2018 from 2018-01 (overlap allows splicing).
- **Cadence**: ENOE = quarterly (mismatch with Pair D's monthly anchor — would require either (i) downcasting to quarterly Y for both Pair D + dev-AI-cost or (ii) sticking with EMS monthly which has the same 2018-cutoff issue as Colombia EMS).
- **N_obs**: ENOE quarterly 2008-2026 = ~73 quarters → ~69 post-lag-4 → BORDERLINE under N_MIN=75; EMS monthly 2008-2026 = ~219 → 207 post-lag-12 → comfortable.
- **Methodology breaks**: ENOE went through ENOEN ("Nueva Edición") during COVID disruption (2020 Q3 onward). EMS has 2013→2018 base year change.

#### 1.4. **Brazil / IBGE PNAD Contínua + PMS** — strong cross-LATAM candidate

- **Canonicality**: Highest. IBGE = federal statistical authority. PNAD Contínua = quarterly micro-data (rotating panel, 5 visits per dwelling). PMS = `Pesquisa Mensal de Serviços`, monthly aggregate index, includes a SEPARATE `Serviços de informação e comunicação` line including `serviços TIC` sub-component.
- **Free-tier**: PNAD Contínua micro-data via FTP (`ftp.ibge.gov.br`). PMS via SIDRA tables + FTP at `https://ftp.ibge.gov.br/Comercio_e_Servicos/Pesquisa_Mensal_de_Servicos/`. SIDRA is queryable and offers an API. No auth required.
- **Sample window**: PMS monthly Jan-2012 → 2026 (start: 2011-01 collection, indicators from 2012-01). PNAD Contínua quarterly from 2012-Q1.
- **Cadence**: PMS = monthly (good for Pair D alignment). PNAD Contínua = quarterly.
- **N_obs**: PMS monthly 2012-2026 = ~171 → 159 post-lag-12 → comfortable.
- **Methodology breaks**: PMS rebased to 2022=100 in 2023-01 with sample updates from PAS 2017 data, revised deflation procedures, and extended revision policy from 1 to 12 mo (per WebFetch finding). This is a non-trivial methodology break analogous to DANE EMS 2020 redesign. Spec must pre-commit to a 2023-01 dummy or splice via the official IBGE empalme.

#### 1.5. **Argentina / INDEC EPH + CESSI** — workable but quality concerns

- **Canonicality**: INDEC = highest national authority for EPH (`Encuesta Permanente de Hogares`) quarterly; CESSI = `Cámara de Empresas de Software y Servicios Informáticos` is a sectoral-association (NOT a statistical agency) but publishes annual employment + revenue indicators.
- **Free-tier**: EPH micro-data free at indec.gob.ar. CESSI reports free PDF + occasional Excel.
- **Sample window**: EPH quarterly 2003-Q1 onward; CESSI annual 2008+.
- **Cadence**: quarterly (EPH) / annual (CESSI).
- **N_obs**: EPH quarterly = ~93 quarters → ~89 post-lag-4 → above N_MIN. CESSI annual = ~17 → too short for solo analysis but pooled into UNCTADstat panel.
- **Methodology breaks**: EPH went through an INDEC credibility crisis (2007-2015, "intervención" period under the Cristina Fernández administration; statistical revisions controversial). Per Reality Checker–style anti-fishing: the Argentina EPH series is **flagged for credibility** during 2007-2015 — any spec using Argentina EPH MUST pre-commit to either (a) restrict-to-≥2016 window, dropping N to ~36 quarters → N_post-lag-4 = 32 → BELOW N_MIN=75 (UNVIABLE solo), or (b) accept 2007-2015 measurement-error noise as a robustness sensitivity.
- **Recommendation**: Argentina is **not viable as primary**. Use only as a panel cell with a regime-period control.

#### 1.6. **Peru / INEI ENAHO** — workable but cadence mismatched

- **Canonicality**: Highest. INEI = official national statistics. ENAHO = `Encuesta Nacional de Hogares`, continuous since 2005, with quarterly TIC bulletin since 2005.
- **Free-tier**: ENAHO micro-data at `https://proyectos.inei.gob.pe/iinei/srienaho/index.htm`. TIC bulletin free PDF.
- **Sample window**: ENAHO quarterly 2005+.
- **Cadence**: quarterly TIC reports; micro-data continuous but standard release pattern is quarterly aggregate.
- **N_obs**: quarterly 2005-2026 = ~85 → ~81 post-lag-4 → above N_MIN.
- **Methodology breaks**: 2017-Q1 sample frame redesign per Census 2017. Peru EPH-style redesign is well-documented but spec must pre-commit handling.

#### 1.7. **Chile / INE ENE + Banco Central de Chile data services** — most data-friendly LATAM cell

- **Canonicality**: INE = official authority. ENE = `Encuesta Nacional de Empleo`, monthly mobile trimester since 2010-01 base.
- **Free-tier**: ENE Banco de Datos at `bancodatosene.ine.cl` — interactive cross-tab system; downloadable Excel + dynamic queries; no auth.
- **Sample window**: ENE mobile-trimester from 2010-01.
- **Cadence**: monthly mobile-trimester (3-month rolling).
- **N_obs**: ~196 monthly mobile-trimesters → ~184 post-lag-12 → comfortable.
- **Methodology breaks**: 2016 adoption of CAENES classification (CIIU4.CL 2012 derivative). Section J coverage requires CIIU4.CL Section J → CIIU Rev. 4 J cross-walk. Pre-2016 series uses CAEN-INE 2008 — splice via INE's published correspondence.
- **Recommendation**: Chile is the cleanest cross-LATAM cell after Colombia for inclusion in a panel sensitivity.

### Category 2 — Trade-in-Services Central-Bank Data

#### 2.1. **Colombia / Banrep BoP services-imports + DANE MTCES/EMCES** — quarterly available; monthly only since 2022

- **Canonicality**: Banrep BoP under BPM6 since 2014 with quarterly statistics standardized from 2000 onward. DANE MTCES (quarterly, 2007-2021) was the source feed; DANE EMCES (monthly, 2022 onward) is the new monthly mandate.
- **Free-tier**: Banrep BoP downloadable Excel quarterly from `https://www.banrep.gov.co/es/estadisticas/balanza-pagos` (URL returned 404 in WebFetch but the parent stats portal is documented; Banrep BoP report Q1-2025 confirms publication). DANE MTCES historical CSV at `https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/muestra-trimestral-de-comercio-exterior-de-servicios/muestra-trimestral-de-comercio-exterior-de-servicios-mtcs-informacion-historica`. DANE EMCES monthly bulletins + Excel annexes at `/files/operaciones/EMCES/`.
- **Sample window**: Banrep quarterly from 2000-Q1; DANE MTCES quarterly 2007-Q1 → 2021-Q4; DANE EMCES monthly 2022-01 onward.
- **Cadence**: Quarterly (Banrep + MTCES); Monthly (EMCES, but only since 2022).
- **N_obs (quarterly)**: 2000-2026 ≈ 105 quarters → 101 post-lag-4 → above N_MIN.
- **N_obs (EMCES monthly)**: 2022-01 → 2026-03 = ~51 → 39 post-lag-12 → BELOW N_MIN. UNVIABLE solo monthly.
- **Computer services line**: DANE classifies "computer services" within "Servicios de telecomunicaciones, informática e información" as a single grouped category; EBOPS code 263 / 9.1 disaggregation per BPM6 not always published as a separate column on Banrep tables. Confidentiality redaction (`reserva estadística`) applies for some cells per WebFetch finding. Detailed EBOPS-9.1 monthly is NOT consistently published.
- **HALT-and-surface**: Banrep `https://www.banrep.gov.co/es/estadisticas/balanza-pagos` returned 404 in WebFetch — INDIRECT EVIDENCE of URL change. Spec must include a HALT clause for the actual download path or fall back to the IMF / UNCTAD harmonized series.

#### 2.2. **Mexico / Banxico SIE BoP services** — cleanly accessible via API

- **Canonicality**: Banxico = official under BPM6 since 2017 (with backfill to 2002 per CEIC).
- **Free-tier**: SIE = `Sistema de Información Económica` at `https://www.banxico.org.mx/SieInternet/`. Public API with token requirement.
- **Sample window**: 2002-Q1 → 2026-Q1 quarterly.
- **Cadence**: quarterly.
- **N_obs**: ~97 quarters → 93 post-lag-4 → above N_MIN.
- **Computer services line**: separate disaggregation not consistently published on the public CA410 summary table; full BPM6 detail in CE174 information structure. EBOPS code-9 detail confirmed at quarterly level for some series.

#### 2.3. **Brazil / BCB BoP open data** — best quality / best access among LATAM

- **Canonicality**: BCB under BPM6.
- **Free-tier**: `dadosabertos.bcb.gov.br/dataset?tags=Balanço+de+Pagamentos+-+BPM6` — open data portal with monthly + quarterly CSV. No auth.
- **Sample window**: monthly from 1995 (legacy methodology); BPM6 standardized from 1995 with revisions; effectively comparable from 2010-01.
- **Cadence**: MONTHLY for the headline services line.
- **N_obs**: monthly 2010-2026 ≈ 195 → 183 post-lag-12 → comfortable.
- **Computer services**: included in services category alongside transport, travel, insurance, financial, construction, COMPUTING AND INFORMATION services, royalties, and others. Whether the EBOPS-9.1 monthly disaggregation is published separately or bundled with telecom requires drilldown into the SGS time-series codes (`https://www3.bcb.gov.br/sgspub/`); search results confirm "computing and information services" appears as a published category but precise SGS series ID requires direct portal browsing.

#### 2.4. **Argentina / BCRA + INDEC** — credibility caveats persist

- BCRA `balance cambiario` methodology defines "Información e informática" as a transaction category for FX-market operations — distinct from BoP-imports BPM6. INDEC publishes balance-of-payments quarterly under BPM6 with services breakdowns.
- 2007-2015 INDEC credibility flag applies to BoP series too. **HALT-and-surface**: post-2015 series are credible; the spec MUST pre-commit to either restrict-to-≥2016 (N becomes ~40 quarters → 36 post-lag-4 → BELOW N_MIN) or accept the noise.

#### 2.5. **Peru / BCRP estadísticas portal** — clean access

- BCRP at `https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/balanza-de-pagos` and monthly imports/exports series. "Servicios computacionales / informáticos" published within "other services" category.
- Quarterly cadence per WebFetch finding ("La balanza de pagos en el Perú... presenta con periodicidad trimestral").
- Sample window from 1991 onward.
- Free-tier: yes.

#### 2.6. **Chile / BCC BDE + Excel BdP tables** — strong access

- BCC at `si3.bcentral.cl/estadisticas/principal1/excel/se/bdp/excel.html` — quarterly Excel.
- BPM6, with computer services explicitly highlighted in 2025-Q1 imports report.
- Sample window 2003+ quarterly.

### Category 3 — Developer-Survey Time Series

#### 3.1. **Stack Overflow Annual Developer Survey** — annual cadence, AI questions added 2023

- **Canonicality**: Industry-standard but private-vendor; not statistical-authority. Extensive global reach (~65,000 to 90,000 respondents/year) including LATAM (Brazil, Mexico, Argentina identified as JetBrains regions).
- **Free-tier**: Yes. Public CSV downloads at `https://survey.stackoverflow.co/datasets/stack-overflow-developer-survey-<YEAR>.zip` for 2017-2025 (verified via WebFetch). No registration, no auth.
- **Sample window**: 2017-2025 (CSV); earlier years available.
- **Cadence**: ANNUAL — fundamental cadence mismatch with Pair D's monthly anchor.
- **N_obs**: 2017-2025 = 9 annual data points → 8 post-lag-1y. **WAY BELOW N_MIN = 75.** Solo-Y unviable.
- **AI-tooling questions**: Added 2023 (so usable AI-specific Y starts 2023-2025 = 3 data points; UNVIABLE).
- **Methodology breaks**: Annual sample-frame variation; not a structural break per se but country-share weights can drift.
- **Recommendation**: NOT a primary or sensitivity Y. Could be used as a *cross-validation reference* for sign-direction sanity checks: if Y_p Section J share is rising in lockstep with Stack Overflow LATAM AI-adoption rates, that's directional confirmation, not a co-test.

#### 3.2. **JetBrains Developer Ecosystem Survey** — annual, LATAM regional cells

- Argentina, Brazil, Mexico identified as separate regions in 2024 survey (23,262 respondents).
- Annual cadence — same N_obs constraint as Stack Overflow.
- Free-tier: aggregate report free PDF; raw data restricted.
- **Recommendation**: NOT a Y candidate; reference only.

#### 3.3. **GitHub Octoverse** — annual, aggregate

- LATAM developer growth ~6 per minute (2024 figure); 80% of new GitHub users use Copilot in their first week (2024 figure).
- Annual report only; raw country-time-series not published.
- **Recommendation**: NOT a Y candidate.

### Category 4 — Proprietary AI-Vendor LATAM Data

- **Anthropic Claude.ai traffic geography** (Semrush, Feb 2026): Brazil 4.02% of claude.ai visits — POINT ESTIMATE, not time-series.
- **OpenAI ChatGPT Plus subscribers**: 50M+ globally Feb 2026; Brazil 5.8% of ChatGPT visits, Mexico 3.6% — POINT ESTIMATES, not time-series.
- App-store revenue data (Sensor Tower, AppMagic): paid services, NOT free-tier.
- Stripe Atlas LATAM AI-SaaS subscription proxy: not public.
- **Recommendation**: NONE viable as Stage-1 β Y. **HALT-and-surface**: this entire category is paywalled or point-estimate-only at free tier.

### Category 5 — Indirect Proxies

#### 5.1. **GitHub commits-per-week from LATAM IPs (BigQuery / GH Archive)** — high-quality monthly proxy

- **Canonicality**: GH Archive captures ~30M events/month (2018+) with hourly snapshots; BigQuery public dataset auto-updated.
- **Free-tier**: 1 TB/month BigQuery free tier; GH Archive raw JSON at gharchive.org no auth.
- **Sample window**: 2011-02 onward (BigQuery dataset start) for events; user country-of-residence is NOT a public field — geolocation must be inferred via commit-author email/profile + IP-derived signals (privacy-redacted in 2017+ for some events).
- **Cadence**: hourly (aggregateable to monthly).
- **N_obs (monthly 2015-2026)**: 134 → comfortable.
- **Methodology breaks**: GH Archive schema changes 2015 (new event types); GitHub IP-redaction 2017 (privacy-rules tightening); LFS adoption 2015. Geolocation methodology MUST be pre-committed (commit-email-domain heuristic vs. profile-self-declared-country).
- **Recommendation**: VIABLE as a monthly indirect proxy IF the spec commits to either (a) profile-declared country (lossy, ~30-40% of users self-declare), (b) commit-email-TLD (.co, .br, .mx, .ar, .pe, .cl) heuristic (also lossy and biased toward institutional contributors). NOT recommended as PRIMARY but workable as an **additional monthly sensitivity** alongside Y_p.

#### 5.2. **Domain registration in LATAM** (whois cadence)

- Free WHOIS APIs unreliable + heavily rate-limited (most LATAM ccTLDs require institutional access). Free-tier-blocked. **HALT-and-surface**.

#### 5.3. **G2 / Capterra LATAM developer-tool review aggregates**

- Aggregated review counts not publicly downloadable as time series. Free-tier-blocked.

#### 5.4. **Meetup.com AI-meetup attendance LATAM cities**

- Meetup API was deprecated 2019 and replaced with paid Pro API. Free-tier-blocked. **HALT-and-surface**.

#### 5.5. **Open-source AI repo contribution from LATAM maintainers**

- Subset of 5.1 (GH Archive) — same caveats apply.

---

## §3. Cross-Country Aggregation Methodology

If the spec elects a **multi-LATAM panel** sensitivity (Y_s3), the recommended structure is:

- **Unit**: country × time (annual for UNCTADstat; quarterly for central-bank BoP).
- **Countries**: Colombia, Mexico, Brazil, Argentina, Peru, Chile (6 cells).
- **Weighting**: equal-weight panel (avoids endogenous-weight fishing) per Y₃ inequality-differential design precedent (`project_y3_inequality_differential_design`).
- **Missing-cell handling**: explicit pre-commit to either (a) drop country-years with NULL EBOPS-9 cell, or (b) impute zero with a missingness-flag dummy. Recommendation: option (a) — drop, do NOT impute, do NOT promote remaining cells without disclosure.
- **Argentina credibility regime control**: pre-registered dummy = 1 for 2007-2015 EPH/INDEC-suspect period × Argentina-only, separately for any Argentina cells. Sensitivity = restrict to non-Argentina 5-country panel.
- **Fixed effects**: country FE always included; time FE optional sensitivity.
- **Standard errors**: cluster by country.

The cross-LATAM Y_s3 panel is **structurally weaker** than the Colombia-only Y_p because (i) annual cadence vs Pair D's monthly anchor, (ii) heterogeneous methodology breaks across 6 statistical agencies, (iii) Argentina credibility caveat. It should NOT be promoted to primary.

---

## §4. Sample Window Proposal

**For PRIMARY Y_p (Colombia GEIH Section J share)**: window pinned to **2015-01 → 2026-03** (latest GEIH-published month).

- Mirror of Pair D Option-α' window per CORRECTIONS-α' (committed 2026-04-28 at spec sha256 `964c62cca…ef659`).
- Rationale (re-stated for transparency, NOT as fishing):
  - Pre-2015: DANE Empalme files for 2010-2014 ship `RAMA4D` with CIIU Rev.3 codes despite column-header showing Rev.4 — this is the pathological-HALT lesson recorded in `feedback_schema_pre_flight_must_verify_values`.
  - 2015-01 onward: DANE-canonical Rev.4 throughout via `RAMA4D_R4` field; no pre-2015 Rev.3 contamination.
  - 2021 Marco-2018 frame change: handled via DANE empalme factor in the existing pipeline (consistent with Pair D Y₁).
- N_obs = 134 post-lag-12.

**For SENSITIVITY Y_s1 (DANE EMS Section J)**: window 2018-01 → 2026-03 (EMS monthly cadence start).

- N_obs = 87 post-lag-12.
- Pre-commit 2020-01 redesign dummy.

**For SENSITIVITY Y_s2 (GEIH Section M share)**: same 2015-01 → 2026-03 window as Y_p.

**For SENSITIVITY Y_s3 (UNCTADstat EBOPS-9 panel)**: 2008-2024 annual.

- N_panel = 6 countries × 17 yrs = 102 cells.

---

## §5. Pre-Commit Recommendation

```text
PRIMARY Y:           Y_p = young-worker (14-28) employment share in
                     CIIU Rev. 4 Section J, Colombia, sourced from
                     DANE GEIH micro-data
SAMPLE WINDOW:       2015-01 → 2026-03 (Pair D Option-α' window)
CADENCE:             monthly (RAMA4D_R4 cells aggregated by month)
TRANSFORMATION:      logit(Y_p) (analog to Pair D; bounded in [0,1])
SIGN EXPECTATION:    β > 0 at conventional significance
N_OBSERVATIONS:      134 post-lag-12

SENSITIVITY 1 (Y_s1): DANE EMS Section J nominal-income index, CO,
                      monthly, 2018-01 → 2026-03, base 2018=100,
                      log(index) transform, 2020-01 redesign dummy,
                      N=87 post-lag-12

SENSITIVITY 2 (Y_s2): GEIH young-worker share in Section M
                      (Profesionales / científicas / técnicas), CO,
                      monthly, 2015-01 → 2026-03, logit transform,
                      N=134 post-lag-12

SENSITIVITY 3 (Y_s3): UNCTADstat EBOPS-9 (Telecom + Computer +
                      Information services) IMPORTS, 6-country LATAM
                      panel (CO/MX/BR/AR/PE/CL), annual 2008-2024,
                      log transform, country FE, AR credibility
                      dummy 2007-2015, N_panel=102
```

**Pre-pinned hypothesis (anti-fishing): NO β preliminaries reported. The β regression is deferred to a v1.5-methodology-equivalent stage; this memo pre-pins Y selection only.**

**Anti-fishing carry-forward from Pair D**: SUBSTRATE_TOO_NOISY exception (§3.5 Pair D spec) carries to dev-AI-cost iteration unchanged. Convex-payoff insufficiency caveat (§11.A from Phase-A.0 Rev-2) carries forward: simple OLS β-FAIL on Y_p does NOT close the iteration; spec author may pre-authorize escalation to quantile regression / GARCH-X / lower-tail evidence per Pair D escalation precedent.

---

## §6. HALT-and-Surface Candidates

The following resources were NOT viable at free tier as of 2026-05-04. Spec author MUST treat each as explicit-null unless paid-tier upgrade is approved:

1. **Banrep `https://www.banrep.gov.co/es/estadisticas/balanza-pagos`** — WebFetch 404. URL likely changed. Spec must reverify via Banrep main statistics portal browse OR pivot to UNCTADstat for Banrep BoP-imports series. NOT a hard blocker (alternate routes exist) but flagged for direct verification before pipeline implementation.
2. **UNCTADstat data viewer `https://unctadstat.unctad.org/datacentre/reportInfo/US.TradeServCatTotal`** — WebFetch 403 (likely needs JavaScript / session). Direct browser download confirmed working in past WebSearch results. Pipeline implementation must use the data centre's CSV export feature, not direct URL fetch.
3. **DANE EMS bulletin Section J detail extraction** — PDF binary content not text-readable via WebFetch (would require PDF parsing or Excel annex download). NOT a blocker; the Excel annex `.xlsx` files at `/files/operaciones/EMS/anex-EMS-<mmm><yyyy>.xlsx` are confirmed available and are the right artifact.
4. **Stack Overflow / GitHub Octoverse / JetBrains country-time-series cross-tabs** — annual cadence is itself the blocker; not paywalled but unsuitable for monthly β.
5. **Anthropic / OpenAI / Cursor LATAM-revenue disclosures** — point estimates only; not time series. Free-tier sufficient for sanity checks but NOT for Y construction.
6. **Sensor Tower / AppMagic LATAM AI-app revenue** — paid service. Free-tier-blocked.
7. **Stripe Atlas LATAM data** — internal Stripe service, not public.
8. **Meetup.com API** — deprecated 2019; paid replacement. Free-tier-blocked.
9. **WHOIS APIs for LATAM ccTLD AI-related domain registrations** — heavily rate-limited at free tier. Effectively blocked.
10. **Argentina EPH 2007-2015 INDEC credibility window** — accessible but ANALYTICALLY UNRELIABLE per documented credibility crisis. HALT-and-surface for any Argentina cell crossing this window.

---

## §7. Sources

### DANE (Colombia)
- DANE GEIH catalog (per-year IDs verified in Pair D memo `2026-04-27-dane-geih-y-feasibility.md`): https://microdatos.dane.gov.co/index.php/catalog/MICRODATOS
- DANE GEIH 2024-2026: catalog/819, /853, /900
- DANE EMS landing: https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-mensual-de-servicios-ems
- DANE EMS Históricos: https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-mensual-de-servicios-ems/encuesta-mensual-de-servicios-ems-historicos
- DANE EMS metodología: https://www.dane.gov.co/files/investigaciones/fichas/comercio_servicios/ems/DSO-EMS-MET-001-V1.pdf
- DANE EMCES: https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-mensual-de-comercio-exterior-de-servicios-emces
- DANE EMCES históricos: https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-mensual-de-comercio-exterior-de-servicios-emces/encuesta-mensual-de-comercio-exterior-de-servicios-emces-informacion-historica
- DANE MTCES históricos: https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/muestra-trimestral-de-comercio-exterior-de-servicios/muestra-trimestral-de-comercio-exterior-de-servicios-mtcs-informacion-historica
- DANE EAS: https://www.dane.gov.co/index.php/estadisticas-por-tema/servicios/encuesta-anual-de-servicios-eas
- DANE CIIU Rev. 4 A.C.: https://clasificaciones.dane.gov.co/ciiu4-0/ciiu4_dispone
- DANE ICT statistics: https://www.dane.gov.co/index.php/en/statistics-by-topic-1/technology-and-innovation/information-and-communication-technology-ict
- DANE Service Annual Survey methodology: https://www.dane.gov.co/files/investigaciones/comercio_servicios/eas/service_annual_survey_methodology.pdf
- DANE EMS Mar 2025 bulletin: https://www.dane.gov.co/files/operaciones/EMS/bol-EMS-mar2025.pdf

### Banrep (Colombia)
- Banrep Balanza de Pagos glossary: https://www.banrep.gov.co/es/glosario/balanza-pagos
- Banrep BPM6 transition note 2014: https://www.banrep.gov.co/es/noticias/evolucion-balanza-pagos-comunicado-27-06-2014
- Banrep services-trade strengthening: https://www.banrep.gov.co/es/banco-republica-fortalece-medicion-del-comercio-exterior-servicios-reportado-balanza-pagos-colombia
- Banrep BoP technical document: https://www.banrep.gov.co/sites/default/files/documento_tecnico_balanza_pagos.pdf
- Banrep BoP Q1-2025 informe: https://www.banrep.gov.co/sites/default/files/informeBOP202501.pdf
- Banrep BoP English Q1-2024 report: https://www.banrep.gov.co/en/publications-research/report-balance-payments/first-quarter-2024

### INEGI (Mexico)
- INEGI ENOE: https://www.inegi.org.mx/programas/enoe/15ymas/
- INEGI EMS Series 2018: https://www.inegi.org.mx/programas/ems/2018/
- INEGI BIE API documentation: https://www.inegi.org.mx/servicios/api_indicadores.html
- INEGIpy Python package: https://pypi.org/project/INEGIpy/
- INEGI ENDUTIH 2024 (TIC en hogares): https://www.inegi.org.mx/rnm/index.php/catalog/1102

### Banxico (Mexico)
- Banxico SIE BPM6 BoP CA410 summary: https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=1&accion=consultarCuadroAnalitico&idCuadro=CA410&locale=en
- Banxico CE174 BoP information structure: https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=1&idCuadro=CE174

### IBGE (Brazil)
- IBGE PNAD Contínua: https://www.ibge.gov.br/estatisticas/sociais/trabalho/9173-pesquisa-nacional-por-amostra-de-domicilios-continua-trimestral.html
- IBGE PMS landing: https://www.ibge.gov.br/estatisticas/economicas/servicos/9229-pesquisa-mensal-de-servicos.html
- IBGE PMS FTP: https://ftp.ibge.gov.br/Comercio_e_Servicos/Pesquisa_Mensal_de_Servicos/
- IBGE SIDRA PMS tables: https://sidra.ibge.gov.br/pesquisa/pms/tabelas

### BCB (Brazil)
- BCB Balanço de Pagamentos BPM6 dados abertos: https://dadosabertos.bcb.gov.br/dataset/?tags=Balan%C3%A7o+de+Pagamentos+-+BPM6
- BCB SGS portal: https://www3.bcb.gov.br/sgspub/
- BCB serviços mensal receita: https://dadosabertos.bcb.gov.br/dataset/22720-servicos---mensal---receita

### INDEC + BCRA (Argentina)
- INDEC EPH: https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58
- BCRA balance cambiario methodology: https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/Metodologia-del-balance-cambiario.pdf
- CESSI talent + employment report Jul-2025: https://cessi.org.ar/wp-content/uploads/2025/08/CESSI-OPSSI-Reporte-de-los-principales-indicadores-de-la-industria-del-Software-con-Foco-en-Talento_Julio-2025.pdf

### INEI + BCRP (Peru)
- INEI ENAHO microdata portal: https://proyectos.inei.gob.pe/iinei/srienaho/index.htm
- INEI TIC en hogares boletines: https://m.inei.gob.pe/biblioteca-virtual/boletines/tecnologias-de-la-informaciontic/1/
- BCRP balanza de pagos series: https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/balanza-de-pagos
- BCRP guía metodológica balanza de pagos: https://www.bcrp.gob.pe/docs/Publicaciones/Guia-Metodologica/Guia-Metodologica-12.pdf

### INE + BCC (Chile)
- INE ENE landing: https://www.ine.gob.cl/encuesta-empleo-contexto-covid-19/para-que-sirve
- INE ENE Banco de Datos: https://bancodatosene.ine.cl/
- BCC BdP Excel: https://si3.bcentral.cl/estadisticas/principal1/excel/se/bdp/excel.html
- BCC BDE base de datos estadísticos: https://si3.bcentral.cl/siete
- BCC BdP first-quarter-2025 report: https://www.bcentral.cl/documents/33528/7225269/Balanza+de+Pagos+Primer+Trimestre+2025.pdf

### International / harmonized
- UNCTADstat data centre (BPM6): https://unctadstat.unctad.org/datacentre
- UNCTAD Trade in Services by category handbook: https://stats.unctad.org/handbook/Services/ByCategory.html
- UNCTAD ICT services + ICT-enabled note: https://unctad.org/system/files/official-document/tn_unctad_ict4d03_en.pdf
- OECD-WTO BaTIS methodology BPM6: https://www.oecd.org/content/dam/oecd/en/data/methods/OECD-WTO-Balanced-Trade-in-Services-database-methodology-BPM6.pdf
- IMF C.6 Trade in Services Classifications: https://www.imf.org/-/media/Files/Data/Statistics/BPM6/CATT/c6-trade-in-services-classifications.ashx
- IMF SDDS Colombia labor market employment: https://dsbb.imf.org/sdds/dqaf-base/country/COL/category/EMP00
- World Bank IPUMS Colombia 2020-Q1 catalog: https://microdata.worldbank.org/index.php/catalog/7662

### Developer surveys
- Stack Overflow Developer Survey 2025: https://survey.stackoverflow.co/2025/
- Stack Overflow 2025 AI section: https://survey.stackoverflow.co/2025/ai/
- Stack Overflow 2025 results blog: https://stackoverflow.blog/2025/12/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here/
- Stack Overflow Developer Survey landing (CSV downloads 2017-2025): https://survey.stackoverflow.co/
- JetBrains DevEcosystem 2024: https://www.jetbrains.com/lp/devecosystem-2024/
- JetBrains DevEcosystem 2025 (AI section): https://devecosystem-2025.jetbrains.com/artificial-intelligence
- GitHub Octoverse 2025: https://octoverse.github.com/
- GitHub Octoverse 2024 blog: https://github.blog/news-insights/octoverse/octoverse-2024/

### Indirect proxies / context
- GH Archive: https://www.gharchive.org/
- GitHub on BigQuery (Google Cloud blog): https://cloud.google.com/blog/topics/public-datasets/github-on-bigquery-analyze-all-the-open-source-code
- Statista LATAM BPO forecast: https://www.statista.com/outlook/tmo/it-services/business-process-outsourcing/mexico
- Statista Colombia BPO key figures: https://www.statista.com/statistics/1221688/colombia-bpo-market-key-figures/
- Brasscom IT-talent demand 2025: https://tiinside.com.br/en/01/12/2021/estudo-da-brasscom-aponta-demanda-de-797-mil-profissionais-de-tecnologia-ate-2025/
- Anthropic statistics 2026 (Business of Apps): https://www.businessofapps.com/data/claude-statistics/
- ChatGPT global statistics 2025-2026: https://nerdynav.com/chatgpt-statistics/

### Pair D (parent iteration) — local references
- Pair D Y feasibility memo (FORMAT PRECEDENT): `contracts/.scratch/2026-04-27-dane-geih-y-feasibility.md`
- CORRECTIONS-θ memo (off-chain Y mandate for dev iteration): `contracts/.scratch/path-b-stage-2/phase-1/corrections_theta_substrate_scope_clarification.md`
- Abrigo Operating Framework: `CLAUDE.md` (dev worktree root)
- Pair D PASS verdict: spec sha256 `964c62cca…ef659`; β=+0.137, p=1.46e-08; project memory `project_pair_d_phase2_pass`

---

**End of feasibility assessment.** No code generated, no spec content authored, no β regression run, no tracked files modified. Output written to `contracts/.scratch/` per project memory convention. **Verdict: FEASIBLE** with PRIMARY Y_p (GEIH Section J share) + 3 sensitivities pre-pinned. Spec author may consume §5 directly to author the dev-AI-cost Stage-1 β spec.
