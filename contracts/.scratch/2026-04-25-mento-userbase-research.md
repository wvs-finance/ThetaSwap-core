# Mento Ecosystem User-Base Research — Evidence-Grounded Findings for X_d Reframe

**Date**: 2026-04-25
**Author**: Product Trend Researcher (sub-agent)
**Project**: Abrigo / Rev-2 X_d hypothesis reframe
**Worktree**: `phase0-vb-mvp` (ranFromAngstrom)
**Wall-time spent**: ~50 min web research + arxiv probes + memory-file checks
**Confidence convention**: HIGH (official docs / multiple corroborating sources), MEDIUM (single source, no contradictions), LOW (inference / plausible-but-undocumented)

---

## Executive Summary (5 Headline Findings)

1. **MiniPay (Opera × Celo) dominates the Mento user surface, but its USDm/COPM exposure is a SMALL minority of activity.** As of Dec 2025, MiniPay has 12.6M-15M activated wallets and 350-430M lifetime transactions, but *USDT* is the dominant stablecoin (5M+ weekly active USDT users; ~50% of all Celo gas paid in USDT via MiniPay; 7M phone-verified USDT wallets in Dec-2025). USDm/cUSD is a *third* stablecoin in MiniPay's three-stablecoin "Pockets" — explicitly minor relative to USDT. **HIGH** confidence — sourced from multiple Opera press releases and Decrypt 2025-12.

2. **MiniPay transactions are dominantly small-value retail payments, not macro-hedge demand.** 87% of P2P transactions are <$5; 60% of USDT purchases/sales are <$5; median fees ~$0.001; total transaction count 270M / volume ~$270M ⇒ implied average ≈ $1/transaction, consistent with airtime top-ups, mobile data, P2P remittance, mini-app utility payments. **HIGH** confidence — Opera press release 2025-09-16 quotes 87%/60%/$0.001 directly.

3. **Colombia's COPM/cCOP is two distinct tokens with different issuers and different user bases — and on-chain volume is NEGLIGIBLE compared to MiniPay-USDT.** (a) `cCOP` (Mento-native, `0xc92e8fc2…`, governed by Celo Colombia DAO) — H1 2025 stats: 82,500 lifetime transactions, 11,058 holders, 270M units circulating, 4 native merchants + BucksPay payment-rail wrap. (b) `COPM` (Minteo, the Colombian fintech) — separate fiat-backed token, 100K+ users in early months, BDO-audited monthly, focused on remittance/payouts/FX/RWA via API for institutions. **HIGH** confidence — Celo forum H1 2025 report + Minteo.com + Yahoo Finance launch coverage. *Note: project memory address `0xc92e8fc2…` resolves to Mento's cCOP, not Minteo's COPM — these have been conflated in prior planning artefacts.*

4. **Documented Mento basket users in Latin America are predominantly inflation-hedgers and remittance senders, not macro-hedge speculators.** Colombia: stablecoins = 48% of all crypto purchases by COP value; primary use cases = inflation hedge, USD savings, cross-border. Brazil: 90%+ of crypto flows are stablecoin-related. The hedge motive is *direct CPI/FX defense*, not Fed-funds-sensitive speculation. **HIGH** confidence — Chainalysis 2025 LATAM report + multiple corroborating analyses.

5. **Macro-correlation evidence flips the prior hypothesis sign expectation.** BIS WP 1340 (2025) and BIS WP 1219 establish: (a) US monetary policy tightening drives stablecoin OUTFLOWS into MMFs (substitution margin); (b) a 1% exogenous net stablecoin inflow widens FX-parity deviation by 40bp and depreciates local currency; (c) ECB/BIS/IMF papers find higher Fed funds → lower stablecoin market cap globally. The Rev-2 result `ρ(X_d, fed_funds) = -0.614` is therefore CONSISTENT with the literature direction (high Fed funds ⇒ MMF substitution ⇒ lower X_d Carbon volume) — but this is a *macro-substitution* coefficient, not a *retail-hedge-demand* coefficient. The β̂ < 0 sign-flip on RV regression suggests the X_d signal is being driven by Carbon DeFi arbitrage flow that responds to global rates, not Colombian retail hedge demand. **HIGH** confidence on literature; **MEDIUM** on the reframe interpretation.

---

## §1. Mento Ecosystem Applications Inventory

### 1.1 MiniPay (Opera × Celo) — DOMINANT user surface

