"""Tests for the placeholder README.md (all notebook skeletons now retired).

Task 1c of the econ-notebook-implementation plan, narrowed progressively.
NB1 was authored by Task 7 (Trios 1-3) and is covered by
``test_nb1_section1.py``. NB2 was authored by Task 16 (§1-2 setup +
descriptive stats) and is covered by ``test_nb2_section1_2.py``. NB3
was authored by Task 24 (§1 setup + §2 T1 exogeneity) and is covered by
``test_nb3_section1_2.py``. All three notebooks are now authored, so the
skeleton-shape invariants (2-cell / zero-code / all-markdown) no longer
apply to any of them — they are retained in git history via earlier
commits.

Remaining assertions (placeholder README only):

  * The placeholder README.md exists, is short (< 500 bytes), and references
    "Task 30" (the Jinja2 auto-render task that overwrites this file).

No mocks — reads the actual README.md file on disk.

Paths are imported from env.py per Rule 11 of the implementation plan (no
bare string paths in notebooks or tests). env.py is not on sys.path, so we
load it by file location following the same pattern as test_env.py.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Final

# ── Load env.py by file path (mirrors test_env.py) ────────────────────────

_ENV_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)


def _load_env():
    """Load env.py as a module by file path (it is not on sys.path)."""
    spec = importlib.util.spec_from_file_location("fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {_ENV_PATH}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_env = _load_env()

# ── Path constants (sourced from env.py per Rule 11) ──────────────────────

README_PATH: Final[Path] = _env.READMEPath


# ── Placeholder README.md tests ───────────────────────────────────────────

def test_readme_placeholder_exists() -> None:
    """Placeholder README.md exists (will be overwritten by Task 30)."""
    assert README_PATH.is_file(), f"Missing placeholder README: {README_PATH}"


def test_readme_placeholder_references_task_30() -> None:
    """Placeholder body mentions Task 30 as the auto-render author."""
    content = README_PATH.read_text(encoding="utf-8")
    assert "Task 30" in content, (
        f"README placeholder should reference 'Task 30'; got: {content!r}"
    )


def test_readme_placeholder_is_short() -> None:
    """Placeholder README stays under 500 bytes — just a pointer, not content."""
    size = README_PATH.stat().st_size
    assert size < 500, (
        f"README placeholder grew to {size} bytes — should be a one-line "
        f"pointer under 500 bytes (Task 30 writes the real content)."
    )
