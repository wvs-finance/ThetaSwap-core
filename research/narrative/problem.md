# The Adverse Competition Problem

<!-- Key Facts (machine-readable for downstream phases) -->
<!-- observation_window: 41 days -->
<!-- positions: 600 -->
<!-- pool: ETH/USDC 30bps -->
<!-- real_null_ratio: 2.65x -->
<!-- days_positive_deviation: 63% (26/41) -->

## 1. The Risk Nobody Hedges

There's a latent risk that discourages passive liquidity providers --- and no current hedging instrument tracks it on-chain.

When multiple liquidity providers (LPs) supply capital to a decentralized exchange pool, each LP earns a share of the trading fees proportional to the liquidity they contribute within the active price range. In theory, if there are $N$ identical LPs, each captures $1/N$ of the fees. In practice, a small number of sophisticated actors --- just-in-time (JIT) liquidity providers and MEV-aware strategies --- concentrate fee revenue away from passive participants.

This is **adverse competition**: sophisticated LPs do not complement passive LPs by growing the pool; they *substitute* for them, capturing fees that would otherwise flow to long-term participants. Capponi, Jia & Zhu (2024) formalize this finding and show that JIT liquidity mechanically dilutes passive LPs' fee share without generating proportional trading volume, which *decreases* overall market quality.

The problem is distinct from three risks that already have hedging instruments:

- **Impermanent loss (IL)** tracks the price divergence between pool assets. Options and structured products hedge IL.
- **Loss-versus-rebalancing (LVR)** tracks the cost of adverse selection by informed traders. MEV-aware products address LVR.
- **Fee concentration risk** tracks the *competition structure* among LPs for fee revenue. Nothing hedges this today.

Fee concentration is a separate dimension of risk. Our econometric model includes an impermanent loss control variable; it does **not** absorb the concentration effect. The two risks can be hedged independently.


## 2. A Passive LP's Experience

Consider a concrete example in the ETH/USDC 30bps pool on Uniswap V3.

1. **Alice deposits liquidity.** She provides capital across a tick range. Under competitive conditions, she expects to earn $1/N$ of the pool's trading fees, where $N$ is the number of active positions. This is the Ma & Crapis (2024) competitive equilibrium baseline.

2. **A JIT provider enters.** Around a large pending trade, a sophisticated LP mints a tightly concentrated position for a single block. This position captures a disproportionate fee share $x_k \gg 1/N$ because its liquidity is concentrated exactly where the trade executes. Alice's share drops from $1/N$ to $x_{\text{Alice}} \ll 1/N$.

3. **Alice's effective fee rate falls.** The fee revenue Alice earns per unit of time drops. Per Capponi & Zhu (2024), every LP has an optimal exit threshold --- a price level at which staying in the pool costs more than leaving. A lower effective fee rate $\hat{\phi}_i = x_i \cdot \phi_{\text{pool}}$ means Alice reaches her exit threshold sooner.

4. **Alice exits earlier.** In a world without adverse concentration, Alice would have stayed longer and earned more fees. The concentration pushed her out of the pool prematurely. This is the economic cost of adverse competition --- and it is currently unhedged.

The severity of Alice's experience depends on how far the realized fee share deviates from the equal-share baseline. At the observed maximum in our dataset ($\Delta^+ = 0.158$), the marginal effect on exit probability is 2.27 --- meaning each additional percentage point of concentration above this level raises Alice's probability of exiting by approximately 2.3 percentage points.

This walkthrough is not hypothetical. In the 41 days of ETH/USDC 30bps data we analyzed (600 positions, 3,365 position-day observations), the real fee concentration index exceeded the equal-share null by an average factor of $2.65\times$, and 63% of days showed positive concentration deviation ($\Delta^+ > 0$).


## 3. Two Properties That Make This Hedgeable

Adverse competition is not merely an inconvenience --- it has two structural properties that make it insurable.

### 3.1 Path-dependent tail risk

Not every day has adverse concentration. In our data, 63% of days have positive deviation ($\Delta^+ > 0$), but only **1 day in 41** exceeds the critical turning point $\delta^* \approx 0.09$. On that day, $\Delta^+$ jumped from near-zero to 0.158 --- extreme concentration driven by a small number of positions capturing the majority of fees.

This is the signature of a classic insurable tail risk: the event is **rare but severe**. Most days are benign; the damage is concentrated in infrequent spikes. Insurance is precisely the right economic tool for this pattern --- a small, predictable premium in exchange for protection against low-probability, high-impact events.

The path-dependent nature of this risk is critical. Fee concentration builds up over time through the accumulation of individual liquidity events. Each JIT entry, each sophisticated repositioning, shifts the fee share distribution further from the competitive null. The risk materializes not as a single shock but as a sequence of small dilutions that occasionally compound into a severe spike. This path dependence means the risk cannot be captured by a point-in-time snapshot --- it requires continuous monitoring of the concentration index $A_T$ relative to the equal-share baseline $A_T^{1/N}$.

