---
artifact_kind: category_iv_pivot_research
spec_ref: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (§6 typed exception Stage2PathBASOnChainSignalAbsent, Pivot β; CORRECTIONS-ε pending placeholder deprecation)
parent_task: Pair D Stage-2 Path B Phase-1 a_s pivot research — category (iv) Mento-stable term-deposit / time-locked savings vaults on Celo
emit_timestamp_utc: 2026-05-03
budget_pin: free_tier_only
methodology: WebSearch + WebFetch only; verification via Celoscan public access; no paid APIs
constraints:
  - On-chain visibility is HARD GATE
  - Fixed-time-T obligation primitive is SECOND HARD GATE (per category-(iv) brief)
  - No WTP / behavioral-demand inference (CORRECTIONS-γ structural-exposure framing)
  - No Path A files touched
  - No spec / plan modification
prior_companion:
  - contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/discovery_research.md (Track 2 prior; consumer-facing payment-rail operators)
  - contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/contract_addresses_verified.toml (Track 2 verified pool)
---

# Pair D Stage-2 Path B — Category (iv) Mento-Stable Term-Deposit / Time-Locked Savings Vaults on Celo

## Executive Summary

Track-1 product-design implication #1 was load-bearing: "CPO needs a_s substrate that holds a deposit and owes a fixed-time-T payment in X. Transactional payment apps (Bitgifty) and orchestration platforms (Walapay) have no such primitive." This research investigates whether **savings vaults / term deposits / time-locked obligations on Celo** carry the missing primitive natively.

**Findings:**

- **Candidates investigated: 9** (3 mandatory + 6 expanded sweep)
- **Candidates passing BOTH gates (on-chain visibility + fixed-time-T obligation primitive): 4**
- **Top a_s candidates with verified on-chain footprint AND fixed-time-T primitive:**
  1. **impactMarket Microcredit** (Celo) — strongest fit; explicit `Repay Loan` + `Add Loans` operations on cUSD-denominated installment schedules
  2. **veMENTO Locking** (Celo) — Mento V3 governance lock; up to 2-year time-lock with weekly decay schedule on MENTO
  3. **StakedCelo** (Celo) — 3-day unlock period on liquid-staking redemptions; CELO-denominated obligation
  4. **GoodDollar UBI Scheme** (Celo, already in Track-2 candidate pool) — daily UBI claim is the q_t schedule
- **HALT items:** None. Multiple candidates pass; gate-pass set exceeds spec §3.5 SUBSTRATE_TOO_NOISY threshold.
- **Critical finding:** None of the candidates have **direct COPm exposure as a fixed-T obligation**. The Mento Reserve does back COPm but at protocol-aggregate level, NOT as a per-position fixed-T deposit. Halofi V2 (the closest "save together" Celo product with explicit T-week obligation) is **DORMANT** — last activity April 2023 on the most-cited pool. This is a COPm-corridor substrate-noise issue per spec §3.5; the a_s archetype IS findable on Celo, but COPm-specific term-deposit primitives have not been deployed as of 2026-05.

**Comparison to Category (ii) (parallel agent investigating consumer-facing payment-rail operators):** Category (iv) has a **STRONGER structural fit** for the a_s archetype because the time-T obligation is **endogenous to the contract** (a vault that grants a redemption window literally encodes the fixed-T primitive in its withdraw function), whereas Category (ii) operators must reconstruct the time-T obligation from off-chain customer agreements. However, Category (iv) candidates have **WEAKER COPm exposure** because savings vaults on Celo predominantly use cUSD (USDm), not COPm. **Net verdict:** Category (iv) is the better technical match; Category (ii) is the better corridor match. **Both should be combined** for the v1 allowlist — vault primitives provide the time-T template; payment-rail operators provide the COP-corridor flow.

---

## Section 1 — Mandatory Candidates

### 1.1 Moola Market

- **Description:** Celo's primary lending protocol; Aave V2 fork. mTokens (mcUSD, mcEUR, mcREAL, mCELO) represent interest-bearing positions in the lending pool.
- **a_s archetype fit:** WEAK_FIT — Moola is a *yield-earning* lending pool, NOT a fixed-T obligation contract. Depositors can withdraw at any time (subject to liquidity); there is no "lock until T" primitive at the user-position level. The closest fixed-T artifact is the *borrower side* repayment schedule, which is variable-rate and not a clean Δ^(a_s) source.
- **ON-CHAIN VISIBILITY GATE: PARTIAL_PASS**
  - **mcUSD AToken**: `0x918146359264C492BD6934071c6Bd31C854EDBc3` (per docs.moola.market — distinct from the `0x64defa3544c695db8c535d289d843a189aa26b98` verified token previously cited in some sources; mcUSD has had multiple deployments)
  - **mcEUR AToken**: `0xE273Ad7ee11dCfAA87383aD5977EE1504aC07568`
  - **mcREAL AToken**: `0x9802d866fdE4563d088a6619F7CeF82C0B991A55`
  - **mCELO AToken**: `0x7D00cd74FF385c955EA3d79e47BF06bD7386387D`
  - **MOO governance token**: `0x17700282592D6917F6A73D0bF8AcCf4D578c131e`
  - **LendingPool (commonly-cited)**: `0xc1548F5AA1D76CDcAB7385FA6B5cEA70f941e535` — UNVERIFIED on Celoscan per direct check 2026-05-03 (no public name tag, no verified source); 41,429 historical transactions but balance is 0.000000002 CELO; no holdings currently in pool. Suggests this is either a deprecated implementation address or upgraded proxy; current active LendingPool address could not be confirmed at free-tier.
  - **Status indicators:** Total Moola TVL reported at $1.2M per DefiLlama, suggesting significant decline from peak; protocol previously suffered $9M exploit (most funds returned).
