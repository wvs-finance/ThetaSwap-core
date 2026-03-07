"""Run duration model — thin CLI wrapper."""
from __future__ import annotations

import json
from dataclasses import asdict

from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
from econometrics.duration import duration_model_robust, economic_magnitude
from econometrics.ingest import build_lagged_positions


def main() -> None:
    positions = build_lagged_positions(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=5)
    print(f"Positions (lag=5): {len(positions)}")

    result = duration_model_robust(positions, measure="max")
    print(f"\n=== Duration Model: log(blocklife) ~ max_A_T + IL (HC1) ===")
    print(f"n={result.n_obs}  R²={result.r_squared:.4f}")
    print(f"β₁(max_A_T) = {result.beta_a_t:.4f}  HC1 SE={result.robust_se_a_t:.4f}  p={result.robust_p_value_a_t:.6f}")
    print(f"β₂(IL)      = {result.beta_il:.4f}  HC1 SE={result.robust_se_il:.4f}  p={result.robust_p_value_il:.6f}")

    mag = economic_magnitude(result)
    print(f"\nA 0.10 increase in max A_T: {mag['pct_change']:+.1f}% position life ({mag['hours_shortened']:.1f} hours)")

    out = asdict(result)
    with open("data/econometrics/duration_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to data/econometrics/duration_result.json")


if __name__ == "__main__":
    main()
