"""Root conftest: add research/ to sys.path so econometrics/backtest are importable."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "research"))
