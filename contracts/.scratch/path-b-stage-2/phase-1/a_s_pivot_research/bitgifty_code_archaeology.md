# Bitgifty — Code Archaeology Report

**Author:** Investigation agent (Path B Stage-2 Phase-1, a_s pivot research)
**Date:** 2026-05-03
**Spec context:** `bitgifty_settlement_celo` was pre-pinned as a candidate `a_s` substrate in the Pair D Stage-2 spec frontmatter; this report determines whether the pin is structurally valid.
**Methodology:** Free-tier only — public GitHub repo enumeration via `gh api`, raw-file fetch via WebFetch, ecosystem write-ups via WebSearch + WebFetch. No paid APIs. No source-code modification. No commits.

---

## §1 GitHub presence

| Repository | Owner | Lang | Last commit | Smart contracts? |
|---|---|---|---|---|
| `Bitgifty/bitgifty-backend` | Bitgifty (org) | Python (Django) | 2025-03-14 | **No** — uses Tatum API as blockchain abstraction |
| `Bitgifty/bitgifty-minipay` | Bitgifty (org) | TypeScript (Next.js) | 2023-12-10 | **No** — direct ERC-20 `transfer()` call to env-var addresses |
| `Bitgifty/bitgifty-giftcards` | Bitgifty (org) | TypeScript | 2025-02-13 | Frontend only |
| `Bitgifty/minipay-frontend` | Bitgifty (org) | TypeScript | 2024-11-25 | Frontend only |
| `Bitgifty/bitgifty-ecom-frontend` | Bitgifty (org) | — | 2024-07-09 | Frontend only |
| `Bitgifty/bitgifty-ecom` / `bitgiftyecom` | Bitgifty (org) | — | 2024-11-06 | (empty / minimal) |
| `damzylance/bigiftyxsoroban` | Founder personal | TypeScript | 2024-10-26 | **One Soroban (Stellar) contract call** — testnet `make_payment`, prototype only |
| `damzylance/bitgiftyxminipay` | Founder personal | — | 2024-11-05 | "Light weight utility payment dapp on MiniPay" — frontend |
| `damzylance/bitgifty` | Founder personal | — | 2025-04-03 | **No** web3/celo/ethers/wagmi/viem in package.json |

**No Solidity / Vyper / Cairo source files found in any repo.** No `contracts/`, `src/`, `protocol/`, `foundry.toml`, `hardhat.config.js`, or equivalent. The closest to a smart-contract surface is the Soroban prototype (testnet, single function `make_payment` parameterised by token-address ScVal) — not production.

---

## §2 Workflow pattern

### What the user does
The end-user runs through one of three flows, all driven by the Django backend (`bitgifty-backend`):

1. **Buy gift card** — pay with crypto (BTC/ETH/BNB/CELO/TRON/USDT-TRON/cUSD/cEUR/Stellar-USDC). Backend stores card record with `code` field; emails recipient.
2. **Redeem gift card** — recipient enters code + their wallet address; backend transfers tokens out of an `AdminWallet` (per-network) to recipient (`dapp/models.py::Redeem.redeem_giftcard`).
3. **Spend on utilities** — pay airtime, mobile data, electricity, cable TV, betting top-up. Crypto is debited from user wallet; fiat-equivalent is paid to the Nigerian/Kenyan utility provider via three off-chain APIs (Flutterwave for NG, Pretium for KE/ZA/UG M-Pesa-style rails, Arktivesub for NG VTU).

