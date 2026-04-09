// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {IPoolManager} from "../interfaces/IUniV4.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {Currency} from "v4-core/src/types/Currency.sol";

/// @author philogy <https://github.com/philogy>
contract UnlockSwapFeeCollector is IUnlockCallback {
    error NotUniswap();
    error NotOwner();

    address internal immutable _owner;
    IPoolManager internal immutable UNI_V4;

    constructor(IPoolManager uniV4) {
        _owner = msg.sender;
        UNI_V4 = uniV4;
    }

    function withdraw_to(address to, bytes calldata packed_assets) external {
        if (msg.sender != _owner) revert NotOwner();
        UNI_V4.unlock(bytes.concat(bytes20(to), packed_assets));
    }

    function unlockCallback(bytes calldata data) external override returns (bytes memory) {
        if (msg.sender != address(UNI_V4)) revert NotUniswap();

        address to = address(bytes20(data[:20]));
        data = data[20:];
        uint256 iters = data.length / 20;

        for (uint256 i = 0; i < iters; i++) {
            address asset;
            assembly {
                asset := shr(96, calldataload(add(data.offset, mul(i, 20))))
            }
            uint256 bal = UNI_V4.balanceOf(address(this), uint160(asset));
            UNI_V4.burn(address(this), uint160(asset), bal);
            UNI_V4.take(Currency.wrap(asset), to, bal);
        }

        return "";
    }
}
