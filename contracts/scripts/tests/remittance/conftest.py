"""Remittance test package conftest — defers to Rev-4 parent conftest.

The Rev-4 conftest at ``contracts/scripts/tests/conftest.py`` is automatically
discovered by pytest as an ancestor conftest when running tests under
``contracts/scripts/tests/remittance/``. That mechanism alone already makes
the ``conn`` fixture (session-scoped read-only DuckDB connection to
``structural_econ.duckdb``) visible here — no re-export or re-import is
required.

This file exists solely to **fail loudly at collection time** if the Rev-4
conftest cannot be located, which catches accidental deletion or path drift
of the shared fixture source before any test runs. We deliberately do NOT
execute the Rev-4 conftest via ``importlib.util.spec_from_file_location``:
doing so would create a second, unregistered module object and break the
``@dataclass`` helpers inside Rev-4 conftest (which rely on
``sys.modules[cls.__module__]`` being populated by pytest's own collector).

If a remittance-specific fixture ever needs to exist, add it below the
guard — do NOT override inherited fixtures silently.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

# Rev-4 conftest absolute path. This file lives at:
#   contracts/scripts/tests/remittance/conftest.py
# parents[0] = remittance/, parents[1] = tests/
_REV4_CONFTEST_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "conftest.py"

# Fail loudly — do not mask a missing parent conftest as a silent
# "no fixture" error deep inside a test run.
if not _REV4_CONFTEST_PATH.is_file():
    raise RuntimeError(
        f"Rev-4 shared conftest.py not found at {_REV4_CONFTEST_PATH}; "
        "the remittance test suite requires it for the `conn` fixture. "
        "Either restore the Rev-4 conftest or replace this defer shim with "
        "an explicit local `conn` fixture (NOT recommended)."
    )
