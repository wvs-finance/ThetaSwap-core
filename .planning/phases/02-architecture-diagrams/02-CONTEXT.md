# Phase 2: Architecture Diagrams - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Create two mermaid diagrams (context + sequence) that visually communicate the FCI system architecture and pool listening flow. Diagrams render in GitHub README markdown and export to PNG for Beamer slides. No code changes, no narrative writing — pure diagramming.

</domain>

<decisions>
## Implementation Decisions

### Context diagram scope
- **Vault and CFMM appear as dashed boxes** labeled "planned" — honest about implementation status while showing the full vision
- **Reactive Network embedded inside the V3 adapter** subgraph — simplifies the diagram by not exposing cross-chain details at this level
- **Generic "Protocol N" dashed adapter box** included — communicates the modular/pluggable design (any protocol can integrate)
- **External actors included**: Passive LP (PLP), Underwriter, and Trader as labeled boxes interacting with the system
- Components: FCI Hook (orchestrator), V4 Adapter (native), V3 Adapter (with Reactive Network inside), Protocol N (dashed), Vault (dashed), CFMM (dashed)

### Sequence diagram depth
- **Starts with listenPool()** — shows the subscription/registration model
- **Depth: to metric output** — Event → hook callback → facet dispatch (delegatecall) → A_T update → DeltaPlus derivation. Abstracts storage details.
- **One representative flow** (swap) — note that mint/burn follow same pattern
- **Modularity is the key message**: FeeConcentrationIndexV2 is protocol-agnostic, it delegatecalls into protocol facets for all protocol-specific behavior (position key derivation, fee growth reads, tick reads)
- **New protocols implement IFCIProtocolFacet** (extends IHooks) in `protocols/` directory — the V3 pattern is the reference implementation
- **Participants**: FCI Hook (Orchestrator), Protocol Facet, External Reader (queries DeltaPlus)
- Flow: listenPool() → FCI V2 registers pool → on swap: FCI V2 receives afterSwap → delegatecall to protocol facet → facet reads protocol state → FCI V2 updates A_T, ThetaSum, N → External Reader queries DeltaPlus

### Diagram aesthetics
- **Status colors**: Live components = solid (green/blue), Planned components = dashed (orange/gray) for Vault, CFMM, Protocol N
- **Edge labels**: Plain English with function name in parentheses — "tracks metrics (afterSwap())", "reads fees (delegatecall)" — serves both technical and non-technical audience
- Mermaid fenced code blocks in markdown for README rendering
- PNG export via mermaid-cli (npx @mermaid-js/mermaid-cli) for Beamer inclusion

### Claude's Discretion
- Exact mermaid syntax choices (flowchart vs C4 vs graph)
- Subgraph grouping strategy
- Arrow styling and direction
- PNG export resolution and sizing

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### FCI V2 architecture (defines the delegation pattern the diagram must show)
- `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` — Orchestrator: hook callbacks, delegatecall dispatch, metric computation
- `src/fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol` — The interface new protocols implement (extends IHooks)
- `.planning/codebase/ARCHITECTURE.md` — Full architecture analysis with layers, data flow, entry points

### Protocol facets (reference implementations the diagram depicts)
- `src/fee-concentration-index-v2/protocols/uniswap-v4/` — Native V4 facet (direct integration)
- `src/fee-concentration-index-v2/protocols/uniswap-v3/` — V3 facet with reactive network integration (cross-chain bridge)

### Mathematical model (defines the metric output shown at diagram endpoint)
- `research/model/payoff.tex` §1.2 — Co-primary state variables (A_T, ThetaSum, N) that the hook tracks
- `research/model/payoff.tex` §1.3–1.4 — DeltaPlus derivation and price mapping (the output an external reader queries)

### Prior phase narrative (provides the story context diagrams support)
- `research/narrative/problem.md` — Problem framing the diagrams visualize
- `.planning/phases/01-problem-research-narrative/01-CONTEXT.md` — Phase 1 decisions (publication style, mermaid→PNG export)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `IFCIProtocolFacet.sol` interface — 62 lines, extends IHooks with 20+ behavioral functions that protocol facets implement via delegatecall
- `FeeConcentrationIndexV2.sol` — The orchestrator with afterSwap, afterAddLiquidity, afterRemoveLiquidity handlers that dispatch to facets
- Two working protocol implementations: `uniswap-v4/NativeUniswapV4Facet.sol` and `uniswap-v3/UniswapV3Facet.sol`

### Established Patterns
- Protocol dispatch via `bytes2` flag in hookData (first 2 bytes identify which protocol facet to delegatecall)
- Diamond storage pattern: keccak256-derived disjoint slots per facet/namespace
- Free functions (not libraries) for reusable logic

### Integration Points
- Context diagram components map 1:1 to the Architecture layers in `.planning/codebase/ARCHITECTURE.md`
- Sequence diagram participants map to the call chain: PoolManager → FCI V2 (hook) → Protocol Facet (delegatecall)
- External Reader maps to view functions on FCI V2 that return A_T, ThetaSum, N, DeltaPlus

</code_context>

<specifics>
## Specific Ideas

- The modularity story is central: "implement IFCIProtocolFacet, drop your facet in protocols/, and the FCI tracks your pool's metrics" — this is what the generic "Protocol N" box communicates
- V3 adapter pattern as the reference: it shows that even cross-chain protocols can integrate via the Reactive Network bridge
- Dashed Vault + CFMM boxes connected to actors (PLP deposits, Underwriter provides USDC) hint at the insurance mechanism without claiming it's built

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-architecture-diagrams*
*Context gathered: 2026-03-18*