### On-chain footprint
- **No deployed Bitgifty contracts.** All chain interaction is mediated by Tatum API (`https://api.tatum.io/v3`), which abstracts wallet creation, balance queries, and `send_token()`. From `core/utils.py`: `Blockchain.send_token()` constructs network-specific payloads — Bitcoin uses UTXO arrays, Ethereum/BNB/Celo use `to + fromPrivateKey`, TRON supports TRC-20 with hardcoded USDT contract `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`.
- **Custodial admin wallets.** Per-network admin wallets store private keys (Fernet-encrypted). All redemptions debit these admin wallets. The user-facing wallets are also custodial (Tatum-generated).
- **Celo footprint specifically:** the MiniPay frontend (`bitgifty-minipay/packages/react-app/utils/transaction.ts`) calls `transferCUSD()` which executes a vanilla ERC-20 `transfer(address,uint256)` against `process.env.NEXT_PUBLIC_SC` (cUSD token contract) sending to `process.env.NEXT_PUBLIC_MW` (Bitgifty's master wallet). That's it — no escrow contract, no swap contract, no time-locked obligation contract.

### Recurring vs one-shot obligation (q_t at fixed times?)
**One-shot.** Every transaction is a single user-initiated buy or redeem. The `redeem_giftcard()` function debits an admin wallet immediately. There is no:
- Subscription primitive
- Streaming payment
- Time-locked obligation that would force the operator to source X-currency at a specific future date `T` per the DRAFT.md `B_T` model

The closest primitive to a fixed-time obligation is a gift-card code that is "outstanding" until redeemed — but redemption time is at the recipient's discretion, not a contract-pinned `T`. The operator's risk is `time-of-redemption` not `pre-committed T`.

### X-side vs Y-side risk
- **User pays in:** any of {BTC, ETH, BNB, CELO, TRX, USDT, cUSD, cEUR, Stellar-USDC} — predominantly USD-pegged stables for utility-payment flows
- **User receives:** either (a) a gift-card code (denominated in the original crypto), or (b) NGN/KES utility delivery (airtime topped up to phone number, electricity unit credit applied to meter)
- **FX path for utility flow:** `usd_price = get_rate(asset)` → `naira_rate = get_naira_price()` → `rate = round(naira × tron, 3)` (`utilities/models.py`). Rate is computed at request time from Binance avgPrice + CoinGecko NGN; **no rate-lock, no spread buffer, no expiration window** (per `swap/views.py`). Flutterwave/Pretium then settle the NGN/KES leg off-chain.

The structural FX exposure: **operator absorbs the spread between (a) the locked Binance/CoinGecko rate at quote time and (b) the off-chain settlement rate at Flutterwave/Pretium debit time**. This is a *latency-bounded* FX exposure (seconds to minutes), not a *path-bounded* one (DRAFT.md §1 model assumes T-horizon obligation).

---

## §3 Utility function reverse-engineering

### User maximises
Three distinct user archetypes, three different objectives:
1. **Gift sender:** delivery certainty + recipient-side ease (no-wallet redemption); price is secondary.
2. **Gift recipient:** value preservation between gift creation and redemption (incurs FX risk if denominated in volatile asset and held).
3. **Utility-bill payer:** cost minimisation per NGN of airtime/data/electricity delivered; latency in seconds.

None of these users exhibit a **pre-committed `q_t` schedule at fixed times `T`**. The "self-LBM premium-funded ratchet" framing of DRAFT.md (wage earner pays small recurring premium → instrument's accumulated convex payoff converts into productive-capital exposure) does not match any of these workflows. Bitgifty users are transactional, not subscription-style.

### Operator maximises
Margin per transaction = (FX spread between Binance/CoinGecko quote and Flutterwave/Pretium settlement) + (per-network gift-card fee, see `GiftCardFee.objects.get(network=..., operation="redeem").amount`). Profit comes from spread capture, NOT from a `(Υ_T, r)` yield vault on a buffered deposit.

There is **no yield vault**. The admin wallets are operationally "hot" (used for daily settlements). No code path allocates `θ · D_0^(Y)` to any yield protocol (Aave, Moola, Compound, etc.). `θ` in DRAFT.md eq (1) = 0 here.

### FX risk absorbed by each party
- **User (utility payer):** absorbs zero FX risk for the few-seconds quote-to-settlement window (operator quotes locked rate at request time).
- **Operator:** absorbs (a) latency-FX between Binance quote and Flutterwave/Pretium fiat debit, (b) inventory-FX on hot admin wallet balances held across multiple chains, (c) gift-card-redemption-time FX on outstanding cards.
- **Recipient (gift card):** absorbs FX between gift-creation time and redemption time IF denominated in non-stable (BTC/ETH/CELO/TRX). For stable-denominated cards (cUSD, USDT, Stellar-USDC), recipient FX risk is bounded.

### Is the operator structurally short σ(X/Y) — i.e., do they LOSE if FX vol rises?
**Weakly yes, but not in the way DRAFT.md §1 requires.** The operator's loss from rising FX vol is *latency-bounded* (the few-seconds settlement window) and *inventory-bounded* (the cross-chain hot-wallet balances they hold to service redemptions). Neither maps to the model's `Σ q_t / (X/Y)_t` sourcing-cost integral over a multi-period horizon `T`.

The DRAFT.md `Δ^(a_s) < 0` derivation assumes an operator that has accepted a deposit `D_0^(Y)` at `t=0` and must deliver `B_T` in X-currency at fixed `T`. Bitgifty does not have this primitive. They never accept a deposit-with-deferred-X-delivery commitment.

---

## §4 a_s candidacy verdict

**VERDICT: WEAK_FIT (leaning NOT_A_FIT).**

Rationale:
1. **No fixed-time obligation primitive.** The DRAFT.md `a_s` model requires `B_T` delivery at pre-committed `T`. Bitgifty's redeem-on-demand gift cards and instant utility payments do not create this; the operator's FX exposure is latency-bounded, not horizon-bounded.
2. **No yield vault.** The DRAFT.md `(Υ, r)` allocation `θ · D_0^(Y)` has no analogue in Bitgifty's code; admin wallets are operational hot wallets, not yield-bearing buffer.
3. **No deployed smart contracts.** All settlement is API-mediated (Tatum + Flutterwave + Pretium). The CPO instrument needs an on-chain `a_s` whose structural Δ can be observed and hedged via Panoptic positions; an off-chain payment app provides no such observable.
4. **Structural FX exposure exists but is wrong-shape.** Operator loses on intra-day FX shocks (latency + inventory), not on multi-week σ(X/Y) realisations. The CPO `Π = K √σ_T` payoff at horizon `T` doesn't neutralise intra-day shocks any more cheaply than vanilla short-dated FX puts would.
5. **Scope contradiction.** Bitgifty's primary fiat rails are NGN (Flutterwave) and KES/ZA/UG (Pretium); the Pair D thesis is COP/USD on Colombian young-worker services-employment. Geographic non-overlap with the validated β.

The fit could be argued as **WEAK** (not absolute zero) because the operator does carry residual FX exposure on hot-wallet inventory and on outstanding gift cards. But this exposure is not the structural short-σ(X/Y) the CPO is designed to hedge.

---

## §5 Product-design implications (≤5 bullets)

1. **The CPO needs a `a_s` substrate that holds a deposit and owes a fixed-time-T payment in X.** Bitgifty's transactional model rules them out as a direct fit. Look for: payroll providers (q_t = monthly), pension-payout providers (q_t = monthly), term-deposit takers, prepaid-utility subscription apps.
2. **Tatum-style API custody is a footgun for CPO integration.** If a candidate `a_s` uses Tatum/Fireblocks/Dfns for custody, the CPO settlement contract cannot read their inventory directly; the hedge purchase would have to be a pre-committed cash spend, not a Δ-neutralising position keyed to actual inventory. Prefer candidates with on-chain treasury (multisig or vault contract).
3. **Latency-FX vs horizon-FX is a load-bearing distinction the spec must pin.** Bitgifty operators care about seconds-to-minutes FX; the CPO at K√σ_T addresses weeks-to-months FX. Sales-pitch alignment requires segmenting target operators by their actual treasury holding period.
4. **Off-chain fiat settlement (Flutterwave, Pretium, M-Pesa) breaks the on-chain Δ-observability the CPO assumes.** Even if Bitgifty held inventory on Celo, the moment they call Flutterwave to debit NGN, the X-side is off-chain and the CPO cannot synchronously hedge it.
5. **Gift cards are an interesting *secondary* CPO use case.** A gift card that is "guaranteed to deliver $X USD-equivalent in [Y currency] at redemption time" is exactly a short-vega obligation; if the redemption-time-window were bounded (e.g., expires in 30 days), it would map cleanly to the DRAFT.md model. Bitgifty's current expiry-less gift card does not.

---

## §6 Sources cited

| URL | Date accessed | Use |
|---|---|---|
| `https://github.com/Bitgifty` (org listing) | 2026-05-03 | repo enumeration |
| `https://github.com/Bitgifty/bitgifty-backend` (repo listing + raw files) | 2026-05-03 | Django backend, Tatum integration |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/wallets/views.py` | 2026-05-03 | wallet API logic |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/wallets/models.py` | 2026-05-03 | wallet data model |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/swap/models.py` | 2026-05-03 | swap rate fetching (Binance + CoinGecko) |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/swap/views.py` | 2026-05-03 | swap API |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/core/tatum.py` | 2026-05-03 | Tatum API wrapper |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/core/utils.py` | 2026-05-03 | `Blockchain` class — chains, send_token, encryption |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/core/pretium.py` | 2026-05-03 | KE/ZA/UG M-Pesa rail |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/core/flutterwave.py` | 2026-05-03 | NG fiat payout rail |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/utilities/models.py` | 2026-05-03 | utility-bill purchase + FX rate composition |
| `gh api repos/Bitgifty/bitgifty-backend/contents/dapp/models.py` (decoded) | 2026-05-03 | gift-card create / redeem flow with admin wallet |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-backend/master/price.json` | 2026-05-03 | hardcoded crypto-USD price snapshot |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-minipay/main/packages/react-app/utils/transaction.ts` | 2026-05-03 | cUSD ERC-20 transfer to env-var master wallet |
| `https://raw.githubusercontent.com/Bitgifty/bitgifty-minipay/main/packages/react-app/package.json` | 2026-05-03 | Celo deps confirmed (contractkit, rainbowkit-celo) |
| `https://raw.githubusercontent.com/damzylance/bigiftyxsoroban/main/app/utils/contractActions.ts` | 2026-05-03 | Stellar Soroban testnet prototype |
| `https://raw.githubusercontent.com/damzylance/bitgifty/main/package.json` | 2026-05-03 | founder repo (no web3 deps) |
| `https://www.celopg.eco/ecosystem/bitgifty` | 2026-05-03 | Celo PG ecosystem page (HQ Lagos, team 2-10, 2022) |
| `https://forum.celo.org/t/bitgifty-a-crypto-gift-card-platform-for-daily-lifestyle-cc8-minipay-launchpad/7144` | 2026-05-03 | Celo Camp 8 / MiniPay Launchpad post |
| `https://www.celocamp.com/post/bitgifty-send-and-receive-crypto-in-a-fun-and-easy-way` | 2026-05-03 | partnership context |
| `https://bitgifty.com/` | 2026-05-03 | product surface |
