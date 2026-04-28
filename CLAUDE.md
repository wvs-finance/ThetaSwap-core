# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Angstrom is a trustless, hybrid AMM/Orderbook exchange that settles on Ethereum L1. It's designed to mitigate MEV for both users and liquidity providers by using a network of staked nodes for order matching and bundle creation.

## Key Commands

### Rust Development (via justfile)

**Recommended**: Use `just` commands when available for consistency and convenience.

```bash
# Quick Commands (preferred)
just                  # Show available commands
just ci               # Run full CI suite (format check, clippy, all tests)
just check            # Check format, clippy, and run unit tests
just fix              # Auto-fix formatting and clippy issues
just test             # Run unit tests
just test-integration # Run integration tests
just build            # Build release version
just clean            # Clean build artifacts

# Detailed just commands
just check-format     # Check code formatting
just fix-format       # Auto-fix formatting issues
just check-clippy     # Run clippy linter
just fix-clippy       # Auto-fix clippy issues
```

### Direct Cargo Commands (when needed)

Use these when the justfile doesn't provide the specific functionality:

```bash
# Building
cargo build --workspace                    # Build all workspace members
cargo build --workspace --all-features     # Build with all features
cargo build --profile maxperf              # Build with maximum performance

# Testing with specific options
cargo test --workspace -- --nocapture      # Run tests with output

# Running binaries
cargo run --bin angstrom                   # Run main node
cargo run --bin testnet                    # Run testnet
cargo run --bin counter-matcher            # Run order matcher
```

### Smart Contract Development

```bash
cd contracts

# Setup Python environment (required for FFI tests)
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Building & Testing
forge build                                # Build contracts
forge test --ffi                           # Run tests (FFI required)
forge test -vvv --ffi                      # Run tests with verbosity
forge test --match-test <name> --ffi       # Run specific test

# Formatting
forge fmt                                  # Format Solidity code
forge fmt --check                          # Check formatting
```

## Architecture Overview

### Smart Contracts (`/contracts`)
- **Core Contract**: Handles order validation, settlement, and AMM reward management
- **Periphery Contracts**: Access control and fee distribution
- Uses Uniswap V4 as underlying AMM
- PADE encoding for efficient data packing
- "Code as storage" (SSTORE2) pattern for gas optimization

### Node Implementation (`/crates`)
- **angstrom-net**: Custom P2P network layer for order propagation
- **consensus**: Leader selection and bundle finalization
- **order-pool**: Manages limit orders, searcher orders, and finalization pool
- **matching-engine**: Implements uniform clearing for order matching
- **validation**: Validates orders and bundles
- **eth**: Ethereum integration layer using Reth
- **rpc**: JSON-RPC and gRPC interfaces

### Key Design Decisions
1. **No Events**: Contracts avoid events to save gas
2. **Explicit Imports**: No auto-exports in contracts
3. **Custom Auth**: Uses controller logic instead of standard Ownable
4. **Economic Security**: Relies on staked nodes for censorship resistance
5. **Uniform Clearing**: Batches limit orders at common prices to prevent MEV

## Testing Strategy

- Unit tests in each crate/contract
- Integration tests for cross-module functionality
- Invariant tests for critical contract properties
- FFI tests using Python scripts for complex scenarios
- Testnet binary for end-to-end testing

## Important Notes

1. **Dependencies**:
   - Requires Rust 1.88.0+ (edition 2024)
   - Requires Foundry for contracts
   - Requires Python 3.12 for FFI tests
   - Requires nightly Rust for formatting
   - Requires `just` command runner for simplified development workflow

2. **Assumptions**:
   - Only standard ERC20 tokens (no fee-on-transfer)
   - Deployment only on Ethereum L1 mainnet or canonical testnets
   - Nodes must provide adequate stake for slashing

3. **Performance Profiles**:
   - `dev`: Development with some optimizations
   - `release`: Standard release build
   - `maxperf`: Maximum performance with aggressive optimizations

4. **Known Limitations**:
   - Limited encoding capabilities (intentional for gas)
   - Single Uniswap AMM pool configuration at a time
   - No cross-pair price consistency guarantees

