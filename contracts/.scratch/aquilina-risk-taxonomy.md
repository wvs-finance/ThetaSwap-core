# Risk Taxonomy for AMM Liquidity Providers

**Source**: Aquilina, Foley, Gambacorta & Krekel (2024). "Decentralised dealers? Examining liquidity provision in decentralised exchanges." BIS Working Paper No. 1227.

**Dataset**: 430,799 liquidity positions across 250 Uniswap V3 pools (May 2021 -- Dec 2023), 88,299 distinct wallet addresses, representing ~96% of total volume traded.

---

## Summary Table

| # | Risk Name | Primary Evidence | Magnitude | Who Bears It | Structural? |
|---|-----------|-----------------|-----------|-------------|-------------|
| 1 | Adverse Selection / Impermanent Loss | Table 5, Eq. 3 | -0.39 bps/day per e-fold vol increase; retail has 0.18 bps *less* IL but net worse | Both (retail net worse) | Yes |
| 2 | Fee Yield Compression from Oligopoly | Table 5, Figure 7 | Retail earns 3.54 bps/day less fee yield; 7% of LPs capture ~80% of fees | Retail | Yes |
| 3 | Gas Cost Drag | Eq. 3, Section 4.3.2 | Narrows retail-sophisticated gap from 3.4 bps to 2.9 bps net return; fixed cost per txn | Both (proportionally worse for small positions) | Yes |
| 4 | Range Management Complexity | Table 6, Cols 2-4 | Active mgmt adds ~5 bps/day excess return; Interacted x Tickrange = -5.75 bps | Both (retail lacks skill) | Yes |
| 5 | JIT Liquidity Dilution | Figure 6, p.18 | <1% of trades; ~40% in ETH/USDC 5bps pool; 10 wallets = 50% of all JIT | Passive LPs in large pools | Yes |
| 6 | High-Volatility Profitability Asymmetry | Table 7 | Retail total return drops additional 6.4 bps on high-vol days; sophisticated earns 2.5x more | Retail | Yes |
| 7 | Concentration / Oligopoly Dynamics | Table 4, Figure 8 | e-fold TVL increase -> 60% higher odds of sophisticated dominance; 80% TVL held by 7% of LPs | Retail (crowded out) | Yes |
| 8 | Information Asymmetry in Tick Range Selection | Table 3 | Sophisticated: 23% tickrange spread vs retail 63%; sophisticated active 90% vs retail 81% of lifetime | Retail | Yes |
| 9 | Volatility-Conditional Spread Widening | Table 8, p.34 | Sophisticated widen spread on high-vol days; retail narrows (-5.1 pp tickrange) and reduces activity (-17 interactions) | Retail | Yes |
| 10 | Negative Risk-Adjusted Returns (Median) | Section 4.3.3 | Median daily excess return is negative; mean positive at 3.5 bps (positive skew from outliers) | Both (retail far worse) | Yes |

---

## Detailed Risk Descriptions

### 1. Adverse Selection / Impermanent Loss

**Evidence**: Table 5 (position-level regression), Equation 3 (p.27). Net return decomposition: `R_net = FeeYield + IL - GasFees`. Impermanent Loss coefficient for log(Volatility) = -0.39 bps (p < 0.01).

**Mechanism**: The AMM cannot update quotes between blocks. When external prices move, arbitrageurs trade against stale AMM quotes, systematically buying low and selling high against LPs. The LP's portfolio drifts away from hold-equivalent value. IL = (V_liq - V_hold) / V_hold, always in [-1, 0].

**Magnitude**: Retail positions experience 0.18 bps *less* impermanent loss than sophisticated positions (Table 5, IL column, Retail coefficient = +0.18***). This is because retail uses wider tick ranges (63% vs 23% tickrange spread), which dilutes adverse selection exposure per unit of capital. However, this "protection" is overwhelmed by the 3.54 bps/day lower fee yield that wider ranges produce.

