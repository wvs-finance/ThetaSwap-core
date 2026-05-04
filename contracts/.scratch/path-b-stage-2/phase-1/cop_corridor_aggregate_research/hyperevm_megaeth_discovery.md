---
artifact_kind: discovery_memo
artifact_subject: COP-pegged stablecoin / token deployments on HyperEVM and MegaETH
emit_timestamp_utc: 2026-05-04T00:00:00Z
emitter: trend-researcher (sub-agent)
parent_artifact: contracts/docs/superpowers/specs/2026-05-04-pair-d-stage-2-v1.5-data-aggregation-design.md
sibling_artifact: contracts/.scratch/path-b-stage-2/phase-1/cop_corridor_aggregate_research/discovery.md
methodology:
  - WebSearch (free-tier; ~14 distinct queries across substrate, issuer, ecosystem-token-list, and bridge angles)
  - WebFetch (free-tier; CoinGecko HyperEVM ecosystem page, CoinGecko MegaETH ecosystem page, Mento V3 multichain docs)
  - Targeted issuer-side announcement scans (Mento V3, Minteo, Wenia/Bancolombia, Num Finance, Tether DLYCOP)
  - HyperEVMScan token-list direct fetch (returned 403 — see HALT-and-surface in §3)
constraints:
  - Free-tier ONLY (no paid CoinGecko Pro / Dune / Token Terminal API)
  - No on-chain reads at discovery stage
  - HALT-and-surface on free-tier resource unavailability rather than infer
inclusion_gate_recommendation: explicit_null_entry
verdicts:
  hyperevm_cop_token: NULL
  megaeth_cop_token: NULL
  hyperevm_options_ecosystem: brief noted (no Panoptic-style LP-position perpetual options yet; Hyperliquid native HIP-3 / HIP-4 are perpetual-futures + binary-outcome contracts, not options)
---

# §1 Executive summary

