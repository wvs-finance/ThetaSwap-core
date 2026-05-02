---
spec_path: pair-d-stage-2-B-on-chain-data
spec_version: v1.1 (BLOCK + FLAG remediation of v1.0)
spec_predecessor_version: v1.0 (initial draft, sha256
  `7af22dd4f95324d777639d509f782efe41560469e29ca037f65c8940c0ee6997`)
spec_author: Data Engineer dispatch 2026-04-30 (v1.0); Data Engineer dispatch 2026-05-02 (v1.1)
spec_sha256: <to-be-pinned-after-2-wave-verify>
stage1_pinned_chain:
  spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
on_chain_pins:
  mento_v3_router_celo: "0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6"
  mento_v2_copm_celo: "0x8A567e2aE79CA692Bd748aB832081C45de4041eA"
  mento_v2_usdm_celo: "<to-be-pinned-at-v0-audit-closure>"
  mento_v3_fpmm_usdm_copm_pool_celo: "<to-be-pinned-at-v0-audit-closure-or-v0-HALT>"
  uniswap_v3_factory_celo: "<to-be-pinned-at-v0-audit-closure>"
  uniswap_v3_usdc_usdm_pool_celo: "<to-be-pinned-at-v0-audit-closure>"
  panoptic_factory_ethereum: "<to-be-pinned-at-v0-audit-closure>"
  bitgifty_settlement_celo: "<to-be-pinned-at-v0-audit-closure-or-v2-HALT>"
  walapay_settlement_celo: "<to-be-pinned-at-v0-audit-closure-or-v2-HALT>"
tooling_budget_committed: $49/mo Alchemy Growth (2026-04-30 user pin)
tooling_budget_pending: false
primary_data_path_v1_1: SQD Network public gateway (free, no documented rate limit) for bulk
  archive extraction; Alchemy Growth for spot RPC + receipts; Dune free tier (2500 SQL
  credits/mo) for ad-hoc analytical queries against pre-existing community datasets
internal_ladder: v0 (data audit) → v1 (CF^a_l) → v2 (CF^a_s) → v3 (CPO backtest)
convergence_point: v3 realized P&L envelope check on Path A v3 MC bounds
verifier_v1_wave1: pending (re-run on v1.1)
verifier_v1_wave2: pending (re-run on v1.1)
anticipated_corrections_gamma: deliverable rename "behavioral demand" →
  "structural exposure" (transaction archaeology cannot infer WTP for a non-existent
  instrument; cash-flow geometry yields |Δ^(a_l)| and |Δ^(a_s)| in $-notional, NOT
  willingness-to-pay). Out of scope for v1.1; placeholder so v1.1 does not drift further
  into demand-language.
---

# Pair D — Stage-2 Path B — On-Chain Data Empirical-Validation Spec

## Change Log v1.0 → v1.1

This revision integrates the 3 BLOCKs and 9 FLAGs surfaced by the 2-wave doc-write
verification (Wave-1 Reality Checker + Wave-2 Workflow Architect) on v1.0. v1.0
structure is preserved; new normative content is additive (new subsections §4.0, §3.A,
§5.A) plus targeted edits in §3, §5, §6 to resolve BLOCK-B3 and FLAG items 1-9.

**BLOCK resolutions:**

- **BLOCK-B1** (v0 output schema not concretely pinned) → resolved by new §4.0 "v0
  Output Schema (normative)" pinning canonical column lists, dtypes, primary keys,
  row-count expectations, file format, and naming convention for `audit_summary`,
  `address_inventory`, and `event_inventory` artifacts.
- **BLOCK-B2** (DATA_PROVENANCE.md mirror requirement missing) → resolved by new §3.A
  "Provenance Discipline (normative)" requiring per-artifact `DATA_PROVENANCE.md`
  alongside every committed dataset, mirroring the Stage-1 Pair D pattern; HALT-on-sha-
  mismatch behavior pinned.
- **BLOCK-B3** (Subsquid "free in compute" claim contradicts $49 budget pin) → resolved
  by §5 rewrite distinguishing **SQD Network** (decentralized data lake; FREE for
  archive extraction; supports Celo + Ethereum mainnet via documented public gateways)
  from **Subsquid Cloud** (hosted indexer-as-a-service; PAID above playground tier).
  Primary high-volume data path REPLACED: SQD Network public gateways become the
  primary archive surface; Alchemy Growth handles spot RPC + receipts; Dune handles
  ad-hoc SQL against pre-existing community tables. Subsquid Cloud is removed from the
  free-tier pivot ladder and listed only as paid escalation with explicit cost ceiling.
  Concrete query-volume projection pinned in new §5.A. Affected typed-exception
  pivots (§6) updated.

**FLAG resolutions** (tag each in §6 / §7 / §3 prose where pre-commit lives):

- **FLAG-B1** (`r_(a_l)` estimator method not pinned) → §3 +
  §6.v1.exception clauses: pre-commit **TWAP-weighted realized fee yield**:
  `r_(a_l) = (cumulative LP fee accrual in USD) / (cumulative |ΔP|-weighted
  swap-volume in USD)` over the v1 sample window, regressed via OLS with HAC SE.
  Gas-deducted variant is sensitivity, not primary. Position-weighted (per-LP-share)
  is out-of-scope (requires per-LP attribution; v1 stays pool-aggregate).
- **FLAG-B2** ({q_t} obligation extraction from a_s ambiguous) → §3 +
  §6.v2.exception clauses: pre-commit **bill-paid lifecycle event** as the q_t
  observation — specifically the on-chain settlement-leg `Transfer` of local-stable
  to the merchant address (not the user-side wallet debit, not the payment-completion
  off-chain confirmation). Funding-leg `Transfer` of USD-stable into the
  Bitgifty/Walapay router contract is a co-observation but does NOT constitute q_t
  alone (it is the input cost, not the obligation).
- **FLAG-B3** (time-binning resolution unspecified) → §3 + §4 bins normative:
  **daily aligned to UTC 00:00:00** as primary cadence; weekly aggregation
  (Mon-anchored) as standard derivation. Per-block resolution is rejected as
  introducing non-uniform temporal weighting that contaminates the
  `Σ |FX_t − FX_{t-1}|` shape check.
- **FLAG-B4** ((X/Y)_t reference price source unpinned) → §3 + §4 normative:
  primary **on-chain Mento V3 FPMM USDm/COPm pool spot price** sampled at the
  daily-bin close-tick; if pool absent (v0 HALT), fallback to **Uniswap V3 USDC/USDm
  Celo pool spot**; further fallback to **Banrep TRM daily series** (off-chain,
  same source as Pair D Stage-1 X). Source-of-record per observation is recorded in
  the per-row `price_source` column.