**Who bears it**: Both, but sophisticated LPs rationally accept higher IL because they are more than compensated by fee revenue. Retail LPs have lower IL in absolute bps terms but worse net outcomes.

**Behavioral driver**: Narrow tick ranges amplify IL exposure but also amplify fee capture. Sophisticated LPs manage this tradeoff via active repositioning (median ~16-day positions with frequent interactions). Retail LPs leave positions open ~120 days, absorbing IL passively.

---

### 2. Fee Yield Compression from Sophisticated Competition

**Evidence**: Table 5 (Fee Yield column: Retail = -3.54*** bps/day); Figure 7 (sophisticated LPs capture ~80% of all accrued fees while representing only 7% of LP addresses and 20-30% of positions).

**Mechanism**: Concentrated liquidity in Uniswap V3 means fee revenue per unit of capital is inversely proportional to the amount of liquidity in the active tick range. When sophisticated LPs concentrate massive capital ($3.7M median position vs $29K retail -- Table 3) in narrow ranges around the current price, they capture the overwhelming majority of swap fees. Retail capital deployed in wide ranges earns proportionally less because it is "diluted" by the concentrated sophisticated capital in the active ticks.

**Magnitude**: 3.54 bps/day fee yield deficit translates to approximately 14 percentage points lower annualized fee revenue for retail vs sophisticated. At the pool-day level, retail collectively earns $6,014 less per pool per day despite representing 93% of all LPs (Table 5, pool-day Fees column).

**Who bears it**: Retail LPs disproportionately. In pools with daily volume exceeding $10M, sophisticated LPs provide essentially all the liquidity and earn most of the fees (Figure 8).

**Behavioral driver**: Sophisticated LPs actively adjust positions, maintaining narrow ranges (23% tickrange spread) that stay in the active price range 90% of the time. Retail's wide ranges (63%) mean most of their capital sits in inactive ticks earning zero fees.

---

### 3. Gas Cost Drag

**Evidence**: Equation 3 (p.27): `R_net = FeeYield + IL - GasFees/V_hold`. Section 4.3.2, p.28-29. Gas costs computed as median gasUsed times gasPrice, converted to USD.

**Mechanism**: Every liquidity management transaction (mint, burn, collect) incurs Ethereum gas fees. These are fixed costs per transaction regardless of position size. For small positions, gas costs consume a larger fraction of the position value. Sophisticated LPs spend more on gas in absolute terms due to more active management, but the greater dilution of gas fees relative to their larger position sizes ($3.7M vs $29K) makes their profits less sensitive to gas price levels.

**Magnitude**: Including gas costs, the retail underperformance gap narrows from 3.4 bps (total return) to 2.9 bps (net return) per day (Table 5). This implies sophisticated LPs pay approximately 0.5 bps/day more in gas costs relative to position value. Appendix H robustness analysis confirms the profitability gap persists across both high and low gas fee environments.

**Who bears it**: Both, but proportionally worse for small (retail) positions. A $29K retail position paying the same gas as a $3.7M sophisticated position faces ~127x higher gas cost as a fraction of capital.

**Behavioral driver**: Retail's lower interaction frequency (median 3 transactions per position) partially mitigates gas drag, but this same passivity causes worse fee yield and range management outcomes.

---

### 4. Range Management Complexity (Active vs Passive Management)

**Evidence**: Table 6, Equation 5 (p.29). Interacted coefficient = +4.77*** to +7.63*** bps/day excess return (Columns 2, 4). Tickrange coefficient = -1.29*** to -4.20*** bps (Columns 3-4). Interacted x Tickrange interaction = -5.75*** bps (Column 4).

**Mechanism**: Concentrated liquidity requires continuous position management. As the market price moves, a narrow-range position can go "out of range" and stop earning fees. The LP must burn the old position and mint a new one centered on the current price. This creates a two-dimensional optimization problem: (a) how narrow to set the range (narrower = more fee yield, but higher IL and higher probability of going inactive), and (b) how frequently to rebalance (more frequent = better range targeting, but higher gas costs).

