---
artifact_kind: phase3_3way_review_disposition_memo
emit_timestamp_utc: 2026-05-06
parent_iteration_pin: dev-AI-cost Stage-1 simple-β
parent_memo_pin: contracts/.scratch/dev-ai-stage-1/output/MEMO.md (sha256 ed38e83fe4a365c0fa498f5ea61280b4e29b9f4eea938a552ccff6876c1d1a6f, 872 lines)
trigger: 3-way review surfaced spec-internal §5.5/§9.6 contradiction affecting verdict; SD BLOCK-3 + CR NIT-2 convergent flag on D-iii sign-AGREE qualifier
authority: feedback_pathological_halt_anti_fishing_checkpoint (HALT + disposition memo + ≥3 pivot options + user adjudication)
user_pick_2026_05_06: Option C (strict §5.5 reading + D-iii preservation as Phase-3 finding for future Section M iteration)
---

# Phase-3 3-way review disposition memo — D-iii spec-contradiction

## §1. Pathological state

The 3-way review (Code Reviewer + Reality Checker + Senior Developer) surfaced a load-bearing spec-internal contradiction between:

- **Spec §5.5 line 252 verbatim**: "The escalation suite is run if and only if §3.3 ESCALATE-trigger fires per §8 verdict tree; running it speculatively when the primary regression PASSes at §3.1 is anti-fishing-banned per §9.6 (escalation as pre-authorization, not post-hoc rescue)."

- **Spec §9.6 (per NB03 Trio 6 dispatch brief reading)**: "Escalation as pre-authorization, not post-hoc rescue. The §5.5 + §3.4 escalation suite was pre-authorized in this spec before any data was pulled. Framing escalation in the result memo as 'rescue' is anti-fishing-banned; the framing must be 'pre-pinned convex-payoff evidence test, ran whether or not mean-OLS passed'."

These are CONTRADICTORY on the EXECUTION question:
- §5.5 says "if and only if §3.3 ESCALATE-trigger fires"
- §9.6 (per Trio 6 reading) says "ran whether or not mean-OLS passed"

NB03 Trio 6 dispatch brief over-extended §9.6 to mean "ran regardless of routing branch", which materially changed the verdict outcome.

## §2. Verdict-relevant numerics

Phase-2 close populated:

- Primary OLS: β_composite = -0.14613, HAC SE = 0.0847, t = -1.726, p_one = 0.958
- §3.3 Clause-A: β > 0 AND p ∈ (0.05, 0.20] → **does NOT fire** (β is negative)
- §3.3 Clause-B (B-i: |β|/SE < 0.5; B-ii: |skew| > 1 OR kurt > 3): both False → **does NOT fire**
- **§3.3 ESCALATE-trigger: does NOT fire**
- §8.1 step 4(d) verdict: β ≤ 0 AND p > 0.05 AND Clause-B does NOT fire → **FAIL**

Per spec §5.5 line 252, escalation should NOT have been run. NB03 Trio 6 ran it anyway under §9.6 pre-authorization framing. Realized D-iii: β_pot = +0.113, p_one = 0.012, sign-positive.

If §3.4 D-iii is read literally:
- "positive coefficient at one-sided p ≤ 0.10": β=+0.113 ✓ AND p=0.012 ≤ 0.10 ✓ → **D-iii PASSES literally**
- §3.4 disjunction: "any one or more of the three disjuncts" → **ESCALATE-PASS via D-iii literally**
- §8.3 routing: "ESCALATE-PASS → unblock Stage-2 M-sketch with explicit convex-payoff documentation"

So a strict literal reading of §3.4 produces ESCALATE-PASS even though §5.5 says the escalation suite shouldn't have been run.

## §3. Pivot options enumerated (4 options; per `feedback_pathological_halt_anti_fishing_checkpoint`)

### Option A — Verdict = FAIL per strict §5.5 reading

**Action**: §5.5 line 252 is the load-bearing rule; §9.6 is about framing not execution. The §5.5 escalation should not have been run; the D-iii result is methodologically inadmissible. Final verdict per §8.1 step 4(d) without §5.5 invocation: **FAIL**.

**Anti-fishing**: CLEAN per §5.5 literal. Does not let the "running escalation regardless" loophole convert a FAIL into an ESCALATE-PASS.

### Option B — Verdict = ESCALATE-PASS via D-iii literal

**Action**: §9.6 pre-authorization governs; D-iii passes spec §3.4 literally (β > 0, p ≤ 0.10). Routes per §8.3 → Stage-2 M-sketch UNBLOCKED with tail-risk-put architecture (per §8.3 D-iii ↔ tail-risk-put mapping).

**Anti-fishing**: CLEAN per §9.6 pre-authorization. But conflicts with §5.5 line 252 literal text.

**Trade-off**: Stage-2 M-sketch on a tail-risk-put architecture for a population (Section J narrow ICT) where the mean transmission is REJECTED. A tail-risk-put cannot generate consistent expected payoff if the mean is wrong-signed; this would be a hedge that fails on average but pays out in tails — unusual structure and probably not what dev-AI population needs.

### Option C — FAIL + D-iii preservation as Phase-3 finding for future Section M iteration

