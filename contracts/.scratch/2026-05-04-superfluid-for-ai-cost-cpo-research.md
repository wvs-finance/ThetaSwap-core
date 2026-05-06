---
research_memo: superfluid-for-ai-cost-cpo
author: trend-researcher (free-tier methodology)
date: 2026-05-04
scope: Superfluid streaming-payment integration with Pair D Stage-2+ Convex Payoff Option (CPO) hedge architecture for LATAM developers paying USD-denominated AI APIs / AI tooling
constraints: free-tier (WebSearch + public block explorers); EVM-only; LATAM scope (CO primary, MX/BR/AR/PE/CL broader); HALT-and-surface on free-tier-blocking sources
related_docs:
  - /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/CLAUDE.md (Abrigo Operating Framework)
  - contracts/docs/superpowers/specs/2026-05-04-pair-d-stage-2-v1.5-data-aggregation-design.md (current substrate scope; EVM-only pin)
  - contracts/.scratch/2026-04-27-m-research-ai-cost-x-decentralized-compute-basket.md (parked AI-cost X research)
  - contracts/.scratch/2026-04-27-onchain-proxies-for-proprietary-ai-cost.md (prior on-chain proxy research)
verdict_oneline: Superfluid is a viable continuous-time settlement primitive for the premium leg of an AI-cost CPO under free-tier methodology on Polygon / Base / Optimism / Arbitrum / Ethereum mainnet; AI-provider leg is BLOCKED (no native AI-API acceptance — x402 + USDC-on-Base is the dominant 2026 standard, not Superfluid streams); payout-leg integration is technically clean but creates a new path-dependence the current K·√σ derivation does not yet model.
---

# Superfluid for AI-Cost CPO — Research Memo

## §1. Superfluid protocol primer

Superfluid is a streaming-payment protocol on EVM chains that introduces continuous-time token transfers — balances update every block at a per-second flow rate rather than via discrete transfer events. The protocol's three load-bearing abstractions are:

**Constant Flow Agreement (CFA).** The CFA opens an open-ended stream from sender to receiver at a fixed flow rate denominated in wei-per-second. A flow rate of 385,802,469,135,802 wei/s is equivalent to ~1,000 token-units / month (3600 × 24 × 30 seconds). Once opened, the stream requires no per-block gas — balances are computed off the most-recent block timestamp times the flow rate. Streams persist until the sender explicitly closes them or until the sender's Super-Token balance is depleted, at which point the liquidation mechanism (§ below) fires. ([Superfluid CFA primer — Medium](https://medium.com/@jtriley15/the-superfluid-protocol-db16f57dfafb), [Superfluid Money Streaming docs](https://docs.superfluid.org/docs/protocol/money-streaming/overview))

