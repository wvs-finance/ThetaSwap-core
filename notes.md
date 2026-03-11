   	feeGrowthInside(position, tickRange) 
  ---------------------------------------- --> x_{position}
  	     feeGrowthInside(tickRange)           
  		                   
						   
- theta(position) =  1/ lk, where lk = 1/positionLifetime 
	  
	  
- positionLifetime  = blockNumber(burnPosition)- blockNumber(mintPosition)



- index = (sum_{position in ALL_POSITIONS} (theta(position)*(x_{position})**2)**(1/2))

- indexAtNull =  sum_{position in ALL_POSITIONS} (theta(position) /N, where N = headCountNumberOfLps
	            -----------------------------------------------
                          |
						  |
                          v
	                    THETA

- deltaPlus (afterRemoveLiquidity) = max( 0, index - indexAtNull)

Note if deltaPlus = C*, where C* is fixed

C*(theta, feeConcentration) = 
	index(theta(lifetime(position)), feeConcentration(position) ) - indexAtNull(theta(lifetime(position)) ,N)

Set N = 2 and let lifetime(1) = 1, lifetime(2) = 1

=> indexAtNull = sqrt( (1/lifetime(1) + 1/lifetime(2)) /(2**2))
         =  sqrt(2/4)
		 =  sqrt(2)/2
		 =  0.707

=> economic interpretation: Since all positions lasted the same You literally cannot get a lower index with 2 positions. It's the point of  maximum "spread" (minimum concentration).
              


==> (INVARIANT)\sum_{position in ALL_POSITIONS} feeConcentration(position) = 1 

feeConcentration(1) = 1/2
feeConcentration(2) = 1/2

index = √(1·1/4 + 1·1/4) 
      = √(1/2) 
	  = √2/2
	  
deltaPlus = 0 - the competitive equilibrium. The fact that Δ⁺ > 0 measures exactly
   how far from "fair competition" this pool is.


## Fabricating the Theta:

N = 2, lifetime(1) =1 and lifetime(2) =1 = > theta = 1/1 + 1/1 = 1 = Q.128 
