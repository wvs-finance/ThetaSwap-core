// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    erc20Mint,
    erc20Burn,
    getERC20Storage,
    ERC20Storage
} from "@fci-token-vault/modules/dependencies/ERC20Lib.sol";
import {
    getERC6909Storage,
    ERC6909Storage
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

uint256 constant WRAPPER_STORAGE_POSITION_SEED = uint256(keccak256("thetaswap.erc20-wrapper"));

error InsufficientERC6909Balance(address owner, uint256 balance, uint256 needed, uint256 tokenId);

/// @dev Read the wrapped ERC-6909 token ID from diamond storage.
function getWrappedTokenId() view returns (uint256 id) {
    bytes32 slot = bytes32(WRAPPER_STORAGE_POSITION_SEED);
    assembly {
        id := sload(slot)
    }
}

/// @title ERC20WrapperFacade — thin ERC-20 wrapper over ERC-6909 token ID
/// @dev Uses inlined ERC20Lib for mint/burn (diamond storage at compose.erc20).
///      Wrapping moves balance from ERC-6909 internal accounting to standard
///      ERC-20 balanceOf visible to external AMMs and protocols.
///      Deploy one instance per (LONG, SHORT) token ID via the diamond.
///      The Compose ERC20Facet handles transfer/approve/allowance externally.
///      This is a contract (not free functions) because it's a diamond facet
///      that needs `external` visibility and `msg.sender` access.
contract ERC20WrapperFacade {
    /// @notice Convert ERC-6909 balance to ERC-20 balance.
    function wrap(uint256 amount) external {
        uint256 tokenId = getWrappedTokenId();
        ERC6909Storage storage s = getERC6909Storage();
        uint256 bal = s.balanceOf[msg.sender][tokenId];
        if (bal < amount) revert InsufficientERC6909Balance(msg.sender, bal, amount, tokenId);
        unchecked {
            s.balanceOf[msg.sender][tokenId] = bal - amount;
        }
        erc20Mint(msg.sender, amount);
    }

    /// @notice Convert ERC-20 balance back to ERC-6909 balance.
    function unwrap(uint256 amount) external {
        erc20Burn(msg.sender, amount);
        uint256 tokenId = getWrappedTokenId();
        getERC6909Storage().balanceOf[msg.sender][tokenId] += amount;
    }
}