- **FLAG-B5** (CF reconciliation between v1 and v2 cadence) → §3 normative: CF
  reconciliation occurs at **monthly bin** (CF^(a_l)_t − CF^(a_s)_t for each calendar
  month overlap of v1 and v2 sample windows), with a cumulative-delta series as
  standard derivation. Per-period reconciliation is preferred over cumulative-only
  to surface regime-conditional asymmetries (RC FLAG #6 inheritance).
- **FLAG-B6** (v3 backtest harness — realized vs implied σ_T) → §3 + §6.v3 normative:
  **realized σ_T from Stage-1 Pair D 2015-2026 monthly COP/USD log-return-squared**
  is the primary input. Implied vol from Panoptic option markets is NOT used (no
  COP/USD option market exists at the relevant historical depth; using a proxy implied
  vol would inject a free-fitting parameter the framework does not authorize).
- **FLAG-B7** (address allowlist vs discovery) → §3 + new §4.0 normative: v0 operates
  on a **fixed allowlist** of contracts named in this spec's `on_chain_pins`
  frontmatter plus the Mento V3 deployment manifest. Discovery is OUT OF SCOPE for
  v0; if a candidate venue is missing from the allowlist, the executor surfaces a
  user-adjudicated typed-exception rather than auto-expanding the audit surface.
  This rule is anti-fishing-load-bearing (auto-discovery introduces selection bias
  on whatever surface produces nicer data).
- **FLAG-B8** (filter for non-economic transactions — MEV / arb / wash) → new §3
  paragraph + §6.v1 normative: pre-commit **two-layer partition rule** for swap
  events. Layer 1: drop swaps where `tx.from` is on a published MEV-bot allowlist
  (Eigenphi or equivalent free-tier list, snapshotted at v1 entry). Layer 2: drop
  swaps where the `(swap_in, swap_out)` round-trips inside a single transaction
  (atomic arb fingerprint). Wash-trading detection (across-tx repeated-counterparty
  cycles) is OUT OF SCOPE for v1 due to Celo's lower MEV depth vs Ethereum; flagged
  as v3 sensitivity. Echoes the Carbon V1/V2 user-vs-arb partition discipline pinned
  in memory `project_carbon_user_arb_partition_rule`.
- **FLAG-B9** (cross-path coupling with Path A) → §8 expansion: paths are **DEFAULT
  INDEPENDENT**. The single permitted Path A → Path B handoff is at v3: Path A
  produces the stochastic-σ Monte-Carlo `Π(σ_T)` price distribution; Path B replays
  realized σ paths through the same parametric `Π(σ_T) ≈ K̂·σ_T` form WITHOUT
  consuming Path A's `K̂` calibration (each path estimates `K̂` independently from
  its own data). Convergence dispatch (separate work item) compares the two
  envelopes. The single permitted Path B → Path A handoff is the empirical
  `r_(a_l)` from v1: Path A v3 may consume Path B v1's `r_(a_l)` point estimate +
  HAC SE as the calibration anchor for its stochastic-σ MC. Handoff schema:
  `r_al_handoff.json` with fields `{r_al_point, r_al_hac_se, sample_n, sample_window,
  source_pool_address, sha256_of_input_panel}`. Any other coupling (Path B
  consuming Path A's parametric assumptions, Path A consuming Path B's σ-path
  decomposition) is anti-fishing-banned.

**Anticipated future revision.** A `CORRECTIONS-γ` block (separate dispatch) will
rename Path B's deliverable framing from "behavioral demand" / "willingness-to-pay"
to **"structural exposure"** — i.e., cash-flow geometry yielding `|Δ^(a_l)|` and
`|Δ^(a_s)|` in $-notional. Transaction archaeology cannot infer WTP for an
instrument that does not yet exist in the market. v1.1 deliberately does NOT
introduce this rename to keep the v1.0 → v1.1 diff scoped to the verification
matrix; v1.1 prose is reviewed to ensure it does not drift further into
demand-language pending CORRECTIONS-γ.

## §1 — Goal + scope

Path B is the on-chain empirical-validation track for the Pair D Convex Payoff Option (CPO)
Stage-2 M-sketch dispatch brief at
`contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md`. Its goal is to confirm
— from realized on-chain history alone, with no simulation and no parameter free-fitting — that
the two real-world flows the dispatch brief identifies as the CPO's `a_l` (long-σ) supply side
and `a_s` (short-σ) demand side actually exhibit the cash-flow shapes the imported convex-payoff
framework predicts for them.

The Stage-1 anchor is the Pair D simple-β PASS verdict committed 2026-04-28 PM late evening, with
sha-pin chain quoted verbatim from the dispatch brief §3:

- Pair D spec v1.3.1: `964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659`
- Joint panel: `6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf`
- Primary OLS results: `d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf`
- Robustness pack: `67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904`
- VERDICT.md: `1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf`

These pins are READ-ONLY through Path B. Any spec edit that would invalidate them is OUT OF
SCOPE; this is a separate document, not a Stage-1 revision.

Path B's purpose is **revealed-preference evidence** of cash-flow geometry — what behavior is
*already* measurable in the existing on-chain history of the candidate venues, expressed as
realized `|Δ^(a_l)|` and `|Δ^(a_s)|` magnitudes in $-notional — rather than the analytical
claim that Path A constructs by stochastic / Monte-Carlo modeling of the same underlying CPO
mechanics. The two paths are independent (FLAG-B9) and converge at v3: Path B reconstructs the
realized `CF^(a_l)` and `CF^(a_s)` and replays them through the framework's `Π(σ_T)` to get a
realized CPO P&L envelope; Path A produces a stochastic-bound P&L distribution under the same
framework. The convergence dispatch (separate from this spec) checks whether Path A's bounds
contain Path B's realized envelope. Disagreement is informative; agreement upgrades the
M-sketch's empirical defensibility.

Path B is intentionally narrower than the dispatch brief itself. The dispatch brief authors a
*deployable* position-construction sketch on Panoptic; Path B does not. Path B audits whether the
flows the M-sketch presupposes are present and measurable on-chain. If they are not, the
M-sketch inherits an architectural risk that propagates into Stage-3.

**Framing reminder (CORRECTIONS-γ-anticipated, not yet applied).** The phrase "behavioral
demand" in v1.0 prose is a misnomer; transaction archaeology measures cash-flow geometry, not
willingness-to-pay for a non-existent instrument. v1.1 retains v1.0 wording to keep the diff
scoped, but executors implementing this spec MUST treat the deliverable as
*structural-exposure* characterization (the magnitudes |Δ^(a_l)| and |Δ^(a_s)| measurable
from realized history), NOT as behavioral-demand inference (what users *would* pay for a
hedge). CORRECTIONS-γ will reconcile prose.

## §2 — Internal ladder (v0 / v1 / v2 / v3)

Each version has a pre-pinned exit criterion and SAA disposition (Success → next version; Abort
→ typed exception → user-pivot disposition memo per
`feedback_pathological_halt_anti_fishing_checkpoint`; Abort-with-Pivot → user-enumerated
alternative; auto-pivot is anti-fishing-banned).

**v0 — Data-coverage audit.** Confirm Mento V3 FPMM USDm/COPm pool existence on Celo (the
dispatch brief §4 rank-1 candidate marks this as "to be confirmed"). Confirm Uniswap V3 / V4
deployment on Celo and existence of FX-pair pools (USDC/USDm, cUSD/cEUR). Confirm Panoptic
factory deployment on Ethereum mainnet and the existence of any FX-pair option market that
establishes the Panoptic-side architecture is reachable. For each confirmed venue: TVL snapshot,
cumulative swap volume, first-swap block, last-swap block, swap-event count. Bitgifty / Walapay
on-chain footprint audit: do these MiniPay applications surface settlement events on-chain at all?

