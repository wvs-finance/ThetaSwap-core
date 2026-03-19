# FCI System Context Diagram

The FCI architecture is a delegation chain: external sources (PoolManager for V4-native, Reactive Network for cross-chain) trigger callbacks, which invoke the FCI Algorithm. The algorithm `delegatecall`s into protocol facets that adapt protocol-specific data to the algorithm's interface.

```mermaid
flowchart LR
    %% ── External sources ──
    PM["PoolManager<br/><i>(V4 native)</i>"]
    RN["Reactive Network<br/><i>(cross-chain pools)</i>"]

    %% ── Callback layer ──
    CB["Callback<br/><i>IHooks interface</i><br/>afterSwap · afterAdd<br/>beforeRemove · afterRemove"]

    %% ── Core algorithm ──
    ALG["FCI Algorithm<br/><i>FeeConcentrationIndexV2.sol</i><br/>fee share · theta weight<br/>A_T accumulation"]

    %% ── Protocol facet ──
    FACET["Protocol Facet<br/><i>IFCIProtocolFacet</i>"]

    %% ── Facet responsibilities ──
    ADAPT["poolRpc → poolId / PoolKey<br/>protocolEventData → hookCalldata<br/>protocol storage slot"]

    %% ── Flow ──
    PM -- "hook call" --> CB
    RN -- "reactive callback" --> CB
    CB -- "call" --> ALG
    ALG -- "delegatecall" --> FACET
    FACET --- ADAPT

    %% ── Styling ──
    classDef source fill:#e2e3e5,stroke:#383d41,stroke-width:1px,color:#383d41
    classDef callback fill:#d1ecf1,stroke:#0c5460,stroke-width:2px,color:#0c5460
    classDef algo fill:#d4edda,stroke:#28a745,stroke-width:3px,color:#155724
    classDef facet fill:#cce5ff,stroke:#004085,stroke-width:2px,color:#004085
    classDef adapt fill:#fff3cd,stroke:#856404,stroke-width:1px,color:#856404,font-style:italic

    class PM,RN source
    class CB callback
    class ALG algo
    class FACET facet
    class ADAPT adapt
```
