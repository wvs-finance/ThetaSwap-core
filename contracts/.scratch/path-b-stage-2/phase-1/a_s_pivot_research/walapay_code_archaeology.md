# Walapay — Code Archaeology Report

**Author:** Investigation agent (Path B Stage-2 Phase-1, a_s pivot research)
**Date:** 2026-05-03
**Spec context:** `walapay_settlement_celo` was pre-pinned as a candidate `a_s` substrate in the Pair D Stage-2 spec frontmatter; this report determines whether the pin is structurally valid.
**Methodology:** Free-tier only — public GitHub repo enumeration via `gh api`, official docs via WebFetch (`docs.walapay.io`), ecosystem write-ups via WebSearch + WebFetch (Dfns announcement, Circle Alliance Directory, FIAT VC portfolio spotlight, Stableminded podcast page). No paid APIs.

---

## §1 GitHub presence

**No public repositories.** `https://github.com/walapay` returns the literal text *"walapay doesn't have any public repositories yet"* — 0 repos, 0 projects, 0 packages.

`gh search repos walapay --limit 10` returns empty. `gh search users walapay` returns no hits. The founders (Tom Borgers, Dimitri Borgers per FIAT VC portfolio post) have no public Walapay code under their personal handles either.

**Walapay is closed-source.** All technical reconstruction below is from official documentation (`docs.walapay.io`), partner announcements (Dfns, Circle), and a Stableminded podcast page.

---

## §2 Workflow pattern

### What the customer (B2B) does
Walapay is **B2B infrastructure**, not a consumer app. Customer types per the FIAT VC portfolio post and the Walapay homepage:

- **PSPs** (e.g. Nuvei) — instant stablecoin settlement, treasury management
- **Fintechs / neobanks** (e.g. Zarpay) — account issuance, collections, global payouts; "off-ramps for neobanks"
- **B2B payments companies** (e.g. Vizum) — emerging-market payouts
- **Payroll providers** — pay individuals and businesses globally
- **Marketplaces / SMBs** — global treasury, repatriation, supplier payments

Quoted from `docs.walapay.io/docs/overview`: *"Customers (individuals/businesses undergoing KYC/KYB), Accounts (virtual or external structures holding funds), and Payments (transfers between accounts)"*.

The flow:
1. Open virtual account(s) for a Customer (one per chain for digital-asset wallets, one per fiat currency for bank accounts)
2. Receive funds (fiat via local rail, or stablecoin into a wallet address)
3. Initiate Payment (fiat→fiat, fiat→stablecoin, stablecoin→fiat, stablecoin→stablecoin)
4. Settle within seconds (per FIAT VC: *"reducing settlement times from days to seconds"*)

### On-chain footprint
- **No deployed Walapay smart contracts.** Walapay's wallets are **Dfns MPC wallets**: per the Dfns announcement, *"Dfns runs on a secure key management system using advanced multi-party computation (MPC) and threshold signatures (TSS)"*. They support both *"self-custodial wallets"* and *"custodial wallets with built-in integrations for qualified custodians"*.
- **Chains supported (per Circle Alliance Directory):** Arbitrum, Avalanche, Base, Ethereum, OP Mainnet *("Show more"-truncated, but Celo is NOT in the visible list)*.
- **Stablecoins supported:** USDC + USDT (per `docs.walapay.io/docs/introduction`: *"2 stablecoins (USDC/USDT)"*), with Circle Products listed as USDC + EURC.
- **No Mento stablecoins.** No cUSD, cKES, cCOP, cREAL, USDm, KESm, COPm, BRLm references in any official document I could access.
- **Settlement on Polygon, Ethereum** appear in the Fiat-to-Stablecoin and Stablecoin-to-Fiat docs as canonical examples.

### Recurring vs one-shot obligation
**One-shot per Payment object.** Each `Payment` is a single transfer between two `Account` records. Recurring/streaming payments are not a primitive in the API. Payroll-provider customers may submit many payments on a recurring cadence externally, but Walapay itself sees each as an independent Payment.

