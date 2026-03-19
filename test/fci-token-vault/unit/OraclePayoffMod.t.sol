// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    oraclePoke,
    oracleSettle,
    oracleRedeemLong,
    oracleRedeemShort
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getOraclePayoffStorage,
    OraclePayoffStorage
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {custodianDeposit} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

contract OraclePayoffModCaller {
    function doPoke() external returns (uint160) { return oraclePoke(); }
    function doSettle() external { oracleSettle(); }
    function doRedeemLong(address r, uint256 a) external returns (uint256) { return oracleRedeemLong(r, a); }
    function doRedeemShort(address r, uint256 a) external returns (uint256) { return oracleRedeemShort(r, a); }
    function doDeposit(address depositor, uint256 amount) external { custodianDeposit(depositor, amount); }
    function initCustodianStorage(address collateral) external {
        getCustodianStorage().collateralToken = collateral;
    }
    function initOracleStorage(uint160 strike, uint256 expiry, bytes32 adapterSlot) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = strike;
        os.expiry = expiry;
        os.adapterSlot = adapterSlot;
    }
    function setHWM(uint160 hwm) external {
        getOraclePayoffStorage().sqrtPriceHWM = hwm;
    }
    function isSettled() external view returns (bool) {
        return getOraclePayoffStorage().settled;
    }
    function longPayoutPerToken() external view returns (uint256) {
        return getOraclePayoffStorage().longPayoutPerToken;
    }
    function erc6909BalanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }
    function totalDeposits() external view returns (uint128) {
        return getCustodianStorage().totalDeposits;
    }
}

contract OraclePayoffModTest is Test {
    OraclePayoffModCaller caller;
    address alice = makeAddr("alice");

    function setUp() public {
        caller = new OraclePayoffModCaller();
        caller.initCustodianStorage(address(1));
        caller.initOracleStorage(
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            block.timestamp + 30 days,      // expiry
            bytes32(0)
        );
    }

    function test_settle_reverts_before_expiry() public {
        vm.expectRevert();
        caller.doSettle();
    }

    function test_settle_after_expiry_sets_settled() public {
        caller.setHWM(uint160(SqrtPriceLibrary.Q96) * 2);
        vm.warp(block.timestamp + 30 days);
        caller.doSettle();
        assertTrue(caller.isSettled());
        assertGt(caller.longPayoutPerToken(), 0);
    }

    function test_redeemLong_burns_long_only() public {
        caller.doDeposit(alice, 100e6);
        caller.setHWM(uint160(SqrtPriceLibrary.Q96) * 2);
        vm.warp(block.timestamp + 30 days);
        caller.doSettle();

        caller.doRedeemLong(alice, 100e6);

        assertEq(caller.erc6909BalanceOf(alice, LONG), 0);
        assertEq(caller.erc6909BalanceOf(alice, SHORT), 100e6);
    }

    function test_redeemShort_burns_short_only() public {
        caller.doDeposit(alice, 100e6);
        caller.setHWM(uint160(SqrtPriceLibrary.Q96) * 2);
        vm.warp(block.timestamp + 30 days);
        caller.doSettle();

        caller.doRedeemShort(alice, 100e6);

        assertEq(caller.erc6909BalanceOf(alice, LONG), 100e6);
        assertEq(caller.erc6909BalanceOf(alice, SHORT), 0);
    }

    function test_redeemLong_plus_redeemShort_eq_deposit() public {
        caller.doDeposit(alice, 100e6);
        caller.setHWM(uint160(SqrtPriceLibrary.Q96) * 2);
        vm.warp(block.timestamp + 30 days);
        caller.doSettle();

        uint256 longPayout = caller.doRedeemLong(alice, 50e6);
        uint256 shortPayout = caller.doRedeemShort(alice, 50e6);

        // Conservation: long + short = deposit (rounding dust stays in vault)
        assertLe(longPayout + shortPayout, 50e6);
        assertGe(longPayout + shortPayout, 50e6 - 1); // at most 1 wei dust
    }
}
