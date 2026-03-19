# Euler Vault Kit -- Beacon Proxy and MetaProxy Deployer Pattern

**Date**: 2026-03-14
**Source repos**: [`euler-xyz/euler-vault-kit`](https://github.com/euler-xyz/euler-vault-kit), [`euler-xyz/euler-earn`](https://github.com/euler-xyz/euler-earn)
**Audits**: [OpenZeppelin EVK Audit](https://www.openzeppelin.com/news/euler-vault-kit-evk-audit), [ChainSecurity EVK Audit (June 2024)](https://cdn.prod.website-files.com/65d35b01a4034b72499019e8/66c6f4820891eb675ce04a26_ChainSecurity_Euler_Euler_Vault_Kit_audit%201.pdf)

---

## Executive Summary

Euler's Vault Kit (EVK) uses a dual-mode proxy factory pattern for deploying lending vaults. The `GenericFactory` contract inherits from `MetaProxyDeployer` and acts as both a deployment factory and an ERC-1967-compatible beacon. Each vault proxy -- whether upgradeable (beacon proxy) or immutable (meta proxy) -- carries **trailing calldata metadata** appended to every `delegatecall`. This metadata encodes vault-specific immutable parameters (underlying asset address, oracle address, unit-of-account address) directly into the proxy's forwarding path, avoiding storage reads entirely. The EVault implementation then reads these parameters from the tail of `msg.data` using assembly in the `ProxyUtils` library.

This pattern is notable because it is NOT the typical "constructor args + initializer" approach used by most proxy factories. Instead, Euler embeds per-instance configuration as bytes that are physically part of every call to the implementation, making them gas-free to read (calldataload vs. sload).

---

## 1. Architecture Overview

```
                        GenericFactory
                    (inherits MetaProxyDeployer)
                   /            |             \
                  /             |              \
       BeaconProxy(A)    BeaconProxy(B)    MetaProxy(C)
       [upgradeable]     [upgradeable]     [immutable]
            |                 |                 |
            v                 v                 v
       staticcall         staticcall        hardcoded
       factory.impl()    factory.impl()     impl addr
            |                 |                 |
            +--------+--------+---------+-------+
                     |
                  EVault (implementation)
                     |
            +--------+--------+--------+
            |        |        |        |
        Initialize Token   Vault  Borrowing ...
        Module    Module  Module  Module
            (delegatecall to standalone module deployments)
```

### Key design decisions

1. **Factory = Beacon**: The `GenericFactory` stores `implementation` and exposes `implementation()` as a public getter. `BeaconProxy` calls this via `staticcall` on every invocation. A single `setImplementation()` call upgrades ALL upgradeable vaults simultaneously.

2. **Trailing metadata, not storage**: Vault-specific parameters (asset, oracle, unitOfAccount) are not stored in the proxy's storage. They are appended to every delegated calldata. The implementation reads them from the end of `msg.data`.

3. **Dual proxy modes**: Upgradeable vaults use `BeaconProxy` (runtime resolution). Immutable vaults use `MetaProxyDeployer` (EIP-3448-inspired, implementation address baked into bytecode).

4. **Static module dispatch**: The EVault implementation itself dispatches to sub-modules via `delegatecall`, but these modules are NOT proxied -- they are standalone contracts whose addresses are stored as `immutable` variables in the EVault implementation.

---

## 2. Key Contracts and Their Roles

### 2.1 GenericFactory

**File**: `src/GenericFactory/GenericFactory.sol`
**Role**: Permissionless vault factory and beacon for upgradeable proxies.

Core state:
- `implementation` -- current EVault implementation address
- `upgradeAdmin` -- address authorized to change `implementation`
- `proxyLookup` -- mapping from proxy address to `ProxyConfig`
- `proxyList` -- ordered array of all deployed proxy addresses

The critical function is `createProxy()`:

```solidity
function createProxy(
    address desiredImplementation,
    bool upgradeable,
    bytes memory trailingData
) external nonReentrant returns (address) {
    address _implementation = implementation;
    if (desiredImplementation == address(0)) desiredImplementation = _implementation;
    if (desiredImplementation == address(0) || desiredImplementation != _implementation)
        revert E_Implementation();

    // Prefix trailing data with 4 zero bytes to avoid selector clashing
    // when the proxy is called with empty calldata
    bytes memory prefixTrailingData = abi.encodePacked(bytes4(0), trailingData);
    address proxy;

    if (upgradeable) {
        proxy = address(new BeaconProxy(prefixTrailingData));
    } else {
        proxy = deployMetaProxy(desiredImplementation, prefixTrailingData);
    }

    proxyLookup[proxy] = ProxyConfig({
        upgradeable: upgradeable,
        implementation: desiredImplementation,
        trailingData: trailingData
    });
    proxyList.push(proxy);

    IComponent(proxy).initialize(msg.sender);

    emit ProxyCreated(proxy, upgradeable, desiredImplementation, trailingData);
    return proxy;
}
```

**Important details**:
- `desiredImplementation` is a front-running guard. If the admin upgrades the implementation between a user's tx submission and execution, the tx reverts instead of creating a vault with unexpected code.
- The trailing data is prefixed with `bytes4(0)` (4 zero bytes) to prevent selector collision when the proxy is called with empty calldata. This prefix is transparent to the implementation since Solidity's ABI decoder ignores extra trailing bytes.
- After deployment, the factory immediately calls `initialize(msg.sender)` on the new proxy, passing the `msg.sender` of the `createProxy` call as the vault creator/governor.

### 2.2 BeaconProxy

**File**: `src/GenericFactory/BeaconProxy.sol`
**Role**: Upgradeable proxy that resolves implementation at runtime via its beacon (the factory).

```solidity
contract BeaconProxy {
    bytes32 internal constant BEACON_SLOT =
        0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50;
    bytes32 internal constant IMPLEMENTATION_SELECTOR =
        0x5c60da1b00000000000000000000000000000000000000000000000000000000;
    uint256 internal constant MAX_TRAILING_DATA_LENGTH = 128;

    address internal immutable beacon;
    uint256 internal immutable metadataLength;
    bytes32 internal immutable metadata0;
    bytes32 internal immutable metadata1;
    bytes32 internal immutable metadata2;
    bytes32 internal immutable metadata3;

    constructor(bytes memory trailingData) {
        require(trailingData.length <= MAX_TRAILING_DATA_LENGTH, "trailing data too long");
        beacon = msg.sender;  // factory is the beacon

        // Store beacon in ERC-1967 slot for block explorer compatibility
        assembly { sstore(BEACON_SLOT, caller()) }

        metadataLength = trailingData.length;

        // Pad and decode into 4 x bytes32 immutable slots
        assembly { mstore(trailingData, MAX_TRAILING_DATA_LENGTH) }
        (metadata0, metadata1, metadata2, metadata3) =
            abi.decode(trailingData, (bytes32, bytes32, bytes32, bytes32));
    }

    fallback() external payable {
        // ... (see below)
    }
}
```

The `fallback()` function performs two operations in sequence:

1. **Resolve implementation**: `staticcall` to `beacon.implementation()` to get the current implementation address.
2. **Delegatecall with trailing metadata**: Copy original calldata, then append the 4 metadata slots (up to 128 bytes), then `delegatecall` to the implementation.

```solidity
fallback() external payable {
    address beacon_ = beacon;
    uint256 metadataLength_ = metadataLength;
    bytes32 metadata0_ = metadata0;
    // ... metadata1_, metadata2_, metadata3_

    assembly {
        // 1. Fetch implementation from beacon
        mstore(0, IMPLEMENTATION_SELECTOR)
        let result := staticcall(gas(), beacon_, 0, 4, 0, 32)
        let implementation := mload(0)

        // 2. Delegatecall with trailing metadata
        calldatacopy(0, 0, calldatasize())
        mstore(calldatasize(), metadata0_)
        mstore(add(32, calldatasize()), metadata1_)
        mstore(add(64, calldatasize()), metadata2_)
        mstore(add(96, calldatasize()), metadata3_)
        result := delegatecall(
            gas(), implementation,
            0, add(metadataLength_, calldatasize()),
            0, 0
        )
        returndatacopy(0, 0, returndatasize())

        switch result
        case 0 { revert(0, returndatasize()) }
        default { return(0, returndatasize()) }
    }
}
```

**Key design choices**:
- Metadata is stored in 4 `immutable` `bytes32` slots (128 bytes max), NOT in storage. This makes the proxy extremely gas-efficient since immutables are embedded in the runtime bytecode.
- The ERC-1967 beacon slot is written in the constructor for block explorer compatibility, but it is never read by the proxy itself -- the proxy reads the `immutable beacon` variable instead.
- The `staticcall` to the beacon's `implementation()` is trusted to not revert and to return a valid address. This is safe because the factory guarantees `implementation != address(0)`.

### 2.3 MetaProxyDeployer

**File**: `src/GenericFactory/MetaProxyDeployer.sol`
**Role**: Deploys EIP-3448-inspired minimal proxies with metadata appended to bytecode.

```solidity
contract MetaProxyDeployer {
    error E_DeploymentFailed();

    bytes constant BYTECODE_HEAD =
        hex"600b380380600b3d393df3363d3d373d3d3d3d60368038038091363936013d73";
    bytes constant BYTECODE_TAIL =
        hex"5af43d3d93803e603457fd5bf3";

    function deployMetaProxy(
        address targetContract,
        bytes memory metadata
    ) internal returns (address addr) {
        bytes memory code = abi.encodePacked(
            BYTECODE_HEAD,
            targetContract,
            BYTECODE_TAIL,
            metadata
        );

        assembly ("memory-safe") {
            addr := create(0, add(code, 32), mload(code))
        }

        if (addr == address(0)) revert E_DeploymentFailed();
    }
}
```

The deployed bytecode layout for an immutable vault proxy:

```
[BYTECODE_HEAD (31 bytes)]
[targetContract address (20 bytes)]
[BYTECODE_TAIL (13 bytes)]
[metadata (variable length)]
```

**Difference from standard EIP-3448**: Euler's variant does NOT append a length suffix. Standard EIP-3448 requires the last 32 bytes to encode the metadata length. Euler skips this, saving gas, but this means the metadata must be fixed-length or the reader must know its length a priori. In Euler's case, the implementation knows the metadata is exactly `PROXY_METADATA_LENGTH` (64 bytes) and reads from the tail of calldata.

The runtime bytecode delegatecalls to `targetContract` and appends the trailing metadata bytes to the calldata automatically. This is the same semantic as the BeaconProxy -- the implementation receives calldata with metadata appended at the end.

### 2.4 ProxyUtils

**File**: `src/EVault/shared/lib/ProxyUtils.sol`
**Role**: Library for extracting proxy metadata from trailing calldata.

```solidity
library ProxyUtils {
    function metadata()
        internal pure
        returns (IERC20 asset, IPriceOracle oracle, address unitOfAccount)
    {
        assembly {
            asset        := shr(96, calldataload(sub(calldatasize(), 60)))
            oracle       := shr(96, calldataload(sub(calldatasize(), 40)))
            unitOfAccount := shr(96, calldataload(sub(calldatasize(), 20)))
        }
    }

    function useViewCaller() internal pure returns (address viewCaller) {
        assembly {
            viewCaller := shr(96, calldataload(
                sub(calldatasize(), add(PROXY_METADATA_LENGTH, 20))
            ))
        }
    }
}
```

The metadata layout in trailing calldata (64 bytes total):

```
Offset from end of calldata:
  -64..-61  : bytes4(0)          -- 4-byte zero prefix (selector clash guard)
  -60..-41  : address asset      -- 20 bytes, underlying ERC-20 token
  -40..-21  : address oracle     -- 20 bytes, price oracle
  -20..-1   : address unitOfAccount -- 20 bytes, unit of account
```

Total: 4 + 20 + 20 + 20 = 64 bytes = `PROXY_METADATA_LENGTH`

The `shr(96, ...)` right-shifts by 96 bits (12 bytes) to extract 20-byte addresses from 32-byte calldataload results. Since `calldataload` loads 32 bytes starting at the given offset, and addresses are 20 bytes, the shift discards the 12 trailing bytes of each load.

### 2.5 Constants

**File**: `src/EVault/shared/Constants.sol`

```solidity
// proxy trailing calldata length in bytes.
// Three addresses, 20 bytes each: vault underlying asset, oracle
// and unit of account + 4 empty bytes.
uint256 constant PROXY_METADATA_LENGTH = 64;
```

### 2.6 Dispatch

**File**: `src/EVault/Dispatch.sol`
**Role**: Selector-based router that delegates to sub-module contracts.

The Dispatch contract uses `PROXY_METADATA_LENGTH` in several places to strip trailing metadata when forwarding calls:

- `delegateToModuleView()` strips the proxy metadata before building the `viewDelegate()` call, then the proxy re-appends it on the `staticcall` back into the vault.
- `callThroughEVCInternal()` strips the metadata when building the `EVC.call()` payload.

This is critical: the metadata must be stripped when making external calls that should not include it, and re-appended when the call re-enters through the proxy.

### 2.7 Initialize Module

**File**: `src/EVault/modules/Initialize.sol`
**Role**: One-time vault initialization, called by the factory after proxy deployment.

```solidity
function initialize(address proxyCreator) public virtual reentrantOK {
    if (initialized) revert E_Initialized();
    initialized = true;

    // Validate: calldata must be exactly selector + creator + metadata
    if (msg.data.length != 4 + 32 + PROXY_METADATA_LENGTH)
        revert E_ProxyMetadata();

    (IERC20 asset,,) = ProxyUtils.metadata();
    AddressUtils.checkContract(address(asset));

    // Create sidecar DToken for debt tracking
    address dToken = address(new DToken());

    // Initialize storage
    vaultStorage.lastInterestAccumulatorUpdate = uint48(block.timestamp);
    vaultStorage.interestAccumulator = INITIAL_INTEREST_ACCUMULATOR;
    vaultStorage.interestFee = DEFAULT_INTEREST_FEE.toConfigAmount();
    vaultStorage.creator = vaultStorage.governorAdmin = proxyCreator;
    vaultStorage.hookedOps = Flags.wrap(OP_MAX_VALUE - 1);

    // Generate name/symbol from underlying token
    string memory underlyingSymbol = getTokenSymbol(address(asset));
    uint256 seqId = sequenceRegistry.reserveSeqId(underlyingSymbol);
    vaultStorage.symbol = string(
        abi.encodePacked("e", underlyingSymbol, "-", uintToString(seqId))
    );
    vaultStorage.name = string(
        abi.encodePacked("EVK Vault ", vaultStorage.symbol)
    );

    emit EVaultCreated(proxyCreator, address(asset), dToken);
}
```

The `msg.data.length` check is a validation that the proxy correctly appends the metadata. It ensures: 4 bytes (selector) + 32 bytes (ABI-encoded `proxyCreator` address) + 64 bytes (metadata) = 100 bytes total.

The constructor of `InitializeModule` sets `initialized = true` on the implementation contract itself, preventing direct initialization of the singleton.

---

## 3. Deployment Flow (Step by Step)

### Step 1: Deploy the EVault implementation

The EVault implementation is deployed once. Its constructor takes `Integrations` (EVC, ProtocolConfig, SequenceRegistry, BalanceTracker, Permit2 addresses) and `DeployedModules` (8 module addresses). All of these are stored as `immutable` variables.

### Step 2: Deploy GenericFactory

```solidity
GenericFactory factory = new GenericFactory(adminAddress);
factory.setImplementation(address(evaultImpl));
```

### Step 3: Create a vault

```solidity
// trailingData = abi.encodePacked(asset, oracle, unitOfAccount)
bytes memory trailingData = abi.encodePacked(
    address(usdc),     // 20 bytes
    address(chainlink),// 20 bytes
    address(usd)       // 20 bytes
);

address vault = factory.createProxy(
    address(0),    // use current implementation
    true,          // upgradeable
    trailingData   // 60 bytes -> factory prepends 4 zero bytes -> 64 bytes
);
```

Internal flow:
1. Factory prepends `bytes4(0)` to trailingData -> 64 bytes total.
2. Factory deploys `new BeaconProxy(prefixedTrailingData)`.
3. BeaconProxy constructor stores factory as `beacon` (immutable + ERC-1967 slot).
4. BeaconProxy constructor decodes trailing data into 4 immutable `bytes32` slots.
5. Factory calls `IComponent(proxy).initialize(msg.sender)`.
6. BeaconProxy fallback: fetches `factory.implementation()` via staticcall, then delegatecalls EVault with original calldata + trailing metadata.
7. EVault dispatches to InitializeModule via the `use(MODULE_INITIALIZE)` modifier.
8. InitializeModule validates metadata, creates DToken, initializes storage, sets governor = `msg.sender`.

---

## 4. Data Flow During a Normal Call

When a user calls `vault.deposit(amount, receiver)`:

```
User -> BeaconProxy.fallback()
  |
  +-- staticcall factory.implementation() -> EVault address
  |
  +-- delegatecall EVault.deposit(amount, receiver)
        with calldata = [deposit selector][amount][receiver][metadata0..3]
        |
        +-- EVault.deposit() has modifier callThroughEVC
        |     -> strips metadata, calls EVC.call(vault, sender, value, originalCalldata)
        |     -> EVC calls back vault.deposit() with same calldata
        |     -> this time msg.sender == EVC, so modifier passes through
        |
        +-- EVault.deposit() has modifier use(MODULE_VAULT)
        |     -> delegatecall to VaultModule
        |     -> VaultModule reads asset address from trailing metadata
        |          via ProxyUtils.metadata()
        |     -> performs deposit logic using asset address
        |
        +-- returns result back through the proxy
```

---

## 5. Comparison: BeaconProxy vs MetaProxy

| Property | BeaconProxy | MetaProxy |
|----------|-------------|-----------|
| Upgradeable | Yes (via factory.setImplementation) | No (impl baked in bytecode) |
| Implementation resolution | Runtime staticcall to beacon | Hardcoded in bytecode |
| Metadata storage | 4 immutable bytes32 slots | Appended to deployed bytecode |
| Metadata forwarding | Appended to calldata in fallback | Appended to calldata by runtime bytecode |
| Gas per call | Higher (staticcall overhead) | Lower (no staticcall) |
| Deployment gas | Higher (more bytecode) | Lower (minimal bytecode) |
| ERC-1967 compatible | Yes (beacon slot written) | No |

Both proxy types produce identical calldata for the EVault implementation: `[original calldata][64 bytes metadata]`. The implementation is completely agnostic to which proxy type is used.

---

## 6. EulerEarn Factory (Contrast)

The `EulerEarnFactory` in `euler-xyz/euler-earn` does NOT use the MetaProxy/BeaconProxy pattern. It uses standard Solidity `new` with `CREATE2` (salt-based deterministic deployment):

```solidity
function createEulerEarn(
    address initialOwner,
    uint256 initialTimelock,
    address asset,
    string memory name,
    string memory symbol,
    bytes32 salt
) external returns (IEulerEarn eulerEarn) {
    eulerEarn = IEulerEarn(
        address(
            new EulerEarn{salt: salt}(
                initialOwner, address(evc), permit2Address,
                initialTimelock, asset, name, symbol
            )
        )
    );
    // ...
}
```

This is a full deployment (no proxy), so each EulerEarn vault gets its own bytecode. This approach was chosen because EulerEarn vaults are not lending vaults with the same modular architecture -- they are simpler yield aggregators (forked from Metamorpho) that don't benefit from the proxy gas savings.

---

## 7. Key Takeaways for ThetaSwap

### Pattern applicability

The trailing-metadata proxy pattern is useful when:
- You have a single implementation shared by many instances.
- Each instance has a small, fixed set of immutable parameters (addresses, configuration).
- You want to avoid storage reads for frequently-accessed parameters.
- You need optional upgradeability via beacon pattern.

### Gas implications

Reading from trailing calldata (`calldataload`) costs 3 gas. Reading from storage (`sload`) costs 2100 gas (cold) or 100 gas (warm). For parameters read on every call (like the underlying asset address), the trailing metadata approach saves significant gas across the vault's lifetime.

### Limitations

- Maximum 128 bytes of trailing metadata (4 slots of 32 bytes each in BeaconProxy).
- The implementation must be aware of and correctly handle the trailing bytes.
- Solidity's ABI decoder tolerates extra trailing data, but custom integrations calling the vault must NOT include unexpected trailing bytes.
- The `PROXY_METADATA_LENGTH` constant must be consistent across all contracts.

### The 4-byte zero prefix

The factory prepends `bytes4(0)` to avoid a subtle issue: if the proxy is called with empty calldata (e.g., a plain ETH transfer), the trailing metadata could be misinterpreted as a function selector. The 4 zero bytes ensure the "selector" portion of the metadata is always `0x00000000`, which is not a valid function selector.

---

## 8. Source File Index

| File | Role |
|------|------|
| [`src/GenericFactory/GenericFactory.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/GenericFactory/GenericFactory.sol) | Factory + Beacon |
| [`src/GenericFactory/BeaconProxy.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/GenericFactory/BeaconProxy.sol) | Upgradeable proxy with immutable metadata |
| [`src/GenericFactory/MetaProxyDeployer.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/GenericFactory/MetaProxyDeployer.sol) | EIP-3448-based minimal proxy deployer |
| [`src/EVault/shared/lib/ProxyUtils.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/EVault/shared/lib/ProxyUtils.sol) | Metadata extraction from trailing calldata |
| [`src/EVault/shared/Constants.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/EVault/shared/Constants.sol) | PROXY_METADATA_LENGTH = 64 |
| [`src/EVault/Dispatch.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/EVault/Dispatch.sol) | Module dispatch router |
| [`src/EVault/EVault.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/EVault/EVault.sol) | Main vault contract |
| [`src/EVault/modules/Initialize.sol`](https://github.com/euler-xyz/euler-vault-kit/blob/master/src/EVault/modules/Initialize.sol) | One-time vault initialization |

---

## References

- [Euler Vault Kit Whitepaper](https://github.com/euler-xyz/euler-vault-kit/blob/master/docs/whitepaper.md)
- [Euler Vault Kit Specs](https://github.com/euler-xyz/euler-vault-kit/blob/master/docs/specs.md)
- [EIP-3448: MetaProxy Standard](https://eips.ethereum.org/EIPS/eip-3448)
- [Euler Docs -- EVK Overview](https://docs.euler.finance/developers/evk/)
- [Euler Docs -- Creating and Managing Vaults](https://docs.euler.finance/developers/evk/creating-managing-vaults/)
- [RareSkills -- ERC-3448 MetaProxy Clone](https://rareskills.io/post/erc-3448-metaproxy-clone)
- [Euler Vault Kit White Paper (official docs)](https://docs.euler.finance/euler-vault-kit-white-paper/)
