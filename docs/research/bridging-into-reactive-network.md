# Bridging Data and Tokens INTO Reactive Network

**Date**: 2026-03-14
**Branch**: 005-frontend-spec-clean
**Status**: Research complete

---

## Executive Summary

Reactive Network's architecture is fundamentally **event-driven and inbound-only by design**. There is no general-purpose "send a message to Reactive" interface on origin chains. Instead, the primary mechanism for getting data INTO Reactive Network is **emitting events on an origin chain that a reactive contract has subscribed to**. For tokens, there is no programmatic on-chain bridge contract you call from Sepolia -- the official paths are the **Token Portal** (portal.reactive.network) for mainnet REACT, and a **faucet contract** for Lasna testnet lREACT. Hyperlane integration exists but currently flows **Reactive-to-origin** (outbound callbacks), not origin-to-Reactive.

This means the user's goal of "one transaction on Sepolia that sends calldata AND bridges tokens to Reactive" is **not natively supported**. However, there are practical patterns that achieve the same end result.

---

## 1. Reactive Network's Core Architecture: Events Are the Inbound Channel

### How Data Gets INTO Reactive

Reactive Network is not a traditional L2 with a bridge inbox. It operates as an **event indexer + autonomous execution layer**:

1. **Origin chain** emits an EVM event log (e.g., Uniswap V3 Swap event)
2. **Reactive Network's relayer** picks up the log and matches it against subscription criteria
3. **ReactVM** executes the `react()` method on the subscribed reactive contract, passing the log data
4. The reactive contract processes the event and optionally emits a **Callback** log
5. The Callback is transported (via Hyperlane or the legacy callback proxy) to the **destination chain**

The critical insight: **there is no step where an origin-chain contract "sends" anything to Reactive Network**. The origin chain simply emits events; the Reactive Network watches and reacts.

