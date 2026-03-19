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
  /** Called when user clicks a pool row to drill down into the Pool Terminal. */
  onPoolClick?: (pool: Pool) => void;
  /** Called when user clicks a column header to sort. */
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  /** Called when user changes filter controls. */
  onFilter?: (filters: PoolFilters) => void;
}

export interface PoolFilters {
  pair?: string;
  feeTier?: number;
  vaultStatus?: 'active' | 'settled' | 'none' | 'all';
}
