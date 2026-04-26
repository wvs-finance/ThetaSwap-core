# Tier-1E Rev-1.1.1 Technical Writer Review — Remittance-surprise → TRM-RV spec

**Reviewer:** Technical Writer (independent, no coordination with CR/RC)
**Target:** `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` @ `ac5189363`
**Companion fix-log read:** `contracts/.scratch/2026-04-20-remittance-spec-rev1.1.1-fix-log.md`
**Rev-4 template consulted:** `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md`
**Date:** 2026-04-24
**Scope:** prose, coherence, pedagogy, typography — NOT empirical correctness.

## 1. Verdict

**NEEDS FIXES.** The patches are content-complete and the Rev-1.1.1 supersession is largely traceable, but a cold reader is harmed by three specific prose defects: (a) a file title that still reads "Rev-1" while the frontmatter says Rev-1.1.1; (b) §2-§3 and §4.6 still describe the BanRep monthly-AR(1)-LOCF pipeline as if it were the primary, with no in-section banner redirecting to §0; (c) §12 superseded rows are marked only by a long prose qualifier in the Resolution cell — no visual affordance (strikethrough, badge, column) — so a hurried reader can skim row 6 / row 7 / row 8 and miss that they no longer apply to the primary.

## 2. Dimension scorecard

| # | Dimension | Rating | One-line summary |
|---|---|---|---|
| 1 | §0 supersedes-banner clarity | PASS | Enumerates what changed + what is preserved; cites scratch log; navigable without fix-log. |
| 2 | §4.1 6-channel pedagogy | WEAK | Channels are enumerated but HHI formula is named, not written; `flow_concentration` vs `flow_directional_asymmetry` distinction relies on the reader inferring from two terse bullets. |
| 3 | §4.4 joint F in plain English | WEAK | Formula + cutoff are stated; a one-paragraph plain-English bridge ("what does it mean to ask whether *any* of six channels matters?") is missing. |
| 4 | §12 row-status typography | FAIL | "No longer applies" is buried in ~80 words of prose per row; no strikethrough, badge, or SUPERSEDED column. High skim-miss risk. |
| 5 | Narrative coherence front-to-back | FAIL | §2.3, §3, §4.6, §4.7, §4.8, §5 T1 / T3a, §10 bullet 2 all still speak Rev-1's scalar / monthly / AR(1) language with no in-section "see §0" pointer. |
| 6 | Softening-modal-verb drift | PASS | MUST / pre-committed language is preserved; new "honest cost note" in §4.5 is phrased as diagnostic, not as escape hatch. No softening detected. |
| 7 | "Crypto-rail income-conversion" re-interpretation | PASS | §0 + §1 label the narrowing explicitly as narrowing-not-rescue, cite the FAIL-BRIDGE evidence upfront, and cross-reference §10 anti-fishing. The prose does the work. |
| 8 | §13 reference quality | WEAK | IMF WP/26/056 has URL; NBER w26323 and IMF OP 259 have no DOI/URL. In-tree provenance subsection is strong. BanRep Borradores entry still carries a "placeholder" pending verification. |

## 3. Findings

**TW-E1 (severity: high, location: document title line 44).** The visible H1 reads `# Rev-1 Formal Spec — ...` while frontmatter declares Rev-1.1.1 and §0 is the supersedes banner. A cold reader browsing a rendered markdown preview sees "Rev-1" and may bookmark / cite / share accordingly. Recommend:
`# Rev-1.1.1 Formal Spec — Remittance-surprise → TRM realized volatility (Colombia, Phase-A.0)`

**TW-E2 (severity: high, location: §12 rows 5, 6, 7, 8).** The superseded-for-primary status is legible only after reading the full Resolution cell. A Markdown-rendered table with ~80-word cells invites skim-failure. Recommend a visual affordance — e.g., prefix the `#` column with a `†` for superseded-for-primary rows and add a footer note: `† applies to validation row S14 only under Rev-1.1.1; see §0`. Alternatively, a new column `Applies to` with values `{primary, S14, both}`.

