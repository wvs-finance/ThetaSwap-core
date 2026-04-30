---
spec_path: pair-d-stage-2-B-on-chain-data
spec_version: v1.0 (initial draft)
spec_author: Data Engineer dispatch 2026-04-30
spec_sha256: <to-be-pinned-after-2-wave-verify>
stage1_pinned_chain:
  spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel: 6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols: d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack: 67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf
on_chain_pins:
  mento_v3_router: "0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6"
  mento_v2_copm: "0x8A567e2aE79CA692Bd748aB832081C45de4041eA"
  # USDm canonical, Mento V3 USDm/COPm pool, Uniswap V3 Celo factory, Panoptic Ethereum factory,
  # Bitgifty / Walapay settlement contracts: frozen into frontmatter at v0 audit closure
tooling_budget_committed: $49/mo Alchemy Growth (2026-04-30 user pin)
tooling_budget_pending: false
internal_ladder: v0 (data audit) → v1 (CF^a_l) → v2 (CF^a_s) → v3 (CPO backtest)
convergence_point: v3 realized P&L envelope check on Path A v3 MC bounds
verifier_v1_wave1: pending
verifier_v1_wave2: pending
---

# Pair D — Stage-2 Path B — On-Chain Data Empirical-Validation Spec

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

Path B's purpose is **revealed-preference evidence** — what behavior is *already* measurable in
the existing on-chain history of the candidate venues — rather than the analytical claim that
Path A constructs by stochastic / Monte-Carlo modeling of the same underlying CPO mechanics. The
two paths are independent and converge at v3: Path B reconstructs the realized `CF^(a_l)` and
`CF^(a_s)` and replays them through the framework's `Π(σ_T)` to get a realized CPO P&L envelope;
Path A produces a stochastic-bound P&L distribution under the same framework. The convergence
dispatch (separate from this spec) checks whether Path A's bounds contain Path B's realized
envelope. Disagreement is informative; agreement upgrades the M-sketch's empirical defensibility.

Path B is intentionally narrower than the dispatch brief itself. The dispatch brief authors a
*deployable* position-construction sketch on Panoptic; Path B does not. Path B audits whether the
flows the M-sketch presupposes are present and measurable on-chain. If they are not, the
M-sketch inherits an architectural risk that propagates into Stage-3.

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

**Exit:** feasibility yes/no per data source, with sha-pinned snapshot of pool addresses,
cumulative metrics, and block-range bounds. Frontmatter `on_chain_pins` block frozen.

**v1 — Empirical `CF^(a_l)` reconstruction.** For each viable pool from v0, extract historical
swap events and reconstruct LP-side cash flow per the framework definition
`CF^(a_l)_T = Σ_t r_(a_l) · |(X/Y)_t − (X/Y)_{t-1}|`. The `r_(a_l)` parameter is **derived from
data** — realized fee yield per unit of σ-driven turnover, computed by regressing realized
LP-fee accrual on realized FX-tick magnitude over the v1 sample. No curve-fitting; `r_(a_l)`
comes out where it comes out.

**Exit:** per-pool empirical `CF^(a_l)` realized series (block-aligned, normalized to the Pair D
2015-2026 window), estimated `r_(a_l)` with HAC-corrected SE. Qualitative shape check against the
framework's `Σ r·|FX_t − FX_{t-1}|` shape; sign-and-magnitude pattern only, no goodness-of-fit
threshold (no honest threshold exists absent reference baselines).

**v2 — Empirical `CF^(a_s)` reconstruction.** Harder version of the ladder; most likely HALT
site. Bill-pay flows are partially abstracted: a Bitgifty / Walapay user pays USD-stable in
their wallet and the merchant receives local-stable somewhere downstream, possibly through an
off-chain corridor with no usable on-chain fingerprint. v2 attempts to extract the on-chain
settlement-leg events for the top a_s candidates from the dispatch brief §5 and estimate
fixed-obligation turnover plus realized FX-path cost: specifically the `Σ q_t / (X/Y)_t` term
from the framework's a_s cash-flow definition.

**Exit:** at minimum, directional evidence of `Δ^(a_s) < 0` shape against realized σ in the same
sample window. If the on-chain fingerprint is too abstracted to reconstruct, v2 HALTs and surfaces
the typed exception in §6. The HALT is expected with non-trivial probability and does not
invalidate Path B; the framework's `Δ^(a_l) > 0` evidence from v1 is sufficient for CPO
supply-side fitness. The dispatch brief §6.8 already flags equilibrium pricing `K_l = K_s` as
the most architecturally consequential Stage-2 decision; v2's success or HALT propagates
directly into that decision.

