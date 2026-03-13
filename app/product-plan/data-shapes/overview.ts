// =============================================================================
// ThetaSwap Data Shape Overview
//
// All TypeScript interfaces used across the four frontend sections.
// Section-specific types are also available in each section's types.ts file.
// =============================================================================

// ---------------------------------------------------------------------------
// Pool Explorer
// ---------------------------------------------------------------------------

export interface PoolVault {
  status: 'active' | 'settled' | 'none';
  strike: number;
  expiry: number;
  hwm: number;
  totalDeposits: number;
  settled: boolean;
  longPayoutPerToken: number;
}

export interface Pool {
  poolKey: string;
  pair: [string, string];
  feeTier: number;
  deltaPlusEpoch: number;
  deltaPlus: number;
  sparkline: number[];
  thetaSum: number;
  atNull: number;
  removedPosCount: number;
  positionCount: number;
  tvl: number;
  volume24h: number;
  vault: PoolVault | null;
}

export interface PoolExplorerProps {
  pools: Pool[];
  onPoolClick?: (pool: Pool) => void;
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  onFilter?: (filters: PoolFilters) => void;
}

export interface PoolFilters {
  pair?: string;
  feeTier?: number;
  vaultStatus?: 'active' | 'settled' | 'none' | 'all';
}

// ---------------------------------------------------------------------------
// Pool Terminal
// ---------------------------------------------------------------------------

export interface PoolIdentity {
  pair: [string, string];
  feeTier: number;
  poolKey: string;
}

export interface OracleState {
  deltaPlusEpoch: number;
  deltaPlusCumulative: number;
  atNull: number;
  thetaSum: number;
  removedPosCount: number;
  epochProgress: number;
  epochLength: number;
  epochStartTimestamp: number;
  lastPokeTimestamp: number;
}

export interface VaultState {
  strike: number;
  hwm: number;
  expiry: number;
  totalDeposits: number;
  settled: boolean;
  longPayoutPreview: number;
  shortPayoutPreview: number;
}

export interface Position {
  address: string;
  tickLower: number;
  tickUpper: number;
  liquidity: number;
  feeRevenue0: number;
  feeRevenue1: number;
  blockLifetime: number;
  maxDelta: number;
  isUser: boolean;
}

export interface PayoffPoint {
  deltaPlus: number;
  longPayout: number;
}

export interface TimeSeriesPoint {
  timestamp: number;
  deltaPlus: number;
  hwm: number;
  epochBoundary?: boolean;
}

export interface PoolTerminalProps {
  pool: PoolIdentity;
  oracle: OracleState;
  vault: VaultState;
  positions: Position[];
  payoffCurve: PayoffPoint[];
  timeSeries: TimeSeriesPoint[];
  onDeposit?: (amount: number) => void;
  onRedeemPair?: (amount: number) => void;
  onPoke?: () => void;
  onRedeemLong?: (amount: number) => void;
  onRedeemShort?: (amount: number) => void;
  onPositionClick?: (position: Position) => void;
}

// ---------------------------------------------------------------------------
// Portfolio
// ---------------------------------------------------------------------------

export interface PortfolioSummary {
  totalDeposited: number;
  longValue: number;
  shortValue: number;
  netPnl: number;
}

export interface ActiveVault {
  pool: [string, string];
  feeTier: number;
  longBalance: number;
  shortBalance: number;
  status: 'active' | 'settled';
  strike: number;
  expiry: number;
  payoutPreview: { long: number; short: number };
}

export interface SettledVault {
  pool: [string, string];
  settlementDate: number;
  longPayout: number;
  shortPayout: number;
  netResult: number;
}

export interface PortfolioProps {
  summary: PortfolioSummary;
  activeVaults: ActiveVault[];
  settledVaults: SettledVault[];
  onVaultClick?: (pool: [string, string]) => void;
}

// ---------------------------------------------------------------------------
// Research
// ---------------------------------------------------------------------------

export interface ResearchMethodology {
  dataSource: string;
  mechanism: string;
  payoff: string;
}

export interface ResultsSummary {
  totalEpochs: number;
  epochsAboveStrike: number;
  pctBetterOff: number;
  meanHedgeValue: number;
  totalPremiums: number;
  totalPayouts: number;
}

export interface WelfareComparison {
  label: string;
  mean: number;
  std: number;
}

export interface DeltaDistBin {
  bin: string;
  count: number;
}

export interface PayoffSensitivityPoint {
  strike: number;
  meanPayout: number;
}

export interface CalibrationParameter {
  name: string;
  value: string;
  description: string;
}

export interface ResearchProps {
  title: string;
  abstract: string;
  methodology: ResearchMethodology;
  results: {
    summary: ResultsSummary;
    welfareComparison: WelfareComparison[];
    deltaDistribution: DeltaDistBin[];
    payoffSensitivity: PayoffSensitivityPoint[];
  };
  parameters: CalibrationParameter[];
  conclusion: string;
}