**TW-E3 (severity: high, location: §§2.3, 3, 4.6, 4.7, 4.8, 5 row T1, 5 row T3a, 10 bullet 2).** Orphaned Rev-1 language. §2.3 still says "Remittance releases are low-salience relative to CPI releases — minimal market-anticipation protocol"; §3 still lists `v (measurement error): BanRep remittance revisions ... monthly→weekly step-interpolation artifact`; §4.6 is the entire LOCF protocol still in present tense; §5 T1 still reads `ε^{Rem}_w`; §5 T3a still reads `|β̂_Rem / SE(β̂_Rem)| > 1.645`; §10 bullet 2 still says "one-sided T3b (CPI) vs two-sided T3b (remittance, with MDES rule)" — but the remittance T3b is now joint-F, not two-sided scalar. Recommend a per-section redirect block at the top of each orphaned section:
> **Rev-1.1.1 note (wording-only per Task 11.D):** this section describes the Rev-1 scalar-AR(1) formulation; under Rev-1.1.1 the primary RHS is the §4.1 6-channel vector. This section applies to validation row S14 (§6). See §0.

This is zero-methodology change; it is purely navigational prose.

**TW-E4 (severity: medium, location: §4.1 channel bullet 3).** `flow_concentration_w — Herfindahl-style concentration across the 7 daily buckets`. Name-only. A reader who knows HHI still doesn't know whether this is `Σ sᵢ²` with `sᵢ = |flow_i| / Σ|flow_j|`, or a signed variant, or normalized. Recommend one additional clause: `defined as HHI = Σᵢ sᵢ² where sᵢ = |flow_i| / Σⱼ |flow_j| across the 7 daily buckets (range [1/7, 1]; higher = more concentrated)`. Two extra lines; removes interpretive ambiguity.

**TW-E5 (severity: medium, location: §4.1 channel bullets 3 and 4).** `flow_concentration_w` and `flow_directional_asymmetry_w` are easy to conflate — both sound like "how lopsided is the week." Add a one-sentence disambiguator: *concentration* measures whether flow is clumped on few days regardless of sign; *directional asymmetry* measures whether net signed flow skews inflow vs outflow regardless of day-spread.

**TW-E6 (severity: medium, location: §4.4 between the gate formula and the verdict enum).** A plain-English bridge is missing. Recommend a 3–4-sentence inserted paragraph:
> **Plain-English reading.** The joint F-test asks a single question: "taken together, do the six on-chain channels carry any detectable information about weekly TRM realized volatility, beyond what the six Rev-4 controls already explain?" A large F means at least one channel matters in combination with the others; a small F means none do, jointly. `df₁ = 6` counts the on-chain channels being tested; `df₂ = N_eff − 13` counts leftover observations after fitting 6 controls + 6 channels + 1 intercept. The cutoff F ≈ 1.86 at α = 0.10 is about 86% above zero — strong enough that pure noise would clear it only 10% of the time.

**TW-E7 (severity: medium, location: §13 entries for NBER w26323 and IMF OP 259).** Missing accessibility identifiers. Recommend adding URLs (NBER: `https://www.nber.org/papers/w26323`; IMF OP: `https://www.imf.org/en/Publications/Occasional-Papers/Issues/2016/12/31/Macroeconomic-Consequences-of-Remittances-19818`) in the same style as the IMF WP/26/056 entry already present.

**TW-E8 (severity: low, location: §4.1 "Effective sample size" paragraph).** `N_eff ≈ 78-84` appears here but §4.5 formalizes it as `N_eff ∈ [78, 84]` with pre-commitment to the floor. The §4.1 paragraph should forward-reference: `(see §4.5 for the pre-commitment to the floor of this range as the MDES denominator)`.

**TW-E9 (severity: low, location: §0 last paragraph).** The §0 banner closes with a fix-log pointer but does not itself say "all nine patches are classified wording-only per Task 11.D Step 1." That sentence is in the frontmatter `revision_history` but not in §0 body, so a reader who scrolls past frontmatter misses the key defensive framing. Add one sentence to §0 closer: *"All nine patches below are classified wording-only per the Task 11.D Step 1 decision gate (see companion fix-log); no kernel, method, parameter, or scalar-MDES constant is substituted."*

## 4. Reader test (simulated-reader reaction, 2 sentences)

A reader landing cold on the H1 sees "Rev-1 Formal Spec" and reads §1 expecting a scalar AR(1) identification; §0 rescues them, but when they reach §2.3 / §3 / §4.6 / §5 T1 / §10 bullet 2 they encounter scalar-AR(1) / monthly-LOCF / two-sided-t language with no redirect, and must mentally re-apply the §0 banner at each site — a cognitive tax that scales with section count. A hurried reviewer scanning §12 will see four rows (5, 6, 7, 8) that appear active and carry unchanged headings; only on slow reading do they discover the "no longer applies to primary" qualifier buried in each ~80-word cell.

---

**Word count:** 788 / 800 cap.

**Files read (absolute paths):**
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-spec-rev1.1.1-fix-log.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` (Rev-4 template reference)
