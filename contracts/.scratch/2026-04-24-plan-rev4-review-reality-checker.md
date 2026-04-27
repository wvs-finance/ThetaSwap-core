# Rev-4 Plan Review — Reality Checker

**Target:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `dded7d637`
**Diff base:** `726ce8f74`
**Date:** 2026-04-24
**Reviewer:** Reality Checker (independent; no coordination with CR/TW)

## 1. Verdict

**NEEDS WORK.** Rev-4's core idea (escalate to a filter-design phase rather than debug Rev-1.1.1 scalar/vector semantics) is empirically well-grounded — the roundtripping evidence is real (verified below) and the cCOP power-user/treasury concentration is documented in three prior-research artifacts. However, the M objective as written is arithmetically incorrect ([−0.75, +1], not [−1, +1]), the N=6 small-sample behavior of the component floors is statistically weak, and the search-space cardinality creates a family-wise error the "non-stop" policy does not address.

## 2. Feasibility table

| ID | Claim | Empirical grounding check | Pass/Fail | Required fix |
|----|-------|---------------------------|-----------|--------------|
| RC-P1 | Top single-day events are arbitrage roundtrips (e.g., 2025-09-18 in=$429,592.26, out=$429,592.27 balanced to 7 dp) | Verified via `pd.read_csv(copm_ccop_daily_flow.csv)` + nlargest: 2025-09-18 `ccop_usdt_inflow_usd=429592.258535`, `ccop_usdt_outflow_usd=429592.270090` — 7-decimal match confirmed. Top 10 days show 6 events with \|in−out\|/max < 0.01. | PASS | None — trigger evidence is real |
| RC-P2 | Task 11.F background web-search can identify confounding events on top-30 peak days | cCOP has ~$75k total circulation (per `CELO_ECOSYSTEM_USERS.md:153` and `:260`); 5+ of the top 10 days exceed 5× total circulation. This is consistent with single-entity treasury operations, which by nature have **no public-news footprint**. Realistic hit-rate from WebSearch: 20-40% of top-30 dates (migration 2026-01-25, MiniPay 2025-11-19 are documented; rest are likely private). | FAIL (partial) | Pre-register expected sparse-evidence outcome. The `RESEARCH_SPARSE_ESCALATE > 50% sparse` threshold is too loose given the expected 60-80% sparse rate. Tighten to "escalate to user if >30% of top-30 have no public documentation AND the event is >$100k" so dominant-treasury events trigger re-scope rather than proceeding with blind dummies. |
| RC-P3 | Rev-4 non-stop filter iteration produces an argmax filter usable as Rev-2 primary X | With BanRep quarterly N=5 usable overlap quarters (not N=7 as Task 11.C claims; cCOP launched 2024-10-31, so 2024Q3 is pre-sample and 2026Q1 is past BanRep's 2026-03-06 last-cargue), ρ_Pearson and Kendall τ are estimable but wildly unstable: at N=5, a single quarter's flip can move ρ from +0.8 to −0.2. | FAIL | Document actual N (likely 5, possibly 6), not N=7. Enlarge BanRep series by pulling monthly-equivalent-via-linear-distribution OR accept that the "non-stop" phase is running on a 5-obs test whose 90% CI under H0 spans essentially all of [−1, +1]. |
| RC-P4 | Phase 1.5.5 completes "before Phase 2b" (plan L490: Task 12 implementation blocked on 11.J) | 5 new tasks (F/G/H/I/J) where H is a non-stop enumeration, I is a full skill re-invocation, J is a 3-way review with Rule 13 up to 3 cycles = realistically 5–10 business days. Even optimistic parallelism of F‖G ahead of H, and Task 12 failing-tests-only in parallel, this is ≥1 week. | PASS-WITH-NOTE | Call out the ≥5-day expected duration in the Rev-4 bullet so downstream phases' date estimates are adjusted. |
| RC-P5 | cCOP large-day events are real (not double-counting mint+transfer+burn) | Loader docstring at `contracts/scripts/dune_onchain_flow_fetcher.py:35-51` distinguishes mint (`from=0x0`) and burn (`to=0x0`) from user-side transfers; `ccop_usdt_inflow_usd` explicitly *excludes* mints (L47-48). Double-counting risk is low. However the magnitudes ($400-800k/day vs $75k total circulation) imply **very high velocity** — consistent with the same wallet routing repeatedly through the Mento broker, not distinct inflows. | PASS (no double-count) but CONCERN | No code fix needed; but Rev-2 spec §4.1 must document that "inflow_usd" includes all intraday re-entries of the same balance, i.e. it is a velocity metric not a stock. |
| RC-P6 | Pre-commitment via `git log --follow` is sufficient audit trail | The plan states "Commit the pre-reg BEFORE Step 2" (Task 11.H Step 1). `git log` IS tamper-evident for additions, but `git commit --amend` + `git push --force` on a feature branch CAN rewrite history without detection unless the remote disables force-push. The plan has no Merkle-log or signed-commit requirement. | FAIL | Add a Step 1.5: "immediately after committing the pre-reg, push to `origin` (NOT upstream, per `feedback_push_origin_not_upstream.md`) and record the remote-SHA in the `.scratch` file." Remote-push + SHA citation makes tampering detectable by external observer. |
| RC-P7 | Task 11.I dependency on 11.H argmax / Task 12 parallelism (plan L490) | If 11.H returns `M_THRESHOLD_UNMET`, 11.I halts. Plan L490 says "Phase 2b Task 12 failing-test authoring may begin in parallel with Phase 1.5.5." But the failing test for Task 12 (panel extension) was itself pinned to the Rev-1.1.1 spec's primary-X definition — which is now superseded. If Rev-2 redefines primary X (expected), Task 12's failing test will need to be re-authored. | FAIL | Clarify in Rev-4 bullet: "Task 12's parallel execution is limited to the decision-hash-extension plumbing that is spec-independent; any failing-test authoring that encodes a specific primary-X channel vocabulary MUST wait for Task 11.J." |

## 3. Statistical-integrity findings (on M objective)

Three separate defects in the objective as stated at Task 11.H Step 1:

**Bounded?** — plan text: "M ∈ [−1, +1]". **FALSE.** Because `sign_concordance = fraction of quarters where sign(Δx)·sign(Δy) = +1` is in [0, 1] (a frequency), not [−1, +1] (a rank correlation), the composite with equal weights 0.25 yields:
- Max: 0.25·1 + 0.25·1 + 0.25·1 + 0.25·1 = **+1.0**
- Min: 0.25·(−1) + 0.25·(−1) + 0.25·0 + 0.25·(−1) = **−0.75**

So M ∈ [−0.75, +1.0], **asymmetric**. This is not merely a typo — it means the threshold M ≥ 0.70 is closer to the maximum than to the midpoint of the feasible range, not a 85th-percentile cut as the "0.70 on [−1, +1]" framing suggests. **Required fix:** redefine sign_concordance as `2·fraction − 1 ∈ [−1, +1]` (so 50% concordance maps to M-component = 0, full agreement = +1, full anti-agreement = −1) OR keep the current definition but rewrite the bound to [−0.75, +1.0] and recalibrate the threshold.

**Symmetric under argument swap?** — plan claim: symmetric. **TRUE but not for the reason stated.** Pearson/Spearman/Kendall are symmetric; `sign(Δx)·sign(Δy) = sign(Δy)·sign(Δx)` makes sign_concordance symmetric. No action needed on this claim (but the defect above still applies).

**Small-N behavior at N=6 (or more accurately N=5) under H₀:** Monte Carlo 100k trials at N=6 with independent Gaussian draws:
- P(ρ_Pearson ≥ 0.6 | H₀) = **10.4%** — so a single-filter pass has >10% false-positive rate at the component-floor threshold
- P(sign_concord ≥ 0.6 | H₀) = **50.2%** — the sign floor is effectively a coin-flip at N=5 deltas (3-of-5 majority)
- P(ρ_P ≥ 0.6 AND sign ≥ 0.6 | H₀) = **9.7%** — joint floors do not save it
- P(composite M ≥ 0.70 | H₀) = **5.1%** — at the nominal-α boundary

So the "pre-committed" M ≥ 0.70 gate is effectively a 5% single-test at N=6 before any multiple-testing correction, and individual component floors are 10% and 50% — **not statistically defensible as "rigorous"**. Consider either (i) increasing N by interpolating BanRep to monthly and comparing quarterly-aggregated-monthly-interpolation, or (ii) raising M_threshold to 0.85+ (which under H₀ has P ≈ 0.3% at N=6 per an extended MC).

## 4. Multiple-testing audit

Enumerating Task 11.G Step 2's candidate families:
- (a) 12 address-exclusion filters
- (b) 4 tx-size filters
- (c) 3 roundtrip filters
- (d) 4 event-window filters
- (e) 4 entropy filters
- (f) composite conjunctions: at minimum 12·4·3 = **144** combinations (the plan literally says "try the conjunction …")

**Lower bound on |F|: 27 singletons + 144 composites = 171 filters.**

Under H₀ (filter has no true similarity) at α=0.05 per test:
- Bonferroni-adjusted α_per_test = 0.05/171 ≈ **0.00029**
- Unadjusted FWER over 171 tests ≈ **1 − (0.95)^171 ≈ 99.98%** — essentially guaranteed that at least one filter will spuriously pass M ≥ 0.70 even under pure noise.

**Rev-4's "anti-fishing guard" (plan L418, Task 11.H anti-fishing note) addresses the specification-search problem — pre-committing F, M, and weights — but does NOT control for multiple comparisons across |F|=171 tests.** The non-stop enumeration over a 171-member F is precisely the multiple-comparisons problem that pre-commitment does not solve; pre-commitment solves p-hacking (changing tests after seeing data), not maximum-selection bias (picking the max of many).

**Required fix:** Add to Task 11.H Step 1 pre-commitment: "the argmax filter is reported as a point estimate, NOT as a test of H₀; the Rev-2 gate for whether the argmax filter's series is usable as primary X is a separate hold-out test on the 2026Q1+ out-of-sample BanRep quarters once available." Alternatively, require the argmax M ≥ M_threshold at a **Bonferroni-adjusted** component level (ρ_Pearson ≥ 0.85 instead of ≥ 0.6, etc.) to preserve 5% FWER over |F|=171. Without one of these, Task 11.I consumes a statistically-selected filter and the Rev-2 spec inherits a survivorship bias comparable to the specification-search pathology the FX-vol-CPI exercise deliberately avoided.

## Summary (3 sentences)

Rev-4's escalation is empirically justified — the roundtripping evidence in top-day flows is genuine and cCOP's power-user concentration is well-documented — but the proposed M objective is arithmetically mis-bounded ([−0.75, +1], not [−1, +1]), the N=5-or-6 small-sample behavior makes the component floors statistically toothless (P(ρ≥0.6|H₀)≈10%, P(sign≥0.6|H₀)≈50%), and the non-stop enumeration over a |F|≥171 search space creates a family-wise error rate near 100% that pre-commitment of M/weights does NOT address. The plan must (a) redefine sign_concordance to be in [−1, +1], (b) disclose and correct the N=5 actual overlap rather than claim N=7, (c) either raise M_threshold to ~0.85 for Bonferroni-adjusted single-filter honesty or reframe argmax as a point estimate requiring out-of-sample validation on 2026Q1 BanRep when available. These fixes are structural, not wording-only, and trigger a new three-way review cycle before Task 11.F dispatches.

**Verdict: NEEDS WORK.**
