# Phase-A.0 Remittance Exercise — ZK Steward Digest (2026-04-20)

**Luhmann-style atomic notes preserving full Phase-A.0 execution context pre-compaction.**
**Branch `phase0-vb-mvp`, worktree `ranFromAngstrom`. 11/41 tasks done. Phase 2 escalation pending.**

See master state: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_phase_a0_remittance_execution_state.md`

---

## Atomic Note 1: Task 11 quarterly-only finding

**Fact.** BanRep publishes remesas (remittance inflow) at **quarterly cadence only**. No monthly public feed exists. Evidence trail:

- MPR (Monetary Policy Report) index consulted — no monthly remittance series referenced
- Suameca series id **4150** is the authoritative "Remesas de trabajadores, por año" series; resolution is quarterly
- Methodology note URL on BanRep site confirms: remittance statistics are compiled from ACH reporting channels aggregated to **quarterly** balance-of-payments frequency
- Series runs 2000-Q1 through 2025-Q4 -> 104 rows, all committed at `939df12e1`
- All rows carry `mpr_vintage_date = 2026-03-06` (single snapshot, **no revision archive available**)

**Impact.** Invalidates Rev-1 spec sections:
- §4.6 LOCF weekly-align assumption (can't LOCF a quarterly series onto weekly grid without ~13-week stale-data artifact)
- §4.7 AR(1) surprise on monthly series — the monthly grid doesn't exist
- §4.8 real-time vintage primary identification — no vintage archive to reconstruct

**Evidence commit.** `939df12e1` Task 11 — 104 real rows from suameca 4150 in `data/remittance_quarterly_banrep.parquet` with schema `{reference_period, value_usd, mpr_vintage_date, source_url}`.

**See also:** [[atomic note 2]] (escalation paths), [[atomic note 3]] (COPM bridge brainstorm), [[project_phase_a0_remittance_execution_state]]

---

## Atomic Note 2: Four escalation paths A/B/C/D

**Fact.** Four escalation options surfaced after Task 11. User decision pending.

| Path | Description | Pros | Cons | Foreground prior |
|------|-------------|------|------|------------------|
| **A** | Amend Rev-1 -> Rev-1.1 quarterly cadence | Cleanest; keeps remittance as X; real data already ingested | N_eff~50; MDES~0.28 SD (weak power); 3-way review re-opens | **Preferred if B fails** |
| **B** | COPM mint/burn proxy-monthly bridge | Keeps monthly cadence; exploits on-chain data; publishable methodology contribution | Unproven bridge; correlation must validate first; adds proxy-variable risk | Active brainstorm (see atomic note 3) |
| **C** | Pivot Y to quarterly RV | Aligns X and Y cadence | ~72 obs; very low power; loses TRM-RV weekly granularity which is the commercial hook | Disfavored |
| **D** | Switch primary X to TES surprise or ITI-PPI ToT | Falls back to Y×X matrix runner-up; preserves weekly Y | Burns pre-commit discipline on remittance; requires fresh spec; anti-fishing optics | **Acceptable fallback** |

**Methodology constraint.** Per [[project_fx_vol_econ_gate_verdict_and_product_read]] anti-fishing discipline, any pivot must be justified by **structural** cadence constraint (path A/B) not by power-shopping after seeing data. Path D is defensible because remittance cadence is a real-world constraint, not a p-value optimization.

**See also:** [[atomic note 1]] (quarterly finding), [[atomic note 3]] (COPM bridge), [[project_colombia_yx_matrix]] (runner-up X choices for path D)

---

## Atomic Note 3: COPM bridge strategy brainstorm (placeholder)

**Status.** Foreground is actively brainstorming a "middle plan": use Celo-Mento COPM on-chain mint/burn flow (stablecoin corridor proxy) to interpolate quarterly BanRep remittance to monthly cadence. Slot reserved for future agent to link.

**Core idea.** If COPM monthly mint/burn correlates >0.7 with BanRep quarterly remittance (aggregated), COPM becomes a high-frequency proxy. AR(1) surprise on COPM monthly -> LOCF weekly -> Rev-1 §4.7 survives with proxy-variable footnote in §10.

**Unknowns to resolve before adopting path B.**
- Correlation COPM(monthly) vs BanRep(quarterly aggregate) — empirical
- Does COPM have sufficient history to match BanRep 2008-2026 window? Likely NO — COPM mint-burn data starts much later
- Measurement error bias direction if bridge is imperfect
- Publication risk: novel bridge = novel reviewer attack surface

**Expected foreground output.** A separate `.scratch` brainstorm file + decision. When that file exists, this atomic note should be updated with its path.

**See also:** [[atomic note 2]] path B, [[project_colombia_yx_matrix]] (COPM is a matrix cell: COPM mint/burn x Y3)

---

## Atomic Note 4: Rev-1 spec anti-fishing provenance anchor

**Fact.** `REMITTANCE_VOLATILITY_SWAP.md` mtime is **2026-04-02**. CPI-FAIL gate_verdict is **2026-04-19**. The remittance hypothesis predates CPI-FAIL by **17 days**.

**Why this matters.** Per [[feedback_notebook_citation_block]] and anti-fishing discipline in [[project_fx_vol_econ_gate_verdict_and_product_read]], a pivot after FAIL looks like p-hacking unless the new hypothesis was pre-registered. The 17-day gap is the core anti-rescue evidence:

- File system mtime is immutable forensic evidence
- `git log --follow REMITTANCE_VOLATILITY_SWAP.md` will confirm pre-CPI authorship commits
- External pitch / reviewer defense: "This is not a rescue hypothesis. The pre-registration is on-disk."

**How to preserve this.** When Rev-1.1 amendment ships (path A) or any path-D pivot, the commit message MUST cite this 2026-04-02 mtime. Do not let the provenance chain break.

**See also:** [[project_fx_vol_cpi_notebook_complete]] (CPI-FAIL source of truth), [[project_fx_vol_econ_gate_verdict_and_product_read]] (anti-fishing discipline), [[atomic note 2]] (any path picked must cite this)

---

## Atomic Note 5: Paper deep-read contributions pending integration

**Fact.** Two paper deep-reads were completed 2026-04-20 but their recommendations are **not yet applied** to Rev-1 spec. Six pending integration items:

**From `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-nber-w26323-deep-read.md` (Dew-Becker-Giglio-Kelly 2019 Hedging Macroeconomic and Financial Uncertainty):**

1. fn 23 defense of AR(1) surprise on admin aggregates — cite in §4.7
2. 50-day block bootstrap -> 12-week block for weekly Y — update §6 SE construction
3. σ² vs ε² formalization distinction — add to §3 notation
4. **Caution:** GARCH as DGP empirically rejected by DGK (rv-iv correlation ~0.03) — add footnote to Rev-1 §10 reconciliation block, since Rev-1 co-primary is GARCH(1,1)-X inherited from CPI notebook

**From `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-imf-op259-deep-read.md` (Chami et al. 2008 IMF OP-259 Macroeconomic Consequences of Remittances):**

5. Countercyclicality + Dutch-disease dual-channel prior — add to §2 economic motivation
6. Gravity-IV reverse-causation concern -> "β̂_Rem is predictive-regression coefficient, not causal" caveat in §10; REER vs log-TRM sign-convention footnote

**Neither paper provides Colombia-specific coefficients or closes the Basco-Ojeda-Joya citation gap (atomic note 6).**

**See also:** [[atomic note 6]] citation gap, [[atomic note 1]] quarterly constraint (methodology additions survive any escalation path)

---

## Atomic Note 6: Basco-Ojeda-Joya BdE 1273 citation gap (open)

**Fact.** RC FLAG-2 from Task 3 review flagged missing Basco-Ojeda-Joya 2023 Banco de España WP 1273 citation as a placeholder. Task 5 fix-pass left it unresolved pending Phase-1 data-acquisition attempt. **Neither the NBER w26323 nor the IMF OP-259 deep-reads close this gap.**

**Context of original flag.** BOJ 2023 WP 1273 was cited for remittance-surprise methodology on Colombian sample specifically — not for data access.

**Why it may now be obviated.** If path A (quarterly pivot) is adopted, the methodology stack shifts to:
- AR(1) on quarterly BanRep (admin aggregate, DGK fn 23 defense)
- 4-quarter block bootstrap (adapted from DGK 50-day / 12-week)
- Chami predictive-regression framing (not causal claim)

This stack does not specifically require BOJ methodology. **Gap may close as moot.**

**Action required.** Before Rev-1.1 ships (path A) or any path-D spec, explicitly document: "BOJ 2023 WP 1273 citation gap closed as not-applicable under quarterly methodology" OR "BOJ 2023 WP 1273 recovered via [source]". Do not let the gap persist silently.

**See also:** [[atomic note 5]] methodology additions, [[atomic note 2]] path A, Rev-1 spec §4.7 + §10

---

## Commit-hash trail (chronological)

`437fd8bd2` design doc -> `e71044ce0` Rev-1 spec -> `9a5432d3a` spec fix-pass -> `a87d096d8` plan Rev-2 -> `666ba7da3` Task 6 -> `70ceeb8b2` Task 7a -> `a1cffcea0` Task 7b -> `50052af80` Task 7c -> `b23908067` Task 8a -> `63de65863` Task 8b -> `28d76cbb0` Task 9 -> `93b8529bd` Task 10 -> `939df12e1` Task 11 (escalation point).

## Cross-reference bundle

- Master memory: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_phase_a0_remittance_execution_state.md`
- Y×X matrix: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_colombia_yx_matrix.md`
- CPI-FAIL precedent: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_fx_vol_cpi_notebook_complete.md`
- Anti-fishing discipline: `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_fx_vol_econ_gate_verdict_and_product_read.md`
- Paper deep-reads: `.../contracts/.scratch/2026-04-20-nber-w26323-deep-read.md`, `.../2026-04-20-imf-op259-deep-read.md`
- Rev-1 spec: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md`
- Rev-2 plan: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