**v3 — Backtest CPO P&L.** Replay the Pair D 2015-2026 window of realized COP/USD σ-paths
through a theoretical `Π(σ_T)` replication using the empirical `r_(a_l)` from v1 and (if
available) empirical `B_T` calibration from v2. Compute realized CPO P&L for both legs across
the sample.

**Exit:** realized P&L envelope characterized by mean, SD, full quantile vector, max drawdown,
plus a regime-conditional decomposition keyed to the four regimes RC FLAG #6 identified as
over-represented in the 2015-2026 window. Calibration-handoff packet to Path A v3 ready.

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
  on Celo (if deployed), Panoptic factory on Ethereum mainnet, and any Bitgifty / Walapay
  on-chain settlement contracts: pinned at v0 audit completion.

**Block-range bounds.** Mento V3 deployment block is the lower bound for the USDm/COPm pool
sample; the Pair D 2015-01-31 → 2026-02-28 window is the analytical reference. Pre-Mento-V3
history is reachable only through Mento V2 BiPool or earlier constructions; whether usable for
the same `CF^(a_l)` calculation is a v0 audit question. The Pair D window is the *outer*
envelope; if the Mento-V3 deployment block trims it, that fact is recorded and does not
constitute anti-fishing window-curation, because the trim is forced by data availability not
chosen post-data to improve a result (per §7).

**Data-source candidates.** Free-tier and committed-budget on-chain data sources only. Committed
budget is `$49/mo Alchemy Growth` (49M CU / day; user pin 2026-04-30). Beyond Alchemy: Dune
Analytics free tier (2500 SQL credits / month, primary SQL surface for v0 + early v1); Flipside
Crypto free SQL credits (secondary, pivot target if Dune insufficient); The Graph hosted service
(free for any pre-existing subgraph; preferred over raw RPC where coverage exists); Celoscan +
Etherscan free API tier (5 req/s; spot-check verification only); Subsquid self-hosted indexer
(free in compute, high in setup; pre-pinned as v1 / v2 escalation pivot if SQL surfaces hit
ceilings); Jupyter + pandas + statsmodels + sympy (free analysis stack inherited from Pair D
notebooks).

The 2500-credit Dune ceiling is **load-bearing**. v0 data audit roughly fits inside it (~5-10
queries against `mento.swaps`, `uniswap_v3_celo.swaps`, `panoptic_ethereum.events` if those
tables exist). v1 + v2 are credit-heavy and may force a pivot to Flipside or Subsquid; the HALT
condition for credit exhaustion is pre-pinned in §6.

## §4 — Outputs

**v0:** data-coverage audit report (CSV / JSON) listing each candidate venue with venue name,
network, contract address, deployment block, first-swap block, last-swap block, swap-event count,
cumulative volume in USD-equivalent, current TVL in USD-equivalent, snapshot timestamp,
sha-pinned snapshot id. Frontmatter `on_chain_pins` update freezing audited addresses. Findings
memo (1-2 pp) recommending which candidates graduate to v1 with data-availability reasons (not
result-shaping reasons).

**v1:** per-pool empirical `CF^(a_l)` time series (daily or weekly cadence pre-pinned at v1
entry), estimated `r_(a_l)` with HAC SE, qualitative shape-check chart against
`Σ r·|FX_t − FX_{t-1}|`, findings memo recommending whether v2 proceeds or v1 alone provides
sufficient empirical defensibility for the M-sketch supply-side leg.

**v2:** if `CF^(a_s)` reconstruction succeeds — empirical demand-side cash-flow series, estimated
effective `B_T` calibration, realized Δ-shape against σ. If HALT — typed-exception HALT memo per
`feedback_pathological_halt_anti_fishing_checkpoint` documenting which fingerprint was sought,
why unreachable, and ≥3 user-enumerated pivots.

**v3:** realized CPO P&L distribution over feasible block-range overlap with the Pair D window
(mean, SD, quantiles, max drawdown, regime-conditional decomposition); calibration-handoff
packet to Path A v3 (empirical `r_(a_l)`, `B_T` or v2 HALT artifact, realized envelope) as JSON
plus tabular CSV; findings memo characterizing the envelope and flagging convergence questions.

## §5 — Tooling stack + budget assumption

The committed Path B tooling budget is `$49/mo Alchemy Growth` (user pin 2026-04-30) plus
free-tier everything else.