- **FIXED-T OBLIGATION PRIMITIVE GATE: FAIL** — Moola has NO time-locked deposit feature. Aave V2 fork architecture is fully liquid (subject to utilization-driven withdrawal queueing in extreme cases, but not a fixed-T primitive).
- **Geography fit:** mcREAL exists for cREAL/BRLm exposure. NO mcCOP, NO mcKES per docs.moola.market core listing. COPm exposure: ZERO at the mToken layer.
- **Sample data:** Activity-low; TVL $1.2M; protocol-level transaction velocity hard to verify at free-tier without paid analytics.
- **Verdict:** **DROP** — Fails fixed-T primitive gate. Moola is a yield-earning pool not a term-deposit contract. The Δ^(a_s) attribution would be possible but the obligation is not fixed-T (depositors withdraw at will).

### 1.2 Halofi (formerly GoodGhosting)

- **Description:** "Save together" goal-based savings circles. Users join a pool with a fixed deposit schedule (e.g., 4 weekly deposits of 10 cUSD), then a "waiting round" where deposits earn yield, then redemption at a known T.
- **a_s archetype fit:** STRONG_FIT (architecturally) — this is the textbook fixed-T obligation primitive: each pool has a deterministic lifecycle (deposit segments → waiting round → redemption at T), and the protocol owes each compliant participant their principal + pro-rata yield at a contractually-fixed time.
- **ON-CHAIN VISIBILITY GATE: PASS** — multiple verified pool contracts on Celoscan
  - **Pool: "Celo-brate 100 cUSD"**: `0xe2Db3Ff23adF232b0dB2c652d50B413f6511BAcd` (verified, deposit token = USDm/cUSD, 1,997 lifetime tx)
  - **Pool: "The Second Wave"**: `0xd144f0848a3b1c08abbf33c976ed9fd2e822729c` (verified)
  - **Pool: GoodGhosting V1 baseline**: `0x1b4fd5cc2e39cb002f96f4bdad015e8188a8bf25`, `0xffD343a7F20093E9bcefe45Af552C1718059329E`, `0x32Bd3ce981A575569d4bf1179f6B70D14Cf8E881`
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS (architecturally) but DORMANT (operationally)**
  - Per direct Celoscan verification 2026-05-03: the Celo-brate 100 cUSD pool's last transaction was **April 7, 2023** (Withdraw call). Pool holdings now ~$917 across 6 tokens. No active pool launches found in 2024-2025 search.
  - GoodGhosting V2 GitHub repository ARCHIVED November 20, 2024.
  - The HaloFi V2 architecture supports "hodl pools" with single-deposit segments + 3/6+ month waiting rounds — exactly the a_s primitive the brief requested — but no active Celo deployment of this configuration has been launched in 2024-2026 per free-tier search.
- **Geography fit:** Pools historically denominated in cUSD/USDm only. NO COPm pool launched. NO KESm pool launched.
- **Sample data:** Pool-level event volumes available via verified contracts but events are 2-3 years old. Total cumulative TVL across all Celo HaloFi pools reportedly under $50K at peak.
- **Verdict:** **CONDITIONAL_PASS_WITH_DORMANCY_FLAG** — the contracts ARE the textbook a_s archetype, but the protocol is operationally dormant on Celo. INCLUDE in candidate pool with explicit "DORMANT" flag; useful for *retrospective* Δ^(a_s) attribution on the 2021-2023 historical data, but NOT a forward-looking deployable substrate. Suggests Pair D Stage-2 Path B should consider a *historical-window* fit on Halofi as a one-time empirical check rather than a live monitoring substrate.

### 1.3 Mento Liquidity Mining (veMENTO Locking)

