"""jupyter-nbconvert configuration for the Pair D Stage-2 Path A notebook suite.

Mirrors the canonical pattern at fx_vol_cpi_surprise/Colombia/_nbconvert_template/
(adapted for the Path A scope — sympy + QuantLib heavy v0/v3 NBs share the
same nbconvert pipeline as the FX-vol notebooks).

Pins two behaviors the default nbconvert pipeline does not enforce:

  1. ``TagRemovePreprocessor`` is enabled and set to strip the INPUT of any
     code cell tagged ``remove-input``. Outputs of those cells survive. This
     lets NB1/NB2/NB3 carry utility cells (imports, data-load boilerplate,
     plot helpers) whose source pollutes the rendered PDF but whose
     products (tables, figures, stream prints) are load-bearing. See the
     notebook design spec, Rule 5 — Code visibility.

  2. ``ExecutePreprocessor.timeout`` is pinned to ``env.NBCONVERT_TIMEOUT``
     (1800 s). The default 600 s is insufficient for NB2 GARCH-X MLE +
     NB3 bootstrap + Bai-Perron changepoint search on a clean venv. The
     literal 1800 lives in ``env.py`` alone so any future bump propagates
     through this config automatically.

Both settings are additive to nbconvert's own preprocessor pipeline — they
do not replace preprocessors that are enabled by default.

Loading env.py:
  env.py is not on ``sys.path``; it is imported by file location via
  ``importlib.util.spec_from_file_location`` (same pattern as the test
  suite and the notebook skeletons). env.py resolves:

      <this file>  = .../Colombia/_nbconvert_template/jupyter_nbconvert_config.py
      parents[1]   = .../Colombia/env.py  ← target

If the loader ever fails (env.py moved, file missing, importlib unable to
build a spec), we RAISE a ``RuntimeError`` rather than silently falling back
to a hard-coded literal. Rationale: env.NBCONVERT_TIMEOUT is the single
source of truth for the PDF-export runtime budget. A silent fallback would
mask structural drift — a moved env.py, a renamed directory, a broken
``parents[1]`` offset — and let CI pass while the notebook suite runs
under a duplicated, stale constant. A hard error surfaces the breakage at
config-load time, where the fix (update the path offset, or re-run
``just pre-commit-install``) is obvious.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# ── Resolve env.py by file location (parents[1]/env.py relative to here) ──

_CONFIG_DIR = Path(__file__).resolve().parent
_ENV_PATH = _CONFIG_DIR.parent / "env.py"

# Documented-expected value used ONLY in the RuntimeError message below so
# operators know what timeout env.NBCONVERT_TIMEOUT should currently produce.
# NOT used as a silent fallback — see _load_env_timeout() for the rationale.
_FALLBACK_TIMEOUT_SECONDS = 1800  # kept in sync with env.NBCONVERT_TIMEOUT


def _load_env_timeout() -> int:
    """Return env.NBCONVERT_TIMEOUT, or raise RuntimeError if env.py is unloadable.

    This function intentionally does NOT fall back to a hard-coded literal.
    env.NBCONVERT_TIMEOUT is the single source of truth for the notebook-
    export runtime budget; a silent fallback would hide structural drift
    (moved env.py, broken path offset, incomplete setup) behind a stale
    duplicate constant. A loud RuntimeError at config-load time forces the
    fix to happen where it's needed.
    """
    if not _ENV_PATH.is_file():
        raise RuntimeError(
            f"Could not load env.py at {_ENV_PATH}: file missing. "
            f"NBCONVERT_TIMEOUT is the single source of truth for the "
            f"notebook PDF-export runtime budget (expected value would have "
            f"been {_FALLBACK_TIMEOUT_SECONDS}s); falling back silently "
            f"would hide structural drift. To fix: update the `parents[1] / "
            f"\"env.py\"` path in this config if env.py has moved, or re-run "
            f"`just pre-commit-install` if setup is incomplete."
        )

    spec = importlib.util.spec_from_file_location("path_a_env", _ENV_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Could not load env.py at {_ENV_PATH}: importlib failed to "
            f"build a module spec. NBCONVERT_TIMEOUT is the single source "
            f"of truth for the notebook PDF-export runtime budget (expected "
            f"value would have been {_FALLBACK_TIMEOUT_SECONDS}s); falling "
            f"back silently would hide structural drift. To fix: update "
            f"the `parents[1] / \"env.py\"` path in this config if env.py "
            f"has moved, or re-run `just pre-commit-install` if setup is "
            f"incomplete."
        )
    module = importlib.util.module_from_spec(spec)
    # Register by a private name so we do not collide with a real package
    # if env.py is later promoted to sys.path. The underscore prefix keeps
    # the namespace obviously-internal.
    sys.modules["_path_a_env_for_nbconvert"] = module
    spec.loader.exec_module(module)
    return int(module.NBCONVERT_TIMEOUT)


# ── Apply config ──────────────────────────────────────────────────────────

c = get_config()  # noqa: F821 — jupyter injects ``get_config`` at load time

# TagRemovePreprocessor — hide input of cells tagged ``remove-input``.
# Cell OUTPUTS are preserved; only the source is stripped from the export.
c.TagRemovePreprocessor.enabled = True
c.TagRemovePreprocessor.remove_input_tags = {"remove-input"}

# ExecutePreprocessor — pin the per-cell execution timeout.
c.ExecutePreprocessor.timeout = _load_env_timeout()
