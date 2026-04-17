"""jupyter-nbconvert configuration for the Colombia FX-vol notebook suite.

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

If the loader ever fails (env.py moved, file missing), we fall through to
the literal 1800 s so nbconvert still works; a warning is printed so the
drift is visible in CI logs.
"""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path

# ── Resolve env.py by file location (parents[1]/env.py relative to here) ──

_CONFIG_DIR = Path(__file__).resolve().parent
_ENV_PATH = _CONFIG_DIR.parent / "env.py"

_FALLBACK_TIMEOUT_SECONDS = 1800  # kept in sync with env.NBCONVERT_TIMEOUT


def _load_env_timeout() -> int:
    """Return env.NBCONVERT_TIMEOUT, or the hard fallback if env.py is missing."""
    if not _ENV_PATH.is_file():
        warnings.warn(
            f"env.py not found at {_ENV_PATH}; falling back to "
            f"{_FALLBACK_TIMEOUT_SECONDS}s timeout. This is expected only "
            f"if the notebook directory has been restructured — update "
            f"this config's parents[1] offset if so.",
            RuntimeWarning,
            stacklevel=2,
        )
        return _FALLBACK_TIMEOUT_SECONDS

    spec = importlib.util.spec_from_file_location("fx_vol_env", _ENV_PATH)
    if spec is None or spec.loader is None:
        warnings.warn(
            f"Could not build importlib spec for {_ENV_PATH}; falling back "
            f"to {_FALLBACK_TIMEOUT_SECONDS}s timeout.",
            RuntimeWarning,
            stacklevel=2,
        )
        return _FALLBACK_TIMEOUT_SECONDS
    module = importlib.util.module_from_spec(spec)
    # Register by a private name so we do not collide with a real package
    # if env.py is later promoted to sys.path. The underscore prefix keeps
    # the namespace obviously-internal.
    sys.modules["_fx_vol_env_for_nbconvert"] = module
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
