The payoff of a liquidity perovider whib lends it's position is decomposed as a covered call payoff

as seen on Kristensen

LP = P_T - (P_T - K)^+ + RangePayoff

Consider the payoff has a range component. One can tokenized range striuctured products and this can be used by liquidity proirders to hedge or do other thin. Additionally if time is ioncorm[portated. This can help control the welfacre maximizationn or pprice the JIT intrution

Given a way to len the liquidyt poistion. Which is akin as selling a covered call in Panoptic

Then decomposing the non-covered call paprt of the paylfoff of the LP as arange struictured note how ?

Thus the range payoff must be tested in such way that is equivalent to

LP(providing liquidity)  + short a perpetual futures (- P_T) + long a call option (max (P_T -K, 0)) = rangePayoff


impliedOccupation time calculated from implied volatility

realizedOccupationTime


RANGE_ACCRUAL_NOTE::
	underlying: feeGrowthInside(liquidityPosition);
	strikeInterval: TickRange;
	coupon(period):  inStrikeInterval(price(swap)) ? fee*swap : 0x00;  
	observationPeriods: <NUMBER_OF_BLOCKS>, <...>
	accrualFrequency: <2 BLOCKS>, <N BLOCKS>, ..., <TIME_FREQUENCY>
	payoff(RANGE_ACCRUAL_NOTES) -> feeGrowthInside



Example: 6 block wsETTH/WBTC feeGrowth

RANGE_ACCRUAL_NOTE::BOND

BOND::
	principal: 

R1: Accrues cupon in each period (Already fullfilled by Uniswap design)
R2: Pays out the coupon at the end of the block (Start of the new block)
R3: strikeInterval can be changed
R4: The accrued cupon can change across periods (Dynamic Fees)
R5: entitles the holder to coupon payments
R6: entitles the holder the payment of the principal


CFMM(RANGE_ACCRUAL_NOTE):
	tradingFunction(payoff(RANGE_ACCRUAL_NOTE)):
		rule: NoArbitrage: price(RANGE_ACCRUAL_NOTE) =  price(liquidityPosition(underlying))
	      		   			       	     - price(futuresPerpetual(underlying))
						       	     + price(Option(underlying)

		rule NoArbitrage: price(RANGE_ACCRUAL_NOTE) =
	     		  sum(discounted(price(Option(underlying),tickLower))
			      - discounted(price(Option(underlying), tickUpper)))

		invariant (tradingFunction):

## Extensions

Extensions(RANGE_ACCRUAL_NOTE)::
	Accrual_Decrual(RANGE_ACCRUAL_NOTE) -> RANGE_ACCRUAL_NOTE
		updateAccrualFrequency(RANGE_ACCRUAL_NOTE, Frequency)
	rule: price(Accrual_Decrual(RANGE_ACCRUAL_NOTE) < price(RANGE_ACCRUAL_NOTE);
	
	TargetRedemptionNote(RANGE_ACCRUAL_NOTE) -> RANGE_ACCRUAL_NOTE
		setRedemptionTargetCap(RANGE_ACCRUAL_NOTE, Cap)

	Barriers(RANGE_ACCRUAL_NOTE) -> RANGE_ACCRUAL_NOTE
		setKnockInBarrier(RANGE_ACCRUAL_NOTE, Barrier)
		setKnockOutBarrier(RANGE_ACCRUAL_NOTE, Barrier)

	rule: price(Barriers(RANGE_ACCRUAL_NOTE)) < price(RANGE_ACCRUAL_NOTE)

	Callable(RANGE_ACCRUAL_NOTE) -> Option(RANGE_ACCRUAL_NOTE)
		mint(
			OptionType(Option(RANGE_ACCRUAL_NOTE))= CALL,
			OptionPosition(Option(RANGE_ACCRUAL_NOTE)) = SHORT
			strikePrice(Option(RANGE_ACCRUAL_NOTE))
		)
	 rule: price(Callable(RANGE_ACCRUAL_NOTE)) < price(RANGE_ACCRUAL_NOTE)
	 rule: Automatically repaid to the holder if certain conditions are met

	 BasketUnderlier(RANGE_ACCRUAL_NOTE) -> RANGE_ACCRUAL_NOTE
	 	updateUnderlying(RANGE_ACCRUAL_NOTE, MultiAssetVault (IERC7575))

	FloatingRangeAccrual(RANGE_ACCRUAL_NOTE) -> RANGE_ACCRUAL_NOTE
		updateCouponRule(RANGE_ACCRUAL_NOTE, TradingFeePolicy)

# Advantages:

credit risk --> hack risk ==> hack risk < credit risk
- In traditional finance, the product is not standarized, and is usually not exchange-traded. However
the nature of LP's make the product possible to be tokenized and standarized considering the identity

LP(providing liquidity)  + short a perpetual futures (- P_T) + long a call option (max (P_T -K, 0)) = rangePayoff

# Replication

- RAN can be thought as a series of range cash-or-nothing (digital options)
- each option pays (feeGrowth/#Blocks (or observationPeriods))


  portafolio(strike) = (feeGrowth/#Blocks (strike), 0)
			   (cash)

Then the price of RAN is analytical when the price of digital options are calculated

# Paper


- fee-free LPing is akin to a 1/2 power perpetual (REF)
- fee-free LPing can be perfectly hedged with a squared perpetual payoff(REF)
- fee-free CLAMM position when lent is akin to shorting a covered call or a cash-secured put (REF)
- fee-free CLAMM positions alough more capital efficient (REF)
  - No LP would participate due to impermanent loss (REF)
- impermanent loss premia is needed to encourage LPing (REF)
- CLAMM imperment loss premia is the cash-flow induced by tradingFees on fee CLAMM(REF)
- fee CLAMM when lent needs to be paid by borrower of the LP position (REF -> Panoptic)
- fee CLAMM payoff is fee-free CLAMM payoff + RangePayoff component (REF)
- RangePayoff are part of LPing expected return (REF)
- RangePayoff are part of the LPing pricing (REF)
- RangePayoff capture the Theta component of LPing (REF)
- RangePayoffs can be standarized with RangeAccrualStructuredNotes (REF --> This is the work)
  - RangeStructuredNotes capture the Theta component of LPing (REF)
- RangeStructuredNotes pricing is uniquely determined by the  "impliedOccupationTime"
- "impliedOccupationTime" is uniquely determined by impliedVolatility
- Then the following ThetaSwap market emerges:

feeGrowth                E[T_ITM(impliedVolatility) -> "impliedOccupationTime"]
----------  *(    
observationFrequency

		- realizedOccupationTime(realizedVolatility) --> TO_BE_PROVED

- RangeStructuredNotes pricing is obtained analyticaly from a series of "delayed" digital option straddles (OR THE option strategy that bundles a long call with a strikePrice lowTick and a short call with a
strikePrice upperTick)

> This allows standarized diversifications for LP's and contributes to DeFi composability
> This allows mechanisms for pricing JIT externalities on PLP


## Implementation Notes

Given an active LiquidityPosition the LP:
      mints a ThetaToken(isLong) --> RANGE_NOTE
      	    record RANGE_NOTE payoff
     	    collect RANGE_NOTE collateral

	    provideLiquidity on CLAMM(RANGE_NOTE)
	    provide (ThetaToken, collateral) liquidity on CFMM(RANGE_NOTE)
	    	    - initial price must satisfy no-arbitrage
	    swap MUST rebalance to no-arbitrage price
	    If perpetual
	       - long must finance the short (FundingFee on CFMM(RANGE_NOTE))
	       	 ----induces---->
			-> liquidation
		        -> reedemption

    mints a ThetaToken(isShort)
    	  require (exist(liquidityPosition, params(RANGE_NOTE)))