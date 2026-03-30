
struct Timepoint {
    bool initialized; // whether or not the timepoint is initialized
    uint32 blockTimestamp; // the block timestamp of the timepoint
    int56 tickCumulative; // the tick accumulator, i.e. tick * time elapsed since the pool was first initialized
    uint88 volatilityCumulative; // the volatility accumulator; overflow after ~34800 years is desired :)
    int24 tick; // tick at this blockTimestamp
    int24 averageTick; // average tick at this blockTimestamp (for WINDOW seconds)
    uint16 windowStartIndex; // closest timepoint lte WINDOW seconds ago (or oldest timepoint), _should be used only from last timepoint_!
  }



interface IVolatilityOracle {
  function timepoints(
    uint256 index
  ) external view returns (Timepoint);

  function timepointIndex() external view returns (uint16);
  function lastTimepointTimestamp() external view returns (uint32);
  function isInitialized() external view returns (bool);
   function getSingleTimepoint(uint32 secondsAgo) external view returns (int56 tickCumulative, uint88 volatilityCumulative);

  function getTimepoints(uint32[] memory secondsAgos) external view returns (int56[] memory tickCumulatives, uint88[] memory volatilityCumulatives);

  function prepayTimepointsStorageSlots(uint16 startIndex, uint16 amount) external;
}


write (TimePoint[MAX_LENGHT], ...)

  t ----------------------------> i(t)
  (blocktimestamp)               (tick)
   - lastIndex :: i(t-lastVisited)







  vol (i(t), E [i (...)] = f( i(t -lag) ) )




track on sqrtPriceX96 the metric And then the VolatilityOracle integration realizes the FeeConcentration index


What is the primitive needed to be tracked --> It MUST be a price

      --->  [feeRevenue(price)::unitOfAccount] / [::LiquidityActive(price)]

--> This is already tracked per-tick on TickState {}.

What is needed is to accumulate it on the oracle:
    - feeRevenuePerLiquidityX96 -> feeRevenuePerLiquidityTick -> write

    - when EACH of the tracked variables changes we update feeRevenuePerLiquidityX96,
      then we add slotX {feeRevenuePerLiquidityX96}

     - Each time StateViewExt.getSlotX() -> slotX { feeRevenuePerLiquidityX96 }

     ONLY ONE STORAGE SLOT added


- Does this metric captures what we want ?

every price update



   (feeGrowthInside0X128 *sqrtPriceX96 + feeGrowthInside0x128)/ liquidityNet(tick(sqrtPriceX96)))


--> UPDATES

----> per price (afterSwap)
       
---> per liquidity event (afterRemoveLiquidity/afterAddLiquidity)


- How 


--> CHECKPOINT : Test Algebra integration against behavioral semantics of the mentric 
