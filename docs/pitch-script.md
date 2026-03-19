# ThetaSwap — 5-Minute Hackathon Pitch Script

**Target:** DeFi / Uniswap Hook Incubator Demo
**Duration:** 5 minutes (strict)
**Slide deck:** `research/slides/presentation.pdf` (19 slides)

---

## [0:00–0:05] TITLE (Slide 1)

> ThetaSwap is an adverse competition oracle for AMM liquidity providers.

## [0:05–0:40] HOOK — The Risk Nobody Hedges (Slide 2)

> On top of the already identified opportunity costs faced by liquidity providers — impermanent loss 
> and adverse selection — both well understood, both hedgeable today through variance perpetuals — there is a third, research-validated risk induced by the competitive nature of price provision among LPs: **fee concentration**.
>
> It's been shown that across the top 250 Uniswap V3 pools, just seven percent of LP addresses — classified as sophisticated — capture seventy-five to ninety percent of trading fees.

>Even if you eliminate IL and LVR entirely, your profit still depends on your share of the fee pool — and that share is being compressed by sophisticated actors.
>
> We call this **Loss Versus Competition — LVC**. It dilutes your fee revenue — the higher the concentration, the less you earn. And right now, **nothing hedges it**.

---

## [0:30–1:30] EVIDENCE — Research Question + Model (Slides 3–5)

> We asked a simple question: **is there empirical demand for a hedging instrument against adverse competition? And if so — how much are LPs willing to pay?**
>
> We collected 41 days of data from the ETH/USDC 30-basis-point pool on Uniswap V3 mainnet. 600 positions, over 3,300 position-day observations, 597 exits.
>
> Our treatment variable is **Delta-Plus** — how much more concentrated fees are compared to the symmetric Ma-Crapis competitive null.
>
> The model is a logistic regression on exit probability. The key insight is **nonlinear**: there are two regimes.
>
> At low concentration, more competition actually *helps* — it signals high trading volume, all LPs benefit. We call this the **shelter effect**. A linear-only model would stop here and conclude concentration is protective.
>
> But beyond a threshold — roughly 9% above equilibrium — the effect **flips**. Concentration no longer signals volume. It signals **fee extraction** by sophisticated actors. This is the **adverse competition regime**.
>
> Together: an inverted-U. Shelter below the turning point, adverse above it.

---

## [1:30–2:15] RESULTS — What the Data Says (Slides 6–8)

> The empirical results confirm both coefficients with high statistical significance across multiple lag structures. The turning point sits consistently around 9%.
>
> What does this mean concretely? When fee dispersion exceeds 9% above equilibrium, each additional percentage point of concentration **raises exit probability by 2.3 percentage points**.
>
> Translated to a price: LPs in this pool are willing to pay approximately **10% above the average hourly pool fee revenue** for protection.
>
> So we have both things: **existence of demand** — the inverted-U with a statistically significant adverse regime — and a **concrete price** for the insurance premium.

---

## [2:15–3:00] BACKTEST — Does Hedging Improve Outcomes? (Slides 9–11)

> Theory is nice. Does it work in practice?
>
> We replayed all 600 real positions through a power-squared exit payoff with $200K underwriter seed capital.
>
> **18.8% of positions were better off hedged.** Mean hedge value: **+$23 per position.** Payout-to-premium ratio: 121% — payouts exceed premiums. The reserve absorbs the concentration spike and stays solvent.
>
> And here's the critical property: only **1 day in 41** exceeds the turning point. Delta-Plus jumped from near-zero to 0.158. **Rare but severe** — a classic insurable tail event. This is exactly the risk profile that makes insurance economically viable.

---

## [3:00–4:15] SOLUTION — FCI Oracle On-Chain (Slides 12–16)

> So how do we bring this on-chain? The **Fee Concentration Index** — our Uniswap V4 hook.
>
> The algorithm has two phases. **Position tracking**: when liquidity enters, we record the position key and snapshot the fee growth baseline. On every swap, we use transient storage to capture tick movement and increment overlapping range counters.
>
> **Index accumulation**: when a position fully exits, we compute its fee share x_k from the fee growth delta, weight it by one-over-blocklife as theta_k, and accumulate theta_k times x_k-squared into A_T-squared. That's the on-chain state — one storage slot.
>
> Anyone can then query `getDeltaPlus()` — max of zero, square root of A_T-squared minus the competitive null. That's your adverse competition signal. We also expose `getDeltaPlusEpoch()` for time-windowed metrics, because the cumulative index has infinite memory.
>
> The architecture is **protocol-agnostic**. The FCI algorithm sits in a core contract. Protocol-specific facets adapt data via delegatecall — same algorithm, any AMM. We have a native V4 facet and a **Reactive Network adapter** that bridges V3 events cross-chain. The oracle is not limited to V4-native pools.

---

## [4:15–4:45] DEMO (Slide 17)

> You can run it yourself: `make sol-test-demo`.
>
> This is a **differential test**. Scenarios are generated in Python — expected metric values computed off-chain — then contrasted against on-chain state on a Sepolia fork via `forge test`.
>
> Three scenarios: **equilibrium** — symmetric LPs, Delta-Plus approximately zero. **Crowding-out** — a JIT-style position captures disproportionate fees, Delta-Plus spikes above the turning point. **Mixed** — passive and sophisticated LPs coexist, shelter and adverse regimes in the same pool. All values verified against Python-generated expectations.

---

## [4:45–5:00] CLOSE — What's Next (Slide 18)

> **What we've built:** the FCI oracle live on Uniswap V4, a reactive adapter bridging V3 events cross-chain, and backtest validation showing the insurance is economically viable.
>
> **What's next:** the linearized power-squared CFMM — the trading function is complete in the mathematical specification — and the vault settlement mechanism.
>
> The math spec is complete, the oracle tracks metrics across protocols, and the next milestone delivers the full insurance product. **ThetaSwap — hedging the risk nobody hedges.**

---

## Delivery Notes

- **Pace:** ~150 words/minute. Script is ~750 words. Leaves ~30s buffer for transitions and breathing.
- **Slide transitions:** Advance roughly every 15–20 seconds. Don't linger on the math — the table and inverted-U intuition are what land.
- **Emphasis points:** "Nothing hedges this today" (slide 2), "10% above hourly fee revenue" (slide 7), "1 day in 41" (slide 11), "one storage slot" (slide 13).
- **Demo:** If live demo time is separate from the 5 minutes, extend the demo section. If not, the verbal walkthrough of the three scenarios suffices.
- **Tone:** Confident, research-backed, builder-focused. You have real data, real contracts, real tests. Lead with the gap in the market, prove it empirically, show the on-chain solution.
