# Phase 4: Beamer Slide Deck - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce a compilable LaTeX Beamer .tex file with all presentation frames — problem, evidence, solution, demo, and roadmap. The .tex file uses content from Phases 1-3 (narrative, diagrams, plots). No new research, no code changes — pure LaTeX authoring.

</domain>

<decisions>
## Implementation Decisions

### Frame count and pacing
- **5-7 minute presentation** — ~10 frames total
- **Frame allocation**:
  1. Title (1 frame)
  2. Problem (2 frames — adverse competition framing + concrete LP example)
  3. Evidence (3 frames — model equation + coefficient table + inverted-U interpretation)
  4. Solution (2 frames — architecture context diagram + sequence/modularity)
  5. Demo (1 frame — forge command + what to look for)
  6. Roadmap (1 frame — what's built vs what's next)
- **One idea per frame** (locked from Phase 1)
- **Flat frames** — no \section navigation bar (locked from Phase 1)
- **Flow**: Problem → Evidence → Solution → Demo → Roadmap (locked from Phase 1)

### Beamer theme and branding
- **Theme**: Claude's discretion (pick something clean for dark blue + white)
- **Colors**: Dark blue + white — professional, works on any projector
- **Title slide**: "ThetaSwap: Adverse Competition Oracle"
- **Author**: ThetaSwap
- **Date**: \today

### Evidence frames (3 frames)
- **Frame 1**: Quadratic hazard model equation (main.pdf eq. 9) — the model specification
- **Frame 2**: Coefficient table (lag 1-3, Section 2.2) — the empirical results
- **Frame 3**: Inverted-U interpretation (shelter vs Capponi regime, turning point δ* ≈ 0.09) — the economic meaning
- Three pillars (demand exists / price exists / backtest validates) organize the evidence narrative (locked from Phase 1)

### Solution frames (2 frames)
- **Frame 1**: Architecture context diagram — include `docs/diagrams/context-diagram.png` via \includegraphics
- **Frame 2**: Sequence diagram showing modularity — include `docs/diagrams/sequence-diagram.png`

### Demo frame (1 frame)
- forge command for NativeV4FeeConcentrationIndex.integration.t.sol
- 3-5 bullets on what to look for (swap updates A_T, mint increments N, burn triggers DeltaPlus)

### Roadmap frame (1 frame)
- **Two-column layout**: "Built" (left) vs "Next" (right)
  - Built: FCI oracle live on V4, reactive adapter bridging V3 events, backtest validation (18.8% better off, +$23 mean HV)
  - Next: Linearized power-squared CFMM, vault settlement mechanism
- **Ambitious tone**: "The mathematical specification is complete, the oracle tracks metrics across protocols, and the next milestone delivers the full insurance product."

### LaTeX configuration
- Reuse macros from `research/model/preamble.tex` (\AT, \ATnull, \DeltaPlus, \ThetaSum, etc.)
- Include 4 backtest PNGs from `research/figures/` where relevant (dose-response in evidence, others as needed)
- Include 2 diagram PNGs from `docs/diagrams/` in solution frames
- Output file: `research/slides/presentation.tex` (create slides/ directory)

### Claude's Discretion
- Exact Beamer theme choice (within dark blue + white constraint)
- Which backtest plots to include on which frames (dose-response most likely on evidence frame 3)
- Font sizing for equations and tables
- Whether to include a "Thank You" / closing frame
- Exact wording of frame titles

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Narrative content (source for problem and evidence frames)
- `research/narrative/problem.md` — Full problem statement; frames 2-3 condense from this
- `research/narrative/research-summary.md` — Three-pillar structure; evidence frames draw from this

### Mathematical specification (source for equations and tables)
- `research/model/preamble.tex` — LaTeX macros to \input or copy into Beamer preamble
- `research/model/payoff.tex` — FCI definition (eq. 1), co-primary state (eq. 2-4), DeltaPlus (eq. 7), price mapping (eq. 8)
- `research/model/econometrics.tex` — Quadratic hazard model (eq. 9 equivalent), coefficient table, inverted-U interpretation
- `research/model/main.pdf` §2 — Econometric Calibration (rendered equations for reference)

### Visual assets (include via \includegraphics)
- `research/figures/dose-response.png` — Dose-response quartile chart
- `research/figures/trigger-days.png` — Daily Delta+ with trigger line
- `research/figures/alpha-sweep.png` — Alpha sweep comparison
- `research/figures/reserve-dynamics.png` — Seeded reserve trajectories
- `docs/diagrams/context-diagram.png` — Architecture context diagram (1584x445)
- `docs/diagrams/sequence-diagram.png` — Sequence diagram (1358x2196)

### Demo test (reference for demo frame content)
- `test/fee-concentration-index-v2/protocols/uniswapV4/NativeV4FeeConcentrationIndex.integration.t.sol`

### Prior phase contexts
- `.planning/phases/01-problem-research-narrative/01-CONTEXT.md` — All Phase 1 decisions (visual elements, research depth, narrative structure)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `research/model/preamble.tex` — All custom LaTeX macros (\AT, \ATnull, \DeltaPlus, \ThetaSum, \PosCount, \DeltaStar, etc.) — copy or \input into Beamer preamble
- `research/narrative/problem.md` — Pre-written problem narrative; adapt sections into frame content
- `research/narrative/research-summary.md` — Pre-written evidence with exact coefficient values and backtest results
- 6 PNG files ready for \includegraphics

### Established Patterns
- LaTeX compilation: `pdflatex` available system-wide (verified in Phase 1 research)
- Mathematical notation consistent across all .tex files via shared macros
- All equations already typeset in the model — can copy equation environments directly

### Integration Points
- Beamer preamble needs macro definitions from preamble.tex
- \includegraphics paths must be relative to the .tex file location (research/slides/)
- Compilation: `cd research/slides && pdflatex presentation.tex` (may need 2 passes for references)

</code_context>

<specifics>
## Specific Ideas

- The presentation tells the story: "There's a risk no one tracks → we proved it exists with data → we built an oracle that tracks it → here's it running → here's what's next"
- Evidence frames should feel like the best 3 slides from a research seminar — equation, data, interpretation
- Solution frames should show the architecture is real (live diagrams from actual contracts) not vaporware
- Roadmap frame should leave the audience thinking "they've done the hard part" (research + oracle), not "they haven't built it yet"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-beamer-slide-deck*
*Context gathered: 2026-03-18*
