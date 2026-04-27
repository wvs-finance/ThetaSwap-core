# Reality Checker Rev 2 Review — Tier 1 Feasibility Filter

**Spec reviewed:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` (Rev 2)
**Prior review:** `contracts/.scratch/2026-04-14-tier1-review-reality-checker.md`
**Reviewer:** Reality Checker
**Date:** 2026-04-14

## OVERALL VERDICT: NEEDS WORK

Three of five Rev 1 BLOCKs (#3 liquidity, #2 proxy tiers, #8 DISCONFIRMED) are closed in form. Two (#9 cCOP self-refutation, #7 success criterion) have structural fixes but retain residual attack surface. More damaging: the fresh Rev 2 angles expose that the spec's expected outcome, by the spec's own prior-calibration text, is almost certainly `CONFIRMED_NO_INFRASTRUCTURE` or `NO_LITERATURE_SUPPORT` on both channels — meaning the 1-3 day exercise is **predictably** going to spit out a gate to Tier 1b (in-house regression), which is the same terminus Rev 1 would have hit for different reasons. The feasibility filter has been expanded to look harder but the outcome space has not been meaningfully changed.

The fixes are not theater, but the exercise they gate is close to theater given its own priors.

---

## Part 1 — Rev 1 BLOCKs: do the fixes close the attack surface?

### BLOCK #3 — "liquidity sufficient" → §10 numeric gates — CLOSED

§10 now has (a)-(d) with $50K 30-day avg notional and $5K 1%-slip round-trip, plus a `△` simulation-only tier at $5K-$50K. Each cell in §9 must cite 2026-04-02 source and snapshot date. Attack surface ("searcher decides liquidity is sufficient") is closed for the numeric part.

**Residual attack — threshold arbitrariness:** the $50K / $5K numbers have a one-line rationale ("1% daily move produces < $500 bid-cost, economically indistinguishable from noise under typical Angstrom bid discretization") but no tie to a concrete Angstrom bid-discretization figure. An executor under pressure can argue "$45K 30-day is essentially $50K" and the spec has no tie-break mechanism. This is NOT a reopening of the BLOCK — the gate is objective enough to refuse — but it is a **soft-spot** the second reader should be directed to challenge. Recommend: add "round half up to nearest $5K from raw computation; no rounding at the boundary; boundary ties fail closed to `△`."

### BLOCK #9 — cCOP self-refutation → §10(d) symmetric gate — PARTIALLY CLOSED

§10(d) says "the cCOP side of the pair ALSO supports criteria (a)–(c)." §3 q3 rephrased with "symmetric gate — thin cCOP defeats any X wrapper." §11 decision tree step 3 correctly emits `CONFIRMED_NO_INFRASTRUCTURE` when no row is `✓`.

**Residual attack — where does the "cCOP side" pass (a)-(c)?** §2 already stipulates secondary Uniswap V3 cCOP/USDT peaks near $7K/day. That is below $5K in (c)? Above $5K but below $50K? Either way, EVERY row in §9 fails (d) because the cCOP side cannot clear (b) on any known venue. This is fresh-angle #5 below, and it means §10(d) is not just a gate — it is a guaranteed-fail-closed. The BLOCK is closed in the sense that the verdict-generation logic is correct. It is NOT closed in the sense that the spec anticipates the predictable outcome. The spec writes as if (d) will sometimes pass; evidence in §2 says it almost never will.

Status: mechanically closed, but the spec's framing understates what (d) actually does.

### BLOCK #8 — DISCONFIRMED missing → §11 added — CLOSED IN FORM, DEAD IN PRACTICE

§11 defines `DISCONFIRMED` requiring "≥1 credible paper with specification in Tier A or B reporting β ≈ 0 or adj-R² < 0.05 with tight CIs." Wired into global roll-up as `RETIRE_THESIS`.

**Residual attack — publication bias:** null-result FX-vol regressions on EM CPI surprises are publication-biased OUT of the literature. Papers that found null typically got rejected or repurposed. Realistic probability of a Tier-A-or-B-with-tight-CI null on Colombia ERPT-on-vol: <5%. Consequence: `DISCONFIRMED` fires approximately never; `RETIRE_THESIS` is a ghost terminal; `PIVOT_NEEDED` absorbs ~99% of the "literature doesn't support" mass. The verdict exists on paper but carries no decision weight in the expected-outcome distribution.

This is not a spec bug — you can't legislate publication bias away. But it means Rev 1's original concern (verdicts have no load-bearing negative) is preserved: the literature cannot disconfirm in practice; it can only fail to confirm. The pivot protocol is therefore decorative.

Recommend: add one line to §11 Prior Calibration acknowledging this: "Publication bias against null ERPT-on-vol results for EM currencies means `DISCONFIRMED` has a low expected firing rate; `NO_LITERATURE_SUPPORT` is the modal literature-negative verdict."

### BLOCK #7 — §15 gameable → §18 outcome-based — CLOSED

§18(a) now says ≥3-of-4 query patterns per channel per source; skipping a non-arxiv source downgrades the channel's verdict by one tier AND requires a timestamped hard block. §18(b) requires ≥5 total citations OR signed exhaustive-search failure OR a `DISCONFIRMED` shortcut. §18(c) kills `—` placeholders. §18(d) requires per-cell citations. §18(f) requires second-reader sign-off.

Attack surface (trap-door "skip with documented reason") is closed. The criterion now binds on outputs, not on process hygiene.

**Residual attack — §18(f) unpowered:** fresh-angle #6 below. Second reader is not named. Any reader works including the searcher's LLM twin, which defeats the countermeasure against searcher-bias-toward-CONFIRMED (§19 names this risk explicitly). Recommend: constrain second reader to "a human reviewer distinct from the searcher, identified by name in §13 deliverable section 9 before deliverable is considered complete."

### BLOCK #2 — proxy-closeness unregistered → §7 Tiers A/B/C/D — CLOSED

§7 registers Tier A (exact), Tier B (same channel, weaker construction), Tier C (panel w/ Colombia coefficient separately), Tier D (non-COP EM peer), NOT STUDIED. §11 verdicts cite the tier; §12 handoff columns require per-citation tier. §18(e) requires auditability.

Attack surface (searcher stretches proxy during execution) is closed. The tier is pre-registered and load-bearing in the verdict.

**Residual attack — tier downgrade asymmetry:** a Tier-D-only hit still can fire `CONFIRMED` via §11 step 2 ("≥1 citation meets τ_lit ≥ 0.10"). Tier D is non-COP; Colombia may not generalize. Recommend: §11 step 2 refinement: `CONFIRMED` at Tier D requires a second Tier-D hit with same sign and overlapping CIs, or downgrade to `PARTIAL_SUPPORT`. (This is on the edge of BLOCK; flagging as strong FLAG.)

---

## Part 2 — Fresh Rev 2 angles

### Angle 1 — $50K / $5K threshold arbitrariness — FLAG

Thresholds are defensibly chosen (bid-cost vs noise argument) but not tied to a named Angstrom parameter. An executor under time pressure can argue $45K is close. Mitigation above: fail-closed rounding rule.

### Angle 2 — DISCONFIRMED verdict is publication-biased to never fire — FLAG (confirms BLOCK #8 residual)

See BLOCK #8 above. Pivot protocol is dead weight in the expected outcome distribution. Not a bug, but the spec should acknowledge it.

### Angle 3 — Two channels in 1-3 days, time estimate — FLAG

Rev 1 had "one day" for one channel, reviewed as underestimate, revised to 1-3 days. Rev 2 now covers **two** channels ($\pi$ and $C_{\text{remittance}}$) in the same 1-3 day window. Two channels with different literatures (ERPT/announcement-effect vs remittance-flow macroeconomics), different author seed sets (§6), different Spanish-language search terms — the honest estimate is 2-5 days, not 1-3. Hard cap of 3 days in §17 is not loosened to match scope expansion. This is a Rev-1-concern reintroduced.

Recommend: revise §17 low/typical/high to 1.5 / 3 / 5 days, or explicitly accept "channel $C_{\text{remittance}}$ will be less exhaustively covered than $\pi$."

### Angle 4 — Prior calibration admits the detour — FLAG, borderline BLOCK

§11 Prior Calibration:
> "`CONFIRMED` on either channel is the less-likely outcome and is not the success criterion — a crisp `NO_LITERATURE_SUPPORT` justifying Tier 1b is also a successful gate."

This is epistemically honest but operationally damning. If the expected outcome on both channels is `NO_LITERATURE_SUPPORT` → `PIVOT_NEEDED` → Tier 1b in-house regression, then Tier 1 is a 1-3 day ritual whose modal output was predictable at spec-writing time. The exercise's value is therefore ~purely in the 20-30% tail where literature actually confirms.

Expected-value check: is a 1-3 day search with ~25% hit rate on the confirming outcome worth the delay vs. going straight to Tier 1b? The spec does not do this tradeoff.

Recommend: §2 must explicitly justify the 1-3 day detour by citing one of:
- (i) the cost of running Tier 1b blind (no literature prior) is substantially greater than 3 days, OR
- (ii) a confirming citation at Tier A/B meaningfully reduces Tier 2's scoping work, OR
- (iii) the exercise surfaces a specification — counterparty currency, control set — that the executor cannot derive without the literature pass.

Without this, the spec is open to "theater" reading.

### Angle 5 — §10(b) $50K threshold vs cCOP reality — BLOCK

§2 establishes secondary Uniswap V3 cCOP/USDT peaks near **$7K/day** on $66-86K market cap. Mento vAMM is the primary venue but is not an LP-slippage venue (§0 glossary, §2 line 27). §10(d) requires the cCOP side to clear §10(b) ≥$50K 30-day average notional.

$7K/day peak (not average) × 30 days ≪ $50K average. The cCOP side **by the spec's own §2 evidence** cannot clear (d). Therefore EVERY pair in §9 → `✗` or at best `△`. §11 step 3 then fires `CONFIRMED_NO_INFRASTRUCTURE` for any literature hit, on any channel.

This is a structural short-circuit. The feasibility filter reduces to:
- If any literature hit at τ_lit ≥ 0.10 exists → `CONFIRMED_NO_INFRASTRUCTURE` → `PIVOT_NEEDED`
- If no literature hit → `NO_LITERATURE_SUPPORT` → `PIVOT_NEEDED`
- Either way → Tier 1b

The spec does not acknowledge this short-circuit. §11 Prior Calibration mentions `CONFIRMED`-unlikely but does not observe that even a literature hit cannot clear infrastructure. The 1-3 day literature work is disconnected from the infrastructure gate: infrastructure has already failed at spec-authoring time based on Rev 2's own §2 evidence.

Two legitimate responses:
- (A) Acknowledge the short-circuit, reframe Tier 1 as literature-only (drop §10(d), drop §9 infrastructure gate to Tier 2 prerequisite), saving 1-3 days of infrastructure-matrix work that is predetermined.
- (B) Keep the gate but add to §11 Prior Calibration: "Given 2026-04-02 evidence of cCOP thinness, §10(d) is expected to fail for all rows; the modal channel verdict is `CONFIRMED_NO_INFRASTRUCTURE` (on lit hits) or `NO_LITERATURE_SUPPORT` (absent hits); both roll up to `PIVOT_NEEDED`."

Escalating to BLOCK because the gate's predetermined failure is not acknowledged and the spec looks like it thinks the gate is live.

### Angle 6 — Second reader unspecified — BLOCK

§13 deliverable §9 requires "second-reader sign-off block." §18(f) requires "a second reader (distinct from the searcher)" who spot-checks ≥3 citations. §19 names searcher bias as a risk and points to §18(f) as the countermeasure.

Nowhere does the spec specify:
- Human vs. AI? If AI, is a second-instance LLM acceptable? (This is the exact scenario the risk is about.)
- Named ahead of time, or ad-hoc at deliverable close?
- Does the second reader need to be qualified in the domain (someone who can distinguish Tier B from Tier C) or is any reader OK?

As written, §18(f) is satisfied by the searcher asking a second Claude instance to spot-check. That is not a countermeasure; that is the failure mode with extra steps.

BLOCK. Recommend: "Second reader MUST be a human, named in §13 deliverable §1 header before search begins, with self-attested capacity to distinguish Tier A/B/C/D classification. Peer LLM review is disallowed for this criterion."

### Angle 7 — §16 "structurally current" → executor judgment — FLAG

§16 says "If inaccessible or stale beyond the threshold the executor's judgment allows, Tier 1 blocks pending re-audit." This is Rev 1's BLOCK #5 FLAG (staleness promotion) partially resolved (it IS in §16 as a dependency) but the "threshold the executor's judgment allows" phrasing **is** the discretion-hidden-in-prose pattern Rev 1 called out elsewhere.

What counts as structurally current? "Pools still exist on-chain" is one threshold; "30-day notional within 20% of 2026-04-02 snapshot" is another. Spec says neither.

Recommend: §16 replace "structurally current" with "pool contract addresses cited in the 2026-04-02 package still resolve on-chain AND at least one venue per row still reports non-zero 30-day notional." This is a pre-registered check the executor runs, not a judgment call.

### Angle 8 — Other smells

- **§15 "no paraphrased-rerunning of cited papers' regressions" is strict.** Good. But §11 tie-break on multiple ✓ counterparties uses "lowest confound density" — undefined. Confound density is the kind of measure a searcher hand-waves. Recommend: replace with "fewer controls reported in citation" or "citation reports robustness to global risk factor (VIX or equivalent)."

- **§10(c) 1% slippage / $5K round-trip:** slippage cost depends on fee tier not just liquidity. A $5K round-trip at 0.3% fee pays $30 in fees alone regardless of slippage. The spec conflates price impact with total cost. Recommend: rephrase as "$5K round-trip incurs price-impact ≤1%, excluding pool fee."

- **§18(b) citation count threshold:** ≥5 distinct citations in TOTAL across two channels. Two channels, five citations total → as few as 1 per channel with 3 on the other is compliant. A channel with 1 citation cannot credibly emit any verdict other than `NO_LITERATURE_SUPPORT`. Recommend: ≥3 per channel, or ≥5 total AND ≥2 per channel, or an explicit per-channel exhaustive-search failure statement.

- **§2 "the Celo governance proposal dated July 2025 requesting $3.3M for FX-market infrastructure confirms the gap"** — this evidence is 8-9 months old at execution time. Has the $3.3M been deployed? Has cCOP liquidity materially changed? §16's staleness check would catch this but the reference to "confirms the gap" reads as if the 2025 state is current. FLAG: anchor the evidence to 2026-04-02 audit, not the 2025 proposal.

- **τ_lit = 0.10 vs τ_op = 0.15 asymmetry:** §3 line 56 notes "in-sample literature adj-R² typically overstates out-of-sample." Reasonable. But in-sample vs out-of-sample gap in EM FX-vol regressions is often 30-50%, not 33% (0.15/0.10). A marginal 0.11 Tier-1 confirm could be out-of-sample 0.05-0.08. The provisional-confirm case is real. Rev 1 flagged this as NIT; Rev 2 did not tighten. Still a NIT but worth noting the gap is not conservative.

- **§11 tie-break hierarchy** lists "deepest 30-day notional" as the second tie-breaker. That is on the X side. The binding constraint per §10(d) and §2 is the cCOP side. Tie-break should surface "deepest 30-day notional on cCOP side of the pair" — which, given §2, is approximately constant across all rows (all go through the same thin cCOP venues). Effectively no tie-break. Recommend: swap tie-break 2 and 3.

---

## Summary

### What Rev 2 actually fixed

| Rev 1 BLOCK | Fix location | Status |
|---|---|---|
| #3 liquidity operational | §10(a)-(d) numeric gates | CLOSED (residual: threshold arbitrariness soft-spot) |
| #2 proxy tiers unregistered | §7 Tiers A/B/C/D | CLOSED (residual: Tier-D-only `CONFIRMED` allowed) |
| #8 DISCONFIRMED missing | §11 defined and wired | CLOSED in form, DEAD in practice (publication bias) |
| #7 gameable criterion | §18 outcome-based | CLOSED (residual: §18(f) second reader unpowered) |
| #9 cCOP self-refutation | §10(d) symmetric gate | MECHANICALLY CLOSED; spec under-acknowledges the gate is pre-failed |

### Fresh Rev 2 issues

| # | Issue | Severity | Where |
|---|---|---|---|
| 5 | cCOP side pre-fails §10(d); gate is predetermined per §2 evidence | BLOCK | §2, §10(d), §11 Prior Calibration |
| 6 | Second reader unspecified; LLM peer defeats searcher-bias countermeasure | BLOCK | §13, §18(f), §19 |
| 3 | 1-3 day estimate for two channels understates scope expansion | FLAG | §17 |
| 4 | Prior calibration admits detour; spec doesn't justify 1-3 day cost vs Tier 1b | FLAG | §2, §11 |
| 2 | DISCONFIRMED publication-biased to never fire; spec silent | FLAG | §11 Prior Calibration |
| 7 | §16 "structurally current" = hidden executor discretion | FLAG | §16 |
| 1 | $50K/$5K thresholds have no fail-closed rounding rule | NIT-FLAG | §10 |
| 8a | "Lowest confound density" tie-break undefined | NIT | §11 |
| 8b | $5K / 1% slippage conflates price-impact and fees | NIT | §10(c) |
| 8c | ≥5 total citations allows 1-4 per-channel imbalance | NIT | §18(b) |
| 8d | 2025 Celo proposal evidence presented as current | NIT | §2 |
| 8e | Tie-break hierarchy puts X-side liquidity above cCOP-side | NIT | §11 |

### Bottom line

Rev 1's five BLOCKs are formally addressed. Two residuals (#9 mechanical vs acknowledged, #7 second-reader identity) are re-raised as fresh BLOCKs (angles #5, #6). Angle #5 is the structural finding: the infrastructure gate has already failed per Rev 2's own §2 evidence on cCOP liquidity, which means the literature half of Tier 1 can confirm anything and the verdict still collapses to `PIVOT_NEEDED`/`CONFIRMED_NO_INFRASTRUCTURE`. The 1-3 day exercise therefore produces a predictable route to Tier 1b in the modal case; the confirming outcome is the ~20-30% tail.

Three legitimate paths forward:
- **A (scope shrink):** drop §9 infrastructure matrix and §10(d) from Tier 1, make infrastructure a Tier 2 prerequisite, run Tier 1 as literature-only in <1 day per channel.
- **B (acknowledge):** keep the structure, add Prior Calibration language explicitly stating the modal route is `PIVOT_NEEDED` due to cCOP infrastructure failure, justify the detour on Tier 2 scoping value.
- **C (pre-run the infrastructure gate):** spec-author declares at spec-write time that §10(d) fails given §2 evidence; Tier 1 skips §9 population and runs literature only; deliverable's infrastructure section is a one-line "per §2, all rows `✗`; see 2026-04-02 package for detail."

Re-review required after choosing a path and addressing BLOCK #6 (named human second reader).

The spec is not theater. The exercise it gates is adjacent to theater and the spec does not acknowledge this.
