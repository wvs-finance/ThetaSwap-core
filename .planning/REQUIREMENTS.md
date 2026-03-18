# Requirements: ThetaSwap Presentation

**Defined:** 2026-03-18
**Core Value:** Communicate that ThetaSwap builds the first on-chain adverse competition oracle enabling LP hedging — orthogonal to LVR

## v1 Requirements

### Problem Synthesis

- [x] **PROB-01**: Presentation opens with the adverse competition problem — fee concentration is orthogonal to LVR, passive LPs face a risk no existing product hedges
- [x] **PROB-02**: Research summary covers the quadratic deviation hazard model, inverted-U finding, turning point delta* ~ 0.09
- [x] **PROB-03**: Key statistics presented accessibly (41 days, 600 positions, 2.65x real vs null A_T, 63% of days with positive deviation)

### Architecture Diagrams

- [x] **ARCH-01**: Context diagram (mermaid) showing FCI Hook, Vault, CFMM, Protocol Adapters (V3, V4), and Reactive Network
- [x] **ARCH-02**: Sequence diagram (mermaid) for pool listening flow: listenPool() -> swap/mint/burn events -> metric update -> DeltaPlus derivation
- [x] **ARCH-03**: Diagrams render correctly in GitHub README markdown

### Root README

- [ ] **ROOT-01**: Root README.md has brief project description and Architecture section with both mermaid diagrams
- [ ] **ROOT-02**: Root README contains strategic pointers to sections of interest (research/, src/, test/)
- [ ] **ROOT-03**: Root README is accessible to mixed audience — brief, high-level, not dense

### Research README

- [ ] **RREAD-01**: research/README.md provides detailed research summary (problem, methodology, key findings)
- [ ] **RREAD-02**: research/README.md has pointers to actual artifacts: notebooks, econometrics modules, model LaTeX, data fixtures
- [ ] **RREAD-03**: research/README.md organized by research domain (econometrics, backtest, model, data)

### Demo

- [ ] **DEMO-01**: Demo script documented — runs NativeV4FeeConcentrationIndex.integration.t.sol with forge command
- [ ] **DEMO-02**: Demo shows FCI tracking through real swap/mint/burn scenarios on V4

### Beamer Slides

- [ ] **BEAM-01**: LaTeX Beamer .tex file with problem frame(s) synthesized from research
- [ ] **BEAM-02**: LaTeX Beamer research summary frame(s) (approach, key results, demand identification)
- [ ] **BEAM-03**: LaTeX Beamer solution frame(s) with architecture diagram reference
- [ ] **BEAM-04**: LaTeX Beamer demo frame(s) with run instructions
- [ ] **BEAM-05**: LaTeX Beamer roadmap frame(s) — missing CFMM, missing vault/settlement, framed as next steps

## v2 Requirements

### Extended Presentation

- **EPRE-01**: Video recording of demo walkthrough
- **EPRE-02**: Appendix frames with full econometric tables
- **EPRE-03**: Interactive notebook demo (Jupyter) for live audience

## Out of Scope

| Feature | Reason |
|---------|--------|
| New Solidity contracts | Presentation prep only — no contract changes |
| CFMM implementation | Roadmap item to mention, not deliver |
| Vault/settlement implementation | Roadmap item to mention, not deliver |
| Re-running econometrics | Research is complete, we synthesize existing results |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROB-01 | Phase 1 | Complete |
| PROB-02 | Phase 1 | Complete |
| PROB-03 | Phase 1 | Complete |
| ARCH-01 | Phase 2 | Complete |
| ARCH-02 | Phase 2 | Complete |
| ARCH-03 | Phase 2 | Complete |
| ROOT-01 | Phase 3 | Pending |
| ROOT-02 | Phase 3 | Pending |
| ROOT-03 | Phase 3 | Pending |
| RREAD-01 | Phase 3 | Pending |
| RREAD-02 | Phase 3 | Pending |
| RREAD-03 | Phase 3 | Pending |
| DEMO-01 | Phase 3 | Pending |
| DEMO-02 | Phase 3 | Pending |
| BEAM-01 | Phase 4 | Pending |
| BEAM-02 | Phase 4 | Pending |
| BEAM-03 | Phase 4 | Pending |
| BEAM-04 | Phase 4 | Pending |
| BEAM-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 after roadmap revision (Beamer + dual README)*
