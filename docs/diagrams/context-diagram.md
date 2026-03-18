# FCI System Context Diagram

The Fee Concentration Index (FCI) Hook is a protocol-agnostic orchestrator that tracks adverse selection metrics across any DEX protocol. It dispatches behavioral calls via `delegatecall` to registered protocol facets, each implementing `IFCIProtocolFacet`. The diagram below shows all live integrations (solid borders), planned components (dashed borders), and external actors who interact with the system.

**Legend:** Solid border = live on testnet. Dashed border = planned / not yet deployed. Edge labels show plain-English description with Solidity function name in parentheses where applicable.

```mermaid
flowchart TB
    %% ── Actors ──
    PLP["PLP (Passive LP)"]
    UW["Underwriter"]
    TR["Trader"]

    %% ── Central orchestrator ──
    FCI["FCI Hook<br/>(Orchestrator)<br/><i>FeeConcentrationIndexV2.sol</i>"]

    %% ── Live protocol adapters ──
    V4["Uniswap V4 Adapter<br/><i>NativeUniswapV4Facet</i>"]

    subgraph V3Sub["Uniswap V3 Adapter"]
        V3Facet["UniswapV3Facet"]
        RN["Reactive Network<br/><i>UniswapV3Reactive +<br/>UniswapV3Callback</i>"]
    end

    %% ── Planned components ──
    PN["Protocol N<br/>(planned)"]
    VAULT["Token Vault<br/>(planned)<br/><i>CollateralCustodianFacet</i>"]
    CFMM["CFMM<br/>(planned)<br/><i>Price Discovery</i>"]

    %% ── Orchestrator to adapters ──
    FCI -- "tracks metrics<br/>(afterSwap() delegatecall)" --> V4
    FCI -- "bridges events<br/>(unlockCallbackReactive())" --> V3Sub
    FCI -. "implements IFCIProtocolFacet" .-> PN

    %% ── Orchestrator to downstream ──
    FCI -- "provides DeltaPlus oracle<br/>(getDeltaPlus())" --> VAULT

    %% ── Internal V3 adapter flow ──
    RN -- "V3 Swap log --> ReactVM --> Callback" --> V3Facet

    %% ── Vault ecosystem ──
    VAULT -. "price discovery" .-> CFMM

    %% ── Actor interactions ──
    PLP -- "deposits collateral" --> VAULT
    UW -- "provides USDC" --> VAULT
    TR -- "trades LONG/SHORT" --> CFMM

    %% ── Styling: live components ──
    classDef live fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
    classDef orchestrator fill:#cce5ff,stroke:#004085,stroke-width:3px,color:#004085
    classDef planned fill:#fff3cd,stroke:#856404,stroke-width:2px,stroke-dasharray:5 5,color:#856404
    classDef actor fill:#e2e3e5,stroke:#383d41,stroke-width:1px,color:#383d41
    classDef reactive fill:#d1ecf1,stroke:#0c5460,stroke-width:2px,color:#0c5460

    class FCI orchestrator
    class V4 live
    class V3Facet live
    class RN reactive
    class PN planned
    class VAULT planned
    class CFMM planned
    class PLP,UW,TR actor
```
