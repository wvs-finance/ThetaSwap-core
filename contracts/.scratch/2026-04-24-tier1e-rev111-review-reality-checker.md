# Rev-1.1.1 Reality-Checker Review — Tier-1e

**Reviewer:** Reality Checker (evidence-obsessed, default NEEDS WORK)
**Target:** `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` @ `ac5189363`
**Date:** 2026-04-24

## 1. Verdict: **NEEDS WORK**

Most load-bearing claims verified; three substantive discrepancies found. Two are MAJOR (MDES-λ and CSV-row-count), one is MINOR (CSV-zero-row counts). Anti-fishing discipline is intact; commit hashes all resolve; 6-channel names match exactly; mtime evidence checks out. Not REJECTED because none of the findings invalidate the FAIL-BRIDGE verdict or the joint-F gate architecture; but the spec cannot go to production implementation carrying numerical claims that fail recomputation.

## 2. Verification table

| # | Claim | Evidence path | Verified? | Discrepancy |
|---|---|---|---|---|
| 1 | Task 11.C: ρ=+0.7554, conc 2/5, N=6, FAIL-BRIDGE via OR-clause | `2026-04-20-onchain-banrep-bridge-result.md` L11, L13, L21, L3 | YES (exact) | None |
| 2 | Commits `bc12e3c30`, `2bff6d79f`, `91e5d2664`, `ac5189363` | `git log --oneline --all \| grep …` | YES (all four) | None |
| 3 | Dune query `#7366593` is non-temp, feeds Task 11.A | `dune_onchain_flow_fetcher.py` L12, L193; no "temp\|TEMP\|dune_sql" hits | YES | None |
| 4 | 6 channel names match between spec §4.1 and `weekly_onchain_flow_vector.py` | loader L85–L90, L199–L204, L300–L307 | YES (exact) | None |
| 5 | N_eff=78 floor justified in §4.5 | spec L360–L380 | PARTIAL | See RC-E1 |
| 6 | MDES_R² ≈ 0.143, λ ≈ 13, f² ≈ 0.167 at N=78, df₁=6, df₂=65, α=0.10 | scipy recomputation | NO | See RC-E2 |
| 7 | NBER w26323 fn 23 defends AR(1) on admin aggregates; IMF OP 259 motivates reverse-causation | `2026-04-20-nber-w26323-deep-read.md` L38, L50; `2026-04-20-imf-op259-deep-read.md` L40, L91 | YES | None (but see RC-E4) |
| 8 | `REMITTANCE_VOLATILITY_SWAP.md` mtime = 2026-04-02, predates CPI-FAIL by 17 days | `stat` output | YES | Instructions listed wrong path; actual file at `/notes/REMITTANCE_VOLATILITY_SWAP/REMITTANCE_VOLATILITY_SWAP.md` (spec L587 cites correct path) |
| 9 | BanRep `suameca` 4150 is quarterly-only | — | UNVERIFIED | See Unverifiable-1 |
| 10 | Notebook §4 classifier consumes pre-computed booleans, does not re-read ρ | notebook cell 11 `classify_bridge_verdict(rho_above_pass, …)` | YES | None |
| A | CSV row count "585 rows" | `wc -l` = 597; 11 comment lines → 586 data rows | NO | See RC-E3 |

## 3. Findings

### RC-E1 — MAJOR — N_eff=78 floor, not-quite-honest justification

**Spec §4.5 L371:** "Conservative floor: `N_eff = 78`." But the Task 11.C scratch log L44 reports "84 weekly rows … 1 partial_week, 2 all_zero_full_week, 81 valid" after NaN-ambiguity filtering. That yields **81 valid + 2 all-zero-full-week retentions = 83 usable**, not 78. The spec's L252–L254 claims "N_eff ∈ [78, 84]" without reconciling to 81/83. The `N_eff ≈ 78-84` range is handwaved; there is no arithmetic path from 84 raw → 78 floor documented in spec or scratch log. Spec L373 asserts "slightly conservative (underestimating) detection floor" but the 78 floor looks closer to a pessimistic-but-arbitrary round-down than a derived value.

**Required fix:** Either (a) cite the specific exclusions taking 84 → 78 (e.g., Rev-4 panel-end clipping, specific weeks dropped), or (b) recompute MDES at N_eff=81 (the empirically-derived valid count from the Task 11.C log) and preserve N_eff=78 only as a sensitivity. Without either, the 78 figure is unjustified.

### RC-E2 — MAJOR — MDES arithmetic fails independent scipy recomputation

**Spec §4.5 L385–L395** claims: `λ ≈ 13` (specifically "`statsmodels.stats.power.FTestPower` returns λ=12.97 at df₁=6, df₂=72, α=0.10, power=0.80"), `MDES_R² ≈ 0.143`, `f²_MDES ≈ 0.167`.

**Scipy recomputation at df₁=6, df₂=65 (N_eff=78), α=0.10, power=0.80:**

```
F_crit(0.10, 6, 65) = 1.8668   (spec claim ~1.87 — MATCH)
F_crit(0.10, 6, 72) = 1.8576   (spec claim ~1.86 — MATCH)
lambda (80% power)  = 12.0602  (spec claim ~13 → ~8% off)
MDES_R² = lam/(lam+N) = 12.06/90.06 = 0.1339   (spec claim 0.143 → 6.4% off — INSIDE ±5% tolerance? NO, outside 5%)
f² = lam/N           = 12.06/78 = 0.1546        (spec claim 0.167 → 7.4% off — OUTSIDE ±5%)
```