- **RPC:** Alchemy Growth — 49M CU / day, reliable at the scale Path B needs for Celo + Ethereum
  log extraction. Primary RPC surface; Celoscan / Etherscan free tier (5 req/s) for spot-check
  verification only.
- **SQL:** Dune Analytics free tier — 2500 SQL credits / month. v0 audit fits at roughly 5-10
  small queries. v1 + v2 are credit-heavy: a multi-month swap-event extraction over Mento V3 +
  Uniswap V3 Celo can consume 50-200 credits depending on partition pruning. At v1 entry the
  executor pre-budgets the v1 SQL workload against the remaining credit balance and HALTs if
  insufficient. Pivot target: Flipside Crypto free SQL credits, then The Graph hosted-service
  subgraphs (free), then Subsquid self-hosted (free-but-effortful).
- **Subgraphs:** The Graph hosted service — free for any pre-existing subgraph. Mento V3,
  Uniswap V3 Celo, and Panoptic Ethereum all have community subgraphs as of 2026-04. v0 confirms
  subgraph existence per venue; v1 / v2 prefer subgraphs over raw `eth_getLogs` where coverage
  exists.
- **Block explorer:** Celoscan + Etherscan free-tier API for ad-hoc verification, transaction
  decoding, and source-code lookup. Rate-limit-bound; not for bulk extraction.
- **Notebook stack:** Jupyter + pandas + statsmodels + sympy inherited from the Pair D notebook
  environment at `contracts/notebooks/bpo_offshoring_fx_lag/Colombia/`. Path B notebooks live at
  a Path-B-specific subdirectory specified at v0 entry.
- **Self-hosted indexer:** Subsquid — free if Dune + Flipside + The Graph coverage proves
  jointly insufficient. Pre-pinned as v1 / v2 fallback. Setup cost (squid generator + TypeScript
  indexing) is non-trivial for single-purpose audits; fallback, not default.

The 2500-credit Dune ceiling is acknowledged as a load-bearing constraint that may force
HALT-and-pivot at v0 if v0 alone consumes the full month's allowance. Auto-pivot to the paid
Dune Analyst tier ($89/month) is **deferred** and not authorized under this spec without
explicit user re-budgeting. Frontmatter records `tooling_budget_pending: false;
tooling_budget_committed: $49/mo Alchemy Growth (2026-04-30 user pin)`.

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

- **v0 — `Stage2PathBDuneCoverageInsufficient`.** Triggers if Dune's `mento.swaps` /
  `uniswap_v3_celo.swaps` / `panoptic_ethereum.events` coverage is missing or has fewer than 100
  events for the primary candidate. Pivots: (a) Flipside Crypto SQL queries; (b) The Graph
  hosted subgraphs against Mento or Uniswap; (c) Subsquid self-hosted indexer.

- **v0 — `Stage2PathBDuneCreditCapHit`.** Triggers if v0 alone consumes the full 2500-credit
  monthly Dune allowance before the audit report is complete. Pivots: (a) move remaining work
  to Flipside; (b) move remaining work to The Graph; (c) request user re-budgeting to paid Dune
  Analyst tier (NOT auto-authorized).

- **v1 — `Stage2PathBALCashFlowContaminated`.** Triggers if observed LP-fee accrual is materially
  mixed with non-σ-driven incentive emissions (Mento liquidity mining, Uniswap UNI emissions,
  third-party rewards) such that `r_(a_l)` cannot be cleanly attributed to σ-tracking turnover.
  Pivots: (a) net out incentive emissions by parsing reward distributions per LP and report
  `r_(a_l)` as a fee-only residual; (b) drop the contaminated pool and elevate the rank-2
  candidate from dispatch brief §4; (c) report `r_(a_l)` as a confidence interval rather than a
  point estimate and pass wider uncertainty into v3.

- **v2 — `Stage2PathBASOnChainSignalAbsent`.** Triggers if Bitgifty / Walapay / equivalent
  candidates settle bill-pay flows off-chain such that the on-chain signal contains only the
  funding leg without the obligation leg. **Most likely v2 HALT.** Pre-pinned disposition:
  **PROCEED-without-v2-`CF^(a_s)`** is acceptable. Path B graduates to v3 with v1 alone as the
  empirical anchor; the framework's `Δ^(a_s) < 0` shape can be argued symmetrically from
  `Δ^(a_l) > 0` plus the framework derivation. The findings memo records the asymmetry
  explicitly and flags it for Path A v3 convergence dispatch as a known empirical asymmetry. v3
  reports the supply-side P&L envelope only and explicitly flags the demand-side as
  un-replicated. Pivots (if orchestrator declines PROCEED-without): (a) source off-chain
  Bitgifty / Walapay aggregate volume statistics from publicly available reports as upper-bound
  proxy; (b) substitute Walapay's published Africa-side cross-currency reels as a geography
  substitute; (c) drop v2 and explicitly scope Path B to supply-side empirical validation only.

