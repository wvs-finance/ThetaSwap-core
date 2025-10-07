// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ParityTaxRouter
 * @author ParityTax Team
 * @notice Router contract for executing swaps and liquidity operations with ParityTax hook integration
 * @dev This router handles both swap and liquidity modification operations, integrating with the ParityTax hook system
 * for equitable fee distribution between JIT and PLP providers
 */

import {TransientStateLibrary} from "@uniswap/v4-core/src/libraries/TransientStateLibrary.sol";


import {CurrencyLibrary} from "@uniswap/v4-core/src/types/Currency.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {TickBitmap} from "@uniswap/v4-core/src/libraries/TickBitmap.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import{
    Currency,
    CurrencySettler
} from "@uniswap/v4-core/test/utils/CurrencySettler.sol";


import "./types/Shared.sol";


import {IParityTaxRouter} from "./interfaces/IParityTaxRouter.sol";
import {IUnlockCallback} from "@uniswap/v4-core/src/interfaces/callback/IUnlockCallback.sol";

import {console2} from "forge-std/Test.sol";

import "./SwapMetrics.sol";
import "./LiquidityMetrics.sol";
import "./LiquiditySubscriptions.sol";
import {Position} from "@uniswap/v4-core/src/libraries/Position.sol";

import {IParityTaxHook} from "./interfaces/IParityTaxHook.sol";

import {ImmutableState} from "@uniswap/v4-periphery/src/base/ImmutableState.sol";