v0 operates on the **fixed allowlist** of contract addresses listed in this spec's
`on_chain_pins` frontmatter plus the addresses enumerated in the Mento V3 deployment manifest
(per memory `project_no_mento_carbon_protocol_integration`). Discovery beyond the allowlist
requires user-adjudicated typed exception (FLAG-B7).

**Exit:** feasibility yes/no per data source, with sha-pinned snapshot of pool addresses,
cumulative metrics, and block-range bounds. Frontmatter `on_chain_pins` block frozen. v0 output
artifacts conform to §4.0 normative schema.

**v1 — Empirical `CF^(a_l)` reconstruction.** For each viable pool from v0, extract historical
swap events and reconstruct LP-side cash flow per the framework definition
`CF^(a_l)_T = Σ_t r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|`. The `r_(a_l)` parameter is **derived from
data** via the FLAG-B1-pinned **TWAP-weighted realized fee yield** estimator: cumulative LP fee
accrual in USD divided by cumulative |ΔP|-weighted swap-volume in USD over the v1 sample,
regressed via OLS with HAC SE. Gas-deducted is a sensitivity (one of the R1-R4 robustness
slots), not the primary. No curve-fitting; `r_(a_l)` comes out where it comes out.

The `(X/Y)_t` reference price (FLAG-B4) is the on-chain Mento V3 FPMM USDm/COPm pool spot
price sampled at the daily-bin close-tick (FLAG-B3); fallback ladder per FLAG-B4 above.

Non-economic transaction filtering follows the FLAG-B8 two-layer partition rule (MEV-bot
allowlist + atomic-arb round-trip detection); pre-filter applied before fee-yield estimation;
the dropped-row count and dropped-volume fraction are reported as audit metadata in
`audit_summary` per §4.0.

**Exit:** per-pool empirical `CF^(a_l)` realized series (daily-binned per FLAG-B3, normalized
to the Pair D 2015-2026 window), estimated `r_(a_l)` with HAC-corrected SE. Qualitative shape
check against the framework's `Σ r·|FX_t − FX_{t-1}|` shape; sign-and-magnitude pattern only,
no goodness-of-fit threshold (no honest threshold exists absent reference baselines).
`r_al_handoff.json` (FLAG-B9 schema) emitted for Path A v3 consumption.

**v2 — Empirical `CF^(a_s)` reconstruction.** Harder version of the ladder; most likely HALT
site. Bill-pay flows are partially abstracted: a Bitgifty / Walapay user pays USD-stable in
their wallet and the merchant receives local-stable somewhere downstream, possibly through an
off-chain corridor with no usable on-chain fingerprint. v2 attempts to extract the on-chain
settlement-leg events (FLAG-B2: the merchant-side local-stable `Transfer`, not the user-side
funding `Transfer`) for the top a_s candidates from the dispatch brief §5 and estimate
fixed-obligation turnover plus realized FX-path cost: specifically the `Σ q_t / (X/Y)_t` term
from the framework's a_s cash-flow definition.