Each HALT requires a typed-exception memo, a disposition memo with ≥3 user-enumerated pivots,
and explicit user adjudication before any pivot is taken.

## §7 — Anti-fishing posture

Path B inherits the full Pair D Phase-3 anti-fishing posture and adds Path-B-specific invariants:

- **Pool selection follows the dispatch brief candidate ranking.** §4 + §5 rank candidate venues
  by Δ-fit × deployment-readiness; v0 audits them in that order. A post-data swap to a venue
  with nicer data is anti-fishing-banned. If rank-1 HALTs at v0, substitution is a typed-exception
  event with user adjudication, not a silent pivot.
- **σ-period matches Pair D's 2015-01-31 → 2026-02-28 window.** Restricting to a "cleaner"
  sub-period to improve qualitative shape match is anti-fishing-banned. If on-chain block-range
  cannot cover the full window (Mento V3 was deployed after 2015), the Path B sample is the
  maximum feasible overlap, and the gap is recorded explicitly. Window-trim forced by data is
  acceptable; window-curation chosen to improve a result is not.
- **`r_(a_l)` is computed as-is from realized fee data.** No curve-fitting to frame the result.
  Estimated parameter is reported with SE and propagated into v3 unchanged.
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
- **No post-data threshold tuning.** The 100-event v0 floor, the 2500-Dune-credit budget
  ceiling, and the v0-v3 SAA dispositions are pre-pinned at authoring time and do not move
  post-data. Free-tuning a threshold to avoid a HALT is exactly the failure mode
  `feedback_pathological_halt_anti_fishing_checkpoint` exists to prevent.

## §8 — Convergence with Path A

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
realized supply-side envelope. Demand-side convergence remains an open question for downstream
Stage-3 work.

## §9 — Self-review checklist

- **≥4 of 5 building blocks:** Background Information (Stage-1 sha pins + dispatch brief
  lineage); Context Information (Pair D PASS verdict + framework imports + on-chain pin
  scaffolding); Tonal Control (reliability-obsessed Data Engineer voice; precise quantification;
  no marketing copy); Tool Use Instructions (committed Alchemy budget + Dune ceiling + fallback
  ladder). User Preferences emerges through the inherited RC FLAG handling and HALT discipline.
  Coverage: 4 of 5 explicit + 1 implicit-through-inheritance.
- **≥6 of 7 complexity principles:** Define Personality and Tone; Guide Tool Use and Response
  Formatting (Dune / Flipside / Subgraph / Subsquid ladder with pre-pinned ceilings);
  Implement Dynamic Behavior Scaling (v0-v3 ladder with per-version exit criteria); Inject
  Critical Non-Negotiable Facts (Stage-1 sha pin chain, on-chain address pins, $49 Alchemy
  commitment); Instruct Critical Evaluation (no causal claims, no β re-litigation, no
  curve-fitting, no post-data threshold tuning); Provide Context Information (full inheritance
  from dispatch brief + MEMO §7 + VERDICT.md); Set Clear Guardrails (typed-exception HALT
  pathway with ≥3 pre-pinned pivots per HALT, anti-fishing posture, Stage-3 out-of-scope).
  Coverage: 7 of 7.
- **No XML tags.** Section headers and bullet points only.
- **No code.** Code-agnostic per `feedback_no_code_in_specs_or_plans`.
- **Quality metrics 1-8.** Completeness (4+ building blocks, 6+ principles); clarity (each
  section is unambiguous and actionable); consistency (no conflicting directives — Stage-3
  out-of-scope is repeated wherever it could be ambiguous); purposefulness (every section
  serves the v0-v3 ladder or inherited anti-fishing); naturalness (Data Engineer voice is
  consistent and Phase-A.0 discipline integrates organically); comprehensiveness (dense, no
  filler); safety (HALT pathway is the load-bearing safety mechanism); user experience (clear
  ladder with pre-pinned exits and pre-pinned pivots).

End of spec body. Frontmatter `verifier_v1_wave1` and `verifier_v1_wave2` fields are pending the
2-wave doc-write verification pass per `feedback_two_wave_doc_verification`.