## Abrigo Operating Framework: (Y, M, X) Triples for Permissionless Convex Hedges

**Highest-level goal**: minimize income inequality, framed in post-Keynesian terms — distribution is institutionally determined, not equilibrium-given. The product family contributes to this goal by altering the institutional structure that currently blocks wage earners from accumulating productive capital.

**Instrument family**: permissionless on-chain perpetual convex instruments, settled on **Panoptic** (perpetual options written on Uniswap v3/v4 LP positions). The denomination of any given hedge — Mento-native (COPm, BRLm, KESm, EURm, USDm), USDC, ETH, sectoral basket tokens, or any Panoptic-eligible pair — is a *parameter of each iteration*, selected to fit the target population. Mento-native is one valid denomination family among many, not a framework-level constraint.

**Ideal-scenario modeling permitted (Panoptic-liquidity caveat).** Panoptic deployment liquidity is structurally thin today (M-search agent 2026-04-27 confirmed only wTAO + ASI on Ethereum-side, ~$200K TVL; first-of-kind for any synthetic-index deployment). The framework permits — and at this stage *requires* — modeling the **ideal scenario** in which the proposed instrument settles cleanly with adequate liquidity. The empirical β-estimate work (does the underlying microeconomic risk admit a positive measurable beta?) is independent of actual on-chain deployment; the M-design step proposes the ideal settlement architecture; only the deployment step requires real LP capital. Per Phase-A.0 lessons, conflating the empirical-validation step with the deployment-feasibility step is what produced the over-engineered slow-lane P1 apparatus that eventually parked. **Stage-correctly with explicit exit criteria:** empirical risk validation FIRST (exit: positive-β confirmation on the chosen X at conventional significance), ideal-scenario M sketch SECOND (exit: a Panoptic-position construction that *would* settle the empirical β if deployed; no liquidity sourcing required), deployment LAST (exit: live LP capital + execution test). Stage drift (M-design ballooning back into apparatus) is itself a Phase-A.0 failure mode and is anti-fishing-banned.

**Transmission channel — wage → productive capital via premium-funded ratchet (self-LBM)**: the perpetual hedge functions as a self liquidity-bootstrapping mechanism for the *holder*. A wage earner pays a small recurring premium out of wage income; the instrument's accumulated convex payoff and roll yield convert over time into productive-capital exposure. The hedge's existence is what *creates* the capital position — absent the instrument, the wage earner never crosses the wage/capital boundary because the macro risks (X) along the path are unbearable from a pure-savings start. This is the premium-funded ratchet design, not up-front capital protection.

**Operating unit of work — (Y, M, X) triples**:

- **Y** = outcome variable on which a target population's exposure to the wage→capital transition is measured. Examples: realized volatility of a household consumption basket; cross-sectional differential between productive-capital returns and wage-indexed CPI; entrepreneurship-failure indicators.
- **M** = the Panoptic pool configuration that hosts the hedge — the underlying token pair, the strike/range geometry of the deployed position, and the payoff shape (long-gamma covered call, range LP, perpetual put, straddle, etc.). M choice is constrained by Panoptic's pool mechanics: the (Y, X) pair must admit a continuous on-chain reference price representable as a Panoptic position. Off-Panoptic venues (custom v4 hooks, Carbon DeFi, Bunni-v2) are out of scope for the framework.
- **X** = the *major risk* that currently blocks the target population's wage→capital transition. First-cut iteration question is always: "what kills wage earners' attempts to enter productive-capital ownership for *this* population?" X identification is empirical and must precede M selection.

**Iteration order (default — target-population dominant)**: fix the population → fix Y on a candidate inequality/transition-exposure measure → enumerate X candidates from the empirical risk surface → for each surviving X, search Panoptic-eligible M for tradability. The (Y, X) pair only graduates to instrument design once a Panoptic position with viable convex pricing exists. Closed iterations (gate verdict FAIL) inform the X-search prior for the next population, not silent re-runs of the same (Y, X) at different thresholds — Phase-A.0 anti-fishing invariants carry forward.

**Active iteration (as of 2026-04-27, late evening update — target narrowed)**:

- **Last decision (2026-04-27 PM, late evening):** Pair D committed as the active (Y, X) per BPO literature-pass agent's rank-1 recommendation (output at `contracts/.scratch/2026-04-27-colombian-bpo-non-industrialization-hedge-research.md`, 5,620 words). Literature anchors GROUNDED in the BPO research note (35-year evidence base including Colombia-specific Mendieta-Muñoz 2017 + Philippines BPO direct-mechanism validation; full citations + author-list reconciliation pending in research note).

- **Target population:** Colombian young workers employed by US companies in the **service sector** (BPO, call centers, sales outsourcing, business process outsourcing). Mechanism (literature-confirmed): US service-sector productivity is structurally low (Baumol cost disease); US wage inflation in services widens US-Colombia service-wage arbitrage; BPO offshoring to Colombia accelerates; young Colombian workers absorbed into low-productivity BPO labor with no path to industrial / capital ownership (premature deindustrialization trap, Rodrik 2016 lineage; Colombian deindustrialization traces to 1990 Apertura under Gaviria per Mendieta-Muñoz 2017).

- **Committed (Y, X) — Pair D:**
   - **Y = Colombian young-worker services-sector employment share** (DANE GEIH monthly micro-data; "young" likely 15-24 or 18-29 — exact age band pending GEIH feasibility check). Captures the structural-transformation indicator: trap-tightening = young-worker share in services rises as alternatives shrink.
   - **X = COP/USD lagged 6-12 months.** Reuses closed FX-vol-CPI pipeline series. Literature-grounded via the Baumol → arbitrage → offshoring transmission chain; sign expectation pre-pinned positive (devaluation → cheaper Colombian labor in USD terms → more US offshoring → higher young-worker services share at lag).
   - Sign expectation: β > 0 at conventional significance.

- **Pre-pinned escalation contingency (per Phase-A.0 §11.A convex-payoff insufficiency caveat):** simple OLS mean-β may FAIL (as it did on Carbon-X_d). If β̂ is statistically indistinguishable from zero in mean-OLS, the framework pre-authorizes escalation to convex-payoff evidence: quantile regression on Y, GARCH-X variance specification, and lower-tail / extreme-value analysis of the (X, Y) joint distribution. This escalation is NOT a rescue claim — it tests the convex-instrument fitness directly, which is the ultimately load-bearing question for the perpetual-options M sketch.

- **M (ideal scenario, no actual deployment required):** Panoptic perpetual on a Colombian-structural-transformation index referenced to Y. Liquidity *modeled* not required per the ideal-scenario clause in the framework section above (under "Instrument family"); M sketch follows after empirical β confirmation per stage discipline.

- **Data assets — GEIH FEASIBILITY CONFIRMED (2026-04-27 PM):** closed FX-vol-CPI pipeline (Colombia 2008-2026 — COP/USD, Banrep CPI) — COP/USD series ready for X. **DANE GEIH micro-data is FEASIBLE-WITH-CAVEATS** per Data Engineer report at `contracts/.scratch/2026-04-27-dane-geih-y-feasibility.md`. Pinned spec parameters: youth band = **14-28** (Ley 1622 de 2013, DANE published convention); sector = **CIIU Rev. 4 A.C. sections G-T (broad services)** primary, **J+M+N (BPO-narrow)** as pre-registered sensitivity; ~218 monthly observations (Aug 2006-present, Jan 2008 cleanest start) well above N_MIN=75; Y empirically bounded [0.55, 0.75] → logit-transformed Y as technically correct primary specification; access friction LOWER than Banrep API (plain CSV ZIP, no auth, no rate limit). **Dominant caveat:** 2021 Marco-2005 → Marco-2018 methodology break — simple-β spec MUST pre-commit one of {apply DANE empalme factor / 2021 regime dummy / restrict to ≥2022}; restrict-to-≥2022 collapses N to ~51 (below N_MIN=75) and is therefore NOT viable. Mento on-chain flows (COPm transfers, Carbon DeFi β-track) retained as future-iteration assets.