**What we KNOW (HIGH confidence, cross-corroborated):**

| Metric | Q4 2024 | Q2 2025 | Q3 2025 | Dec 2025 |
|---|---|---|---|---|
| Activated wallets | 5M | 8M | 10M | 12.6M-15M |
| Cumulative transactions | n/a | 200M | 271M | 350-430M |
| Countries | 50 | 50+ | 60 | 66 |
| DAUs | n/a | n/a | n/a | 700K |
| Weekly USDT users | n/a | n/a | n/a | 3M-5M+ |

Sources: Opera press releases 2025-07-17, 2025-09-16, 2025-12-03; Decrypt 2025-12; Celo forum Q4 2024 update.

**Stablecoin composition (HIGH confidence)**:
- **USDT** — primary, 5M+ weekly active, ~50% of all Celo gas paid in USDT via MiniPay
- **USDC** — secondary
- **cUSD/USDm** — third option in "Pockets" feature (Mento-powered swap UX)
- The "Pockets" feature lets users one-click swap between *the three* stablecoins — Mento is the swap rail, USDm is one of three options

**Key implication**: MiniPay's Mento-rail dominance is in the *swap engine* (Mento Broker), not in *USDm holdings*. Most MiniPay value is held in USDT.

**Geographic distribution (HIGH on top markets, MEDIUM on ranking)**:
- **South Africa**: 860% YoY activation growth (2024→2025) — leader by growth
- **Ghana**: 357% YoY
- **Kenya**: 177% YoY; #1 free app on Google Play in Kenya (Q4 2024)
- **Nigeria**: implicit large base (Africa stablecoin leader, $92.1B 12-mo on-chain)
- **United States**: 23x growth (small base)
- **Brazil/Argentina/Colombia**: explicit 2026 expansion focus per Decrypt 2025-12; Mercado Pago + Pix integration piloted in Argentina/Brazil
- **EU/Asia**: tripled YoY (small base)

**Use cases (HIGH confidence)**:
- P2P transfers (Cash Links, zero fees)
- Bill payments (utility, mobile data top-ups)
- Mini-app ecosystem (33 live apps, 16M monthly opens; subscriptions, games, donations, Learn-and-Earn)
- Savings (Hold & Earn, up to 2% weekly in select markets)
- Cross-border (Pix integration Brazil; Mercado Pago LATAM)
- Merchant settlement (BitGifty: 300K monthly transactions; 9,000 freelance writers paid in stablecoins/month)

**On/off-ramp partners (MEDIUM, not exhaustive list)**:
- Apple Pay, card, mobile money (M-PESA, MoMo, GCash), bank transfer
- Specifically named: Noah, Daimo, Binance Pay, Pix
- 12 partners offering zero-fee services across 35 currencies (Q4 2024 figure)

### 1.2 Valora — Mento-native wallet, smaller scale

**What we KNOW (MEDIUM)**:
- Self-custodial mobile wallet, phone-number-based send
- Full Mento support: USDm, EURm, BRLm explicitly listed (per docs.mento.org)
- Direct in-app CELO ↔ Mento-stable swaps
- Access to Celo DeFi (Ubeswap)
- Geographic focus: global, originally 3M+ users
- Highlighted yield: ~10% APY on USDm/cUSD via Valora promotional product (2025; check current)

**No public 2025/2026 user count** — last-confirmed figure is 3M+ from older Mento docs. Likely smaller MAU than MiniPay.

### 1.3 Other Mento-integrating apps — Colombia/LATAM specific

**TuCop (Colombia, MEDIUM):**
- Wallet specifically for cCOP, integrated with BucksPay
- Allows direct cCOP purchase via crypto-to-fiat gateway
- Marketed for Colombian retail
- Confirmed via @TuCopFinance on X (2025-09)

**BucksPay (Colombia, MEDIUM):**
- Crypto-to-fiat payment rail
- Claims coverage of "94% of payment options" in Colombia (bank transfers, QR-based)
- Lets cCOP be spent at "virtually any business" — not via direct merchant on-chain settlement, but via fiat conversion at point-of-sale

**Marranitos (Colombia, MEDIUM):**
- Staking/savings incentive product for cCOP holders
- Mentioned in Celo Colombia H1 2025 report
- No public TVL or user count

