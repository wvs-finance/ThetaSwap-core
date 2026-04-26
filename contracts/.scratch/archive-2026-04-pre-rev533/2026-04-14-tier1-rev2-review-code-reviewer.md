# Code Reviewer — Tier 1 Feasibility Spec Rev 2 Review

**Spec:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` (Rev 2)
**Prior review:** `contracts/.scratch/2026-04-14-tier1-review-code-reviewer.md`
**Date:** 2026-04-14

## OVERALL: APPROVE_WITH_CHANGES

Rev 2 makes substantive progress on every Rev 1 FLAG and most NITs. The scope expansion to two channels is handled coherently, the decision tree is now explicit, and the τ-gap is finally defended. However, three new issues surface with the revision: (a) §10 thresholds are asserted with only partial rationale, (b) §11 decision tree has one remaining non-determinism around "PARTIAL_SUPPORT beyond Tier D", (c) §18 success criterion still permits a 5-weak-citation pass under a narrow reading. Nothing blocking; resolve inline during execution.

---

## Part 1 — Rev 1 finding disposition

| # | Rev 1 finding | Status | One-line justification |
|---|---|---|---|
| 1 | Verdict rules not mutually exclusive | **FIXED** | §11 now has explicit top-down first-match decision tree with five labeled verdicts; the `△` ternary collapses into §10 thresholds not §11 verdict logic. |
| 2 | τ-gap unjustified | **FIXED** | §3 item 1 now states "published in-sample adj-R² typically overstates out-of-sample performance" — a real rationale, not hand-wave. Acceptable. |
| 3 | Tier 2 handoff hidden coupling | **FIXED** | §12 enumerates 11 required per-citation columns including `sample period start and end years`, `frequency`, `surprise construction`, `portability-to-cCOP-specification caveat`. Resolves the implicit-coupling complaint. |
| 4 | Non-goals list has gaps | **FIXED** | §15 adds [strict] bullets for no-meta-analysis, no-paraphrased-rerun, no-side-quest-scoping, and read-only on 2026-04-02 repo. All four Rev 1 requests present. |
| 5 | Success criterion permits under-specified deliverables | **PARTIAL** | §18(a) now requires ≥3 of 4 query patterns per source and downgrades a strength tier on skip; §18(b) requires ≥5 citations total OR signed exhaustive-search failure OR Tier-A/B `DISCONFIRMED`. But "≥5 distinct citations across both channels" does not force per-channel minima — a channel could carry 0 citations while the other carries 5, and still pass (see NEW-3 below). |
| 6 | Infra-check load-bearing but unsourced | **FIXED** | §2 Finding 1 now names three specific files with absolute paths and notes they are copied to `.scratch/` on execution start. Snapshot-date anchor is now required per §10 last paragraph. Acceptable. |
| 7 | "Close proxy" unbounded | **FIXED** | §7 Tier A/B/C/D hierarchy with explicit Tier-D definition ("non-COP EM currency that shares Colombia-relevant macro structure: inflation-targeting, commodity-exporter, similar openness") bounds admissible proxies. |
| 8 | §7 rating scale undefined | **FIXED** | §8 now specifies cell format `adj-R² \| significance \| tier \| citation(s)` with `NOT STUDIED` sentinel and strength-bucket symbols ✦/✧/✧·. Empty `—` explicitly disallowed. |
| 9 | §8 ternary vs §9 binary | **FIXED** | §10 defines the ternary with numeric thresholds; §11 decision tree reads `✓` vs `△/✗` consistently. No binary/ternary mismatch. |
| 10 | MIXED lacks tie-break | **FIXED** | §11 step 2 now has three-level tie-break: (i) highest adj-R², (ii) deepest notional, (iii) lowest confound density. Ties surfaced via `target_counterparty=<primary>,<secondary>`. |
| 11 | Time estimate no stop condition | **FIXED** | §17 "Hard cap: 3 days. If trending above 3 days, reopen as Tier 1a — do not silently extend." Exact fix requested. |
| 12 | notes/ vs .scratch/ split | **PARTIAL** | §13 still puts deliverable in `notes/structural-econometrics/identification/` and artifacts in `.scratch/`. No explicit acknowledgement that this differs from the `feedback_research_output_folder.md` memory. Likely intentional (durable deliverable vs transient artifacts), but the silent policy divergence is not confirmed in-spec. |

Score: 10 FIXED, 2 PARTIAL, 0 NOT FIXED, 0 WORSE.

---

## Part 2 — Targeted verification of the five specific questions

### Q1. §11 decision tree determinism

**Verdict: DETERMINISTIC with one edge case.**

Walkthrough over §7 tier × §8 citation × §10 wrapper state space, per channel:

- Step 1 gate: `≥1 Tier-A/B citation with β≈0 or adj-R²<0.05 tight CI` → `DISCONFIRMED`. Well-specified.
- Step 2 gate: `≥1 citation ≥0.10 AND ≥1 counterparty ✓` → `CONFIRMED`. Well-specified with tie-break.
- Step 3 gate: `≥1 citation ≥0.10 AND no counterparty ✓` → `CONFIRMED_NO_INFRASTRUCTURE`. Well-specified.
- Step 4 gate: `≥1 citation below threshold OR specification-distance flagged beyond Tier D` → `PARTIAL_SUPPORT`.
- Step 5: everything else → `NO_LITERATURE_SUPPORT`.

**Edge case — Step 1 vs Step 2 precedence when both conditions hold simultaneously:** A channel could have one Tier-A paper reporting $\operatorname{adj-}R^2 = 0.02$ (null) AND another Tier-B paper reporting $\operatorname{adj-}R^2 = 0.18$ (confirming). Top-down first-match emits `DISCONFIRMED`, suppressing the confirming evidence. This is defensible (null from a Tier-A paper outweighs a Tier-B confirm) but not documented. Add one sentence: "Step 1 takes precedence over Step 2 by design — a credible Tier-A/B null outweighs a same-channel confirm; the tension is surfaced in the deliverable rationale field."

**Edge case — Step 4 boundary "specification-distance flagged beyond Tier D":** §7 defines NOT STUDIED as "farther than Tier D". So "beyond Tier D" in §11 step 4 collapses into NOT STUDIED, which shouldn't produce PARTIAL_SUPPORT — it should fall through to Step 5. Wording is loose. Fix: "≥1 citation below threshold OR at best a Tier-D-classified hit" (drop "beyond Tier D").

Otherwise deterministic: every fill of §7+§8+§10 maps to exactly one verdict.

### Q2. Two-channel pivot — does MIXED_GLOBAL drop channels?

**Verdict: NO CHANNELS DROPPED.** §11 Global roll-up handles heterogeneity correctly:
- `PROCEED_WITH` fires on ≥1 CONFIRMED regardless of the other channel's verdict.
- `RETIRE_THESIS` fires only on **all** DISCONFIRMED.
- `PIVOT_NEEDED` fires only on **all** NO_LITERATURE_SUPPORT or CONFIRMED_NO_INFRASTRUCTURE.
- `MIXED_GLOBAL` catches everything else and **surfaces each per-channel verdict** — no forced CONSENSUS.

**Minor concern:** A {CONFIRMED, DISCONFIRMED} pair does trigger PROCEED_WITH (the CONFIRMED survivor) per §11 pivot protocol. The surviving-channel path is correct but the DISCONFIRMED result on the other channel is not explicitly preserved in the Tier 2 handoff — it's just absorbed into "PROCEED_WITH the survivor". Add a note: "When PROCEED_WITH fires on a {CONFIRMED, DISCONFIRMED} pair, the DISCONFIRMED channel's evidence must be surfaced in the deliverable so Tier 2 doesn't resurrect it." Otherwise the pivot cleanly preserves multi-channel evidence.

### Q3. §10 thresholds ($50K / $5K) — load-bearing, defensible, or magic?

**Verdict: PARTIALLY DEFENSIBLE; needs one sentence of arithmetic.**

- **$50K 30-day avg daily notional (✓ gate):** §10(b) provides rationale: "below this, a 1% daily move produces <$500 of bid-cost, indistinguishable from noise under typical Angstrom bid discretization." This is a real calculation and traces back to a claimed Angstrom property. **Acceptable.**
- **$5K 1% slippage round-trip (✓ gate):** §10(c) provides no rationale. Why $5K not $1K or $10K? This looks like "arbitrary small number". It's likely calibrated to minimum-viable-hedge size for the RAN, but nothing in §10 says so. **NEEDS ONE SENTENCE.** Suggested: "$5K is the minimum-viable round-trip for a RAN hedge to meaningfully dominate gas + priority fees on L1/L2 under current fee regimes." Or tie it to a multiple of (b).
- **$5K lower bound for △ gate:** §10 penultimate paragraph. Same concern; inherits rationale from (c) if (c) is fixed.

The $50K and $5K are load-bearing: they partition the `✓`/`△`/`✗` space that §11 keys on. If they move by 2x in either direction, the verdict flips for marginal pairs. Rationale for $5K is the hole.

### Q4. §18 success criterion — gameable with 5 weak Tier-D citations?

**Verdict: STILL GAMEABLE, but the attack surface is narrower.**

§18(b) says "≥5 distinct citations in total across both channels". Reading strictly:
- 5 Tier-D citations on one channel + 0 on the other → passes §18(b).
- Each citation reports $\operatorname{adj-}R^2 = 0.11$ (just above $\tau_{\text{lit}}$) on a panel EM study that includes Colombia.
- §11 Step 2 requires `≥1 citation meets τ_lit ≥ 0.10 AND ≥1 counterparty ✓`. Tier-D citations ARE admissible to clear this bar — §7 does not restrict Step 2 to Tier A/B/C.
- Result: a Tier-D-only CONFIRMED verdict passes the deliverable.

§7 closes the loop by saying "Tier D citations only motivate Tier 1b" — but this is narrative guidance, not a §11 gate. §11 Step 2 does not check tier.

**Two fixes possible:**
1. Add to §11 Step 2: "If the strongest qualifying citation is Tier D, downgrade the verdict to `PARTIAL_SUPPORT` with `which_dimension=tier_too_distant`."
2. Add to §18(b): "Each channel requires ≥2 citations at Tier C or above, OR explicit exhaustive-search failure."

Without one of these, the "5 Tier-D citations pass" scenario is real. §18(f) second-reader gate only spot-checks tier classification, not whether tier-distribution suffices for the verdict.

**Smaller gaming lane:** §18(a) "downgrades the relevant channel's verdict by one strength tier" on source-skip — but verdict labels (`CONFIRMED`/`DISCONFIRMED`/...) don't have "strength tiers"; §8 strength buckets do. Language mismatch: what does it mean to downgrade `CONFIRMED` one tier? To `PARTIAL_SUPPORT`? Clarify.

### Q5. §12 Tier 2 handoff columns — all fillable from abstract/intro/methodology?

**Per-column assessment:**

| Column | Source in paper | Fillable from abstract? |
|---|---|---|
| citation | metadata | YES |
| sample period start/end years | abstract or §1 intro | USUALLY YES |
| country | abstract | YES |
| counterparty pair | abstract or methodology | USUALLY YES (may need §2) |
| frequency (daily/weekly/monthly) | methodology / §2 data | **USUALLY NO** — requires methodology section |
| LHS (vol/level/basket) | abstract or methodology | USUALLY YES |
| surprise construction | methodology | **NO** — requires methodology section; often buried in §3 |
| control set | methodology / table notes | **NO** — usually requires reading the regression table |
| reported adj-R² | results table | **NO** — requires results section |
| proxy tier (A/B/C/D) | derived from above | depends on upstream columns |
| distance-from-hypothesis note | analyst synthesis | derived |
| portability-to-cCOP caveat | analyst synthesis | derived |

**Verdict: 4 of 12 columns require reading the full paper (or at minimum methodology + results tables).** Specifically: `frequency`, `surprise construction`, `control set`, `reported adj-R²`. An abstract-only sweep will not fill these. This is not a defect — serious literature review requires full-text — but the spec should acknowledge it. Current §5/§6 search protocol is silent on "what to do when full text is paywalled and the abstract doesn't surface these columns": §19 mentions paywall risk but doesn't say "leave those columns blank and downgrade tier" or "treat as NOT STUDIED". Add one sentence to §12: "Rows where methodology-sourced columns (frequency, surprise construction, control set, reported adj-R²) cannot be extracted from available text must be downgraded one proxy tier and flagged `full-text-blocked`."

---

## Part 3 — New issues introduced by Rev 2

**NEW-1 (§10 threshold rationale): $5K slippage threshold has no arithmetic.** See Q3. One-sentence fix.

**NEW-2 (§11 Step 4 wording): "beyond Tier D" collides with §7 NOT STUDIED.** See Q1 edge case. One-sentence fix.

**NEW-3 (§18(b) per-channel minimum absent): ≥5 citations total permits 0-on-one-channel passes.** Combined with Q4 gaming: a 5-Tier-D-on-one-channel deliverable passes both §18(b) and §11. Needs per-channel floor: "≥2 citations per channel, OR per-channel exhaustive-search failure signed."

**NEW-4 (§18(a) "downgrade a strength tier" is ambiguous): strength tiers live in §8 (✦/✧/✧·), verdict labels live in §11.** The downgrade target is unclear. Clarify whether §18(a) means "§8 bucket" or "§11 verdict".

**NEW-5 (§20 References contains many `[citation to confirm]` stubs — 8 of 15 entries).** For a spec that is about literature rigor, unconfirmed references in the spec itself undermine the credibility signal. These are explicitly downstream to resolve, but the spec could mark them clearly as "search seeds, not endorsed citations" — currently they look like half-done bibliography. Downgrade this section's heading to "Search seeds (to be confirmed in execution)" or similar.

**NEW-6 (§11 prior-calibration phrased in first-person aside): "The pivot you triggered in Rev 2…"** addresses the user directly. This leaks an authoring artifact into what should be a durable spec. De-personalize: "The Rev 2 pivot extending scope to two channels is baked into the global roll-up above."

**NEW-7 (§11 Step 1 vs Step 2 precedence undocumented): Tier-A null suppressing a Tier-B confirm is defensible but not flagged.** See Q1.

**NEW-8 (§2 Finding 3 cites unrun Exercise 1 as evidence for channel viability): §2 claims "drafted-but-unrun Exercise 1 specification" shows remittance is viable.** An unrun exercise is evidence that someone thought the channel was plausible, not that it is viable. The real evidence is the "53% of cCOP inflows are US→Colombia remittances" stat. Tighten §2 Finding 3 to lean on the stat, not the draft.

---

## Recommended changes before execution (priority-ordered)

1. **§11 Step 2 tier gate OR §18(b) per-channel floor** — closes the Tier-D-gaming hole (Q4, NEW-3).
2. **§10(c) $5K rationale sentence** — closes magic-number concern (Q3, NEW-1).
3. **§12 full-text-blocked downgrade rule** — closes the abstract-only gap (Q5).
4. **§11 Step 4 wording: "at best Tier-D-classified hit"** — removes NOT STUDIED collision (Q1, NEW-2).
5. **§11 Step 1 vs Step 2 precedence note** — documents the design choice (Q1, NEW-7).
6. **§18(a) clarify downgrade target** (NEW-4).
7. **§20 rename or relabel `[citation to confirm]`** (NEW-5).
8. **§11 de-personalize "you triggered"** (NEW-6).
9. **§2 Finding 3 lean on stat not draft** (NEW-8).
10. **§13 acknowledge notes/ vs .scratch/ split** (Rev 1 #12 PARTIAL).

Items 1–3 are substantive and should be in the spec before execution. 4–10 can be handled inline with one-sentence edits.

---

## What Rev 2 gets right

- Decision tree is now genuinely decidable on every input fill (modulo NEW-2 wording).
- Two-channel pivot is architected, not bolted on — global roll-up handles all four heterogeneity cases cleanly.
- τ-gap rationale is real (in-sample vs out-of-sample), not wave-hand.
- Evidence anchors for the pivot now trace to specific files and snapshot dates.
- Tier A/B/C/D proxy hierarchy replaces unbounded "close proxy" with a traceable classification.
- Non-goals carry all four Rev 1 asks plus scope-expansion-mid-execution guard.
- Success criterion is now outcome-based with a second-reader gate (addresses bias risk §19 names).
- §11 label normalization (`UPPER_SNAKE_CASE`, regex-matchable, structured payload) is a craftsmanship upgrade.
