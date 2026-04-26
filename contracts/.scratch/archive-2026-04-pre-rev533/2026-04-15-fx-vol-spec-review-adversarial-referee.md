# Referee Report: Colombian Price-Level Surprise and COP/USD FX Realized Volatility

**Verdict: MAJOR REVISION (Revise and Resubmit)**

The paper poses an economically relevant question and the two-layer architecture is a reasonable design choice. However, several identification and specification issues must be resolved before the estimates can support the product claims made in the motivation.

---

## 1. Composite surprise does not identify inflation specifically [MAJOR]

The regressor $s_t^{\text{price}}$ bundles CPI + PPI, released the same day by DANE. The exclusion restriction delivers identification of "Colombian price-level announcement news," not "inflation" per se. PPI captures producer-cost shocks (imported intermediates, energy) that affect firm margins before they pass through to consumer prices. If $\beta$ loads primarily on PPI-driven repositioning, the product is hedging input-cost volatility, not household purchasing-power erosion. For the target user (Colombian households), this distinction matters: a pure PPI shock that never passes through to CPI (Rincon-Castro et al. 2021 estimate pass-through of only 0.01-0.05) provides no purchasing-power hedge. **Required:** Run A2 (CPI vs PPI decomposition) as a primary specification, not a robustness check. Report $\beta_{\text{CPI}}$ and $\beta_{\text{PPI}}$ separately and test $H_0: \beta_{\text{CPI}} = \beta_{\text{PPI}}$. The product claim stands only if $\beta_{\text{CPI}} > 0$ independently.

## 2. GARCH-X omission is a critical gap [MAJOR]

The entire Colombian FX-vol literature uses GARCH models. Rincon-Torres et al. (2021, be_1171) identify via GARCH(1,1) conditional heteroskedasticity. Berganza-Broto (2012) model FX conditional variance with GARCH. The spec proposes OLS on log(RV) with no autoregressive variance dynamics. This is econometrically naive for a volatility LHS: realized vol exhibits strong persistence (typically $\gamma + g > 0.95$ in weekly FX data), so the OLS residuals will be serially correlated even after the A5 lagged-RV patch. A GARCH(1,1)-X with $s_t^{\text{price}}$ in the variance equation is the natural specification for this question and the standard in the cited literature. **Required:** Add GARCH(1,1)-X as a co-primary specification alongside the OLS log(RV) model. Report the surprise coefficient in the variance equation. If the two models disagree on significance or magnitude, discuss why.

## 3. Sign restriction $\beta > 0$ is asserted, not derived [MAJOR]

The spec claims T3 tests $\beta > 0$ but never derives this from the economic model. Under inflation targeting with credible BanRep, a positive CPI surprise triggers expected tightening, which should appreciate COP (lower COP/USD). Clarida-Waldman (2007) confirm this for G10 IT regimes. But the LHS is volatility, not level. Vol increases from repositioning regardless of the direction of the level move. The sign restriction $\beta > 0$ therefore follows from a "repositioning generates vol" argument that is agnostic to the monetary-policy channel -- it would hold equally for any surprise that triggers portfolio adjustment. This weakens the economic interpretation: $\beta > 0$ does not confirm an inflation-hedging channel; it confirms only that price-level news moves markets. **Required:** Acknowledge explicitly that $\beta > 0$ tests "announcement generates volatility" not "inflation channel operates." Derive the sign from first principles (information arrival + repositioning) rather than from the monetary-policy transmission mechanism.

## 4. Net-bias direction is internally contradictory [MAJOR]

Section 3.4 claims "net: all attenuation" and therefore $\hat{\beta}$ is a lower bound. But S1 in Section 6.1 states stale consensus may bias $\beta$ upward (overstated surprise magnitude inflates the regressor, biasing $\beta$ upward if the measurement error is non-classical). These cannot both be true simultaneously. If consensus staleness generates a systematic upward component in $s_t^{\text{price}}$ correlated with vol (stale forecasts during volatile periods), the bias is upward, and the "conservative lower bound" claim collapses. **Required:** Resolve the contradiction formally. Either prove the staleness bias is dominated by classical attenuation (requires a signed bound on the covariance structure), or withdraw the "all attenuation" claim and report the bias direction as ambiguous. The product-safety implication ("conservative for the RAN") depends on this.

