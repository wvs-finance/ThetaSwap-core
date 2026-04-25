# RC advisory — Task 11.N.2.OECD-probe diagnostic memo (single-pass, non-blocking)

**Reviewer:** TestingRealityChecker (Reality Checker lens)
**Date:** 2026-04-25
**Memo under review:** `contracts/.scratch/2026-04-25-oecd-direct-cpi-probe.md`
**Plan task spec:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` lines 1842–1860 (Task 11.N.2.OECD-probe under Rev-5.3.2)
**Prior RC report referenced:** `contracts/.scratch/2026-04-25-rev532-review-reality-checker.md` (lines 132–142, 375)
**Re-review at this RC's authoring head:** memo at `16c2e75b1`

---

## Verdict: **PASS-with-non-blocking-corrections**

The DE's diagnostic memo is archival-quality, the recommendation is sound, and — most importantly — the memo has caught and corrected **two substantive errors in this RC's prior review** that require explicit acknowledgement under anti-fishing discipline.

I PASS the memo for archival use. The "non-blocking-corrections" qualifier is **about my own prior report**, not the DE's memo: I owe the project record an explicit retraction of (a) the speculative "level-series via IX" assertion at the prior RC report line 140, and (b) the transcription error mapping `5.290032` to `2026-03` at lines 135 and 375. The DE's memo §2.1 and §2.2 already correctly narrate these corrections; this advisory reinforces them on the RC side of the project history.

---

## Live re-verification of DE's two load-bearing corrections

I ran two independent live probes from `contracts/.venv` to test the DE's claims, refusing to take them on faith. Both probes were performed at this RC authoring time (2026-04-25, post-DE-commit `16c2e75b1`).

### Verification 1 — IX-404 across all anchor countries (DE §2.1 finding)

```python
url = f'https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/{ref}.M.N.CPI.PA._T.N.IX?startPeriod=2025-01&endPeriod=2026-04&format=jsondata'
```

| REF_AREA | HTTP | body[:200] |
|----------|------|------------|
| COL | **404** | `NoResultsFound` |
| BRA | **404** | `NoResultsFound` |
| KEN | **404** | `NoResultsFound` |
| EU27_2020 | **404** | `NoResultsFound` |
| EA20 | **404** | `NoResultsFound` |

Wildcard transformation probe (`COL.M.N.CPI.PA._T.N.`) returns exactly **one** TRANSFORMATION value: `GY = Growth rate, over 1 year`. **No `IX` (level) transformation exists in `DSD_PRICES@DF_PRICES_ALL`.**

**Confirmed:** the DE is right; the prior RC report's speculative note ("level-series equivalent retrievable via the `IX` filter") was unverified and incorrect. `IX` returns 404 universally; only `GY` is published.

### Verification 2 — CO transcription (DE §2.2 finding)

```
COL.M.N.CPI.PA._T.N.GY recent observations:
  2025-12 -> 5.099884
  2026-01 -> 5.353601
  2026-02 -> 5.290032          ← prior RC mislabeled as 2026-03
  2026-03 -> 5.558094          ← prior RC missed this value entirely
