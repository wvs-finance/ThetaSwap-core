# Cross-Chain Bridge and Messaging Protocols for Reactive Network Integration

**Date**: 2026-03-14
**Branch**: 005-frontend-spec-clean
**Purpose**: Evaluate on-chain cross-chain messaging protocols usable from Solidity contracts to send messages from/to the Reactive Network and arbitrary destination chains.

---

## Executive Summary

Reactive Network already ships two cross-chain transport layers:

1. **Native Callback Proxy** -- the built-in relay that ThetaSwap currently uses on Sepolia. Reactive contracts emit a `Callback` event; the Reactive relayer network picks it up and submits a transaction on the destination chain via the callback proxy. This is the simplest path but is limited to chains where Reactive Network has deployed callback proxy infrastructure.

2. **Hyperlane Mailbox integration** -- an officially supported alternative transport. Reactive contracts emit a `Callback` that dispatches through Hyperlane's `Mailbox.dispatch()` instead of the native proxy, unlocking 50+ destination chains permissionlessly.

Beyond these two, four additional general-purpose messaging protocols (LayerZero V2, Chainlink CCIP, Axelar GMP, Wormhole) could theoretically be invoked from contracts on Reactive-supported chains, but **none of them currently deploy endpoints on the Reactive Network itself**. They are useful if the destination-chain contract (on Ethereum, Arbitrum, Base, etc.) needs to relay onward to a third chain.

---

## Table of Contents