**Magnitude**: Positions actively managed (interacted within past 3 days) earn approximately 5 bps/day more in excess returns. Narrower tickrange independently improves returns by 1.29-4.20 bps per unit. The interaction term (Interacted x Tickrange = -5.75) shows narrow positions benefit *even more* from active management, creating a compounding advantage.

**Who bears it**: Both, but retail lacks the infrastructure, monitoring tools, and automation. Table 3 shows retail has 1.18 fewer interactions per position, wider ranges (+40.13 pp), and longer durations (+120 days).

**Behavioral driver**: Retail that mimics sophisticated behavior can improve (Table 6, Columns 7-8 show the same directional effects for retail-only subsample). The barrier is operational, not access-based.

---

### 5. JIT (Just-In-Time) Liquidity Dilution

**Evidence**: Figure 6 (timeseries peaking at ~400 JIT transactions/day); p.18. Less than 1% of trades. Almost 40% in ETH/USDC 5bps pool. Only 10 wallet addresses account for ~50% of all JIT.

**Mechanism**: JIT providers observe pending swaps in the mempool, then sandwich them: mint a highly concentrated position in the exact tick range the swap will execute in, the swap pays fees to the JIT position, then the JIT provider immediately burns. The position exists for one block. This dilutes fee income of all other LPs in that tick range without bearing meaningful IL risk.

**Magnitude**: Less than 1% of all trades, but heavily concentrated in the highest-volume pool. The concentration among 10 wallets indicates a specialized, infrastructure-heavy strategy analogous to speed races in TradFi (Aquilina et al., 2021 showed ~25% of UK equity volume in such races).

**Who bears it**: All passive LPs in high-volume pools, regardless of sophistication.

**Behavioral driver**: JIT is enabled by mempool visibility and bundled transaction submission. It cannot be mitigated by LP behavior alone -- it requires protocol-level changes (private mempools, MEV-aware sequencing, batch auctions).

---

### 6. High-Volatility Profitability Asymmetry

**Evidence**: Table 7, Equation 6 (p.32). HighVolatility = 95th percentile of pool-day volatility. Retail x HighVolatility interaction coefficients: Fees (pool-day) = -$14,212***, Fee Yield = -5.20*** bps, IL = -1.17** bps, Total Return = -6.38*** bps, Net Return = -4.74*** bps.

**Mechanism**: During high-volatility episodes, prices move rapidly across tick ranges. Sophisticated LPs exploit this by increasing activity (+22.37 interactions, Table 8) and widening tick ranges (+2.66 pp) -- a defensive maneuver mirroring TradFi market maker spread-widening. Retail does the opposite: reduces activity (-17 interactions) and narrows ranges (-5.10 pp, Table 8), providing tighter quotes precisely when adverse selection is most dangerous.

**Magnitude**: On high-vol days, retail total return drops an additional 6.4 bps (4.7 bps after gas). Sophisticated positions earn 2.5x higher profit on high-vol days (7.6 bps increase vs baseline ~3 bps average retail net return). At the pool level, retail collectively earns $14,212 less on high-vol days, more than tripling the normal-day differential.

**Who bears it**: Overwhelmingly retail. Sophisticated LPs actively profit from volatility, consistent with Brogaard et al. (2018).

**Behavioral driver**: Retail's inability to dynamically adjust positions during volatile periods. The paper notes (p.34) sophisticated LPs capitalize on short-term vol spikes in low-vol, high-volume pools rather than maintaining permanent presence in structurally volatile pairs.

---

### 7. Concentration / Oligopoly Dynamics

**Evidence**: Table 4 (logistic regression, Equation 2, p.25). Figure 7 (participation rates over time), Figure 8 (scatter plots).

**Mechanism**: Despite permissionless access, economic forces drive concentration. Sophisticated LPs (7% of addresses) hold ~80% of TVL and capture ~80% of fees. They preferentially target high-volume, low-volatility pools. This creates a self-reinforcing dynamic: dominance of profitable pools funds further infrastructure investment, widening the gap. From V3 inception to end-2023, sophisticated LP interaction share grew from 40-50% to 70-80% (Figure 7).