```

**Confirmed:** the DE is right. The prior RC report at lines 135 and 375 reported "2026-03: 5.290032" — but `5.290032` is the **2026-02** value. The true 2026-03 value is `5.558094`. The error appears to be a one-row off-by-one in the prior RC's transcription pass.

**Operational consequence:** none. The OECD probe is diagnostic-only under Rev-5.3.2 anti-fishing guard at plan line 1860; the value mapping does not feed any source-mix decision. But anti-fishing discipline applies to reviewers too — recording the correction is the honest move.

---

## Memo-quality checks (per the user's check-list 1–5)

### Check 1 — Probe coverage of all four anchors + GY/IX variants

YES. Memo §2 table covers CO, BR, KE, and EU (twice — `EU27_2020` and `EA20` because the Eurozone aggregation has two valid REF_AREA codes, plus the deprecated `EA19` and the unrelated `OECDE` aggregate for completeness). Each country is probed with both `GY` and `IX` variants. Coverage is complete; if anything, slightly more thorough than the plan spec required (EU was added as a fourth anchor; the plan spec mentions only CO/BR/KE in line 1849, but adding EU is correct because the four-source matrix at line 1850 implicitly anchors to all four Y₃ countries).

### Check 2 — IX-404 finding spot-check

VERIFIED LIVE for all five REF_AREAs (one Eurozone code redundantly probed), per the §"Verification 1" table above. The DE's structural finding stands: `IX` is not exposed in this dataflow.

### Check 3 — Transcription correction spot-check

VERIFIED LIVE. The 2026-02 = 5.290032, 2026-03 = 5.558094 mapping in the DE memo is correct. My prior RC report's mapping was incorrect. Acknowledging here.

### Check 4 — Recommendation soundness ("REMAIN UNUSED")

The DE's four-prong rationale is defensible and I would have come to the same conclusion:

1. **No freshness gain** — confirmed by my own §3.1 table and the DE's. CO at parity (DANE 2026-03 = OECD 2026-03), BR at parity-or-better-than-OECD (BCB SGS will land at 2026-03 same as OECD), EU at parity (Eurostat 2025-12 = OECD 2025-12), KE genuinely absent from OECD. No country gains freshness.

2. **Methodology penalty for Y₃** — Y₃ design §10 row 2 needs **levels**; OECD direct exposes only `GY` (annual %). A rate-to-level reconstruction utility is a non-trivial methodology change that would need its own pre-commitment. The DE correctly flags this is NOT byte-exact reproducible without additional schema discipline. This is a strong reason against substitution.

3. **KE coverage gap** — confirmed live. KE GY returns HTTP 200 with empty `series:{}` (6046-byte response with no observations). Wildcard probe also yields zero series. KE is genuinely absent from this dataflow; OECD does not solve the IMF-fallback-or-skip problem at Y₃ design §10 row 1.

4. **Anti-fishing-guard at plan line 1860** — explicitly forbids feeding OECD outcome into the source mix under Rev-5.3.2; the DE's "REMAIN UNUSED" recommendation respects this guard.

The memo's §4 "Trade-off articulation" (lines 106–110) is exactly the right framing: REJECT folding into Rev-5.3.3 as primary, WEAK MOTIVATION for sensitivity-only, RECOMMENDED to remain unused under current evidence. I endorse.

### Check 5 — Memo quality (archival appropriateness, reproducibility, table accuracy)

- **Detail level appropriate:** yes — §1 endpoint family + §2 per-country table + §3 freshness comparison + §4 recommendation + §5 acceptance trace + §6 verbatim probe outputs is the right cut for a `.scratch/` archival memo. Not over-engineered, not under-detailed.
- **Reproducibility:** §6.3 reproduction recipe is byte-exact runnable (I tested a variant of it during this advisory). The URL family in §1 is parameterized correctly. The SDMX-JSON v2.0 wrapper-structure note is a useful trap-warning for future revisions.
- **Comparison-vs-current-mix table accuracy (§3):** verified accurate. CO at parity, BR at parity-or-+1, EU at parity, KE absent. The "OECD supersedes? **No**" verdicts hold under my live evidence.
- **Acceptance trace (§5):** all six criteria from plan lines 1848–1852 are met. The deliverable filename in the plan spec is `2026-04-25-oecd-sdmx-co-cpi-probe.md` (line 1846) but the actual filename is `2026-04-25-oecd-direct-cpi-probe.md` — cosmetic deviation, does not affect archival utility.

---

## Cosmetic findings (none load-bearing)

1. **Filename deviation:** plan spec at line 1846 prescribed `2026-04-25-oecd-sdmx-co-cpi-probe.md`; memo lands as `2026-04-25-oecd-direct-cpi-probe.md`. Both are searchable; the DE's filename is arguably more descriptive (encodes "direct" vs. "via DBnomics" disambiguation). Non-blocking.

2. **EU added as a fourth anchor (not in plan-spec criterion 1, but consistent with criterion 2):** the plan-spec criterion #1 at line 1849 says "CO / BR / KE coverage" but criterion #2 at line 1850 implies a four-source matrix that includes Eurostat HICP (for EU). The DE's memo treats EU as a fourth anchor consistently. This is the right call for Y₃ context (4-country panel). Non-blocking.

---

## Self-correction owed by RC (anti-fishing-applies-to-reviewers)

For the project record:

> **The prior RC report `2026-04-25-rev532-review-reality-checker.md` contains two substantive errors that the DE's `2026-04-25-oecd-direct-cpi-probe.md` memo correctly identifies and corrects:**
>
> 1. **Line 140:** "level-series equivalent retrievable via the `IX` filter" — this assertion was speculative and not live-probed at the time. Live verification at this advisory's authoring time confirms `IX` returns HTTP 404 `NoResultsFound` for all anchor countries (CO, BR, KE, EU27_2020, EA20). Only `GY` (annual rate) is exposed.
>
> 2. **Lines 135 and 375:** "2026-03: 5.290032" — the value `5.290032` is the OECD direct SDMX 2026-02 observation for COL CPI annual %. The true 2026-03 value is `5.558094`. This was a transcription mistake in the prior RC's evidence-block.

These corrections do **not** change the prior RC's verdict on the Rev-5.3.2 plan (the BLOCKERs at the prior review were resolved by the fix-up rewrite under the second-pass re-review at `2026-04-25-rev532-rereview-reality-checker.md`, where these errors were not re-cited as load-bearing — the fresh-through-2026-03 finding remained correct in spirit even with the off-by-one transcription). But the corrections matter for archival accuracy and for the principle that anti-fishing discipline applies symmetrically: I cannot demand DE/Author reports include verified-only claims if I do not hold my own reports to the same bar.

---

## What I tried to break (adversarial spot-checks)

1. **Did the DE's IX-404 finding hold for non-anchor REF_AREAs?** — Probed `EU27_2020` and `EA20` separately; both 404. The DE's structural conclusion ("only GY is published, not IX, in `DSD_PRICES@DF_PRICES_ALL`") survives.

2. **Was the wildcard-transformation probe technique sound?** — Replicated `COL.M.N.CPI.PA._T.N.` (any TRANSFORMATION); response includes one TRANSFORMATION dimension value: `GY = Growth rate, over 1 year`. Confirms structural assertion. No silent IX exists.

3. **Could OECD direct have hidden an IX series under a different MEASURE/UNIT_MEASURE/EXPENDITURE combination?** — Did not exhaustively sweep the 8-axis dataquery key space (would be a broader probe than the plan spec requires; the DE's probe targeted `CPI.PA._T.N` which is the canonical headline-CPI key). For Rev-5.3.2 archival purposes, the `CPI.PA._T.N.IX` 404 across 5 REF_AREAs is sufficient evidence.

4. **Did the memo overstate the DANE-vs-OECD parity at CO?** — Confirmed independently from my own prior `Command 1` (DANE 2026-03-01 ingested 2026-04-16) — at parity with OECD's 2026-03. No overstatement.

5. **Did the memo correctly classify OECD-Europe (`OECDE`) as not Y₃-relevant?** — `OECDE` is the OECD-Europe aggregate (38 OECD-member European countries); it is NOT the Eurozone. Correctly listed for completeness only and not folded into the Y₃-EU comparison. Sound classification.

---

## Recommendation

**PASS-with-non-blocking-corrections.** The DE's memo is archival-quality. The recommendation ("REMAIN UNUSED") is sound on the data and on the anti-fishing-guard interpretation. Two corrections to the **prior RC report** (not the DE memo) are recorded above for project-history completeness.

No re-dispatch needed. No edit to the DE's memo needed. No edit to the plan needed. This advisory is a passive archival note that, combined with the DE's memo, fully closes Task 11.N.2.OECD-probe under Rev-5.3.2.

**Re-review trigger:** none. Task closes at this advisory's commit.

---

**Reviewer signoff:** TestingRealityChecker
**Live-probe evidence reproducible:** see `contracts/.scratch/2026-04-25-oecd-direct-cpi-probe.md` §6.3
**Verdict:** PASS-with-non-blocking-corrections (corrections apply to the prior RC report, not to the DE memo).
