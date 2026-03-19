export interface PortfolioSummary {
  totalDeposited: number
  longValue: number
  shortValue: number
  netPnl: number
}

export interface ActiveVault {
  pool: [string, string]
  feeTier: number
  longBalance: number
  shortBalance: number
  status: 'active' | 'settled'
  strike: number
  expiry: number
  payoutPreview: { long: number; short: number }
}

export interface SettledVault {
  pool: [string, string]
  settlementDate: number
  longPayout: number
  shortPayout: number
  netResult: number
}

export interface PortfolioProps {
  summary: PortfolioSummary
  activeVaults: ActiveVault[]
  settledVaults: SettledVault[]
  onVaultClick?: (pool: [string, string]) => void
}
