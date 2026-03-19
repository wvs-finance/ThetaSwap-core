# Design: Structural Discrete Choice Model for LP Insurance Demand

## Research Question

Does fee concentration (A_T) causally drive passive LP withdrawal, and what is the dollar-denominated willingness to pay for insurance against JIT competition?

## Decisions Made (Brainstorming Phase)

| Decision | Choice | Rationale |
|---|---|---|
| Evidence type | Willingness to pay | Dollar-denominated, directly validates market size |
| WTP signal | Capital withdrawal | High impact, high success likelihood, easiest on-chain data |
| Causal claim | Causal | Required for publishable identification |
| Identification strategy | JIT entry shocks | Discrete observable event, strongest causal claim |
| Econometric approach | Structural discrete choice | Recovers dollar WTP, maps to CFMM payoff function |
| Data scope | Specific high-volume pairs | ETH/USDC, ETH/USDT, WBTC/ETH on Uniswap V3 mainnet |

## Model Overview

Each passive LP *i* in pool *j* at block *t* chooses to STAY or EXIT. They exit when:

> Expected net payoff (fees - IL - concentration cost) < outside option

The key structural parameter is the **concentration cost coefficient** — how much fee revenue LPs forgo per unit of A_T. This coefficient, combined with the observed A_T distribution, gives the dollar WTP for insurance.

## Identification Strategy

**Instrument**: JIT entry shocks. A new JIT LP appearing in pool *j* shifts expected future concentration without being caused by any individual passive LP's exit decision.

**JIT classification**: Positions with blocklife = 1 (same-block add and remove), corresponding to theta_k = 1 in the ThetaSwap model.

**Reverse causality problem**: LP removal mechanically updates A_T. JIT entry shocks break this because the *arrival* of a JIT LP precedes A_T changes — passive LPs respond to the *expectation* of future concentration, not the realized value.

## Connection to ThetaSwap Model

The ThetaSwap CFMM offers protection with payoff V_LP(p) = ln(1+p) where p = A_T/(1-A_T).

- If estimated WTP > 0 and economically significant → insurance market has demand
- WTP magnitude → what premium the CFMM can charge
- **Testable implication**: If LPs value the ln(1+p) payoff structure, their exit probability should be concave in A_T (matching V_LP concavity). Linear or convex response suggests a different payoff preference.

## Components

1. **Data pipeline** — on-chain event extraction, A_T computation, JIT classification
2. **Reduced-form evidence** — event-study around JIT entry (motivating, not main result)
3. **Structural estimation** — discrete choice with IV, WTP recovery
4. **Specification tests** — concavity of exit response, overidentification, placebo tests

## Next Step

Formal Reiss-Wolak structural econometric specification (19-question process) to fully specify the economic model, stochastic model, and estimation strategy.