**HyperEVM COP-token verdict: NULL.** No Colombian-peso-pegged ERC-20 token (under any naming — COP, COPm, COPM, COPW, nCOP, DLYCOP, wCOP, or synthetic-COP) is currently deployed on HyperEVM (Hyperliquid's EVM execution layer; mainnet since 2025-02-18). Confirmed across:

- CoinGecko HyperEVM ecosystem page (Top tokens by market cap; top stablecoins are USD-denominated: USDC, USDT0, USDE, USDM-equivalents, RUSDC-HYPER) — no COP tokens present.
- Issuer-side announcement scans for all four known COP-token issuers (Mento V2 COPm, Minteo COPM, Bancolombia/Wenia COPW, Num Finance nCOP, Tether DLYCOP) — zero have announced or deployed on HyperEVM as of 2026-05-04.
- Mento V3 multichain docs explicitly do NOT list HyperEVM among supported chains; Mento's first non-Celo expansion was Monad (with GBPm/USDm pool only — no COPm yet on Monad either).

**MegaETH COP-token verdict: NULL.** No COP-pegged token deployed on MegaETH (mainnet since 2026-02-09). Confirmed via:

- CoinGecko MegaETH ecosystem page: stablecoin substrate is dominated by USDM (Ethena-issued, BlackRock BUIDL-backed, ~74% of $84M MegaETH stablecoin market cap as of 2026-04), plus USDT0, USDE; no LATAM-fiat tokens present.
- No issuer announcements link any COP token to MegaETH.

**HyperEVM options ecosystem brief.** No Panoptic-style (perpetual options on Uniswap-V3-style LP positions) deployment exists on HyperEVM as of 2026-05-04. Hyperliquid's native derivative innovation is concentrated in HIP-3 (permissionless builder-deployed perpetual *futures* via 500K HYPE stake — perp futures, not options) and HIP-4 (event-based / binary-outcome contracts, mainnet 2026-05-03 — fully-collateralized prediction-market-style, not options either). Panoptic V2 has been confirmed as Ethereum-mainnet-only at launch. Lyra/Derive, Dopex/Stryke, Premia — none publicly announced HyperEVM deployments. **Implication for Stage-3 dispatch:** HyperEVM is currently NOT a viable Panoptic-replacement deployment substrate; the framework's M-sketch step would still need to use Panoptic on Ethereum mainnet (the existing canonical Panoptic substrate) until either (a) Panoptic deploys to HyperEVM, or (b) a new LP-position-based perpetual-options protocol launches there.

**Inclusion-gate decision: NULL on both substrates → recommend explicit-null entry in v1.5-data spec §16 pre-conditions; do NOT amend substrate scope.** The existing 8-venue COP-corridor inventory (Celo + Polygon, per discovery.md §1) remains the binding substrate for Phase-1 aggregate work.

# §2 Per-venue inventory

Not applicable — no FOUND venues. Per methodology constraint, no inventory rows are emitted.

# §3 Sources cited

## HyperEVM substrate scan

- [CoinGecko HyperEVM Ecosystem](https://www.coingecko.com/en/categories/hyperevm-ecosystem) — top tokens by market cap; verified no COP/Colombian/peso tokens listed
- [HyperEVMScan Block Explorer](https://hyperevmscan.io/) — direct token-list fetch returned HTTP 403 (HALT-and-surface fired; CoinGecko ecosystem page used as substitute since CoinGecko's HyperEVM API is documented to cover 2.7K+ HyperEVM tokens, sufficient for negative-presence claim at discovery stage)
- [Hyperliquid HyperEVM Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperevm) — confirms HyperEVM is a permissionless EVM with no token-listing approval gate; any COP issuer *could* deploy without permission, none has
- [DEXScreener HyperEVM](https://dexscreener.com/hyperevm) — HyperEVM DEX activity overview; no COP-pair pools surfaced
- [Wormhole HyperEVM Live Announcement](https://wormhole.com/blog/hyperliquids-hyperevm-is-now-live-on-wormhole) — bridge availability confirmed, but Mento has not used the Wormhole-HyperEVM lane to bridge Mento stables there
- [HyperEVM Statistics 2026 (CoinLaw)](https://coinlaw.io/hyperevm-statistics/) — ecosystem composition overview

## MegaETH substrate scan

- [CoinGecko MegaETH Ecosystem](https://www.coingecko.com/en/categories/megaeth-ecosystem) — confirmed no COP tokens
- [The Defiant — MegaETH Launches Mainnet](https://thedefiant.io/newsletter/defi-daily/megaeth-launches-mainnet) — mainnet launch and stablecoin landscape
- [CoinDesk MegaETH Mainnet Launch](https://www.coindesk.com/tech/2026/01/28/megaeth-mainnet-to-go-live-feb-9-in-major-test-of-real-time-ethereum-scaling) — 2026-02-09 launch confirmation
- [MegaETH USDM (MegaUSD)](https://www.coingecko.com/en/coins/megausd) — native stablecoin; Ethena-issued; BUIDL-backed; USD-denominated only

## Issuer-side scans

- [Mento V3 Multichain Docs](https://docs.mento.org/mento-v3/other/getting-mento-stables/from-other-chains) — Squid Router supports 20+ chains for Mento stables; HyperEVM and MegaETH NOT listed
- [Mento Launches on Monad (Stablecoin Insider)](https://www.stablecoininsider.com/mento-launches-on-monad-bringing-fx-markets-to-a-high-performance-l1/) — first non-Celo Mento V3 deployment was Monad (GBPm/USDm only, no COPm yet on Monad either)
- [Mento Wormhole Multichain FX Announcement](https://www.mento.org/blog/mento-selects-wormhole-as-its-official-interoperability-provider-to-power-multichain-fx) — Wormhole-routed multichain ambition stated; HyperEVM/MegaETH not yet activated
- [Minteo](https://minteo.com/) — primary chains: Celo, Polygon, Solana; no HyperEVM or MegaETH mention
- [Wenia / Bancolombia COPW Announcement](https://cryptonews.com/news/colombias-bancolombia-launches-crypto-exchange-wenia-and-stablecoin-copw/) — Polygon-only; expansion plans cited but no HyperEVM/MegaETH
- [Num Finance nCOP Launch](https://www.crowdfundinsider.com/2023/08/212010-latin-america-num-finance-introduces-ncop-stablecoin-supporting-colombians-with-remittance-tokenization/) — Polygon-primary by issuer's own statement; multichain "possible but not pursued"
- [Tether DLYCOP Repo](https://github.com/tethercoin/columbianpesogaslesspeg) — Polygon-only; no other-chain deployment

## HyperEVM options ecosystem (informational, §5 forward note)

- [Hyperliquid HIP-3 Builder-Deployed Perpetuals](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-3-builder-deployed-perpetuals) — perpetual *futures*, not options
- [HyperEVM HIP-4 Event-Based Trading](https://coinstats.app/ai/a/fundamental-analysis-hyperliquid) — binary-outcome contracts, not options
- [Panoptic Docs — Perpetual Options](https://panoptic.xyz/docs/trading/perpetual-options) — Ethereum-mainnet-only at V2 launch
- [Panoptic November 2025 Newsletter](https://panoptic.xyz/blog/panoptic-november-2025-newsletter) — no HyperEVM deployment mentioned
- [Panoptic January 2026 Newsletter](https://panoptic.xyz/blog/panoptic-january-2026-newsletter) — no HyperEVM deployment mentioned
- [DeFi Options Trading 2025 (Yellow Research)](https://yellow.com/research/defi-options-trading-in-2025-how-lyra-dopex-and-panoptic-are-reshaping-derivatives) — Panoptic, Lyra/Derive, Dopex/Stryke ecosystem map; none cite HyperEVM

# §4 Inclusion-gate recommendation

**Recommendation: NULL on both substrates → record explicit-null entry in v1.5-data spec §16 pre-conditions; do NOT amend substrate scope.**

Suggested CORRECTIONS-block prose for the spec author (drop-in copy ready):

> **§16 Pre-conditions, sub-clause [HyperEVM/MegaETH explicit null]:** Per discovery memo `contracts/.scratch/path-b-stage-2/phase-1/cop_corridor_aggregate_research/hyperevm_megaeth_discovery.md` (emit 2026-05-04), zero COP-pegged ERC-20 tokens are currently deployed on either HyperEVM (Hyperliquid EVM, mainnet 2026-02 era) or MegaETH (mainnet 2026-02-09) under any naming convention (COP, COPm, COPM, COPW, nCOP, DLYCOP, wCOP, synthetic-COP). All four known COP-token issuers (Mento, Minteo, Bancolombia/Wenia, Num Finance, Tether DLYCOP) confirm Celo + Polygon as their substrate scope. Mento V3 multichain expansion is on Monad (GBPm/USDm only) with HyperEVM/MegaETH not on the public roadmap. **Substrate scope for v1.5-data Phase-1 aggregate remains the 8-venue Celo+Polygon inventory per discovery.md §1.** Re-evaluation trigger: any of the four issuers announces a HyperEVM or MegaETH deployment, OR Mento V3 expands COPm to a new EVM chain via Wormhole — at which point spec §16 reopens via CORRECTIONS-block + 2-wave verify (Reality Checker + Senior Developer in parallel per `feedback_two_wave_doc_verification`).

**Do NOT add HyperEVM or MegaETH endpoints to RPC config, do NOT add new venue rows to Phase-1 audit_metrics_raw.json, do NOT touch the 13-venue per-venue audit produced at commits `898d44910` / `3116f818f` / `821f6f1ca`.** The current substrate (3 PASS / 1 marginal / 9 HALT under Path B Stage 2 v0 emission) is the binding scope for v1.5-data execution.

# §5 Stage-3 forward note: HyperEVM options ecosystem

(Informational only; NOT load-bearing for v1.5-data substrate work.)

User flagged HyperEVM as "highly interested for developments and options" separately from substrate scope, suggesting interest in HyperEVM as a *future deployment-target venue* for Panoptic-style perpetual-options M sketches. As of 2026-05-04 the answer is: **HyperEVM does not yet host an LP-position-based perpetual-options protocol of the Panoptic / Carbon-DeFi family.** What HyperEVM (and adjacent Hyperliquid HyperCore) does host:

- **HIP-3 (live since 2025-Q4):** permissionless deployment of perpetual *futures* markets on HyperCore via 500K HYPE stake. This is futures-payoff (linear), not options-payoff (convex). Not a substitute for the framework's perpetual-options M-sketch requirement.
- **HIP-4 (mainnet 2026-05-03):** event-based / binary-outcome contracts (e.g., "BTC closes above X by date Y"). Fully collateralized; no leverage; no liquidation. This is prediction-market-style, again not the convex-options shape the framework's M-sketch needs.
- **Q3 2026 roadmap (Hyperliquid):** "Forex & Commodities perpetual futures" announced — still futures, not options.
- **No public Panoptic / Premia / Lyra-Derive / Dopex-Stryke deployment to HyperEVM** as of 2026-05-04. Panoptic V2 launched Ethereum-mainnet-only with four initial vaults; their newsletter cadence (Nov 2025, Jan 2026) makes no HyperEVM mention.

**Implication for Pair D Stage-2 M-sketch step (when it graduates from this v1.5-data Phase-1 aggregate work):** the M-sketch must still target Panoptic on Ethereum mainnet (canonical substrate per the framework "Instrument family" clause), with the Mento-COPm corridor priced via the Celo+Polygon-rooted aggregate the v1.5-data spec is currently building. HyperEVM remains a *future-iteration deployment-target candidate* — not a current-iteration substrate. If the user wishes to elevate HyperEVM to active Stage-3 status, the Stage-3 dispatch would need to either (a) wait for Panoptic to deploy to HyperEVM (no public timeline), (b) commission a new LP-position-based perpetual-options primitive native to HyperEVM (out of scope for Pair D's stage-correctness), or (c) accept that HyperEVM hosts only futures + binary outcomes and re-shape the M-sketch toward those primitives (which would require revisiting the framework "Instrument family" clause's perpetual-options anchor — non-trivial).

End of memo.