## 5. Asymmetric effects not tested [MINOR]

Positive CPI surprises (inflation above consensus) and negative surprises (below consensus) are treated symmetrically. Under inflation targeting, upside surprises are more disruptive: BanRep tightening is contractionary, triggers capital-flow reversals, and generates larger FX repositioning than easing. Menon (1995) and the pass-through literature (cited in traspasoAinflacion) document asymmetric ERPT. A symmetric $\beta$ averages over potentially heterogeneous effects. **Required:** Add $\beta^+ \neq \beta^-$ split (positive vs negative surprise) as a specification test or robustness check. If asymmetry is large, the hedge payoff profile differs materially from what a symmetric $\beta$ implies.

## 6. Layer 1 to Layer 2 mapping is undefined [MINOR]

Section 1 motivates the regression by claiming $g^{\text{pool}} \approx \phi^2 V(P)/(8L)$ captures FX realized vol. But $\beta$ estimates the effect of CPI surprise on TOTAL weekly RV. The RAN underlying $U_{\text{RAN}}$ depends on the DIFFERENTIAL $g^{\text{pool}}(i_S) - g^{\text{pool}}(i_T)$ -- the concentration of LVR across tick ranges, not total vol. Total RV maps to total $g^{\text{pool}}$, but the hedge payoff depends on how vol distributes across ticks. A CPI surprise that raises total vol uniformly across all ticks would increase $g^{\text{pool}}$ but leave $U_{\text{RAN}} \approx 0$. The regression does not identify whether CPI surprises generate CONCENTRATED vol (which triggers the hedge) or DIFFUSE vol (which does not). **Required:** Acknowledge this gap explicitly. Either (a) defer the concentration question to Layer 2 simulation and state that $\beta$ is a necessary but not sufficient condition for the hedge, or (b) propose an empirical test of whether CPI-surprise-driven vol concentrates in tail ticks.

## 7. Layer 1 / Layer 2 conceptual tension [SUGGESTION]

Layer 1 is reduced-form: the FX market is a black box. Layer 2 assumes structural agent behavior (LP_short, LP_long, ARB) responding to an external FX oracle. This is internally consistent IF the separation is maintained cleanly -- Layer 1 estimates the statistical input ($\beta$) and Layer 2 takes it as a parameter. But Section 8b of the literature deliverable and the notebook's closed-loop mechanism blur this boundary by arguing the pool "observes the efficient price-discovery venue" (be_1171) as if the reduced-form finding validates the structural model. Be precise: be_1171 shows FX leads TES in a structural VAR on 5-minute returns. This does not validate the Angstrom pool's structural assumptions (competitive LP equilibrium, GBM price process, etc.). The structural Layer 2 stands or falls on its own assumptions, which are untested. State this limitation clearly.

---

## Summary of Required Revisions

| # | Severity | Revision |
|---|----------|----------|
| 1 | MAJOR | Decompose $\beta_{\text{CPI}}$ vs $\beta_{\text{PPI}}$ as co-primary |
| 2 | MAJOR | Add GARCH(1,1)-X as co-primary specification |
| 3 | MAJOR | Derive $\beta > 0$ from information arrival, not monetary channel |
| 4 | MAJOR | Resolve attenuation-vs-upward-bias contradiction formally |
| 5 | MINOR | Test $\beta^+ \neq \beta^-$ asymmetry |
| 6 | MINOR | Define or explicitly defer the total-vol-to-tick-concentration mapping |
| 7 | SUGGESTION | Sharpen Layer 1 / Layer 2 boundary claims |

The four MAJOR issues are individually addressable and do not require redesigning the study. The identification strategy is sound in principle; the revisions sharpen what $\beta$ actually identifies and ensure the econometric specification matches the literature standard.