contract ParityTaxRouter is IUnlockCallback, SwapMetrics, LiquidityMetrics, LiquiditySubscriptions, ImmutableState,IParityTaxRouter{
    using SafeCast for *;
    using Position for address;
    using SqrtPriceMath for uint160;
    using TickMath for uint160;
    using TickMath for int24;
    using TickBitmap for int24;
    using StateLibrary for IPoolManager;
    using TransientStateLibrary for IPoolManager;
    using PoolIdLibrary for PoolKey;
    using BalanceDeltaLibrary for BalanceDelta;
    using CurrencyLibrary for Currency;
    using CurrencySettler for Currency;
    

    /**
     * @notice Initializes the ParityTaxRouter with required dependencies
     * @dev Sets up the pool manager, quoter, and parity tax hook for router operations
     * @param _poolManager The Uniswap V4 pool manager contract
     * @param _v4Quoter The V4 quoter for price calculations
     * @param _parityTaxHook The ParityTax hook contract for fee distribution
     */
    constructor(
        IPoolManager _poolManager,
        IV4Quoter _v4Quoter,
        IParityTaxHook _parityTaxHook
    ) SwapMetrics(_v4Quoter) LiquidityMetrics(_poolManager) LiquiditySubscriptions(_parityTaxHook) ImmutableState(_poolManager){}

    /**
     * @notice Modifies liquidity in a pool with PLP commitment handling
     * @dev Handles both adding and removing liquidity with proper commitment validation for PLP providers
     * @param poolKey Pool configuration data including currencies and fee tier
     * @param liquidityParams Liquidity modification parameters including amount and tick range
     * @param _plpLiquidityBlockCommitment Block commitment for PLP liquidity (used if no existing commitment)
     * @return delta The balance delta resulting from the liquidity modification
     * @dev There needs to be a mechanism for handling when a PLP already has a position. Let's query the poolManager for the position of the PLP
     * @dev WARNING: What important data can it pass to the tax controller for subscription management
     */
    function modifyLiquidity(
        PoolKey memory poolKey,
        ModifyLiquidityParams memory liquidityParams,
        uint48 _plpLiquidityBlockCommitment 
    ) external payable returns (BalanceDelta delta){
        PoolId poolId = poolKey.toId();
        uint256 tokenId = uint256(liquidityParams.salt);
        uint48 plpLiquidityBlockCommitment = _plpLiquidityCommitments[poolId][msg.sender][tokenId] > NO_COMMITMENT ? _plpLiquidityCommitments[poolId][msg.sender][tokenId] : _plpLiquidityBlockCommitment;

        
        Commitment memory plpLiquidityBlockCommitmentData = Commitment({
            committer: msg.sender,
            blockNumberCommitment: plpLiquidityBlockCommitment
        });

        bytes memory hookData = abi.encode(plpLiquidityBlockCommitmentData);
        bytes memory encodedLiquidityCallbackData = abi.encode(
                    ModifyLiquidityCallBackData(
                        msg.sender,
                        poolKey,
                        liquidityParams,
                        hookData
                    )
                );

        delta = abi.decode(
            poolManager.unlock(
               
                encodedLiquidityCallbackData
                
            ),
            (BalanceDelta)
        );

    }



    /**
     * @notice Executes a swap with ParityTax hook integration and price impact simulation
     * @dev Simulates swap output, calculates price impact, and executes swap with hook data
     * @param poolKey Pool configuration data including currencies and fee tier
     * @param swapParams Swap parameters including amount and direction
     * @return delta The balance delta resulting from the swap
     * @dev What we need is the PLP liquidity on the range where the swap will happen
     */
    function swap(
        PoolKey memory poolKey,
        SwapParams memory swapParams
    ) external payable returns (BalanceDelta delta)
    {
        (uint160 beforeSwapSqrtPriceX96,int24 beforeSwapTick,,uint24 lpFee) = poolManager.getSlot0(poolKey.toId());
        bool isExactInput = swapParams.amountSpecified <0;
        bool zeroForOne = swapParams.zeroForOne;

        
        uint128 plpLiquidity= poolManager.getLiquidity(poolKey.toId());

        (BalanceDelta noHookSwapDelta, SwapOutput memory noHookSwapOutput) = _simulateSwapOutputOnUnHookedPool(
            poolKey,
            swapParams
        );


        (uint160 expectedSqrtPriceImpactX96,int24 expectedAfterSwapTick) = _simulatePriceImpact(
            poolKey,
            beforeSwapSqrtPriceX96,
            plpLiquidity,
            swapParams,
            noHookSwapOutput
        );

        

        bytes memory hookData = abi.encode(
            SwapContext({
                poolKey: poolKey,
                swapParams: swapParams,
                amountIn: noHookSwapOutput.amountIn,
                amountOut: noHookSwapOutput.amountOut,
                beforeSwapSqrtPriceX96:beforeSwapSqrtPriceX96,
                plpLiquidity:plpLiquidity,
                expectedAfterSwapSqrtPriceX96:expectedAfterSwapTick.getSqrtPriceAtTick(),
                expectedAfterSwapTick:expectedAfterSwapTick
            })
        );
        bytes memory encodedSwapCallBackData = abi.encode(
                    SwapCallbackData(
                        msg.sender,
                        poolKey,
                        swapParams,
                        hookData)
                    );
        delta = abi.decode(
            poolManager.unlock(
                encodedSwapCallBackData
                ),
            (BalanceDelta)
        );

        uint256 ethBalance = address(this).balance;
        if (ethBalance > 0) CurrencyLibrary.ADDRESS_ZERO.transfer(msg.sender, ethBalance);
    }

    /**
     * @notice External unlock callback function called by the pool manager
     * @dev Entry point for pool manager callbacks during swap and liquidity operations
     * @param data Encoded callback data containing operation details
     * @return Encoded result data from the callback operation
     */
    function unlockCallback(bytes calldata data) external onlyPoolManager returns (bytes memory) {
        return _unlockCallback(data);
    }

    /**
     * @notice Internal unlock callback handler for swap and liquidity operations
     * @dev Routes between swap and liquidity modification callbacks based on data length
     * @param rawData Encoded callback data containing operation type and parameters
     * @return Encoded result data from the callback operation
     * @dev WARNING: Bytes length checking for routing on liquidity modifications
     * @dev This is actually the check for add PLP liquidity entry point
     * @dev Let's pass the msg.sender as the hook data
     */
    function _unlockCallback(bytes calldata rawData) internal virtual returns (bytes memory) {
        require(msg.sender == address(poolManager));
        BalanceDelta delta;

        if (rawData.length == SWAP_CALLBACK_DATA_LENGTH){
            SwapCallbackData memory data = abi.decode(rawData, (SwapCallbackData));

            (,, int256 deltaBefore0) = _fetchBalances(data.key.currency0, data.sender, address(this));
            (,, int256 deltaBefore1) = _fetchBalances(data.key.currency1, data.sender, address(this));

            require(deltaBefore0 == 0, "deltaBefore0 is not equal to 0");
            require(deltaBefore1 == 0, "deltaBefore1 is not equal to 0");

            delta = poolManager.swap(data.key, data.params, data.hookData);

            (,, int256 deltaAfter0) = _fetchBalances(data.key.currency0, data.sender, address(this));
            (,, int256 deltaAfter1) = _fetchBalances(data.key.currency1, data.sender, address(this));

            if (data.params.zeroForOne) {
                if (data.params.amountSpecified < 0) {
                    // exact input, 0 for 1
                    require(
                        deltaAfter0 >= data.params.amountSpecified,
                        "deltaAfter0 is not greater than or equal to data.params.amountSpecified"
                    );
                    require(delta.amount0() == deltaAfter0, "delta.amount0() is not equal to deltaAfter0");
                    require(deltaAfter1 >= 0, "deltaAfter1 is not greater than or equal to 0");
                } else {
                    // exact output, 0 for 1
                    require(deltaAfter0 <= 0, "deltaAfter0 is not less than or equal to zero");
                    require(delta.amount1() == deltaAfter1, "delta.amount1() is not equal to deltaAfter1");
                    require(
                        deltaAfter1 <= data.params.amountSpecified,
                        "deltaAfter1 is not less than or equal to data.params.amountSpecified"
                    );
                }
            } else {
                if (data.params.amountSpecified < 0) {
                    // exact input, 1 for 0
                    require(
                        deltaAfter1 >= data.params.amountSpecified,
                        "deltaAfter1 is not greater than or equal to data.params.amountSpecified"
                    );
                    require(delta.amount1() == deltaAfter1, "delta.amount1() is not equal to deltaAfter1");
                    require(deltaAfter0 >= 0, "deltaAfter0 is not greater than or equal to 0");
                } else {
                    // exact output, 1 for 0
                    require(deltaAfter1 <= 0, "deltaAfter1 is not less than or equal to 0");
                    require(delta.amount0() == deltaAfter0, "delta.amount0() is not equal to deltaAfter0");
                    require(
                        deltaAfter0 <= data.params.amountSpecified,
                        "deltaAfter0 is not less than or equal to data.params.amountSpecified"
                    );
                }
            }

            if (deltaAfter0 < 0) {
                data.key.currency0.settle(poolManager, data.sender, uint256(-deltaAfter0), false);
            }
            if (deltaAfter1 < 0) {
                data.key.currency1.settle(poolManager, data.sender, uint256(-deltaAfter1), false);
            }
            if (deltaAfter0 > 0) {
                data.key.currency0.take(poolManager, data.sender, uint256(deltaAfter0), false);
            }
            if (deltaAfter1 > 0) {
                data.key.currency1.take(poolManager, data.sender, uint256(deltaAfter1), false);
            }

            return abi.encode(delta);
        // TODO: bytes length cheching for routing on liquidity modifications
        // NOTE: This is actually the check for add PLP liquidity entry point
        } else if (rawData.length == LIQUIDITY_COMMITMENT_LENGTH) {
        
           
            ModifyLiquidityCallBackData memory data = abi.decode(rawData, (ModifyLiquidityCallBackData));
            
            
           
            (uint128 liquidityBefore,,) = poolManager.getPositionInfo(
                data.key.toId(), address(this), data.params.tickLower, data.params.tickUpper, data.params.salt
            );

            //NOTE: Let's pass the msg.sender as the hook data

            (delta,) = poolManager.modifyLiquidity(data.key, data.params, data.hookData);
            (uint128 liquidityAfter,,) = poolManager.getPositionInfo(
                data.key.toId(), address(this), data.params.tickLower, data.params.tickUpper, data.params.salt
            );

            (,, int256 delta0) = _fetchBalances(data.key.currency0, data.sender, address(this));
            (,, int256 delta1) = _fetchBalances(data.key.currency1, data.sender, address(this));

            require(
                int128(liquidityBefore) + data.params.liquidityDelta == int128(liquidityAfter), "liquidity change incorrect"
            );

            if (data.params.liquidityDelta < 0) {
                assert(delta0 > 0 || delta1 > 0);
                assert(!(delta0 < 0 || delta1 < 0));
            } else if (data.params.liquidityDelta > 0) {
                assert(delta0 < 0 || delta1 < 0);
                assert(!(delta0 > 0 || delta1 > 0));
            }

            if (delta0 < 0) data.key.currency0.settle(poolManager, data.sender, uint256(-delta0),false);
            if (delta1 < 0) data.key.currency1.settle(poolManager, data.sender, uint256(-delta1), false);
            if (delta0 > 0) data.key.currency0.take(poolManager, data.sender, uint256(delta0), false);
            if (delta1 > 0) data.key.currency1.take(poolManager, data.sender, uint256(delta1), false);

            return abi.encode(delta);
        }

        return abi.encode(delta);

        
    }


    
    /**
     * @notice Fetches balance information for a currency across user, pool, and delta holder
     * @dev Utility function for balance tracking during operations
     * @param currency The currency to fetch balances for
     * @param user The user address to check balance
     * @param deltaHolder The delta holder address for currency delta calculation
     * @return userBalance The user's currency balance
     * @return poolBalance The pool's currency balance
     * @return delta The currency delta for the delta holder
     * @dev Taken from @PoolTestBase
     */
    function _fetchBalances(Currency currency, address user, address deltaHolder)
        internal
        view
        returns (uint256 userBalance, uint256 poolBalance, int256 delta)
    {
        userBalance = currency.balanceOf(user);
        poolBalance = currency.balanceOf(address(poolManager));
        delta = poolManager.currencyDelta(deltaHolder, currency);
    }







}