### 3.2 Orthogonal to impermanent loss and LVR

Impermanent loss depends on price divergence between the pool's two assets. LVR depends on the information advantage of informed traders. Fee concentration depends on the *competition structure among LPs* --- how fee revenue is distributed across positions.

These are mathematically independent dimensions. In the econometric model, the IL control variable ($\beta_3 = 13.52$) has the expected positive sign (higher IL leads to more exits), but including or excluding it does **not** change the significance of the concentration coefficients ($\beta_1$, $\beta_2$). The quadratic concentration structure is present in the $A_T$-only model as well.

This orthogonality is practically important: a passive LP can hedge price risk with options, hedge MEV with LVR products, **and separately** hedge fee concentration risk with ThetaSwap. These protections stack without redundancy.


## 4. What the Literature Says

Five independent research papers validate different components of the adverse competition problem and the feasibility of hedging it. Together, they establish that (1) adverse fee concentration exists empirically, (2) it drives LP exits through a well-understood economic mechanism, and (3) the resulting risk is priceable as a derivative.

- **Capponi, Jia & Zhu (2024)** --- *"The Paradox of Just-in-Time Liquidity in Decentralized Exchanges: More Providers Can Lead to Less Liquidity."* JIT liquidity crowds out passive LPs by substituting their fee share, not complementing it. In pools where trading volume is inelastic to liquidity depth, JIT positions dilute passive LPs' effective fee rate without generating proportional volume.

- **Capponi & Zhu (2024)** --- *"Optimal Exiting for Liquidity Provision in Constant Function Market Makers."* LPs have optimal exit thresholds determined by their effective fee rate. A lower effective fee rate means the LP's optimal exit price is reached sooner --- the formal mechanism by which fee concentration drives premature exits.

- **Ma & Crapis (2024)** --- *"Decentralized Exchange Design: Permissionless Liquidity Provision."* In a symmetric free-entry equilibrium, each of $N$ identical LPs earns $1/N$ of pool fees. This equal-share outcome is the competitive baseline --- deviation from it is our treatment variable $\Delta_t = A_T^{\text{real}} - A_T^{1/N}$.

- **Aquilina, Foley, Gambacorta & Krekel (2024, BIS)** --- *"Decentralised Dealers? Examining Liquidity Provision in Decentralised Exchanges."* BIS Working Paper No. 1227. Empirically, 7% of LP addresses capture 80% of fees. These sophisticated actors use tick ranges $3.4\times$ tighter and hold positions $7.5\times$ shorter than passive LPs, confirming that fee shares are highly skewed.

- **Bichuch & Feinstein (2024)** --- *"The Price of Liquidity: Implied Volatility of AMM Fees."* The LP fee rate is priceable as a derivative. Their fixed-for-floating fee swap (Corollary 5.5) --- where an LP exchanges volatile realized fees for a fixed premium --- is structurally identical to ThetaSwap's insurance design. This independently validates that fee-based derivatives are a viable product class.

Our own data confirms what these papers predict: the real $A_T$ exceeds the competitive null on 63% of days, and the quadratic deviation model identifies a turning point at $\delta^* \approx 0.09$ that separates benign concentration from the regime where adverse competition drives LP exits.


## 5. Key Statistics

| Statistic | Value | Source |
|---|---|---|
| Observation window | 41 days (2025-12-05 to 2026-01-14) | Dune Q6 |
| Pool | ETH/USDC 30bps | Uniswap V3 mainnet |
| Positions analyzed | 600 | Dune Q4v2 |
| Position-day observations | 3,365 | econometrics.tex Section 5.7 |
| Exit events | 597 | econometrics.tex Section 5.7 |
| Real/Null $A_T$ ratio | $2.65\times$ | econometrics.tex Section 5.1 |
| Days with $\Delta^+ > 0$ | 63% (26/41) | econometrics.tex Section 5.1 |
| Trigger days ($\Delta^+ > \delta^*$) | 1 in 41 | backtest notebook |
| Turning point ($\delta^*$) | $\approx 0.09$ | econometrics.tex Section 5.7 |
| Max observed $\Delta^+$ | 0.158 | econometrics.tex Section 5.1 |
| Sophisticated LP fee capture | 7% of addresses capture 80% of fees | Aquilina et al. (2024) |
| Implied premium at $\Delta = 0.15$ | $\$110$ per position | econometrics.tex Section 5.8.3 |

---

*This document is the single source of truth for the adverse competition problem statement. Downstream phases (root README, research README, Beamer slides) consume this file by reference or adapted copy. All statistics are extracted from the canonical LaTeX specification (`research/model/econometrics.tex`) and the ETH/USDC 30bps backtest notebooks.*
