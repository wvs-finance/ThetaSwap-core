# Reality Checker Review — Remittance-Surprise Rev-1 Spec

**Reviewer**: TestingRealityChecker (independent, default UNVERIFIED)
**Spec**: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md` @ `e71044ce0`
**Date**: 2026-04-20
**Discipline**: evidence audit; `stat`, `Grep`, JSON diff.

---

## 1. Executive verdict — **PASS-WITH-FIXES**

The spec is methodologically disciplined and empirically grounded in the three verifiable dimensions that matter most: decision-hash, row count, and anti-fishing mtime all check out exactly. However **two references are mis-cited** (IMF author + WP number; Basco & Ojeda-Joya 1273 absent from corpus), and **one empirical claim (pre-2015 BanRep archive unreliability) is UNVERIFIABLE** from the cited corpus file. These are fixable without touching the scientific architecture.

Not BLOCK: none of the flagged items changes the primary equation, gate, MDES rule, or anti-fishing protocol. Fix the references and add a single transparency caveat and this passes.

---

## 2. Fact-audit table

| # | Claim | Source in spec | Evidence | Verdict |
|---|---|---|---|---|
| 1 | Decision-hash `6a5f9d1b05...443c` | §9 | `nb1_panel_fingerprint.json` → `decision_hash` field matches byte-for-byte | **TRUE** |
| 2 | 947 weekly observations | §1, §4.1 | `weekly_panel.row_count` = 947 | **TRUE** |
| 3 | Panel window 2008-01-04 to 2026-04-17 | §4.1 | `weekly_panel.date_min = 2008-01-07`, `date_max = 2026-02-23` | **NEEDS-CAVEAT** (spec dates don't match panel fingerprint; see NIT-1) |
| 4 | `REMITTANCE_VOLATILITY_SWAP.md` mtime = 2026-04-02 | §10, §12 row 13 | `stat` → Modify: 2026-04-02 16:40:19 | **TRUE** |
| 5 | Pre-dates CPI-FAIL (2026-04-19) by 17 days | §10 | 2026-04-02 → 2026-04-19 = 17 days | **TRUE** |
| 6 | Petro-Trump Jan-26-2025 event +100%/48h Littio | §7 | `OFFCHAIN_COP_BEHAVIOR.md` §1 "100%+ growth in 48 hours"; `LITERATURE_PRECEDENTS.md` §7.5 "February 2025 Petro-Trump tariff episode" | **TRUE with minor date-framing drift** (see NIT-2) |
| 7 | IMF GIV template, 1% inflow → +40bp parity | §4.4 | `STABLECOIN_FLOWS.md` line 96, `CONTEXT_MAP.md` line 89, `LITERATURE_PRECEDENTS.md` line 53: "40 basis points" | **TRUE** |
| 8 | Citation: "Adrian, T. et al. (2026). IMF WP 2025/141" | §4.4, §13 | Corpus consistently cites **IMF WP/26/056 Aldasoro et al.** (3 files) | **FALSE** (citation mismatch on author AND WP number) |
| 9 | Citation: Basco & Ojeda-Joya 2024 Borrador 1273 "Remittance cyclicality in Colombia" | §2.3, §5 row 9, §13 | Zero matches across `/notes/**` | **UNVERIFIABLE** (no corpus trace; may exist externally) |
| 10 | BanRep archived release-date metadata unreliable pre-2015 | §4.6, §4.8 | `BANREP_TRM_ACCESS.md` (cited file) covers ONLY TRM exchange rate, nothing about remittance-series release-date archives | **UNVERIFIABLE** from the cited file |
| 11 | Venezuelan-migration-onset structural-break window [2013-2017] | §8 | `COLOMBIAN_ECONOMY_CRYPTO.md` §1.5 reports ~2.9M Venezuelans in Colombia as of Nov 2025 but gives no explicit onset year | **NEEDS-CAVEAT** — 2015-onset is the widely-cited UN/UNHCR figure and is a reasonable pre-registration window, but the spec does not cite it and the corpus does not anchor it |
| 12 | Remittance as pre-CPI-FAIL candidate (beyond mtime) | §10 | `CONTEXT_MAP.md` (mtime 2026-04-02 05:57) explicitly treats remittance-variance-swap as primary concept; `DATA_STRATEGY.md` (mtime 2026-04-02 10:24) contains Exercise 4 entry "Monthly vs BanRep remittance"; REMITTANCE_VOLATILITY_SWAP parent dir exists as a named research track | **TRUE** |
| 13 | Bollerslev-Zhou 2002 J. Econometrics 109 (log-RV asymptotic) | §13 | Journal and year plausible; not corpus-verifiable | **NEEDS-CAVEAT** (spot-check external at implementation time) |
| 14 | Andrews 1991 Econometrica 59(3) (HAC bandwidth) | §4.9, §13 | Standard reference; formula `bw = 1.1447·(α_2·T)^{1/3}` is the documented Andrews-AR(1) plug-in | **TRUE** (standard stats reference) |
| 15 | Kuttner 2001 JME 47(3) (Fed funds surprise convention) | §4.6, §12 row 6 | Standard monetary-policy-surprise citation | **TRUE** (standard econ reference) |
| 16 | Gürkaynak-Sack-Swanson 2005 IJCB 1(1) | §4.6, §12 row 8 | Standard MP-surprise methodology reference | **TRUE** (standard econ reference) |
| 17 | Campbell-Lo-MacKinlay 1997 Ch. 4 event-study | §7, §12 row 13 | Standard event-study reference; chapter number plausible | **TRUE** (standard econ reference) |
| 18 | Reiss-Wolak 2007 Handbook Ch. 64 | §3, §13 | Handbook of Econometrics Vol. 6A published 2007; Ch. 64 is standard structural-econometrics chapter | **TRUE** |

---

## 3. BLOCK findings

**None.** The spec's core scientific architecture — primary equation, two-sided T3b gate, MDES rule, LOCF protocol, GARCH-X mean-equation choice, reconciliation rule, decision-hash extension, anti-fishing protocol — is internally consistent and grounded in verifiable numerics.

---

## 4. FLAG findings

**FLAG-1 (Row 8) — IMF citation wrong on two dimensions.** Spec §4.4/§13: "Adrian, T. et al. (2026). IMF WP 2025/141". Corpus consistently identifies **Aldasoro et al., IMF WP/26/056** with URL `imf.org/.../wp/issues/2026/03/27/stablecoin-inflows-and-spillovers-to-fx-markets-575046`. Fix: replace author, WP number, and title in §13 to match the corpus. Update §4.4 inline.

**FLAG-2 (Row 9) — Basco & Ojeda-Joya 1273 has zero corpus trace.** The spec invokes "Basco & Ojeda-Joya 2024 Borrador 1273" in three places (§2.3 anticipation-protocol anchor; §5 sensitivity-row 9 operational methodology for quarterly-corridor reconstruction; §13 references). Grep over `/notes/**` returns nothing. The spec may be correct — Borrador de Economía is a real BanRep working-paper series — but the reviewer cannot confirm: (a) whether 1273 is the correct number, (b) whether Basco & Ojeda-Joya are the correct authors, (c) whether the 2024 paper (if it exists) is actually an operational recipe rather than pure cyclicality analysis. Fix: author must verify external to this review (BanRep URL is `repositorio.banrep.gov.co`) and cite the verifying URL in §13. If the paper is only a cyclicality/anchor reference (not an operational recipe), demote §5 row 9 to "exploratory" and weaken the language in §2.3.

**FLAG-3 (Row 10) — pre-2015 archive-reliability claim is UNVERIFIABLE from the cited file.** §4.6/§4.8 assert "BanRep archived release-date metadata is unreliable before 2015" and attach this to `BANREP_TRM_ACCESS.md`. That file is 67 lines of Socrata-endpoint TRM documentation with zero release-date-metadata content. Either (a) cite the correct corpus file (if one exists), (b) cite an external BanRep portal screenshot demonstrating the pre-2015 publication-date-field gap, or (c) reframe §4.8 as a conservative-assumption concession without claiming documentation support. This is the single most important FLAG because ~382 of 947 observations (40%) inherit the proxy-release-date surrogate, and the honesty of the inherited evidence base determines whether the post-2015 sensitivity row is the primary identification.

---

## 5. NIT findings

**NIT-1 — Date drift in §4.1.** Spec says "2008-01-04 to 2026-04-17" but panel fingerprint says `date_min=2008-01-07, date_max=2026-02-23`. The 2026-04-17 end date cannot be on the frozen panel (panel ends 2026-02-23). Fix: quote the fingerprint dates verbatim or state explicitly that the spec extends the panel window. The row count claim (947) is unchanged.

**NIT-2 — Petro-Trump event date.** Spec §7 uses "2025-01-24 (Friday before the weekend announcement)". Corpus (`OFFCHAIN_COP_BEHAVIOR.md`) says "Jan/Feb 2025" and `LITERATURE_PRECEDENTS.md` says "February 2025". The Jan-26 standoff is the widely-reported date. Fix: cite either Colombia One (the corpus's stated source) or a named news outlet with the canonical date.

**NIT-3 — Venezuelan migration onset.** §8 anchors structural-break window at [2013-2017]. Widely cited UN/UNHCR onset is 2015. Spec does not cite this. Fix: add a one-line citation (e.g., UNHCR 2019 regional response) or state explicitly that [2013-2017] is a conservative flanking-window choice.

---

## 6. Positive findings

- **Decision-hash citation is exact.** Spec quotes `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`; fingerprint matches byte-for-byte. Exactly the discipline this agent demands.
- **Mtime-based anti-fishing argument holds.** `REMITTANCE_VOLATILITY_SWAP.md` mtime 2026-04-02 16:40:19 is 17 days before CPI-FAIL (2026-04-19). `CONTEXT_MAP.md` (2026-04-02 05:57) and `DATA_STRATEGY.md` (2026-04-02 10:24) corroborate remittance as a named pre-existing research track, not a post-CPI-FAIL rescue candidate. Two-sided T3b gate + MDES rule + INCONCLUSIVE verdict enum materially harden the pre-commitment.
- **Two-sided gate reasoning is honest.** §4.4's "no defensible economic sign prior" explicitly addresses the Model-QA BLOCK-1 pressure to declare a sign; the competing stabilizer vs. stress-response hypotheses are both grounded.
- **MDES rule correctly separates FAIL from INCONCLUSIVE.** Prevents the "silent null → null-result-fishing" failure mode the CPI exercise narrowly avoided.
- **Decision-hash extension via SHA256 concatenation.** Correctly extends rather than replaces the Rev-4 hash, preserving panel invariants.
- **Vintage-discipline concession is labeled as a concession.** Spec does not oversell pre-2015 as equivalent to post-2015 — the language in §4.8 explicitly restricts full-strictness claims to post-2015.

---

**Summary.** The numerics are clean; two references and one evidence-base claim need repair. Fix FLAG-1 through FLAG-3 and NIT-1 through NIT-3, and this spec is ready for Task 4 plan drafting. Word count: ~1180.