1. [Reactive Network Native Cross-Chain Mechanism](#1-reactive-network-native-cross-chain-mechanism)
2. [Reactive Network + Hyperlane Integration](#2-reactive-network--hyperlane-integration)
3. [LayerZero Endpoint V2](#3-layerzero-endpoint-v2)
4. [Chainlink CCIP](#4-chainlink-ccip)
5. [Axelar GMP](#5-axelar-gmp)
6. [Wormhole Core Messaging](#6-wormhole-core-messaging)
7. [Comparison Matrix](#7-comparison-matrix)
8. [Relevance to ThetaSwap Deployment](#8-relevance-to-thetaswap-deployment)
9. [Recommendations and Next Steps](#9-recommendations-and-next-steps)
10. [Sources](#10-sources)

---

## 1. Reactive Network Native Cross-Chain Mechanism

### 1.1 Architecture

Reactive Network is an EVM-compatible chain purpose-built for event-driven automation. Its core primitive is the **Reactive Contract (RC)** -- a standard Solidity contract deployed on the Reactive Network that:

- Subscribes to event logs on one or more origin chains (via `ISubscriptionService`).
- Receives matching logs in its `react(LogRecord)` function, executed inside an isolated **ReactVM**.
- Emits a `Callback` event to trigger a transaction on a destination chain.

The Reactive Network operates a **Relayer Network** that bridges events between EVM chains. All operations remain on-chain; the relayer merely ferries signed event data.

### 1.2 The Callback Event (Cross-Chain Primitive)

```solidity
event Callback(
    uint256 indexed chain_id,    // destination chain ID
    address indexed _contract,   // target contract on destination
    uint64  indexed gas_limit,   // gas budget for the callback tx
    bytes   payload              // abi.encodeWithSelector(...)
);
```

When the Reactive Network detects this event in a ReactVM transaction trace, it:

1. Replaces the first 160 bits of `payload` with the **RVM ID** (the ReactVM address, equal to the deployer's EOA). This is a mandatory security injection -- the first argument of every callback is always the RVM ID regardless of what the contract encodes.
2. Submits a transaction to `_contract` on `chain_id` via the **Callback Proxy** deployed on that chain.
3. The Callback Proxy calls the target contract, forwarding the payload.

### 1.3 Callback Proxy Addresses (Testnet -- Lasna)

| Destination Chain | Callback Proxy Address |
|---|---|
| Ethereum Sepolia (11155111) | `0x9b9BB25f1A81078C544C829c5EB7822d747Cf434` |
| Base Sepolia (84532) | `0x2afaFD298b23b62760711756088F75B7409f5967` |

The user's existing deployment uses the Sepolia callback proxy at `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA` (per MEMORY.md). This may be an older Kopli-era proxy or a custom wrapper.

### 1.4 Supported Chains

**Mainnet (launched 2025-02-25, Chain ID 1597):**
- Ethereum, Avalanche C-Chain, Base, BNB Chain, Polygon PoS (day-one)
- Soneium, Linea, Unichain, Abstract, Plasma (added throughout 2025)

**Testnet Lasna (Chain ID 5318007):**
- Ethereum Sepolia, Base Sepolia

With the Hyperlane integration (see section 2), the effective reach extends to 50+ chains.

### 1.5 Gas/Payment Model

- Reactive contracts pre-fund a reserve via `depositToSystem()` on the Reactive Network.
- The callback proxy on the destination chain calls `pay(uint256 amount)` on the target contract to collect gas costs for executing the callback.
- If the target cannot pay, the proxy still executes the callback but emits `CallbackFailure`.
- On the Reactive Network side, subscription and computation costs are drawn from the pre-funded reserve; any shortfall accrues as debt covered by `coverDebt()`.

### 1.6 On-Chain Interface (What ThetaSwap Already Uses)

The `IReactive` interface:

```solidity
interface IReactive {
    struct LogRecord {
        uint256 chain_id;
        address _contract;
        uint256 topic0;
        uint256 topic1;
        uint256 topic2;
        uint256 topic3;
        bytes   data;
        uint256 block_number;
        uint256 op_code;
        uint256 tx_hash;
        uint256 log_index;
    }

    function react(LogRecord calldata log) external;
}
```

The `AbstractReactive` base contract:
- Detects whether the instance is running on the Reactive Network or in a ReactVM.
- Provides `vmOnly` and `rnOnly` modifiers.
- Integrates with `AbstractPayer` for gas cost settlement.

### 1.7 How ThetaSwap Uses This Today

The existing deployment (from the 003-reactive-integration branch):

- **`ThetaSwapReactive`** (on Lasna): subscribes to V3 pool events on Sepolia, processes them in ReactVM, and emits `Callback` events targeting the `ReactiveHookAdapter` on Sepolia.
- **`ReactiveHookAdapter`** (on Sepolia, at `0xF3B1023A4Ee10CB8F51E277899018Cd6D2836071`): receives callbacks from the Sepolia callback proxy, verifies `rvmSender == rvmId`, and translates V3 event data into FCI state updates.
- **Callback Proxy** (on Sepolia, at `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA`): the Reactive Network's relay endpoint that delivers callbacks and calls `pay()`.

The flow is: **V3 Pool (Sepolia)** -> event log -> **Reactive relayer** -> **ThetaSwapReactive ReactVM (Lasna)** -> `emit Callback(...)` -> **Reactive relayer** -> **Callback Proxy (Sepolia)** -> **ReactiveHookAdapter.onV3Swap/onV3Mint/onV3Burn (Sepolia)**.

---

## 2. Reactive Network + Hyperlane Integration

### 2.1 Overview

In 2025, Reactive Network officially integrated **Hyperlane** as an alternative transport to the native callback proxy. This is the recommended path for reaching chains beyond the native proxy list.

Hyperlane is a permissionless interoperability protocol. Its core contract is the **Mailbox**, deployed on every supported chain. Any chain can deploy a Hyperlane Mailbox -- no governance approval needed.

### 2.2 How It Works with Reactive

The demo pattern (from `reactive-smart-contract-demos/src/demos/hyperlane`):

1. **HyperlaneReactive** (on Reactive Network): inherits `AbstractReactive` and `AbstractCallback`. When triggered by a subscribed event, it emits a `Callback` that routes through Hyperlane's mailbox on the Reactive Network.
2. **HyperlaneOrigin** (on the destination chain, e.g., Base): implements `handle()` to receive messages from the Hyperlane mailbox on that chain.

The key difference from the native proxy: instead of the Reactive relayer delivering the callback, **Hyperlane's decentralized validator set** relays the message via its own infrastructure.

### 2.3 Solidity Interface -- Sending (Hyperlane Mailbox)

```solidity
interface IMailbox {
    function dispatch(
        uint32 destinationDomain,    // Hyperlane domain ID (not EVM chain ID)
        bytes32 recipientAddress,    // left-padded address on destination
        bytes calldata messageBody   // arbitrary payload
    ) external payable returns (bytes32 messageId);

    function quoteDispatch(
        uint32 destinationDomain,
        bytes32 recipientAddress,
        bytes calldata messageBody
    ) external view returns (uint256 fee);
}
```

### 2.4 Solidity Interface -- Receiving

```solidity
interface IMessageRecipient {
    function handle(
        uint32 origin,           // source domain
        bytes32 sender,          // sender address on source
        bytes calldata message   // payload
    ) external payable;
}
```

### 2.5 Gas/Payment Model

- Fees are quoted on-chain via `quoteDispatch()`.
- On Reactive Network, all fees (Hyperlane relay + destination gas) are paid in **REACT tokens**.
- Each message costs approximately 3-5 REACT depending on current rates and destination chain gas prices.

### 2.6 Reactive Network Support

**Yes, natively supported.** Hyperlane mailboxes are deployed on both Reactive Mainnet (Chain ID 1597) and Lasna Testnet (Chain ID 5318007). This is the official alternative to the callback proxy and provides access to 50+ chains including Ethereum, Arbitrum, Avalanche, Base, BNB Chain, Optimism, and more.

### 2.7 Implications for ThetaSwap

This is the most natural upgrade path. Instead of relying solely on the native callback proxy (which is limited to chains with deployed proxies), ThetaSwap could:

- Use Hyperlane to relay FCI state updates to chains beyond Sepolia/Base Sepolia.
- Deploy `ReactiveHookAdapter` variants on Arbitrum, Optimism, etc., each receiving messages via the local Hyperlane mailbox.
- Keep the same ReactVM logic; only the transport changes.

---

## 3. LayerZero Endpoint V2

### 3.1 Overview

LayerZero is an omnichain messaging protocol using **Decentralized Verifier Networks (DVNs)** and **Executors** to verify and deliver cross-chain messages. V2 separates verification from execution, giving developers configurable security.

### 3.2 On-Chain Interface -- Sending (OApp Standard)

```solidity
// Inherit from OApp to get _lzSend
abstract contract OApp is OAppSender, OAppReceiver {
    // ...
}

// Sending a message:
function sendMessage(
    uint32 _dstEid,         // destination endpoint ID
    string memory _message,
    bytes calldata _options  // gas settings, executor options
) external payable {
    bytes memory payload = abi.encode(_message);
    MessagingFee memory fee = _quote(_dstEid, payload, _options, false);
    _lzSend(
        _dstEid,
        payload,
        _options,
        fee,
        payable(msg.sender)  // refund address
    );
}
```

Under the hood, `_lzSend` calls `EndpointV2.send()`.

### 3.3 On-Chain Interface -- Receiving

```solidity
function _lzReceive(
    Origin calldata _origin,
    bytes32 _guid,
    bytes calldata _message,
    address _executor,
    bytes calldata _extraData
) internal override {
    // Decode and process _message
}
```

### 3.4 Gas/Payment Model

- Fees paid in native gas token of the source chain.
- Fee quote available via `_quote()` or `EndpointV2.quote()`.
- Developers configure which DVNs verify their messages (trade-off between cost and security).

### 3.5 Reactive Network Support

**No.** LayerZero does not currently deploy endpoints on the Reactive Network (mainnet or Lasna). LayerZero endpoints exist on Ethereum, Arbitrum, Optimism, Base, Polygon, Avalanche, BNB Chain, and many others -- but not Reactive.

**Usable from destination chains only**: a contract on Ethereum/Base (like `ReactiveHookAdapter`) could use LayerZero to relay messages onward to a third chain.

---

## 4. Chainlink CCIP

### 4.1 Overview

Chainlink Cross-Chain Interoperability Protocol (CCIP) enables token transfers, arbitrary data messaging, and programmable token transfers across chains. Backed by Chainlink's decentralized oracle network. Surged to $7.77B in cross-chain transfers in 2025.

### 4.2 On-Chain Interface -- Sending

```solidity
import {IRouterClient} from "@chainlink/contracts-ccip/src/v0.8/ccip/interfaces/IRouterClient.sol";
import {Client} from "@chainlink/contracts-ccip/src/v0.8/ccip/libraries/Client.sol";

function sendMessage(
    uint64 destinationChainSelector,
    address receiver,
    bytes memory data
) external returns (bytes32 messageId) {
    Client.EVM2AnyMessage memory message = Client.EVM2AnyMessage({
        receiver: abi.encode(receiver),
        data: data,
        tokenAmounts: new Client.EVMTokenAmount[](0),
        extraArgs: Client._argsToBytes(
            Client.EVMExtraArgsV1({gasLimit: 200_000})
        ),
        feeToken: address(0)  // pay in native; or set to LINK address
    });

    uint256 fee = IRouterClient(router).getFee(
        destinationChainSelector, message
    );

    messageId = IRouterClient(router).ccipSend{value: fee}(
        destinationChainSelector, message
    );
}
```

### 4.3 On-Chain Interface -- Receiving

```solidity
import {CCIPReceiver} from "@chainlink/contracts-ccip/src/v0.8/ccip/applications/CCIPReceiver.sol";

contract MyReceiver is CCIPReceiver {
    function _ccipReceive(
        Client.Any2EVMMessage memory message
    ) internal override {
        address sender = abi.decode(message.sender, (address));
        bytes memory data = message.data;
        // process
    }
}
```

### 4.4 Gas/Payment Model

- Fees payable in LINK or native gas token.
- Fee quote via `router.getFee()`.
- CCIP 2.0 (Q4 2025 / early 2026) introduces tiered security levels.

### 4.5 Reactive Network Support

**No.** Chainlink CCIP does not support the Reactive Network. CCIP connects 60+ blockchains but Reactive is not among them.

**Usable from destination chains**: a contract on Ethereum could use CCIP to relay a message from Ethereum to Avalanche, for example, after receiving a Reactive callback.

---

## 5. Axelar GMP

### 5.1 Overview

Axelar General Message Passing (GMP) allows a contract on one chain to call any function on any connected chain, passing arbitrary data. Secured by Axelar's proof-of-stake validator set.

### 5.2 On-Chain Interface -- Sending

```solidity
import {IAxelarGateway} from "@axelar-network/axelar-gmp-sdk-solidity/contracts/interfaces/IAxelarGateway.sol";
import {IAxelarGasService} from "@axelar-network/axelar-gmp-sdk-solidity/contracts/interfaces/IAxelarGasService.sol";

function sendMessage(
    string memory destinationChain,    // e.g., "ethereum"
    string memory destinationAddress,  // target contract (string)
    bytes memory payload
) external payable {
    // Pay gas for destination execution
    gasService.payNativeGasForContractCall{value: msg.value}(
        address(this),
        destinationChain,
        destinationAddress,
        payload,
        msg.sender  // refund address
    );

    // Send the cross-chain message
    gateway.callContract(
        destinationChain,
        destinationAddress,
        payload
    );
}
```

### 5.3 On-Chain Interface -- Receiving

```solidity
import {AxelarExecutable} from "@axelar-network/axelar-gmp-sdk-solidity/contracts/executable/AxelarExecutable.sol";

contract MyReceiver is AxelarExecutable {
    function _execute(
        string calldata sourceChain,
        string calldata sourceAddress,
        bytes calldata payload
    ) internal override {
        // decode payload and process
    }
}
```

### 5.4 Gas/Payment Model

- Gas for destination execution paid upfront via `IAxelarGasService.payNativeGasForContractCall()`.
- Can also use `payGasForContractCall()` to pay in an ERC-20 token.

### 5.5 Reactive Network Support

**No.** Axelar does not currently support Reactive Network as an origin or destination chain.

---

## 6. Wormhole Core Messaging

### 6.1 Overview

Wormhole uses a network of **Guardians** (19 validators) to observe and sign messages (Verified Action Approvals -- VAAs). The core contract on each chain allows publishing and verifying messages.

### 6.2 On-Chain Interface -- Sending

```solidity
interface IWormhole {
    function publishMessage(
        uint32 nonce,              // arbitrary identifier
        bytes memory payload,      // data to send
        uint8 consistencyLevel     // 0 = instant finality (usually sufficient)
    ) external payable returns (uint64 sequence);

    function messageFee() external view returns (uint256);
}

function sendMessage(bytes memory payload) external payable {
    uint256 fee = wormhole.messageFee();
    wormhole.publishMessage{value: fee}(
        0,        // nonce
        payload,
        0         // consistency level
    );
}
```

### 6.3 On-Chain Interface -- Receiving

On the destination chain, a relayer submits the signed VAA:

```solidity
function receiveMessage(bytes memory encodedVAA) external {
    (IWormhole.VM memory vm, bool valid, string memory reason) =
        wormhole.parseAndVerifyVM(encodedVAA);
    require(valid, reason);
    require(!processedMessages[vm.hash], "already processed");
    processedMessages[vm.hash] = true;

    // decode vm.payload and process
}
```

### 6.4 Gas/Payment Model

- Source chain: `messageFee()` (typically very small, often 0 on testnets).
- Destination chain: relayer pays gas; can use Wormhole's automatic relayer or run your own.

### 6.5 Reactive Network Support

**No.** Wormhole does not deploy core contracts on the Reactive Network.

---

## 7. Comparison Matrix

| Protocol | Reactive Network Support | Destination Reach | On-Chain Interface | Gas Token | Decentralization | Latency |
|---|---|---|---|---|---|---|
| **Reactive Native Proxy** | Yes (built-in) | Limited to proxy-deployed chains (~10 mainnet, 2 testnet) | `emit Callback(chain_id, contract, gas_limit, payload)` | Pre-funded ETH reserve + REACT for subscriptions | Reactive relayer network | ~30-60s |
| **Hyperlane (via Reactive)** | Yes (official integration) | 50+ chains permissionlessly | `IMailbox.dispatch(domain, recipient, body)` | REACT (covers everything) | Hyperlane validators | ~1-5 min |
| **LayerZero V2** | No (not on Reactive) | 70+ chains | `EndpointV2.send()` via OApp `_lzSend()` | Native gas | DVNs (configurable) | ~1-3 min |
| **Chainlink CCIP** | No (not on Reactive) | 60+ chains | `IRouterClient.ccipSend()` | LINK or native | Chainlink DON | ~5-20 min |
| **Axelar GMP** | No (not on Reactive) | 50+ chains | `IAxelarGateway.callContract()` | Native gas | Axelar PoS validators | ~2-5 min |
| **Wormhole** | No (not on Reactive) | 30+ chains | `IWormhole.publishMessage()` | Native gas (small fee) | 19 Guardians | ~1-15 min |

---

## 8. Relevance to ThetaSwap Deployment

### 8.1 Current Architecture (003-reactive-integration)

ThetaSwap's current cross-chain setup uses the **Reactive Native Proxy** exclusively:

- `ThetaSwapReactive` (Lasna, `0x302adeea6BE9a6e22f319f9ee2ABE1Be60Cc4C14`) subscribes to V3 pool events on Sepolia.
- ReactVM processes events and emits `Callback` events.
- Reactive relayers deliver callbacks to `ReactiveHookAdapter` (Sepolia, `0xF3B1023A4Ee10CB8F51E277899018Cd6D2836071`) via the callback proxy (Sepolia, `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA`).

**Limitation**: this only works for Sepolia as the destination. The callback proxy is a Reactive Network infrastructure component -- it is not deployable by third parties.

### 8.2 The Callback Proxy Pattern Explained

The callback proxy is NOT a general cross-chain bridge. It is a Reactive Network infrastructure contract that:

1. Is deployed and operated by the Reactive Network team on each supported destination chain.
2. Receives authenticated callback payloads from the Reactive relayer network.
3. Injects the RVM ID as the first argument for authentication.
4. Calls `pay()` on the target contract to collect gas costs (regardless of whether the callback succeeded).

You cannot deploy your own callback proxy. You can only use the ones provided by Reactive Network on their supported chains.

### 8.3 Bridging Beyond Sepolia from Lasna Testnet

Currently, Lasna testnet supports only **Ethereum Sepolia** and **Base Sepolia** as destinations via the native proxy. To reach other testnets (Arbitrum Sepolia, Optimism Sepolia, etc.) from Lasna, you would need to:

1. Use the **Hyperlane integration** if Hyperlane has mailboxes on those testnets (it does for many).
2. Deploy a two-hop relay: Reactive -> Sepolia (via native proxy) -> target chain (via LayerZero/CCIP/Axelar from Sepolia).

### 8.4 Mainnet Path

On mainnet (Reactive Chain ID 1597), the native proxy covers Ethereum, Avalanche, Base, BNB, Polygon, Soneium, Linea, Unichain, Abstract, and Plasma. The Hyperlane integration extends this to 50+ chains with a single unified Solidity interface.

---

## 9. Recommendations and Next Steps

### 9.1 Immediate (Testnet)

**Use the Hyperlane integration for multi-chain reach.** This is the path of least resistance:

- The Reactive Network team has already built and documented the integration.
- The `reactive-smart-contract-demos/src/demos/hyperlane` repository contains working examples.
- Fees are paid entirely in REACT -- no need to hold native gas on multiple chains.
- Permissionless: no need to wait for Reactive to deploy callback proxies on new chains.

### 9.2 Architecture Pattern for Multi-Chain FCI

```
V3 Pool (Chain X)
  |  emit Swap/Mint/Burn
  v
Reactive Relayer (monitors Chain X events)
  |
  v
ThetaSwapReactive ReactVM (Reactive Network)
  |  emit Callback -> Hyperlane Mailbox.dispatch()
  v
Hyperlane Validator Set (relays message)
  |
  v
Hyperlane Mailbox (Chain X or Chain Y)
  |  calls handle()
  v
ReactiveHookAdapter (Chain X or Y)
  |  updates FCI state
  v
V4 PoolManager / Hook (Chain X or Y)
```

### 9.3 If Onward Relay Is Needed

If a contract on Ethereum needs to relay a message further (e.g., to a chain not supported by Hyperlane), the adapter on Ethereum could integrate LayerZero V2 or Chainlink CCIP as a secondary hop. This would be a destination-side concern, not a Reactive Network concern.

### 9.4 IBC / Cosmos Consideration

Reactive Network is EVM-based, not Cosmos-based. It does not use IBC (Inter-Blockchain Communication). IBC is not relevant to this architecture.

### 9.5 Future Monitoring

- Watch for Reactive Network expanding native callback proxy support to more chains (reducing the need for Hyperlane as intermediary).
- Watch for LayerZero, Chainlink CCIP, or Axelar adding Reactive Network as a supported chain -- this would provide additional transport options directly from Reactive.
- CCIP 2.0 (expected early 2026) with tiered security levels could be attractive for high-value DeFi callbacks if it adds Reactive support.

---

## 10. Sources

- [Reactive Network -- Getting Started](https://dev.reactive.network/)
- [Reactive Network -- Events and Callbacks](https://dev.reactive.network/events-&-callbacks)
- [Reactive Network -- Origins and Destinations](https://dev.reactive.network/origins-and-destinations)
- [Reactive Network -- Hyperlane Integration](https://dev.reactive.network/hyperlane)
- [Reactive Network -- Mainnet / Lasna Testnet](https://dev.reactive.network/reactive-mainnet)
- [Reactive Network -- FAQ](https://dev.reactive.network/faq)
- [Reactive Network -- Reactive Library](https://dev.reactive.network/reactive-library)
- [Reactive Network x Hyperlane Blog Post](https://blog.reactive.network/reactive-network-x-hyperlane-unlocking-native-cross-chain-automation-with-react/)
- [Reactive Network -- 2026 Utility Outlook](https://blog.reactive.network/reactive-network-utility-looking-forward-to-2026/)
- [Reactive Network -- 2025 Reflections](https://blog.reactive.network/reactive-network-utility-reflections-on-2025/)
- [Reactive Network GitHub](https://github.com/Reactive-Network)
- [Reactive Smart Contract Demos -- Hyperlane](https://github.com/Reactive-Network/reactive-smart-contract-demos/tree/main/src/demos/hyperlane)
- [Reactive Bridge Blog Post](https://blog.reactive.network/reactive-bridge-decentralizing-cross-chain-token-transfers/)
- [Hyperlane Docs -- Mailbox](https://docs.hyperlane.xyz/docs/protocol/mailbox)
- [Hyperlane Docs -- Send a Message](https://docs.hyperlane.xyz/docs/reference/messaging/send)
- [LayerZero V2 -- Protocol Overview](https://docs.layerzero.network/v2/concepts/protocol/protocol-overview)
- [LayerZero V2 -- OApp Quickstart](https://docs.layerzero.network/v2/developers/evm/oapp/overview)
- [LayerZero V2 -- Send Messages](https://docs.layerzero.network/v1/developers/evm/evm-guides/send-messages)
- [LayerZero V2 GitHub](https://github.com/LayerZero-Labs/LayerZero-v2)
- [Chainlink CCIP Documentation](https://docs.chain.link/ccip)
- [Chainlink CCIP -- Send Arbitrary Data](https://docs.chain.link/ccip/tutorials/evm/send-arbitrary-data)
- [Chainlink CCIP Starter Kit](https://github.com/smartcontractkit/ccip-starter-kit-hardhat/blob/main/contracts/BasicMessageSender.sol)
- [Axelar GMP Overview](https://docs.axelar.dev/dev/general-message-passing/overview/)
- [Axelar GMP SDK Solidity](https://github.com/axelarnetwork/axelar-gmp-sdk-solidity)
- [Wormhole -- Core Contracts Guide](https://wormhole.com/docs/products/messaging/guides/core-contracts/)
- [Wormhole -- Cross-Chain Contracts Tutorial](https://wormhole.com/docs/products/messaging/tutorials/cross-chain-contracts/)
- [Linea Docs -- Reactive Network](https://docs.linea.build/get-started/tooling/cross-chain/reactive-network)
