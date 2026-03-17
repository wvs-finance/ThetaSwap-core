// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {CollateralCustodianFacet} from "@fci-token-vault/facets/CollateralCustodianFacet.sol";
import {OraclePayoffFacet} from "@fci-token-vault/facets/OraclePayoffFacet.sol";
import {ERC20WrapperFacade, WRAPPER_STORAGE_POSITION_SEED} from "@fci-token-vault/tokens/ERC20WrapperFacade.sol";
import {getCustodianStorage, CustodianStorage} from "@fci-token-vault/storage/CustodianStorage.sol";
import {getOraclePayoffStorage, OraclePayoffStorage} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {protocolAdapterStorage, ProtocolAdapterStorage} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {erc6909Mint, getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {getERC20Storage} from "@fci-token-vault/modules/dependencies/ERC20Lib.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Test deployer that inherits all three vault facets so they share
/// one address and one diamond storage context. NOT a diamond proxy.
/// Used by all three test layers.
contract FacetDeployer is CollateralCustodianFacet, OraclePayoffFacet, ERC20WrapperFacade {

    /// @dev Initialize all diamond storage slots for testing.
    /// @param collateralToken USDC address (or MockERC20)
    /// @param depositCap 0 = unlimited
    /// @param sqrtPriceStrike Strike price in sqrtPriceX96
    /// @param expiry Vault expiry timestamp
    /// @param adapterSlot Diamond storage slot for ProtocolAdapterStorage
    /// @param fciEntryPoint DeltaPlusStub (L1) or real FCI hook (L2/L3)
    /// @param poolKey PoolKey for adapter (dummy for L1, real for L2/L3)
    /// @param reactive False for L1/V4 native, true for V3 reactive
    function init(
        address collateralToken,
        uint128 depositCap,
        uint160 sqrtPriceStrike,
        uint256 expiry,
        bytes32 adapterSlot,
        address fciEntryPoint,
        PoolKey calldata poolKey,
        bool reactive
    ) external {
        // Seed CustodianStorage
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;
        cs.depositCap = depositCap;

        // Seed OraclePayoffStorage
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.expiry = expiry;
        os.adapterSlot = adapterSlot;

        // Seed ProtocolAdapterStorage at the adapter slot
        ProtocolAdapterStorage storage adapter = protocolAdapterStorage(adapterSlot);
        adapter.fciEntryPoint = IHooks(fciEntryPoint);
        adapter.poolKey = poolKey;
        adapter.reactive = reactive;
    }

    /// @dev Set the wrapped token ID for ERC20WrapperFacade testing.
    function initWrappedTokenId(uint256 tokenId) external {
        bytes32 slot = bytes32(WRAPPER_STORAGE_POSITION_SEED);
        assembly {
            sstore(slot, tokenId)
        }
    }

    /// @dev Mint ERC-6909 tokens directly (for test setup, bypasses custodian).
    function mintERC6909(address to, uint256 id, uint256 amount) external {
        erc6909Mint(to, id, amount);
    }

    /// @dev Read ERC-6909 balance (convenience for assertions).
    function erc6909BalanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }

    /// @dev Read ERC-20 balance (convenience for assertions).
    function erc20BalanceOf(address owner) external view returns (uint256) {
        return getERC20Storage().balanceOf[owner];
    }

    /// @dev Read vault storage (convenience for assertions).
    function getVaultStorage() external view returns (
        uint160 sqrtPriceStrike_,
        uint160 sqrtPriceHWM,
        uint256 expiry_,
        bool settled,
        uint256 longPayoutPerToken
    ) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        return (os.sqrtPriceStrike, os.sqrtPriceHWM, os.expiry, os.settled, os.longPayoutPerToken);
    }

    /// @dev Force-set HWM for testing edge cases.
    function setHWM(uint160 hwm) external {
        getOraclePayoffStorage().sqrtPriceHWM = hwm;
    }

    /// @dev Receive ETH (needed if tests send ETH).
    receive() external payable {}
}