Reference: [Reactive Contracts documentation](https://dev.reactive.network/reactive-contracts), [Subscriptions](https://dev.reactive.network/subscriptions)

### System Contract Address

Both Reactive Mainnet and Lasna Testnet share the system contract / callback proxy address:

```
0x0000000000000000000000000000000000fffFfF
```

This is the address that reactive contracts on the Reactive Network interact with for:
- `subscribe()` / `unsubscribe()` -- registering event subscriptions
- `depositTo()` -- pre-funding subscription reserves
- `debt()` -- checking outstanding subscription debt

Reference: [Economy](https://dev.reactive.network/economy), [Reactive Mainnet / Lasna Testnet](https://dev.reactive.network/reactive-mainnet)

---

## 2. How ThetaSwap Currently Handles This

### Current Architecture (003-reactive-integration)

The existing ThetaSwap deployment uses this exact pattern:

**On Lasna (Reactive Network):**
- `ThetaSwapReactive` (at `0x302adeea6BE9a6e22f319f9ee2ABE1Be60Cc4C14`) subscribes to V3 pool events on Sepolia
- Its `react()` method processes Swap/Mint/Burn events and emits Callbacks
- Funded manually by the deployer EOA (`0xe69228626E4800578D06a93BaaA595f6634A47C3`) sending lREACT directly

**On Sepolia (Origin/Destination):**
- V3 Pool (`0xcB80f9b60627DF6915cc8D34F5d1EF11617b8Af8`) emits events -- this IS the "inbound data channel"
- `ReactiveHookAdapter` (`0xF3B1023A4Ee10CB8F51E277899018Cd6D2836071`) receives callbacks from the callback proxy
- Callback Proxy (`0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA`) delivers callbacks and calls `pay()`

**Funding flow:**
1. Developer gets Sepolia ETH from a faucet
2. Developer sends Sepolia ETH to the Reactive Faucet contract on Sepolia (`0x9b9BB25f1A81078C544C829c5EB7822d747Cf434`) -- exchange rate: 1 ETH = 100 lREACT
3. lREACT appears in the deployer's Lasna wallet
4. Developer sends lREACT to the ThetaSwapReactive contract address on Lasna (either directly or via `fund()`)
5. The contract deposits into the SystemContract via `depositToSystem()`

Key source files:
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/src/reactive-integration/ThetaSwapReactive.sol` -- lines 43-71 (constructor with subscribe + depositToSystem), lines 100-106 (funding)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/lib/reactive-hooks/src/modules/DebtMod.sol` -- lines 6, 22-27 (SYSTEM_CONTRACT address, depositToSystem implementation)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol` -- lines 174-191 (pay() for callback gas, receive() for ETH funding)

---

## 3. Token Bridging: Getting REACT/lREACT onto Reactive Network

### Mainnet: Token Portal

- **URL**: https://portal.reactive.network
- **Supported pairs**: Ethereum wREACT <-> Native REACT, Ethereum PRQ -> Native REACT, BSC PRQ -> Native REACT, Native REACT <-> Base REACT
- **Wrapped REACT (ERC-20) on Ethereum**: `0x817162975186d4D53dBF5a7377dd45376e2D2fc5`
- **Mechanism**: The portal is a web UI; the underlying bridge uses Reactive Contracts themselves (event-driven lock/mint pattern)
- **No programmatic on-chain bridge contract** is exposed for arbitrary callers on the origin chain

### Testnet (Lasna): Faucet Contract

| Chain | Faucet Address | Exchange Rate |
|-------|---------------|---------------|
| Ethereum Sepolia | `0x9b9BB25f1A81078C544C829c5EB7822d747Cf434` | 1 ETH = 100 lREACT |
| Base Sepolia | `0x2afaFD298b23b62760711756088F75B7409f5967` | 1 ETH = 100 lREACT |

**How the faucet works (two-contract architecture):**

1. `ReactiveFaucetL1` on Sepolia: accepts ETH, emits `PaymentRequest` event (max 5 ETH per tx)
2. `ReactiveFaucet` on Reactive Network: subscribes to `PaymentRequest` events from the L1 contract, processes callbacks, distributes lREACT to the receiver address

This is itself an example of the "emit event on origin -> Reactive picks it up" pattern. The faucet contract is **not** a general-purpose bridge -- it only mints lREACT.

Source: [Reactive-Network/testnet-faucet](https://github.com/Reactive-Network/testnet-faucet)

---

## 4. Cross-Chain Message Passing: Directions and Limitations

### Direction 1: Origin -> Reactive (Inbound Data)

**Mechanism**: Event subscription. No explicit "send" required.

The origin chain does not need to know about Reactive Network at all. Any contract emitting standard EVM events can be an origin. The reactive contract subscribes via the system contract:

```solidity
service.subscribe(chainId, contractAddress, topic0, topic1, topic2, topic3);
```

To "send a message" to Reactive, you simply **emit an event on the origin chain**. If a reactive contract is subscribed to that event signature from that contract on that chain, the ReactVM will execute `react()` with the log data.

**This is the only native inbound data channel.**

### Direction 2: Reactive -> Destination (Outbound Callbacks)

**Mechanism**: Callback proxy (legacy) or Hyperlane Mailbox.

The reactive contract emits a specially-formatted log in `react()`. The Reactive Network detects this and submits a transaction to the destination chain contract. The callback proxy on the destination chain calls the target function and then calls `pay()` on the target contract to collect gas costs.

### Direction 3: External -> Reactive (Direct Transactions)

**Mechanism**: Standard RPC transactions to Reactive Network.

You CAN send transactions directly to contracts on Reactive Network using the Reactive RPC (`https://lasna-rpc.rnk.dev` for testnet). These are standard EVM transactions. The ThetaSwapReactive contract's `registerPool()`, `unregisterPool()`, and `fund()` functions are called this way.

However, this requires the caller to already have REACT/lREACT on Reactive Network for gas.

### Direction 4: Origin -> Reactive via Hyperlane (Experimental)

**Mechanism**: Hyperlane Mailbox dispatch on origin -> Hyperlane Mailbox handle on Reactive.

The Hyperlane demo in the official repos shows a `HyperlaneOrigin` contract on Base that can dispatch messages to Reactive Network via Hyperlane's `Mailbox.dispatch()`. The `HyperlaneReactive` contract on Reactive Network implements `handle()` to receive these messages.

**Current limitation**: The demo focuses on **Reactive -> Base** messaging (reactive contract sends callback via Hyperlane mailbox instead of legacy callback proxy). The reverse direction (Base -> Reactive via Hyperlane) IS technically possible because Hyperlane mailboxes are bidirectional, but:
- Hyperlane mailbox addresses on Reactive Network mainnet/Lasna are not well-documented
- The demo's `HyperlaneOrigin.handle()` receives messages FROM Reactive, not the other way around
- No production examples exist of Sepolia -> Reactive via Hyperlane

Reference: [Hyperlane demo](https://github.com/Reactive-Network/reactive-smart-contract-demos/tree/main/src/demos/hyperlane), [Hyperlane docs](https://dev.reactive.network/hyperlane)

---

## 5. Can You Do Both (Data + Tokens) in One Transaction?

### Short Answer: No, not natively.

The system has separate concerns on separate chains:
- **Data** flows via event subscriptions (origin chain events -> ReactVM)
- **Token funding** happens on Reactive Network itself (lREACT sent to contract -> depositToSystem)

There is no single origin-chain transaction that atomically sends calldata AND bridges tokens.

### Practical Patterns to Approximate This

#### Pattern A: "Emit-and-Fund" (Two-Step, Same EOA)

1. **Step 1 (Sepolia)**: Call your origin-chain contract, which emits a custom event (e.g., `FundingRequest(address receiver, uint256 amount)`). In the same tx, send ETH to the faucet contract to request lREACT.
2. **Step 2 (Automatic)**: The reactive contract on Lasna is subscribed to both:
   - Your custom `FundingRequest` event
   - The faucet's `PaymentRequest` event (or it receives lREACT from the faucet callback)
3. The reactive contract's `react()` processes your custom event. The lREACT arrives separately via the faucet mechanism.

**Problem**: The lREACT from the faucet goes to the EOA, not directly to the contract. You still need a manual `fund()` call or a secondary reactive contract that forwards.

#### Pattern B: "Self-Funding Reactive Contract" (Current ThetaSwap Pattern)

1. Pre-fund the reactive contract with a large lREACT reserve via `depositToSystem()`
2. All subsequent "inbound data" is free -- just emit events on origin chain
3. The reactive contract draws from its reserve for subscription and callback costs

**This is the simplest and most practical approach.** The contract is funded once (or periodically topped up), and all data flows in via event subscriptions at zero marginal cost to the origin-chain user.

#### Pattern C: "Hyperlane Warp Route" (Future/Advanced)

Deploy a Hyperlane Warp Route between Sepolia and Reactive Network:
1. Lock tokens on Sepolia via the Warp Route collateral contract
2. Mint wrapped tokens on Reactive Network
3. In the same Hyperlane message, include calldata that gets delivered to a handler contract on Reactive

This would achieve true one-transaction bridging of both data and tokens, but requires:
- Deploying Hyperlane infrastructure on both chains (if not already present)
- Building a custom Warp Route for REACT or a proxy token
- The Hyperlane mailbox on Reactive Network must be deployed and configured

Reference: [Hyperlane Warp Routes](https://docs.hyperlane.xyz/docs/guides/quickstart/deploy-warp-route), [Reactive x Hyperlane announcement](https://blog.reactive.network/reactive-network-x-hyperlane-unlocking-native-cross-chain-automation-with-react/)

#### Pattern D: "Custom Bridge via Reactive Contract" (DIY)

Build a bridge contract using Reactive's own primitives (similar to how the faucet works):

1. **Sepolia contract** (`BridgeEntrypoint`):
   - Accepts ETH + calldata
   - Emits `BridgeRequest(address sender, uint256 amount, bytes calldata data)`
   - Holds the ETH in escrow

2. **Reactive contract** (`BridgeReactive`):
   - Subscribes to `BridgeRequest` events from the Sepolia contract
   - In `react()`, processes the calldata (or forwards it)
   - Emits a callback to the destination (could be Sepolia itself for the adapter)

3. **Funding**: The reactive contract needs its own pre-funded reserve. The "bridged" ETH stays on Sepolia and can fund the origin-side adapter's `pay()` costs.

This is essentially what the Reactive Bridge demo does for token transfers, but generalized to include arbitrary calldata.

---

## 6. Reactive Bridge Demo: Relevant Architecture

The official Reactive Bridge demo ([blog post](https://blog.reactive.network/reactive-bridge-decentralizing-cross-chain-token-transfers/)) implements:

1. **Origin chain**: User calls `bridgeRequest()`, which burns tokens and emits `BridgeRequest` event
2. **Reactive Network**: `ReactiveBridge` contract subscribes to `BridgeRequest` events
3. **ReactVM**: `react()` processes the event and emits a Callback to the destination chain
4. **Destination chain**: Callback mints equivalent tokens

This is a **burn-and-mint** pattern coordinated entirely by event subscriptions. No direct cross-chain message passing is needed because Reactive Network watches the origin chain autonomously.

---

## 7. Key Contract Addresses Reference

### Reactive Network Infrastructure

| Component | Address | Notes |
|-----------|---------|-------|
| System Contract / Callback Proxy | `0x0000000000000000000000000000000000fffFfF` | Same on mainnet and Lasna |
| Lasna RPC | `https://lasna-rpc.rnk.dev` | Testnet |
| Mainnet RPC | `https://erpc.reactive.network` | Mainnet |

### Token Contracts

| Token | Chain | Address |
|-------|-------|---------|
| Wrapped REACT (ERC-20) | Ethereum | `0x817162975186d4D53dBF5a7377dd45376e2D2fc5` |

### Faucet Contracts (Testnet)

| Chain | Address | Rate |
|-------|---------|------|
| Ethereum Sepolia | `0x9b9BB25f1A81078C544C829c5EB7822d747Cf434` | 1 ETH = 100 lREACT |
| Base Sepolia | `0x2afaFD298b23b62760711756088F75B7409f5967` | 1 ETH = 100 lREACT |

### ThetaSwap Deployment (Sepolia + Lasna)

| Component | Address | Chain |
|-----------|---------|-------|
| ReactiveHookAdapter v3 | `0xF3B1023A4Ee10CB8F51E277899018Cd6D2836071` | Sepolia |
| ThetaSwapReactive v9 | `0x302adeea6BE9a6e22f319f9ee2ABE1Be60Cc4C14` | Lasna |
| V3 Pool (fee=3000) | `0xcB80f9b60627DF6915cc8D34F5d1EF11617b8Af8` | Sepolia |
| Callback Proxy | `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA` | Sepolia |

---

## 8. Recommendations for ThetaSwap

### Short Term: Keep Pattern B (Pre-Funded Reserve)

The current approach is correct and practical:
- Pre-fund `ThetaSwapReactive` with lREACT via `depositToSystem()`
- Data flows in for free via V3 event subscriptions
- Origin-chain users never interact with Reactive Network directly
- Top up the reserve periodically via `fund()` called from the deployer EOA

### Medium Term: Build a Funding Relay

If you want origin-chain users to help fund the reactive contract:
1. Deploy an `OriginFundingRelay` on Sepolia that accepts ETH and emits `FundingContribution(address contributor, uint256 amount)`
2. Build a `FundingReactive` contract on Lasna that subscribes to those events
3. When a contribution event arrives, the reactive contract can update internal accounting (who contributed how much)
4. The actual lREACT funding still comes from the pre-funded reserve or the faucet

### Long Term: Hyperlane Warp Route

When Hyperlane's Sepolia deployment and Reactive Network's Hyperlane mailbox are mature:
1. Deploy a Warp Route for a "subscription credit" token
2. Users lock ETH/tokens on Sepolia -> get subscription credits on Reactive
3. Combine with calldata dispatch for true one-transaction "bridge + command"

---

## 9. Key Takeaways

1. **Reactive Network's inbound channel IS event subscriptions.** There is no inbox, no bridge relay, no `dispatch()` to call on the origin chain. You emit events; Reactive watches.

2. **Token bridging is separate from data bridging.** Tokens (REACT/lREACT) must be on Reactive Network already. The faucet (testnet) or Token Portal (mainnet) are the only official paths.

3. **One-transaction bridge+data is not natively supported** but can be approximated with the Emit-and-Fund pattern or a custom bridge contract.

4. **Hyperlane enables bidirectional messaging** in theory, but the production integration currently focuses on Reactive->origin callbacks. Origin->Reactive via Hyperlane is possible but undocumented for Sepolia.

5. **The current ThetaSwap pattern (pre-funded reserve + event subscriptions) is the recommended approach** and matches how most Reactive Network applications work.

---

## Sources

- [Reactive Network Developer Docs](https://dev.reactive.network/)
- [Economy (callback payments, depositTo)](https://dev.reactive.network/economy)
- [Subscriptions](https://dev.reactive.network/subscriptions)
- [Origins & Destinations](https://dev.reactive.network/origins-and-destinations)
- [Reactive Mainnet / Lasna Testnet](https://dev.reactive.network/reactive-mainnet)
- [Hyperlane Integration](https://dev.reactive.network/hyperlane)
- [Events & Callbacks](https://dev.reactive.network/events-&-callbacks)
- [Reactive Contracts](https://dev.reactive.network/reactive-contracts)
- [Reactive Bridge Blog Post](https://blog.reactive.network/reactive-bridge-decentralizing-cross-chain-token-transfers/)
- [REACT Token Expanding to Base](https://blog.reactive.network/react-token-is-expanding-to-base/)
- [Reactive x Hyperlane Announcement](https://blog.reactive.network/reactive-network-x-hyperlane-unlocking-native-cross-chain-automation-with-react/)
- [Reactive Token Portal](https://portal.reactive.network/)
- [Testnet Faucet Repo](https://github.com/Reactive-Network/testnet-faucet)
- [Hyperlane Demo (reactive-smart-contract-demos)](https://github.com/Reactive-Network/reactive-smart-contract-demos/tree/main/src/demos/hyperlane)
- [Hyperlane Mailbox Docs](https://docs.hyperlane.xyz/docs/protocol/mailbox)
- [Hyperlane Warp Routes](https://docs.hyperlane.xyz/docs/guides/quickstart/deploy-warp-route)