CF^(a_l) − CF^(a_s) reconciliation cadence is **monthly** (FLAG-B5), with cumulative-delta
series as standard derivation; per-month surfacing is required to expose regime-conditional
asymmetry (RC FLAG #6 inheritance).

**Exit:** at minimum, directional evidence of `Δ^(a_s) < 0` shape against realized σ in the same
sample window. If the on-chain fingerprint is too abstracted to reconstruct, v2 HALTs and surfaces
the typed exception in §6. The HALT is expected with non-trivial probability and does not
invalidate Path B; the framework's `Δ^(a_l) > 0` evidence from v1 is sufficient for CPO
supply-side fitness. The dispatch brief §6.8 already flags equilibrium pricing `K_l = K_s` as
the most architecturally consequential Stage-2 decision; v2's success or HALT propagates
directly into that decision.

**v3 — Backtest CPO P&L.** Replay the Pair D 2015-2026 window of realized COP/USD σ-paths
through a theoretical `Π(σ_T)` replication using the empirical `r_(a_l)` from v1 and (if
available) empirical `B_T` calibration from v2. The σ_T input is **realized monthly
log-return-squared from Stage-1 Pair D's COP/USD series** (FLAG-B6); implied vol is rejected
as primary because no historical COP/USD option-market depth exists, making implied a
free-fitting parameter not authorized by the framework. Compute realized CPO P&L for both
legs across the sample.

**Exit:** realized P&L envelope characterized by mean, SD, full quantile vector, max drawdown,
plus a regime-conditional decomposition keyed to the four regimes RC FLAG #6 identified as
over-represented in the 2015-2026 window. Calibration-handoff packet to Path A v3 ready
(includes `r_al_handoff.json` already emitted at v1 Exit + the v3 envelope JSON).

## §3 — Inputs (sha-pinned + on-chain)

**Stage-1 sha pins (READ-ONLY).** Quoted verbatim in §1 above. The dispatch brief itself at
`contracts/.scratch/2026-04-30-stage-2-m-sketch-dispatch-brief-pair-d.md` is the master input
that prioritizes which candidate flows Path B audits first.

**On-chain pre-pins.**

- Mento V3 router (Celo): `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`
- Mento V2 StableTokenCOP (canonical Mento-native COPm per memory
  `project_mento_canonical_naming_2026` β-corrigendum):
  `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`
- Mento V2 StableTokenUSD (USDm equivalent), Uniswap V3 factory on Celo, Uniswap V4 PoolManager
  on Celo (if deployed), Panoptic factory on Ethereum mainnet, and Bitgifty / Walapay
  on-chain settlement contracts: pinned at v0 audit completion. Fixed-allowlist discipline
  per FLAG-B7.

**Block-range bounds.** Mento V3 deployment block is the lower bound for the USDm/COPm pool
sample; the Pair D 2015-01-31 → 2026-02-28 window is the analytical reference. Pre-Mento-V3
history is reachable only through Mento V2 BiPool or earlier constructions; whether usable for
the same `CF^(a_l)` calculation is a v0 audit question. The Pair D window is the *outer*
envelope; if the Mento-V3 deployment block trims it, that fact is recorded and does not
constitute anti-fishing window-curation, because the trim is forced by data availability not
chosen post-data to improve a result (per §7).

**Time-binning (FLAG-B3, normative).** Daily bins aligned to UTC 00:00:00 are primary. Weekly
aggregation (Mon-anchored) is a standard derivation. Per-block resolution is rejected — it
introduces non-uniform temporal weighting that contaminates the `Σ |FX_t − FX_{t-1}|` shape
check.

**(X/Y)_t reference price (FLAG-B4, normative).** Primary: on-chain Mento V3 FPMM USDm/COPm
pool spot price at daily-bin close-tick. Fallback-1 if v0 confirms pool absent: Uniswap V3
USDC/USDm Celo pool spot at daily-bin close-tick. Fallback-2 if both unusable: Banrep TRM
daily series (off-chain; same source as Pair D Stage-1 X). Per-row `price_source` column
records source-of-record per observation; downstream consumers must respect the partition.

**`r_(a_l)` estimator (FLAG-B1, normative).** TWAP-weighted realized fee yield. Estimator
form: numerator = cumulative LP-fee accrual denominated in USD over the v1 sample; denominator
= cumulative |ΔP|-weighted swap-volume denominated in USD over the same sample; regression
form OLS with HAC SE on the fee-accrual-on-|ΔP|-volume specification. Gas-deducted variant is
slot R3 of the v1 robustness pack. Position-weighted (per-LP attribution) is OUT OF SCOPE for
v1 — Path B stays pool-aggregate.

**`q_t` extraction from a_s (FLAG-B2, normative).** Bill-paid lifecycle event. The on-chain
settlement-leg `Transfer` of local-stable to the merchant address is the q_t observation. The
funding-leg `Transfer` of USD-stable into the Bitgifty / Walapay router is a co-observation
recorded as the per-q_t input cost but does NOT alone constitute q_t. Off-chain
payment-completion confirmations (webhook responses, bill provider acknowledgements) are NOT
authorized inputs for v2.

**v1 ↔ v2 reconciliation cadence (FLAG-B5, normative).** Monthly bins. Per-month CF^(a_l)_t
− CF^(a_s)_t reconciliation is primary; cumulative-delta series is standard derivation.
Per-month surfacing is required to expose regime-conditional asymmetry (RC FLAG #6).

**Non-economic transaction partition (FLAG-B8, normative).** Two-layer rule applied to swap
events before fee-yield estimation. Layer-1: drop swaps where `tx.from` is on the Eigenphi (or
equivalent free-tier) MEV-bot allowlist snapshotted at v1 entry. Layer-2: drop swaps where
the same wallet executes paired swap-in / swap-out within a single transaction (atomic-arb
fingerprint). Wash-trading (cross-tx repeated-counterparty cycles) is NOT detected at v1
(Celo MEV depth is materially lower than Ethereum; cost of wash detection exceeds expected
contamination); flagged as v3 sensitivity. Echoes the Carbon V1/V2 user-vs-arb partition
discipline pinned in memory `project_carbon_user_arb_partition_rule`. Dropped-row count and
dropped-volume fraction reported in `audit_summary` per §4.0.

**Data-source candidates (revised per BLOCK-B3).** Free-tier and committed-budget on-chain
data sources only. Committed budget: `$49/mo Alchemy Growth` (49M CU / day; user pin
2026-04-30). The full revised tooling stack is in §5 below. The salient v1.0 → v1.1
substitution: **SQD Network public gateways** (FREE for archive extraction; documented Celo
+ Ethereum mainnet support) replace **Subsquid Cloud** (paid hosted indexer-as-a-service)
as the primary high-volume archive surface. The 2500-credit Dune ceiling is no longer
load-bearing for bulk extraction (it remains load-bearing for ad-hoc analytical SQL against
pre-existing community tables); SQD Network absorbs the bulk-extraction load.

## §3.A — Provenance Discipline (normative; resolves BLOCK-B2)

Path B inherits the per-artifact `DATA_PROVENANCE.md` discipline from Stage-1 Pair D. Every
committed dataset (v0 audit artifact, v1 panel, v2 panel, v3 backtest output) MUST be
accompanied by a `DATA_PROVENANCE.md` file in the same directory recording, for each input:

- **source**: data origin URL or contract address + chain (e.g.,
  `sqd_network_gateway://celo-mainnet/contract=0x8A56...41eA/topic0=Transfer`,
  `dune.com/queries/<id>`, `alchemy://eth_getLogs/<block-range>`)
- **fetch_method**: tool + parameters (e.g.,
  `sqd-archive-cli v0.X.Y --network celo-mainnet --block-range 12345-67890`,
  `python sql_alchemy/dune_client.py --query-id 12345`)
- **fetch_timestamp**: ISO-8601 UTC of the fetch
- **sha256**: of the raw fetched payload (pre-transformation) AND of the committed parquet
- **row_count**: post-fetch row count
- **block_range**: `(first_block, last_block)` of the on-chain query window
- **schema_version**: hash of the column-set + dtypes (per §4.0 schema)
- **filter_applied**: descriptive string of any partition rules (e.g.,
  `FLAG-B8-layer-1+layer-2 applied; dropped 412 rows / 0.8% volume`)

**HALT-on-mismatch.** Re-execution of the same fetch must produce a sha256 within ±0.01% row
count and identical schema_version (the row tolerance accommodates new on-chain blocks since
the previous fetch; a non-trivial schema_version drift, a >0.01% row delta inside a frozen
block range, or a sha256 change that cannot be reconciled to known new-block additions
triggers `Stage2PathBProvenanceMismatch` typed exception per §6).

The `DATA_PROVENANCE.md` file format mirrors the Stage-1 Pair D pattern at
`contracts/.scratch/simple-beta-pair-d/data/DATA_PROVENANCE.md`. Field-by-field schema
parity is required; new fields specific to on-chain extraction (`block_range`,
`filter_applied`) are added on top, never instead of, the Stage-1 fields.

## §4 — Outputs

**v0:** data-coverage audit report conforming to §4.0 normative schema (three artifacts:
`audit_summary.parquet`, `address_inventory.parquet`, `event_inventory.parquet`) plus
co-located `DATA_PROVENANCE.md` per §3.A. Frontmatter `on_chain_pins` update freezing audited
addresses. Findings memo (1-2 pp) recommending which candidates graduate to v1 with
data-availability reasons (not result-shaping reasons).

**v1:** per-pool empirical `CF^(a_l)` time series (daily-binned per FLAG-B3, normalized to
the Pair D 2015-2026 window), estimated `r_(a_l)` with HAC SE, qualitative shape-check chart
against `Σ r·|FX_t − FX_{t-1}|`, `r_al_handoff.json` per FLAG-B9 schema, plus co-located
`DATA_PROVENANCE.md` per §3.A. Findings memo recommending whether v2 proceeds or v1 alone
provides sufficient empirical defensibility for the M-sketch supply-side leg.

**v2:** if `CF^(a_s)` reconstruction succeeds — empirical
demand-side / structural-exposure cash-flow series, estimated effective `B_T` calibration,
realized Δ-shape against σ, plus `DATA_PROVENANCE.md`. If HALT — typed-exception HALT memo
per `feedback_pathological_halt_anti_fishing_checkpoint` documenting which fingerprint was
sought, why unreachable, and ≥3 user-enumerated pivots.

**v3:** realized CPO P&L distribution over feasible block-range overlap with the Pair D window
(mean, SD, quantiles, max drawdown, regime-conditional decomposition keyed to RC FLAG #6
regimes); calibration-handoff packet to Path A v3 (empirical `r_(a_l)` carried forward from
v1's `r_al_handoff.json`, `B_T` or v2 HALT artifact, realized envelope) as JSON plus tabular
CSV; findings memo characterizing the envelope and flagging convergence questions.

## §4.0 — v0 Output Schema (normative; resolves BLOCK-B1)

Three artifacts emitted by v0 in `parquet` format (per Pair D notebook convention) at
`contracts/.scratch/pair-d-stage-2-B/v0/`. Naming is fixed; column order is fixed; dtypes are
fixed.

**Artifact 1: `audit_summary.parquet`** — one row per audited venue.

| column | dtype | nullable | description |
|---|---|---|---|
| `venue_id` | string | NO | stable slug, e.g., `mento_v3_fpmm_usdm_copm_celo` |
| `venue_name` | string | NO | human-readable, e.g., `Mento V3 FPMM USDm/COPm` |
| `network` | string | NO | one of `celo-mainnet`, `ethereum-mainnet` |
| `contract_address` | string | NO | 0x-prefixed checksummed address |
| `venue_kind` | string | NO | one of `mento_fpmm`, `uniswap_v3_pool`, `uniswap_v4_pool`, `panoptic_factory`, `bill_pay_router`, `remittance_router` |
| `deployment_block` | int64 | NO | block number of contract deployment |
| `first_event_block` | int64 | YES | block of first relevant event; null if no events |
| `last_event_block` | int64 | YES | block of last relevant event in audit window; null if no events |
| `event_count` | int64 | NO | count of relevant events in audit window (0 allowed; triggers HALT review per §6) |
| `cumulative_volume_usd` | float64 | YES | sum of swap-volume USD-equivalent if applicable; null for non-pool venues |
| `tvl_usd_snapshot` | float64 | YES | TVL at snapshot timestamp; null where N/A |
| `snapshot_timestamp_utc` | timestamp[ns,UTC] | NO | ISO-8601 UTC of the audit snapshot |
| `audit_block` | int64 | NO | block number used as the audit's "now" |
| `data_source_primary` | string | NO | one of `sqd_network`, `alchemy_growth`, `dune`, `the_graph`, `celoscan`, `etherscan` |
| `feasibility_v1` | string | NO | one of `pass`, `marginal`, `halt` |
| `feasibility_notes` | string | YES | freeform; required if `feasibility_v1` is `marginal` or `halt` |

Primary key: `(venue_id)`. Uniqueness constraint: `venue_id` unique within file.
Row-count expectation: 6-12 rows (the named pre-pins + Mento V3 manifest entries); <4 or >20
triggers HALT-review per §6 (`Stage2PathBAuditScopeAnomaly`).

**Artifact 2: `address_inventory.parquet`** — one row per unique on-chain address discovered
within the audit allowlist. Distinct from `audit_summary` because a venue can involve multiple
addresses (router, factory, pool implementation, fee collector).

| column | dtype | nullable | description |
|---|---|---|---|
| `address` | string | NO | 0x-prefixed checksummed |
| `network` | string | NO | one of `celo-mainnet`, `ethereum-mainnet` |
| `venue_id` | string | NO | foreign key to `audit_summary.venue_id` |
| `address_role` | string | NO | one of `router`, `factory`, `pool`, `token`, `fee_collector`, `merchant`, `user_eoa`, `mev_bot`, `other` |
| `is_contract` | bool | NO | true if `eth_getCode` returns nonempty |
| `first_seen_block` | int64 | NO | block of first inbound or outbound transaction |
| `last_seen_block` | int64 | NO | block of last inbound or outbound transaction in audit window |
| `tx_count_window` | int64 | NO | total transactions in audit window |

Primary key: `(network, address)`. Foreign key: `(venue_id)` references
`audit_summary.venue_id`. Row-count expectation: 10-200 rows; <5 triggers HALT review.

**Artifact 3: `event_inventory.parquet`** — one row per (venue, event_topic) pair recording
event-frequency in audit window.

| column | dtype | nullable | description |
|---|---|---|---|
| `venue_id` | string | NO | foreign key to `audit_summary.venue_id` |
| `event_signature` | string | NO | canonical event signature, e.g., `Swap(address,uint256,uint256,uint256,uint256,address)` |
| `topic0` | string | NO | keccak256 of event signature, 0x-prefixed |
| `event_count` | int64 | NO | count of emissions in audit window |
| `first_emit_block` | int64 | YES | null if `event_count == 0` |
| `last_emit_block` | int64 | YES | null if `event_count == 0` |
| `relevance_v1` | string | NO | one of `cf_al_input`, `cf_as_input`, `oracle_input`, `metadata`, `unused` |

Primary key: `(venue_id, topic0)`. Row-count expectation: 2-8 rows per venue.

**File format.** Apache Parquet with Snappy compression (project convention from Pair D
notebooks). Schema metadata MUST include `schema_version` field hashing the column-set +
dtypes; consumers MUST verify match before reading.

**Naming.** Exact filenames `audit_summary.parquet`, `address_inventory.parquet`,
`event_inventory.parquet` in `contracts/.scratch/pair-d-stage-2-B/v0/`.

## §5 — Tooling stack + budget assumption (revised per BLOCK-B3)

The committed Path B tooling budget is `$49/mo Alchemy Growth` (user pin 2026-04-30) plus
free-tier everything else. v1.0 listed Subsquid as "free in compute" — **this conflated
Subsquid Cloud (paid hosted indexer) with SQD Network (free decentralized data lake)**. v1.1
disambiguates and re-orders the data-path priority.

**Primary high-volume archive surface: SQD Network public gateways (FREE).**

- SQD Network is the decentralized data lake at the foundation of the Subsquid ecosystem.
  Public gateways are documented at https://docs.sqd.ai/subsquid-network/reference/networks/.
- Celo mainnet gateway: `https://v2.archive.subsquid.io/network/celo-mainnet`
- Ethereum mainnet gateway: `https://v2.archive.subsquid.io/network/ethereum-mainnet`
- Cost model per official documentation: "freely accessible to public using the same API"; no
  documented rate limits as of 2026-05-02 (one "rate limited" reference page exists in the
  docs, suggesting limits exist but are not published as concrete quotas; budget-aware
  degradation in §5.A handles unanticipated throttling)
- Use case in Path B: bulk extraction of swap events, transfer events, pool-deployment
  events for v0 + v1 + v2. Replaces the v1.0 "Subsquid as escalation pivot" framing.

**Spot RPC + receipts: Alchemy Growth ($49/mo committed).**

- 49M CU / day on the Growth tier; sufficient for spot-check verification, transaction-receipt
  fetching where event extraction needs `tx.from` for FLAG-B8 layer-1 partitioning, and
  `eth_call` for current-state snapshots (TVL, pool prices) in v0.
- Celo network support: confirmed available on Alchemy as of 2026-05-02 (per Alchemy public
  documentation; v0 audit re-verifies at session start).
- Use case in Path B: audit-time TVL snapshots, transaction-level enrichment for partition
  rules, fallback when SQD Network throttles.

**Ad-hoc analytical SQL: Dune Analytics free tier (2500 SQL credits / month).**

- Pre-existing community tables on Dune (e.g., `mento.swaps`, `uniswap_v3_celo.swaps`,
  `panoptic_ethereum.events` if available) provide ad-hoc analytical surfaces useful for
  spot-checks and findings-memo charts.
- The 2500-credit ceiling is **NO LONGER load-bearing for bulk extraction** in v1.1 (SQD
  Network absorbs that load). It remains load-bearing for ad-hoc SQL: a careless query
  scanning multiple months of swap data can consume 50-200 credits. Pre-flight cost estimation
  required before each Dune query (Dune surfaces estimated cost at query-edit time).
- Pivot if exhausted: switch to Flipside Crypto free SQL credits, or write the same query
  against SQD Network primitives.

**Subgraphs: The Graph hosted service (free for pre-existing subgraphs).**

- Mento V3, Uniswap V3 Celo, and Panoptic Ethereum all have community subgraphs as of 2026-04.
  v0 confirms subgraph existence per venue; preferred over raw `eth_getLogs` where coverage
  exists AND where SQD Network does not give cleaner schema.
- Use case in Path B: ergonomic typed-event access for findings-memo prep when SQD Network
  raw-log extraction is heavier than needed.

**Block explorer: Celoscan + Etherscan free-tier API (5 req/s).**

- Ad-hoc verification, source-code lookup, transaction decoding for human-readable audit
  notes only. NEVER for bulk extraction.

**Notebook stack: Jupyter + pandas + statsmodels + sympy (free).**

- Inherited from the Pair D notebook environment at
  `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/`. Path B notebooks live at
  `contracts/notebooks/pair_d_stage_2_path_b/` (subdirectory pinned at v0 entry).

**Paid escalation only — NOT authorized under v1.1 spec without explicit user re-budgeting:**

- Subsquid Cloud (hosted indexer-as-a-service) — pay-as-you-go above free playground tier.
  Cost ceiling if user re-authorizes: $X TBD per executor-side estimation; placeholder for
  future CORRECTIONS-block.
- Dune Analyst tier ($89/mo) — credit ceiling lifted; not auto-authorized.
- Alchemy tier above Growth — not authorized; if Growth CU cap is hit, the v1.1 fallback is
  to lean harder on SQD Network rather than upgrade Alchemy.

Frontmatter records `tooling_budget_pending: false; tooling_budget_committed: $49/mo Alchemy
Growth (2026-04-30 user pin); primary_data_path_v1_1: SQD Network public gateway`.

## §5.A — Query-volume projection + budget reconciliation (normative; resolves BLOCK-B3)

Concrete projection of Path B query volume per data source, used to verify the v1.1
free-tier-primary architecture is feasible inside the $49/mo budget pin.

**v0 audit volume projection.**

- `address_inventory` discovery within allowlist: ~10 contracts × 1 RPC call each (`eth_getCode`
  + first/last block scan) ≈ 30-50 Alchemy CU per contract = ~500 CU total. Negligible vs
  49M/day Growth cap.
- `event_inventory` topic-frequency scan: ~10 contracts × 5 topics × 1 SQD Network archive
  query each = 50 SQD queries; FREE.
- `audit_summary` aggregation: ~10 venues × cumulative-volume + TVL = 20-30 Alchemy `eth_call`s
  ≈ 1000 CU. Negligible.
- v0 total: <5000 Alchemy CU (single-day, well inside cap); <100 SQD queries (FREE); 0-5 Dune
  credits (only if a community-table-backed sanity-check query is convenient).

**v1 CF^(a_l) extraction volume projection.**

- Mento V3 USDm/COPm pool swap events over Mento-V3-deployment to 2026-02-28 window: estimate
  100K-500K swaps depending on pool age + activity. SQD Network archive query = ONE bulk
  extraction returning all events; FREE; documented data lake throughput is order-of-minutes
  for sub-million event extractions.
- Uniswap V3 USDC/USDm Celo pool swap events: similar order of magnitude. Same SQD Network
  surface; FREE.
- Per-event LP-fee accrual computation requires either: (a) on-chain `Mint`/`Burn` events
  (also extractable via SQD Network in the same bulk pull; FREE), OR (b) per-block reserve
  snapshots (more expensive but not needed if approach (a) is sufficient).
- FLAG-B8 layer-1 partition (MEV-bot allowlist) requires `tx.from` enrichment for each swap
  — already included in SQD Network swap event payload; FREE.
- FLAG-B8 layer-2 partition (atomic-arb round-trip) requires per-tx event grouping —
  computed locally from the SQD Network bulk extract; FREE.
- v1 total: 2-3 SQD Network bulk extractions per pool × 1-3 pools = ~5-9 free queries;
  <50K Alchemy CU for any spot-check enrichment; ~20-50 Dune credits for findings-memo charts.

**v2 CF^(a_s) extraction volume projection (conditional on v0 confirming Bitgifty / Walapay
on-chain footprint).**

- Bitgifty / Walapay router + merchant-side `Transfer` events: estimate 10K-100K events over
  Mento V3 deployment window. SQD Network bulk extraction; FREE.
- Per-merchant aggregation + obligation-leg attribution: local computation; FREE.
- v2 total: 3-5 SQD Network queries; <20K Alchemy CU.

**v3 backtest computational load.**

- Pure local computation (Python + statsmodels + numpy) over v1 + v2 extracted panels.
  Zero on-chain queries; zero Alchemy CU; zero Dune credits.

**Aggregate monthly usage estimate.**

- SQD Network: ~10-15 queries total across v0 + v1 + v2; FREE; throttling risk LOW per
  documented "no rate limits" stance, mitigated by §6's `Stage2PathBSqdNetworkThrottled`
  typed exception.
- Alchemy Growth: <100K CU total across v0 + v1 + v2; ~0.2% of monthly cap; well inside
  $49 commit.
- Dune: <100 credits total; ~4% of monthly free quota; ample headroom for unanticipated
  ad-hoc queries.
- The Graph: opportunistic free queries; bounded by community-subgraph availability.
- Celoscan + Etherscan: ad-hoc only; bounded by 5 req/s.

**Conclusion.** The v1.1 architecture (SQD Network primary archive + Alchemy Growth spot RPC
+ Dune ad-hoc SQL) fits comfortably inside the $49/mo budget pin with substantial headroom
for re-runs, sensitivity passes, and CORRECTIONS-block iterations. BLOCK-B3 is resolved:
no paid Subsquid Cloud usage is required for the v0 → v3 ladder.

**Budget-aware degradation path.** If SQD Network throttles or has a coverage gap:
Step 1: switch to The Graph hosted-service subgraph for the affected venue (FREE if subgraph
exists). Step 2: switch to Alchemy `eth_getLogs` for the affected block range (paid CU but
inside budget). Step 3: switch to Dune SQL against the relevant community table (paid
credits, watch ceiling). Step 4 (only if Steps 1-3 jointly insufficient): typed-exception
HALT requesting user re-budgeting for paid Subsquid Cloud. Auto-pivot up the ladder is
permitted (this is a tooling fallback, not a result-shaping decision); auto-pivot to Step 4
is anti-fishing-banned and requires explicit user adjudication.

## §6 — HALT discipline

Path B inherits the Phase-A.0 HALT-disposition discipline from
`feedback_pathological_halt_anti_fishing_checkpoint`: every typed-exception HALT surfaces a
disposition memo to the orchestrator with ≥3 user-enumerated pivots; auto-pivot is
anti-fishing-banned; CORRECTIONS-block discipline applies on the chosen pivot.

Pre-pinned typed exceptions:

- **v0 — `Stage2PathBMentoUSDmCOPmPoolDoesNotExist`.** Triggers if v0 confirms Mento V3 FPMM has
  no USDm/COPm pool, or pool exists with fewer than 100 swap events (pre-pinned floor). Pivots:
  (a) check Mento V2 BiPool USDm/COPm legacy pool and treat as supply-side reference; (b) accept
  cUSD/cEUR or USDC/USDm as σ-pattern proxy with explicit CORRECTIONS-block; (c) reframe Path B
  around USDm/EURm or GBPm/USDm pools that DO exist and document that the Pair-D-specific
  COP/USD anchor cannot be reproduced on-chain at the supply side.

- **v0 — `Stage2PathBAuditScopeAnomaly`.** Triggers if §4.0 row-count expectations
  fail (audit_summary <4 or >20 rows; address_inventory <5 rows). Pivots: (a) re-run with
  expanded allowlist (requires user-adjudicated FLAG-B7 exception); (b) document scope as
  unexpectedly narrow / broad and proceed with explicit notes; (c) split the audit into
  per-network sub-audits and re-evaluate row counts per network.

- **v0 — `Stage2PathBSqdNetworkCoverageInsufficient`.** Triggers if SQD Network gateway returns
  zero or fewer-than-100 events for a venue that on-chain explorers confirm has activity (i.e.,
  archive-side coverage gap). Pivots: (a) The Graph community subgraph for the affected venue;
  (b) Alchemy `eth_getLogs` for the affected block range against the $49 budget; (c) Dune SQL
  against the relevant community table.

- **v0 — `Stage2PathBSqdNetworkThrottled`.** Triggers if SQD Network gateway returns
  documented or undocumented rate-limit responses on a query that should be inside its free
  bounds. Pivots: (a) reduce query window and chunk; (b) switch to The Graph hosted-service
  subgraph; (c) switch to Alchemy `eth_getLogs` (CU cost); (d) escalation to paid Subsquid
  Cloud requires user re-budgeting per §5.A degradation Step 4.

- **v0/v1/v2/v3 — `Stage2PathBProvenanceMismatch`.** Triggers if §3.A re-execution discipline
  surfaces a sha256 / row-count / schema_version delta that cannot be reconciled to known
  new-block additions. Pivots: (a) investigate whether SQD Network re-indexed the
  affected block range (legitimate cause; document and proceed); (b) investigate whether a
  partition rule (FLAG-B8) was inadvertently changed; (c) full re-extraction with a fresh
  fetch_timestamp and side-by-side diff.

- **v1 — `Stage2PathBALCashFlowContaminated`.** Triggers if observed LP-fee accrual is materially
  mixed with non-σ-driven incentive emissions (Mento liquidity mining, Uniswap UNI emissions,
  third-party rewards) such that `r_(a_l)` cannot be cleanly attributed to σ-tracking turnover.
  Pivots: (a) net out incentive emissions by parsing reward distributions per LP and report
  `r_(a_l)` as a fee-only residual; (b) drop the contaminated pool and elevate the rank-2
  candidate from dispatch brief §4; (c) report `r_(a_l)` as a confidence interval rather than a
  point estimate and pass wider uncertainty into v3.

- **v2 — `Stage2PathBASOnChainSignalAbsent`.** Triggers if Bitgifty / Walapay / equivalent
  candidates settle bill-pay flows off-chain such that the on-chain signal contains only the
  funding leg without the obligation leg (FLAG-B2 q_t observation absent). **Most likely v2
  HALT.** Pre-pinned disposition: **PROCEED-without-v2-`CF^(a_s)`** is acceptable. Path B
  graduates to v3 with v1 alone as the empirical anchor; the framework's `Δ^(a_s) < 0` shape
  can be argued symmetrically from `Δ^(a_l) > 0` plus the framework derivation. The findings
  memo records the asymmetry explicitly and flags it for Path A v3 convergence dispatch as a
  known empirical asymmetry. v3 reports the supply-side P&L envelope only and explicitly flags
  the demand-side as un-replicated. Pivots (if orchestrator declines PROCEED-without): (a)
  source off-chain Bitgifty / Walapay aggregate volume statistics from publicly available
  reports as upper-bound proxy (NOTE: this is structural-exposure proxy not WTP per
  CORRECTIONS-γ-anticipation); (b) substitute Walapay's published Africa-side cross-currency
  reels as a geography substitute; (c) drop v2 and explicitly scope Path B to supply-side
  empirical validation only.

Each HALT requires a typed-exception memo, a disposition memo with ≥3 user-enumerated pivots,
and explicit user adjudication before any pivot is taken. The v1.0 `Stage2PathBDuneCoverageInsufficient`
and `Stage2PathBDuneCreditCapHit` typed exceptions from v1.0 §6 are RETIRED in v1.1 (Dune is
no longer the primary high-volume surface; SQD-Network-side exceptions above replace them);
Dune-credit exhaustion at the residual ad-hoc-SQL volume is handled inside the §5.A
degradation path without a typed exception.

## §7 — Anti-fishing posture

Path B inherits the full Pair D Phase-3 anti-fishing posture and adds Path-B-specific invariants:

- **Pool selection follows the dispatch brief candidate ranking.** §4 + §5 of the dispatch
  brief rank candidate venues by Δ-fit × deployment-readiness; v0 audits them in that order. A
  post-data swap to a venue with nicer data is anti-fishing-banned. If rank-1 HALTs at v0,
  substitution is a typed-exception event with user adjudication, not a silent pivot.
- **Allowlist-only audit (FLAG-B7).** v0 operates on a fixed allowlist; auto-discovery is
  banned. If a candidate venue is missing from the allowlist, the executor surfaces a
  user-adjudicated typed exception rather than auto-expanding the audit surface.
- **σ-period matches Pair D's 2015-01-31 → 2026-02-28 window.** Restricting to a "cleaner"
  sub-period to improve qualitative shape match is anti-fishing-banned. If on-chain block-range
  cannot cover the full window (Mento V3 was deployed after 2015), the Path B sample is the
  maximum feasible overlap, and the gap is recorded explicitly. Window-trim forced by data is
  acceptable; window-curation chosen to improve a result is not.
- **`r_(a_l)` is computed via the FLAG-B1-pinned TWAP-weighted realized-fee-yield estimator,
  as-is from realized fee data.** No curve-fitting to frame the result. Estimated parameter is
  reported with HAC SE and propagated into v3 unchanged. Substituting an alternative estimator
  post-data (gas-deducted, position-weighted) requires CORRECTIONS-block discipline.
- **Time-binning (FLAG-B3) is daily-UTC primary; switching to a different cadence post-data
  to improve qualitative shape match is anti-fishing-banned.** Weekly aggregation as
  derivation is acceptable.
- **Reference price (FLAG-B4) follows the pinned ladder (Mento V3 → Uniswap V3 → Banrep TRM);
  swapping mid-analysis to whichever source produces nicer data is anti-fishing-banned.**
  Per-row `price_source` records the partition.
- **Non-economic transaction filter (FLAG-B8) is applied uniformly across the v1 sample;
  per-period adjustment of the partition rule to retain or exclude swaps is
  anti-fishing-banned.**
- **CF reconciliation cadence (FLAG-B5) is monthly, fixed at v1 entry; switching to per-week
  or quarterly post-data to improve agreement is anti-fishing-banned.**
- **v3 σ_T input (FLAG-B6) is realized monthly log-return-squared from Stage-1's COP/USD;
  substituting implied vol or a different realization window post-data is
  anti-fishing-banned.**
- **No causal-channel claims (RC FLAG #1 inheritance).** Path B language uses "FX-vol-driven
  services-share movement" and "supply-side σ-tracking LP yield." It does not claim that
  Bitgifty bill-pay reflects the BPO offshoring channel, nor that the empirical CPO architecture
  identifies the BPO mechanism. The CPO hedges the *correlation* established by Pair D Stage-1;
  it does not identify the *channel*.
- **No empirical β re-litigation.** Pair D Stage-1 PASS is the load-bearing input. Path B does
  not re-estimate β, re-run robustness, or propose a refined Y or X. Stage-1 sha pins are
  immutable through Path B.
- **No Stage-3 deployment claims.** Path B characterizes realized history; it does not
  recommend deployment, propose LP capital sourcing, scope onboarding, or describe regulatory
  framing. All deployment-adjacent reasoning is Stage-3 and out of scope.
- **RC FLAG #3 inheritance — lag-6 dominance honored in v3 backtest.** The v3 P&L envelope is
  computed under the Pair D-pinned 6-month-dominant lag pattern, not a uniform 6-12mo lag. If
  the backtest naturally surfaces a different best-fit lag-distribution, that is reported as an
  *observation* not as a re-specification of the empirical anchor.
- **RC FLAG #5 inheritance — verdict-sensitive to brief-vs-spec.** Path B treats the dispatch
  brief and this spec as the joint source of truth; if a v0-v3 finding contradicts one but not
  the other, the typed-exception HALT pathway is engaged before any disposition.
- **RC FLAG #6 inheritance — regime mix flagged.** The v3 envelope decomposition explicitly
  partitions realized P&L across the four regimes (post-2014 oil shock, COVID, Fed tightening,
  normalcy) and flags regime over-representation for downstream Stage-3 calibration cadence.
- **No post-data threshold tuning.** The 100-event v0 floor, the §4.0 row-count expectations,
  the SQD-Network-primary tooling architecture, and the v0-v3 SAA dispositions are pre-pinned
  at authoring time and do not move post-data. Free-tuning a threshold to avoid a HALT is
  exactly the failure mode `feedback_pathological_halt_anti_fishing_checkpoint` exists to
  prevent.
- **No silent path-coupling with Path A (FLAG-B9).** The two permitted handoffs are
  enumerated in the §1 Change Log; any additional coupling requires explicit spec amendment.

## §8 — Convergence with Path A

Paths A and B are **DEFAULT INDEPENDENT** (FLAG-B9). The single permitted Path B → Path A
handoff is the empirical `r_(a_l)` from v1, emitted as `r_al_handoff.json` with schema
`{r_al_point, r_al_hac_se, sample_n, sample_window, source_pool_address,
sha256_of_input_panel}`. Path A v3 may consume this packet as the calibration anchor for its
stochastic-σ Monte-Carlo. The single permitted Path A → Path B handoff is at v3-convergence
time only: Path A's MC envelope JSON is read for comparison against Path B's realized
envelope. Path B does NOT consume Path A's parametric assumptions, σ-path decomposition, or
position-geometry choices at any earlier stage.

Path A produces a stochastic / Monte-Carlo P&L distribution under the same CPO mechanics that
Path B characterizes empirically. The convergence point is at v3: Path B's realized P&L envelope
should fall *inside* Path A's Monte-Carlo bounds if the framework's analytical assumptions hold
in realized history. Disagreement is informative — it indicates either a Path-A modeling
assumption that does not match realized behavior, or a Path-B data-construction artifact that
distorts the realized envelope.

The convergence dispatch is a separate work item, not within Path B's scope. Path B v3 closes
when the realized envelope is characterized and the calibration-handoff packet is produced. The
orchestrator dispatches the convergence comparison after both Path A v3 and Path B v3 deliver
their respective handoff packets.

If Path B v2 HALTs with the PROCEED-without-`CF^(a_s)` disposition, v3 envelope characterizes
the supply side only and convergence checks Path A's supply-side bounds against Path B's
realized supply-side envelope. Demand-side / structural-exposure-side convergence remains an
open question for downstream Stage-3 work.

## §9 — Self-review checklist

- **≥4 of 5 building blocks:** Background Information (Stage-1 sha pins + dispatch brief
  lineage + v0 schema + provenance discipline); Context Information (Pair D PASS verdict +
  framework imports + on-chain pin scaffolding + budget-aware degradation path); Tonal Control
  (reliability-obsessed Data Engineer voice; precise quantification; no marketing copy); Tool
  Use Instructions (committed Alchemy budget + SQD-Network-primary architecture + Dune ceiling
  + degradation ladder). User Preferences emerges through the inherited RC FLAG handling and
  HALT discipline. Coverage: 4 of 5 explicit + 1 implicit-through-inheritance.
- **≥6 of 7 complexity principles:** Define Personality and Tone; Guide Tool Use and Response
  Formatting (SQD / Alchemy / Dune / Subgraph / Subsquid-Cloud-paid-only ladder with
  pre-pinned ceilings); Implement Dynamic Behavior Scaling (v0-v3 ladder with per-version
  exit criteria); Inject Critical Non-Negotiable Facts (Stage-1 sha pin chain, on-chain
  address pins, $49 Alchemy commitment, SQD Network FREE classification); Instruct Critical
  Evaluation (no causal claims, no β re-litigation, no curve-fitting, no post-data threshold
  tuning, no silent path-coupling); Provide Context Information (full inheritance from
  dispatch brief + MEMO §7 + VERDICT.md); Set Clear Guardrails (typed-exception HALT pathway
  with ≥3 pre-pinned pivots per HALT, anti-fishing posture, Stage-3 out-of-scope,
  CORRECTIONS-γ scoping reminder). Coverage: 7 of 7.
- **No XML tags.** Section headers and bullet points only.
- **No code.** Code-agnostic per `feedback_no_code_in_specs_or_plans`. Schema definitions,
  address pins, mathematical formulas, configuration parameters, and dependency lists are
  permitted; actual Python/SQL/JavaScript implementation is not.
- **Quality metrics 1-8.** Completeness (4+ building blocks, 6+ principles, 3 BLOCKs +
  9 FLAGs resolved); clarity (each section is unambiguous and actionable; new schema +
  provenance sections are tabular and testable); consistency (no conflicting directives —
  Stage-3 out-of-scope is repeated wherever it could be ambiguous; CORRECTIONS-γ is
  flagged but not applied to keep diff scoped); purposefulness (every section serves the
  v0-v3 ladder, the budget-pin reconciliation, or inherited anti-fishing); naturalness
  (Data Engineer voice is consistent and Phase-A.0 discipline integrates organically);
  comprehensiveness (dense, no filler); safety (HALT pathway is the load-bearing safety
  mechanism; provenance discipline is the audit-incompatibility safeguard; budget-aware
  degradation is the cost-discipline safeguard); user experience (clear ladder with
  pre-pinned exits and pre-pinned pivots; explicit free-vs-paid cost classifications).

End of spec body. Frontmatter `verifier_v1_wave1` and `verifier_v1_wave2` fields are pending
re-run of the 2-wave doc-write verification on v1.1 per
`feedback_two_wave_doc_verification`.