**Magnitude**: log($TVL) coefficient = 0.62*** (exp(0.62) = 1.86, i.e., e-fold TVL increase -> 86% higher odds of sophisticated dominance). log($Volume) = 0.66*** for fee dominance (exp(0.66) = 1.93, 93% higher odds). log(Volatility) = -0.18*** (exp(-0.18) = 0.84, 16% lower odds per e-fold vol increase). Pools with daily volume > $10M are essentially fully dominated (Figure 8).

**Who bears it**: Retail LPs are crowded into low-volume pools (<$100K daily volume). The conclusion (p.36) states this "challenges the fundamental ethos of DEXs."

**Behavioral driver**: Economies of scale in monitoring infrastructure, capital deployment, and gas cost amortization. Parallels TradFi concentration (Aquilina et al., 2021; Budish et al., 2015, 2024).

---

### 8. Information Asymmetry in Tick Range Selection

**Evidence**: Table 3 (Equation 1, p.21). Sophisticated LP intercept for Tickrange Spread = 22.77%; Retail coefficient = +40.13*** (total retail spread = 62.9%). Proportion Active: sophisticated = 90.27%, retail = 80.85% (-9.42***).

**Mechanism**: Tick range selection is the central strategic decision in V3 LP-ing. Sophisticated LPs set ranges roughly one-third the width of retail (23% vs 63%) yet maintain active status for a higher proportion of their lifetime (90% vs 81%). This implies superior information about expected price ranges through better forecasting models or real-time monitoring. The advantage compounds with shorter durations (16 days vs 136 days), allowing more frequent recalibration.

**Magnitude**: The 40 pp difference in tickrange spread translates to approximately 2.7x higher effective leverage for sophisticated positions. Despite this leverage, sophisticated positions maintain higher active time, indicating ~40% tighter price prediction accuracy. This drives the 3.54 bps/day fee yield gap (Table 5).

**Who bears it**: Retail. The gap is not about market access but about analytical infrastructure.

**Behavioral driver**: Retail's "set and forget" approach (median 3 interactions = mint, collect, burn) vs. sophisticated's continuous recalibration. Table 6 Columns 7-8 show retail *can* improve by adopting narrower ranges and active management.

---

### 9. Volatility-Conditional Spread Widening (Asymmetric Volatility Response)

**Evidence**: Table 8. Top 25 pools: Retail x HighVolatility on #Interactions = -17.37***, on Interactions(%) = -9.20**, on Tickrange Spread = -5.10***. Sophisticated baseline HighVolatility: #Interactions = +22.37***, Tickrange Spread = +2.66*.

**Mechanism**: When volatility spikes, sophisticated and retail LPs respond in opposite directions. Sophisticated LPs increase activity and widen tick ranges -- exactly mirroring TradFi market maker spread-widening during volatile periods. Retail LPs reduce activity and narrow ranges, providing tighter quotes precisely when adverse selection is most dangerous while lacking monitoring to exit when positions go underwater.

**Magnitude**: Combined effect explains the -6.38 bps total return gap on high-vol days (Table 7). Retail has 17 fewer interactions and 5.1 pp narrower spreads on high-vol days; sophisticated has the opposite response.

**Who bears it**: Retail. Sophisticated LPs' spread-widening is simultaneously protective and profitable.

**Behavioral driver**: Retail likely narrows ranges on high-vol days because wider price movements push existing ranges out-of-range, and new mints are concentrated near the moved spot price. Reduced interactions suggest many retail LPs simply stop managing during volatility.

---

### 10. Negative Risk-Adjusted Returns (Median LP Loses Money)

**Evidence**: Section 4.3.3 (p.29). Median daily excess return is negative (ExcessReturn = NetReturn - RiskFreeRate, benchmarked to 4-week T-bills). Mean daily excess return = +3.5 bps/day. Sophisticated mean = 8.4 bps/day vs retail = 2.7 bps/day.

