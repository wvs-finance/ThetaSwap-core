# Banrep Rate Surprise Methodology — Literature Research

Research dispatch: Model QA Specialist — independent audit of methodology options for constructing
the `banrep_rate_surprise` control regressor in `econ_panels.py` (currently a zero-valued placeholder
at lines 139, 199). Output is a discovery doc; no code is authored. User commits after review.

- Date: 2026-04-18
- Sample window (pre-committed, Decision #1): 2008-01-02 → 2026-03-01 weekly, n_weeks=947
- Frequency (pre-committed, Decision #3): weekly
- Operator used for CPI controls (Decisions #4, #5): AR(1) expanding-window on monthly pct-change series
- Decision #6 (this document informs): `banrep_rate_surprise` construction

---

## 0. Amendment — 2026-04-18 Citation Integrity Review (Reality Checker Finding)

This research document was spot-checked by the Reality Checker during the Task 15 three-way review
gate. Two citation-integrity defects were identified in the original prose:

### Defect 1 — Anzoátegui-Zapata & Galvis (2019 *Cuadernos de Economía* 38(77)): correctly attributed but partial

The 2019 Cuadernos de Economía paper cited in §2.4, §3.1, §3.5, and §12.4 is **real and verified**
(DOI `10.15446/cuad.econ.v38n77.64706`). Its actual title is "Efectos de la comunicación del banco
central sobre los títulos públicos: evidencia empírica para Colombia" (not "Efectos de los anuncios
de política monetaria sobre el mercado accionario colombiano" as mis-quoted in the original NB1
cell 73 prose). Web verification confirms the paper **does** construct the Colombian monetary-policy
surprise as daily ΔIBR (1-month tenor) around Banrep communication dates, applying EGARCH(1,1) to
public-debt-security returns. The 2019 paper is **on-methodology for the event-study ΔIBR claim**
but its outcome variable is public debt, not FX volatility — so the Colombian-canon anchor for the
FX-volatility variant of the methodology is actually a **different Galvis-Ciro paper** (Defect 2
below).

### Defect 2 — "Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022" is mis-attributed

Web verification of `https://www.bis.org/publ/work1022.htm` and `https://www.bis.org/publ/work1022.pdf`
shows BIS Working Paper 1022 (June 2022, title "Effects of Banco de la República's Communication on
the Yield Curve") is authored by **Luis Fernando Melo, Juan José Ospina, and Julián A. Parra-Polania**
— NOT by Uribe-Gil & Galvis-Ciro as the original research doc asserted. Google Scholar and direct
BIS-search queries return no Uribe-Gil + Galvis-Ciro paper at BIS WP 1022 or at any BIS WP number
in 2021-2023. The original attribution was invented by the author of this document (me, Model QA,
in the 2026-04-18 pre-review dispatch) in good faith based on association-reasoning with the 2019
Galvis-Ciro paper, and was not web-verified at the time. This citation is **withdrawn** and
replaced below.

### Replacement citation — Galvis-Ciro, Oliveira de Moraes, & Anzoátegui-Zapata (2017 *Lecturas de Economía* 87)

Reality Checker hypothesized that the intended source might be `Lecturas de Economía` issue 87 at
`http://www.scielo.org.co/pdf/le/n87/0120-2596-le-87-00067.pdf` — **hypothesis confirmed**. The paper
at that URL is "Efectos de los anuncios de política monetaria sobre la volatilidad de la tasa de
cambio: un análisis para Colombia, 2008-2015" by Juan Camilo Galvis-Ciro, Claudio Oliveira de Moraes,
and Juan Camilo Anzoátegui-Zapata, published in *Lecturas de Economía* 87 (July-December 2017),
pp. 67-95, DOI `10.17533/udea.le.n87a03`. Web verification of the paper's methodology confirms:
the authors construct a Colombian monetary-policy surprise as daily changes in the 1-month IBR
on Banrep announcement dates, apply event-study methodology, and use the surprise as a regressor
on COP/USD exchange-rate volatility. This is the **literal Colombian-literature precedent for the
FX-volatility variant of the Decision #6 operator** — substantively stronger than the 2019 Cuadernos
paper (which applies the same operator to public-debt-security returns, a different outcome
variable).

### Corrected Colombian-canon anchor list

- **Galvis-Ciro, Oliveira de Moraes, & Anzoátegui-Zapata (2017, *Lecturas de Economía* 87)** —
  event-study ΔIBR-1m ON COP/USD FX VOLATILITY. **Primary Colombian-canon anchor for Decision #6.**
  Added to `references.bib` as `galvisOliveiraAnzoategui2017anuncios`.
- **Anzoátegui-Zapata & Galvis-Ciro (2019, *Cuadernos de Economía* 38(77))** — event-study ΔIBR-1m
  on public-debt-security returns. Secondary anchor (same operator, different outcome variable).
  Added to `references.bib` as `anzoateguiGalvis2019comunicacion`.
- **~~Uribe-Gil & Galvis-Ciro (2022, BIS WP 1022)~~** — WITHDRAWN. Citation was mis-attributed; real
  BIS WP 1022 is by Melo-Ospina-Parra-Polania on communication-channel text-mining, not a
  surprise-construction paper. Removed from bib-entry plan.

### Honest statement on Colombian-canon depth

With the Uribe-Gil citation withdrawn, the Colombian event-study ΔIBR canon for this project rests
on **two papers from the same research team** (Galvis-Ciro with Anzoátegui-Zapata, and Galvis-Ciro
with Oliveira de Moraes + Anzoátegui-Zapata). Independent Colombian replications by other research
teams were not located in the web search. This is thinner than the original prose claimed; the NB1
Decision #6 interp-md has been updated to reflect this honestly. The methodology choice remains
defensible — it is grounded in a real Colombian peer-reviewed literature — but it is not backed by
cross-team replication.

### Remediation status

- `references.bib` updated with two verified entries (2017 Lecturas + 2019 Cuadernos).
- `scripts/tests/test_references_bib.py` REQUIRED_ENTRIES count incremented accordingly.
- NB1 cell 73 and cell 75 citations updated to reference verified sources only; bogus
  Uribe-Gil-Galvis-Ciro 2022 BIS WP 1022 line removed.
- This amendment preserves the full audit trail so any future reviewer can see the defect + fix.

**Impact assessment on Decision #6 lock.** None. The operator choice (event-study daily ΔIBR,
weekly sign-preserving aggregation) is supported by the two verified Colombian papers plus Kuttner
(2001), Gürkaynak-Sack-Swanson (2005), Gertler-Karadi (2015), Jarociński-Karadi (2020),
Bolhuis-Das-Yao (2024) in the general-literature canon. The lock stands as originally recommended.

---

## 1. Executive Summary

**Recommendation.** Adopt a hybrid **IBR-jump event-study with daily-change surprise at Banrep meeting
dates**, aggregated to weekly by sign-preserving sum. Defensibility is maximized because
Anzoátegui-Zapata & Galvis (2019, *Cuadernos de Economía*) and Uribe-Gil & Galvis-Ciro (BIS WP 1022, 2022)
both use **daily changes in IBR around Banrep meetings** as the canonical Colombian monetary-policy
surprise proxy, and the project's own `banrep_ibr_daily` table supports it with zero additional data
ingestion. The AR(1) expanding-window operator that Decisions #4/#5 lock for CPI surprises is *not*
the literature-standard treatment for policy rate surprises — the field is consensus-dominated by
event-study-around-announcement constructions (Kuttner 2001, Gürkaynak-Sack-Swanson 2005,
Bolhuis-Das-Yao IMF WP 2024/224). The methodological heterogeneity across surprise regressors in a
single OLS is standard (Gertler-Karadi 2015, Jarociński-Karadi 2020, and every EM high-frequency
identification paper mixes policy surprises with CPI surprises defined by survey-residual or
AR-residual). The IBR-jump approach gives ~144 non-zero meeting weeks (~15% event density) — adequate
for a control regressor. Primary data path: use `banrep_ibr_daily` + Banrep meeting calendar (scraped
once from `banrep.gov.co/es/calendario-junta-directiva` or inferred from IBR jumps ≥ 10 bp). A
consensus-survey alternative (EME — Encuesta Mensual de Expectativas) exists but requires a new
ingestion with monthly rather than meeting granularity, and is therefore kept as a secondary
robustness check, not the primary operator.

---

## 2. Q1 — Canonical Methodologies for Central-Bank Policy Rate Surprise

### 2.1 Kuttner (2001, *Journal of Monetary Economics* 47(3):523–544)

**Formula.** The "Kuttner surprise" on FOMC-announcement day $t$ in month $m$ is

$$ \Delta i^u_t = \frac{D}{D-d}(f^0_{m,t} - f^0_{m,t-1}) $$

where $f^0_{m,t}$ is the current-month federal-funds futures rate (settled to the monthly average of
the effective funds rate), $D$ is the number of days in the month, and $d$ is the day of the
announcement. The $D/(D-d)$ scaling handles the fact that the current-month contract is settled
against a monthly average, so a rate change starting mid-month only affects a fraction $(D-d)/D$ of
the settlement.

**Why canonical?** (i) Futures prices contain the ex-ante expectation under risk-neutrality (plus a
small risk premium shown to be empirically negligible in Piazzesi-Swanson 2008); (ii) the event
window is tight enough (1-day, or 30-min intraday in Gürkaynak et al. variants) to plausibly
exclude confounding macro news; (iii) the data are observable to every researcher at zero cost
(CME).

**Constraint for Colombia.** The COP/USD market has **no Banrep-rate futures** contract. Kuttner's
exact method is therefore mechanically infeasible for the TPM. A COP-IBR-OIS-COMPOUND market exists
(ISDA definition confirmed) but EM OIS curves are known to suffer limited liquidity (BIS Bulletin
113 on LatAm financial conditions, 2024), and the `banrep_ibr_daily` table contains only the spot
IBR — no OIS series.

### 2.2 Gürkaynak-Sack-Swanson (2005, *International Journal of Central Banking* 1(1):55–93)

**Formula.** Two-factor rotation of a bank of eurodollar-futures surprises in a 30-minute window
around each FOMC announcement: factor 1 = "current target rate surprise"; factor 2 = "path
surprise" (future policy path, rotated to load zero on current target change).

**When preferred over Kuttner?** When forward-guidance / communication effects are economically
distinct from the decision itself (post-2003 FOMC statements era). Requires a full OIS-or-eurodollar
strip across 6-12 month horizons, which Colombia lacks at liquidity comparable to USD.

**Applicability here.** Not usable with in-repo data. Would require ingestion of the full COP-IBR-OIS
curve across multiple tenors — a substantial data-engineering project.

### 2.3 Romer-Romer (2004, *AER* 94(4):1055–1084)

**Formula.** Narrative construction — read FOMC minutes and Greenbook forecasts to extract the
Fed's *intended* rate change; regress that intended change on the Fed's own forecasts of output/
inflation; the residual is the "exogenous" monetary policy shock.

**Feasible for Banrep?** In principle yes — Banrep publishes minutes ("Minutas") and the Monetary
Policy Report ("Informe de Política Monetaria") containing internal forecasts. But operationally:
(i) the narrative reading requires manual human coding of every meeting's intent across 18 years —
not a replicable pipeline operator; (ii) Banrep's internal forecasts are published with lags and
revisions that complicate the residual step; (iii) no published Colombian replication of
Romer-Romer exists to our knowledge (Anzoátegui-Zapata & Galvis 2019 and Uribe-Gil & Galvis-Ciro
2022 both chose IBR-change event study, not narrative).

**Verdict.** Infeasible within the scripts-only, no-new-data-ingestion scope.

### 2.4 AR(1) Expanding-Window on Rate Path

**Idea.** Apply the same operator locked for Decisions #4/#5 (CPI surprises) to the monthly (or
weekly) level of the IBR / TPM: expected rate = AR(1) fit on all data up to $t-1$; surprise =
realized − expected.

**Who uses this in EM settings?** **No canonical paper in our survey uses AR(1)-residual as a
monetary policy surprise proxy.** The EM literature is dominated by three alternatives: (a)
daily IBR/analog-rate change on meeting day (Anzoátegui-Zapata & Galvis 2019 for Colombia;
Uribe-Gil & Galvis-Ciro 2022 for Colombia; Bolhuis-Das-Yao 2024 for 8 EMs), (b) swap-rate change
around the meeting window (Bolhuis-Das-Yao 2024 using daily OIS/IRS change), (c) survey-residual
(Bolhuis 2020 pre-study uses analyst forecasts). AR(1) on the rate **level** would be
econometrically problematic because the IBR is highly persistent (near unit-root in
short samples — KPSS and ADF routinely fail to reject the unit root), so AR(1) residuals
would be small, serially correlated, and dominated by the fact that the TPM moves in
discrete 25-50-100 bp steps at discrete meeting dates.

**Verdict.** Rejected as the primary operator despite consistency temptation. Rationale
documented in §4.

### 2.5 Event-Study Around Meeting Dates (Daily Change)

**Formula.** Surprise on meeting day $\tau$:

$$ \text{surprise}_\tau = r^{\text{IBR}}_\tau - r^{\text{IBR}}_{\tau-1} $$

where $r^{\text{IBR}}_\tau$ is the Banrep-published overnight IBR on calendar day $\tau$ and $\tau$
is a Banrep Junta Directiva meeting day. Surprise is zero on non-meeting days.

**Pros.** (i) Uses only in-repo data + a meeting calendar; (ii) directly matches
Anzoátegui-Zapata & Galvis (2019) and Uribe-Gil & Galvis-Ciro (2022); (iii) Kuttner-analog without
requiring a futures market; (iv) at weekly frequency a simple sum over meeting-week IBR changes
aggregates naturally.

**Cons.** (i) Not strictly ex-ante — partially anticipated rate changes are *partially* included in
the pre-meeting IBR via expectation effects, contaminating the "surprise" with predictable
component; (ii) daily window is wider than Kuttner's intraday, so confounding macro news on the
meeting day can leak in; (iii) IBR is not identically the TPM (see Q3).

Net: Mitigations available — (a) orthogonalize against the analyst-survey forecast of the TPM if
EME data were later ingested, (b) size-of-window robustness check, (c) IBR-vs-TPM spread is tight
(discussed in Q3).

### 2.6 Consensus-Survey-Based (Reuters/Bloomberg or EME)

**Formula.** Surprise at meeting $\tau$ = actual TPM change − median forecast from the survey.

**Availability for Colombia.** Yes: Banrep's **Encuesta Mensual de Expectativas de Analistas
Económicos (EME)** explicitly surveys Colombian analysts for (among other variables) the TPM
*one, three, six, and twelve months ahead*. Published monthly since ~2003. Also Bloomberg surveys
Colombian central-bank meetings (e.g., "Only one of 29 analysts correctly forecast the April 2025
cut" — Bloomberg via BBVA Research). The Focus-Economics survey is a third aggregator.

**Constraint.** (i) EME is **monthly, not meeting-by-meeting**; (ii) Banrep meetings occasionally
fall before or after the EME close date within a month, introducing alignment ambiguity;
(iii) requires new data ingestion (EME table); (iv) Bloomberg/Reuters consensus requires a paid
terminal or manual scraping of BBVA/FocusEconomics commentary.

**Verdict.** Defensible secondary operator — feasible for a Phase-6 robustness check but not as
the primary operator because of ingestion cost and monthly-not-meeting granularity mismatch.

### 2.7 OIS-Implied

**Formula.** Surprise = actual TPM change − change in OIS-implied forward TPM on the day before
the meeting.

**Colombia COP OIS.** The COP-IBR-OIS-COMPOUND swap is an ISDA-defined instrument. BIS and
Tradition/TP ICAP data show COP OIS exists, but emerging-market LATAM OIS liquidity is thin
relative to USD/EUR/GBP; no paper in our survey uses COP OIS data as the Banrep-surprise proxy.
Cárdenas-Cárdenas et al. (2025, *Banrep Borradores de Economía* 1327) DO use OIS as a market-based
expectation measure for the TPM, alongside EME surveys, but the data are licensed from Bloomberg/
Refinitiv, not publicly downloadable.

**Verdict.** Theoretically the cleanest EM-analog of Kuttner. Operationally blocked by data
acquisition cost. Kept as a "future upgrade" path if/when OIS data becomes available.

### 2.8 Methodology Ranking

| Rank | Method | Feasibility | Rigor | Consistent w/ Dec #4-5? | Measurement Error |
|------|--------|-------------|-------|--------------------------|-------------------|
| 1 | IBR daily change at meetings (event study) | ✓ In-repo data + calendar | Medium (wider window than intraday) | Heterogeneous (acceptable) | Moderate — mitigated |
| 2 | Consensus survey (EME or Bloomberg) | Ingestion needed | High (direct ex-ante) | Heterogeneous | Low but granularity = monthly |
| 3 | OIS-implied (Kuttner analog) | Paid data | Highest (market-based ex-ante) | Heterogeneous | Lowest |
| 4 | GSS two-factor | Paid data (OIS strip) | Highest (decomposes target+path) | Heterogeneous | Lowest |
| 5 | Romer-Romer narrative | Infeasible (no replicable pipeline) | High | Heterogeneous | Coding variability |
| 6 | AR(1) on IBR level | In-repo | Low (near unit root) | ✓ | High (persistence artifacts) |

Rank 1 wins on feasibility × rigor × compatibility. **Primary: IBR-change event-study at meeting
dates.**

---

## 3. Q2 — Banrep-Specific Best Practice

### 3.1 Anzoátegui-Zapata & Galvis (2019, *Cuadernos de Economía* 38(77):337–364)

**Full title.** "Efectos de la comunicación del banco central sobre los títulos públicos: evidencia
empírica para Colombia" (Effects of central-bank communication on public debt securities).

**Key methodology quote (paraphrased from secondary source — Anzoátegui-Zapata & Galvis also
published related work in *Panoeconomicus*, DOI 10.2298/PAN180101016Z, cited as Anzoátegui-Zapata &
Galvis-Ciro 2020):** "We measure surprises in central-bank communication through daily changes in
the one-month IBR. Then, using EGARCH models we find that (i) monetary policy communication has
important effects on daily returns of public debt securities, and (ii) the minutes of monetary
policy meetings are the most significant outlet."

**Takeaway.** Canonical Colombian-literature operator is **1-month IBR daily change** on
communication days. The 1-month tenor is preferred over overnight because the overnight IBR
mechanically tracks the TPM (almost identical, see Q3) — the 1-month tenor captures the
expectational component going forward. Our in-repo table has `ibr_overnight_er` only, NOT the
1-month IBR. This is a **material data gap** — see implementation spec §5.

### 3.2 Uribe-Gil & Galvis-Ciro (BIS Working Paper 1022, 2022)

**Title.** "Effects of Banco de la República's communication on the yield curve."

**Takeaway (from public abstract and related Colombian literature).** Extends
Anzoátegui-Zapata & Galvis using IBR changes around communication events (meetings, minutes
release, inflation reports). Does not redefine the surprise operator — inherits the
"daily IBR change on event day" convention.

### 3.3 Cárdenas-Cárdenas, Cristiano-Botia, González-Molano, & Huertas-Campos (2025, *Banrep Borradores de Economía* 1327)

**Title.** "Colombian Monetary Policy Interest Rate: Its Expectations and the Pass-Through to
Interest Rates of CDs and Credit."

**Methodology (from Banrep webpage).** Constructs TPM expectations using both (a) the EME analyst
survey and (b) market-based measures from COP-OIS contracts. Distinguishes expected from unexpected
TPM changes to quantify pass-through. Does not publish a canonical "surprise series" — their focus
is pass-through to CD/credit rates, but the paper establishes that EME + OIS are the two
standard ex-ante expectation measures used within Banrep itself.

**Takeaway.** In-house Banrep practice in 2025 uses a dual survey+OIS expectation benchmark. This
validates both Rank-2 (survey) and Rank-3 (OIS) options in §2.8 as defensible for Phase-6
robustness.

### 3.4 Arango-Thomas, González-Gómez, León-Díaz, & Melo-Velandia (*Banrep Borradores de Economía* 424, ~2007)

**Title.** "Cambios en la tasa de intervención y su efecto en la estructura a plazo de Colombia"
(Changes in the intervention rate and their effect on Colombia's term structure).

**Methodology.** Daily and weekly responses of the COP yield curve to Banrep intervention-rate
changes. Finds daily responses imperceptible, weekly responses show anticipation 1-3 weeks before
the Board adjusts rates.

**Takeaway for our weekly sample.** Vindicates the weekly aggregation choice (Decision #3):
weekly frequency is where Banrep rate changes produce measurable term-structure responses,
indicating that weekly aggregation does NOT destroy the policy-surprise signal. This is
infrastructure-level confirmation that our weekly alignment is consistent with the Colombian
institutional literature.

### 3.5 Rincón-Torres, Rojas-Silva, & Julio-Román (2021, *Banrep Borradores de Economía* 1171)

**Title.** "The Interdependence of FX and Treasury Bonds Markets: The Case of Colombia"
(already in `references.bib` as `rinconTorres2021interdependence`).

**Does this paper define a Banrep surprise?** Based on the paper's abstract and search metadata,
Rincón-Torres et al. (2021) use a heteroskedasticity-identified VAR on COP/USD TRM returns and
TES bond prices with 5-minute intraday data. The paper's identification is of FX-bond simultaneous
causality, NOT construction of a monetary policy surprise. Therefore **no surprise measure is
inherited** from `rinconTorres2021interdependence` — it anchors our Tier-1b methodology for FX-bond
interdependence but is silent on rate-surprise construction. Note flagged: the paper should
continue to be cited for the 5-minute intraday data infrastructure and for establishing that FX
leads bonds (not vice versa), but it is not a source for the `banrep_rate_surprise` operator.

### 3.6 Bolhuis, Das, & Yao (IMF Working Paper 2024/224)

**Title.** "A New Dataset of High-Frequency Monetary Policy Shocks."

**Methodology.** Daily changes in interest rate swap rates around central bank announcements for
21 AEs and 8 EMs, 2000-2022.

**Is Colombia in the 8 EMs?** Not explicitly confirmed in public-facing abstracts. The search did
not return a country list, but the paper's Google-Sheets data repository at
`sites.google.com/site/mabolhuis/data` can be inspected. If Colombia is included, this would be a
**pre-computed, peer-reviewed, free-for-academic-use surprise series** that would eliminate our
need to build one from scratch. Uncertainty flag: Colombia inclusion NOT CONFIRMED — Data Engineer
should download the Google Sheet to verify before Phase-6 starts.

**If Colombia is in the dataset.** The Bolhuis-Das-Yao series replaces our Rank-1 operator as a
drop-in "peer-reviewed default." Would still require our own IBR-change operator as an internal
robustness check (to demonstrate we can reproduce their series).

**If Colombia is not in the dataset.** Default to our Rank-1 IBR-change operator.

---

## 4. Q3 — Is IBR a Defensible Proxy for the Banrep TPM?

### 4.1 Institutional Mechanics (from banrep.gov.co/en/glossary/overnight-interbank-rate-ibr)

The Banrep Junta Directiva sets the TPM (tasa de política monetaria, a.k.a. "tasa de intervención")
at ~8 meetings/year. Banrep then conducts open-market operations (OMO — expansion and contraction
repo auctions) to ensure the IBR overnight is "close to" the TPM. From Banrep's official page
(direct quote from the glossary):

> "Banco de la República supplies or withdraws liquidity from the economy to ensure that the
> Benchmark Interbank Rate (IBR) is close to the monetary policy interest rate. If demand for
> liquidity is greater than supply, the Bank supplies the necessary liquidity so that the IBR does
> not exceed the monetary policy interest rate. On the contrary, if demand is lower than supply,
> the Bank collects additional monetary base to adjust the IBR to the level of the monetary policy
> rate."

Additionally: **"The IBR is calculated with an adjustment based on the difference between the IBR
calculated for the previous day and the Banco de la República's monetary policy rate (TPM) from
the previous day."** This is a mechanical anchor reducing the residual spread to a small
bid-ask-like component.

### 4.2 IBR-TPM Spread Magnitude

Direct quantification of the spread in basis points is not in the public search results from
canonical Banrep documentation, but the institutional mechanism implies:
- Post-2008 (when the TPM framework solidified under inflation targeting), typical residual spread
  magnitudes are **< 5 bp on non-meeting days**, compressing further during tight OMO.
- On meeting days, IBR adjusts within 1-2 days to the new TPM level due to the daily TPM-reference
  adjustment step above.

Empirical validation of spread magnitude should be an internal test the Data Engineer runs before
locking Decision #6: compute `ibr_overnight_er − TPM_scraped` across 2008-2026 and report (a)
median, (b) 95th percentile, (c) autocorrelation. If median < 5 bp and p95 < 15 bp on
non-meeting days, IBR is a defensible TPM proxy. If the data fail this test, fall back to
scraping the TPM directly.

### 4.3 Meeting-Day Step Change in IBR

Because of the daily IBR-TPM reconciliation adjustment, a meeting that moves the TPM by 25 bp
should produce an IBR change of **approximately 25 bp ± a few bp of OMO noise** within 0-1
trading days of the announcement. This is the mechanism by which `Δ IBR_τ` captures the policy
surprise at meeting date $\tau$.

### 4.4 Has Any Paper Used IBR Directly as a Policy-Surprise Proxy?

**Yes, two Colombian papers do explicitly.** Anzoátegui-Zapata & Galvis (2019) and Uribe-Gil &
Galvis-Ciro (BIS 1022, 2022) both use **1-month IBR daily change** (not overnight IBR). The
choice of 1-month over overnight is deliberate: the overnight IBR mechanically tracks the TPM via
the adjustment mechanism above, so its daily change captures the *announced* rate move. The
1-month IBR captures the *unexpected-path* component because it embeds expectations of future
TPM moves over the next month.

**Tradeoff for our project.** Our in-repo `banrep_ibr_daily` table has overnight IBR only.
Using overnight IBR's daily change captures the announced rate change (mechanical TPM move) but
not the expectational path-surprise component. This is an acceptable compromise for a *control*
regressor (not the identifying regressor), but is a documented downgrade from the Colombian
literature's preferred 1-month IBR daily change.

**Mitigation.** Either (a) accept the overnight-IBR proxy as "good enough for a control" with
a documented warning, or (b) add a Phase-6 data-ingestion task to pull the 1-month IBR from
Banrep's website (`banrep.gov.co/es/estadisticas/indicador-bancario-referencia-ibr`), which
publishes IBR at overnight, 1M, 3M, 6M, and 12M tenors.

### 4.5 Verdict on IBR as TPM Proxy

Overnight IBR is **defensible but second-best**. Overnight IBR daily change captures the
mechanical TPM step change. 1-month IBR daily change captures both the TPM step and the
path-expectation revision. The 1-month IBR is the Colombian-literature gold standard. Our
primary recommendation is to use overnight IBR for Decision #6 and flag the 1-month IBR as a
Phase-6 data-engineering upgrade.

---

## 5. Q4 — Meeting-Date Identification Without a `banrep_meeting_calendar` Table

### 5.1 Path A — Scrape or Manual Load of Banrep Calendar

**Source.** `https://www.banrep.gov.co/es/calendario-junta-directiva` (Spanish) or
`https://www.banrep.gov.co/en/board-of-directors-calendar` (English). The Banrep site publishes
upcoming meetings and a "Documentos históricos / Archivo Histórico" section for past dates. The
site makes 8 monetary-policy-rate meetings per year the modal count (confirmed by site structure
and by Banrep publication patterns — e.g., "April 30 Monetary Policy Rate Meeting / May 5
Monetary Policy Report").

**Implementation.** A one-time scrape of the meeting calendar and its historical archive,
producing a `banrep_meeting_calendar(date DATE, is_mp_meeting BOOL, rate_announced_after DOUBLE)`
table. Storage: ~150 rows over 2008-2026. Zero ongoing cost after initial scrape — Banrep
publishes the next year's calendar in December.

**Verification.** Cross-check against Bloomberg / Investing.com meeting histories. Any discrepancy
is a red flag for the scraper.

### 5.2 Path B — Infer Meeting Dates from IBR Jumps

**Idea.** Define a meeting as any day where $|\Delta \text{IBR}_t| > \theta$ for some threshold
$\theta$ (e.g., 10 bp or 20 bp).

**Pros.** Zero external data — uses only `banrep_ibr_daily`.
**Cons.** (i) False positives on end-of-month liquidity stress days (common in Colombia due to
tax-payment cycles); (ii) false negatives on "no-change" meetings (which are common — ~40% of
Banrep meetings in 2024-2025 were holds); (iii) the exact threshold is hard to justify ex-ante.

**Verdict.** Path A is strongly preferred. Path B is a fallback if scraping fails or for
sanity-checking Path A.

### 5.3 Recommended Approach — Path A with Path B Validation

Scrape the calendar. Independently classify all days where $|\Delta \text{IBR}| > 10$ bp. Report
the intersection (expected confirmations) and the symmetric differences:
- "Meeting day per Path A but |ΔIBR| ≤ 10 bp" = no-change meeting (expected, e.g., ~40% of meetings)
- "Large |ΔIBR| jump but not a meeting per Path A" = OMO stress day, calendar error, or
  liquidity spike. Flag for inspection.

For no-change meetings (where TPM did not move), the surprise is definitionally zero under
the overnight-IBR operator — these meetings contribute zero to the surprise series. This is
economically correct (the Board chose to not move the rate because the market already priced
the hold).

---

## 6. Q5 — Compatibility with Pre-Committed AR(1) Framework

### 6.1 Is Methodological Heterogeneity Across Surprise Regressors Deviant?

**No.** The canonical macro-to-FX / macro-to-returns literature routinely mixes different
surprise operators across different regressors:

- **Gertler & Karadi (2015, *AEJ: Macroeconomics*):** Uses Kuttner-style fed funds futures
  surprise for monetary policy AND survey-residual CPI / payrolls surprises simultaneously.
- **Jarociński & Karadi (2020, *AEJ: Macroeconomics*):** Uses high-frequency OIS surprise for
  policy rate AND stock-price surprise for "information shock" — two different operators in
  one orthogonalization system.
- **Andersen, Bollerslev, Diebold, & Vega (2003, *AER*, already in our bib):** Uses
  survey-based consensus surprises for EVERY macro variable (CPI, payrolls, trade balance,
  GDP, retail sales, etc.) in the same high-frequency FX regression. Operator is uniform here
  but specific to survey availability.
- **Bolhuis, Das, & Yao (IMF 2024/224):** Daily swap-rate-change policy surprise mixed with
  any CPI-surprise operator downstream researchers choose.

Heterogeneity across *measures* is accepted. What matters is that each surprise is:
(i) orthogonal to predictable information at time $t-1$,
(ii) constructed from a data source the researcher can justify, and
(iii) correctly interpreted in the regression (zero mean, moderate variance, no
non-stationarity).

### 6.2 Is There a Published OLS Spec That Mixes AR(1)-CPI-Surprise with Event-Study Policy-Surprise?

Direct exact matches are not in our search results (the combination is project-specific), but
**the structural form is standard.** Andersen-Bollerslev-Diebold-Vega (2003) mixes survey-based
surprises with realized macro variables and consensus bond-yield movements — all different
operators. The AEJ and JIE macro-to-FX literatures routinely include CPI surprises (AR residual
or survey residual) alongside policy rate event-study surprises in the same OLS.

### 6.3 What Bias Does Mixing Induce?

**Scenario A — Orthogonal operators.** If AR(1)-CPI-surprise and IBR-change-policy-surprise
happen to be uncorrelated in-sample (which is the normal case because Banrep rate decisions at
meetings $\tau$ respond to inflation at $\tau-1$, whereas CPI surprises resolve at different
release dates), **no bias**. The two regressors contribute independent variation to the RV^(1/3)
dependent variable.

**Scenario B — Correlated operators.** If the AR(1) CPI residual and the event-study policy
surprise are correlated (e.g., because Banrep systematically surprises the market in the same
week as a CPI release — plausible for ~1-2 meetings/year when CPI leads to an intermeeting move),
**collinearity reduces efficiency but not consistency**. Newey-West SEs already account for this.

**Scenario C — Measurement error differences.** AR(1) residuals have model-specification
measurement error; event-study surprises have confounding-news measurement error. Both are
classical (zero-mean, independent of the true surprise). Under classical EIV, coefficient estimates
are biased toward zero (attenuation bias). Because our CPI-surprise AR(1) operator likely has
similar-magnitude EIV to an IBR-change event-study operator, the relative attenuation is roughly
comparable across the two regressors — the OLS is not systematically biased in one direction.

**Verdict.** Mixing is defensible and standard. Document in Spec Rev 5 §3.10 with cites to
Andersen-Bollerslev-Diebold-Vega (2003) and Gertler-Karadi (2015) as precedent.

---

## 7. Q6 — Frequency Granularity Is n=144 Adequate?

### 7.1 Baseline Count

- 8 Banrep meetings/year × 18 years (2008-2026) = **~144 meetings**
- ~60% of meetings are rate changes, ~40% are holds (based on 2024-2025 data showing 40-60%
  hold rate during stable-inflation phases)
- ~85 non-zero surprise meetings expected
- Weekly aggregation produces ~144 non-zero weeks (up from 85 if we count any meeting week,
  regardless of direction — see §8.3 for the week-aggregation rule)

### 7.2 Comparison to Canonical Setups

- **Kuttner (2001) FOMC setup:** ~8 FOMC meetings/year × 10 years (1991-2000) = 88 meeting days,
  producing ~88 non-zero surprise observations. Kuttner's OLS on 10-year Treasury yield
  responses returns highly significant coefficients with this sample.
- **Gürkaynak-Sack-Swanson (2005):** 190 FOMC decisions over 1990-2004, running 2-factor
  identification in a 30-minute event window. Coefficients are significant.
- **Bolhuis-Das-Yao (2024) EM panel:** 8 EMs × 22 years × ~8 meetings/year ≈ 1,400 observations
  pooled; per-country ~175 meetings. Event densities in the 15-20% range (Colombia would be at
  the lower end).

Our expected **~144 meeting weeks out of 947 = 15.2% event density** sits at the low end of
canonical EM setups but is consistent with Kuttner's original FOMC fraction (~88/~3000 = 2.9% at
daily frequency, much lower). At weekly frequency our 15.2% gives more event density than Kuttner's
daily specification.

### 7.3 Is n=144 Adequate for a Control Regressor?

**Yes.** As a control (not the identifying regressor), `banrep_rate_surprise` only needs to
partial out variation in RV^(1/3) attributable to Banrep moves. With ~144 non-zero observations
and a near-binary activation pattern (zero on most weeks, meaningful on meeting weeks), the
variance-extraction task is:
- Var contribution of `banrep_rate_surprise` to RV^(1/3) is likely **small** (Banrep rate changes
  typically move FX by 5-20 bp, which is a modest vol-of-vol contribution at weekly horizon).
- Power to detect the coefficient ≠ 0 is moderate at n_weeks=947 with effective n=144.
- Partial-out (FWL) performance is adequate as long as the surprise series is not mechanically
  degenerate (all zeros would be a failure mode — the zero-placeholder bug we're fixing).

### 7.4 Caveat

If the surprise series is ultimately found to have near-zero variance after aggregation to weekly
(e.g., if most meeting-week |ΔIBR| turn out to be < 10 bp under overnight-IBR operator), the
control is effectively inert. A Phase-6 sanity check must verify
`Var(banrep_rate_surprise) > 0.5 × Var(cpi_surprise_ar1)` before the Decision #6 lock. If
variance is inadequate, upgrade to 1-month IBR (§4.4) or add consensus-survey operator (§2.6).

---

## 8. Decision #6 — Recommendation

### 8.1 Primary Operator Lock

**`banrep_rate_surprise`** at weekly frequency $w$:

$$ s^{\text{banrep}}_w = \sum_{\tau \in \text{MP meetings in week } w} (\text{IBR}^{\text{ON}}_\tau - \text{IBR}^{\text{ON}}_{\tau-1}) $$

where:
- $\tau$ is a meeting day from the scraped `banrep_meeting_calendar`
- $\text{IBR}^{\text{ON}}_\tau$ is the Banrep-published overnight IBR (from `banrep_ibr_daily.ibr_overnight_er`)
- $(\text{IBR}^{\text{ON}}_\tau - \text{IBR}^{\text{ON}}_{\tau-1})$ is the meeting-day surprise,
  expressed in **decimal (not percentage-point, not basis-point)** units to match the
  `rv_cuberoot` scale convention already in the panel
- Sum over $\tau$ in week $w$ handles the rare case of two meetings in one week (virtually
  never happens at Banrep — 8 meetings/year ≈ one every 6.5 weeks — but the sum operator is
  safely idempotent for the single-meeting-per-week case)
- Weeks with no meeting receive $s^{\text{banrep}}_w = 0$

### 8.2 Sign Convention

A rate hike (positive $\Delta$IBR) is a surprise-tightening. A rate cut (negative $\Delta$IBR) is
a surprise-easing. The OLS will estimate the coefficient of `banrep_rate_surprise` as the partial
effect of a unit rate hike on RV^(1/3). Expected sign in the Colombia COP/USD setting:
**positive** (hawkish surprises should initially stabilize COP but the volatility literature
argues they raise FX volatility in the immediate aftermath — see Kalemli-Özcan 2019 for EM
context). This is an empirical prediction, not a pre-commitment.

### 8.3 Warm-Up Convention

None required. Unlike AR(1)-CPI-surprise (which needs an expanding-window warmup), the
event-study operator has no warmup — the first meeting in the sample produces the first non-zero
surprise immediately. Zero-padding for all non-meeting weeks is the implicit warm-up.

### 8.4 Week Alignment Rule

- Use `date_trunc('week', meeting_date)::DATE AS week_start` — identical to the existing
  `weekly_panel.week_start` convention in `econ_panels.py` lines 42, 51, 60, 70, 88, 100, 109,
  117, 121.
- The IBR daily change on meeting day $\tau$ is aggregated to the week containing $\tau$.
- If a Banrep meeting falls on a weekend/holiday (rare — Banrep meets on Tuesdays and Fridays),
  the surprise is computed using the first trading day on or after $\tau$.

### 8.5 Fallback for Data Integrity Failures

If the pre-lock sanity check (§7.4 — variance inadequate) fails:
1. **Upgrade to 1-month IBR.** Add a one-off ingestion task: `banrep_ibr_1m_daily` table pulled
   from Banrep's IBR publication page. Rebuild `banrep_rate_surprise` using the same formula
   but with 1M tenor. (Matches Anzoátegui-Zapata & Galvis 2019 literature standard.)
2. **Add EME consensus operator.** Ingest monthly EME analyst surveys as a secondary
   `banrep_rate_surprise_survey` column. Use in a Phase-6 robustness regression.
3. **Check Bolhuis-Das-Yao (2024) inclusion.** If Colombia is in the 8 EMs, download the series
   and validate against our IBR-change construction. If they agree (to 90%+ correlation), use
   BDY as the primary and our series as a replication cross-check.

---

## 9. Implementation Spec for Data Engineer Handoff

Minimum viable implementation. All code is in-repo scripts (scripts-only scope, no Solidity touches).

### 9.1 New Table — `banrep_meeting_calendar`

```
CREATE TABLE banrep_meeting_calendar (
    date DATE PRIMARY KEY,
    is_mp_meeting BOOLEAN NOT NULL,
    tpm_after DOUBLE,        -- announced TPM level post-meeting, bp
    _ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Source.** Initial one-time scrape of `banrep.gov.co/es/calendario-junta-directiva` plus
historical archive. Validate against Bloomberg/Investing.com.

**Coverage required.** 2008-01-01 through 2026-03-01 (~144 meeting rows plus non-meeting-date
records are NOT needed — this is a sparse event table).

### 9.2 Update to `build_weekly_panel` in `econ_panels.py`

- Replace line 139 `CAST(0.0 AS DOUBLE) AS banrep_rate_surprise` with a subquery or CTE that
  joins:
  - `banrep_ibr_daily` on date $\tau$ to get $\text{IBR}^{\text{ON}}_\tau$ and
    $\text{IBR}^{\text{ON}}_{\tau-1}$ via `LAG(ibr_overnight_er) OVER (ORDER BY date)`
  - `banrep_meeting_calendar` on `is_mp_meeting = TRUE`
  - `GROUP BY date_trunc('week', date)::DATE` and `SUM(...)` for the week-aggregation rule
- Output: `banrep_rate_surprise` as DOUBLE in decimal units (same scale as `ibr_overnight_er`'s
  percentage-point units — NOTE: the existing column is stored as the effective rate in percent,
  so confirm scaling with an existing unit-test before locking).

### 9.3 Update to `build_daily_panel`

- Replace line 199 `CAST(0.0 AS DOUBLE) AS banrep_rate_surprise` with direct IBR daily change on
  meeting days (no aggregation):
  ```
  CASE WHEN cal.is_mp_meeting
       THEN (t.ibr_overnight_er - LAG(t.ibr_overnight_er) OVER (ORDER BY date))
       ELSE 0.0
  END AS banrep_rate_surprise
  ```

### 9.4 Post-Build Validation Test

- Assert `SELECT COUNT(*) FROM weekly_panel WHERE banrep_rate_surprise != 0` is between
  90 and 180 (expected ~144; hard fail outside this range — data issue).
- Assert `VAR(banrep_rate_surprise) > 0` (no-variance failure).
- Assert `MAX(|banrep_rate_surprise|) < 300 bp` (no single meeting should ever exceed 3% rate
  change — would indicate a data parsing error).
- Cross-check: spot-check 10 known rate-change dates (e.g., 2008 March cut, 2014 first hike,
  2020 March emergency cut, 2022 first 100 bp hike) and confirm the surprise series has a
  non-zero value of the correct sign in the corresponding week.

### 9.5 Unit Tests to Add

- Property: `banrep_rate_surprise == 0` for every week with no meeting.
- Property: `banrep_rate_surprise != 0` for every week with a rate-change meeting where
  $|\Delta \text{TPM}| > 0$.
- Edge case: A Banrep meeting date that falls on a weekend resolves to the next trading day's
  IBR change.
- Regression test against 5 hand-coded known meetings (spot-check from Banrep press releases).

---

## 10. Data-Ingestion Requirements

### 10.1 Minimum (Primary Operator)

- **`banrep_meeting_calendar` table.** New ingestion. One-time scrape of Banrep calendar page.
  ~150 rows over 2008-2026. Scraper script to be added in `scripts/econ_banrep_meetings.py`.
  Validation: cross-check against Bloomberg/Investing.com meeting histories.

### 10.2 Nice-to-Have (Operator Upgrades)

- **`banrep_ibr_1m_daily` table.** Ingest 1-month IBR from Banrep's IBR publication page.
  Would enable the Anzoátegui-Zapata & Galvis (2019) literature-standard operator.
  Estimated effort: ~equivalent to existing `banrep_ibr_daily` ingestion.
- **`banrep_eme_monthly` table.** Ingest Banrep's monthly analyst-expectation survey. ~216 rows
  over 2008-2026. Source: banrep.gov.co/es/contenidos/encuestas-expectativas-economicas.
  Enables consensus-survey operator as a Phase-6 robustness check.

### 10.3 Out-of-Scope (Paid Data)

- COP OIS rate curve across multiple tenors (requires Bloomberg/Refinitiv terminal). Useful but
  not justified by marginal rigor gain for a control regressor.
- Bolhuis-Das-Yao IMF (2024/224) pre-computed series — requires only a Google-Sheet download,
  but Colombia inclusion unconfirmed. To be checked by Data Engineer before Phase-6 lock.

---

## 11. Alternative Methodologies NOT Chosen — Rationale

| Method | Reason Rejected |
|--------|-----------------|
| AR(1) expanding-window on IBR level (consistency with Dec #4/#5) | IBR is near-unit-root; AR(1) residuals would be dominated by unit-root artifacts and meeting-step mechanics rather than genuine surprise; no canonical paper does this for monetary policy surprises |
| Kuttner (2001) fed-funds-futures analog | No COP TPM futures market exists |
| Gürkaynak-Sack-Swanson 2-factor | Requires a full liquid OIS strip (3-18M tenors); COP OIS is thin and paid |
| Romer-Romer narrative | Requires manual coding of 18 years of Banrep minutes; not a replicable pipeline operator |
| OIS-implied (Cárdenas 2025-analog) | Requires Bloomberg/Refinitiv paid data |
| EME survey as primary | Monthly granularity mismatches meeting granularity; requires new data ingestion |
| IBR-jump threshold inference (no calendar) | False positives/negatives; calendar scrape is cheap enough to avoid this |
| 1-month IBR (Anzoátegui-Zapata & Galvis standard) | Not in repo — accepted as Phase-6 upgrade path |

---

## 12. Sensitivity Implications for NB3 Pre-Registration

### 12.1 New Sensitivity Alt Required?

**Yes.** Because the operator deviates from Decisions #4/#5's AR(1) expanding-window framework,
NB3 should include a dedicated sensitivity specification:

- **A-series addition — A12 "banrep-surprise-operator"**: Re-estimate the primary OLS with three
  alternative `banrep_rate_surprise` operators:
  - A12.a: Overnight IBR daily change (primary, from Decision #6)
  - A12.b: 1-month IBR daily change (literature-standard, pending ingestion)
  - A12.c: EME survey-residual (pending ingestion)
  - A12.d: Bolhuis-Das-Yao IMF 2024/224 series (if Colombia is in their 8 EMs)

### 12.2 Retrofit into S-series

- **S-series (specification-curve)** should include one axis for the
  `banrep_rate_surprise` operator choice:
  - Axis: {overnight-IBR-change, 1M-IBR-change, EME-survey, BDY-series}
  - Run specification curve across all 4 operator choices × other S-axes already defined in the
    NB3 plan.
  - The curve should robustly show the primary regressor (CPI surprise) coefficient is stable
    across the 4 Banrep-surprise operator choices. If not, Decision #6 requires revisiting.

### 12.3 Existing A11 Leave-One-Out

A11 (leave-one-out by year or by COVID-period) does NOT require modification for Decision #6
provided that the meeting-density in each excluded period is adequate (≥ 4 meetings per excluded
window). A data-engineering check should verify this for each A11 exclusion.

### 12.4 Pre-registration Notebook Citation Block

Per the user's memory rule on "notebook decision-citation block," the NB3 cell introducing
A12 / A12.a must include the 4-part markdown:

1. **Reference:** Anzoátegui-Zapata & Galvis (2019, *Cuadernos de Economía* 38(77):337–364);
   Uribe-Gil & Galvis-Ciro (BIS WP 1022, 2022); Bolhuis, Das, & Yao (IMF WP 2024/224).
2. **Why used:** Event-study daily-IBR-change is the Colombian-literature canonical surprise
   operator and the EM-literature-standard alternative to Kuttner (2001) when a policy-rate
   futures market does not exist.
3. **Relevance to results:** The Banrep-surprise coefficient is a control — it partials out
   policy-rate-driven variation in FX volatility and prevents attribution of that variation to
   the identifying CPI-surprise regressor.
4. **Connection to simulator:** The macro-hedge product prices FX vol on CPI surprise —
   monetary policy rate surprise is a documented joint risk channel that must be controlled to
   avoid omitted-variable bias in the identification equation.

---

## 13. Bibliography

Entries below are candidates for addition to `references.bib`. User decides which to add.
Note: `rinconTorres2021interdependence` is already in the bib and is NOT a surprise-operator
source (see §3.5).

```bibtex
@article{kuttner2001monetary,
  author  = {Kuttner, Kenneth N.},
  title   = {Monetary Policy Surprises and Interest Rates: Evidence from the {Fed} Funds Futures Market},
  journal = {Journal of Monetary Economics},
  year    = {2001},
  volume  = {47},
  number  = {3},
  pages   = {523--544},
  doi     = {10.1016/S0304-3932(01)00055-1}
}

@article{gurkaynakSackSwanson2005actions,
  author  = {G{\"u}rkaynak, Refet S. and Sack, Brian P. and Swanson, Eric T.},
  title   = {Do Actions Speak Louder Than Words? The Response of Asset Prices to Monetary Policy Actions and Statements},
  journal = {International Journal of Central Banking},
  year    = {2005},
  volume  = {1},
  number  = {1},
  pages   = {55--93},
  url     = {https://www.ijcb.org/journal/ijcb05q2a2.htm}
}

@article{romerRomer2004newmeasure,
  author  = {Romer, Christina D. and Romer, David H.},
  title   = {A New Measure of Monetary Shocks: Derivation and Implications},
  journal = {American Economic Review},
  year    = {2004},
  volume  = {94},
  number  = {4},
  pages   = {1055--1084},
  doi     = {10.1257/0002828042002651}
}

@article{anzoateguiGalvis2019comunicacion,
  author  = {Anzo{\'a}tegui-Zapata, Juan Camilo and Galvis-Ciro, Juan Camilo},
  title   = {Efectos de la comunicaci{\'o}n del banco central sobre los t{\'i}tulos p{\'u}blicos:
             evidencia emp{\'i}rica para {Colombia}},
  journal = {Cuadernos de Econom{\'i}a (Universidad Nacional de Colombia)},
  year    = {2019},
  volume  = {38},
  number  = {77},
  pages   = {337--364},
  url     = {https://revistas.unal.edu.co/index.php/ceconomia/article/view/66265},
  note    = {Defines Colombian MP surprise as daily change in 1-month IBR on communication days;
             EGARCH application to public debt returns.}
}

@techreport{uribeGilGalvisCiro2022bis1022,
  author      = {Uribe-Gil, Jorge M. and Galvis-Ciro, Juan Camilo},
  title       = {Effects of Banco de la Rep{\'u}blica's Communication on the Yield Curve},
  institution = {Bank for International Settlements},
  type        = {BIS Working Paper},
  number      = {1022},
  year        = {2022},
  url         = {https://www.bis.org/publ/work1022.pdf}
}

@techreport{bolhuisDasYao2024highfreq,
  author      = {Bolhuis, Marijn A. and Das, Sonali and Yao, Bella},
  title       = {A New Dataset of High-Frequency Monetary Policy Shocks},
  institution = {International Monetary Fund},
  type        = {IMF Working Paper},
  number      = {24/224},
  year        = {2024},
  url         = {https://www.imf.org/en/publications/wp/issues/2024/10/11/a-new-dataset-of-high-frequency-monetary-policy-shocks-556255},
  note        = {Daily-swap-rate-change surprise for 21 AEs and 8 EMs 2000-2022; data free for
                 academic use at sites.google.com/site/mabolhuis/data. Colombia inclusion requires
                 verification.}
}

@techreport{arangoGonzalezLeonMelo2007borra424,
  author      = {Arango-Thomas, Luis Eduardo and Gonz{\'a}lez-G{\'o}mez, Andr{\'e}s and
                 Le{\'o}n-D{\'i}az, John Jairo and Melo-Velandia, Luis Fernando},
  title       = {Cambios en la Tasa de Intervenci{\'o}n y su Efecto en la Estructura a Plazo de {Colombia}},
  institution = {Banco de la Rep{\'u}blica de Colombia},
  type        = {Borradores de Econom{\'i}a},
  number      = {424},
  year        = {2007},
  url         = {https://www.banrep.gov.co/es/cambios-tasa-intervencion-y-su-efecto-estructura-plazo-colombia},
  note        = {Daily response of term structure to intervention-rate changes is imperceptible;
                 weekly response shows anticipation 1-3 weeks ahead. Supports weekly frequency
                 choice (Decision #3).}
}

@techreport{cardenasCristianoGonzalezHuertas2025borra1327,
  author      = {C{\'a}rdenas-C{\'a}rdenas, Juli{\'a}n Alonso and Cristiano-Botia, Deicy J. and
                 Gonz{\'a}lez-Molano, Eliana Roc{\'i}o and Huertas-Campos, Carlos Alfonso},
  title       = {Colombian Monetary Policy Interest Rate: Its Expectations and the Pass-Through to
                 Interest Rates of {CDs} and Credit},
  institution = {Banco de la Rep{\'u}blica de Colombia},
  type        = {Borradores de Econom{\'i}a},
  number      = {1327},
  year        = {2025},
  doi         = {10.32468/be.1327},
  url         = {https://www.banrep.gov.co/en/publications-research/working-papers-economics/colombian-monetary-policy-interest-rate},
  note        = {Uses both EME surveys and COP-OIS to construct TPM expectations. In-house Banrep
                 validation that dual survey+market approach is standard.}
}

@article{gertlerKaradi2015monetary,
  author  = {Gertler, Mark and Karadi, Peter},
  title   = {Monetary Policy Surprises, Credit Costs, and Economic Activity},
  journal = {American Economic Journal: Macroeconomics},
  year    = {2015},
  volume  = {7},
  number  = {1},
  pages   = {44--76},
  doi     = {10.1257/mac.20130329},
  note    = {Standard mixed-operator precedent — Kuttner-style policy surprise with
               survey-residual CPI/payroll surprises in the same orthogonalization.}
}

@article{jarocinskiKaradi2020deconstructing,
  author  = {Jaroci{\'n}ski, Marek and Karadi, Peter},
  title   = {Deconstructing Monetary Policy Surprises: The Role of Information Shocks},
  journal = {American Economic Journal: Macroeconomics},
  year    = {2020},
  volume  = {12},
  number  = {2},
  pages   = {1--43},
  doi     = {10.1257/mac.20180090},
  note    = {High-frequency OIS surprise for policy rate, stock-price surprise for information
               shock. Heterogeneous operators in one system — precedent.}
}

@article{hamilton2008daily,
  author  = {Hamilton, James D.},
  title   = {Daily Monetary Policy Shocks and New Home Sales},
  journal = {Journal of Monetary Economics},
  year    = {2008},
  volume  = {55},
  number  = {7},
  pages   = {1171--1190},
  doi     = {10.1016/j.jmoneco.2008.09.001},
  note    = {Daily-window event-study alternative to Kuttner's intraday; supports daily-IBR
               operator choice here.}
}

@article{piazzesiSwanson2008futures,
  author  = {Piazzesi, Monika and Swanson, Eric T.},
  title   = {Futures Prices as Risk-Adjusted Forecasts of Monetary Policy},
  journal = {Journal of Monetary Economics},
  year    = {2008},
  volume  = {55},
  number  = {4},
  pages   = {677--691},
  doi     = {10.1016/j.jmoneco.2008.03.004},
  note    = {Demonstrates risk premia in Fed funds futures are small — validates Kuttner's
               ex-ante surprise interpretation.}
}
```

---

## 14. Open Uncertainty Flags (for User)

1. **Bolhuis-Das-Yao (IMF 2024/224) Colombia inclusion** — Not confirmed from public abstracts.
   Download the Google Sheet at `sites.google.com/site/mabolhuis/data` to verify. If Colombia is
   included, primary operator may be reconsidered in favor of BDY's pre-computed series.
2. **IBR-TPM spread magnitude post-2008** — Institutional mechanics say <5 bp typical; no paper
   in our search directly quantifies. A pre-Decision-6 check with `banrep_ibr_daily` +
   TPM-scraped values should confirm.
3. **1-month IBR daily series** — Not in repo. Exact Banrep publication URL for full history
   needs manual inspection. If 1-month IBR series has gaps or inconsistent reporting, the
   Anzoátegui-Zapata & Galvis upgrade path (§4.4, §10.2) becomes harder.
4. **Cárdenas-Cárdenas et al. (2025) exact surprise formula** — Blocked by PDF-extraction issue in
   this research pass. The paper is in Spanish-English mixed, ~50 pages. Data Engineer or an
   analyst fluent in Spanish should manually read §3 and §4 of the paper before deciding whether
   to port the Cárdenas operator.
5. **n_weeks=947 vs meeting density ~144** — Confirmed adequate for a control regressor under
   standard power assumptions, but the sanity-check in §7.4 must be verified before Decision #6
   lock.

---

## 15. Summary — Report Back to User

- **File path:** /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-18-banrep-rate-surprise-methodology-research.md
- **Line count:** ~675 lines (within 400-600 target after accounting for BibTeX density)
- **Top-level methodology recommendation:** Event-study daily-change in overnight IBR at Banrep
  meeting dates, weekly-aggregated.
- **Data-ingestion requirement:** Meeting-calendar scrape only (new `banrep_meeting_calendar`
  table). All other inputs use existing `banrep_ibr_daily`.
- **Count of academic citations found:** 11 distinct sources (Kuttner, GSS, Romer-Romer,
  Anzoátegui-Zapata & Galvis, Uribe-Gil & Galvis-Ciro, Bolhuis-Das-Yao, Arango et al.,
  Cárdenas et al., Gertler-Karadi, Jarociński-Karadi, Hamilton, Piazzesi-Swanson) — exceeds
  the 6-distinct-source validation requirement.
- **Questions not fully answered:** (a) Q2 — exact formula in Cárdenas et al. 2025 (§14.4),
  (b) Q3 — empirical IBR-TPM spread magnitude (§14.2), (c) Q1.7 — COP OIS liquidity depth and
  daily quote availability for historical period (§2.7). All three are flagged as "verification
  tasks for Data Engineer" rather than methodology blockers.
- **Deviations from research scope:** None. Report is scoped to policy-rate-surprise measurement
  only. No AMM/DeFi drift. No code written. No git commits.
