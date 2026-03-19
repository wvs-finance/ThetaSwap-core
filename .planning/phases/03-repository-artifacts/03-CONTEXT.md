# Phase 3: Repository Artifacts - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Create two READMEs (root and research) and document the demo. Root README is the project landing page — brief, strategic, with diagrams. Research README organizes pointers to all research artifacts. Demo is a section in root README with the forge command and what to look for. No new code, no Solidity, no slides.

</domain>

<decisions>
## Implementation Decisions

### Root README structure
- **One paragraph** project overview — what ThetaSwap is, adverse competition oracle, orthogonal to LVR. Point to `research/README.md` for the full story.
- **Architecture section** — embed both mermaid diagrams from `docs/diagrams/context-diagram.md` and `docs/diagrams/sequence-diagram.md` inline
- **Quick Start / Demo section** — the forge command to run the NativeV4 integration test + 3-5 bullets explaining what each scenario demonstrates (swap updates A_T, mint increments N, burn triggers DeltaPlus)
- **Directory pointers** — strategic links to `research/`, `src/`, `test/`, `docs/` with one-line descriptions
- Sections in this order: Overview → Architecture → Demo → Directory

### Research README structure
- **Table of contents style** — minimal prose, organized links to artifacts with brief labels
- **Organized by domain**: Econometrics, Backtest, Model, Data
- Each domain: brief one-line summary + list of key files/modules with one-line descriptions
- **Mathematical notation**: prose description + key equations in collapsible `<details>` blocks (A_T definition, Delta+, turning point formula) — GitHub renders LaTeX math
- Points to notebooks, econometrics modules, model LaTeX, data fixtures

### Demo documentation
- **Lives in root README** under "Quick Start / Demo" section — most visible
- **The forge command** + 3-5 bullet points explaining what to look for in the output
- Test file: `test/fee-concentration-index-v2/protocols/uniswapV4/NativeV4FeeConcentrationIndex.integration.t.sol`
- Scenarios: swap updates A_T, mint increments position count N, burn triggers fee share computation and DeltaPlus derivation

### Claude's Discretion
- Exact wording of directory pointer descriptions
- Whether to include badges (build status, license) in root README
- Formatting details within the research README domains
- How to format the collapsible equation blocks

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 narrative (source content for root README paragraph)
- `research/narrative/problem.md` — Full problem statement; root README condenses Section 1 into one paragraph
- `research/narrative/research-summary.md` — Three-pillar research summary; research README points to this

### Phase 2 diagrams (embed in root README)
- `docs/diagrams/context-diagram.md` — Mermaid context diagram to embed inline
- `docs/diagrams/sequence-diagram.md` — Mermaid sequence diagram to embed inline

### Existing README (will be overwritten)
- `README.md` — Current root README; read before replacing to preserve any useful content

### Demo test (document in root README)
- `test/fee-concentration-index-v2/protocols/uniswapV4/NativeV4FeeConcentrationIndex.integration.t.sol` — The integration test to run for the demo

### Research artifacts (research README points to these)
- `research/model/main.pdf` — Compiled mathematical specification
- `research/model/main.tex` — LaTeX master document
- `research/model/econometrics.tex` — Full econometric specification
- `research/model/payoff.tex` — FCI definition, co-primary state, price mapping
- `research/notebooks/eth-usdc-insurance-demand-identification.ipynb` — Demand identification notebook
- `research/notebooks/eth-usdc-backtest.ipynb` — Backtest notebook
- `research/backtest/` — 8 Python modules (daily, sweep, calibrate, payoff, plotting)
- `research/econometrics/` — 13 Python modules (types, data, ingest, hazard)
- `research/data/` — Fixtures, raw events, queries, oracle scripts
- `research/figures/` — 4 publication-style PNGs from Phase 1

### Project structure reference
- `CLAUDE.md` — Project structure section defines the directory layout
- `.planning/codebase/STRUCTURE.md` — Detailed directory analysis

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `research/narrative/problem.md` Section 1 — condense into root README paragraph
- `docs/diagrams/*.md` — mermaid source to embed directly (copy fenced code blocks)
- `CLAUDE.md` project structure section — basis for directory pointers

### Established Patterns
- Current README.md exists but will be largely rewritten; preserve forge commands if still valid
- `research/` directory has no README.md yet — creating from scratch
- Mermaid diagrams are already GitHub-compatible fenced code blocks

### Integration Points
- Root README → links to `research/README.md`
- Root README → embeds mermaid from `docs/diagrams/`
- Root README → references `test/` for demo
- Research README → links to all `research/` subdirectories and key files

</code_context>

<specifics>
## Specific Ideas

- Root README should feel like a landing page — someone finds the repo, reads one paragraph, sees the architecture, knows how to run the demo, and can navigate to details
- Research README is for someone who wants to dig into the research — they should find every artifact organized by domain without hunting

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-repository-artifacts*
*Context gathered: 2026-03-18*