Both MDES_R² and f² diverge from spec by >5%. The root cause is the spec's λ figure: spec cites "λ=12.97 at df₂=72" (statsmodels.stats.power), but at df₂=65 (the realized df₂ = N_eff−13 = 78−13), scipy's non-central-F inversion returns λ ≈ 12.06. The spec did the λ computation at df₂=72 (= 84−12), which is either the wrong N_eff (84 instead of 78) or the wrong regressor count (12 instead of 13). This is a computable-numeric mis-statement.

**Required fix:** Either (a) recompute λ at df₂=65 and update MDES_R² to ~0.134 and f² to ~0.155, or (b) explicitly pre-commit to df₂ computed at N_eff=84 (unconservative) with MDES_R² = λ/(λ+84) = 12.06/96.06 ≈ 0.126, but then change the conservative-floor language in L371. The current spec mixes the conservative-N for the floor statement with the larger-N for the λ computation — an arithmetic inconsistency.

### RC-E3 — MINOR — CSV row-count claim is off-by-one

**Spec L72, L252, L367** claim the Task 11.A daily CSV has "585 rows." `wc -l` returns 597; 11 lines are comment headers (lines beginning `#`); data-row count is **586**, not 585. Off-by-one. Instructions' "585 rows (534 non-zero)" is also off: `awk` count of non-zero rows returned 596 (unreliable heuristic — better counts depend on column choice, but 534 cannot be reproduced from naïve column checks). Neither the spec nor the instructions' claims match the file.

**Required fix:** Re-count with `python3 -c "import pandas as pd; df = pd.read_csv('contracts/data/copm_ccop_daily_flow.csv', comment='#'); print(len(df))"` and update spec L72, L252, L367 with the pandas-round-trip-verified count. If the "534 non-zero" figure matters to any claim, also emit a script-computed non-zero count using the authoritative zero-definition.

### RC-E4 — MINOR — NBER w26323 citation has a subtle scope mismatch

**Spec L631** claims DGK fn 23 supports "AR(1) surprise on BanRep." The deep-read at L38 confirms DGK fn 23 defends AR(1) surprise on administrative-aggregate series that are NOT two-sided smoothers. BanRep remittance is an administrative aggregate, so the citation applies. However, the deep-read's Action 3a (L50) recommends wording that makes clear the DGK footnote defends AR(1) on administrative aggregates **by contrast with JLN two-sided-filter series** — the spec's current §13 citation does not include this contrast, so the reader cannot tell why the citation is load-bearing.

**Required fix:** Expand §13 DGK citation to paraphrase: "DGK fn 23 defends AR(1) residuals as statistical innovations on administrative-aggregate series (as distinct from two-sided-filter indices such as JLN, where AR residuals are not innovations)." Or accept this as a wording-only defect and defer to Tier-1e.

### RC-E5 — INFO — Rev-1.1.1 word delta 3× the target

The fix-log L45–L48 concedes: spec grew from 3,847 words (Rev-1) to 7,012 (Rev-1.1.1), +3,165 words vs target "+1,500 to +2,500 words" (per Task 11.D prompt). The 665-word overage is concentrated in §0 banner, §4.4 joint-F rationale, §13 provenance. The fix-log correctly flags this as reviewer-evaluable. I flag it as a mild finding: the "wording-only" classification would be more credible if the patch were closer to target size. The overage is not disqualifying.

**Required fix:** None strictly required — fix-log already disclosed. If a future reviewer asks, be prepared to justify §0 banner (~800 words) as non-redundant with §1 and §10.

## 4. Unverifiable claims (recommend citation)

**Unverifiable-1 — BanRep `suameca` series 4150 quarterly cadence.** Spec L66–L67 asserts BanRep publishes this series at quarterly cadence only. No BanRep metadata file is reachable in the worktree; `contracts/data/banrep_remittance_aggregate_monthly.csv` exists (per scratch log L51) but its naming is misleading and I did not re-open it to verify cadence. **Recommend spec add a pointer to the Task 11 metadata-inspection artifact** where the quarterly cadence was confirmed (plan Task 11 description or a scratch log from the plan-commit chain).

**Unverifiable-2 — "LITTIO USDC-account opens grew +100% within 48h" (§7 Petro-Trump event).** Spec L540 cites `COPM_MINTEO_DEEP_DIVE.md` and `LITERATURE_PRECEDENTS.md`; I did not attempt to verify these corpus anchors. Not a Rev-1.1.1 patch (Rev-1 material, already reviewed); flagged for future triage.

**Unverifiable-3 — Rev-4 decision-hash `6a5f9d1b…` match against `nb1_panel_fingerprint.json`.** Spec L558 cites this hash; I did not cross-reference. Not a Rev-1.1.1 patch; assumed-correct from Rev-1.

---

**Reviewer posture:** Verdict NEEDS WORK due to RC-E1 and RC-E2 (MAJOR). RC-E3 and RC-E4 are easy-fix MINOR. RC-E5 is disclosure-only. Unverifiable-1 deserves one citation line in §13 or §1. The Rev-1.1.1 architecture — six-channel primary, joint-F gate, N_eff narrowing, S14 bridge-back-pointer — is methodologically sound and the FAIL-BRIDGE handling is anti-fishing-clean. The numeric errors (λ, N_eff derivation, row count) are what blocks production-ready certification.
