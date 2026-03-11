// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IERC6909Claims} from "@uniswap/v4-core/src/interfaces/external/IERC6909Claims.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {PremiumFactor, PremiumFactor__Zero, fromRaw, Q128_ONE} from "@theta-swap-insurance/types/PremiumFactorMod.sol";
import {
    register, deregister, isRegistered, getRegistration,
    setFeeClaimsToken, feeClaimsToken,
    TSI__NotRegistered, TSI__NotOperator
} from "@theta-swap-insurance/modules/ThetaSwapStorageMod.sol";

contract ThetaSwapStorageTest is Test {
    IERC6909Claims claims;
    PoolId poolId;
    bytes32 positionKey;
    uint128 factorRaw;
    address plp;
    address hook;

    function setUp() public {
        claims = IERC6909Claims(address(new MockERC6909Claims()));
        setFeeClaimsToken(claims);

        poolId = PoolId.wrap(keccak256("test-pool"));
        positionKey = keccak256("test-position");
        factorRaw = 1e17;
        plp = address(0xBEEF);
        hook = address(this);
    }

    // ── Register ──

    function test_registerStoresFactor() public {
        _grantOperator();
        this.externalRegister(poolId, positionKey, _packFactor(factorRaw), plp, hook);
        assertTrue(isRegistered(poolId, positionKey));
        assertEq(PremiumFactor.unwrap(getRegistration(poolId, positionKey)), factorRaw);
    }

    function test_registerRevertsNotOperator() public {
        vm.expectRevert(TSI__NotOperator.selector);
        this.externalRegister(poolId, positionKey, _packFactor(factorRaw), plp, hook);
    }

    function test_registerZeroFactorReverts() public {
        _grantOperator();
        vm.expectRevert(PremiumFactor__Zero.selector);
        this.externalRegister(poolId, positionKey, _packFactor(0), plp, hook);
    }

    // ── Deregister ──

    function test_deregisterRemoves() public {
        _grantOperator();
        this.externalRegister(poolId, positionKey, _packFactor(factorRaw), plp, hook);
        assertTrue(isRegistered(poolId, positionKey));

        deregister(poolId, positionKey);
        assertFalse(isRegistered(poolId, positionKey));
    }

    function test_deregisterRevertsNotRegistered() public {
        vm.expectRevert(TSI__NotRegistered.selector);
        this.externalDeregister(poolId, positionKey);
    }

    // ── Default state ──

    function test_notRegisteredByDefault() public view {
        assertFalse(isRegistered(poolId, positionKey));
    }

    function test_feeClaimsTokenSetGet() public view {
        assertEq(address(feeClaimsToken()), address(claims));
    }

    // ── Helpers ──

    function _grantOperator() internal {
        MockERC6909Claims(address(claims)).setIsOperator(plp, hook, true);
    }

    function _packFactor(uint128 raw) internal pure returns (bytes memory) {
        return abi.encodePacked(raw);
    }

    function externalRegister(
        PoolId _poolId, bytes32 _posKey, bytes calldata _hookData, address _plp, address _hook
    ) external {
        register(_poolId, _posKey, _hookData, _plp, _hook);
    }

    function externalDeregister(PoolId _poolId, bytes32 _posKey) external {
        deregister(_poolId, _posKey);
    }
}

contract MockERC6909Claims {
    mapping(address => mapping(address => bool)) public operatorApprovals;

    function setIsOperator(address owner, address operator, bool approved) external {
        operatorApprovals[owner][operator] = approved;
    }

    function isOperator(address owner, address spender) external view returns (bool) {
        return operatorApprovals[owner][spender];
    }
}
