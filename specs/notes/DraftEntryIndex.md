We want to find or build a state-variable that tracks the risk of adverse competition in liquidity provision

- grows as more lp's enter the market
- grows faster as sophisticcated LP's enter the market

Once this variable is found and is fully traceable on-chain we can price it

1. What is useful for lp's entering the market:

- headcount of mint/burn transaction NOT becuase ...


We now that LP's compete for prices, then for effects on competition we are better of tracking
changes on fee variables than on liquidity. Given the optimal tickRange where volume is concentrating what allows me to measure the entry
of lp's on that range such that insights from


tx = afterAddLiquidity(Position)

--> feeGrowthInside(position, tickRange)
    -----------------------------------    = x_{tx}
      feeGrowth(tickRange)

This represents how much of the available feeRevenue per unit of liquidity is captured by position

Then our metric becomes:

A = (\sum^{\#tx in block} \theta (x_{tx}^p))^{1/p}

> Most likely p  =2 , but we shall see
> \theta is the contribution of a position to such coefficient, Note that this contribution is greater whne the LP is sophisticated.

Assumming sopghisticated == JIT. Then

JIT => \theta = 1 

And in general \theta (life of the position) being decreasing in the life of the position with max value
=1 iff position is JIT

```
lifetime(position) = swapCount(removal) - swapCount(creation)
```

\theta = 1/lifetime. Note that \theta ends on afterRemoveLiquidity


Then the realized fee concetration index is a path that updates every afterRemoveLiquidity 
==> Any payoff built is path-dependent

===> To make it costly to manipulate we do time-wights on the tracked variables

====> time dependatn + path-dependant non-linear derivatives



## DERIVATIVES

payoff: 1 unit of account per 1 index appreciation

Who appreciates the index JITS --> JIT's are SHORT derivative

Who deppreciates the index PLP's --> PLP's are LONG derivative

--> There is a market

How to price derivative ?
--> no-arbitrage contingent claim pricing of time-dependant + path-dependant + non-linear derivatives
How to make the market ?
--> perpetuals

    ---> funding rate LONGS pay SHORTS
--> CFMM
    payoff -> trading function -> invariant

what is the price
--> price do not evolve in time but on liquidity events

--> price is how many units of fee revenue am I sacrificing per unit of lifetime (block)
--> This is the collateral is feeRevenue (or access to the feeRevenu through the LP token) and the 
feeConcetrationToken

[feeRevenue] / [feeConcentrationToken]



--> This payoff pays for every afterRemoveLiquidity

## IMPLEMENTATION DRAFTS
Hook callbacks:
- `afterAddLiquidity`: starts  lifetimes -> starts theta 
- `afterRemoveLiquidity`:  end lifetime -> end theta -> updates index ->  updates payoff (P&L)
- `afterSwap`: -> updates lifetimes -> upadtes theta
--------------------------------------------------------------------
| Priceable primitive | Fee concentration index (HHI weighted by θ) |
| Position lifetime unit | Swap count, not time |
| θ function | `1/lifetime` — max at JIT, decreasing |
------------------------------------------------------------

## Fee Concentration Index

We now need to think on the number representastion on the EVM of the feeConcetration index



1. The firts to think is that we are not storing the value and then taking sqrt.

Since the value will interact with sqrtPriceX96, we can follow the same numbe representation so

operating mul(sqrtPriceX96,feeConcentrationX96)

- Anothe consideration is x_k which is an elemnt of the index

feeGrowthInsideX128(position, tickRange) and same for feeGrowth(tickRange)

- What is the most optimal way to store the division, what is the number represntation

This also needs to consider we need to square the number meaning we probably want a number represntation or transformation that allows large values and sqauring does not lead overflows



THe consideration also goes for \theta_k, per position we save a number between 0 and 1 which
is the quotien between a natural naumber swapCount(reemoval, tickRange) - swapCount(creation)

