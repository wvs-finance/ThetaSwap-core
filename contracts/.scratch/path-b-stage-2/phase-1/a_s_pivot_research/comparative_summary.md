# Comparative Summary — Bitgifty vs Walapay vs DRAFT.md `a_s` archetype

**Author:** Investigation agent (Path B Stage-2 Phase-1, a_s pivot research)
**Date:** 2026-05-03
**Companion files:**
- `bitgifty_code_archaeology.md` (this directory)
- `walapay_code_archaeology.md` (this directory)
- DRAFT.md framework: `contracts/notes/2026-04-29-macro-markets-draft-import.md`
- Pair D Stage-1 PASS verdict: `contracts/.scratch/simple-beta-pair-d/results/VERDICT.md`

---

## §1 Side-by-side comparison

| Dimension | DRAFT.md `a_s` archetype (target) | Bitgifty | Walapay |
|---|---|---|---|
| **Settlement chain** | Celo / Mento V3 FPMM | Celo + BTC + ETH + BNB + TRON + Stellar (Tatum-mediated) | Arbitrum, Avalanche, Base, Ethereum, OP **(no Celo)** |
| **Stablecoin family** | Mento (USDm/COPm/KESm/BRLm/EURm) | cUSD, cEUR, USDT (TRON), Stellar-USDC | USDC, USDT, EURC **(no Mento)** |
| **Custody model** | On-chain vault `(Υ, r)` with θ-allocation | Custodial admin wallets, Tatum API, Fernet-encrypted private keys | MPC wallets via Dfns (TSS) — opaque to Δ-observation |
| **Smart contracts deployed** | Required: yield vault + buffer accounting | None (only ERC-20 `transfer()` calls; one Soroban testnet prototype) | None public; closed-source orchestrator |
| **Yield vault `(Υ_T, r)`** | YES — `Υ_T = θ D_0^(Y) (1 + rT)` | NO — admin wallets are operational hot wallets | NO — "orchestration" not warehousing |
| **Liquid-buffer split θ** | `θ ∈ [0,1]` allocated to yield, `(1-θ)` to payments buffer | Implicit `θ = 0` (no yield allocation) | N/A (no inventory held) |
| **Fixed-time-T obligation `B_T`** | Required — operator owes `B_T` in X at horizon `T` | NO — gift cards expire-less; utility flows are instant | NO — per-Payment sub-minute orchestration |
| **Sourcing-cost integral `Σ q_t / (X/Y)_t`** | Operator must minimise this s.t. `Σ q_t (X/Y)_t = B_T` | NO — no time-segmented sourcing; rate quoted at request | NO — orchestrated via LPs; Walapay not principal |
| **Structural Δ^(a_s) < 0** | YES — operator loses if σ(X/Y) rises over `[0,T]` | WEAK — latency-FX (seconds) + inventory-FX, not horizon-FX | NO — orchestration model passes risk through to LPs / customer |
| **Geographic / X overlap with Pair D (COP/USD)** | COP/USD is the X; need a Colombian-services denominated `a_s` | NO — primary fiat rails NGN (Flutterwave) + KES/ZA/UG (Pretium) | NO — no published Colombian-specific corridor |
| **Open-source / observable** | Required for permissionless CPO integration | YES (Bitgifty/* org public) | NO (0 repos) |
| **CPO integration surface** | Need on-chain inventory observable + obligation event hook | None — backend custodial API | None — closed orchestration |
| **Verdict** | — | **WEAK_FIT** (leaning NOT_A_FIT) | **NOT_A_FIT** |

---

## §2 Recommendation

**KEEP NEITHER as a viable `a_s` candidate.** Both fail on multiple structural dimensions of the DRAFT.md archetype, with non-overlapping failure modes:

- **Bitgifty** is the closer of the two — Celo-resident, open-source, holds some FX inventory — but lacks the time-`T` obligation primitive that gives the CPO its load-bearing economic content. A CPO sold to Bitgifty would hedge a *latency-bounded* exposure that vanilla short-dated FX puts already cover more cheaply.
- **Walapay** fails on every dimension — wrong chain, wrong stable family, wrong business model (orchestration not warehousing), closed-source, no smart contracts. The pre-pinned `walapay_settlement_celo` field in the spec frontmatter is **provably empty** because Walapay is not on Celo.

This finding **CONFIRMS Pivot γ** (the framing under CORRECTIONS-γ that re-cast `Δ^(a_s)` in `$-notional` rather than WTP terms): the original assumption that off-the-shelf payment apps would be drop-in `a_s` substrates does not survive code-level inspection. The structural-exposure framing is correct; the candidate substrates pre-pinned in the spec are not.

---

## §3 Pivot recommendation — Path B v2 explicit re-routing

The spec frontmatter pins (`bitgifty_settlement_celo`, `walapay_settlement_celo`) should be **deprecated** and the v2 `a_s` search should re-anchor on the structural primitives the DRAFT.md model actually requires:

### Required `a_s` properties (re-stated from DRAFT.md eq §1 + §11)
1. **On-chain treasury** holding a deposit `D_0^(Y)` at `t=0`
2. **Time-T obligation** to deliver `B_T` denominated in X-currency at horizon `T > 0`
3. **Yield-vault allocation** `(Υ, r, θ)` permitting `θ ∈ (0,1]`
4. **Resident on the same chain as the CPO settlement venue** (Celo for Mento V3 FPMM)
5. **Open-source or open-API** to permit CPO Δ-monitoring

### Candidate categories worth searching (in priority order)
1. **Mento-native payroll providers** — payroll deposits in USDm/COPm/KESm with monthly disbursement schedule = perfect `q_t` at fixed `T`. Track 2 (Trend Researcher) candidates likely live here.
2. **Celo/Mento prepaid-utility apps with multi-week subscription** — e.g. solar-energy pay-as-you-go (M-KOPA-style on-chain), school-fee installment apps. Each subscription period = `T`.
3. **Mento-stable savings vaults that promise local-currency redemption** — any "save in Y, withdraw in X at maturity" product on Celo.
4. **Term-deposit / time-locked stable savings on Celo** — e.g. Moola Market savings accounts denominated in COPm or KESm.
5. **(STRETCH) Cross-chain bridges quoting fixed-time settlement in Mento stables** — this re-introduces orchestration risk but if the bridge holds principal it warehouses Δ.

### Track 2 hand-off
Per the user's brief, Track 2 (Trend Researcher's discovery) should be the destination for the v2 `a_s` candidate list. This research **DOES NOT recommend continuing to Stage-2 with the spec's pre-pinned Bitgifty/Walapay**; the product design should pivot to the categories above.

---

## §4 HALT items

**No HALT condition fires** in the strict sense ("BOTH companies are off-chain-only with no smart-contract surface"):

- Bitgifty does have *some* on-chain footprint (custodial Tatum-mediated transfers on Celo + multiple chains, plus a Soroban testnet prototype). Off-chain-only would be too strong a claim.
- Walapay is effectively off-chain from a *deployed-contract* perspective (Dfns MPC wallets are key-management, not contract logic), but they do touch chain (the wallets sign EVM/Solana txs).

However, the **functional HALT condition** does fire: **neither company implements the time-`T` obligation primitive that makes them economically equivalent to the DRAFT.md `a_s`**. The spec's pre-pinned candidates are structurally inappropriate. Continuing Stage-2 with these substrates would force the CPO design to either (a) hedge a wrong-shape exposure (latency-FX), or (b) fabricate a synthetic obligation surface that neither operator actually has.

**Surfaced for orchestrator decision:**
1. Deprecate `bitgifty_settlement_celo` and `walapay_settlement_celo` from spec frontmatter.
2. Trigger Path B v2 re-pivot to Track 2 candidates (Trend Researcher's discovery).
3. Add to anti-fishing log: "spec-frontmatter pre-pinning of substrate addresses without code-level archaeology produced a 2/2 false-positive rate on candidate `a_s` substrates" — for Path A.0 lessons-learned carry-forward.

---

## §5 Cross-references

- DRAFT.md framework — eq (1), §11 K_l = K_s equilibrium, §1 `Δ^(a_s) < 0` derivation
- VERDICT.md (Stage-1 PASS) — β = +0.137, p = 1.46e-08; the COP/USD × young-worker channel is empirically validated, but the M-side substrate is not yet pinned
- Memory `project_pair_d_phase2_pass` — Stage-2 M-sketch UNBLOCKED; this report is one of the inputs to the M-sketch
- CORRECTIONS-γ structural-exposure framing — confirmed correct; the failure is in candidate selection, not in the framing itself
