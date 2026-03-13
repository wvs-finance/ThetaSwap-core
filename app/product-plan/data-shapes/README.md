# ThetaSwap Data Shapes

## Entities

### Pool
A Uniswap V4 pool being monitored by the FCI oracle. Has a PoolKey (bytes32), current Delta-plus (fee concentration severity, 0.0-1.0), theta-sum (cumulative sum of 1/block_lifetime_k), atNull (competitive null threshold), and epoch configuration (length, start time).

### Position
An LP position within a pool. Identified by owner address and tick range (tickLower, tickUpper). Tracks liquidity amount, fee revenue (token0 and token1), block lifetime (seconds active), and maximum Delta-plus experienced during the position's life.

### Vault
An insurance vault instance for a specific pool and expiry cycle. Stores strike price (Delta-plus threshold), expiry timestamp, HWM (high-water mark of observed Delta-plus), total USDC deposits, and settlement status. Mints paired LONG + SHORT tokens on deposit.

### LongToken
ERC-6909 token representing the insurance buyer's claim. Payout after settlement = f(HWM, strike) using a power-squared lookback payoff. Value increases when fee concentration exceeds the strike.

### ShortToken
ERC-6909 token representing the insurance seller's exposure. Payout after settlement = 1 - longPayoutPerToken. The counterparty to LongToken -- conserves total value with LongToken.

### OracleReading
A snapshot of Delta-plus at a point in time, derived from HWMUpdated events emitted by the oracle payoff module. Includes the sqrtPrice conversion of the concentration index. Not a stored struct -- reconstructed from event logs.

### Epoch
A time boundary for accumulating Delta-plus. Defined by epoch length (seconds) and start time. The epoch-reset variant of Delta-plus (getDeltaPlusEpoch) accumulates within an epoch and resets at the boundary.

## Relationships

- Pool has many Positions
- Pool has many OracleReadings
- Pool has many Epochs
- Pool has one active Vault (per expiry cycle)
- Vault mints LongToken and ShortToken pairs (1:1 ratio)
- Vault reads OracleReadings via the poke() function
- Position belongs to one Pool, owned by one address
- LongToken and ShortToken belong to one Vault
