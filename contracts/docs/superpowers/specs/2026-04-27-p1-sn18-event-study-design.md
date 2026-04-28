---
spec_version: 3
decision_hash: f855e036d3c7807e2bef414a91a806caec1279a9d83575020bc2b3e82b47aeab
decision_hash_protocol: sha256 computed against this file with `decision_hash` field set to the sentinel `<to-be-pinned-after-Task-0.3-v3>`. To re-verify, replace the pinned hash with the sentinel string and recompute sha256; should match.
maymin_arxiv_id: "2603.29751"
maymin_arxiv_id_verified: 2026-04-27 via mcp__arxiv__get_abstract; candidate typo "2503.29751" returned 404 (does not exist); 2603.29751 returned full match (Maymin, P. Z., "Common Risk Factors in Decentralized AI Subnets", q-fin.PM/PR, published 2026-03-31)
dependent_plan: contracts/docs/superpowers/plans/2026-04-27-p1-sn18-event-study-implementation.md
verifier_v1_wave1: PASS-WITH-REVISIONS (Reality Checker, 2026-04-27, against v1, 6 BLOCKING + 4 NB + 3 OOS — all closed in v2)
verifier_v1_wave2: PASS-WITH-REVISIONS (Model QA Specialist fresh instance, 2026-04-27, against v1, 8 defects D1-D8 — all closed in v2)
verifier_v2_wave1: PASS-WITH-REVISIONS (Reality Checker, 2026-04-27, against v2, 5 NEW non-blocking polish items NEW-1 to NEW-5 — all but NEW-3/NEW-5 closed in v3)
verifier_v2_wave2: PASS-WITH-REVISIONS (Model QA Specialist fresh instance, 2026-04-27, against v2, 3 NEW BLOCKING items V2-N1, V2-N2, V2-N3 — all closed in v3)
verifier_v3_wave1: PASS (Reality Checker, 2026-04-27, against v3, no STILL-BLOCKING; no new defects; anti-fishing posture stable)
verifier_v3_wave2: PASS (Model QA Specialist fresh instance, 2026-04-27, against v3, all 4 v3 fixes properly close v2 issues; no v3-introduced defects; no threshold loosened)
execution_status: PARKED 2026-04-27 per user directive — slow-lane P1 spec finalized + sha256-pinned for the record but execution deferred. Refocus to fast-lane simple-β exercise (FX-X → Y1 RWC-USD). P1 may be re-activated as a future iteration if fast-lane succeeds and AI-cost X is added as a second instrument.
revision_history:
  - v1 2026-04-27 initial draft (Model QA Specialist)
  - v2 2026-04-27 integrate B1-B6 + D1-D4 + NB3/NB4 + D5/D6/D7/D8 per Wave 1 + Wave 2 verifier findings; orchestrator resolved D2 (extend-backward fix) and D3 (asymmetric placebo-FAIL retention) (Model QA Specialist, fresh instance)
  - v3 2026-04-27 integrate v2 verifier findings (orchestrator-applied — scope was 4 textual edits, ~17 lines): V2-N1 + RC NEW-4 §5.2 cascade-to-N_MIN_EVENTS clarification + edge-case ack; V2-N2 + RC NEW-2 §3 ceil/floor convention + sign-agreement table footer; V2-N3 §8.2(b.i) joint qualifier paragraph for R-H1/R-T1 decrement interaction; RC NEW-1 §3 R-T1 cutoff wording cleanup
---

# P1 — SN18 Cortex.t Alpha Event Study: Pre-Registered Design

This spec is the load-bearing artifact of P1 Phase 0. Its sha256 pin (computed by Task 0.3 after 2-wave review) governs every downstream artifact in the implementation. All thresholds, sample-selection rules, methodology choices, and verdict-decision-tree branches are committed here BEFORE any data is pulled or analysis is run, per the Phase-A.0 anti-fishing pattern (`feedback_pathological_halt_anti_fishing_checkpoint`).

---

## §1 Background and motivation

The Abrigo product family pursues a post-Keynesian inequality goal: alter the institutional structure that currently blocks wage earners from accumulating productive capital, by selling permissionless on-chain perpetual convex instruments whose accumulated payoff converts wage premium into capital exposure over time. Each iteration is a (Y, M, X) triple — outcome variable, Panoptic-eligible market configuration, and macro risk that blocks the wage-to-capital transition for a target population.

