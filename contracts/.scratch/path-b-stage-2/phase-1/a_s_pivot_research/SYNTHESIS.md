# a_s Pivot Research — Unified Synthesis

**Authored**: 2026-05-03 by orchestrator
**Spec under revision**: `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md` (v1.3, sha `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea`)
**Plan under revision**: `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md` (sha `406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38`)

## §1. Trigger

Plan-Task 1.1 (allowlist confirmation) HALT-and-surface 2026-05-02: Bitgifty + Walapay merchant settlement contracts unfindable on-chain. Spec frontmatter `bitgifty_settlement_celo` and `walapay_settlement_celo` placeholders cannot be filled from canonical documentation.

## §2. Research dispatched (all committed)

Two parallel tracks per user direction "ii and iv independently":

| Track | Agent | Output | Commit |
|---|---|---|---|
| Bitgifty + Walapay code archaeology (initial Pivot α') | general-purpose | `bitgifty_code_archaeology.md` (1842 w), `walapay_code_archaeology.md` (1497 w), `comparative_summary.md` (1131 w) | `2fdf78482` |
| Discovery sweep (initial Pivot α') | Trend Researcher | `discovery_research.md` (~3200 w), `contract_addresses_verified.toml` (5 entries) | `2fdf78482` |
| Category (ii) deep-dive | Trend Researcher | `category_ii_deep_dive.md` (~5400 w), `category_ii_addresses.toml` (~1400 w; 6 entries) | `015f440cd` |
| Category (iv) discovery | Trend Researcher | `category_iv_discovery.md` (~5300 w), `category_iv_addresses.toml` (~1800 w; 14 entries) | `055c7a103` |

## §3. Convergent findings (4 tracks → 3 architectural conclusions)

### §3.1 Consumer-facing payment-rail-operator archetype is OFF-CHAIN

Bitgifty (Tatum API custody, no smart contracts), Walapay (Dfns MPC, no Celo, no Mento), Pretium, Kotani Pay, Fonbnk, Yellow Card — ALL fail the on-chain visibility gate. Operator-side fiat conversion happens in traditional banking rails / API custody. On-chain footprint is just user-side `Transfer` to recipient wallet; no operator treasury contract.

**Implication for spec**: deprecate `bitgifty_settlement_celo` + `walapay_settlement_celo` from frontmatter. Add anti-fishing log entry: "spec-frontmatter pre-pinning of substrate addresses without code-level archaeology produced 2/2 false-positive rate."

### §3.2 Tokenized-fiat-issuers have NO FX exposure (one-sided reserves)

MXNB/Juno (Arbitrum), BRL1 consortium (Polygon), wARS/Ripio (Eth/Base/WC) — all hold ONE-SIDED LOCAL-CURRENCY RESERVES. Issuer mints local-stable backed by local-currency reserves; no FX risk on issuer's books. The actual FX exposure sits with the user/holder of the local-stable, not the issuer.

**Architectural correction**: the a_s in category (ii) is at the **AMM LP level**, not the issuer level. LP holds the local-stable side of a CFMM pair (e.g., MXNB/USDC LP on Arbitrum) and is structurally short to local-currency depreciation via impermanent-loss asymmetry.

### §3.3 The user's two-party model maps cleanly onto Mento ecosystem

Per user direction (2026-05-03):
- **a_s = payment reel ENTITY (aggregator-level)** — operates a payment workflow whose USERS are exposed to FX depreciation on local-currency obligations
- **a_l = yield-seeking protocol on the strongest currency**
- Matching mechanism: a_s pays Π premium → a_l receives premium as yield top-up → both delta-neutralize via Π = K·√σ_T (DRAFT.md K_l = K_s equilibrium)

The category (ii) architectural correction REFINES this: the "payment reel" with on-chain visibility is the LP infrastructure (Mento V2/V3 BiPool / FPMM, Uniswap V3 on cross-corridor chains), not the consumer-facing operator. LPs aggregate the swap demand from users with local-currency obligations.

## §4. Proposed paired (a_s, a_l) per corridor

### §4.1 PRIMARY (COP-corridor, direct Pair-D match — Celo)

| Side | Entity | Contract address | Role | Δ exposure |
|---|---|---|---|---|
| a_s | Mento V2 BiPool COPm/USDm exchange | BiPoolManager `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`; COPm `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`; USDm `0x765DE816845861e75A25fCA122bb6898B8B1282a` | Per-exchange LP positions (BiPool-internal) | Structural impermanent-loss exposure on COPm leg when COP devalues |
| a_s (alternate) | Mento Reserve aggregate | Reserve Proxy `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` | Aggregates COPm + KESm + USDm + ... issuance backing across Reserve | Multi-currency Δ; per-COPm allocation requires `getReserveAddressBalance()` decomposition |
| a_l | Aave V3 Celo USDm pool | Pool `0x3e59a31363e2ad014dcbc521c4a0d5757d9f3402` | Single-side USDm depositors earning lending yield | Pure USD-yield, no FX exposure — premium from a_s tops up yield |
| a_l (alternate) | Moola Market USDm market | per Moola V2 reserves on Celo | Single-side USDm depositors | Pure USD-yield |

**Sample window**: 134 weekly observations (Aug 2023 → present), PASSES N_MIN=75 at weekly cadence per spec §3.5.

### §4.2 SECONDARY (cross-corridor sanity check — Arbitrum)

| Side | Entity | Contract address | Role | Δ exposure |
|---|---|---|---|---|
| a_s | MXNB/USDC LP on Uniswap V3 Arbitrum | Uniswap V3 factory + MXNB `0xF197FFC28c23E0309B5559e7a166f2c6164C80aA` | LP positions on MXNB/USDC pool | Structural IL on MXNB leg when MXN devalues |
| a_l | Aave V3 Arbitrum USDC pool | per Aave V3 deployment on Arbitrum | USDC depositors | Pure USD-yield |

**Sample window constraint**: ~13 months MXNB history → use DAILY cadence (~390 obs PASSES N_MIN=75); weekly ~52 obs FAILS. **DO NOT borrow Stage-1 β = +0.137 — re-estimate per corridor.**

### §4.3 ARCHITECTURAL TEMPLATE (NOT a substrate, methodology only)

| Side | Entity | Contract address | Role | Use |
|---|---|---|---|---|
| a_s template | impactMarket Microcredit | `0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb` (Celo) | Per-loan maturity T + per-installment q_t encoding | Reference for time-T obligation primitive structure; informs how Mento BiPool's swap-flow can be decomposed into q_t schedules |

NOT in v1 substrate. Used as design reference for q_t aggregation methodology only.

### §4.4 DROPPED candidates

| Candidate | Reason |
|---|---|
| Bitgifty | NOT_A_FIT — no smart contracts, Tatum API custody |
| Walapay | NOT_A_FIT — closed source, no Celo, no Mento, MPC custody |
| Pretium / Kotani Pay / Fonbnk / Yellow Card | NOT_A_FIT — consumer-rail operators, off-chain only |
| BRL1 (Polygon) | DROP — float $1.3M USD, $55K/day volume; 2-3 orders below MXNB; consortium attribution opaque |
| MXNT (Tether-Mexico) | DROP — dormant since 2022 launch, no 2024-2026 supply data |
| veMENTO Locking | DROP — X = MENTO/USD, SUBSTRATE_TOO_NOISY per spec §3.5 |
| GoodDollar UBI | DEFER — X = G$/cUSD purchasing power, not direct COP corridor |
| Moola COPm protocol-side | NOT_A_FIT — yield-bearing protocol; lender-side is a_l-flavored, not a_s |
| Halofi V2 | DROP — operationally dormant since April 2023; GitHub archived November 2024 |
| wARS/Ripio | DEFER — Argentina trend regime confounds LP-level analysis |

## §5. Spec CORRECTIONS-ε scope

Path B spec v1.3 → v1.4. Prose-only redefinition of a_s framing + frontmatter `on_chain_pins` overhaul.

### §5.1 Frontmatter changes

DEPRECATE:
- `bitgifty_settlement_celo` (placeholder unfillable)
- `walapay_settlement_celo` (placeholder unfillable)
- `mento_v3_fpmm_usdm_copm_pool_celo` (does not exist — use V2 BiPool)
- `uniswap_v3_usdc_usdm_pool_celo` (mis-named — actual canonical is Mento V3 FPMM, but USDm/COPm V3 doesn't exist)

ADD:
- `mento_v2_bipool_manager_celo: 0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`
- `mento_v2_usdm_celo: 0x765DE816845861e75A25fCA122bb6898B8B1282a`
- `aave_v3_celo_pool: 0x3e59a31363e2ad014dcbc521c4a0d5757d9f3402` (a_l primary)
- `mento_reserve_proxy_celo: 0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` (a_s alternate aggregate)
- `mxnb_arbitrum: 0xF197FFC28c23E0309B5559e7a166f2c6164C80aA` (cross-corridor a_s)
- `impact_market_microcredit_celo: 0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb` (architectural template, not substrate)

### §5.2 Prose redefinitions

§1 — Path B's purpose: structural-exposure characterization at the **LP-level / Reserve-aggregate level**, NOT consumer-facing operator level. The user's two-party model under the LP-infrastructure refinement.

§2 — v0/v1/v2/v3 ladder semantics:
- v0 audit: now audits BOTH a_s LP-positions AND a_l yield positions per pair, per-corridor
- v1: CF^(a_l) reconstruction → unchanged in spirit; concrete substrate is now Aave V3 Celo USDm depositors (not "Mento V3 FPMM LP" since that's the a_s side)
- v2: CF^(a_s) reconstruction → concrete substrate is now Mento V2 BiPool COPm/USDm LP positions (not Bitgifty/Walapay)
- v3: CPO retrospective backtest unchanged

§3 — Inputs reflect the corrected pin set.

§4.0 — Schema unchanged (BLOCK-B1 closure preserved); add per-paired-substrate columns where relevant.

§6 — Typed exceptions: deprecate `Stage2PathBASOnChainSignalAbsent` (resolved by pivot); add `Stage2PathBASLPCompositionDriftBeyondTolerance` (covering the LP-side reframing where impermanent-loss attribution requires LP-composition tracking).

§8 — Cross-path handoff `r_al_handoff.json` remains unchanged in schema; the producer is now Aave V3 Celo USDm pool yield instead of Mento V3 FPMM LP fees.

### §5.3 Plan implications (CORRECTIONS to plan)

Plan §3 Phase 1 task 1.2 (per-venue audit) inherits the new allowlist composition. Tasks 1.3 (Parquet emission) schema unchanged. Task 1.4 (TDD) tests unchanged. Task 1.5 Gate B1 unchanged.

Phase 2 (v1) and Phase 3 (v2) substrate references update:
- Phase 2 = a_l = Aave V3 Celo USDm pool (lending yield reconstruction); was Mento V3 FPMM LP fee yield
- Phase 3 = a_s = Mento V2 BiPool COPm/USDm LP positions (impermanent-loss-based Δ^(a_s) attribution); was Bitgifty/Walapay merchant settlement

## §6. Anti-fishing posture

This pivot is structurally motivated, not threshold-tuned:
- Original Bitgifty/Walapay pre-pinning failed empirical existence check (HALT-and-surface fired correctly)
- Replacement candidates derived from independent research tracks with hard on-chain visibility gates
- Architectural correction (LP-level vs issuer-level) is grounded in financial structure, not data fitting
- COP-corridor preservation maintained where possible (Mento V2 BiPool, Aave V3 Celo); cross-corridor sanity check explicitly flagged as substrate-relocation per spec §3.5

## §7. Operational notes

- Cross-worktree write incident: category (iv) agent wrote to main repo path instead of angstrom worktree; manually moved before commit. Add absolute-worktree-path pin to dispatch brief boilerplate.
- Concurrent-agent serialization held: Path A Phase 1 paused during Path B Phase 1 work; no commit interleaving observed in this session block.

## §8. Decision (user, 2026-05-03)

User confirmed: **the on-chain a_s entity per the DRAFT.md simplified model (fixed B_T in local currency, sourced from Y reserves, on-chain treasury) does not exist.** §4.1 PRIMARY mapping is REJECTED — proposed a_s (Mento V2 BiPool LP) is structurally a_l per LVR (Milionis-Moallemi-Roughgarden 2022: LP NET = short variance); proposed a_l (Aave V3 USDm) is decoupled from FX entirely.

### §8.1 Structural finding

**Abrigo is an a_s-INSTANTIATING product, not an a_s-hedging product.** The CPO cannot be sold into an existing on-chain a_s population because that population doesn't exist on-chain. Product must DEPLOY the a_s side simultaneously — a vault that:
1. Accepts Y-stable deposits (USDm) from wage earners
2. Creates the fixed-T X-denominated obligation (commits to delivering COPm monthly per schedule)
3. Acts as the a_s itself (vault operator sources COP from USD reserves over time)
4. Buys CPO Π hedge from LP side (a_l) to neutralize FX vol exposure
5. Charges margin to wage earner; CPO premium funds LP-side counterparty

This matches the CLAUDE.md "premium-funded ratchet (self-LBM)" framing — the instrument doesn't merely hedge an existing position, it CREATES the position that gets hedged.

### §8.2 User-picked refinement: OPTION 3 (synthetic counterfactual)

Path B v2 reframes from on-chain a_s extraction (impossible) to **synthetic counterfactual generation**:

- Use historical Mento V3 / V2 swap flows (real, observable; 2023-08→present, 134 weekly obs)
- Assumed q_t schedule (parametric; e.g., monthly COPm payouts of B_T/12 over T=12 months; sweep over q_t profiles)
- Observed COP/USD path (Banrep TRM + Mento on-chain price; already pinned in Stage-1 chain)
- Output: counterfactual time-series of Δ^(a_s) showing what a hypothetical vault WOULD have produced

Output is simulation, NOT measurement. Anti-fishing posture: q_t schedules pre-committed; no fitting; sensitivity sweep over pre-pinned schedule families.

### §8.3 Path B reframe scope

- Path B v1 (a_l characterization) — UNCHANGED. Real, observable. Mento V3 FPMM LP fee yield → realized r_(a_l). Emits r_al_handoff.json to Path A v3.
- Path B v2 (a_s synthetic counterfactual) — NEW METHODOLOGY. Simulated Δ^(a_s) under historical Mento flows + parametric q_t + observed FX path. Does NOT consume on-chain a_s entity addresses (none exist).
- Path B v3 (CPO retrospective backtest) — UPDATED. Replays Π(σ_T) against synthetic Δ^(a_s) + observed Δ^(a_l). K_l = K_s equilibrium check becomes simulated under each q_t schedule.

### §8.4 Spec CORRECTIONS-ε scope (revised per option 3)

Path B v1.3 → v1.4. Substantive revision (not micro-edit):
- Frontmatter on_chain_pins: deprecate Bitgifty/Walapay/Mento V3 USDm-COPm pool/Uniswap V3 USDm-COPm pool placeholders. Add Mento V3 FPMM USDm/COPm or V2 BiPool addresses for a_l side. Do NOT pin on-chain a_s entity addresses (none exist).
- §1 framing: revise to "a_l characterization (on-chain) + a_s synthetic counterfactual (simulated)"; explicit acknowledgment that Abrigo is a_s-instantiating product
- §2 ladder: v0/v1 unchanged (audit + a_l reconstruction); v2 reframes to synthetic generation methodology; v3 updates to mixed empirical-+-synthetic backtest
- §4.0 schema: a_l Parquet schema unchanged; ADD a_s_counterfactual schema (q_t parameters, COP path source, simulated Δ trace)
- §6 typed exceptions: deprecate Stage2PathBASOnChainSignalAbsent (resolved by acknowledging non-existence + pivot to synthetic); ADD Stage2PathBSyntheticDriftBeyondTolerance (when synthetic q_t-sweep produces inconsistent Δ across reasonable schedules)
- §8 cross-path handoff: B→A r_al_handoff.json unchanged; A→B v3 envelope handoff updates to consume Path A's σ-distribution AS INPUT to Path B v2 synthetic counterfactual (allowing scenario-replay over the Path A simulated FX paths)

End of synthesis.