**Instant Distribution Agreement (IDA).** The IDA is a one-to-many distribution primitive: a publisher allocates units to N subscribers, then triggers a single distribution call that splits a lump sum proportionally across all units in O(1) gas. IDA is the publisher-pays-many primitive (e.g., dividend payouts, airdrops, multi-recipient revenue shares); CFA is the one-to-one continuous-stream primitive. ([Superfluid SDK overview](https://v2.docs.superfluid.finance/docs/sdk/overview))

**Super Tokens.** The Super Token is the on-chain representation that aggregates an account's CFA + IDA effects on its balance. Most Super Tokens in active use are **ERC-20 wrappers** — `SuperTokenFactory.createERC20Wrapper(address erc20, …)` deploys a UUPS proxy that wraps any underlying ERC-20 (USDC → USDCx, DAI → DAIx, etc.). Wrapper deployment is **permissionless**: anyone can call the factory, the deployer receives no admin powers, and Super-Token logic upgrades are governed by Superfluid Protocol Governance. ([Super Token Deployment Guide — superfluid-org](https://github.com/superfluid-org/protocol-monorepo/wiki/Super-Token-Deployment-Guide), [ERC20 wrapper docs](https://github.com/jelilat/superfluid-docs/blob/master/protocol-overview/super-tokens/erc20-wrapper-tokens.md))

**Liquidation / solvency.** Opening a stream requires a small **buffer deposit** held by the protocol (governance-set parameter, typically ~1 hour of stream value). When the sender's balance drops below the buffer threshold, the stream becomes "critical." A three-phase liquidation begins: **Patrician period** (only the Patrician Incentive Contract / TOGA-winner can liquidate and claim the buffer reward), then **Plebs period** (anyone can liquidate, partial buffer reward), then **Pirate period** (post-insolvency, sentinel-of-last-resort closes the stream and the buffer is fully consumed to make the protocol whole). ([Superfluid Liquidations & TOGA docs](https://docs.superfluid.org/docs/protocol/advanced-topics/solvency/liquidations-and-toga), [Stream buffers help-center](https://help.superfluid.finance/en/articles/5744874-how-do-stream-buffers-work-in-superfluid))

This liquidation discipline is **central to the premium-leg integration**: if a wage-earner's COPM-wrapped Super Token balance hits zero mid-month, the premium stream auto-terminates. From the CPO vault's perspective, this is desirable (no deficit accumulation), but from the holder's perspective it implies the hedge silently lapses if wage-receipt cadence is mis-aligned with stream burn rate.

**Chain support (EVM-only, the framework's pin).** Superfluid's `@superfluid-finance/metadata` npm package enumerates 9 mainnet networks. Per Superfluid's own subscription-product page and protocol blog: **Polygon, Optimism, Arbitrum, Avalanche, BNB Chain, Gnosis Chain, Celo, Base, Ethereum mainnet** are all supported. ([Superfluid metadata package — npm](https://www.npmjs.com/package/@superfluid-finance/metadata), [Superfluid on Base announcement — Medium](https://medium.com/superfluid-blog/superfluid-protocol-is-now-live-on-base-54029978e8a6), [Superfluid Subscriptions launch](https://superfluid.org/post/announcing-superfluid-subscriptions), [Superfluid on Optimism+Arbitrum announcement](https://medium.com/superfluid-blog/superfluid-protocol-is-live-on-optimism-and-arbitrum-3a1f09df541)) **Confirmed for the framework's anchor chains: Polygon ✓, Celo ✓, Base ✓, Arbitrum ✓, Optimism ✓, Ethereum mainnet ✓.**

**Free-tier observability.** Superfluid maintains hosted subgraphs on The Graph for every supported chain. The schema exposes `flowUpdatedEvent` (CFA stream open / update / close), `streamPeriodStarted`, `accountTokenSnapshot`, `superToken`, and aggregate higher-order entities. Every CFA event is queryable via GraphQL with no API key on Superfluid's hosted endpoints; The Graph's hosted-service tier is free for moderate volumes. ([Superfluid Subgraph docs](https://docs.superfluid.org/docs/sdk/money-streaming/subgraph), [Superfluid v1 Subgraph blog](https://medium.com/superfluid-blog/introducing-the-v1-superfluid-subgraph-b0b59ef4ccf9), [protocol-monorepo schema.graphql](https://github.com/superfluid-org/protocol-monorepo/blob/dev/packages/subgraph/schema.graphql)) Alternative indexers — SQD Network (free tier per its docs), public-RPC `eth_getLogs` against the CFA contract — are also available; the Stage-2 v1.5-data spec already pins SQD as a primary indexer. ([SQD docs](https://docs.sqd.ai/), [Subsquid free tier confirmation](https://www.sqd.ai/))

**Token compatibility for the LATAM-dev population.** USDC, USDT, DAI all have wrapped Super Tokens deployed on Polygon, Base, Optimism, Arbitrum, Ethereum mainnet (USDCx Polygon at `0xCAa7349CEA390F89641fe306D93591f87595dc1F`). ([Polygonscan USDCx](https://polygonscan.com/address/0xCAa7349CEA390F89641fe306D93591f87595dc1F)) Mento USDm, COPm, BRLm, KESm and Minteo COPM **do not appear to have official Super-Token wrappers as of 2026-05** — the search did not surface any Mento × Superfluid integration announcement, and Minteo's product surface (per [Minteo press release](https://www.newswire.com/news/minteo-launches-stablecoin-based-settlement-layer-for-latin-america-22295376)) is fiat-rails / settlement-layer, not streaming-rails. **HALT-AND-SURFACE flag**: a deployment-side question for any future M-sketch is whether the Mento and Minteo tokens need their Super-Token wrappers deployed permissionlessly (the framework can do this — `SuperTokenFactory.createERC20Wrapper(0x8A567e2aE79CA692Bd748aB832081C45de4041eA, …)` for Mento V2 COPm on Celo — but the wrapper has no liquidity nor wider ecosystem until other apps adopt it).

## §2. Three-leg integration architecture

### Leg 1 — Premium leg (developer → CPO vault)

**Mechanics map.** The wage-earner opens a CFA stream from their wage-receiving wallet to the CPO vault's premium-receiving address. The flow rate equals the premium-per-second: e.g., a $20/month premium = $20 × 10⁶ / (30 × 24 × 3600) ≈ 7.72 USDC-units/second = 7.72 × 10¹² wei/s for USDCx (which has the underlying USDC's 6 decimals). The vault's premium-accumulator entitlement is computed as `flowRate × elapsed_time` since stream-open; no per-block gas cost is incurred by either party once the stream is open. ([Money Streaming docs](https://docs.superfluid.org/docs/protocol/money-streaming/overview))

**On-chain observability.** The CFA contract emits a `FlowUpdated` event on every open / update / close, with fields `(token, sender, receiver, flowRate, oldFlowRate, totalAmountStreamedUntilTimestamp, …)`. Higher-order subgraph entities (`stream`, `accountTokenSnapshot`) aggregate per-pair lifetime. Filtering by `receiver = <CPO vault address>` exhaustively partitions premium-leg activity. This is **identical in indexability to Mento Broker / Carbon TokensTraded** — same GraphQL substrate, same SQD-Network ingest path, same `eth_getLogs` fallback.

**Free-tier-compatible.** Yes. Superfluid hosted subgraph + SQD free tier + public RPC are all available with no paid services required. The volume profile is favorable: a single developer-wallet generates O(1) `FlowUpdated` events per stream lifecycle (open + close + 0–N updates), versus O(many) per month of discrete transfers — Superfluid is **lighter** on indexer load than equivalent push-payment cadence.

**Failure modes.** The dominant failure is **buffer-depletion liquidation**. If the wage-earner's USDCx (or COPMx, BRLmx, etc.) balance falls below the protocol's solvency threshold, the stream is forcibly closed during the Patrician/Plebs period — the buffer is paid to the liquidator as a reward and the holder loses ~1 hour of premium value as a penalty. ([Liquidations & TOGA](https://docs.superfluid.org/docs/protocol/advanced-topics/solvency/liquidations-and-toga)) For the LATAM-dev wage-cadence reality (irregular-frequency wage receipts, multi-currency leg), this is a **non-trivial UX risk**. Mitigations: (a) periodic top-up automation (Stroller Protocol or equivalent — see [Stroller-Protocol on GitHub](https://github.com/DAM-Protocol/Stroller-Protocol)); (b) over-provisioned buffer at stream-open; (c) discrete monthly payment fallback if streaming creates more failure surface than it eliminates.

**Cross-chain.** If the wage-earner holds Minteo COPM on **Polygon** and the CPO vault settles on **Base** or **Arbitrum** (Panoptic V2's deployment targets), there is no in-protocol cross-chain stream — Superfluid CFA is per-chain. Bridging architecture must precede the stream: e.g., bridge Polygon-COPM → Polygon-USDC → Base-USDC via LayerZero / Across / Stargate, then `upgrade()` to USDCx-on-Base, then open the CFA. **This adds a discrete bridging-event UX step that streaming was supposed to eliminate** — a tension the M-sketch must resolve. The cleanest topology is single-chain: deploy CPO vault on the same chain as the wage-token (e.g., Polygon if Minteo COPM is the wage substrate). Per CLAUDE.md the framework's anchor chain for Mento V2 is Celo, which Superfluid supports — so a Celo-native CPO vault using Mento USDm / COPm wrapped Super-Tokens is mechanically clean (after the wrappers are deployed; see §1 HALT flag).

### Leg 2 — Payout leg (CPO vault → developer's AI-spend wallet)

**Mechanics map.** The CPO payoff Π(σ_T) is conventionally a **lump sum at expiry T** in the Π = K·√σ_T derivation. Replacing this with a Superfluid stream means the vault opens a CFA from itself to the developer's AI-spend wallet at a flow rate calibrated to deliver Π over a payout window [T, T + Δ]. This is mechanically identical to Mode/Sablier-style vesting streams.

**Why this might matter for the CPO economics.** Streaming payout is a **risk-management tool, not just UX polish**: lump-sum payout creates a single-block sink-cliff in the vault's USDC balance on expiry day; streaming spreads the sink across Δ seconds, giving the vault treasury time to rebalance LP positions, harvest premium tail, and source liquidity for the next epoch's hedges. From the developer's perspective, streamed payout matches the spending profile of AI-API consumption (continuous, not lump-sum), which is the **natural hedge match**.

**On-chain observability.** Identical to Leg 1 — `FlowUpdated` events emitted, indexable on the same subgraph. From a v1.5-data substrate-side perspective, payout-leg streams are observable structural exposure of the vault's entire premium-paying customer base.

**Failure modes.** Vault-side liquidation risk if vault USDCx balance falls below the buffer threshold mid-payout — would require vault treasury management to keep streams solvent.

### Leg 3 — AI-provider leg (developer → AI API vendor)

**Mechanics map.** The developer opens a CFA from their AI-spend wallet to the AI API provider's wallet, denominated in USDCx. The provider must (a) have a wallet that can receive USDCx Super-Tokens, (b) have a back-end accounting layer that converts received-USDCx into API-key credit at the spot rate.

**Reality check (2026-05 state).** **No major AI API provider — Anthropic, OpenAI, Replicate, Together AI, Cursor — accepts Superfluid streams natively.** All web-search probes returned third-party intermediaries (Pay With Moon, BotFundr, Coda One virtual cards, ClaudeStore, paywithmoon) that accept USDC / USDT and bridge to credit-card-style billing on the AI provider's side. No native Superfluid integration at any major LLM API vendor was found. ([How to pay for Claude API with crypto — SolCard](https://www.solcard.cc/blog/pay-claude-ai-with-crypto), [BotFundr](https://botfundr.com/), [Hyperbolic GPU + Inference crypto payments](https://www.hyperbolic.ai/blog/pay-for-gpu-and-ai-inference-models-with-crypto))

**Closest analogs.** Two industry-scale flows have moved fast in 2025-2026 and are competing for the AI-API-payment standard:

1. **x402 (Coinbase + Linux Foundation)** — HTTP 402-based on-demand USDC payment over Base / Polygon / Arbitrum / World / Solana. Coinbase facilitator processes ERC-20 payments with a 1,000-tx/month free tier. As of Mar 2026 x402 had processed >119M transactions on Base + 35M on Solana, ~$600M annualized volume. Supported by OpenAI, Google, Circle, Stripe. AI-agent frameworks (LangChain, CrewAI, AutoGPT, Claude MCP) ship x402 adapters out-of-box. ([x402.org](https://www.x402.org/), [Coinbase x402 docs](https://docs.cdp.coinbase.com/x402/welcome), [Coinbase x402 launch announcement](https://www.coinbase.com/developer-platform/discover/launches/x402))

2. **Stripe Crypto / Agentic Commerce Protocol (ACP)** — Sep 2025 Stripe + OpenAI partnership; Stripe launched x402-on-Base USDC machine payments in Feb 2026 enabling AI agents to charge each other via stablecoin rails. ([Stripe x402 launch — TheStreet](https://www.thestreet.com/crypto/markets/google-openai-circle-join-hands-for-agentic-payments), [Stripe stablecoins newsroom](https://stripe.com/newsroom/news/tour-newyork-2025), [Stripe + crypto agents — Paypers](https://thepaypers.com/crypto-web3-and-cbdc/news/stripe-launches-crypto-based-payment-system-for-ai-agents))

**Conclusion for the AI-provider leg.** Superfluid streams as direct AI-API payment is **not a 2026 reality**. The dominant architecture is **discrete USDC payments on Base via x402 / Stripe**, denominated in USD (no streaming primitive). For an Abrigo CPO architecture, this means the AI-provider leg cannot use Superfluid natively — the natural design is: CPO vault streams USDCx to developer (Leg 2) → developer downgrades USDCx → USDC at the moment of API call → x402 / Stripe pays the AI provider. The streaming primitive lives only on the upstream-of-developer side; the AI provider sees discrete USDC.

## §3. AI-API-provider acceptance of Superfluid

Direct survey of 2026-05 state for the AI providers most relevant to a LATAM-developer population:

| Provider | Accepts Superfluid streams? | Accepts native USDC? | Accepts crypto via 3rd party? | Source |
|---|---|---|---|---|
| Anthropic / Claude API | No | No (Stripe only) | Yes (BotFundr, Pay With Moon, Coda One Visa) | [SolCard guide](https://www.solcard.cc/blog/pay-claude-ai-with-crypto), [Anthropic billing](https://support.anthropic.com/en/articles/8114526-how-will-i-be-billed) |
| OpenAI | No | x402-via-Stripe (Feb 2026) | Yes (Pay With Moon, ClaudeStore) | [Stripe x402 partnership](https://www.thestreet.com/crypto/markets/google-openai-circle-join-hands-for-agentic-payments), [paywithmoon OpenAI](https://paywithmoon.com/merchants/open-ai) |
| Cursor | No | No | Yes (Pay With Moon, Coda One) | [Coda One Cursor](https://www.codaone.ai/pay-with-crypto/cursor/), [paywithmoon Cursor](https://paywithmoon.com/merchants/cursor) |
| Replicate | No | Not confirmed | Not confirmed | (no source found) |
| Together AI | No | Not confirmed | Not confirmed | (no source found) |
| Hyperbolic | No | Yes (USDC, USDT, DAI on Base) | Yes (native crypto) | [Hyperbolic crypto payments blog](https://www.hyperbolic.ai/blog/pay-for-gpu-and-ai-inference-models-with-crypto) |

**Pattern.** USDC discrete payments are reaching mainstream AI-API acceptance (x402 + Stripe is the standard); **streaming-payment AI APIs do not exist in commercial form as of 2026-05**. There is no Superfluid → API-key paymaster contract reported in any of the searched sources. The closest design pattern that *could* exist — and would be a research / dev-tooling opportunity for the framework — is a paymaster contract that:

1. accepts an inbound CFA stream from developer in USDCx,
2. integrates a balance accumulator,
3. periodically (e.g., every block, or on a credit-buy-trigger threshold) downgrades USDCx → USDC,
4. routes USDC to AI provider via x402 / Stripe / API-key-buying intermediary,
5. credits the developer's API quota.

This is a **net-new infrastructure piece**. It does not exist today. Building it is out of scope for the CPO design spec but is a candidate Stage-3 dev-stack contribution.

## §4. AI-developer-population observability via Superfluid (future-iteration substrate consideration)

If LATAM developers WERE to adopt Superfluid for AI-API-spend streams (Leg 3 above, which today is hypothetical given §3 findings), a **new substrate-side observability layer** opens up. Specifically:

**Per-developer monthly USD AI-spend = time-integral of outbound stream(s).** Concretely: query subgraph for `flowUpdatedEvent` records where `sender = <developer wallet>` and `receiver ∈ {<known AI-provider receiver wallets>}`; for each stream interval, integrate `flowRate × (end_block_ts − start_block_ts)`; sum across all such streams in a month. This yields a continuous-time, exhaustive measure of the developer's USD AI-spend, denominated in whatever Super-Token wraps USDC on the chain.

**Aggregate LATAM-developer AI-spend = supply-share-weighted aggregator.** Assuming a tagging methodology (the same kind already proven in Pair D Stage-2 v1.5-data — combining on-chain heuristics + off-chain wallet labels; see e.g., the Mexican / Colombian / Argentine wallet-cohort filters in the v1.5-data spec §10), filter by LATAM-tagged sender wallets paying to known AI-provider receiver wallets and apply the same aggregation methodology already specified for the COP-corridor.

**Why this matters for the framework.** The CLAUDE.md "Abrigo Operating Framework" defines (Y, M, X) iteration where X is the *major risk* blocking a target population's wage→capital transition. For LATAM developers, **AI-API USD-cost is a candidate X** (the prior parked AI-cost-X research in `2026-04-27-m-research-ai-cost-x-decentralized-compute-basket.md` and `2026-04-27-onchain-proxies-for-proprietary-ai-cost.md` already explored synthetic / index-based approximations). Superfluid-stream observability would convert a currently-unobservable X (off-chain credit-card AI-spend) into a substrate-native observable, structurally identical to the COP-corridor substrate already in scope.

**Future-iteration substrate consideration.** This is recorded here as **a candidate v1.5-data extension if/when a parallel (Y, X) iteration lands** (e.g., Y = LATAM-dev AI-spend / wage ratio, X = USD/local-FX or AI-API base-rate). **Do NOT add to v1.5-data now.** The current Pair D iteration's a_s population, Y, and X are committed; opening a new substrate requires a new iteration. The note here is to make the substrate viability legible to the next iteration's M-research dispatch.

**Critical pre-condition for this consideration to bind.** AI-API providers must accept Superfluid streams (or a paymaster contract per §3 must exist that bridges Superfluid → API-key purchase). Per §3, neither holds in 2026-05. Until that changes, AI-spend remains off-chain-observable only — no Superfluid substrate signal exists to index.

## §5. Economic-analytical implications for the CPO model

The Pair D Stage-2 CPO architecture conventionally derives the convex payoff Π = K · √σ_T (or analogous form) under **discrete settlement at expiry T**: premium paid at t=0 in lump sum, payoff received at t=T in lump sum, σ_T realized over [0, T]. Streaming integration changes three pieces of this calculus.

**Streaming premium changes a_l economics.** Premium-leg streaming converts a discrete monthly cash-out into a continuous wage-aligned outflow. From the holder's wage-earner-economics perspective, this is **strictly Pareto-improving** in the cash-flow-matching dimension (no need to set aside a monthly lump for premium — premium accretes at the same per-second cadence as the wage flows in). From the CPO vault's premium-revenue perspective, the integral of `flowRate × T` over the hedge window equals the discrete premium provided (a) `flowRate = premium / T`, and (b) the stream remains solvent through T (per the §1 liquidation analysis). Conditional on solvency, **the discrete-time Π = K · √σ_T derivation continues to hold**: premium revenue is the same scalar; only the temporal collection profile changes.

**Streaming payout changes Π payoff structure — re-derivation may be required.** Replacing the lump-sum Π payoff with a streaming payout over [T, T + Δ] introduces **time-value-of-money discounting** that the conventional K · √σ_T derivation does not include. Concretely, the present-value of a payout stream of total notional Π over Δ seconds at risk-free rate r is `Π · (1 − exp(−rΔ)) / (rΔ)`, which approaches Π only as Δ → 0. For Δ = 1 month and r = 5% APR, the discount factor is ~0.998 — *de minimis* in the LATAM-dev premium magnitude (premium ≈ $20/mo, payout cap ≈ $200-500/mo). **Practical conclusion:** the K · √σ_T derivation can absorb streaming-payout under a small discount-factor adjustment; **no fundamental re-derivation is needed** unless Δ is large (multi-quarter payout) or r is high (LATAM local-currency rates of 10-15% would push the adjustment to 1-2%, which could matter at hedge-portfolio scale but not at single-position-pricing scale).

**Path-dependence of streaming AI-spend creates a new exposure profile.** This is the substantive economic point. The conventional CPO hedges a **point-in-time σ_T** — the realized USD/local-FX volatility over [0, T]. But the developer's actual AI-spend exposure is **path-dependent**: it depends not only on σ_T but on the realized FX path, because each second of API-call activity is priced at that-second's spot FX, integrated over the hedge window. Formally, the developer's realized AI-cost-in-local-currency over [0, T] is `∫₀ᵀ usd_spend_rate(t) · fx(t) dt`, which is not a function of σ_T alone — it depends on the realized fx(t) trajectory.

**Implication.** If the CPO is meant to **fully hedge** the developer's realized AI-cost path, the K · √σ_T payoff is **mis-specified** — it pays based on terminal volatility, not on the path-integral of FX × spend-rate. The mis-specification is a **basis risk**: σ_T-based payoff and path-integrated AI-cost will be highly correlated (per the Pair D β=+0.137 lag-6 result), but not identical. For a first-order Stage-2 M-sketch this basis is acceptable — the framework's ideal-scenario clause in CLAUDE.md permits modeling the cleanly-settling payoff first. For a Stage-3+ refinement, the correct M structure would be either (a) a path-dependent option (Asian or barrier variant of the CPO) settling on `∫ fx(t) dt` rather than σ_T, or (b) a portfolio of multiple CPOs at staggered maturities approximating the path.

**Streaming AI-spend itself (Leg 3 hypothetical) creates a continuous-time hedging-need profile** — the developer's hedge requirement updates per-second as their cumulative spend accumulates. A single fixed-strike CPO captures this only on average; a basket of strikes or a streaming-replenishment hedge structure would be the higher-fidelity match. **Out of scope for the immediate v1.5-methodology work; flagged for Stage-3 M-sketch design space.**

## §6. Free-tier compliance verdict

**Verdict: Y — Superfluid integration can be researched, observed, and architected within free-tier methodology**, with the following itemized compliance check:

| Capability | Free-tier source | Confirmed? | Note |
|---|---|---|---|
| CFA event indexing (FlowUpdated) | Superfluid hosted subgraph (The Graph) | Y | No API key required for hosted-service queries. ([Superfluid subgraph docs](https://docs.superfluid.org/docs/sdk/money-streaming/subgraph)) |
| Alternative event indexing | SQD Network free tier | Y | Already pinned in Pair D Stage-2 v1.5-data spec §3.bis. ([SQD docs](https://docs.sqd.ai/)) |
| Public-RPC fallback (eth_getLogs) | Alchemy 30M CU/mo free; Quicknode free; public chain RPCs | Y | Identical to Pair D Stage-2 v1.5-data fallback path. |
| Super Token wrapper deployment | One-shot tx via `SuperTokenFactory.createERC20Wrapper(…)` | Y | Cost is gas only; no service fee. ([Super Token Deployment Guide](https://github.com/superfluid-org/protocol-monorepo/wiki/Super-Token-Deployment-Guide)) |
| Subgraph-schema reference | `superfluid-org/protocol-monorepo` schema.graphql | Y | Open-source; no auth. |
| Cross-chain bridging (if multi-chain CPO) | Public bridges (Across, Stargate, LayerZero front-end) | Partial | Bridging itself is permissionless; programmatic-monitoring tools may have free-tier limits — surface case-by-case. |

**Minimal paid-tier escalation.** None required for the research and architecture-design phase. If Stage-3 deployment requires sub-second-latency stream observability (e.g., for a real-time risk dashboard), The Graph's paid Subgraph Studio tier or a dedicated SQD squid would be candidates — but this is **deployment-stage**, not design-stage, and is identical in cost profile to Pair D's existing substrate-monitoring needs.

## §7. Integration with Panoptic V2 (forward-note)

Panoptic V2 is the framework's settlement-rail for Convex Payoff Options. Per Panoptic's own docs, **Panoptic V2 supports any ERC-20 token as collateral / underlying** for its perpetual options ([Panoptic Smart Contracts overview](https://panoptic.xyz/docs/contracts/smart-contracts-overview)) and has expanded in V2 to support Uniswap V4 pools including pools with hooks ([Panoptic V2 audit on Code4rena](https://code4rena.com/audits/2025-12-panoptic-next-core)). The protocol is **streaming-premium-native at its core**: option buyers continuously pay "streamia" to option sellers as the position unfolds — a discrete-event design at the AMM-LP-fee level, not a Superfluid-CFA design at the wallet-balance level. Panoptic's streamia is internal accounting; Superfluid's CFA is an external Super-Token-balance abstraction. The two streaming primitives are **architecturally orthogonal** and **mechanically composable** without protocol-level integration: a developer's wallet streams USDCx to an "Abrigo CPO vault" wallet via Superfluid CFA; the Abrigo vault internally manages a Panoptic V2 perpetual-options position whose own streamia accounting is in USDC (not USDCx) at the Panoptic-pool level.

**Open question (not researched in depth here).** Whether Panoptic V2's collateral whitelist accepts the Super-Token-wrapped form (USDCx) directly, or requires the underlying (USDC). The 2026-05 web search did not surface a Panoptic × Superfluid integration announcement. The likely architecture is: vault holds USDCx on the receive-leg (from developer), `downgrade()`s to USDC at the moment of Panoptic-position adjustment, then `upgrade()`s the residual back to USDCx for any payout-leg streaming. This is a **vault-treasury-management concern**, not a protocol-integration concern; both protocols compose cleanly via the standard ERC-20 boundary.

## §8. Sources cited

**Superfluid protocol primer**
- [Superfluid CFA primer — Medium](https://medium.com/@jtriley15/the-superfluid-protocol-db16f57dfafb)
- [Superfluid Money Streaming overview docs](https://docs.superfluid.org/docs/protocol/money-streaming/overview)
- [Superfluid SDK overview v2 docs](https://v2.docs.superfluid.finance/docs/sdk/overview)
- [Super Token Deployment Guide — superfluid-org wiki](https://github.com/superfluid-org/protocol-monorepo/wiki/Super-Token-Deployment-Guide)
- [ERC20 wrapper Super Tokens docs](https://github.com/jelilat/superfluid-docs/blob/master/protocol-overview/super-tokens/erc20-wrapper-tokens.md)
- [Super Token Factory wiki](https://github.com/superfluid-org/protocol-monorepo/wiki/About-Super-Token-Factory)
- [Liquidations & TOGA docs](https://docs.superfluid.org/docs/protocol/advanced-topics/solvency/liquidations-and-toga)
- [Stream buffers help-center article](https://help.superfluid.finance/en/articles/5744874-how-do-stream-buffers-work-in-superfluid)
- [Stroller-Protocol auto-top-up](https://github.com/DAM-Protocol/Stroller-Protocol)

**Chain support**
- [Superfluid metadata package — npm](https://www.npmjs.com/package/@superfluid-finance/metadata)
- [Superfluid on Base announcement — Medium](https://medium.com/superfluid-blog/superfluid-protocol-is-now-live-on-base-54029978e8a6)
- [Superfluid on Optimism + Arbitrum — Medium](https://medium.com/superfluid-blog/superfluid-protocol-is-live-on-optimism-and-arbitrum-3a1f09df541)
- [Superfluid Subscriptions launch (chain list)](https://superfluid.org/post/announcing-superfluid-subscriptions)
- [Superfluid Ethereum Mainnet announcement](https://superfluid.org/post/superfluid-is-now-available-on-ethereum-mainnet-in-early-access)
- [Polygonscan USDCx contract](https://polygonscan.com/address/0xCAa7349CEA390F89641fe306D93591f87595dc1F)

**Subgraph / observability**
- [Superfluid Subgraph docs](https://docs.superfluid.org/docs/sdk/money-streaming/subgraph)
- [Introducing Superfluid v1 Subgraph — Medium](https://medium.com/superfluid-blog/introducing-the-v1-superfluid-subgraph-b0b59ef4ccf9)
- [Superfluid subgraph schema.graphql](https://github.com/superfluid-org/protocol-monorepo/blob/dev/packages/subgraph/schema.graphql)
- [SQD Network docs](https://docs.sqd.ai/)
- [SQD landing](https://www.sqd.ai/)

**AI-API payment landscape**
- [x402 protocol home](https://www.x402.org/)
- [Coinbase x402 docs](https://docs.cdp.coinbase.com/x402/welcome)
- [Coinbase x402 launch announcement](https://www.coinbase.com/developer-platform/discover/launches/x402)
- [Stripe x402 + OpenAI partnership — TheStreet](https://www.thestreet.com/crypto/markets/google-openai-circle-join-hands-for-agentic-payments)
- [Stripe stablecoin / agentic commerce newsroom](https://stripe.com/newsroom/news/tour-newyork-2025)
- [Stripe crypto for AI agents — Paypers](https://thepaypers.com/crypto-web3-and-cbdc/news/stripe-launches-crypto-based-payment-system-for-ai-agents)
- [Anthropic billing docs](https://support.anthropic.com/en/articles/8114526-how-will-i-be-billed)
- [Pay Anthropic with crypto — SolCard guide](https://www.solcard.cc/blog/pay-claude-ai-with-crypto)
- [BotFundr — Claude with USDC](https://botfundr.com/)
- [Pay With Moon — OpenAI](https://paywithmoon.com/merchants/open-ai)
- [Pay With Moon — Cursor](https://paywithmoon.com/merchants/cursor)
- [Coda One — Cursor crypto payments](https://www.codaone.ai/pay-with-crypto/cursor/)
- [Hyperbolic — pay GPUs / inference with crypto](https://www.hyperbolic.ai/blog/pay-for-gpu-and-ai-inference-models-with-crypto)

**LATAM-stablecoin context**
- [Minteo — settlement layer for LatAm](https://minteo.com/)
- [Minteo COPM launch press release](https://www.newswire.com/news/minteo-launches-stablecoin-based-settlement-layer-for-latin-america-22295376)
- [Polygon LatAm dispatch](https://polygon.technology/blog/latam-dispatch-inflation-and-blockchain-projects-in-the-global-south)

**Panoptic V2**
- [Panoptic Smart Contracts overview](https://panoptic.xyz/docs/contracts/smart-contracts-overview)
- [Panoptic V2 Code4rena audit](https://code4rena.com/audits/2025-12-panoptic-next-core)
- [Panoptic perpetual-options paper (arxiv)](https://arxiv.org/html/2204.14232v3)

---

## Summary verdicts (one-paragraph for orchestrator)

**Premium leg (developer → CPO vault) via Superfluid CFA: VIABLE under free-tier on Polygon / Celo / Base / Arbitrum / Optimism / Ethereum mainnet using existing USDCx wrappers; LATAM-stablecoin support (USDm / COPm / BRLm / KESm / Minteo COPM) requires permissionless wrapper deployment per chain — cost is one tx + gas, not a protocol-integration project. Buffer-depletion liquidation is the non-trivial UX risk and needs Stroller-Protocol-style auto-top-up.**

**Payout leg (CPO vault → developer): TECHNICALLY CLEAN; introduces a small TVOM adjustment (<2% even at LATAM rates) to the Π = K·√σ_T derivation that is acceptable for Stage-2 M-sketch; full path-dependence (Asian / barrier variant) is a Stage-3 refinement.**

**AI-provider leg (developer → AI vendor) via Superfluid: BLOCKED — no major AI API accepts Superfluid streams as of 2026-05. The dominant 2026 standard is x402 (Coinbase + OpenAI + Circle + Stripe + Linux Foundation) on USDC over Base + Polygon + Arbitrum + Solana. Superfluid → x402 paymaster bridge is a net-new infrastructure piece that does not exist; constructing it is a candidate Stage-3 dev-stack contribution but is out of scope for the v1.5 work.**

**Future-iteration substrate consideration: IF the next-iteration (Y, X) lands on LATAM-developer AI-spend, AND Superfluid streaming becomes an accepted AI-API payment method, THEN AI-spend becomes a substrate-native observable indexable on the same SQD-Network / hosted-subgraph rails already in v1.5-data scope. Both conditionals must hold; today, neither does.**

**Free-tier compliance: PASS. All research, architecture, and substrate observability achievable on free-tier (hosted Superfluid subgraph + SQD Network + Alchemy 30M CU/mo + public RPCs).**

**Out-of-scope confirmations: Panoptic × Superfluid integration is ARCHITECTURAL ORTHOGONAL — both compose via the ERC-20 boundary at the vault-treasury layer; no protocol-level integration exists or is required for the M-sketch.**
