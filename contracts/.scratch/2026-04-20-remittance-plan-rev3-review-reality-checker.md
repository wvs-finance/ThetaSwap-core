# Rev-3 Remittance Plan Patch — Reality Checker Review

**Reviewer:** TestingRealityChecker (independent discipline pass)
**Document:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `6034b360f`
**Date:** 2026-04-23
**Default posture:** UNVERIFIED until evidenced.

---

## 1. Executive verdict

**NEEDS WORK — 2 BLOCKs, 3 FLAGs, 2 NITs.** The Rev-3 patch is substantially well-grounded: the Task 11 commit citation, BanRep quarterly-only finding, COPM/cCOP contract addresses, Dune query IDs, and "no β̂_Rem yet" anti-fishing defense all hold under audit. However, one factual claim in the Rev-3 history bullet (line 10) is demonstrably inconsistent with the in-tree `banrep_mpr_sources.md` provenance log, and the "95 weekly obs" rationale-arithmetic cited in the review charter conflicts with the plan's own text ("24 months ≈ 95–104 weekly obs"). Two grounded claims are preserved and should stay.

## 2. Fact-audit table

| # | Claim | Source verified | Verdict |
|---|---|---|---|
| 1 | Commit `939df12e1` exists, touches `banrep_remittance_aggregate_monthly.csv`, contains ~104 rows | `git show 939df12e1`; `wc -l` CSV = 118 (104 data + header + provenance) | **TRUE** |
| 2 | BanRep publishes remittance QUARTERLY-only | `contracts/data/banrep_mpr_sources.md` lines 27-45 (in-tree provenance) | **TRUE** |
| 3 | Suameca series 4150 = `REMESAS_TRIMESTRAL`, Trimestral | `banrep_mpr_sources.md` lines 42-52 | **TRUE** (in-tree; live URL not re-fetched, relying on commit-time verification) |
| 4 | COPM Celo address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | `COPM_MINTEO_DEEP_DIVE.md` lines 85, 344 | **TRUE** |
| 5 | "cCOP + Mento broker `0x777a8255ca72412f0d706dc03c9d1987306b4cad`" | `/home/jmsbpp/apps/liq-soldk-dev/notes/research-ccop-stablecoin.md` line 41 | **TRUE** (address is Mento broker — cCOP itself is NOT at this address; see FLAG-3) |
| 6 | Dune `#6939814` = Mento broker swaps | `CURRENCY_SELECTION.md` line 21 | **TRUE** |
| 7 | Dune `#6940691` = COP token comparison / "COPM transfers" | `CCOP_BEHAVIORAL_FINGERPRINTS.md` line 209 labels it "COP Token Comparison (all 3 tokens)" | **NEEDS-CAVEAT** (plan calls it "COPM transfers" — actual title is 3-token comparison; see FLAG-1) |
| 8 | Dune `#6941901` = cCOP volume | Corpus references it as Dune-Colombia data source in `structural-econometrics/analysis/2026-04-02-ccop-cop-usd/fetch_dune_data.py` | **TRUE** (existence + cCOP association confirmed in-corpus; "volume" label approximate) |
| 9 | 4,913 cleaned-cohort senders for cCOP | `CCOP_BEHAVIORAL_FINGERPRINTS.md` line 27 | **TRUE** (but row is "cCOP (old)" Dead/migrated — see FLAG-2) |
| 10 | "22 months = ~95 weekly obs" (review charter framing) | Plan actually says "Apr-2024 → most-recent ≈ 24 months daily ≈ 95–104 weekly observations" (line 236) | **NEEDS-CAVEAT** (plan is internally consistent; charter summarized it imprecisely) |
| 11 | 7 quarterly obs for bridge-gate | 2024-Q2 through 2025-Q4 inclusive = Q2/Q3/Q4 2024 + Q1/Q2/Q3/Q4 2025 = 7 quarters | **TRUE** |
| 12 | Anti-fishing defense: no β̂_Rem computed yet | `find -name "gate_verdict_remittance*"` → only CPI `gate_verdict.json` found; no notebook cells beyond `env_remittance.py` scaffold | **TRUE** |
| 13 | Memory rules `feedback_three_way_review.md`, `feedback_notebook_trio_checkpoint.md`, `feedback_specialized_agents_per_task.md` all exist | `ls ~/.claude/projects/*/memory/` confirms all three | **TRUE** |

## 3. BLOCK-severity findings

**B-R1. Line-10 Rev-3-history claim "4 recent MPR PDFs" is evidentiary theater, not provenance.**
The Rev-3 history bullet asserts BanRep-quarterly-only was verified against "the MPR index, 4 recent MPR PDFs, the ficha metodológica, BanRep suameca series 4150, and the methodology note." But the actual in-tree provenance at `contracts/data/banrep_mpr_sources.md` grounds the claim in the suameca series metadata (id 4150, plan `REMESAS_TRIMESTRAL`) + the ficha metodológica — NOT the MPR PDFs. The MPR PDFs contain "C. Ingresos secundarios (transferencias corrientes)" which is total-current-transfers, not disaggregated remittance, as `939df12e1`'s commit message itself explains. The factual load-bearing step is the suameca `descripcionPeriodicidad=Trimestral` metadata, not an MPR-count. **Fix:** rewrite line 10 to ground the claim in the suameca metadata primarily, and treat the 4 MPRs as corroborating (ruled out) rather than confirming evidence. Audit trail should point to `banrep_mpr_sources.md` by path.