**Mechanism**: LP returns follow a fat-tailed, positively-skewed distribution. The typical (median) position loses money on a risk-adjusted basis on any given day. Positive average returns are driven by a subset of highly profitable positions/days. The combination of adverse selection, gas costs, and fee competition means the "default" outcome for undifferentiated capital is a slow bleed.

**Magnitude**: Mean excess return = +3.5 bps/day; median is negative (p.27: "the negative median indicates that the positions of retail LPs lose money for the majority of days"). Retail's positive mean is driven by a "select few" highly profitable positions.

**Who bears it**: Both, but retail far more severely. Most retail LP-days are value-destroying.

**Behavioral driver**: The structural skew means LP-ing is not a passive income strategy. It requires active management to reliably stay in the profitable tail.

---

## Cross-Cutting Structural Implications

### The Concentration-Volatility Nexus
Risks 6, 7, and 9 form a reinforcing cycle: sophisticated LPs dominate low-vol, high-volume pools (Risk 7), then capitalize on transient vol spikes within those pools (Risk 6), using spread-widening techniques retail cannot replicate (Risk 9). The most profitable LP opportunities are structurally captured by a small oligopoly.

### The Range-Management Trap
Risks 4 and 8 create a Catch-22 for retail: narrow ranges earn more fees but require active management that retail cannot provide. Wide ranges avoid IL but earn minimal fees due to competition with concentrated sophisticated capital (Risk 2). There is no "safe" passive strategy in concentrated liquidity AMMs.

### The Fee Compression Spiral
As sophisticated participation grows (Figure 7 shows monotonic increase 2021-2023), Risks 2 and 7 intensify. More sophisticated capital in active ticks means lower fee yield for everyone, a higher bar for profitability, more retail exits, and even greater sophisticated dominance. This is a structural equilibrium, not a transitional phase.

### Gas as Regressive Tax
Risk 3 is particularly pernicious for small retail positions. A $29K position and a $3.7M position pay the same gas, making it a ~127x higher cost burden for retail proportionally. This makes active management (which would help with Risks 4, 8, and 9) economically irrational for small positions.

---

## Key Equations Referenced

- **Eq. 1** (p.21): `Y_i = alpha + beta_1 * Retail_i + epsilon_i` -- behavioral differences regression
- **Eq. 2** (p.25): `Y_{i,t} = alpha + beta_1*log($TVL) + beta_2*log($Volume) + beta_3*log(Volatility) + epsilon` -- dominance logistic regression
- **Eq. 3** (p.27): `R_net = FeeYield + ImpermanentLoss - GasFees` -- return decomposition
- **Eq. 4** (p.27): `Y_{i,t} = alpha + beta_1*Retail + beta_2*log(Vol) + beta_3*log($TVL) + beta_4*log($Volume) + epsilon` -- profitability regression
- **Eq. 5** (p.29): `Y_{i,t} = alpha + beta_1*Retail + beta_2*Interacted + beta_3*Tickrange + controls + epsilon` -- excess return drivers
- **Eq. 6** (p.32): `Y_{i,t} = alpha + beta_1*Retail + beta_2*HighVol + beta_3*HighVol x Retail + controls + epsilon` -- volatility interaction

## Key Tables Referenced

| Table | Content | Page |
|-------|---------|------|
| 2 | Summary statistics: 430,799 positions, median size $25,899, median fees $129, median duration 2.82 days | 20 |
| 3 | Retail vs sophisticated behavioral differences (OLS) | 22 |
| 4 | Logistic regression: sophisticated dominance by pool characteristics | 25 |
| 5 | Profitability decomposition: fee yield, IL, total return, net return | 28 |
| 6 | Excess return drivers: Interacted, Tickrange, and their interaction | 31 |
| 7 | High-volatility profitability: Retail x HighVolatility interaction effects | 33 |
| 8 | Liquidity management differences during high volatility | 35 |
