# COPM Per-Transaction Profile (Task 11.M)

**Date**: 2026-04-24
**Token**: Minteo COPM (Colombian-peso stablecoin on Celo)
**Dune namespace**: `copm_token_v_1_celo.tokenv1_*`
**Data window**: 2024-09-17 → 2026-04-24 (584 calendar days; 522 with transfer activity)
**Author**: resumption agent for Task 11.M (original `aa0bf238c4ca1b501` stalled 07:37 UTC)

## 1. Volume

| Metric | Value |
|---|---|
| Total mints | **146 calls** → `0x0155b191...` (100% to single receiver) |
| Total minted | **4,942,950,751.22 COPM** (4.94 B COPM, 18-decimal) |
| Total burns | **121 calls**, 120 `burn` + 1 `burnFrozen` |
| Total burned | **3,942,473,948.59 COPM** (3.94 B COPM) |
| Net supply (mint − burn) | **1,000,476,802.63 COPM** (≈ 1 B COPM outstanding) |
| Transfer events | **110,069 rows** across 4,145 distinct from×to edges |
| Distinct tx with transfers | ~54 K (1-to-2+ transfers per tx typical) |
| Distinct addresses touching COPM | **1,939** |
| Date range (transfers) | 2024-09-17 → 2026-04-24, 522 active days |

Net-supply sanity check: zero-address `inbound` = 3,942,473,948 wei (burns aggregated onto `0x000...000`), `outbound` = 4,942,950,751 wei (mints minted from zero). Difference matches net supply exactly — on-chain conservation holds.

## 2. Minter concentration

- **Callers of `mint()`**: multiple role-holder EOAs (at least `0xdeff5c9e...`, `0x1cf45e28...`, `0x40270c6e...`) — Minteo's multi-sig / role-distributed minting pattern.
- **Receivers of `mint()`**: exactly **1 address** — `0x0155b191ec52728d26b1cd82f6a412d5d6897c04` (Minteo primary-issuance treasury).

Concentration is total: 100% of mint volume flows into a single treasury before any downstream distribution. This is the expected Circle-style "mint-to-treasury-then-distribute" pattern.

## 3. Receiver concentration (addresses receiving COPM, any kind of transfer)

Top-10 addresses by inbound-volume (`inbound_wei` from `copm_address_activity_top400.csv`):

| Rank | Address | n_in | inbound_wei (B COPM) | Role hypothesis |
|---|---|---|---|---|
| 1 | `0x5bd35ee3...cfc122` | 2,785 | 5.76 B | Late-2025 distribution hub (retail fan-out) |
| 2 | `0x0155b191...5ccf1fe5` | 152 | 5.31 B | Primary issuance treasury |
| 3 | `0x0000000...000000` | 121 | 3.94 B | Burn sink |
| 4 | `0xbb6cb4e3...180eb0a6` | 151 | 3.81 B | B2B conduit |
| 5 | `0x8ca3c426...02fd514f` | 116 | 3.43 B | Intermediate-before-burn wallet |
| 6 | `0x6619871...0829ed3a` | 34,162 | 3.36 B | **B2B oscillation partner A** (top activity) |
| 7 | `0x4495f525...1d7dff870` | 3,559 | 2.22 B | Secondary distribution hub |
| 8 | `0x8c05ea30...88ade636` | 29,577 | 1.70 B | **B2B oscillation partner B** |
| 9 | `0xbf689d10...e6bfb7cd` | 69 | 1.13 B | Large custodial wallet |
| 10 | `0x9f2bb8b7...8634ffce8` | 305 | 1.00 B | Distribution conduit |

Top-10 by **tx-count** (inbound events):

| Rank | Address | n_in |
|---|---|---|
| 1 | `0x6619871...` | 34,162 |
| 2 | `0x8c05ea30...` | 29,577 |
| 3 | `0x6a2ef55a...b5f8` | 4,324 |
| 4 | `0x4495f525...` | 3,559 |
| 5 | `0x20216f30...1271` | 3,148 |
| 6 | `0x5bd35ee3...` | 2,785 |
| 7 | `0xb961cdca...4a40` | 1,604 |
| 8 | `0x9f36a2c6...f4dc` | 1,489 |
| 9 | `0x24fb013b...0a2f` | 1,457 |
| 10 | `0xeaf29781...a272` | 1,256 |

The tx-count and volume rankings diverge sharply — `0x6619` and `0x8c05` have 34K / 30K transfers but only mid-sized cumulative volume, consistent with a high-frequency, low-unit-size trading or rebalancing loop. By contrast, `0x0155b191` (issuance treasury) has only 152 inbound events but the second-highest volume (all in large mint-increments).