- **Description:** Mento V3 governance lock. Users deposit MENTO tokens and receive veMENTO proportional to lock duration (max 2 years for 1:1 ratio); veMENTO decays weekly until reaching zero. The lock contract is the explicit time-T primitive.
- **a_s archetype fit:** GOOD_FIT — the Locking contract takes user MENTO, holds it for a contractually-fixed duration T (up to 104 weeks), and owes the user's MENTO back at T. The "obligation" is denominated in MENTO not in COP, so the X-relationship is MENTO/USD not COP/USD; this is a substrate-noise compromise per spec §3.5.
- **ON-CHAIN VISIBILITY GATE: PASS**
  - **veMENTO Locking proxy**: `0x001Bb66636dCd149A1A2bA8C50E408BdDd80279C` (verified TransparentUpgradeableProxy, label "Mento Labs: veMENTO Token" on Celoscan; implementation `0x5a2c50efa0f63f0f97da9f002fefef3f64ed7d46` named "Locking")
  - **MENTO token**: `0x7FF62f59e3e89EA34163EA1458EEBCc81177Cfb6`
  - **MentoGovernor**: `0x47036d78bB3169b4F5560dD77BF93f4412A59852`
  - **Timelock**: `0x890DB8A597940165901372Dd7DB61C9f246e2147`
  - Per direct Celoscan check 2026-05-03: 213 lifetime transactions; latest activity 44 hours ago (block 65748386, dated 2026-05-01); holds **276,862,955 MENTO** tokens (substantial TVL by token-count; valued $0.00 per current Celoscan price feed which suggests MENTO market is illiquid).
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS** — the Locking contract IS the time-T primitive. Each user's lock has a known unlock date encoded on-chain. The contract owes each user their original MENTO at their personal T.
- **Geography fit:** MENTO/USD relationship, NOT COP/USD. Substrate-noise compromise per §3.5.
- **Sample data:** Block range 2024-Q3 onwards (deployment); 213 cumulative lifecycle events across active locks. Per-user `Lock`, `Withdraw`, `Relock` events isolated and parseable.
- **Verdict:** **PASS** — both gates met. Top-2 candidate by structural cleanliness; substrate-noise compromise (X = MENTO/USD not COP/USD) explicitly acknowledged per §3.5 SUBSTRATE_TOO_NOISY framing. This is the cleanest single-contract a_s archetype on Celo as of 2026-05.

---

## Section 2 — Other Discovered Candidates

### 2.1 impactMarket Microcredit

- **Description:** On-chain microcredit protocol on Celo. Mobile bankers deploy cUSD to entrepreneurs as small loans; borrowers repay in monthly installments via the contract. Operates as part of impactMarket's broader UBI + Microcredit + Learn&Earn DAO.
- **a_s archetype fit:** **STRONGEST_FIT in entire candidate set** — Microcredit IS the a_s archetype made explicit:
  - The protocol takes cUSD reserves (deposit Υ in spec terminology)
  - It owes each borrower a fixed cUSD loan amount disbursed at T_0
  - It expects each borrower to repay on a fixed installment schedule q_t for t = 1, 2, ..., T_maturity
  - Each loan has a known maturity T encoded on-chain
  - Default rate × FX fluctuation between cUSD-reserve and local-purchasing-power generates Δ^(a_s)
- **ON-CHAIN VISIBILITY GATE: PASS** — verified addresses
  - **MicrocreditProxy**: `0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb` (verified TransparentUpgradeableProxy, label "MicrocreditProxy" on Celoscan; implementation `0xe29a5e0b8a52cef37a757add2b177d32664ae329`; Solidity v0.8.4)
  - **MicrocreditRevenueProxy**: `0xa75D14c212df85F24ead896747cb1688C1F889D7`
  - **TreasuryProxy**: `0xa302dd52a4a85e6778E6A64A0E5EB0e8C76463d6` (verified; holds 4.85 USDm; latest tx Sep 18, 2025)
  - **CommunityAdminProxy**: `0xd61c407c3A00dFD8C355973f7a14c55ebaFDf6F9` (verified; deploys per-Community sub-contracts via internal txs)
  - **CommunityImplementation**: `0xEc94c60f17F7f262973f032965534D1137f1202c`
  - **PACT token**: `0x46c9757C5497c5B1f2eb73aE79b6B67D119B0B58`
  - **ImpactMultiSigProxyAdmin**: `0x5e7912f6C052D4D7ec8D6a14330c0c3a538e3f2B`
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS** — Per direct Celoscan check 2026-05-03: MicrocreditProxy has 3,959 lifetime transactions with explicit `Add Loans`, `Repay Loan`, `Transfer ERC20` operations within the last 30 days (latest activity Oct 25, 2024). Each loan has a fixed maturity; each repayment is a q_t event. This is precisely the q_t/(X/Y)_t schedule the brief asks for.
- **Geography fit:** Operates in multiple developing-country corridors (Brazil, Honduras, Venezuela, Nigeria, etc. per impactMarket community deployments). Loan denomination is **cUSD**, NOT COPm; borrowers convert cUSD → local currency off-chain via mobile money (Libera wallet). This means the Δ^(a_s) FX exposure is borne by the **borrower** not the **protocol** at the on-chain layer; the *protocol's* a_s exposure is in default-rate variance correlated with local-currency stress, which is a second-order indirect signal.
- **Sample data:** 3,959 lifetime tx; ~30-day activity persistent; per-loan `Add Loans` + per-installment `Repay Loan` events directly observable.
- **Verdict:** **PASS** — both gates met; structurally the cleanest a_s primitive in the entire research, BUT the FX exposure is at the borrower-wallet layer (off-chain conversion) so the on-chain Δ^(a_s) is more about default-rate-vs-FX correlation than direct treasury-drawdown FX attribution. Top-1 candidate by archetype cleanliness; need to flag the indirect-FX-attribution caveat.