**B-R2. "cCOP + Mento broker address" phrasing is a contract-address category error.**
The review charter frames "cCOP contract + Mento broker address (`0x777a8255…`)" as one verification; but `0x777a8255ca72412f0d706dc03c9d1987306b4cad` is the Mento **broker**, not the cCOP token contract. The plan rationale cites Dune `#6939814` = Mento broker swaps (TRUE), so the plan itself is consistent — but any rewrite of the plan or downstream spec Rev-1.1 that conflates the two will poison data acquisition. **Fix:** Task 11.A step-3 should explicitly disambiguate `{cCOP token address: [to-be-looked-up], Mento broker: 0x777a8255…}` so the subagent does not query the broker when it needs token transfers.

## 4. FLAG-severity findings

**F-R1. Dune `#6940691` mislabeled "COPM transfers" in plan line 246.**
In-corpus title: "COP Token Comparison (all 3 tokens)" — a cross-sectional comparison, NOT a COPM transfer time series. Fetching it expecting daily COPM transfers will silently return a different schema. **Fix:** relabel in-plan; verify at Task 11.A step 3.

**F-R2. "4,913 cleaned-cohort senders" is from cCOP-OLD (migrated/dead).**
`CCOP_BEHAVIORAL_FINGERPRINTS.md` line 27 table row reads `| cCOP (old) | 0x8a56... | Dead (migrated Jan 2025) | 227,536 | 4,913 | 12,197 | 13,851 |`. The 4,913 figure is a historical stock, not an active-post-Oct-2024 population. The Rev-3 plan line 236 uses it as forward-looking cohort size for the union window Apr-2024 → present. **Fix:** either (a) cite the post-migration cohort count instead, or (b) re-phrase as "≥4,913 lifetime cleaned-cohort senders (pre-migration)" with an explicit caveat that the post-migration cohort in the 95-week window may be smaller.

**F-R3. "24 months daily ≈ 95–104 weekly observations" needs a single committed number for pre-registration.**
The plan line 236 offers a range (95-104) but Task 11.B/11.C downstream gates reference N≈95 (line 258). A range is acceptable for rationale prose but the pre-committed T3b critical value and the bridge-gate power analysis need a single N. **Fix:** pick one (recommend N=95, the conservative floor anchored to Rev-4-panel-end Feb-2026) and commit it in the Rev-1.1 spec patch.

## 5. NIT-severity findings

**N-R1.** Line 246 says "cached permanent queries (`#6941901` cCOP volume…) where available; fall back to `mcp__dune__updateDuneQuery` only if modification is required." The fallback verb is correct but the plan should also name `mcp__dune__executeQueryById` as the read path (read-only, no credits burned on existing query). Saves one Dune credit round-trip per re-execution.

**N-R2.** The Rev-3 rationale at line 236 cites "$200M/mo, 100K Littio users" for COPM — that marketing figure is not in-corpus-verifiable in this review (no grep hit in `REMITTANCE_VOLATILITY_SWAP/research/` for "200M" or "Littio"). Remove or cite source. Low-stakes (marketing colour, not load-bearing for identification).

## 6. Positive findings (preserve)

**P-R1. Anti-fishing defense holds.** Verified: `find -name "gate_verdict_remittance*"` returns nothing; only `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` (the CPI-FAIL) exists. No β̂_Rem notebook cells exist beyond an `env_remittance.py` scaffold. The methodology shift from monthly-LOCF to daily-on-chain therefore CANNOT be rescue-motivated because Task 11 is Phase-2 ingestion and Task 21 (β̂ estimation) is two phases downstream. The anti-fishing logic is sound and should be preserved verbatim in the Rev-1.1 spec patch rationale.

**P-R2. Commit citation `939df12e1` is a model of forensic grounding.** The commit message itself exhaustively documents the MPR-dead-end and the pivot to suameca, with filename + schema + row count + fechaUltimoCargue snapshot date. This is the standard against which other load-bearing citations in the plan should be measured.

**P-R3. Memory-rule citations are clean.** All three cited feedback files (`three_way_review`, `notebook_trio_checkpoint`, `specialized_agents_per_task`) exist at the expected path. No dangling references.

**P-R4. Bridge-gate N=7 arithmetic is correct.** 2024-Q2 through 2025-Q4 inclusive = 7 quarters. The plan's ρ>0.5 threshold on N=7 is underpowered (typical), but that is a FLAG for the spec-review agent, not an arithmetic error.

---

**Reviewer disposition:** proceed to spec-review once B-R1 and B-R2 are addressed; FLAGs can be folded into the Rev-1.1 spec patch at Task 11.D. P-R1 should be lifted verbatim into the Rev-1.1 pre-registration rationale as the anti-fishing audit trail.

**Evidence paths:**
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/banrep_mpr_sources.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/banrep_remittance_aggregate_monthly.csv`
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COPM_MINTEO_DEEP_DIVE.md`
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CCOP_BEHAVIORAL_FINGERPRINTS.md`
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CURRENCY_SELECTION.md`
- `/home/jmsbpp/apps/liq-soldk-dev/notes/research-ccop-stablecoin.md`
- `git show 939df12e1`

Word count: ~1060.