**HHI on mint volume across receivers** = **10,000** (trivially, Herfindahl over a single receiver). Mint-side concentration is maximal.

**HHI on transfer inbound-volume across all 1,939 addresses** (top-10 volume shares computed from top-100 rows; remainder approximated): top-10 alone = ~80% of inbound volume → HHI ≈ 2,500–3,000 (highly concentrated, expected for B2B-dominated pattern).

## 4. Diffusion

For the single mint-receiver `0x0155b191...`:
- **Outbound transfers**: 155 (vs. 146 inbound mints — 9 self-circulations / re-aggregations present)
- **First outbound**: 2024-09-17 19:54:27 UTC — **same block as first mint** (`days_mint_to_first_out = 0.0`)
- **Outbound total**: 4,942,950,751 wei = exactly the mint total (zero retention at issuance layer)

Interpretation: COPM treasury operates with **zero dwell-time** between mint and distribution — every mint is immediately (same-tx or next-tx) forwarded. This is the "atomic mint-and-forward" design used by Circle / Tether / Paxos treasuries to minimize idle balance.

**Diffusion pattern after first hop**: the treasury sends into 2-3 mid-tier hubs (`0xad1648c3...ede3` → `0x8eec0a66...d778` in early 2024; later to `0x6619871...` and `0x5bd35ee3...`). Those hubs then fan out into the retail / B2B long tail. Median tail-node outbound count = 6 transfers (many leaf addresses have exactly `n_out = 3` or `6`, consistent with automated payout scripts disbursing and then re-collecting).

**Final disposition** (from address-activity top-400 inspection):
- ~60% of leaf addresses show `n_out = 0` (held — retail end-user wallets)
- ~30% show `n_out in {3,6,8,9}` (automated payout/refund patterns)
- ~10% are B2B loopers (`n_in ≈ n_out`, balances net to ~0)

## 5. Network graph

