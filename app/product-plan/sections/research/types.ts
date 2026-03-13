export interface ResearchMethodology {
  dataSource: string
  mechanism: string
  payoff: string
}

export interface ResultsSummary {
  totalEpochs: number
  epochsAboveStrike: number
  pctBetterOff: number
  meanHedgeValue: number
  totalPremiums: number
  totalPayouts: number
}

export interface WelfareComparison {
  label: string
  mean: number
  std: number
}

export interface DeltaDistBin {
  bin: string
  count: number
}

export interface PayoffSensitivityPoint {
  strike: number
  meanPayout: number
}

export interface CalibrationParameter {
  name: string
  value: string
  description: string
}

export interface ResearchProps {
  title: string
  abstract: string
  methodology: ResearchMethodology
  results: {
    summary: ResultsSummary
    welfareComparison: WelfareComparison[]
    deltaDistribution: DeltaDistBin[]
    payoffSensitivity: PayoffSensitivityPoint[]
  }
  parameters: CalibrationParameter[]
  conclusion: string
}