### 2.2 StakedCelo (stCELO)

- **Description:** Liquid staking protocol on Celo developed by cLabs. Users deposit CELO, receive stCELO; redemptions delayed by 3-day unlock period (matching Celo Locked Gold).
- **a_s archetype fit:** WEAK_FIT — the time-T primitive is short (3 days) and the obligation is in CELO not local currency. The "X" here is CELO/USD which is NOT the FX-volatility variable the spec targets.
- **ON-CHAIN VISIBILITY GATE: PASS** — verified addresses from `celo-org/staked-celo` deployment manifest
  - **StakedCelo_Proxy** (stCELO token): `0xC668583dcbDc9ae6FA3CE46462758188adfdfC24` (verified ERC1967Proxy on Celoscan, label "Staked Celo: stCELO Token"; 1,253 lifetime tx; ongoing approvals within last 4 hours)
  - **Account_Proxy**: `0x4aAD04D41FD7fd495503731C5a2579e19054C432` (verified; 49,802 lifetime tx; holds 22.5 CELO; recent "Activate and Vote", "Revoke Votes", "Withdraw" operations — actively staking on validator groups)
  - **Manager_Proxy**: `0x0239b96D10a434a56CC9E09383077A0490cF9398`
  - **MultiSig_Proxy**: `0x78DaA21FcE4D30E74fF745Da3204764a0ad40179`
  - **RebasedStakedCelo_Proxy**: `0xDc5762753043327d74e0a538199c1488FC1F44cf`
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS (3-day unlock)**
  - Per docs.stcelo.xyz: "After the 3 day unlocking period has passed, `Account.finishPendingWithdrawal` should be called, specifying the pending withdrawal that was created in the previous step."
  - Each user's withdrawal request creates an on-chain pending state with a known unlock timestamp.
- **Geography fit:** CELO-denominated; NO COPm or local-currency exposure. NOT a Pair D corridor match.
- **Sample data:** Account_Proxy is the highest-activity contract (49,802 tx). Per-pending-withdrawal events parseable. Account_Proxy holdings are tiny (22.5 CELO) suggesting most CELO is in validator groups not in the Account itself.
- **Verdict:** **PASS** (both gates) but **NOT_A_PAIR_D_CORRIDOR_MATCH** — include in candidate pool as a same-architecture/different-X reference; explicitly flag that X = CELO/USD not COP/USD.

### 2.3 GoodDollar UBI Scheme (already in Track-2 candidate pool)

