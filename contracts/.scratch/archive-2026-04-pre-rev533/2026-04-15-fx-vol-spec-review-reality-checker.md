# Reality Checker Review: FX Vol / CPI Surprise Spec

**Verdict: NEEDS WORK**

Spec is structurally sound and honest about its Tier-1b status, but contains one internal contradiction, two unverified data claims, and one unjustified quantitative gate. Seven issues below.

---

## 1. BLOCK -- "All attenuation" claim contradicts S1 (Section 3.4 vs 6.1)

Section 3.3 lists S1 (stale monthly consensus overstating surprise) with bias direction "Attenuation ... OR upward (stale consensus overstates)." Section 3.4 then concludes "Net bias: all attenuation." These directly contradict. If stale consensus systematically overstates the surprise magnitude, the regressor is inflated, and beta is biased UPWARD -- the opposite of attenuation. The spec even acknowledges this in the table but then ignores it in the summary sentence. This is not a minor wording issue; the "lower bound" claim that follows ("A significant beta-hat is a LOWER BOUND on the true effect") depends entirely on all-attenuation holding. If S1 produces upward bias, beta-hat could be an UPPER bound, which reverses the product safety argument.

**Fix:** Remove the "all attenuation / lower bound" sentence from 3.4. Replace with: "Net bias direction is ambiguous pending T1 (consensus rationality test). If T1 rejects, S1 dominates and beta may be upward-biased." Add S1 to the T1 spec-test linkage explicitly.

## 2. BLOCK -- BanRep consensus survey: "free" claim unverified (Section 4.3)

The surprise construction requires BanRep's monthly inflation-expectations survey (Encuesta de Expectativas). The spec marks this as free-tier. BanRep publishes CURRENT survey results on its website, but historical survey microdata (month-by-month consensus median going back to 2003) is not obviously downloadable as a machine-readable time series. The literature deliverable itself notes be_1171 used "Bloomberg's World Economic Calendar" for expectations (Section 2.4, footnote 16 of the PDF). If the anchor paper needed Bloomberg for consensus, claiming "no Bloomberg required" needs proof, not assertion.

**Fix:** Before Phase 5, verify that the BanRep Encuesta de Expectativas historical archive is downloadable as a CSV/Excel file covering 2003-2025. Document the URL. If only recent years are available, document the coverage gap and its impact on N.

## 3. FLAG -- IBR-implied BanRep-rate consensus: computability from public data (Section 4.3)

The spec claims BanRep policy-rate surprise is constructable from "BanRep rate decisions + IBR-implied consensus." IBR (Indicador Bancario de Referencia) swap rates are not on FRED. BanRep publishes the IBR fixing daily, but constructing an implied policy-rate consensus from IBR requires either: (a) the IBR term structure (not just overnight), which may need Bloomberg/Refinitiv, or (b) a simplifying assumption (IBR overnight = market expectation of next BanRep decision). The spec does not specify which. The literature deliverable's gap analysis (Section 8) acknowledges "Colombian OIS is thinner -- may need interpolation from IBR swaps" but the spec table says free-tier with a checkmark.

**Fix:** Specify the exact IBR-to-consensus formula. If it requires term IBR data, verify public availability. If unavailable, downgrade to AR(1) proxy (same as US CPI surprise) and flag the measurement-error implication.

## 4. FLAG -- adj-R2 >= 0.15 gate: scaling arithmetic not shown (Section 1)

Rincon-Torres 2023 found <10% R-squared at DAILY frequency on TES bonds (adjacent asset, not FX). At quarterly frequency they found 34%. The spec sets a WEEKLY out-of-sample gate at 15%. The implicit claim is that weekly aggregation lifts daily single-digit R-squared to 15%+. Variance-ratio scaling under iid would give roughly sqrt(5)-times improvement in signal-to-noise, but R-squared does not scale linearly with horizon under realistic autocorrelation. The 34% quarterly figure is on a DIFFERENT asset class (bonds vs FX) with different noise properties. The gap analysis in the literature deliverable (Section 8) honestly calls this "borderline" but the spec presents 15% as a firm gate without showing the interpolation math.