The slow-lane research thread tests whether **proprietary AI provider pricing power** is a viable X for entrepreneur populations whose unit economics are dominated by inference cost. Prior signal-research (`contracts/.scratch/2026-04-27-onchain-proxies-for-proprietary-ai-cost.md`) found that the broad on-chain AI-token basket {TAO, AKT, RNDR, FET/ASI, VIRTUAL, OLAS, MOR, CGPT, ai16z/ELIZAOS} is **not a tradable substrate** for this risk: 70-95% of basket monthly variance is attributable to crypto-narrative cycles, project-idiosyncratic shocks (ASI merger, AI16Z fraud, Bittensor halving, Render Solana migration), broader macro factors, and BTC beta — leaving at most 5-15% to the actual proprietary-AI policy signal. Six attempts to detect a clean Anthropic-event abnormal return in the broad basket failed (events #6, #8, plus four implied by the Claude 3.5 → 4.7 cadence).

The bridge-research follow-up (`contracts/.scratch/2026-04-27-bittensor-claude-bridges-prototype-modeling.md`) identified Bittensor Subnet 18 (Cortex.t, operated by Corcel) as the **single cleanest candidate substrate**. Verbatim from the Cortex.t project documentation: *"Neither the miner or the validator will function without a valid and working OpenAI API key"* (source: `https://cortex-t.ai/docs`, retrieved and verified accessible 2026-04-27 by Wave-1 Reality Checker). **CORRECTIONS NOTE (v2):** the bridge-research report (`contracts/.scratch/2026-04-27-bittensor-claude-bridges-prototype-modeling.md`) gives the GitHub URL `https://github.com/corcel-api/cortex.t` for the same quote; that URL returned 404 at Wave-1 verification time and is stale. The canonical, verifiable source is `https://cortex-t.ai/docs`. The canonical software stack supports `gpt-3.5-turbo`, `gpt-4`, `gemini`, and `claude3` as backends; miner unit economics are mechanically `(α_18 emission share × α_18 USD price) − (proprietary API USD spend)`. This is the only known on-chain substrate where the proprietary-AI cost signal enters miner break-even *as a hard constraint*, not as one input among many.

This study tests whether that mechanical linkage is **empirically detectable** in α_18 returns at dated proprietary-AI provider events. A PASS verdict would establish that a channel exists at retail-prototype scale and would unlock P2 (SUR triangulation across SN18 + SN4 + Olas Mech) or P3 (cointegrated SN18-vs-SN64 pair-trade calibration) per the bridge-research design tiers. A FAIL verdict would close the slow-lane substrate question and redirect M-track research to other substrate candidates or accept the absence of a viable substrate. An INDETERMINATE verdict would name the additional data or methodology required to resolve.

The substrate's *distinguishing claim* — that proprietary-AI cost is mechanically embedded in miner break-even — is what "cleaner than the broad basket" empirically means. This study operationalizes that distinction: if the broad-basket finding holds at SN18 (no detectable signal), the cleanliness claim was wrong and the substrate question is closed; if SN18 produces a detectable signal where the broad basket did not, the claim is vindicated and the slow-lane substrate is named.

---

## §2 Hypothesis statement

Let `α_18,t` denote the daily log return on the Bittensor Subnet 18 (Cortex.t) dTAO subnet token at trading day `t`. Let `E` denote the pre-registered set of proprietary-AI policy events (Anthropic and OpenAI; Google deferred to Tier-2 per §4) falling within the in-sample window. Let `AR_i` denote the abnormal return on α_18 attributable to event `i ∈ E`, computed per the methodology in §5.

**H₀ (null):** `E[AR_i] = 0` for all `i ∈ E`. Proprietary-AI policy events have no detectable mean effect on α_18 abnormal returns over the pre-registered event window.

**H₁ (alternative, two-sided):** `E[AR_i] ≠ 0` for the joint test across `i ∈ E`. Proprietary-AI policy events have a detectable mean effect on α_18 abnormal returns over the pre-registered event window.

**Direction of the alternative — two-sided, justified.** The bridge-research design source (§2.5) identifies *two competing economic mechanisms* with opposite predicted signs:

- **Substitution channel (negative β predicted):** when proprietary providers raise prices, Cortex.t miners' cost floor moves up; some exit, some reduce serving volume; under Taoflow flow-based emissions, reduced net staking inflow into SN18 cuts next-period emission allocation; α_18 falls. Sign: *price-up → α_18-down*.
- **Passthrough / monopoly-rents channel (positive β predicted):** when proprietary providers raise prices, Cortex.t miners can raise the per-call price they charge Cortex.t API clients; the margin layer thickens; α_18 rises. Sign: *price-up → α_18-up*.

Neither mechanism is theoretically excluded ex ante. The bridge-research report explicitly flags this ambiguity and treats either-sign-significant as informative. Pre-committing to a one-sided test would constitute spec-leakage given the genuine theoretical disagreement. The two-sided choice is locked here and may not be revised post-data.

The joint hypothesis treats `E` as a single test (the pre-registered event family) rather than per-event tests; per-event significance is reported only as descriptive context, never as the primary verdict input.

---

## §3 Falsification criteria

Three-way exhaustive over the (primary test statistic, primary p-value, robustness consistency) outcome space. The primary test is the joint test on `E[AR_i] = 0` across the pre-registered event family per §5; the primary p-value is the multiple-testing-adjusted p-value per §6; robustness consistency is computed across the pre-committed robustness checks per §7 and classified into {AGREE, MIXED, DISAGREE} per the rules below.

**Robustness consistency classification (pre-committed):**
- **AGREE:** All three pre-committed robustness families (alternative event windows; alternative controls; sub-sample splits) produce point estimates with the same sign as the primary AND at least 70% of robustness specifications individually reject H₀ at the spec-pinned α level.
- **DISAGREE:** At least one pre-committed robustness family produces a point estimate with the opposite sign from the primary, or fewer than 30% of robustness specifications individually reject H₀.
- **MIXED:** Neither AGREE nor DISAGREE conditions are satisfied. (I.e., 30%-70% of robustness specifications reject, or at least one family wavers but no family flips sign.)

The 70% / 30% thresholds are pinned here and may not be tuned post-data. The "robustness specification" denominator is the count of distinct robustness rows enumerated in §7 (`N_robustness`); the numerator is the count of those rows whose individual p-value is below the spec-pinned α level (no multiple-testing correction is applied at the per-row robustness level — robustness is an internal-consistency test, not a confirmatory test).

**Robustness denominator decrement paths (exhaustively enumerated; no other paths admitted).** `N_robustness` is nominally 13 (per §7.8) but may be decremented at runtime by ONE OR MORE of the following pre-committed paths:

1. **R-H1 underpower (per §7.4):** if events overlapping the Bittensor halving window are excluded under R-H1 and the residual event count drops below `N_MIN_EVENTS = 8`, R-H1 is reported as "underpowered, excluded from AGREE/DISAGREE count" and `N_robustness` is decremented by 1.
2. **R-T1 underpower (per §7.5):** R-T1 tests robustness to the Nov 2025 Taoflow regime change by *excluding pre-Taoflow events* (events with `t_event < 2025-11-15`) from the analysis and re-running. If after this exclusion the residual post-Taoflow event count drops below `N_MIN_EVENTS = 8`, R-T1 is reported as "underpowered, excluded from AGREE/DISAGREE count" and `N_robustness` is decremented by 1.
3. **R-J1 degenerate cross-provider count (per §7.6):** if the realized count of cross-provider same-day events is zero, R-J1 is reported as "no cross-provider clustering observed; spec is identical to primary" and is excluded from the AGREE/DISAGREE count; `N_robustness` is decremented by 1.

These three are the ONLY admitted decrement paths. Any impulse to decrement `N_robustness` on any other ground triggers a HALT-disposition memo per §9. The maximum admitted decrement is 3 (all three paths fire), giving `N_robustness ∈ {10, 11, 12, 13}` as the only admissible runtime values.

**AGREE/DISAGREE absolute counts at each admitted denominator** (for transparency and operational pin):

| `N_robustness` | AGREE threshold (≥70%) | DISAGREE threshold (≤30%) | MIXED band |
|----------------|------------------------|---------------------------|------------|
| 13             | ≥ 9.1 → ≥ 10 rows reject | ≤ 3.9 → ≤ 3 rows reject  | 4-9 rows reject |
| 12             | ≥ 8.4 → ≥ 9 rows reject  | ≤ 3.6 → ≤ 3 rows reject  | 4-8 rows reject |
| 11             | ≥ 7.7 → ≥ 8 rows reject  | ≤ 3.3 → ≤ 3 rows reject  | 4-7 rows reject |
| 10             | ≥ 7.0 → ≥ 7 rows reject  | ≤ 3.0 → ≤ 3 rows reject  | 4-6 rows reject |

The integer thresholds are obtained by `ceil(0.70 × N_robustness)` for AGREE (yielding ≥10/9/8/7 at N=13/12/11/10) and `floor(0.30 × N_robustness)` for DISAGREE (yielding ≤3 at all admissible N), and are pinned here. The `ceil`/`floor` convention is the mathematically correct handling of the inequality `≥0.70` and `≤0.30` and is binding; the table is the authoritative artifact if any prose-vs-table ambiguity arises.

**Table footer (binding reminder).** Sign-agreement is independently required for AGREE per the §3 AGREE definition above (the percentage threshold is necessary but not sufficient — a count meeting the AGREE row threshold but with mixed-sign rejections is MIXED, not AGREE). Phase-3 robustness aggregation must compute both (a) the per-row reject count and (b) the per-row sign of the rejected coefficient before classifying.

**PASS-trigger conditions:** primary p-value < α (per §6) AND robustness consistency = AGREE. The signal exists, is statistically detectable, and survives the pre-committed robustness perturbations.

**FAIL-trigger conditions:** primary p-value ≥ α (per §6) AND robustness consistency ∈ {AGREE, MIXED, DISAGREE}. The signal does not exist at the spec-pinned detection threshold. (FAIL is the default when the primary test does not reject; robustness consistency cannot rescue a primary FAIL into a PASS.)

**INDETERMINATE-trigger conditions:** primary p-value < α AND robustness consistency = DISAGREE. The signal is statistically detectable in the primary specification but the pre-committed robustness perturbations contradict it; the result is not safe to escalate. Also INDETERMINATE: primary p-value < α AND robustness consistency = MIXED, unless §8 pre-commits a tie-break rule (see §8).

**Mutual-exclusivity proof:** Every (primary p-value, robustness consistency) pair maps to exactly one verdict per §8's 9-cell matrix. No pair is unmapped; no pair maps to two verdicts.

---

## §4 Sample-selection rules

### 4.1 Event eligibility (Anthropic and OpenAI in-scope; Google deferred)

An event is eligible for inclusion in `E` if and only if it satisfies ALL of the following:

1. **Provider:** Issued by Anthropic or OpenAI. Google / Gemini events are deferred to Tier-2 because (a) bridge-research shows the Cortex.t README does not name Gemini as a default backend in the same way it names OpenAI as required, (b) Google does not publish a comparable changelog cadence, and (c) including Google would dilute the multiple-testing power budget at α level pinned in §6. The deferral is a scope choice, not a substantive judgment about Google events.

2. **Event type:** Falls in one of the following pre-registered categories, each defined to be unambiguously verifiable from the source URL alone (no operator-judgment classification at analysis time):
   - `price_change` — published change to per-token input or output pricing for any production model.
   - `rate_limit_change` — published change to per-account rate limits, tier thresholds, or capacity allocation.
   - `model_launch` — first-availability date of a new production model (not a research preview).
   - `model_deprecation` — published date of removal, sunset, or end-of-life for a production model.
   - `tos_change` — change to API terms of service that restricts or expands developer use cases (e.g., commercial licensing, output redistribution).
   - `capacity_event` — published incident on the provider's status page lasting ≥ 1 hour with `affected_endpoints` including a chat or completion model API.

3. **Source verifiability:** The event has a public, durable source URL (provider blog, provider docs changelog, provider status page, or major press outlet of record). X/Twitter posts are admissible only if the same content is mirrored on a durable provider channel.

4. **Timestamp resolution:** The event timestamp is known to at least daily resolution in UTC. Events with only "month of" or "quarter of" resolution are excluded.

5. **Non-clustering rule:** If two eligible events from the *same provider* fall on the *same UTC date*, they are merged into a single composite event for the analysis (event_type recorded as the higher-impact category per a fixed precedence: `price_change` > `model_launch` > `rate_limit_change` > `model_deprecation` > `tos_change` > `capacity_event`). Cross-provider same-day events are NOT merged but are flagged for joint-window treatment in §5.

### 4.2 Time window

**Start date:** 2025-02-13 (best-estimate dTAO mainnet activation date — bridge-research §2.1 cites only "Q1 2025" and a primary source for the exact 2025-02-13 date has NOT been verified at spec-pin time; this date is therefore **provisional pending Data Engineer Phase 2 verification** against a primary source — taostats.io changelog, Bittensor Foundation announcement, or first observed `α_18` price tick in the on-chain data). The α_18 series does not exist before whatever the verified activation date is, so the window cannot extend earlier regardless of event count.

**Mandatory verification step (binding on Phase 2):** Data Engineer Task 2.1 MUST resolve the dTAO activation date against a primary source before any Phase 3 work begins. Three outcomes are admitted:
1. **2025-02-13 confirmed** by primary source — the spec start date stands; the pin is upgraded from "provisional" to "verified" in `DATA_PROVENANCE.md` with the source citation.
2. **Primary source disagrees with 2025-02-13 by ≤ 14 days** — the spec start date is amended to the primary-source date via the §0 2-wave amendment process; the amendment is purely administrative (no methodology drift) and is logged in `DATA_PROVENANCE.md` with both dates and the source citation.
3. **Primary source disagrees by > 14 days OR no primary source can be located** — HALT-disposition memo required; orchestrator dispatches the spec amendment under §9 invariant 1 before Phase 3 begins. Tuning the start date to maximize event count without primary-source backing is anti-fishing-banned.

**End date:** 2026-04-27 (this spec date). No events after this date are in scope. Data pulls in Phase 2 capture through this date; later data is treated as out-of-sample by construction.

**Resulting nominal window:** ~14.5 months of dTAO history. Given Anthropic's 2024-2026 release cadence (Claude 3.5 → 3.5-Oct → 3.7 → 4 → 4.5 → 4.6 → 4.7) and OpenAI's parallel cadence (GPT-4o, GPT-4o-mini, o1, o3-mini, plus GPT-5 if shipped), the bridge-research §2.5 estimate of ~10-12 dated events extending across the full 2024-2026 corridor will be truncated to the post-dTAO subset — the orchestrator and Trend Researcher will count actual eligible events under the §4.1 criteria during Phase 1.

### 4.3 N_MIN_EVENTS

**N_MIN_EVENTS = 8.**

Justification grounded in the test's power requirements at the spec-pinned α level:

- The primary test (§5) is a joint test across the pre-registered event family with multiple-testing correction at α = 0.05 (two-sided) per §6. Below ~8 events, the multiple-testing-adjusted critical value approaches the un-adjusted critical value (Bonferroni at K=8 gives α' = 0.00625; below K=8 the practical penalty is small but the per-event AR estimates have insufficient cross-sectional variation to support a stable joint-test variance estimate).
- Maymin (2026, arXiv:2603.29751) analyzes 128 subnets at daily frequency and reports HAC(K) with K computed via `floor(4(n/100)^(2/9))`. Our event-study cross-section is much smaller; below 8 events the bootstrap CI on the joint AR estimate is not credible (rule of thumb for bootstrap consistency: ≥ 8 cluster-equivalents).
- The bridge-research §6.1 explicitly states "need 8-10 events for any directional inference" — N_MIN_EVENTS = 8 is the lower bound of that range. Setting it lower would invite a HALT-disposition rationalization at analysis time; setting it higher would risk N_MIN_EVENTS itself becoming binding without principled escalation.

**Power disclosure (mandatory in Phase-4 memo).** At α_primary = 0.0167, N=8, df=7, two-sided, the cross-sectional t-test on mean CAR has the following power profile against Cohen's d effect sizes (computed analytically from the non-central Student-t distribution; pinned here as a reference profile for the Phase-4 memo, not as a gate threshold):

- Power ≈ 0.80 against d ≈ 1.4 (very large effect on AR — i.e., per-event mean CAR roughly 1.4 × cross-sectional SD of CAR).
- Power ≈ 0.40 against d ≈ 0.8 (large effect).
- Power ≈ 0.13 against d ≈ 0.5 (medium effect).

**Operational consequence:** the prototype is explicitly underpowered against medium effects. A FAIL verdict at N≈8 is consistent with EITHER (a) "no signal exists" OR (b) "a medium-or-smaller effect exists that this study could not detect at α_primary = 0.0167". The Phase-4 memo MUST report this power profile against the realized N (recomputing the d-vs-power table at the realized DF) and MUST disclose it in any external communication that cites the verdict. Promoting a FAIL verdict to "no signal exists, channel ruled out" without the power-disclosure footnote is an anti-fishing violation under the spirit of §9 invariant 4.

**HALT-disposition trigger:** If at Phase 2 Task 2.4 Step 4 the count of Phase-1-eligible events falling within the §4.2 window is `< N_MIN_EVENTS = 8`, the Data Engineer / Reality Checker HALTS and the orchestrator dispatches a spec amendment via the 2-wave rule before any Phase 3 work begins. The amendment must EITHER (a) extend the eligibility criteria with explicit pre-data justification (e.g., admit Google events if their inclusion can be justified independently of the observed event count), (b) widen the time window if dTAO activation date is corrected backward, or (c) accept the prototype as inconclusive at the substrate-availability level (a substantively different verdict than INDETERMINATE — the substrate is too young, not the signal too weak). Threshold-tuning the N_MIN_EVENTS integer downward is *banned* under the anti-fishing invariants (§9).

### 4.4 Exclusion criteria

The following events are *excluded* from `E` even if they satisfy §4.1:

- Events whose source URL has been retracted or 404s at the time of Phase 1 assembly (Reality Checker verifies per Task 1.4 Step 5).
- Events that are pure restatements of prior events (e.g., a press-release recap of a prior changelog entry from the same provider) — included only once, dated to the earliest publication.
- Bittensor protocol-internal events (dTAO launch transient, **Dec 15 2025** halving (corrected from "Dec 14 2025" cited in v1 and bridge-research §2.1; the verified halving date is 2025-12-15 per Wave-1 Reality Checker), Nov 2025 Taoflow regime change). These are NOT proprietary-AI events; they are controlled for in §7 robustness.

---

## §5 Methodology

### 5.1 Event-window length (primary)

The primary event window is **(t_event − 1, t_event + 3)** trading days, i.e., a 5-day window starting one trading day before the event and ending three trading days after. This window is chosen because:

- The bridge-research §6.1 defaults to 3-day cumulative abnormal return (CAR), which assumes the market response is largely complete within three trading days. The pre-event leg (−1) absorbs information leakage on the day prior (e.g., a price-change announcement leaked the evening before).
- Subnet-token CPMM markets on Bittensor have shallow daily liquidity (Maymin 2026 documents the size premium is implementable only sub-$10K AUM); response should be largely complete within three trading days, but a (0, +1) window risks missing slow propagation through cross-subnet rotation.
- (-1, +3) is shorter than the (−5, +5) and (−10, +30) ranges tested as robustness in §7, providing a tighter primary-test window with the longer windows serving as sensitivity checks.

### 5.2 Abnormal return calculation

Abnormal return for event `i` on calendar day `t` within the event window:

```
AR_{i,t} = R_{α_18, t} − [β̂_TAO · R_{TAO, t} + β̂_64 · R_{α_64, t} + β̂_ETH · R_{ETH, t} + α̂]
```

where:
- `R_{X, t}` = log return of asset X on day `t`.
- `(α̂, β̂_TAO, β̂_64, β̂_ETH)` = OLS coefficients from the **estimation window** regression of `R_{α_18}` on the three controls plus a constant.
- **Estimation window:** trading days `[t_event − 30, t_event − 6]` (a 25-day pre-event window, leaving a **4-day buffer** — days `t_event − 5, t_event − 4, t_event − 3, t_event − 2` — between estimation and event windows to prevent estimation leakage from any pre-event drift). Buffer math corrected in v2 from v1's "2-day buffer" (factual error: estimation-window endpoint `t_event − 6` and event-window start `t_event − 1` give 4 strictly-between days, not 2).

**Estimation-window leakage from clustered prior events (extend-backward rule, hard-pinned).** If a prior event-window falls within the estimation window of event `i` — formally, if `t_event(j) ∈ [t_event(i) − 30, t_event(i)]` for some `j ≠ i` — the estimation window for event `i` is extended backward by the number of trading days lost to the prior event-window overlap, capped at `[t_event(i) − 60, t_event(i) − 6]`. If even the extended window cannot accommodate 25 clean trading days (i.e., 25 trading days that contain no other event-window day), event `i` is excluded from the primary analysis (logged in `PRIMARY_RESULTS.md` with explicit reason). **Cascade to N_MIN_EVENTS:** the post-exclusion realized event count `|E|` (after extend-backward exclusions are applied) is the count compared to `N_MIN_EVENTS = 8` per §4.3 and §8.3; if extend-backward exclusions drop `|E|` below the threshold, the §4.3 HALT-disposition pathway is dispatched and the §8.3 `SUBSTRATE_TOO_YOUNG` verdict applies. **Edge-case acknowledgement:** the 60-day cap (≈ 38-39 trading days at a typical 5-day week) leaves ~13-14 trading days of slack to absorb prior-event-window contamination before the exclusion-of-last-resort fires. There is no partial-credit / shrinkage option for an extended window that contains only 20-24 clean trading days — such an event is excluded entirely (the 25-day floor is binding, not negotiable). The orchestrator resolved the cross-reviewer disagreement on this rule in favor of the extend-backward fix because it preserves more events under §4.3 N_MIN_EVENTS pressure than alternative leak-handling rules (e.g., dropping the affected event without extension); the rule is hard-pinned here and may not be revised post-data.

Cumulative abnormal return for event `i` over the primary window:

```
CAR_i = sum over t in [t_event − 1, t_event + 3] of AR_{i,t}
```

The control series choice — joint regression on TAO, α_64, and ETH — is pre-committed because:
- **TAO** controls for Bittensor-network-wide moves (e.g., halving expectation, cross-subnet rotation, TAO macro narrative). **R_TAO denotes the TAO root-token spot return** (taostats.io `tao_price` field, log return), NOT an aggregate market-cap-weighted index across subnets. The root-token return is the appropriate cross-subnet risk control because it is the numéraire of subnet emissions and is structurally exogenous to any single subnet's idiosyncratic moves; subnet-component circularity (which would arise from a market-cap-weighted index that includes α_18 itself) does not apply to the root-token spot.
- **α_64 (SN64 / Chutes)** controls for *decentralized-AI-within-Bittensor* moves; it is the structurally-clean substitute comparator (open-source serverless inference, not proprietary-API-routed). Including α_64 as a control means a positive `β_64` is "α_18 moves with the rest of decentralized-AI-Bittensor", and what remains is genuinely SN18-specific. **Substitute-channel absorption caveat (per Wave-2 D5):** because α_64 is the *substitute* in the substitute-vs-passthrough mechanism enumerated in §2, including α_64 in the primary control set risks absorbing part of the substitute-channel signal (i.e., if proprietary-AI events shift demand from SN18 → SN64, α_64 will rise and α_18 will fall, and the joint-control regression will partly attribute the α_18 fall to the α_64 rise rather than to the event). The orchestrator chose option (b) of D5 — keep α_64 in the primary specification (because dropping it would weaken the structurally-clean comparator argument) but route this absorption risk through the §7 robustness specifications: **R-C1 (TAO+ETH only, dropping α_64) is the operative sensitivity for the substitute-absorption concern, and §8 will explicitly inspect R-C1's sign and magnitude alongside R-C3 (ETH-only) when the primary verdict is FAIL or INDETERMINATE.** A primary FAIL accompanied by an R-C1 PASS-eligible point estimate is itself a strong signal of substitute-channel absorption and MUST be flagged in the Phase-4 memo as a candidate explanation; promoting that combination silently to a primary verdict revision is anti-fishing-banned.
- **ETH** controls for broader crypto risk-on / risk-off regime moves.

Single-control alternatives (TAO-only, α_64-only, ETH-only) are tested as robustness in §7.

If any control series has a missing observation on a day within either the estimation window or the event window for any event, that event is excluded from the primary analysis (and its exclusion is logged in `PRIMARY_RESULTS.md`). A subsidiary event-count is reported separately for robustness.

### 5.3 Test-statistic family (primary)

The primary test is a **two-sample t-test on the cross-sectional mean CAR**:

```
t_primary = mean(CAR_i for i in E) / [SD(CAR_i for i in E) / sqrt(|E|)]
```

with `|E|` = the realized count of in-window eligible events from §4.

This is the standard event-study cross-sectional t-test (Brown & Warner 1985 lineage; see also the Celeny et al. 2024 reference at arXiv:2402.04773 cited in the **signal-research bibliography** at `contracts/.scratch/2026-04-27-onchain-proxies-for-proprietary-ai-cost.md` for cross-sectional event-induced variance corrections — corrected from v1's mis-attribution to the bridge-research bibliography per Wave-1 Reality Checker). The test statistic is compared to a two-sided critical value at the §6 multiple-testing-adjusted α level.

**Auxiliary tests reported alongside the primary** (descriptive, not verdict-determining): non-parametric sign test on `sign(CAR_i)` and Wilcoxon signed-rank test on `CAR_i`. These are reported to flag distributional concerns but do not enter the §3 falsification criteria.

### 5.4 Multiple-testing correction

The primary test is a *single joint test* on the event family `E`. A per-event correction is therefore not required for the primary verdict. However, Bonferroni adjustment is applied at the *spec level* to account for the fact that this study is one of three pre-registered prototype tests (P1, P2, P3 per the bridge-research §6 design tiers); the family-wise α budget at the spec level is therefore 0.05 / 3 = 0.0167 (two-sided), which becomes the operative significance threshold per §6.

**Why Bonferroni (not Holm-Bonferroni or BH-FDR) for the spec-level family.** Holm-Bonferroni and Benjamini-Hochberg FDR were considered as alternatives. Bonferroni is selected because the P1-P2-P3 family is **conjunctive** (the substrate-hierarchy thesis requires that all three claims hold — P1: SN18 is a clean substrate; P2: SN18+SN4+Mech triangulate; P3: SN18-vs-SN64 cointegrates as a pair-trade) rather than **disjunctive** (any one rejecting the null would advance the thesis). Under conjunctive multiple testing the family-wise error rate (FWER) is the binding constraint — false rejection in any single member compromises the joint claim — and Bonferroni is the appropriate correction. Holm-Bonferroni is a refinement of Bonferroni that is uniformly more powerful but identical at K=3 in the worst case relevant here (it only differs when at least one p-value is well below α/K, in which case Holm relaxes the threshold for the remaining tests; this gain is operationally negligible at K=3 and does not justify the additional methodological complexity). BH-FDR (false discovery rate) is **rejected** because (a) the spec-level family is fixed at K=3, well below the K~20+ regime where FDR's power gain over Bonferroni dominates, and (b) FDR is designed for *discovery* contexts (which of many candidates merits follow-up?) rather than *confirmation* contexts (does the joint claim hold?) — the wrong tool for a conjunctive substrate-hierarchy thesis.

**Pin:** the choice of Bonferroni over Holm and BH-FDR is locked here and may not be revised post-data. Any impulse to re-derive multiple-testing under an alternative correction after observing the realized p-values triggers a HALT-disposition memo per §9.

### 5.5 Maymin 2026 methodology baseline and explicit divergences

Maymin (2026, arXiv:2603.29751) is the methodological backbone. Verified arXiv ID per `mcp__arxiv__get_abstract` lookup on 2026-04-27 — the candidate typo `2503.29751` returned 404; `2603.29751` is the correct ID and the paper is "Common Risk Factors in Decentralized AI Subnets" by Philip Z. Maymin (q-fin.PM/PR, published 2026-03-31).

**Where this study follows Maymin:**
- HAC standard errors with `K = floor(4(n/100)^(2/9))` lag length for any time-series regression that appears in robustness (§7).
- Bittensor subnet daily price data from public sources (taostats.io); CPMM mechanics acknowledged as intrinsic to the price-formation process.
- Halving as in-sample shock requiring explicit treatment (§7).

**Where this study diverges from Maymin:**
- **Shock type:** Maymin tests *protocol-internal* events (Dec 2025 halving) on the *cross-section of all 128 subnets*. This study tests *exogenous* events (proprietary-AI provider policy actions) on a *single subnet* (SN18), with three other subnets/assets serving as controls. The economic rationale for the divergence: the substitute-vs-passthrough question is structurally about SN18, not about the cross-section.
- **Test design:** Maymin estimates a small-minus-big size factor across subnets via Fama-MacBeth-style cross-sectional regressions; this study estimates a residual abnormal return on a single subnet via market-model AR with three controls. The economic rationale: cross-sectional factor pricing is irrelevant to the question "did α_18 move on event day?" but Maymin's HAC-K machinery is directly applicable to the residual-AR variance estimation.
- **Sample size:** Maymin: ~128 subnets × ~daily, well over 10,000 obs. This study: ~25-day pre-event estimation window per event × ~8-15 events. The cross-sectional power is dramatically lower; the multiple-testing budget (§5.4) is correspondingly tighter.
- **Halving treatment:** Maymin tests halving as the *primary* shock and finds it cuts the size premium 1.17% → 0.51% (p=0.044). This study treats halving as a *nuisance* shock to be controlled for; events whose primary event window overlaps the halving date (**Dec 15 2025**, corrected from v1's "Dec 14 2025" per Wave-1 Reality Checker verification) are flagged for joint-window treatment per §7.

These divergences are explicit and pre-committed; they may not be revised post-data.

---

## §6 Pre-registered significance thresholds

**Primary α (two-sided):** 0.05 family-wise / 3 spec-level tests = **α_primary = 0.0167** (two-sided; equivalent to one-sided 0.00833).

**Critical t-value:** `t_crit = ±2.394` for a two-sided test at α = 0.0167 with degrees of freedom approximated as `|E| − 1` (degrees of freedom is computed at analysis time given realized `|E|`; the critical value above is the `|E| → ∞` asymptote and is replaced by the exact Student-t critical value at realized DF). **Both the formula (`t_crit` from Student-t at DF = `|E| − 1`, two-sided, α = 0.0167) and the asymptote (`2.394`) are pinned here**; only the numerical evaluation at realized DF is computed at analysis time.

**Decision rule for the primary test:** PASS-eligible (prior to robustness check) iff `|t_primary| ≥ t_crit(|E|−1, α=0.0167, two-sided)`. The PASS bar is **statistically defensible at α = 0.0167** — it is tighter than the conventional 0.05 because of the spec-level multiple-testing budget per §5.4. There are no "soft thresholds"; a t-statistic of 2.30 with realized DF = 10 (where exact critical value is ~2.764) is a FAIL even though it would clear an un-adjusted 0.05 test.

**Robustness threshold for individual specifications (§7):** α_robustness = 0.05 (two-sided), un-adjusted. Robustness rows are individually tested at the conventional level because robustness is an *internal-consistency* test (does the result hold under perturbation?) not a *confirmatory* test (does the signal exist?). The 70%/30% AGREE/DISAGREE thresholds in §3 are computed against this α_robustness, not against α_primary.

**Per-row-descriptive-only guardrail (hard-pinned, no exceptions).** Per-row robustness p-values are **descriptive only** and may NOT be cited in the §8 verdict, the Phase-4 memo's executive summary, or any external communication as substantive evidence of provider-specific or regime-specific signal. The only substantive output of the §7 robustness machinery is the AGREE / MIXED / DISAGREE classification feeding §8. Citing, for example, "R-S1 (Anthropic-only) rejected H₀ at p=0.03 — therefore Anthropic events drive the channel" is **expressly prohibited**: R-S1 is one of 13 (or 10-12 after admitted decrements) robustness specifications, has no per-row multiple-testing correction, and was never powered or pre-committed as a confirmatory test for provider-specific signal. Any narrative or external-communication line of that form constitutes a per-row-descriptive loophole and is treated as an anti-fishing violation under §9 invariant 4. The Phase-4 memo MAY report per-row p-values in an appendix table for full transparency, but MUST flag any provider-specific or regime-specific reading explicitly as "exploratory hypothesis for a P1.1 follow-up; NOT supported by this spec's confirmatory machinery".

These thresholds are pinned here and may not be revised post-data under any circumstance.

---

## §7 Robustness checks (pre-committed)

The robustness check enumeration produces a fixed integer count `N_robustness` of distinct (window, control, sub-sample) specifications. **N_robustness = 13**, computed below. The 70%/30% AGREE/DISAGREE thresholds in §3 use 13 as the denominator.

### 7.1 Alternative event windows (3 specifications)

For each window tuple, recompute CAR_i and the cross-sectional t-test per §5.3. Specifications:
- R-W1: window (−5, +5) — symmetric 11-day window; tests whether the (−1, +3) primary missed slow propagation.
- R-W2: window (−1, +1) — tight 3-day window; tests whether the (−1, +3) primary diluted signal with post-day-+1 noise.
- R-W3: window (−10, +30) — wide asymmetric window; tests whether the response has long-horizon component the primary missed.

### 7.2 Alternative control series (3 specifications)

For each alternative-control specification, recompute AR_i per §5.2 with the substituted controls, then CAR_i over the primary (−1, +3) window. Specifications:
- R-C1: TAO-only as control (drop α_64 and ETH).
- R-C2: α_64-only as control (drop TAO and ETH).
- R-C3: ETH-only as control (drop TAO and α_64).

### 7.3 Sub-sample splits (3 specifications)

For each split, restrict `E` to the named subset and re-run the primary cross-sectional t-test. Specifications:
- R-S1: Anthropic-only events (excludes OpenAI events from `E`).
- R-S2: OpenAI-only events (excludes Anthropic events from `E`).
- R-S3: Pre-halving events only (excludes events with `t_event ≥ 2025-12-15`, the corrected halving date per Wave-1 Reality Checker; equivalent to the v1 cutoff `t_event > 2025-12-14` but pinned explicitly against the verified halving date to avoid off-by-one ambiguity); a sample-period split testing whether the post-halving regime is materially different.

### 7.4 Bittensor halving treatment (1 specification, mandatory)

The **Dec 15 2025** Bittensor halving (corrected from v1's "Dec 14 2025" per Wave-1 Reality Checker verification of the canonical halving date) is the largest known non-event-set shock in the sample window. Maymin (2026) documents it cut the cross-subnet size premium from 1.17% → 0.51% (p=0.044). The halving is treated as follows:

- **Primary specification (§5):** events with primary event window overlapping the halving date `[2025-12-14, 2025-12-18]` (covering −1 to +3 trading days around **2025-12-15**) are *retained* in `E` but with a halving-window dummy added to the market-model regression (estimation window) for any event whose pre-event estimation window includes the halving date. This is a control, not an exclusion.
- **R-H1 (this robustness specification):** events with primary event window overlapping the halving date `[2025-12-14, 2025-12-18]` are *excluded* from `E`, and the cross-sectional t-test is recomputed on the reduced sample. This isolates whether the halving treatment in the primary specification is materially driving the result.

If the realized event count after R-H1 exclusion drops below `N_MIN_EVENTS = 8`, R-H1 is reported as "underpowered, excluded from the AGREE/DISAGREE count" and `N_robustness` is decremented (path 1 of the three admitted decrement paths enumerated in §3; the post-decrement denominator is computed per the §3 table).

**Halving-control sensitivity sub-section (mandatory in Phase-4 memo when R-H1 is decremented).** If R-H1 is decremented (excluded for underpower), the §8 verdict matrix is unchanged but the Phase-4 memo MUST include a "halving-control sensitivity" sub-section explicitly stating that:
1. The halving treatment in the primary specification is supported only by the in-regression halving-window dummy variable, NOT by an event-exclusion robustness corroboration.
2. The verdict's robustness to alternative halving controls is therefore unverified at this sample size.
3. The additional events that would be needed to support an R-H1 corroboration in a P1.1 follow-up are explicitly named (e.g., "five additional Anthropic / OpenAI events post-2026-04-27 with primary windows non-overlapping `[2025-12-14, 2025-12-18]` would restore R-H1's power above N_MIN_EVENTS").

This memo requirement is binding regardless of the primary verdict and may not be omitted on the grounds that the verdict is FAIL or INDETERMINATE.

### 7.5 Nov 2025 Taoflow regime change (1 specification, conditional)

The Nov 2025 Taoflow flow-based emission redesign restructured cross-subnet emission allocation. Per bridge-research §2.1, pre-November and post-November SN18 emissions are not directly comparable.

- **R-T1:** events with `t_event < 2025-11-15` (a pre-registered cutoff that places the regime change boundary at mid-November) are excluded; the cross-sectional t-test is recomputed on the post-Taoflow-only sample.
- If the realized post-Taoflow event count is `< N_MIN_EVENTS = 8`, R-T1 is reported as "underpowered, excluded from the AGREE/DISAGREE count" and `N_robustness` is decremented (path 2 of the three admitted decrement paths enumerated in §3; subject to the same ban-on-tuning rule as §7.4).

**Taoflow-control sensitivity sub-section (mandatory in Phase-4 memo when R-T1 is decremented).** If R-T1 is decremented (excluded for underpower), the §8 verdict matrix is unchanged but the Phase-4 memo MUST include a "Taoflow-regime sensitivity" sub-section explicitly stating that:
1. The Taoflow regime-change treatment in the primary specification is supported only by the implicit assumption that pre- and post-Nov-2025 SN18 emissions enter the market-model regression on equal footing, NOT by an explicit regime-split robustness corroboration.
2. The verdict's robustness to the Taoflow regime change is therefore unverified at this sample size.
3. The additional post-2025-11-15 events that would be needed to support an R-T1 corroboration in a P1.1 follow-up are explicitly named (recompute against realized event distribution at memo authoring time).

This memo requirement is binding regardless of the primary verdict.

### 7.6 Cross-provider joint-window treatment (1 specification)

Per §4.1 rule 5, cross-provider same-day events are flagged for joint-window treatment. R-J1: events flagged as cross-provider same-day are merged into composite events (cross-provider variant of the same-day same-provider merge rule); the cross-sectional t-test is recomputed on the merged-event sample. Tests whether near-simultaneous Anthropic + OpenAI announcements are causing event-clustering bias in the primary.

**Degenerate-case rule (hard-pinned per Wave-1 NB4).** If the realized count of cross-provider same-day events is zero, R-J1 is reported as **"no cross-provider clustering observed; spec is identical to primary"** and is excluded from the AGREE / DISAGREE count; `N_robustness` is decremented by 1 (path 3 of the three admitted decrement paths enumerated in §3). This degenerate case is a likely outcome — Anthropic and OpenAI typically space major announcements deliberately — and pre-committing the rule here prevents any post-data temptation to either (a) silently inflate the AGREE numerator by claiming R-J1 trivially "agrees" because it equals primary, or (b) post-hoc widen the same-day clustering window to manufacture a non-degenerate R-J1.

### 7.7 Falsification placebo (1 specification, mandatory)

R-F1: replace the realized event dates in `E` with `|E|` random dates drawn uniformly from the §4.2 window, excluding any date within ±5 trading days of any realized event. Recompute the cross-sectional t-test; this should *not* reject H₀ at α_robustness. R-F1 entering the AGREE bucket (i.e., its placebo-test rejecting H₀) is itself a red flag and triggers a HALT-disposition memo per §9 regardless of the primary verdict.

### 7.8 N_robustness summary

`N_robustness = 3 (windows) + 3 (controls) + 3 (sub-samples) + 1 (halving R-H1) + 1 (Taoflow R-T1) + 1 (cross-provider R-J1) + 1 (placebo R-F1) = 13` (nominal).

`N_robustness` may be decremented at runtime ONLY by the three pre-committed paths exhaustively enumerated in §3 (R-H1 underpower, R-T1 underpower, R-J1 degenerate cross-provider count). The admissible runtime values are `N_robustness ∈ {10, 11, 12, 13}`; the AGREE / DISAGREE / MIXED integer thresholds at each value are pinned in the §3 table. No other decrement path is admitted; any impulse to decrement on any other ground triggers a HALT-disposition memo per §9.

---

## §8 Verdict-decision tree

The verdict-decision tree maps the 3 × 3 outcome cube `(primary verdict, robustness consistency) ∈ {PASS-eligible, FAIL-eligible} × {AGREE, MIXED, DISAGREE}` to one of `{PASS, FAIL, INDETERMINATE}`.

A primary outcome is **PASS-eligible** if `|t_primary| ≥ t_crit(|E|−1, α_primary, two-sided)` per §6; otherwise it is **FAIL-eligible**. Robustness consistency is computed per §3 from the §7 robustness specifications. The cross-product matrix is:

| Primary       | Robustness | Verdict        | Justification |
|---------------|------------|----------------|---------------|
| PASS-eligible | AGREE      | **PASS**       | Signal detected, robustness confirms. The bar designed by this spec. |
| PASS-eligible | MIXED      | **INDETERMINATE** | Default per §3. Tie-break NOT pre-committed (see §8.1 for the decision against a tie-break). |
| PASS-eligible | DISAGREE   | **INDETERMINATE** | The robustness perturbations contradict the primary. Per §3, this is unsafe to escalate. NEVER downgraded to PASS. |
| FAIL-eligible | AGREE      | **FAIL**       | No signal in primary; robustness confirms no signal. |
| FAIL-eligible | MIXED      | **FAIL**       | No signal in primary; robustness shows internal disagreement but not enough to support a PASS. FAIL stands. |
| FAIL-eligible | DISAGREE   | **INDETERMINATE** | Primary shows no signal but at least one robustness family contradicts (i.e., robustness rows reject H₀ even though primary doesn't). The contradiction is itself informative — possibly the primary specification is suboptimal. Escalate to memo with explicit "primary FAIL but robustness rejected" annotation. |

All 9 cells (3 × 3) are covered; the table has 6 rows because the matrix collapses (PASS-eligible × MIXED / DISAGREE both → INDETERMINATE; FAIL-eligible × AGREE / MIXED both → FAIL). The covered cells are:

- (PASS-elig, AGREE) → PASS
- (PASS-elig, MIXED) → INDETERMINATE
- (PASS-elig, DISAGREE) → INDETERMINATE
- (FAIL-elig, AGREE) → FAIL
- (FAIL-elig, MIXED) → FAIL
- (FAIL-elig, DISAGREE) → INDETERMINATE

**The matrix verdict is an intermediate output.** The §8.2 R-F1 placebo gate (asymmetric, per orchestrator resolution of D3) is a downstream adjustment layered on top of the matrix verdict before the verdict is finalized for §8.3 / §9 reporting. Specifically: PASS verdicts are subject to placebo-driven downgrade to INDETERMINATE; FAIL and INDETERMINATE verdicts are retained but annotated. See §8.2 for the full rule.

### 8.1 Tie-break rule for (PASS-eligible × MIXED): NOT pre-committed

The plan permits the spec to pre-commit a tie-break rule that would override the default INDETERMINATE for this cell. **This spec elects NOT to commit such a tie-break.** The economic justification: a MIXED robustness profile means 30%-70% of robustness specifications individually reject H₀ — i.e., the signal is fragile enough that some plausible robustness perturbation breaks it. Promoting such a result to PASS would amount to a PASS-with-asterisk that contradicts the substrate-cleanliness claim that motivates the study (§1: SN18 is supposed to be cleaner than the broad basket). If the substrate is truly clean, the robustness profile should be AGREE. Allowing a MIXED result to PASS would silently relax the bar that the entire study was set up to clear. INDETERMINATE is the honest verdict for this cell, escalating to memo with a recommendation that the additional robustness specifications resolving the disagreement be identified for a P2 or revised-P1 follow-up.

### 8.2 R-F1 placebo gate (asymmetric — orchestrator-resolved)

If R-F1 (the falsification placebo per §7.7) individually rejects H₀ at α_robustness = 0.05 — i.e., random event dates produce a "signal" comparable to the realized events — the verdict is adjusted **asymmetrically by primary verdict class**, per the orchestrator's resolution of the cross-reviewer disagreement on D3 (the v1 symmetric-downgrade rule was illogical because downgrading a FAIL on placebo rejection treats false-positive bias in the machinery as if it weakened the FAIL — but a FAIL produced *despite* false-positive bias is *stronger* evidence against signal, not weaker):

(a) **Any PASS verdict is automatically downgraded to INDETERMINATE.** The apparent signal in the realized event set is suspect because the placebo demonstrates the machinery produces signal on noise; the realized-event signal cannot be cleanly attributed to the events.

(b) **Any FAIL verdict is RETAINED but flagged in the Phase-4 memo with a placebo-rejection annotation.** Failure to reject H₀ on the realized event set despite biased-toward-false-positive machinery is *stronger* evidence against signal than a clean FAIL, not weaker. The annotation must read: "Verdict: FAIL. Placebo gate (R-F1) rejected H₀ at α_robustness = 0.05, indicating the test machinery exhibits false-positive bias in this sample. The primary's failure to reject H₀ despite this bias strengthens the substantive interpretation that the channel is not detectable at this sample size and specification."

**(b.i) Joint qualifier when R-H1 or R-T1 is decremented (binding).** If R-H1 (per §7.4) or R-T1 (per §7.5) was decremented for underpower, the §8.2(b) "strengthened" annotation is *qualified* by the §7.4/§7.5 sensitivity sub-sections: the FAIL is strengthened against signal-existence ONLY for the regime contexts in which the primary specification's regime controls (halving-window dummy; Taoflow-implicit) are themselves credible. The Phase-4 memo MUST jointly resolve the §8.2(b) and §7.4/§7.5 language by appending the explicit sentence: *"FAIL is consistent with EITHER (a) no detectable channel exists OR (b) a detectable channel exists but is confounded by the [halving / Taoflow] regime shock that R-H1/R-T1 was unable to test at this sample size."* Promoting the §8.2(b) "strengthened" framing without this qualification when R-H1 or R-T1 is decremented is anti-fishing-banned under §9.

(c) **Any INDETERMINATE verdict is RETAINED with the same placebo-rejection annotation.** The placebo rejection neither rescues nor strengthens an INDETERMINATE; it is reported transparently and the diagnostic follow-up is escalated.

In all three cases (a, b, c) a HALT-disposition memo is required per §9 documenting the placebo rejection, naming the suspected source of false-positive bias (e.g., overlapping estimation windows across events, autocorrelation in α_18 returns not absorbed by the controls, structural break the market model fails to neutralize), and proposing diagnostic follow-up (e.g., re-fit market model with HAC errors at adjusted lag length, run R-F1 with a stratified-by-month placebo draw rather than uniform draw).

### 8.3 N_MIN_EVENTS shortfall

If the realized event count `|E|` after Phase 1 + Phase 2 is `< N_MIN_EVENTS = 8` (per §4.3), the verdict is **NEITHER PASS, FAIL, NOR INDETERMINATE** — the prototype is reported as `SUBSTRATE_TOO_YOUNG` and the orchestrator dispatches the spec amendment per §4.3. This is a substantively different verdict because it does not reject the hypothesis that the channel exists; it reports that the substrate is not yet old enough to test the hypothesis at the spec-pinned power.

---

## §9 Anti-fishing invariants (immutable)

These invariants carry forward the Phase-A.0 anti-fishing discipline (`feedback_pathological_halt_anti_fishing_checkpoint`) into P1 and govern every downstream artifact in the implementation plan.

1. **No threshold tuning post-data.** The α_primary = 0.0167, α_robustness = 0.05, the 70%/30% AGREE/DISAGREE thresholds, the N_MIN_EVENTS = 8, the t_crit formula, and every numeric threshold in this spec are immutable post-data. Any impulse to tune them after observing results triggers a HALT-disposition memo before any revision lands.

2. **No event-set re-curation post-data.** The §4.1 eligibility criteria are mechanical and verifiable from source URLs alone. Once Phase 1 produces the event panel, no event may be added or removed except via the 2-wave spec amendment process (Task 0.2 pattern, applied to the amendment). "Looks-like-an-outlier" is *not* a valid removal criterion.

3. **No methodology change post-data.** The §5 methodology (window, AR formula, control series, test statistic, multiple-testing correction) is immutable post-data. The §7 robustness enumeration is similarly immutable. Adding a robustness check after observing the primary result would be spec-leakage; deleting one would be cherry-picking. Both are banned.

4. **HALT-disposition required for any tuning impulse.** If during Phase 3 / Phase 4 any specialist (Analytics Reporter, Reality Checker, Code Reviewer, Senior Developer, or orchestrator) recognizes an impulse to tune a threshold, re-curate an event, or change a methodology choice in response to observed data, the impulse triggers a HALT and a written disposition memo per the Phase-A.0 pattern. The memo records (a) the impulse, (b) the data trigger, (c) the user-enumerated pivot options, (d) the chosen pivot, and (e) the CORRECTIONS-block annotation in the spec amendment. No silent threshold tuning is admissible under any circumstance.

5. **Spec sha256 governs all downstream artifacts.** Once Task 0.3 computes the sha256 of this spec and records it in the frontmatter `decision_hash` field, every downstream artifact (notebooks, memo, gate_verdict.json, final disposition) quotes that hash in its own frontmatter / metadata. Any artifact whose quoted hash does not match the file content's hash at audit time is a defective artifact.

6. **3-way memo review regardless of verdict.** Per `feedback_implementation_review_agents`, the Phase 4 memo undergoes Code Reviewer + Reality Checker + Senior Developer review *regardless* of whether the verdict is PASS, FAIL, or INDETERMINATE. PASS is not a free pass; FAIL is not "no need to verify"; INDETERMINATE is not "skip review and write a punt memo".

7. **Phase-A.0 pattern carries forward.** The 14-row resolution matrix, CORRECTIONS-block discipline, and HALT-then-disposition workflow that governed the Phase-A.0 Y₃ × X_d work (per project memory `project_phase_a0_remittance_execution_state` and successors) apply mutatis mutandis to this study. Any deviation from these patterns is itself a defect requiring 2-wave review.

---

## References

1. Maymin, P. Z. (2026). *Common Risk Factors in Decentralized AI Subnets.* arXiv:2603.29751. https://arxiv.org/abs/2603.29751 — methodology baseline; Dec 2025 halving 1.17% → 0.51% size-premium documentation. Verified 2026-04-27 via `mcp__arxiv__get_abstract`.

2. Lui, E. & Sun, J. (2025). *Bittensor Protocol: The Bitcoin in Decentralized AI? A Critical and Empirical Analysis.* arXiv:2507.02951. https://arxiv.org/abs/2507.02951 — concentration analysis across 64 subnets; reflexivity hazard in subnet-level signals.

3. Brown, S. J. & Warner, J. B. (1985). "Using daily stock returns: The case of event studies." *Journal of Financial Economics* 14(1), 3-31. — cross-sectional event-study t-test methodology.

4. Celeny, D. et al. (2024). *Prioritizing Investments in Cybersecurity: Empirical Evidence from an Event Study on the Determinants of Cyberattack Costs.* arXiv:2402.04773. https://arxiv.org/abs/2402.04773 — cross-sectional event-induced variance corrections cited in the **signal-research bibliography** at `contracts/.scratch/2026-04-27-onchain-proxies-for-proprietary-ai-cost.md` (corrected from v1's mis-attribution to the bridge-research bibliography per Wave-1 Reality Checker).

5. Cortex.t / SN18 project documentation. **https://cortex-t.ai/docs** (verified accessible 2026-04-27 by Wave-1 Reality Checker) — verbatim quote on OpenAI API key requirement; backend support for gpt-3.5-turbo, gpt-4, gemini, claude3. **CORRECTIONS NOTE (v2):** the bridge-research report (`contracts/.scratch/2026-04-27-bittensor-claude-bridges-prototype-modeling.md`) gives the GitHub URL `https://github.com/corcel-api/cortex.t` for the same quote; that URL returned 404 at Wave-1 verification time and is stale. The canonical, verifiable source is `https://cortex-t.ai/docs`.

6. Bittensor Foundation. *Emissions and Taoflow.* https://docs.learnbittensor.org/learn/emissions — Taoflow Nov 2025 regime change; halving cadence. The first dTAO halving date is **2025-12-15** (corrected from v1's "2025-12-14" per Wave-1 Reality Checker verification of the canonical halving date; the bridge-research report's "Dec 14 2025" citation is also stale and is treated as a known-stale source for halving-date purposes).

7. Bridge-research source: `contracts/.scratch/2026-04-27-bittensor-claude-bridges-prototype-modeling.md` — P1 design source; substrate hierarchy; ~10-12 dated event count estimate; 8-10 events for directional inference.

8. Prior signal-research source: `contracts/.scratch/2026-04-27-onchain-proxies-for-proprietary-ai-cost.md` — broad-basket failure mode (70-95% non-AI-policy variance); zero-detected-Anthropic-signal in 6 attempts.

9. P1 implementation plan: `contracts/docs/superpowers/plans/2026-04-27-p1-sn18-event-study-implementation.md` — task-by-task implementation plan governed by this spec.

10. Project memory `feedback_pathological_halt_anti_fishing_checkpoint` — HALT-disposition discipline carried forward from Phase-A.0.
