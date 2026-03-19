# Intent


1. Build model
## Model Assumptions


> The model transitions are not indexed by time BUT by swaps

Then the model life time is the number of swaps 


------------------
## Model Types & Functions

From here we define

type LiquiditySupplyModelSimplestTest extends PosmTestSetUp::
     setUp()
     R1.3  initialization includes token Approval of routers, etx
     R1.4  The traders do not have identity, they are address(this) on tests,
     address constant TRADER = adddres(this)
     '''
     this is beacuase we = do not care on their dynamics
     since we are assuming they are all the same (uninformed)
     '''

	
type toyLiquiditySupplyModelSimplest extends ToyCLAMM2Dir::
     Markets(marketKey);
	R1.1  Both markets MUST have the same underluyign AND unit of account
	R1.2. One of the tokens is a unit of account token (numeraire)

     TradingFLow(marketKey);

      Simplest ==> rules

     PerfectVolumeElasticityWrtLiquidityDepth
     '''
     expl: This is one of the results of JIT papaer from capponi
     sophisticated LP's maximize crowding out effects to passivle LP's when
     uninformed trading flow respond to LiquidityDepth
     '''
     
     FixedMarketPrice
     '''
     expl: For simplicity we assume that the CFMM is the primary market, this is because in this way
     there is no informed trading flow by construction.
     Note that this requirement can be modeled as a consequence of the following model rule

     For every successful TradeRequest whicch execution price is X units awy from the fixedPrice
     the subsequent successful TradeRequest MUST be such that executionPrice = fixedPrice,
     '''


### 1. PerfectVolumeElasticityWrtLiquidityDepth

This is a rule on the swap behavior the TRADER will follow in response ONLY to the LiquidityDpeth
 Observed

This is

rule PerfectVolumeElasticityWrtLiquidityDepth(
	type LiquidityDepth(afterAddLiquidity OR event modifyLiquidity, StateLibrary)
	) --> SwapVolume 
	      
- more LiquidityDepth ==> more SwapVolume
- perfect elastic --> THIS IS WE NEED A DETERMINISTIN RULE FOR HOW SWAPVOLUME REACTS TO LIQUIDITY DPTH
THAT FULFILLS PERFECT ELASTICITY


Following the notation of the formal state model reference we have

elasticity \(\eta\) is defined as  \Delta V/V /Delta L/ L (informal notation), now bringing this to model notation we have

$$
    \eta = \frac{\frac{\sum^N \delta_i + \delta_{N+1}}{\sum^N \delta_i}}{\frac{L_{i*} + \ell^{(k)}}{L_{i*}}}
$$


To define a proxy for perfect elasticity $\eta \to \infty $, we have $\eta_{\texttt{EVM}} < 2^{256}$

Then "despjando" for swap (since thery are the ones reacting to liquidity depth), in response to a
addLiquidity event with position liquidity entered \(\ell^{(k)}\), which is position \(k\) minte an on-rnage position with liquidity size \(\ell^{(k)}\) such that the tick raneg liquidity is now \(L_{i*} + \ell^{(k)}\), then the next-coming swap (can be a single request or bundle ) \(\delta_{N+1}\) must satisfy:

$$
	\delta_{N+1} \leq \eta_{\texttt{EVM}} \cdot \big ( \frac{\sum \delta_i }{L_{i*}}\big) \cdot L_{i*} + \ell^{(k)}) - \sum \delta_i
$$


This is
property perfectElastic(LiquidityDepth(beforeSwap), SwapVolume(afterSwap))

This implies, just the same way uniswap keeps track of a \(L\) scalar that tracks the static
portafolio (X, Y) important information and such that it represetn accumulation of the reserve, etc

And allows to be perfectly indexed by ticks 

We need an equivalent accumulator \(V\) that does the same for the trade cummuklative \((\delta_x, \delta_y)\) and is indexed by ticks


Since it will be divided by liquidity it must be uint128

This allows one to track \(\sum \delta + \delta\) the same way \Liquidity + \ell is tracked on uniswap and thus they have the same underlying structure and can bve compared and operated together 