**Fix:** Add a one-paragraph calibration note: under iid-surprise + AR(1)-vol assumptions, what weekly R-squared does the Rincon-Torres daily bound imply? If the answer is 5-8%, the 15% gate is aspirational and should be labeled as such, with a fallback gate (e.g., 0.08) that would still justify continuing to Layer 2.

## 5. FLAG -- be_1171 TRM finding does not transfer to cCOP/USDC pool (Section 2.1, Section 8b)

be_1171 studied the SET FX market: institutional participants (banks, pension funds, Hacienda, BanRep), regulated counterparties, 5-hour trading session, bid/ask quotes from authorized intermediaries. A cCOP/USDC Angstrom pool is: permissionless LPs, MEV-auction microstructure, 24/7, no authorized-intermediary requirement. The "FX is the efficient aggregator" finding depends on WHO trades and HOW -- institutional flow on a regulated platform. Section 8b correctly lists Conditions (a)-(c) but the main spec body (Section 2.1) states the finding as if it directly justifies the pool without qualification. The phrase "FX is where Colombian macro shocks land first" is true for SET FX; it is an open question for a $7K/day cCOP DEX pool.

**Fix:** In Section 2.1, add a sentence: "The be_1171 efficiency finding applies to the institutional TRM market. Transfer to a cCOP/USDC CLAMM pool requires Condition (a) from Section 8b (liquidity depth >= $50K/day) to hold, which is currently unmet."

## 6. FLAG -- BanRep intervention dummy "free from SUAMECA" (Section 3.1, 4.3)

The spec claims intervention data is free from the SUAMECA portal. BanRep's SUAMECA page provides descriptions of intervention mechanisms but it is not clear that a downloadable daily/weekly time-series of intervention dates and amounts exists there. BanRep's Estadisticas pages have some intervention data but coverage and format vary. be_1171 had institutional access to BanRep internal datasets (the authors work at BanRep). If the intervention series requires scraping PDFs from Comunicados de Prensa, it is not "free" in the regression-ready sense.

**Fix:** Verify the exact SUAMECA URL that provides a downloadable intervention time-series. If it is PDF-only or incomplete, document the alternative (BanRep Estadisticas API) and the manual-extraction cost.

## 7. NIT -- 22-year pooling across regime changes (Section 6.1 S3)

The spec lists sub-sample splits as sensitivity (A3: 2003-14, 2015-20, 2021-25) but the primary regression pools all 22 years. Colombia's monetary regime changed substantially: IT credibility building (2003-2010), low-for-long (2015-2019), COVID shock (2020), aggressive tightening cycle (2021-2023). Beta almost certainly differs across these regimes -- the pass-through literature (Rincon-Castro 2021) documents time-varying coefficients of 0.01-0.05 across crisis episodes. Pooling is standard practice for a first-pass regression, and A3 + T6 (Chow/Bai-Perron) address this, so this is a NIT rather than a FLAG. But the spec should acknowledge that the pooled beta is a weighted average across regimes and may not represent the CURRENT regime's beta, which is what the product needs.

**Fix:** Add one sentence to Section 4.3 or 6.1: "The pooled beta is a weighted average across regimes. For product parameterization, the 2021-25 sub-sample beta (A3) takes precedence if T6 rejects stability."

---

**Summary:** 2 BLOCKs, 4 FLAGs, 1 NIT. The two BLOCKs (attenuation-direction contradiction; unverified consensus-survey data access) must be resolved before Phase 5 begins. The FLAGs should be addressed in the spec revision but do not prevent data-pipeline design work. The spec is honest about its limitations in the literature deliverable and Section 8b, but the main spec body overstates certainty in Sections 2.1 and 3.4.

**Reviewer:** TestingRealityChecker
**Date:** 2026-04-16
