# Fix log — 2026-04-20 remittance-surprise design doc

**Target**: `contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md`
**Inputs**: Code Reviewer + Reality Checker + Model QA (3× PASS-WITH-FIXES)

## Category A — in-place fixes

| Rev | ID | Fix |
|---|---|---|
| CR | B1 | New §"Path allow-list" enumerates 7 paths; Rev-4 precedent cited (`project_fx_vol_cpi_notebook_complete.md`); `research/data/` → `data/`. |
| CR | B2 | §Scope + §Purpose: "one *primary* RHS column + pre-registered auxiliary columns" (regime / event / A1-monthly / release-day). |
| CR | B3 | 3× `.../memory/` ellipses replaced with full absolute path (frontmatter, Deliverable #9, References). |
| RC | B1 | §Scientific question: US-corridor monthly pivoted to BanRep aggregate monthly; data-source note + ≈53% US-dominance caveat; quarterly corridor reconstruction = secondary row. |
| RC | B2 | §Purpose: "unambiguous winner" → "winner under specific rank-aggregation method"; α/β/γ cited; A3 + B1 named as Phase-A.1 companions. |
| CR | F1 | §Pre-commitment #1: spec-hash SHA must be `git merge-base --is-ancestor` of any params commit. |
| CR | F2 | §Deliverables #8: tests moved to `scripts/tests/remittance/`. |
| CR | F3 | §Scientific question: "implemented by importing `from scripts.nb2_serialize import reconcile`". |
| CR | F4 | §Deliverables #8: 5 silent-test-pass patterns named; affirmative-exclusion required. |
| CR | F5 | New §"Why this is not a rescue of CPI-FAIL" co-locates hypothesis / null / sensitivity separators + provenance. |
| CR | N1–N5 | YAML path; spec filename; hash enforcer citation; scripts-only dedup; Model QA unhedged. |
| RC | F1 | Control-set: Agent 3 Hispanic-emp swap rejected with preservation-of-Rev-4-hash rationale. |
| RC | F2 | Vintage ambiguity opens to Rev-1 spec; linked to Phase-0 item #8. |
| RC | F3 | New §Risks #8 scopes novelty to "Colombia-specific remittance-surprise → FX-vol identification". |
| RC | F4 | §Pre-commitment #11: REMITTANCE_VOLATILITY_SWAP.md 2026-04-02 mtime + Reiss-Wolak spec path added. |
| RC | N1–N4 | §Risks #4 Littio figures disambiguated + self-report caveat; β̂ citation → completion memory; memory path concretized. |

## Category B — promoted to Phase-0 mandatory inputs

New §"Mandatory inputs to the Phase-0 `structural-econometrics` skill call" enumerates 13 items the Rev-1 spec MUST resolve:

- MQ BLOCK-1 → Item 1 (sign prior)
- MQ BLOCK-2 → Item 2 (MDES + inconclusive rule)
- MQ BLOCK-3 → Items 4, 5, 6 (kernel / bandwidth / interpolation side)
- MQ BLOCK-4 → Item 3 (alternate-LHS sensitivity)
- MQ FLAG-1 → Item 7 (AR order / SARIMA)
- MQ FLAG-2 → Item 8 (vintage discipline)
- MQ FLAG-3 → Item 10 (numerical-intersection reconciliation)
- MQ FLAG-4 → Item 9 (Quandt-Andrews ±12mo window)
- MQ FLAG-5 → Item 11 (GARCH-X mean vs variance)
- MQ FLAG-6 → Item 12 (Dec-Jan sensitivity)
- MQ FLAG-7 → Item 13 (event-study co-primary)

MQ NITs 1–4 left to Rev-1 spec author (kernel-name / version pins / schema / README Unicode).

## Deferrals / rejections

None. All 9 BLOCKs, 16 FLAGs, 9 NITs addressed.

## Word-count delta

Design doc: ~2,200 → 3,680 (+~1,480). Over the 300–500 target because the 13-item Phase-0 mandatory-inputs section is load-bearing for Rev-1 auditability and cannot be compressed without losing reviewer-traceability. Prose elsewhere tightened; net addition is structural.
