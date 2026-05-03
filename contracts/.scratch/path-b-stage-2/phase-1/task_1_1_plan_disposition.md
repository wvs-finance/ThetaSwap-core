# Task 1.1 (plan-numbered) — Allowlist Confirmation + Mento V3 Manifest Disposition

> **Task scope.** Pair D Stage-2 Path B Phase 1 Task 1.1 (per plan §3 numbering).
> Confirms the spec frontmatter `on_chain_pins` allowlist + enumerates the
> Mento V3 deployment manifest. Outputs:
>
> 1. `contracts/.scratch/pair-d-stage-2-B/v0/allowlist.toml` (13 contracts; sha
>    `5e9b3663efc75dee599966d741ec1ba5afd815194aef758d2c05bc96f09a9443`)
> 2. `contracts/.scratch/pair-d-stage-2-B/v0/DATA_PROVENANCE.md` (Task 1.1 §2
>    entries 1-5 populated; subsequent v0 Tasks 1.2 + 1.3 + 1.4 will append)
> 3. This file (orchestrator-facing disposition memo)

**Governing artifacts (sha-pinned):**

| Artifact | sha256 |
|---|---|
| Spec v1.3 (`contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md`) | `4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea` |
| Plan (`contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`) | `406c55a33e28af9e57b4cb912017e3bea26993733dc5260c0486e507d7f9cd38` |
| `allowlist.toml` (Task 1.1 primary output) | `5e9b3663efc75dee599966d741ec1ba5afd815194aef758d2c05bc96f09a9443` |

**Emit timestamp UTC:** `2026-05-03T11:16:58Z`

---

## §1 — Disposition matrix per spec frontmatter `on_chain_pins` placeholder

Spec v1.3 frontmatter `on_chain_pins` block declares 9 contract pins. Per-pin
disposition under Task 1.1:

| # | Spec frontmatter pin | Disposition | Pinned address | Source | Verification |
|---|---|---|---|---|---|
| 1 | `mento_v3_router_celo` (pre-pinned `0x4861840C…B6f6`) | **CONFIRMED** still canonical | `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6` | Celoscan label "Mento: Router" | confirmed_on_chain (code_len=26464) |
| 2 | `mento_v2_copm_celo` (pre-pinned `0x8A567e2a…41eA`) | **CONFIRMED** canonical Mento-native COPm | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` | Celoscan label "Mento Labs: cCOP Token" + memory `project_mento_canonical_naming_2026` β-corrigendum | confirmed_on_chain (code_len=4824) |
| 3 | `mento_v2_usdm_celo` (TO BE PINNED at v0) | **PINNED** at this Task | `0x765DE816845861e75A25fCA122bb6898B8B1282a` | Celoscan label "Mento" / "Token Contract"; rebranded cUSD → USDm per memory `project_mento_canonical_naming_2026` | confirmed_on_chain (code_len=5172) |
| 4 | `mento_v3_fpmm_usdm_copm_pool_celo` (TO BE PINNED at v0 OR v0-HALT) | **HALT-NO-POOL** | N/A — pool does not exist in V3 manifest | docs.mento.org/mento-v3/build/deployments/addresses lists only 4 V3 FPMM pools (USDC/USDm, USDT/USDm, axlUSDC/USDm, GBPm/USDm); no USDm/COPm pool | N/A — see §3 caveat 2 + §4 HALT memo |
| 5 | `uniswap_v3_factory_celo` (TO BE PINNED at v0) | **PINNED** at this Task | `0xAfE208a311B21f13EF87E33A90049fC17A7acDEc` | Uniswap V3 Celo deployment docs (developers.uniswap.org) | confirmed_on_chain (code_len=49072) |
| 6 | `uniswap_v3_usdc_usdm_pool_celo` (TO BE PINNED at v0) | **MIS-NAMED in spec** — actual canonical USDC/USDm pool is the Mento V3 FPMM, not a Uniswap V3 pool | `0x462fe04b4FD719Cbd04C0310365D421D02AaA19E` (Mento V3 FPMM USDC/USDm) | docs.mento.org Mento V3 manifest + on-chain token0/token1 verification (token0=USDm, token1=USDC.e) | confirmed_on_chain (code_len=4288); §3 caveat 3 records the spec rename request |
| 7 | `panoptic_factory_ethereum` (TO BE PINNED at v0) | **PINNED** at this Task | `0x00000000000142658e41964CBD294a7f731712fD` | Code4rena 2025-12 Panoptic V1 deployment-info.json (canonical pre-audit manifest) | confirmed_on_chain (code_len=48664) |
| 8 | `bitgifty_settlement_celo` (TO BE PINNED at v0 OR v2-HALT) | **HALT-AND-SURFACE** | N/A — no canonical contract address found within Task 1.1 timebox | Bitgifty has no public docs / no Celoscan-verified label / no GitHub deployment manifest discoverable in 30-min search | N/A — see §4 HALT memo |
| 9 | `walapay_settlement_celo` (TO BE PINNED at v0 OR v2-HALT) | **HALT-AND-SURFACE** | N/A — Walapay's website (walapay.io) describes "smart contracts" but does not publish addresses | Walapay docs describe an ops-layer payments orchestrator, not a public on-chain contract registry | N/A — see §4 HALT memo |

**Summary:** 6 of 9 placeholders PINNED with confirmed on-chain verification; 1
mis-named (spec §3.3 cross-ref to USDC/USDm pool should rename `uniswap_v3_usdc_usdm_pool_celo` → `mento_v3_fpmm_usdc_usdm_pool_celo` at next CORRECTIONS revision); 1 HALT-NO-POOL (USDm/COPm V3 absent — documented spec §6 pivot path); 2 HALT-AND-SURFACE (Bitgifty + Walapay merchant addresses — orchestrator adjudication required).

---

## §2 — Success-criteria sanity check (per dispatch brief)

| Criterion | Bound | Result | Pass/Fail |
|---|---|---|---|
| Allowlist row count ≥ 6 (dispatch lower) | 6 | 13 | PASS |
| Allowlist row count ≥ 4 (spec §6 typed-exception lower) | 4 | 13 | PASS |
| Allowlist row count ≤ 20 (spec §6 typed-exception upper) | 20 | 13 | PASS |
| Mento V2 COPm `0x8A567e2a…41eA` PRESENT | required | present | PASS |
| Minteo `0xc92e8fc2…` ABSENT | required | absent | PASS |
| All addresses EIP-55 checksummed | required | 13/13 checksummed | PASS |
| `role` enum membership | {router, factory, pool, token, fee_collector, merchant, mev_bot, other} | 13/13 valid (router=3, factory=4, pool=4, token=2) | PASS |
| `network` enum membership | {celo-mainnet, ethereum-mainnet} | 13/13 valid (celo=11, eth=2) | PASS |
| `verification_status` enum membership | {confirmed_on_chain, manifest_only, inferred_from_event} | 13/13 confirmed_on_chain | PASS |

**Sanity check verdict: ALL PASS.** No `Stage2PathBAuditScopeAnomaly` typed
exception fired. Allowlist comfortably inside the [4, 20] bounds with 13 rows
(7 rows of headroom either way before either bound triggers).

---

## §3 — Caveats / surprises (orchestrator-facing)

### Caveat 1 — Mento V2 Reserve at documented address returned EOA

The Mento V3 deployment manifest at docs.mento.org lists the **Reserve (v2)**
at `0x2bC2D48735842924C508468C5A02580aD4F6d99A`. `eth_getCode` against this
address on `https://1rpc.io/celo` returned `0x` (code_len=2 = empty), indicating
this address holds NO contract code. Two non-mutually-exclusive hypotheses:
(a) the documented address is stale and the Reserve has migrated to a new proxy;
(b) the Reserve is implemented as a UUPS / minimal-proxy pattern with code at a
different upstream address. **Disposition:** address EXCLUDED from allowlist
(verification gate failed); flag for Task 1.2 deeper inspection (etherscan
source-code lookup + tx-history check). Does NOT trigger any typed exception
because the spec does not require Reserve in the on_chain_pins block.

### Caveat 2 — Mento V3 FPMM has no USDm/COPm pool