Let's trace the simil on liquidity updates so we can start the design of this component. When someone adds liquidity it interacts with the periphery contracts (PositionManager).
----------------------------------------------PositionManager----------------------------------------
 function _modifyLiquidity(
   PositionInfo info,
   PoolKey memory poolKey,
   int256 liquidityChange,
   bytes32 salt,
   bytes calldata hookData
 ) internal returns (BalanceDelta liquidityDelta, BalanceDelta feesAccrued) {
        (liquidityDelta, feesAccrued) = poolManager.modifyLiquidity(
            poolKey,
            ModifyLiquidityParams({
                tickLower: info.tickLower(), tickUpper: info.tickUpper(), liquidityDelta: liquidityChange		, salt: salt
            }),
            hookData
        );
	---------------------------PoolManager--------------------------------------------
	   BalanceDelta principalDelta;
            (principalDelta, feesAccrued) = pool.modifyLiquidity(
                Pool.ModifyLiquidityParams({
                    owner: msg.sender,
                    tickLower: params.tickLower,
                    tickUpper: params.tickUpper,
                    liquidityDelta: params.liquidityDelta.toInt128(),
                    tickSpacing: key.tickSpacing,
                    salt: params.salt
                })
            );
	    -----------------------------Pool----------------------------------
	        struct State {
        	       uint128 liquidity;
        		mapping(int24 tick => TickInfo) ticks;
        		mapping(int16 wordPos => uint256) tickBitmap;
        		mapping(bytes32 positionKey => Position.State) positions;
    	       }

	       struct VolumeState{
	       	      mapping(int24 tick => VolumeTickInfo) ticks;
	       }

	       struct VolumeTickInfo{
	       	      uint128 volumeGross;
		      int28 volumeNet;
	       }

	       Like:

	       (TickInfo) -> (VolumeTickInfo)
	       '''
	       Thinking this way since feeGrowth is updated on swap so indirectly tracks volume 

	       struct TickIfo

    	       struct ModifyLiquidityState {
               	      bool flippedLower;
 		      uint128 liquidityGrossAfterLower;
        	      bool flippedUpper;
        	      uint128 liquidityGrossAfterUpper;
    	      }
		State calldata self;
	       {
		     ModifyLiquidityState memory state;

                     updateTick(self, tickLower, liquidityDelta, false);
                     updateTick(self, tickUpper, liquidityDelta, true);
		     
		     TickInfo storage info = self.ticks[tick];
		         struct TickInfo {
       			 	 uint128 liquidityGross;
    				 int128 liquidityNet;
				 ....
		          }
			 uint128 liquidityGrossBefore = info.liquidityGross;
                         int128 liquidityNetBefore = info.liquidityNet;
		         uint128 liquidityGrossAfter =
			                              LiquidityMath.addDelta(
										liquidityGrossBefore,
										liquidityDelta
									    );
			 int128 liquidityNet = upper ? liquidityNetBefore - liquidityDelta :
			  		       	       liquidityNetBefore + liquidityDelta;

		flipped = (liquidityGrossAfter == 0) != (liquidityGrossBefore == 0);

                 }
            }
     

        ---------------------------------------------------------------------------------



You need to normalize by liquidity, the same way `feeGrowthGlobal` does:

```
feeGrowthGlobal += feeAmount / self.liquidity ==> volumeGrowthGlobal += swapAmount / self.liquidity
```

> volume **per unit of liquidity** :

> Is this on TickLens.sol on the panoptic dependenvy
This requires the

mapping(int24 tick => VolumeTickInfo) ticksOnVolume;

struct VolumeTickInfo{
       uint256 volumeGrowthOutside0x128 // cummulative token0 volume outside this tick
}
```
volumeGrowthInside = getVolumeGrowthInside(tickLower, tickUpper)
totalVolume = volumePerLiquidity * positionLiquidity
```

This is directly comparable to `L` because:

- `L` is uint128 liquidity at the active tick
- `V = volumeGrowthInside * L` gives you the total volume that flowed through that liquidity

Track volume elasticity to liquidity depth on chain, something like:

```
  η = (swapDelta / self.liquidity) / volumeGrowthInside / (liquidityDelta / self.liquidity)
  = swapDelta / volumeGrowthInside / (ΔL / L)
```


Then, starting from:

```
δ_{N+1} ≤ η_EVM · (Σδ_i / L_{i*}) · (L_{i*} + ℓ^(k)) - Σδ_i
```

The `Σδ_i / L_{i*}` term is `volumeGrowthInside` (cumulative volume per liquidity).

`L_{i*} + ℓ^(k)` is `self.liquidity` after the add (since `self.liquidity += liquidityDelta` already fired).


```
δ_{N+1} ≤ η_EVM * volumeGrowthInside * ℓ^(k)
```

In Solidity:

```
swapDelta <= ETA_EVM * volumeGrowthInside * liquidityDelta
```

Where:
- `ETA_EVM` — your perfect elasticity proxy constant (`type(uint128).max` or similar)
- `volumeGrowthInside` — from the per-liquidity accumulator
- `liquidityDelta` — the `ℓ^(k)` that just enteredThen the above formula





2. FIxedMeanMarketPrice

At high level:
struct FixedMeanMarketPrice{
       uint160 lastPrice
       PoolId referenceMarket
}

function poolId(FixedMarketPrice) returns(PoolId) 
function lastPrice(FixedMarketPrice) returns(uint160)

function fixedMarketPrice(PoolId){
	 require(StateLibrary.slot0(poolId()) == lastPrice())
}


This needs formal verification

type MeanRevertingVolume(vm.snapshot(state)):
     require(isInvese(swapDeltaPrevious, swapDeltaNow);


Then we are claiming the following construction rule

                               MeanRevertingVolume ===> FixedMarketPrice



CFMMIsOnlyMarket(Model,underlying(market))) ===> impermanentLoss(Model, underlying(market))) ==0 


> We assume a risk-free rate of 0 

This is becuase there is no other benchmark strategy to allocate cpital in this model than liquidity provision

Then the only cost for liquidity provision is operational (gas cost for rebalancing). Thus the
trading fee is bounded below by the LiquidityMintingANdBurnignGasCost

On our model the trading fee is 4*LiquidityMintingANdBurnignGasCost,

   This is 1 unit that for that finances the LiquidityMintingANdBurnignGasCost
   2 units that the JIT captures
   1 unit the JIT leaves as surplues to the PLP as payment for providing the liquidityDepth that
   attracted the tradingVolume



Then \phi = 4*max(LiquidityMintingAndBurningGasCost)

ElasticVolumeWrtLiquidityDepth ==> liquidityDepth_{t+1}(elasticity(volume_t, liquidityDepth_t))
									|
									|
							<---------------
			This is an update rule we must engineer

MeanRevertingVolume ==> JITALwaysWantsToRespondToSwap

'''
This is to be consistnent with JIT always wanting to capture the non-informed trading volume

     ==> JIT probability of arrival is always 1

UnawareSufficiency
	- The JIT does not know, but No swap can exceed JITLiquidityOnSwap
	'''
	This is to show the case where the LP sophisitcation is on  BOTH technology
	(ability to detect swaps on mempool) AND capital, meaning they alwsy have anough capital
	to fulfill UninformedTRading flow 

value(\sum (swaps)) <= value(representativeLPPosition) -> (invariant)

ModelState::
	InitialState(NoSwaps):
		LiquidityProviders(market): 
	 		count(LiquidityProviders,market)) = 4 (2 per pool)
							          |
								  -> 1 plp ^ 1 jit 
        ==> All liquidity providers have same initial capital

LiquidityProvider(type):
	Inventory: [underlying, cash]
	type: <PLP>; <JIT>;

	liquidity(ModelState(...); ...)

LiquidityProvider(<PLP>):
	
	liquidity(ModelState(...); elasticity(volume, liquidityDepth))	
	'''
	passive LP's provide liquidity that maxmizes the demand subject to the
        perfect elasticity only available information they know and budget constrain
	(inventory constrain)
	
	'''

LiquidityProvider(<JIT>)

	liquidity(ModelState(...), liquidityPLP, elasticity)
	'''
	jit LP's provide liquidity such thet they ALWAYS capture 2 units of fee and
	leave the plp 1 unit of surplus
	'''

MeanRevertingVolume  ==> MeanRevertingPrice ==>  ConstantTickSpread



 --> Each swap crosses the tickRange ==> triggers fee revenue collection
 '''
 This is to collect the fees on eacxh swap and thuis calculate markouts at each swap
 '''

--> After each swap a passive liquidity provider enters and adds liquidity such that its share MUST be the same as the others LP's

==> AT THE END THE NUMBER OF SWAPS PER POOL EAULS THE NUMBER OF LP'S + 2

--> The same behavor happens for both pools



==> In one pool ONE passive PLP has access to an instrument that pays
one unit of account per liquidity provider that enters the pool.


==> Result: The ONE PLP that uses the surplus share he has to buy the instrument while
the others LP's on both pools re-invest the surplus as liquidity


- Show that the PLP  hedges the competition risk

- Show that the competition risk is the only risk associated with passive liquidity provision in this model