**Action**: Verdict = FAIL per spec §5.5 strict reading. **But preserve D-iii numerics in MEMO §11.X(d)** as Phase-3-finding evidence: D-iii positive coefficient on the upper-tail of Y_p_logit-vs-X_lag9 may inform Section M tail-risk hedge geometry in a future iteration. Document the spec-internal §5.5/§9.6 contradiction; flag for spec v1.0.3 micro-revision.

**Anti-fishing**: CLEAN. Strict §5.5 governs verdict; D-iii preservation is INFORMATIVE not RESCUE.

**Trade-off**: cleaner anti-fishing posture than Option B; preserves the empirical D-iii signal for cross-iteration framing.

### Option D — Re-author D-iii under expanded spec v1.0.3

**Action**: spec v1.0.3 micro-revision to reconcile §5.5/§9.6 contradiction; re-execute NB03 Trio 6 under unambiguous protocol; surface afresh. Phase-2 close re-runs.

**Anti-fishing**: STRONG (clean re-execution under unambiguous spec). But heaviest lift; punts to spec authoring before disposition.

**Trade-off**: most rigorous but ~2-3 days of additional work to re-spec + re-execute. Not justified given Phase-2 already closed and verdict is unambiguous under either §5.5-strict (FAIL) or §9.6-loose (ESCALATE-PASS) — the disposition is which framework governs, not what the data says.

## §4. Recommendation

**Option C** is recommended for these reasons:

1. **Anti-fishing-cleanest**: §5.5 line 252 verbatim is "if and only if §3.3 ESCALATE-trigger fires"; §9.6 is about framing not execution. Strict §5.5 is the load-bearing rule.
2. **D-iii preservation is informative, not rescue**: the positive D-iii coefficient on upper-tail residuals is a real empirical finding. It says "upper-tail of Y_p responds positively to X even though the mean does not". This is consistent with R2 Section M positive finding and informs cross-iteration framing without altering the FAIL verdict.
3. **Spec v1.0.3 flag**: the §5.5/§9.6 contradiction is a real spec defect that should be reconciled before any future iteration in the Phase-A.0 Pair-D-style spec lineage uses §5.5 + §9.6 jointly. Filing it as a v1.0.3 micro-revision (or a future-spec convention update) preserves the methodological integrity.
4. **Pair D contrast**: Pair D's Stage-1 PASSed at primary; never invoked §5.5; the §5.5/§9.6 contradiction was latent. The dev-AI iteration is the FIRST iteration to surface this contradiction empirically.

## §5. User adjudication — pick one

**Pick A** — Verdict = FAIL strict §5.5; D-iii result inadmissible (drop from MEMO).
**Pick B** — Verdict = ESCALATE-PASS via D-iii literal; route to Stage-2 M-sketch with tail-risk-put.
**Pick C (RECOMMENDED)** — Verdict = FAIL strict §5.5; preserve D-iii in MEMO §11.X(d) as Phase-3 finding for future iterations; flag spec v1.0.3 reconciliation.
**Pick D** — Spec v1.0.3 re-author + re-execute Phase 2.

## §6. Append-only protocol — user pick log

**User pick 2026-05-06**: Option C (FAIL strict §5.5 + D-iii preservation + spec v1.0.3 reconciliation flag).

**Post-pick action trail**:
1. Author CORRECTIONS-λ block recording Option C disposition; bump MEMO to v1.1 integrating ALL 3-way review findings (Option C + SD BLOCK-1/-2/-3 + HIGH-4/-5 + MED-6 + LOW-7 + CR NIT-1/-2/-3 + RC FLAG-1/-2/-3/-4)
2. Re-emit gate_verdict.json with final FAIL state (provisional_flag → false; verdict → "FAIL" not "PROVISIONAL_FAIL"; r_consistency populated with final §7.1 MIXED + per-arm AGREE booleans + escalation_results)
3. Apply MEMO v1.1 edits per §11.X(b) + §7 BLOCK-2 (change "RESOLVES" → "flagged-not-resolved" per spec §9.16(c) verbatim authorization)
4. Apply MEMO v1.1 edits per HIGH-4 (NB02 Trio 2 spec-deviation Phase-2 retro-acknowledgment)
5. Apply MEMO v1.1 edits per HIGH-5 (§11.X(c) downgrade R1 "captures" → "absorbs era-mean-shift")
6. Apply MEMO v1.1 edits per RC HIGH FLAG-1 (add OLS-homoskedastic primary numerics to MEMO §4 body)
7. Apply MEMO v1.1 edits per RC MEDIUM FLAG-2 (re-balance §1 to foreground FAIL; demote R2 to secondary)
8. Apply MEMO v1.1 edits per LOW-7 (sample-window 2026-02 vs 2026-03 reconciliation across §3 / frontmatter / gate_verdict.json)
9. Apply MEMO v1.1 edits per CR NIT-1 (verdict-tree routing terminology)
10. Spec v1.0.3 micro-revision flag: file as Task #N for future spec authoring (NOT immediate; user can defer)
11. Doc-Verify trailer: 3way-integrated → final
12. Phase 4 disposition + closure-archival proceeds with v1.1 MEMO

End of disposition memo.
