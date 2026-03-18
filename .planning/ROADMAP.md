# Roadmap: ThetaSwap Presentation

## Overview

Transform ThetaSwap's research, architecture, and implementation into a cohesive presentation package. The work flows from research synthesis (the foundation narrative) through architecture diagrams, into repository artifacts (dual READMEs, demo), and culminates in a LaTeX Beamer slide deck that ties everything together.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Problem & Research Narrative** - Synthesize econometric research into presentation-ready problem statement and research summary (completed 2026-03-18)
- [ ] **Phase 2: Architecture Diagrams** - Create mermaid context and sequence diagrams showing FCI system architecture and pool listening flow
- [ ] **Phase 3: Repository Artifacts** - Create root README (architecture + pointers), research README (detailed findings + artifact links), and document the demo
- [ ] **Phase 4: Beamer Slide Deck** - Produce LaTeX Beamer .tex file with problem, research, solution, demo, and roadmap frames

## Phase Details

### Phase 1: Problem & Research Narrative
**Goal**: Audience understands adverse competition as a distinct LP risk and sees the empirical evidence supporting ThetaSwap's approach
**Depends on**: Nothing (first phase)
**Requirements**: PROB-01, PROB-02, PROB-03
**Success Criteria** (what must be TRUE):
  1. A reader with no DeFi background can explain in one sentence what adverse competition risk is and why it differs from impermanent loss
  2. The research summary includes the inverted-U finding, turning point delta* ~ 0.09, and the key statistics (41 days, 600 positions, 2.65x real vs null)
  3. Problem and research narrative exists as standalone text that downstream phases (READMEs, Beamer) can consume
**Plans:** 2/2 plans complete

Plans:
- [ ] 01-01-PLAN.md — Write adverse competition problem narrative and three-pillar research summary (2 markdown files in research/narrative/)
- [ ] 01-02-PLAN.md — Add publication rcParams to plotting.py, update notebooks with figure export, generate 4 PNGs in research/figures/

### Phase 2: Architecture Diagrams
**Goal**: System architecture is visually communicable through two mermaid diagrams that work in GitHub markdown
**Depends on**: Nothing (independent of Phase 1 content, but Phase 1 informs narrative framing)
**Requirements**: ARCH-01, ARCH-02, ARCH-03
**Success Criteria** (what must be TRUE):
  1. Context diagram shows FCI Hook, Vault, CFMM, Protocol Adapters (V3, V4), and Reactive Network with their relationships
  2. Sequence diagram traces the full pool listening flow from listenPool() through swap/mint/burn events to metric update and DeltaPlus derivation
  3. Both diagrams render correctly when viewed on GitHub (mermaid fenced code blocks in markdown)
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

### Phase 3: Repository Artifacts
**Goal**: Two READMEs serve distinct audiences (root = strategic overview, research = detailed findings) and the demo is documented so anyone can run it
**Depends on**: Phase 1 (narrative content), Phase 2 (diagrams for root README)
**Requirements**: ROOT-01, ROOT-02, ROOT-03, RREAD-01, RREAD-02, RREAD-03, DEMO-01, DEMO-02
**Success Criteria** (what must be TRUE):
  1. Root README.md contains a brief project description, Architecture section with both mermaid diagrams embedded and rendering, and strategic pointers to research/, src/, test/
  2. Root README is accessible to a mixed audience -- brief and high-level, not dense
  3. research/README.md provides detailed research summary organized by domain (econometrics, backtest, model, data) with pointers to actual artifacts (notebooks, modules, LaTeX, fixtures)
  4. A developer unfamiliar with the project can find and run the demo test using only the documented forge command, and the demo shows FCI tracking through swap, mint, and burn scenarios on V4
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Beamer Slide Deck
**Goal**: Complete LaTeX Beamer .tex file exists with all presentation frames -- compilable to PDF
**Depends on**: Phase 1 (narrative), Phase 2 (diagrams), Phase 3 (demo)
**Requirements**: BEAM-01, BEAM-02, BEAM-03, BEAM-04, BEAM-05
**Success Criteria** (what must be TRUE):
  1. Problem frame(s) synthesize adverse competition from the Phase 1 narrative in a way accessible to a mixed audience
  2. Research summary frame(s) present approach, key results (inverted-U, turning point, demand identification), and statistics
  3. Solution frame(s) reference the architecture diagram and explain FCI Hook, reactive adapter, and cross-protocol design
  4. Demo frame(s) include step-by-step instructions for running and narrating the integration test
  5. Roadmap frame(s) list missing CFMM and vault/settlement as clear next steps, not blockers
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Problem & Research Narrative | 0/2 | Complete    | 2026-03-18 |
| 2. Architecture Diagrams | 0/1 | Not started | - |
| 3. Repository Artifacts | 0/3 | Not started | - |
| 4. Beamer Slide Deck | 0/2 | Not started | - |