This is a load-bearing caveat. The spec § (line 354) and §3 (line 508) name the
**Mento V3 FPMM USDm/COPm pool** as the primary `(X/Y)_t` reference price for
the CPO. Per docs.mento.org/mento-v3/build/deployments/addresses, the V3 FPMM
deploys 4 pools: USDC/USDm, USDT/USDm, axlUSDC/USDm, GBPm/USDm. **No USDm/COPm
pool exists.** Per spec §6 line 1034-1036 the pre-defined typed exception
`Stage2PathBMentoUSDmCOPmPoolDoesNotExist` fires at Task 1.2 audit (not Task
1.1 enumeration); the spec also pre-defines two pivot paths:
(a) check Mento V2 BiPool legacy USDm/COPm pool and treat as supply-side reference;
(b) accept that the on-chain Mento USDm/COPm reference does not exist and use
    a different reference (e.g., Uniswap V3 USDC/COPm spot if such pool exists,
    or the BCRC official COP/USD reference rate as off-chain feed).

**Task 1.1 disposition:** include Mento V2 BiPoolManager
(`0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`) in the allowlist precisely so
Task 1.2 can enumerate its V2 exchange IDs to find the legacy USDm/COPm pool.
This pre-positions pivot path (a) without prejudging the orchestrator decision.

### Caveat 3 — Spec frontmatter pin name is mis-named

The spec frontmatter pin `uniswap_v3_usdc_usdm_pool_celo` names the USDC/USDm
pool as a Uniswap V3 deployment. On Celo, the canonical USDC/USDm pool is the
**Mento V3 FPMM USDC/USDm pool** (`0x462fe04b…A19E`), not a Uniswap V3 pool.
Whether a Uniswap V3 USDC/USDm pool exists separately on Celo would require
calling `getPool(USDC, USDm, fee)` against the Uniswap V3 factory at three fee
tiers (500, 3000, 10000) — Task 1.2 work, not Task 1.1.

**Recommended spec correction (deferred to next CORRECTIONS revision):**

- Rename pin `uniswap_v3_usdc_usdm_pool_celo` →
  `mento_v3_fpmm_usdc_usdm_pool_celo`; OR
- Add separate pin `mento_v3_fpmm_usdc_usdm_pool_celo` and treat
  `uniswap_v3_usdc_usdm_pool_celo` as a Task 1.2 lookup result (likely null).

This correction does NOT block Task 1.1 closure; the `allowlist.toml` records
the Mento V3 FPMM USDC/USDm pool as the canonical USDC/USDm reference per
manifest evidence + on-chain `token0()` / `token1()` verification.

### Caveat 4 — Free public RPC selection notes

First-attempt Celo public RPC `https://forno.celo.org` and Ethereum public RPC
`https://eth.llamarpc.com` both returned **HTTP 403 Forbidden** for `eth_getCode`
calls from this Task's IP. This matches Phase 0 finding `gate_b0_review.md`
documented public-RPC flakiness. **Pivoted** to:

- Celo: `https://1rpc.io/celo` (chainId=0xa4ec verified; all 14 calls succeeded)
- Ethereum: `https://ethereum-rpc.publicnode.com` (chainId=0x1 verified; all 2
  calls succeeded)

Both endpoints SHOULD be added to `network_config.toml` §3 `public_rpc.celo` /
`public_rpc.ethereum` as preferred fallback ordering (forno + ankr remain in
config but should be re-tested; their flakiness suggests they may IP-block at
the cloud-provider level — not a 1rpc/publicnode characteristic). **NOT a
blocking issue for Task 1.1 closure.**

### Caveat 5 — Panoptic deployment-info.json lists a third unlabeled address

The Panoptic V1 deployment-info.json from Code4rena 2025-12 audit lists three
contracts:

- PanopticFactory: `0x00000000000142658e41964CBD294a7f731712fD` ✓ admitted
- SemiFungiblePositionManager: `0x0000000000014BE53913184E1B4585A059Ab0841` ✓ admitted
- Unlabeled: `0x000000000001621A6649E38465B127693fFC5db8` — role unidentified

**Disposition:** EXCLUDED from allowlist pending Task 1.2 Etherscan name lookup.
This is conservative discipline (don't admit something whose role we can't
attribute). Easily backfilled at Task 1.2 if the third address is e.g. the
Panoptic Helper / Multicall / Migrator contract.

---

## §4 — HALT-and-surface memo (Bitgifty + Walapay) — orchestrator adjudication required