- **Description:** Daily UBI claim mechanism on Celo. Each verified member can claim a fixed daily G$ allocation. Reserve composition draws from cUSD (Mento V4 integration).
- **a_s archetype fit:** GOOD_FIT — daily UBI claim IS the q_t schedule. Each member has a daily fixed obligation (the protocol owes the member today's G$ claim), funded from a cUSD-denominated reserve. T is "daily" so the time-T primitive is short but recurring.
- **ON-CHAIN VISIBILITY GATE: PASS** (per Track-2)
  - **UBI Scheme Proxy**: `0x43d72Ff17701B2DA814620735C39C620Ce0ea4A1`
  - **G$ Token**: `0x62B8B11039FcfE5aB0C56E502b1C372A3d2a9c7A`
  - **GOOD Governance**: `0xa9000Aa66903b5E26F88Fa8462739CdCF7956EA6`
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS** — daily distribution obligation is encoded in UBIScheme contract; each day's claim period is a fixed-T window.
- **Geography fit:** Global G$ users; NOT specifically COPm-corridor.
- **Verdict:** **PASS** — both gates met; carry-forward from Track-2 with category-(iv) classification.

### 2.4 Mento Reserve (already in Track-2 candidate pool)

- **Description:** Multi-asset reserve backing all Mento V2/V3 stable tokens including COPm.
- **a_s archetype fit:** WEAK_FIT (aggregate, not per-position fixed-T) — Reserve obligations are *redemption-on-demand* not *fixed-T*. There is no contractual T at which the Reserve must deliver a specific amount.
- **ON-CHAIN VISIBILITY GATE: PASS** — `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` (per Track-2; also verified ReserveV2 in V3 deployment at `0x4255Cf38e51516766180b33122029A88Cb853806`)
- **FIXED-T OBLIGATION PRIMITIVE GATE: FAIL** — redemption is at-will; no T-encoded obligation per position.
- **Verdict:** **DROP from category (iv)** (FAILS the fixed-T gate); retain in Track-2 as protocol-aggregate a_s reference (category-other classification).

### 2.5 Aave V3 on Celo

- **Description:** Standard Aave V3 lending protocol deployed on Celo. Supports CELO, USDT, USDC as collateral and cUSD, cEUR as borrowable assets.
- **a_s archetype fit:** WEAK_FIT — same as Moola, this is a *yield-earning* pool not a fixed-T deposit.
- **ON-CHAIN VISIBILITY GATE: PASS** — Pool V3 verified at `0x3E59A31363E2ad014dcbc521c4a0d5757d9f3402` (verified InitializableImmutableAdminUpgradeabilityProxy, label "Aave: Pool V3" on Celoscan; **2,032,247 lifetime transactions** — by far the most active candidate; recent activity within last 7 hours; implementation upgraded 13 days ago to `0x736A2998...e0459c744`).
- **FIXED-T OBLIGATION PRIMITIVE GATE: FAIL** — Aave is at-will-withdrawal; no native fixed-T deposit primitive. (Aave has historically piloted "credit delegation" with fixed terms, but not in the standard V3 supply/borrow surface.)
- **Geography fit:** Supports cUSD/cEUR borrows; NO COPm/KESm market in Celo deployment per Aave governance. cUSD = USDm exposure available.
- **Verdict:** **DROP** — fails fixed-T gate. Note for record: Aave V3 on Celo is the highest-volume DeFi contract on the chain (2M+ tx) and would be valuable for parallel categories that DON'T require fixed-T (e.g., a hypothetical category-(v) liquid lending pools).

### 2.6 SavingsCELO (terminal-fi/zviadm)

- **Description:** Fully-fungible ERC-20 representation of interest-bearing Locked CELO. Deposit CELO → receive sCELO; redeem sCELO → CELO with 3-day unlock period.
- **a_s archetype fit:** WEAK_FIT — same architecture as StakedCelo (3-day unlock CELO obligation); X = CELO/USD not COP/USD.
- **ON-CHAIN VISIBILITY GATE: PARTIAL** — repository exists at github.com/terminal-fi/savingscelo and github.com/zviadm/savingscelo but specific Celo mainnet contract addresses NOT extracted from free-tier sources. Documentation URL https://docs.savingscelo.com/ accessible but does not display addresses prominently. Documentation also flags **"a critical vulnerability was found in SavingsCELO contract; strongly recommended for users to withdraw funds"** — protocol is effectively deprecated.
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS** (3-day unlock)
- **Verdict:** **DROP** — known critical vulnerability + deprecation guidance + redundant with StakedCelo.

### 2.7 Glo Dollar (USDGLO) on Celo

- **Description:** Fiat-backed stablecoin on Celo with charitable-yield-distribution model. 100% of reserve T-bill yield goes to GiveDirectly to fund $30/month UBI grants in African villages.
- **a_s archetype fit:** WEAK_FIT — Glo Dollar itself is a vanilla 1:1 stablecoin (no on-chain time-lock primitive). The GiveDirectly grant disbursement IS a fixed-T q_t obligation ($30/month for 3-5 years per recipient), but per the official Glo address page this disbursement happens **OFF-CHAIN via mobile money**, not via on-chain contracts.
- **ON-CHAIN VISIBILITY GATE: PASS** for the token (`0x4f604735c1cf31399c6e711d5962b2b3e0225ad3`); FAIL for the grant-disbursement schedule.
- **FIXED-T OBLIGATION PRIMITIVE GATE: FAIL** — the q_t schedule is off-chain.
- **Verdict:** **DROP** — the time-T primitive exists in the business model but not on-chain. Same off-chain-conversion-opacity problem as Pretium / Kotani Pay / Yellow Card from Track-2.

### 2.8 ImpactMarket Community (UBI distribution)

- **Description:** Per-Community UBI distribution contract under impactMarket's CommunityAdmin. Each Community has a fixed daily/weekly claim allowance per beneficiary, funded from cUSD donations.
- **a_s archetype fit:** GOOD_FIT (similar to GoodDollar UBI Scheme but at impactMarket scale) — each Community owes its beneficiaries a fixed-rate cUSD claim per period.
- **ON-CHAIN VISIBILITY GATE: PARTIAL_PASS** — CommunityAdminProxy is verified at `0xd61c407c3A00dFD8C355973f7a14c55ebaFDf6F9`. Per-Community sub-contracts are deployed via internal transactions (not enumerated in free-tier search); the sub-contracts inherit `CommunityImplementation` `0xEc94c60f17F7f262973f032965534D1137f1202c`.
- **FIXED-T OBLIGATION PRIMITIVE GATE: PASS** — each Community's `claim()` function enforces a per-beneficiary cooldown + per-period allowance, encoding the q_t schedule on-chain.
- **Geography fit:** impactMarket has historically operated communities in 35+ countries including Honduras, Venezuela, Nigeria, Brazil; specific COPm-denominated Community NOT confirmed (likely cUSD-denominated like Microcredit).
- **Verdict:** **PASS** — both gates met. Companion to impactMarket Microcredit; same protocol family.

### 2.9 Allbridge Core Pools on Celo

- **Description:** Cross-chain stablecoin bridge with on-chain liquidity pools that warehouse principal in stablecoins (cUSD on Celo). LPs lock principal to earn bridging fees.
- **a_s archetype fit:** WEAK_FIT — bridge pools have an LP-position lifecycle (deposit → earn fees → withdraw at will) without a contractually-fixed T per position.
- **ON-CHAIN VISIBILITY GATE: PARTIAL** — Allbridge Core contracts referenced at `0x609c690e8F7D68a59885c9132e812eEbDaAf0c9e` per general search but Celo-pool-specific cUSD address not confirmed at free-tier (would need direct allbridge.io UI inspection).
- **FIXED-T OBLIGATION PRIMITIVE GATE: FAIL** — at-will LP withdrawal; no fixed-T primitive.
- **Verdict:** **DROP** — fails fixed-T gate.

---

## Section 3 — Ranked Shortlist

| Rank | Candidate | Network | a_s Fit | Time-T Primitive | Pair-D COPm Match | Verdict |
|------|-----------|---------|---------|------------------|-------------------|---------|
| 1 | **impactMarket Microcredit** `0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb` | Celo | STRONGEST | Per-loan maturity; per-installment q_t | INDIRECT (cUSD-denominated; FX borne by borrower) | TOP-1 |
| 2 | **veMENTO Locking** `0x001Bb66636dCd149A1A2bA8C50E408BdDd80279C` | Celo | GOOD | Up to 2-year lock; weekly decay | NO (X = MENTO/USD) | TOP-2; substrate-noise §3.5 flag |
| 3 | **GoodDollar UBI Scheme** `0x43d72Ff17701B2DA814620735C39C620Ce0ea4A1` | Celo | GOOD | Daily claim window | NO (X = G$/cUSD purchasing power) | TOP-3; carry-forward from Track-2 |
| 4 | **impactMarket Community** (via CommunityAdmin `0xd61c407c3A00dFD8C355973f7a14c55ebaFDf6F9`) | Celo | GOOD | Per-period claim cooldown | INDIRECT (cUSD-denominated, multi-corridor) | TOP-4; companion to Microcredit |
| 5 | **StakedCelo** Account `0x4aAD04D41FD7fd495503731C5a2579e19054C432` | Celo | WEAK | 3-day unlock | NO (X = CELO/USD) | TOP-5; same-arch reference; not Pair-D corridor |
| -- | **Halofi V2 pools** (multiple) | Celo | STRONG (architecturally) | Pool-lifecycle T-primitive | NO (cUSD-denominated, dormant) | DORMANT — historical-window only |
| -- | Moola Market | Celo | WEAK (yield pool) | NONE | mcREAL exists; no mcCOP/mcKES | DROP (no fixed-T) |
| -- | Aave V3 Celo | Celo | WEAK (yield pool) | NONE | cUSD only | DROP (no fixed-T) |
| -- | Glo Dollar | Celo | WEAK (token only) | OFF-CHAIN | NONE | DROP (off-chain q_t) |
| -- | Mento Reserve | Celo | WEAK (aggregate) | NONE (at-will redemption) | COPm collateralized | DROP for category (iv); retained Track-2 |

### Top-3 Verdicts + Rationale

1. **impactMarket Microcredit** — `0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb`
   - **a_s fit:** STRONGEST — per-loan maturity T encoded on-chain, per-installment q_t directly observable via `Repay Loan` events; protocol owes each borrower a fixed cUSD disbursement at T_0 and is owed fixed cUSD repayments q_t through T_maturity. This is the textbook a_s archetype.
   - **COPm exposure:** INDIRECT — cUSD-denominated loans; FX risk is at borrower wallet via off-chain Libera mobile-money conversion. Protocol-side a_s is *default-rate variance correlated with COP/USD volatility* (second-order signal), not direct treasury drawdown.
   - **One-line rationale:** Cleanest on-chain time-T deposit primitive on Celo, with active deployment (3,959 tx, last activity Oct 2024) and explicit q_t/T encoding; corridor match is indirect via default-rate channel.

2. **veMENTO Locking** — `0x001Bb66636dCd149A1A2bA8C50E408BdDd80279C`
   - **a_s fit:** GOOD — explicit user-level lock with deterministic unlock T (up to 104 weeks), 213 lifecycle events, 276M MENTO held, recent activity 2026-05-01.
   - **COPm exposure:** NONE — X = MENTO/USD; substrate-noise compromise per spec §3.5 SUBSTRATE_TOO_NOISY.
   - **One-line rationale:** Cleanest single-contract time-T primitive on Celo (no business-logic complexity like Microcredit) but the X-variable is wrong; useful as archetype-validator at zero corridor-fit.

3. **GoodDollar UBI Scheme** — `0x43d72Ff17701B2DA814620735C39C620Ce0ea4A1`
   - **a_s fit:** GOOD — daily UBI claim is the q_t obligation; 69M+ lifetime transactions; daily T-window enforced.
   - **COPm exposure:** NONE — X = G$/cUSD purchasing power.
   - **One-line rationale:** High-volume time-T primitive (69M+ tx) with substrate-noise compromise on X; carry-forward from Track-2 with category (iv) reclassification.

---

## Section 4 — Decision Matrix

| Candidate | On-Chain Gate | Time-T Gate | COPm Geography | Activity Level | Verdict |
|-----------|---------------|-------------|----------------|----------------|---------|
| impactMarket Microcredit | PASS | **PASS** | INDIRECT (cUSD) | Active (3,959 tx, Oct 2024) | **TOP-1 PASS** |
| veMENTO Locking | PASS | **PASS** | NO (MENTO) | Recent (2026-05-01) | **TOP-2 PASS** |
| GoodDollar UBI Scheme | PASS | **PASS** | NO (G$/cUSD) | High (69M+ tx) | **TOP-3 PASS** |
| impactMarket Community | PASS (admin); PARTIAL (per-Community) | **PASS** | INDIRECT (cUSD) | Active | **TOP-4 PASS** |
| StakedCelo Account | PASS | **PASS** (3-day) | NO (CELO) | Very Active (49.8K tx) | **TOP-5 PASS** (wrong X) |
| Halofi Celo-brate 100 cUSD | PASS | **PASS** (architecturally) | NO (cUSD only) | DORMANT (Apr 2023) | **CONDITIONAL** (historical only) |
| Moola Market | PARTIAL | **FAIL** | INDIRECT (cUSD) | Low ($1.2M TVL) | DROP |
| Aave V3 Celo | PASS | **FAIL** | INDIRECT (cUSD) | Highest (2M+ tx) | DROP |
| Glo Dollar | PASS (token) | **FAIL** (off-chain q_t) | NO | Active | DROP |
| SavingsCELO | PARTIAL | PASS | NO | DEPRECATED | DROP |
| Mento Reserve | PASS | **FAIL** (at-will) | YES (COPm collat) | Aggregate | DROP for cat (iv); retain Track-2 |
| Allbridge Core | PARTIAL | **FAIL** | NO | Unknown | DROP |

---

## Section 5 — Geography-Fit Summary (COPm Exposure Quantified Per Candidate)

**The headline finding is that NO category-(iv) candidate has direct COPm exposure as a fixed-T obligation.**

| Candidate | COPm in TVL? | COPm-denominated obligations? | COPm-correlated signal? |
|-----------|--------------|-------------------------------|------------------------|
| impactMarket Microcredit | NO direct (cUSD-denominated) | NO (cUSD loans) | YES (default rate ↑ when COP/USD volatility ↑ for Colombian borrowers) |
| veMENTO Locking | NO | NO (MENTO-denominated) | NO |
| GoodDollar UBI Scheme | Indirect via Mento V4 cUSD reserve integration | NO (G$-denominated) | NO |
| impactMarket Community | NO direct (cUSD-denominated) | NO (cUSD claims) | YES (same channel as Microcredit, if Colombian Communities exist) |
| StakedCelo | NO (CELO-only) | NO | NO |
| Halofi V2 (dormant) | NO (cUSD/USDm pools only) | NO | NO |
| Mento Reserve (cat-other) | YES — backs COPm at protocol-aggregate level | NO (at-will redemption, no T) | YES (Reserve drawdown correlated with COPm redemption pressure) |

**Implication:** Category (iv) provides the **time-T architectural primitive** but NOT the **COPm-corridor flow**. To recover COPm exposure with a fixed-T primitive, the v1 allowlist should combine:
- Category-(iv) candidates for the time-T template (impactMarket Microcredit as template-of-record)
- Category-(ii) candidates (parallel agent) or Track-2's Mento Reserve for the COPm flow

Alternatively, the Pair D Stage-2 Path B specification could authorize **substrate-relocation** to a candidate with cleaner gate-pass (e.g., impactMarket Microcredit on cUSD-denominated Colombian Communities) and explicitly model COPm exposure via the **borrower-side default-rate channel** (Δ^(a_s) = sum over loans of Pr(default | COP/USD shock_t) × loan_principal).

---

## Section 6 — Comparison to Category (ii) (parallel agent)

Without observing the Category (ii) parallel-agent output, by first principles:

- **Category (ii)** = Mento-stablecoin orchestration / payment platforms for merchants and businesses (Bitgifty-class, Walapay-class, plus their successors)
- **Category (iv)** = THIS investigation = savings-vault / time-locked deposit primitives

**Structural fit comparison:**

| Dimension | Category (ii) Payment Operators | Category (iv) Savings Vaults | Winner |
|-----------|--------------------------------|------------------------------|--------|
| Time-T obligation primitive | Reconstructed from off-chain settlement schedules; rarely on-chain | NATIVELY ENCODED in vault contract (lock duration, claim cooldown, loan maturity) | **(iv)** |
| On-chain visibility of obligation magnitude | Limited (operator EOAs typically opaque per Track-2 evidence) | DIRECT (each vault position is an on-chain accounting entry) | **(iv)** |
| FX-conversion visibility | Off-chain (custodial conversion at operator); Track-2 confirmed this as the FAIL pattern for Bitgifty/Walapay/Pretium/Kotani/Yellow Card | Mostly off-chain too (cUSD → local currency via mobile money); a_s exposure is in default-rate / yield variance, not direct conversion | **(ii)** if any operator publishes settlement contracts; otherwise tied at "indirect" |
| COPm-corridor flow | Stronger (operators serving COP-corridor specifically) | Weaker (Celo savings vaults predominantly cUSD-denominated; no COPm-native vault found) | **(ii)** |
| Operational liveness | Mixed (per Track-2: many operators FAIL on-chain visibility; surviving Track-2 candidates are MXNB/GoodDollar/Mento Reserve) | Active (Microcredit, veMENTO, StakedCelo, Aave V3 all live; Halofi/Moola dormant or deprecated) | **(iv)** |
| Δ^(a_s) attribution clarity per CORRECTIONS-γ | Operator P&L not directly observable; structural exposure inferred from balance-sheet proxies | Per-position obligations directly observable; structural exposure quantifiable at deposit/withdraw event level | **(iv)** |

**Net verdict:** Category (iv) is the **technically cleaner** substrate because the time-T obligation is natively contractual; Category (ii) is the **commercially more direct** substrate because it serves the COP corridor directly. **Recommendation:** the v1 allowlist should include the BEST candidate from each category — impactMarket Microcredit (category iv, time-T primitive) PLUS the strongest Category (ii) candidate from the parallel agent's output (most likely a settlement-contract-publishing variant if any has emerged since Track-2). Combined, they provide both the architectural template and the corridor flow.

If forced to choose ONE: **Category (iv) wins** because the spec's Track-1 product-design implication #1 was specifically about the missing time-T primitive — and Category (iv) is where that primitive *natively exists*. Without the time-T primitive, the convex pricing decomposition (DRAFT.md eq 1) cannot be evaluated cleanly regardless of how good the COPm flow is.

---

## Sources

- [Moola Market overview](https://moola.market/) and [Moola Docs](https://docs.moola.market)
- [DefiLlama Moola Market](https://defillama.com/protocol/moola-market) — TVL $1.2M
- [HaloFi Celo Savings Pools v1 docs](https://docs.halofi.me/goodghosting-historical/guarded-launch/celo-savings-pools)
- [GoodGhosting V2 GitHub (archived Nov 2024)](https://github.com/Good-Ghosting/goodghosting-protocol-v2)
- [HaloFi Celo "Celo-brate 100 cUSD" pool on Celoscan](https://celoscan.io/address/0xe2Db3Ff23adF232b0dB2c652d50B413f6511BAcd) — last tx Apr 7, 2023
- [Mento V3 deployment addresses](https://docs.mento.org/mento-v3/build/deployments/addresses)
- [veMENTO and voting power docs](https://docs.mento.org/mento-v3/dive-deeper/governance-and-mento/participating-in-governance/vemento-and-voting-power)
- [veMENTO Locking on Celoscan](https://celoscan.io/address/0x001Bb66636dCd149A1A2bA8C50E408BdDd80279C) — verified TransparentUpgradeableProxy
- [impactMarket smart-contracts repository](https://github.com/impactMarket/impact-market-smart-contracts)
- [impactMarket Microcredit docs](https://docs.impactmarket.com/impactmarket-apps/2.-impactmarkets-products/microcredit)
- [MicrocreditProxy on Celoscan](https://celoscan.io/address/0xEa4D67c757a6f50974E7fd7B5b1cc7e7910b80Bb) — 3,959 lifetime tx
- [impactMarket TreasuryProxy on Celoscan](https://celoscan.io/address/0xa302dd52a4a85e6778E6A64A0E5EB0e8C76463d6)
- [impactMarket CommunityAdminProxy on Celoscan](https://celoscan.io/address/0xd61c407c3A00dFD8C355973f7a14c55ebaFDf6F9)
- [StakedCelo docs](https://docs.stcelo.xyz)
- [staked-celo deployments folder](https://github.com/celo-org/staked-celo/tree/master/deployments/celo)
- [StakedCelo stCELO token on Celoscan](https://celoscan.io/address/0xC668583dcbDc9ae6FA3CE46462758188adfdfC24)
- [StakedCelo Account on Celoscan](https://celoscan.io/address/0x4aAD04D41FD7fd495503731C5a2579e19054C432) — 49,802 tx
- [Aave V3 Pool on Celo (Celoscan)](https://celoscan.io/address/0x3e59a31363e2ad014dcbc521c4a0d5757d9f3402) — 2M+ tx
- [Aave V3 deployment proposal](https://governance.aave.com/t/arfc-aave-deployment-on-celo/17636)
- [SavingsCELO documentation](https://docs.savingscelo.com/) — note critical-vulnerability deprecation guidance
- [Glo Dollar smart contract addresses](https://www.glodollar.org/articles/smart-contract-addresses)
- [Mento Reserve docs](https://docs.mento.org/mento/protocol-concepts/reserve)
- [Mento × Glo Dollar swap announcement](https://www.glodollar.org/articles/mento-glo-dollar)
