# MACRO_RISKS Evidence-Base Pre-flight

**Date:** 2026-04-15
**Task:** Plan Rev 2, Task 0.3a
**Purpose:** Verify the painkiller evidence base exists, classify which files are prose-finished vs. sketch, and identify at least one load-bearing line range for Claim Auditor smoke tests.

## Folder existence

`/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` — exists, readable.

## File inventory and classification

| File | Lines | Content class | Usable for |
|---|---|---|---|
| `MACRO_RISKS.md` | 415 | **Mixed.** Lines 1–5 are finished prose; lines 7–13 and subsequent blocks are arrow-notation pseudocode / sketch form. | Prose sections (lines 1–5, plus scattered finished paragraphs deeper in the file) usable for directional PASS. Sketch sections usable only for PASS-weak per spec §11.13. |
| `INCOME_SETTLEMENT.md` | 213 | Mixed. Contains finished prose on income-settled derivative theory interleaved with code-adjacent sketches. | Usable for directional claims about income settlement; line-range selection required. |
| `MACRO_DERIVATIVES.md` | 88 | Short, mostly design-pattern notation. | Sketch form; PASS-weak only. |
| `SIGNAL_TO_INDEX.md` | 58 | Short, theoretical. | Requires re-reading for prose vs. sketch classification before citation. |
| `PRICE_SETTLEMENT.md` | 18 | Stub-short. | Not citable in its current form. |
| `ECONOMETRICS_NOTES.md` | 16 | Stub-short. | Not citable. |
| `MACRO_RISKS_CHECKPOINT.md` | 14 | Stub-short. | Not citable. |
| `MACRO_RISKS.md~` and `INCOME_SETTLEMENT.md~` | — | Editor backups. | Not cited; excluded from evidence base. |

Excluding the two `~` backups: **5 of 7 primary files** have some finished prose; **3 of 7** are long enough to host meaningful multi-paragraph context. Evidence base is usable but narrower than the spec originally implied. This matches Reality Checker's finding (spec Rev 3 §11.13 — PASS-weak verdict introduced).

## Load-bearing citation for Claim Auditor smoke test

**Path:** `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md`
**Line range:** 1–5
**Content (verbatim):**
```
  The Reality Check
  Macro Risk Proxies Beyond Pure FX

  For underserved countries, FX depreciation is often the dominant macro risk
  ---> It proxies GDP decline, inflation, capital flight).
```

**What this line range grounds:** a directional claim about macro risk in underserved-FX countries — that FX depreciation is a dominant risk and that it proxies (correlates with) inflation and other macro shocks. Suitable for grounding language in Abrigo copy like "in underserved-FX markets, currency depreciation drives compound macro exposure — GDP decline, inflation, and capital flight move together."

**Not suitable for:** quantitative claims ("X% of savings lost to inflation"), country-specific claims without additional citation, or direct causal claims without acknowledging the proxy relationship.

## Tertiary references note

`/home/jmsbpp/apps/liq-soldk-dev/refs/macro-risk/` exists per spec §8.1. Its contents are primary-source papers that the MACRO_RISKS notes reference. Out of scope for this pre-flight to classify line-by-line; the Claim Auditor will consult it when a cited line in MACRO_RISKS/ points further into a referenced paper.

## Gaps flagged for follow-on research

- No prose treatment of remittance-corridor risk. Current coverage is a single row in the MacroRisk block at line 12. Phase 7 (Crecimiento submission) will describe remittance-corridor painkiller claims but citation options are limited to that row + whatever is in INCOME_SETTLEMENT.md.
- No quantitative estimates of erosion magnitudes for any channel.
- No country-specific sections — everything is "underserved countries broadly." Useful for the mission framing, insufficient for Colombia-pilot specificity. Tier 1 feasibility methodology spec is the expected source for Colombia-specific numbers once its deliverable is written.

## Proceed decision

**Proceed to Task 0.3.** Evidence base is usable for v1. The Claim Auditor's PASS-weak verdict handles the sketch-form gap; richer claims will wait for follow-on research passes on the evidence folder.