- **Stage goal per user directive (2026-04-27):** identify ONE empirically-validated microeconomic risk + simple positive-β confirmation → start protocol design. Pair D commits the empirical-validation step's input; β confirmation unblocks M sketch; M sketch unblocks protocol design.

- **Slow lane (PARKED):** AI-cost X via Bittensor SN18 — P1 spec sha256-pinned (`f855e036d3c7807e2bef414a91a806caec1279a9d83575020bc2b3e82b47aeab`) but execution deferred. May reactivate as second instrument family if Pair D track succeeds.

- **Prior fast-lane work disposition (anti-fishing transparency, per RC + WA convergent flag):** **FX-X re-elevated from "demoted X-C" to active primary X.** COP/USD is the same variable that powered the closed FX-vol-on-CPI-surprise pipeline (gate verdict FAIL 2026-04-19); Pair D re-tests it under a *different* transmission hypothesis (Baumol → US-Colombia wage arbitrage → offshoring-demand lagged 6-12mo, with Y = Colombian young-worker services-sector share — NOT the prior FX-vol-on-CPI-surprise hypothesis). The prior FAIL does not taint the new test (different Y, different mechanism, different lag structure), but the re-use of the FX variable is acknowledged explicitly per anti-fishing transparency. Y1 RWC-USD **dropped** (not represented in Pair D; recoverable later via explicit re-promotion). Class 1/3/4 M-search findings **retained** as ideal-scenario design inputs for the M sketch step. X-A/B/D and Y-α/γ from prior preliminary lists **dropped** (Pair D supersedes; agent's report enumerated 5 pairs ranked, Pair D was rank-1 by Panoptic-eligibility).

- **Pending:** (1) ~~DANE GEIH micro-data feasibility check~~ **CONFIRMED 2026-04-27 PM** (FEASIBLE-WITH-CAVEATS; see Data assets bullet above); (2) v2 verification policy (still paused); (3) M framework-scope A/B/C decision — MOOT under ideal-scenario clause until M-sketch graduates to deployment; (4) **NEXT ACTION:** author simple-β spec via writing-plans skill (single OLS or logit-OLS, pre-registered, conventional α=0.05 two-sided, sign expectation positive, Methodology-break disposition pre-pinned to {empalme / 2021-dummy} — NOT restrict-to-≥2022 which fails N_MIN); (5) once simple-β executes and returns, either commit M sketch (PASS) or escalate to convex-payoff evidence per pre-pinned contingency above (FAIL).

## FX-vol-on-CPI-surprise Notebook Pipeline (Colombia, 2008-2026) — CLOSED 2026-04-19

A 33-task / 4-phase structural-econometric pipeline answers the question: do Colombian CPI AR(1) surprises cause a statistically detectable increase in weekly COP/USD realized volatility? The pre-committed Rev 4 spec fixes a one-sided T3b gate on β̂_CPI in an OLS of RV^(1/3) on CPI surprise plus six controls; reconciliation with a co-primary GARCH(1,1)-X and a PPI-decomposition block is required. Three frozen notebooks emit five artifacts and a machine-readable verdict. The project closed with `gate_verdict = "FAIL"` (β̂_CPI = −0.000685, 90% CI = [−0.003635, 0.002265], n = 947; reconciliation AGREE; all thirteen primary + sensitivity rows plotted in a pre-registered forest). The anti-fishing protocol halted §9 material-mover spotlight under T3b-FAIL; A1 (monthly cadence) and A4 (release-day-excluded) are preserved in §8 as pivot candidates, not rescue claims.

- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md` — Jinja2 auto-rendered summary (product-facing)
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` — final scientific verdict (FAIL)
- `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` — Rev 4 spec (pre-committed, reviewer-accepted)
- `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md` — 33-task implementation plan

## Abrigo Phase-A.0 Active Work (Y₃ × X_d structural econometrics) — IN PROGRESS as of 2026-04-26

The active analytical work is the Abrigo macro-hedge structural econometrics under the Phase-A.0 plan. Rev-2 mean-β regression closed with **gate verdict T3b = FAIL** (β̂ = −2.7987e−8, n = 76, T1 REJECTS predictive-not-structural). Per spec §11.A convex-payoff insufficiency caveat, mean-β was always first-stage / linear-hedge calibration only; Rev-3 ζ-group (quantile / GARCH-X / lower-tail / option-implied vol) is where convex-instrument fitness gets tested.

User-picked α + β parallel tracks per HALT-disposition:
- **α-track** = Rev-2 notebook migration (Task 11.O.NB-α; 31 dispatch units across 3 notebooks + README) + Rev-3 ζ-group convex-payoff extensions (Task 11.O.ζ-α; held for user-driven structural-econometrics interactive flow per ε deferral)
- **β-track** = Mento user-base research (Task 11.P.MR-β COMPLETED) → cCOP-vs-COPM provenance audit (Task 11.P.MR-β.1; BLOCKING for spec) → β hypothesis spec (Task 11.P.spec-β) → β execution (Task 11.P.exec-β)

User scope-tightening 2026-04-25: **Mento-native ONLY**. The Mento-native Colombia token is **COPM** at `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` (per Rev-5.3.4 CORRIGENDUM; cCOP and Minteo-fintech tokens are out of scope).

**SUPERSEDED 2026-04-27** — see "Abrigo Operating Framework" section above. The framework generalizes denomination as a per-iteration parameter; Mento-native is one valid family among many, not a global constraint. The `0xc92e8fc2…` COPM attribution above is also stale per Rev-5.3.5 β-corrigendum: canonical Mento V2 `StableTokenCOP` is `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`; `0xc92e8fc2…` is Minteo-fintech (out of Mento-native scope). Both lines preserved for historical accuracy of what governed Phase-A.0 Rev-2 work; neither binds active iterations as of 2026-04-27.

### Active plan + sub-plans

- `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — major plan (canonical source of truth); Rev-5.3.4 latest
- `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` — α-track NB-α sub-plan (467 lines, 31 dispatch units, converged)
- `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — β-track MR-β.1 sub-plan (319 lines, 5 sub-tasks, converged)

### Active design docs (immutable)

- `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` — Y₃ design (4-country panel, 60/25/15 WC-CPI weights)
- `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` — X_d design (Carbon basket user volume)

### Active analytical artifacts (Rev-2 baseline; binding for migration)

- `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` — Track A Rev-2 spec (655 lines, 14-row resolution matrix, §10.6 ζ-group roadmap, §11.A convex-payoff caveat)
- `contracts/.scratch/2026-04-25-task110-rev2-data/` — 14 panel parquets (Phase 5a Data Engineer output)
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/{estimates,spec_tests,sensitivity,summary}.md` — Phase 5b Analytics Reporter outputs
- `contracts/.scratch/2026-04-25-task110-rev2-analysis/gate_verdict.json` — machine-readable FAIL verdict
- `contracts/.scratch/2026-04-25-task110-rev2-gate-fail-disposition.md` — HALT-disposition memo (5 pivot paths α/β/γ/δ/ε)

### Active research

- `contracts/.scratch/2026-04-25-mento-userbase-research.md` — Trend Researcher Mento ecosystem evidence (Findings 1-4; note: TR's Finding 3 cCOP/COPM attribution was inverted; Rev-5.3.4 corrigendum is authoritative override)

### Notebook scaffolding (in flight under Task 11.O.NB-α)

- `contracts/notebooks/abrigo_y3_x_d/` — env.py (parents-fix landed at `865402c2c`), references.bib, _nbconvert_template/, estimates/, figures/, pdf/

### Anti-fishing invariants (immutable through Rev-5.3.x)

- `N_MIN = 75`, `POWER_MIN = 0.80`, `MDES_SD = 0.40` SD-units of Y₃
- `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (sha256-pinned)
- Rev-4 `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`
- Rev-2 published 14-row resolution matrix is binding for migration (no re-estimation drift permitted)

### Stale `.scratch/` archived

Pre-Phase-A.0 scratch documents (2026-04-11 through 2026-04-19; 70 files including FX-vol-spec-review-* and tier1-* iterations) moved to `contracts/.scratch/archive-2026-04-pre-rev533/`. Active scratch is 2026-04-20 onwards.