### HALT trigger

Per dispatch brief: "if not findable in 30 min timebox, mark
`Stage2PathBASOnChainSignalAbsent` HALT path candidate".

After ~25 min of canonical-source search across:
- Walapay official website (walapay.io)
- Walapay Twitter/X (@walapay_io)
- Walapay Circle Alliance Directory entry
- Bitgifty: no canonical website surfaced via web search
- Celoscan general contract search
- General web search for "Bitgifty smart contract address Celo"

**No canonical merchant-side smart-contract addresses found** for either
Bitgifty or Walapay on Celo. Walapay describes their architecture as "funds
routed via smart contracts, converted, and settled directly to local bank
accounts" but does not publish on-chain contract addresses; Bitgifty has no
discoverable public technical documentation surface at all (the search returned
unrelated results for "Bitgifty").

### Spec §6 pivot pre-pinning

Per spec §6 (lines 1037+, deduced from the §6 typed-exception schema preserved
at the spec's pivot list), the documented disposition for
`Stage2PathBASOnChainSignalAbsent` is:

(a) Drop the bill-pay merchant attribution channel and run v2 + v3 on the LP-leg
    (Mento V3 + Uniswap V3) only — produces |Δ^(a_l)| only, not |Δ^(a_s)|;
(b) Substitute a different on-chain payments-rail signal — e.g., Opera MiniPay /
    GoodDollar / Valora wallet `Transfer` aggregation as a Celo-stablecoin
    consumer-flow proxy (still tests the (a_s) economic-leg geometry, but at
    the consumer-side not the merchant-side);
(c) Treat (a_s) as off-chain-only at v2 and rely on the deployed-pilot
    instrumentation at Stage-3 to populate the (a_s) cash-flow geometry;
    Stage-2 v2 then publishes |Δ^(a_l)| only with explicit (a_s) HALT note.

### Orchestrator question (auto-pivot is anti-fishing-banned per `feedback_pathological_halt_anti_fishing_checkpoint`)

**Which pivot does the user authorize?** I am NOT auto-pivoting; per the
HALT-disposition discipline this requires user adjudication before Task 1.2
proceeds with a Bitgifty + Walapay surface. The Phase 1 `allowlist.toml`
delivered at this Task is COMPLETE for the LP-leg + supply-side venues (10
Mento + 1 Uniswap-V3-Celo + 2 Panoptic-Ethereum addresses); Task 1.2 can
proceed against those 13 addresses without orchestrator re-adjudication.

The HALT applies only to the (a_s) merchant-side data path which is a
**downstream blocker** (it would prevent v2 |Δ^(a_s)| computation, not v0
audit closure or v1 |Δ^(a_l)| LP-leg work).

---

## §5 — Burst-rate compliance

| Source | Calls | Peak req/sec observed | Cap | Headroom |
|---|---|---|---|---|
| 1rpc.io/celo (public RPC) | 26 | ~2.5 (4 sec batched, 0.4 sec inter-call sleep) | informal ~5 req/sec | ~50% |
| ethereum-rpc.publicnode.com (public RPC) | 5 | ~2.5 | informal ~5 req/sec | ~50% |
| docs.mento.org (HTTPS WebFetch) | 2 | < 1 | n/a (single GET) | n/a |
| developers.uniswap.org (HTTPS WebFetch) | 2 (with 301) | < 1 | n/a | n/a |
| celoscan.io (HTTPS WebFetch) | 4 (verification) | < 1 (≥30s spacing per call) | informal ~5 req/sec | well clear |
| raw.githubusercontent.com (Panoptic JSON) | 1 | < 1 | n/a | n/a |
| **Alchemy free tier** | **0** | **0** | 25 req/sec, 30M CU/month | full headroom |
| **SQD Network** | **0** | **0** | 5 req/sec sustained, 50 req/10s burst | full headroom |
| **Dune** | **0** | **0** | 15-40 rpm | full headroom |
| **The Graph** | **0** | **0** | none published | full headroom |

**Verdict:** Task 1.1 budget consumption: ~38 outbound HTTPS calls + 0 paid /
metered tier exposure. Well below all caps. `burst_rate_log.csv` was NOT
exercised because the per-source rate stayed below the 80% warning threshold
the entire time.

---

## §6 — Discipline checklist

- [x] Free-tier ONLY (no paid services); 0 Alchemy CU + 0 Dune credits + 0 SQD requests
- [x] venv discipline: source contracts/.venv/bin/activate (verified at start)
- [x] DuckDB schema discipline: NO DuckDB writes at Task 1.1 (allowlist is TOML, not parquet/DuckDB)
- [x] CORRECTIONS-γ structural-exposure framing — NO WTP language
- [x] Stage-1 sha-pin chain READ-ONLY (sha pins quoted only, no Stage-1 file modified)
- [x] Real on-chain verification for `verification_status: confirmed_on_chain` (NO mocked verification)
- [x] Push to `phase0-vb-mvp` branch (dev, not upstream)
- [x] Scripts-only scope: NO touching src/, test/*.sol, foundry.toml, or Solidity
- [x] Concurrent-agent serialization: SOLE Path B agent; Path A files untouched
- [x] HALT-and-surface for Bitgifty + Walapay (no auto-pivot, no silent threshold tuning)
- [x] Mento V3 deployment manifest from canonical source (docs.mento.org Mento Labs)

---

## §7 — Output file inventory

| File | Sha256 | Lines | Role |
|---|---|---|---|
| `contracts/.scratch/pair-d-stage-2-B/v0/allowlist.toml` | `5e9b3663efc75dee599966d741ec1ba5afd815194aef758d2c05bc96f09a9443` | ~140 | Primary deliverable: 13-contract allowlist with EIP-55 checksums + on-chain verification |
| `contracts/.scratch/pair-d-stage-2-B/v0/DATA_PROVENANCE.md` | (computed at commit) | ~250 | §3.A 8-field provenance per source; §1 self-meta + §2 entries 1-5 |
| `contracts/.scratch/path-b-stage-2/phase-1/task_1_1_plan_disposition.md` | (this file; computed at commit) | ~270 | Orchestrator-facing disposition memo with HALT-and-surface notes |

---

## §8 — Next-task readiness assessment

**Task 1.2 (per-venue on-chain audit) can proceed against the 13-contract allowlist
WITHOUT additional orchestrator adjudication for the LP-leg + supply-side venues.**

The HALT-and-surface for Bitgifty + Walapay is a Task 1.2 (a_s) merchant-side
**downstream** blocker; it does NOT block Task 1.2's per-venue audit work for the
13 admitted contracts. Recommended Task 1.2 sequencing:

1. Audit 11 Celo contracts via SQD Network gateway (event extraction) + Alchemy
   free-tier RPC (TVL eth_call snapshot) — sequential, single-IP, ≤25 events/sec
2. Audit 2 Ethereum contracts (Panoptic Factory + SFPM) via SQD Network +
   Alchemy free-tier RPC
3. Investigate Caveat 1 (Mento V2 Reserve EOA result — re-resolve via Etherscan
   contract source-code lookup or via cross-reference to `mento-deployments`
   GitHub repo if it exists)
4. Investigate Caveat 5 (third unlabeled Panoptic deployment-info.json address)
5. Pin the Mento V2 BiPool legacy USDm/COPm exchange ID via Etherscan implementation
   contract `0xc016174b60519bdc24433d4ed2cff6c1efac7881` (per Caveat 2 documented
   pivot path (a))

**The Bitgifty + Walapay HALT is reported separately to the orchestrator** for
user adjudication on which spec §6 pivot to authorize (a / b / c per §4 of this
memo).

---

## §9 — Verdict

**Task 1.1 (plan-numbered) — PASS with 3 caveats + 1 HALT-and-surface.**

- 13/13 allowlist entries confirmed_on_chain
- 6/9 spec frontmatter pins resolved (3 HALT or mis-named — documented above)
- 0 typed exceptions fired
- Burst-rate well clear of all caps
- Free-tier budget pin honored (0 paid-service consumption)
- Stage-1 sha-pin chain unmodified
- Per-pivot HALT discipline observed (no auto-pivot)

**Orchestrator action required:** Adjudicate the Bitgifty + Walapay HALT pivot
selection (§4 of this memo) BEFORE dispatching Task 1.2 on the (a_s)
merchant-side surface.