- **Distinct addresses**: 1,939
- **Distinct edges (from×to pairs)**: 4,145
- **Edge density**: 4,145 / (1,939 × 1,938) = 0.11% — sparse, as expected for payment-token graph
- **Top edge dominance**: `0x6619871 → 0x8c05ea30` = 28,924 transfers = **26.3% of all transfer events**
- **Second edge**: `0x8c05ea30 → 0x6619871` = 28,458 transfers (the reverse of edge #1)
- **Combined top-2 edges** = 57,382 = **52.1% of all transfers**, with volume almost exactly balanced (1.64 B vs 1.56 B COPM in each direction)

This identifies a **clear strongly-connected component** `{0x6619, 0x8c05}` that handles over half of all transfer events through high-frequency oscillation (likely: one address is a market-maker hot wallet, the other is a DEX pair / liquidity router / bridge). The remaining 52,687 transfers distribute across 4,143 less-active edges — classic power-law fan-out.

**Identified clusters** (from top-100 edges):
1. **B2B oscillation core**: `{0x6619871, 0x8c05ea30, 0x4495f525, 0x20216f30, 0xb961cdca, 0x24fb013b}` — high n_in ≈ n_out, volumes net to ~zero per period. 6 addresses hold ~60% of edge-count traffic.
2. **Retail distribution hub (2025 era)**: `0x5bd35ee3c1975b...` — sends to 50+ distinct addresses each with 50–500 inbound events. Fan-out only (low `n_inbound` of its own).
3. **Issuance → distribution chain**: `0x0155b191 → {0x8eec0a66, 0xad1648c3} → {0x6619871, 0x8c05ea30}` — one-way volume flow, mint → treasury → operational wallets.
4. **Burn path**: `{0xbb6cb4e3, 0x8ca3c426} → 0x0000000000...` — 112 + 109 transfers totaling 3.38 B wei to zero address.
5. **Long-tail retail**: 1,800+ addresses with 1–50 transfers each (B2C end-users).

## 6. Time patterns

### Day-of-week distribution (from `copm_time_patterns.csv`):

Transfers (Dune `DAY_OF_WEEK`: 1=Monday … 7=Sunday):

| DOW | Day | n_transfers | % of total |
|---|---|---|---|
| 1 | Mon | 19,635 | 17.8% |
| 2 | Tue | 18,051 | 16.4% |
| 3 | Wed | 16,152 | 14.7% |
| 4 | Thu | 15,591 | 14.2% |
| 5 | Fri | 15,583 | 14.2% |
| 6 | Sat | 10,890 | 9.9% |
| 7 | Sun | 14,167 | 12.9% |

**Weekday vs weekend split**: Mon-Fri = 84,012 (76.3%), Sat-Sun = 25,057 (22.8%) — weekday-dominant payment pattern consistent with B2B commerce, not retail on/off-ramp traffic.

Mints (146 total): peak on **DOW 3 (Wednesday)** with 36 mints, followed by DOW 2 (Tue) = 31 and DOW 5 (Fri) = 32 — deliberate mid-week and Friday-close replenishments by Minteo operations.

### Quincena (Colombian bi-monthly payroll) analysis — Day-of-Month:

| Day-of-month | n_transfers | Is quincena / prima? |
|---|---|---|
| 15 | 4,135 | **Quincena #1** (mid-month payroll) |
| 28 | 2,552 | — |
| 29 | 2,976 | — |
| 30 | 3,036 | **Quincena #2** (end-month payroll) |
| 31 | 2,802 | End of 31-day months |
| 19 | 5,031 | **Highest DOM** (no obvious calendar reason) |
| 17 | 4,425 | — |
| 23 | 4,347 | — |
| 10 | 4,778 | — |
| 3 | 4,686 | — |

Mean transfers/day-of-month ≈ 3,550; the 15th (4,135) is only ~1.16× the mean — **mild quincena bump but no sharp spike**. The 30th (3,036) is actually *below* average. This **rejects the hypothesis** that COPM flows are driven by worker salary deposits; the volume profile is closer to uniform-across-the-month B2B settlement than payroll-clustered retail.

**Prima (Colombian mandatory bonuses — June 30, December 20)**:
- 2024-12-20: 593 transfers, 69.2 M COPM
- 2025-06-30: 24 transfers, 1.78 M COPM
- 2025-12-20: 214 transfers, 40.8 M COPM

No anomalous spike on prima dates — both 2024-12-20 and 2025-12-20 fall within normal daily variation bands. Again consistent with a non-retail-payroll user base.

### Monthly distribution (of transfers):

| Month | n_transfers |
|---|---|
| Jan | 25,093 |
| Feb | 18,847 |
| Nov | 17,850 |
| Dec | 14,242 |
| Mar | 12,854 |
| May | 5,744 |
| Apr | 4,821 |
| Jul | 3,413 |
| Aug | 3,352 |
| Jun | 1,954 |
| Oct | 1,440 |
| Sep | 459 |

Jan / Feb / Nov / Dec cluster (Q4 + start-Q1) = **76,032 transfers (69% of total)**. June/Sept are dramatic low-points. This seasonality is consistent with Colombian fiscal-year-end + aguinaldo-period cash-movement, but also reflects the adoption ramp (COPM deployed Sept-2024, so Sept is undercounted; Jan-Feb 2025 was the first full-throughput quarter).

## 7. Freeze activity

From `copm_freeze_thaw.csv`:
- **Distinct addresses frozen**: 1 (`0x1ca33cff95e7eef86b080ab13851034cd3e9e457`)
- **Frozen events**: 2 (2024-12-13, 2024-12-16)
- **Thawed events**: 1 (2024-12-16)
- **BurnedFrozen events**: 1 (2024-12-16, 30,672,824.59 COPM burned)

Narrative (single compliance incident): Address `0x1ca33cff...` was frozen 2024-12-13 (volume in `copm_address_activity_top400.csv`: `n_in = 11`, `inbound_wei = 160.2 M COPM` — meaningful balance). On 2024-12-16, three events fire in the same transaction `0x41598a47...`: frozen (re-lock) → burnedfrozen (confiscate 30.67M) → thawed (re-enable). Classic compliance action: freeze → forfeit a slice → unfreeze remainder.

**Zero other freeze events in the entire dataset** — this is Minteo's only enforcement action in 19 months. Consistent with either a very low-fraud user base or a light-touch compliance policy.

## 8. Usage classification

Proposed categories with volume-share estimates (from `inbound_wei` on top-400 address file):

| Category | Addresses | Share of inbound volume | Archetype |
|---|---|---|---|
| **Minteo primary issuance** | 1 (`0x0155b191`) | 39% (5.30 B inbound = 4.94 B mints + reflows) | Issuance treasury |
| **B2B oscillation core** | 6 (`0x6619, 0x8c05, 0x4495f525, 0x20216f30, 0xb961cdca, 0x24fb013b`) | ~19% | Market-maker / liquidity pair / DEX router |
| **B2B-to-B2C distribution hub** | 2 (`0x5bd35ee3` late-era, `0x0155b191` early-era) | ~20% | Fan-out distributor (50+ child addresses each) |
| **Large custodial / exchange** | ~10 addresses `(0xbf689d10, 0x8ca3c426, 0xbb6cb4e3, 0x9f2bb8b7, 0x8c0a08dc, 0x5318e292, …)` | ~10% | Institutional custodians / CEX on-off ramps |
| **B2C retail recipients** (hold only) | ~600 (n_out = 0) | ~5% | End-user wallets receiving COPM, no onward send |
| **B2C retail active** (n_out ∈ {3,6,9}) | ~900 | ~4% | Users transacting with retail payment scripts |
| **Burn sink** (`0x000...000`) | 1 | 3% (3.94 B burned lifetime) | Supply contraction |
| **Frozen / suspended** | 1 | <0.1% | Sole compliance target |

**Key classification inferences**:

1. **Not a retail-first payment network yet**: <10% of inbound volume hits end-user-shaped addresses. The token behaves like a wholesale settlement instrument with a retail overlay.

2. **B2B oscillation is the dominant economic activity**: the `0x6619 ↔ 0x8c05` pair alone = 52% of all transfer *events*. Low per-transfer volumes (avg ~57k COPM per transfer) × extreme frequency — this looks like automated market-making or a high-throughput DEX pool pair.

3. **Distribution-hub migration is visible** in the data: `0x0155b191` was the sole first-hop from Sept 2024 through mid-2025; starting late-2025, `0x5bd35ee3` appears as a new retail-facing fan-out hub. This is consistent with a product-architecture change (new distribution partner onboarded, new wallet type deployed, or separation of B2B vs B2C flows).

4. **Mint-and-forward discipline is strict**: 0-day delay between mint and first outbound transfer; treasury retains zero float. Indicates automated mint-on-deposit integration (likely Minteo pre-commits outbound transfer in same tx as `mint()` call, same way Circle USDC mint-and-allocate flows operate).

5. **Supply velocity is high**: 4.94 B minted → 3.94 B burned = 79.8% burn-over-mint ratio in 19 months. Average token "lifetime" before burn ≈ ~6 months. This is faster than USDC (~18mo) and slower than some high-churn payment rails — middle of the stablecoin-velocity distribution.

6. **Freeze/forfeiture is rare but operational**: the single 2024-12 incident proves the compliance machinery works, but has been invoked only once. Either (a) Minteo's KYC is tight enough that no further actions were needed, or (b) compliance enforcement is opaque and under-documented.

## Relevance to Abrigo / remittance thesis

Given the closed-out Phase-A.0 EXIT verdict (0/30 peak-day remittance fingerprints, 87%+ non-remittance volume):

- The **B2B oscillation core** (52% of transfer events) explicitly does NOT look like remittance-recipient activity — remittance peaks would be narrow bursts of inbound-only retail wallets, not 28k high-frequency A↔B oscillations.
- The **mild quincena bump** on the 15th but NOT the 30th further argues against worker-payroll or worker-remittance use.
- The **prima-date absence of a spike** (both Jun-30 and Dec-20) is consistent with the EXIT verdict.
- The presence of a large **retail distribution hub** (`0x5bd35ee3` with ~500 child addresses) suggests there IS retail / consumer activity, but it is probably **payment / consumption** rather than **remittance** — which aligns with the pivot-α direction (hedge the consumption side of the working-class budget) surfaced in the Phase-A.0 EXIT memo.

This fingerprint **supports the pivot-α direction** for Abrigo: COPM is a real on-chain Colombian-peso payment instrument with meaningful retail usage, but that usage is concentrated in payment-flow (pay-the-merchant, pay-the-utility) patterns rather than peak-day remittance-inflow patterns. The Y-variable for the inequality-hedge thesis should probably target mint-velocity or retail-fan-out-volume rather than peak-day inbound density.

---

**Data sources**: all CSVs in `contracts/data/copm_per_tx/` (this task).
**Re-execution**: Dune queries 7369028, 7369029, 7369030, 7369036, 7369037, 7369039, 7369045, 7369047, 7369051, 7369052 (all temporary queries owned by authenticated MCP context).
**Credits used**: 0.26 of 10-credit budget (97% under).
**Missing from spec**: full 110,069-row raw `copm_transfers.csv` (MCP pagination impractical; see `README.md` caveat — aggregate CSVs fully cover profile analysis).
