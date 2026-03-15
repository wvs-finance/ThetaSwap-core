// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {NativeUniswapV4Facet} from "@fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {FCI_HOOK_FLAGS} from "@foundry-script/deploy/DeployFci.s.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {INDEX_ONE} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";

struct FCIContext {
    address hook;
    PoolKey key;
    PoolId poolId;
    bool isV2;
}

/// @title FCI V1 vs V2 Differential Test Base
/// @notice Deploys both V1 and V2+facet inline. Provides context-aware helpers
/// for running the same scenarios against both and comparing state.
abstract contract FCIDifferentialBase is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    FeeConcentrationIndex v1;
    FeeConcentrationIndexV2 v2;

    FCIContext ctxV1;
    FCIContext ctxV2;

    function setUp() public virtual {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("diffLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        // ── Deploy V1 ──
        bytes memory v1Args = abi.encode(address(manager));
        (address v1Addr, bytes32 v1Salt) = HookMiner.find(
            address(this), FCI_HOOK_FLAGS,
            type(FeeConcentrationIndex).creationCode, v1Args
        );
        v1 = new FeeConcentrationIndex{salt: v1Salt}(address(manager));
        require(address(v1) == v1Addr, "V1 hook address mismatch");

        // ── Deploy V2 ──
        (address v2Addr, bytes32 v2Salt) = HookMiner.find(
            address(this), FCI_HOOK_FLAGS,
            type(FeeConcentrationIndexV2).creationCode, ""
        );
        v2 = new FeeConcentrationIndexV2{salt: v2Salt}();
        require(address(v2) == v2Addr, "V2 hook address mismatch");

        // ── Deploy + wire NativeUniswapV4Facet ──
        NativeUniswapV4Facet facet = new NativeUniswapV4Facet();
        v2.initialize(address(this));
        v2.registerProtocolFacet(NATIVE_V4, IFCIProtocolFacet(address(facet)));
        // Write admin storage in V2's context (facet reads via delegatecall)
        v2.setFacetFci(NATIVE_V4, IFeeConcentrationIndex(address(v2)));
        v2.setFacetProtocolStateView(NATIVE_V4, IProtocolStateView(address(manager)));

        // ── Initialize two pools — identical config, different hooks ──
        PoolKey memory keyV1;
        PoolId poolIdV1;
        (keyV1, poolIdV1) = initPool(
            currency0, currency1, IHooks(address(v1)), 3000, SQRT_PRICE_1_1
        );
        ctxV1 = FCIContext({hook: address(v1), key: keyV1, poolId: poolIdV1, isV2: false});

        PoolKey memory keyV2;
        PoolId poolIdV2;
        (keyV2, poolIdV2) = initPool(
            currency0, currency1, IHooks(address(v2)), 3000, SQRT_PRICE_1_1
        );
        ctxV2 = FCIContext({hook: address(v2), key: keyV2, poolId: poolIdV2, isV2: true});
    }

    // ── Scenario helpers (operate on a context) ──

    function _mint(FCIContext memory ctx, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal returns (uint256 tokenId)
    {
        return _mintPosition(ctx.key, tickLower, tickUpper, liquidity);
    }

    function _mintAs(FCIContext memory ctx, address lp, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal returns (uint256 tokenId)
    {
        return _mintPositionAs(lp, ctx.key, tickLower, tickUpper, liquidity);
    }

    function _burn(FCIContext memory ctx, uint256 tokenId, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
    {
        _burnPosition(ctx.key, tokenId, tickLower, tickUpper, liquidity);
    }

    function _burnAs(FCIContext memory ctx, address lp, uint256 tokenId, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
    {
        _burnPositionAs(lp, ctx.key, tokenId, tickLower, tickUpper, liquidity);
    }

    function _doSwap(FCIContext memory ctx, bool zeroForOne, int256 amountSpecified) internal {
        _swap(ctx.key, zeroForOne, amountSpecified);
    }

    // ── View helpers (normalize V1 vs V2 signatures) ──

    function _getDeltaPlus(FCIContext memory ctx) internal view returns (uint128) {
        if (ctx.isV2) return v2.getDeltaPlus(ctx.key, NATIVE_V4);
        return v1.getDeltaPlus(ctx.key, false);
    }

    function _getIndex(FCIContext memory ctx) internal view returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) {
        if (ctx.isV2) return v2.getIndex(ctx.key, NATIVE_V4);
        return v1.getIndex(ctx.key, false);
    }

    function _getAtNull(FCIContext memory ctx) internal view returns (uint128) {
        if (ctx.isV2) return v2.getAtNull(ctx.key, NATIVE_V4);
        return v1.getAtNull(ctx.key, false);
    }

    function _getThetaSum(FCIContext memory ctx) internal view returns (uint256) {
        if (ctx.isV2) return v2.getThetaSum(ctx.key, NATIVE_V4);
        return v1.getThetaSum(ctx.key, false);
    }

    // ── Comparison ──

    function _assertStateEqual() internal view {
        (uint128 indexAV1, uint256 thetaSumV1, uint256 removedV1) = _getIndex(ctxV1);
        (uint128 indexAV2, uint256 thetaSumV2, uint256 removedV2) = _getIndex(ctxV2);
        assertEq(indexAV1, indexAV2, "indexA mismatch");
        assertEq(thetaSumV1, thetaSumV2, "thetaSum mismatch");
        assertEq(removedV1, removedV2, "removedPosCount mismatch");

        assertEq(_getDeltaPlus(ctxV1), _getDeltaPlus(ctxV2), "deltaPlus mismatch");
        assertEq(_getAtNull(ctxV1), _getAtNull(ctxV2), "atNull mismatch");
        assertEq(_getThetaSum(ctxV1), _getThetaSum(ctxV2), "getThetaSum mismatch");
    }
}