### Who holds X-side vs Y-side risk
The customer (PSP/fintech) initiates a Payment specifying source amount + destination currency. From `docs.walapay.io/docs/fiat-to-stablecoin`: rates *"can only be guaranteed during EST trading hours"* (Mexico) and for SEPA *"the destination amount cannot be guaranteed"* — implying that **outside guaranteed windows, the customer (or end-recipient) bears FX risk between quote and settlement**. Walapay's "FX orchestration" routes through optimal liquidity providers; they take a spread but do not warehouse open FX positions (no public claim to inventory-FX risk in any source).

---

## §3 Utility function reverse-engineering

### Customer (B2B operator) maximises
- Settlement speed (advertised "seconds" vs T+2 traditional)
- Coverage (60+ currencies × 180+ countries via 100+ chains' MPC wallet support)
- Operational simplicity (one API endpoint replacing multi-PSP integration)
- Compliance offload (Walapay handles KYC/KYB)

### End-user (recipient of a Walapay-routed payout)
Receives fiat in local bank account or stablecoin in their own wallet. Their utility = nominal amount delivered, in the currency of their choice. They have no contract with Walapay.

### Walapay (operator) maximises
Per-transaction spread (FX margin + on-ramp/off-ramp fee). The FIAT VC portfolio post notes *"FX orchestration and credit solutions help businesses optimize liquidity"* — "credit solutions" hints at Walapay extending working-capital credit to PSP customers (an asset-side carry, not a vol-short position). $85M monthly volume × even ~30bps spread = ~$25K/day gross — order-of-magnitude rev figure consistent with their 40-customer base.

### FX risk absorbed by each party
- **PSP customer:** quote-to-settlement risk in non-guaranteed corridors (MX, EU SEPA per docs). Pays a guaranteed-rate premium during covered windows.
- **End-recipient:** none if PSP locks rate; otherwise inherits PSP's risk.
- **Walapay:** no public claim to warehoused FX. The "orchestration" framing strongly implies routing-through, not principal-trading. Their MPC custody setup (Dfns) is not designed for inventory FX warehousing.
- **Liquidity providers (upstream of Walapay):** carry actual market FX risk — these are the structurally short-σ entities, but they are NOT Walapay.

### Is Walapay structurally short σ(X/Y)?
**No, with the caveat of credit-extension carry.** Walapay's stated business is FX *orchestration* — they route, they don't warehouse. The DRAFT.md `Δ^(a_s) < 0` requires the operator to have accepted Y at `t=0` and owe X at `T`; Walapay's per-Payment model collapses this to ~seconds of orchestration latency. The "credit solutions" line in FIAT VC could indicate small principal-side positions, but no source confirms warehoused FX risk.

If Walapay were structurally short σ(X/Y), they'd publicly hedge (or seek to hedge). The Dfns + Circle integrations are operational, not risk-management.

---

## §4 a_s candidacy verdict

**VERDICT: NOT_A_FIT.**

Rationale (priority-ordered):
1. **Wrong chain.** Walapay does not support Celo (per Circle Alliance Directory: Arbitrum/Avalanche/Base/Ethereum/OP visible). The CPO instrument is settled on Mento V3 FPMM (per spec frontmatter) which requires Celo presence. The pre-pinned `walapay_settlement_celo` value is **structurally unfindable because the substrate isn't on Celo**.
2. **Wrong stablecoin family.** Walapay's USDC/USDT/EURC has zero overlap with Mento's COPm/USDm/BRLm/KESm/EURm. The Pair D thesis is COP/USD on a Colombian young-worker employment substrate; Walapay has no Colombian-peso-denominated rail.
3. **No fixed-time `T` obligation primitive.** Per-Payment orchestration is sub-minute, not multi-week.
4. **No yield vault primitive.** No `(Υ, r)` allocation; Walapay does not hold customer deposits to earn yield. They route.
5. **No deployed smart contracts.** MPC wallets via Dfns provide signing-side custody only; the CPO requires an on-chain inventory observable, which MPC wallets don't expose as a structured Δ.
6. **Closed-source.** Even if the prior 5 points were resolvable, the absence of any public repo means no integration surface for a permissionless CPO product.

The fit could be argued as ZERO (NOT_A_FIT, not even WEAK_FIT) because every dimension of the DRAFT.md `a_s` archetype (chain, stable, time-T obligation, yield vault, on-chain observable) is missing. This is the cleanest negative finding of the two.

---

## §5 Product-design implications (≤5 bullets)

1. **Stablecoin-orchestration B2B platforms are the wrong category for `a_s` substrate.** They're routers, not warehousers. Look for warehousers: payroll deposit takers, prepaid-airtime escrows, term-savings vaults that owe local-currency at T.
2. **Confirm Mento-stablecoin presence as a hard precondition.** The CPO settles in Mento V3 FPMM; any candidate `a_s` that doesn't transact in Mento stables (USDm/COPm/KESm/etc.) cannot anchor the K_l = K_s equilibrium of DRAFT.md eq §11.
3. **MPC custody (Dfns/Fireblocks) is opaque to Δ-observation.** A successful `a_s` integration needs either (a) public on-chain treasury (multisig, vault contract) or (b) a published API endpoint exposing real-time inventory by currency. MPC wallet balances are queryable but per-customer attribution is private.
4. **"Credit solutions" is a flag for upstream `a_s` candidates.** Walapay extends credit to PSPs; the *PSPs themselves* (or their downstream payroll-provider customers) might be the actual `a_s` warehousers. Worth investigating Vizum, Zarpay, Nuvei as second-degree candidates.
5. **The closed-source closed-API pattern is endemic in stablecoin orchestration.** BVNK, Bridge.xyz, Brale, Walapay all closed-source. Path B Stage-2 should pivot away from this category and toward open-source consumer apps with on-chain treasury (MiniPay direct, Valora, Moola, Ubeswap, Carbon DeFi-style).

---

## §6 Sources cited

| URL | Date accessed | Use |
|---|---|---|
| `https://github.com/walapay` | 2026-05-03 | confirmed 0 public repos |
| `https://www.walapay.io/` | 2026-05-03 | product surface |
| `https://docs.walapay.io/docs/introduction` | 2026-05-03 | "2 stablecoins (USDC/USDT)" + "10 fiat" + payment types |
| `https://docs.walapay.io/docs/overview` | 2026-05-03 | Customer/Account/Payment 3-tier model + chain list (Polygon, Solana, Ethereum) |
| `https://docs.walapay.io/docs/fiat-to-stablecoin` | 2026-05-03 | Ethereum settlement; "rates can only be guaranteed during EST trading hours" |
| `https://docs.walapay.io/docs/stablecoin-to-fiat` | 2026-05-03 | Polygon rail; off-ramp flow |
| `https://docs.walapay.io/docs/virtual-accounts` | 2026-05-03 | virtual accounts framing; "can be custodial or non-custodial" |
| `https://www.dfns.co/article/announcing-walapay` | 2026-05-03 | MPC + TSS custody architecture; 100+ chains via Dfns |
| `https://partners.circle.com/partner/walapay` | 2026-05-03 | chain list (Arbitrum/Avalanche/Base/Ethereum/OP — NO Celo); USDC/EURC |
| `https://www.fiat.vc/post/portfolio-spotlight-walapay` | 2026-05-03 | $85M monthly vol; 40+ B2B customers; "FX orchestration and credit solutions"; founders Tom + Dimitri Borgers |
| `https://www.thisweekinfintech.com/stableminded-s3-5-walapay-ft-tom-borgers/` | 2026-05-03 | Dfns flexible custody confirmation; partnership summary |
| `gh search repos walapay --limit 10` | 2026-05-03 | empty result confirms no public code |
