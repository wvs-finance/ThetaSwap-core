export interface PoolIdentity {
  pair: [string, string]
  feeTier: number
  poolKey: string
}

export interface OracleState {
  deltaPlusEpoch: number
  deltaPlusCumulative: number
  atNull: number
  thetaSum: number
  removedPosCount: number
  epochProgress: number
  epochLength: number
  epochStartTimestamp: number
  lastPokeTimestamp: number
}

export interface VaultState {
  strike: number
  hwm: number
  expiry: number
  totalDeposits: number
  settled: boolean
  longPayoutPreview: number
  shortPayoutPreview: number
}

export interface Position {
  address: string
  tickLower: number
  tickUpper: number
  liquidity: number
  feeRevenue0: number
  feeRevenue1: number
  blockLifetime: number
  maxDelta: number
  isUser: boolean
}

export interface PayoffPoint {
  deltaPlus: number
  longPayout: number
}

export interface TimeSeriesPoint {
  timestamp: number
  deltaPlus: number
  hwm: number
  epochBoundary?: boolean
}

export interface PoolTerminalProps {
  pool: PoolIdentity
  oracle: OracleState
  vault: VaultState
  positions: Position[]
  payoffCurve: PayoffPoint[]
  timeSeries: TimeSeriesPoint[]
  onDeposit?: (amount: number) => void
  onRedeemPair?: (amount: number) => void
  onPoke?: () => void
  onRedeemLong?: (amount: number) => void
  onRedeemShort?: (amount: number) => void
  onPositionClick?: (position: Position) => void
}