**Minteo (Colombia, HIGH on existence, MEDIUM on usage):**
- Issuer of COPM (the *fiat-backed* token, distinct from Mento's cCOP)
- BDO-audited monthly
- 100K+ users within months of launch (per Yahoo Finance / Newswire 2024-Q4)
- Use-case marketing: remittances, payouts, FX, RWA tokenization
- B2B / API focus: "third-party payouts to all of LATAM via API"
- Backers: Fabric VC, CMT Digital, Alliance DAO, Susquehanna, Dune VC
- Target: institutional / fintech, not direct retail wallet

### 1.4 Other ecosystem apps (LOW-MEDIUM coverage)

- **GoodDollar (UBI on Celo)**: well-known Celo ecosystem dApp, but no documented evidence in this research session of direct Mento basket integration. Plausible it uses cUSD/USDm in some flows, but undocumented in sources I checked.
- **Ubeswap (Celo DEX)**: documented as place users provide liquidity for cUSD/cEUR after swapping via Mento. LP for Mento basket exists but no usage stats found.
- **Mobius**: not surfaced in searches; flagged as MEDIUM-LOW relevance.
- **Mercado Bitcoin / Banco Inter (Brazil)**: NOT confirmed as Mento integrators in source review. Mercado Pago (different entity) IS confirmed as MiniPay off-ramp partner in LATAM.
- **Tropykus (LATAM)**: not surfaced.
- **WhatsApp/Telegram/SMS wallets**: no Mento-native wrappers documented in this research.

### 1.5 What's PLAUSIBLE but NOT documented

- COPM (Minteo) used by Colombian fintechs/exchanges for retail off-ramp — plausible given API focus, NOT directly confirmed in this research
- USDm being the Mento basket's "anchor token" for Celo DeFi liquidity routing — plausible architecturally, not quantified in evidence
- Mento basket use-case mix shifting toward "global FX layer" per 2026 rebrand strategy — stated as Mento's intention in forum, no usage data yet

---

## §2. Documented Transaction Patterns

### 2.1 Transaction-size distribution (HIGH on MiniPay-aggregate, LOW on per-stable)

**MiniPay aggregate (Sept 2025)**:
- 87% of P2P transactions are <$5
- 60% of USDT purchases/sales are <$5
- Median fee ~$0.001
- Implied average ≈ $1/transaction (270M tx / $270M volume)
- Examples cited in Opera blog: $2 airtime top-up Lagos; $5K transfer NYC

**Implication**: MiniPay = small-value, high-frequency retail. Even where USDm holdings exist, they're held in small amounts.

### 2.2 Diurnal / weekly patterns (LOW in this research; project memory has STRONGER signal)

Public sources do NOT segment MiniPay or Mento basket transaction times. **However**, per `project_carbon_defi_attribution_celo`, the Carbon DeFi protocol on Celo (which dominates COPM Transfer log volume — 52% of events) has:
- UTC 13-17 peak (North-American working-hours signature)
- ~1.9× peak/trough ratio
- Continuous diurnal pattern

This is a **machine-driven MM signature**, not Colombian retail. Important: when the Rev-2 X_d series was constructed from Carbon flows, what was being measured was *NA-business-hours arbitrage activity*, not LATAM retail hedge demand.

### 2.3 On/off-ramp infrastructure — geographic concentration

**Africa**:
- M-PESA (Kenya) — direct mobile-money on/off-ramp
- MoMo (Ghana, Uganda, Cameroon) — mobile money rail
- Bank transfer rails

**Latin America**:
- Pix (Brazil) — instant payment rail; piloted with MiniPay 2025
- Mercado Pago (LATAM e-commerce) — MiniPay partner
- BucksPay (Colombia) — fiat-conversion at POS for cCOP
- TuCop (Colombia) — wallet for cCOP

**Global**:
- Apple Pay, cards (Noah, Daimo)
- Binance Pay (P2P)

**Implication**: MiniPay-USDT-on-Celo has many fiat ramps, but USDm/COPM/cCOP have limited dedicated fiat infrastructure (BucksPay/TuCop only for Colombia; nothing comparable cross-LATAM for COPM at retail scale).

---

## §3. COPM / cCOP — Colombia-Specific Findings

### 3.1 Two distinct Colombian peso tokens — CRITICAL DISAMBIGUATION

| Aspect | cCOP (Mento-native) | COPM (Minteo) |
|---|---|---|
| Issuer | Celo Colombia DAO + Mento protocol | Minteo (Colombian fintech) |
| Address (Celo) | `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | Different (separate token) |
| Type | Decentralized, Mento-reserve-backed (Mento basket model) | Fiat-backed 1:1, BDO-audited monthly |
| Launch | 2024-Q3 (Celo forum proposal cgp-0060) | 2024-2025 |
| Target user | Colombian retail via Valora/MiniPay/TuCop | Institutional / fintech via API |
| Reserve model | Mento basket reserves (USDC/USDT/CELO/BTC/ETH overcollateralization) | Cash in regulated Colombian banks |
| H1 2025 transactions | 82,500 lifetime | n/a (not on-chain dominant) |
| H1 2025 holders | 11,058 | n/a |

**Project memory note**: `project_mento_canonical_naming_2026` lists `COPM` and address `0xc92e8fc2…` together. Per Celo forum source, `0xc92e8fc2…` is **cCOP** (Mento-native). Minteo's COPM is a *different* address. The plan memory has likely conflated the two for slug-naming convenience but the on-chain Carbon flows are against cCOP, not COPM. **Recommend verifying address vs. ticker before locking the next X_d hypothesis.**

### 3.2 cCOP usage in Colombia (H1 2025) — HIGH

- 82,500 lifetime transactions
- 11,058 unique holders
- 270M+ cCOP units in circulation
- 4 merchants accepting cCOP natively on-chain (initial target was 15+; pivoted to BucksPay rails)
- BucksPay claims access to "94% of payment options" — but this is *fiat conversion at POS*, not on-chain settlement
- 20+ in-person events across 5 cities (Medellín, Bogotá, Cartagena, Armenia, Leticia)
- Cashback pilot in Medellín H1 2025 (cCOP rewards for fiat payments)

**Use-case mix (qualitative, MEDIUM)**:
- Coffee/beverage retail at participating merchants (small)
- Cross-border tourist payments (cCOP-instead-of-USD pitch)
- Marranitos staking / savings (yield product)
- COP→USD swaps via Valora (10% yield headline; classic FX hedge)

### 3.3 COPM (Minteo) usage — MEDIUM

- 100K+ users within months of launch (per launch coverage; not segmented retail vs institutional)
- BDO monthly audits (regulatory credibility)
- API-driven: B2B payouts across LATAM
- Use-cases marketed: remittances, payouts, FX, RWA tokenization
- Funding: Fabric VC, CMT Digital, Alliance DAO, Susquehanna, Dune VC, Impatient VC
- Plans for sister tokens: MXNM (Mexico), CLPM (Chile), PENM (Peru) — multi-country settlement layer

### 3.4 Comparison vs USDC/USDT in Colombia (HIGH on aggregate, LOW on per-stable)

- Colombia overall: stablecoin = 48% of all crypto purchases by COP value (Chainalysis 2025)
- "Stablecoin purchases comprise more than half of all exchange activity" in Colombia/Brazil/Argentina (Chainalysis 2025 LATAM report)
- USDT and USDC dominate the 48% — cCOP/COPM are minor share
- Implication: a Colombian retail user wanting USD exposure goes USDT/USDC, not USDm. cCOP/COPM are micro-share niche products.

---

## §4. Macro-Relevance Signals — Documented Linkages

### 4.1 Fed funds → stablecoin demand (HIGH confidence, well-established)

**BIS WP 1219 (Stablecoins, MMFs, monetary policy)**:
- US monetary policy tightening → outflows from stablecoins, inflows into prime MMFs
- Substitution margin between stablecoins and MMFs
- Higher rates raise opportunity cost of holding non-interest-bearing stablecoins

**ECB working paper / Mehra-style analysis**:
- Higher US fed funds rates → reduce stablecoin prices (via demand channel)
- 3-month OIS rate windowing around FOMC meetings is the standard methodology

**Implication for prior `ρ(X_d, fed_funds) = -0.614`**:
- The negative correlation matches the *general* stablecoin literature direction
- BUT: this is a **macro-substitution signal** affecting *all* stablecoin demand globally, not a Colombia-retail-hedge signal
- The X_d series (Carbon DeFi basket volume) likely picked up this global rate-driven *MM positioning* signal, not retail-payment demand

### 4.2 Stablecoin flows → FX market spillover (HIGH, BIS WP 1340 2025)

**Aldasoro / Beltrán / Grinberg (BIS WP 1340)**:
- 27 fiat × 4 stablecoins × 64 exchanges, 2021-2025
- 1% exogenous net stablecoin inflow → 40bp parity deviation widening
- Local currency depreciation
- CIP deviation widening (USD funding cost up)
- Mechanism: intermediary balance sheet capacity is the choke point
- EM currencies most exposed

**Implication for the FX-vol-on-X_d regression**:
- Causation runs both directions: stablecoin demand → FX move; AND FX move → stablecoin demand
- The Rev-2 setup's β̂ < 0 + T1 exogeneity REJECTS is **consistent** with this two-way causation: X_d is *not* an exogenous regressor for FX-vol because both endogenously co-move with global liquidity / dollar-strength shocks
- This is a *predictive-regression* coefficient, NOT a structural causal coefficient (consistent with FX-vol-CPI exercise's predictive-regression flag in `project_fx_vol_econ_complete_findings`)

### 4.3 EM stablecoin × CPI / inflation (MEDIUM-HIGH)

- Multiple sources (Chainalysis, IMF, BIS, WEF, CryptoSlate) document: high EM CPI → high stablecoin demand
- Direction: CPI surprise UP → flight to USD-pegged stablecoins UP
- This is the "digital dollarization" channel
- Colombia, Argentina, Brazil, Turkey, Nigeria all exhibit this pattern
- BUT: documented at country/aggregate level (Chainalysis fiat→stable purchases), not at individual stablecoin (USDm/cCOP/COPM) level

### 4.4 No Mento-specific macro-link papers (LOW)

- arXiv search via WebSearch surfaced NO papers specifically on Mento, Celo MiniPay, or COPM macro-linkage
- arXiv 2507.13883 (stablecoin survey) acknowledges EM stablecoin research as a gap
- Academic literature is dominated by USDT/USDC studies on Ethereum/Tron
- Mento-specific quantitative analysis is essentially absent from peer-reviewed / pre-print literature as of mid-2025

---

## §5. Implications for the β Hypothesis (Given Rev-2 Failure)

### 5.1 Recap of Rev-2 result

- β̂ = -2.799e-8 (sign-flipped vs. expected positive)
- T1 EXOGENEITY: REJECTS (X_d not exogenous to FX-vol)
- Cook's D = 0.888 on a single observation (2026-03-06 dominates fit)
- ρ(X_d, fed_funds) = -0.614

### 5.2 What use-case stories ARE consistent with the data

Given the evidence in §1-§4, the Rev-2 X_d series (Carbon DeFi Mento-basket volume) is **NOT** a retail-hedge-demand signal. It is more plausibly:

**Story A: NA-business-hours MM positioning signal (HIGH evidence support)**
- Carbon DeFi protocol contracts (`0x6619871118D…` CarbonController; `0x8c05ea305…` BancorArbitrage) drive 52%+ of COPM/cCOP Transfer events
- Their hour-of-day signature is UTC 13-17 (NA working hours), not LATAM retail
- These are professional MM/arb operations on Mento basket
- Their position size scales with **global liquidity conditions** (Fed funds, dollar strength, MM balance-sheet capacity per BIS WP 1340 mechanism)
- ρ(X_d, fed_funds) = -0.614 fits: tight monetary policy → less MM capacity → less basket activity

**Story B: Predictive-regression artefact from co-moving global drivers (MEDIUM-HIGH)**
- Both X_d and FX-vol respond to **the same global shocks** (Fed surprises, dollar strength, EM stress index)
- T1 exogeneity rejection is consistent with this: X_d is an endogenous regressor, not a driver
- The FX-vol-CPI project also flagged this — `project_fx_vol_econ_complete_findings` notes the predictive-regression caveat

**Story C: Single-observation Cook's D dominance (HIGH on data, MEDIUM on interpretation)**
- 2026-03-06 alone drives the fit — this is structural fragility
- Whatever happened that week (probably a global liquidity event) explains both X_d spike and FX-vol spike
- Inference from a single influential observation is not robust

### 5.3 What use-case stories are NOT supported by evidence

- **Retail Colombian hedge demand**: cCOP has 11,058 holders, COPM has 100K users (mostly institutional); aggregate USD on-chain flow is dwarfed by USDT MiniPay activity. Even if retail Colombian hedge demand exists, it's NOT visible in Carbon DeFi MM flows.
- **MiniPay as macro-hedge signal**: MiniPay is dominantly USDT-payments, not USDm-savings. 87% of P2P is <$5. The signal-to-noise for macro-hedge is essentially zero in MiniPay aggregate.
- **Mento basket = retail hedge basket**: at $25M USDm + small EURm/BRLm/KESm/COPM/cCOP supply, the basket is a tiny fraction of retail USDT holdings on Celo. Carbon DeFi MM is the dominant flow.

### 5.4 Two β-hypothesis candidates the evidence DOES support

**Candidate H1: X_d as inverse-fed-funds proxy (NOT retail demand)**
- Reframe: X_d measures NA-business-hours MM activity on Mento basket
- Expected sign: β < 0 in FX-vol regression IF global liquidity is the true driver — but interpreting this as "Carbon DeFi flow predicts FX vol" would be a predictive-regression caveat, not a hedge-demand finding
- This reframe is *honest* but kills the Abrigo retail-hedge thesis

**Candidate H2: Use a different X_d altogether — true retail hedge proxy**
- Replace Carbon-basket volume with one of:
  - cCOP holder count growth (11,058 baseline; weekly delta)
  - cCOP merchant transaction volume (excluding Carbon DeFi MM addresses)
  - MiniPay USDm in-app swap volume in Colombia (if obtainable from Celo Colombia DAO reports)
  - cCOP→cUSD/USDm swap volume on Mento Broker (excluding Carbon contracts)
- ALL require **explicitly partitioning out Carbon DeFi MM addresses** before constructing the X_d series
- Per `project_carbon_user_arb_partition_rule`, partition via `trader` field on `tokenstraded` event rows
- Sample size will be dramatically smaller (post-partition); statistical power will be the binding constraint, not signal strength

### 5.5 The honest read

The Rev-2 X_d series captures **professional NA-hours MM activity**, which is:
- Globally rate-sensitive (explains ρ(X_d, fed_funds) = -0.614)
- Endogenous to FX moves (explains T1 rejection)
- Concentrated in 1-2 protocol addresses (explains Cook's D dominance)

It is **NOT** retail Colombian hedge demand. The Abrigo product thesis (`project_abrigo_inequality_hedge_thesis`) requires **a partition that isolates retail flow** — which means filtering OUT Carbon DeFi addresses, not including them.

---

## §6. Source List

### Official documentation (HIGH credibility)
- [Mento.org main site](https://www.mento.org/) — stablecoin list, supply, 12M+ users / 140+ countries / $18.5B 2025 volume / 277M tx claim
- [Mento docs — Mobile wallets](https://docs.mento.org/mento-v3/other/getting-mento-stables/on-mobile) — Valora supports USDm/EURm/BRLm; MiniPay Pockets feature
- [MiniPay.to](https://www.minipay.to/) — 15M+ wallets / 430M+ tx
- [Minteo.com](https://minteo.com/) — COPM facts (BDO audit, fiat-backed, API focus)
- [Mento Reserve](https://reserve.mento.org/) — basket reserves disclosure
- [Mento blog: Announcing cCOP](https://www.mento.org/blog/announcing-the-launch-of-ccop---celo-colombia-peso-decentralized-stablecoin-on-the-mento-platform)
- [Celo governance CGP-0060](https://github.com/celo-org/governance/blob/main/CGPs/cgp-0060.md) — cCOP launch proposal

### Press / industry coverage (HIGH for stats with quotes)
- [Opera press 2025-09-16: MiniPay turns two, 10M wallets, 270M tx](https://press.opera.com/2025/09/16/minipay-turns-two-10-million-wallets/)
- [Opera press 2025-07-17: 8M wallets, 200M tx, 255% Q2 surge](https://press.opera.com/2025/07/17/minipay-surpasses-8-million-wallets/)
- [Opera press 2025-12-03: Opera × Celo strategic partnership extension to 2030](https://press.opera.com/2025/12/03/opera-and-celo-foundation-partnership/)
- [Opera press 2026-04-22: MiniPay $1M CELO mini-app builder incentive](https://press.opera.com/2026/04/22/minipay-builders-incentive-and-roadshow/)
- [Decrypt 2025-12: Opera/Celo scale partnership, 11M wallets / 700K DAU / 3M weekly USDT](https://decrypt.co/350750/opera-celo-scale-up-partnership-to-make-stablecoins-useful-for-millions-of-users)
- [MiniPay blog: 2 years of stablecoins in everyday payments](https://minipay.to/blog/minipay-2-years-stablecoins-everyday-payments)
- [Yahoo Finance: Minteo launches stablecoin settlement layer for LATAM](https://finance.yahoo.com/news/minteo-launches-stablecoin-based-settlement-130000239.html)

### Forum / governance (HIGH for community-DAO data)
- [Celo Colombia Report 2025 H1](https://forum.celo.org/t/celo-colombia-report-2025-h1/11456/1) — 82.5K cCOP tx, 11K holders, 4 merchants, BucksPay/TuCop integration
- [Celo forum: Mento rebrand strategic evolution](https://forum.celo.org/t/mento-stablecoin-rebranding-and-strategic-evolution/12639/1)
- [Celo forum: cCOP launch proposal](https://forum.celo.org/t/launch-of-ccop-colombia-s-first-decentralized-stablecoin/9211)
- [Celo forum Q4 2024 MiniPay update](https://forum.celo.org/t/minipay-update-q4-2024/10035) — 5M wallets / $80M Q4 P2P / $6.9M CICO
- [Celo forum: FX market liquidity strategy](https://forum.celo.org/t/creating-the-next-fx-market-a-strategy-to-attract-liquidity-to-celo/11840/17)

### Academic / regulator (HIGH for macro-correlation literature)
- [BIS WP 1340 (2025): Stablecoin flows and spillovers to FX markets](https://www.bis.org/publ/work1340.htm) — 1% inflow → 40bp parity widening; EM exposure
- [BIS WP 1219: Stablecoins, MMFs, monetary policy](https://www.bis.org/publ/work1219.pdf) — fed funds → stablecoin substitution
- [BIS WP 1270: Stablecoins and safe asset prices](https://www.bis.org/publ/work1270.pdf)
- [Federal Reserve FEDS Note 2025-12: Stablecoins and bank deposits](https://www.federalreserve.gov/econres/notes/feds-notes/banks-in-the-age-of-stablecoins-implications-for-deposits-credit-and-financial-intermediation-20251217.html)
- [IMF Discussion Paper 2025: Understanding Stablecoins](https://www.imf.org/-/media/files/publications/dp/2025/english/usea.pdf)
- [IMF WP 2025/141: International stablecoin flows](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025141-source-pdf.pdf)
- [IMF WP 2026/03: Stablecoin inflows and FX spillovers](https://www.imf.org/en/publications/wp/issues/2026/03/27/stablecoin-inflows-and-spillovers-to-fx-markets-575046)
- [arXiv 2507.13883: Stablecoins fundamentals survey](https://arxiv.org/html/2507.13883v1) — survey, EM as research gap
- [SSRN: Stablecoin runs and centralization of arbitrage (Yiming Ma et al.)](https://anthonyleezhang.github.io/pdfs/stablecoin.pdf) — USDT 6 arbitrageurs / 66% concentration; USDC 521 / competitive

### Industry research (HIGH-MEDIUM)
- [Chainalysis 2025: Sub-Saharan Africa crypto adoption](https://www.chainalysis.com/blog/subsaharan-africa-crypto-adoption-2025/) — Nigeria $92.1B, USDT 7%, March 2025 $25B Naira-devaluation surge
- [Chainalysis 2025: LATAM crypto adoption](https://www.chainalysis.com/blog/latin-america-crypto-adoption-2025/) — Colombia $44.2B, 48% stables; Brazil $318.8B
- [Stablecoin Insider 2026: 50 stats](https://stablecoininsider.org/stablecoin-statistics-in-2026/)

### Project memory cross-references (internal)
- `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_carbon_defi_attribution_celo.md`
- `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_carbon_user_arb_partition_rule.md`
- `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md`
- `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_inequality_hedge_thesis.md`
- `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_fx_vol_econ_complete_findings.md`

---

## §7. Confidence Levels Per Claim

| Claim | Confidence | Source basis |
|---|---|---|
| MiniPay 12.6M-15M wallets, 350-430M tx, Dec 2025 | HIGH | Multiple Opera press + Decrypt corroboration |
| MiniPay 87% P2P <$5, 60% USDT <$5, $0.001 fee | HIGH | Opera press 2025-09-16 direct quote |
| MiniPay USDT >> USDm/cUSD in holdings | HIGH | Opera press: "50% Celo gas in USDT"; 5M weekly USDT |
| MiniPay top growth: SA 860%, Ghana 357%, Kenya 177% | HIGH | Opera press 2025-09-16 |
| cCOP 82.5K tx / 11K holders / 4 merchants H1 2025 | HIGH | Celo forum H1 2025 report |
| cCOP and COPM are different tokens | HIGH | Multiple sources (Mento blog, Minteo.com, forum) |
| COPM (Minteo) 100K+ users early launch | MEDIUM | Single Yahoo Finance / Newswire source |
| Carbon DeFi protocol drives 52% of COPM Transfer events | HIGH | Project memory + Dune attribution research |
| Carbon DeFi diurnal UTC 13-17 NA-hours signature | HIGH | Project memory (Task 11.N.2) |
| Fed funds tightening → stablecoin outflow | HIGH | BIS WP 1219 + ECB + multiple papers |
| 1% stablecoin inflow → 40bp FX parity widening | HIGH | BIS WP 1340 (2025) |
| Colombian retail uses USDT/USDC, not cCOP/COPM, for hedge | HIGH | Chainalysis 48% stables / market share data |
| Carbon DeFi MM is *not* retail Colombian hedge demand | HIGH | §5 synthesis — multiple converging lines |
| Mento-specific macro-correlation papers exist | LOW | None found in arxiv / WebSearch |
| Valora MAU ~3M+ current | MEDIUM | Older Mento doc; no recent confirmation |
| GoodDollar / Mobius / Tropykus use Mento basket | LOW | Not confirmed in this research |
| Reframe to retail-only X_d will dramatically reduce sample | MEDIUM | Inferred from partition impact in project memory; not directly tested |

---

## §8. Unresolved Evidence Gaps Blocking Hypothesis Lock-In

1. **GAP-1: cCOP-vs-COPM address provenance audit** — Project memory file lists `0xc92e8fc2…` under "COPM" naming, but external sources resolve this to Mento's cCOP. A canonical address-and-ticker reconciliation is needed before locking next X_d hypothesis. Recommend running the address resolution check via Celoscan + Mento docs before the next plan iteration.

2. **GAP-2: Time-series of Mento-Broker swap volume by stablecoin** — Per-stable USDm/cCOP/COPM swap volume on the Mento Broker (excluding Carbon DeFi MM contracts) is not publicly aggregated. Would need direct Celo node query or Dune query against Mento Broker contract events.

3. **GAP-3: MiniPay USDm holdings/swap volume specifically (Colombia)** — Opera's stats lump USDT/USDC/cUSD; no Colombia × cUSD/USDm breakdown is publicly available. Celo Colombia DAO H1 2025 report has aggregate cCOP figures but not per-app breakdown.

4. **GAP-4: Single-observation Cook's D root cause** — 2026-03-06 dominates the Rev-2 fit. What macro event happened that week? Suspected candidates: (a) Fed pivot signal, (b) Latin America bond stress, (c) USDT/USDC redemption shock, (d) Mento Reserve event. Not directly investigated in this research; recommend checking macro calendar for that specific week before any reframe.

5. **GAP-5: Valora's Mento-stable user-base scale (current)** — last public figure is "3M+" from older Mento docs. Whether Valora is still a meaningful retail Mento surface (vs. having been eclipsed by MiniPay) is undocumented in 2025-2026 sources.

6. **GAP-6: GoodDollar / Ubeswap / other Celo dApp Mento integration intensity** — none of these have public usage stats segmented by Mento-stable. They are plausible Mento basket users but cannot be quantified from this research.

7. **GAP-7: Pre-rebrand cUSD↔USDm transition confounding the time series** — Mento rebrand happened in 2026; legacy Rev-2 data series may straddle the transition. Need to verify whether the X_d data construction handled cUSD-pre-rebrand vs USDm-post-rebrand consistently (per `project_mento_canonical_naming_2026`, address-level identity is preserved, so this should not affect on-chain queries — but worth verifying).

8. **GAP-8: Causal direction of `ρ(X_d, fed_funds) = -0.614`** — established literature predicts the same sign for *both* (i) global stablecoin demand → fed funds reaction AND (ii) fed funds → stablecoin demand. The observed correlation alone cannot disambiguate. Need an instrument or natural experiment (FOMC announcement-window approach per BIS WP 1219 methodology) to identify direction.

---

## End of report

**File path**: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-mento-userbase-research.md`
