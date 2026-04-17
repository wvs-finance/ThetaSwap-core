"""Tests for the worktree-root `justfile` ``notebooks`` recipe (Task 1d).

Task 1d of the econ-notebook-implementation plan. The worktree-root
``justfile`` is the approved scope-expansion exception (plan Rule 4) — the
only non-``contracts/`` file these infrastructure tasks may touch. This test
suite verifies that:

  * A ``notebooks`` recipe exists in the justfile (head line + body).
  * The recipe references all three FX-vol notebooks (NB1/NB2/NB3) in both
    the ``--execute --to notebook --inplace`` phase AND the ``--to pdf``
    phase, in the canonical NB1 → NB2 → NB3 order.
  * The recipe passes ``--ExecutePreprocessor.timeout=1800`` (matching
    ``env.NBCONVERT_TIMEOUT``) on every execute invocation.
  * A scope-expansion comment on the recipe references plan "Rule 4".
  * Optionally (skipped if ``just`` is not on PATH) the real ``just --list``
    and ``just -n notebooks`` dry-run commands emit the expected output.

Primary verification is STRUCTURAL (parses the justfile text) — no
subprocess dependency. Subprocess assertions run only when ``just`` is
installed; otherwise they skip with an explicit reason.

Paths are imported from env.py per plan Rule 11 (no bare string paths).
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Final

import pytest

# ── Load env.py by file path (mirrors test_notebook_skeletons.py) ─────────

# This test file lives at: contracts/scripts/tests/test_just_notebooks_recipe.py
# env.py lives at: contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py
# contracts/ is parents[2] from here.
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

# ── Path resolution ───────────────────────────────────────────────────────

# Worktree root lives three levels above this test file:
#   parents[0] = tests/
#   parents[1] = scripts/
#   parents[2] = contracts/
#   parents[3] = worktree root (where the justfile lives)
_WORKTREE_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
JUSTFILE_PATH: Final[Path] = _WORKTREE_ROOT / "justfile"

NB1_NAME: Final[str] = _env.NB1_PATH.name
NB2_NAME: Final[str] = _env.NB2_PATH.name
NB3_NAME: Final[str] = _env.NB3_PATH.name
NB_NAMES_IN_ORDER: Final[tuple[str, ...]] = (NB1_NAME, NB2_NAME, NB3_NAME)

EXPECTED_TIMEOUT: Final[int] = _env.NBCONVERT_TIMEOUT  # 1800


# ── Helpers ───────────────────────────────────────────────────────────────

def _read_justfile_text() -> str:
    assert JUSTFILE_PATH.is_file(), f"Worktree-root justfile missing: {JUSTFILE_PATH}"
    return JUSTFILE_PATH.read_text(encoding="utf-8")


def _extract_notebooks_recipe_body(text: str) -> str:
    """Return the body lines of the ``notebooks`` recipe as a single string.

    The body is every line following ``notebooks:`` that is indented (space
    or tab), until the first non-indented, non-blank line (next recipe or
    EOF). Raises AssertionError if the recipe header is missing.
    """
    lines = text.splitlines()
    try:
        header_idx = next(
            i for i, line in enumerate(lines)
            if line.strip() == "notebooks:" or line.startswith("notebooks:")
        )
    except StopIteration as exc:  # pragma: no cover - asserted below
        raise AssertionError(
            "No `notebooks:` recipe header found in justfile"
        ) from exc

    body: list[str] = []
    for line in lines[header_idx + 1:]:
        if not line.strip():
            body.append(line)
            continue
        if line[0] in (" ", "\t"):
            body.append(line)
            continue
        break
    return "\n".join(body)


# ── Structural tests (primary verification) ───────────────────────────────

def test_justfile_exists_at_worktree_root() -> None:
    """The worktree-root justfile exists — sanity check for path resolution."""
    assert JUSTFILE_PATH.is_file(), (
        f"Expected worktree-root justfile at {JUSTFILE_PATH}"
    )


def test_justfile_has_notebooks_recipe_header() -> None:
    """The justfile declares a `notebooks` recipe."""
    text = _read_justfile_text()
    has_header = any(
        line.strip() == "notebooks:" or line.startswith("notebooks:")
        for line in text.splitlines()
    )
    assert has_header, (
        "Expected a `notebooks:` recipe header in the worktree-root justfile"
    )


def test_notebooks_recipe_comments_reference_scope_expansion() -> None:
    """Comment above or within the recipe references plan Rule 4 scope expansion.

    The recipe is the only non-``contracts/`` write the Phase 0 tasks make,
    so its justification MUST live right next to the recipe as an inline
    comment pointing at plan Rule 4.
    """
    text = _read_justfile_text()
    lines = text.splitlines()
    header_idx = next(
        i for i, line in enumerate(lines)
        if line.strip() == "notebooks:" or line.startswith("notebooks:")
    )
    # Look at the ~8 lines immediately above the recipe header for a `# ...`
    # comment referencing Rule 4.
    comment_window = "\n".join(lines[max(0, header_idx - 8):header_idx])
    assert "Rule 4" in comment_window, (
        "Recipe header should be preceded by a comment referencing plan "
        f"'Rule 4' (scope-expansion rationale). Got preceding lines:\n"
        f"{comment_window!r}"
    )


@pytest.mark.parametrize("nb_name", NB_NAMES_IN_ORDER, ids=lambda n: n)
def test_notebooks_recipe_references_each_notebook(nb_name: str) -> None:
    """Each of NB1/NB2/NB3 filenames appears somewhere in the recipe body."""
    body = _extract_notebooks_recipe_body(_read_justfile_text())
    assert nb_name in body, (
        f"Recipe body missing notebook filename {nb_name!r}. Body:\n{body}"
    )


def test_notebooks_recipe_runs_execute_phase_for_each_notebook() -> None:
    """Each notebook has an `nbconvert --execute ... --inplace` invocation.

    We look for a line containing both the notebook filename AND the
    ``--execute`` flag AND the ``--inplace`` flag — the signature of the
    in-place execution phase.
    """
    body = _extract_notebooks_recipe_body(_read_justfile_text())
    for nb_name in NB_NAMES_IN_ORDER:
        matching = [
            line for line in body.splitlines()
            if nb_name in line and "--execute" in line and "--inplace" in line
        ]
        assert matching, (
            f"No `nbconvert --execute ... --inplace` line for {nb_name} "
            f"in recipe body:\n{body}"
        )


def test_notebooks_recipe_runs_pdf_phase_for_each_notebook() -> None:
    """Each notebook has an `nbconvert --to pdf` invocation."""
    body = _extract_notebooks_recipe_body(_read_justfile_text())
    for nb_name in NB_NAMES_IN_ORDER:
        matching = [
            line for line in body.splitlines()
            if nb_name in line and "--to pdf" in line
        ]
        assert matching, (
            f"No `nbconvert --to pdf` line for {nb_name} in recipe body:\n"
            f"{body}"
        )


def test_notebooks_recipe_execute_phase_precedes_pdf_phase() -> None:
    """All --execute lines precede all --to pdf lines (fail-fast ordering).

    If any notebook's execute step fails, just stops before any PDF export,
    so NB1 execute < NB2 execute < NB3 execute < NB1 pdf < NB2 pdf < NB3 pdf.
    """
    body = _extract_notebooks_recipe_body(_read_justfile_text())
    lines = body.splitlines()

    last_execute_idx = max(
        (i for i, line in enumerate(lines) if "--execute" in line),
        default=-1,
    )
    first_pdf_idx = next(
        (i for i, line in enumerate(lines) if "--to pdf" in line),
        -1,
    )
    assert last_execute_idx >= 0, f"No --execute lines found in body:\n{body}"
    assert first_pdf_idx >= 0, f"No --to pdf lines found in body:\n{body}"
    assert last_execute_idx < first_pdf_idx, (
        "All --execute invocations must precede the first --to pdf "
        f"invocation. last_execute_idx={last_execute_idx}, "
        f"first_pdf_idx={first_pdf_idx}. Body:\n{body}"
    )


def test_notebooks_recipe_execute_phase_in_nb_order() -> None:
    """NB1 execute < NB2 execute < NB3 execute (canonical ordering)."""
    body = _extract_notebooks_recipe_body(_read_justfile_text())
    lines = body.splitlines()

    def _first_execute_idx(nb_name: str) -> int:
        for i, line in enumerate(lines):
            if nb_name in line and "--execute" in line:
                return i
        return -1

    nb1_idx = _first_execute_idx(NB1_NAME)
    nb2_idx = _first_execute_idx(NB2_NAME)
    nb3_idx = _first_execute_idx(NB3_NAME)
    assert nb1_idx >= 0 and nb2_idx >= 0 and nb3_idx >= 0, (
        f"Missing execute line for one of the notebooks "
        f"(nb1={nb1_idx}, nb2={nb2_idx}, nb3={nb3_idx}). Body:\n{body}"
    )
    assert nb1_idx < nb2_idx < nb3_idx, (
        f"Execute ordering must be NB1 < NB2 < NB3. Got indices "
        f"nb1={nb1_idx}, nb2={nb2_idx}, nb3={nb3_idx}. Body:\n{body}"
    )


def test_notebooks_recipe_uses_env_timeout() -> None:
    """Every --execute line carries ExecutePreprocessor.timeout=1800.

    1800 is pinned in env.NBCONVERT_TIMEOUT; the recipe must not drift.
    """
    body = _extract_notebooks_recipe_body(_read_justfile_text())
    execute_lines = [
        line for line in body.splitlines() if "--execute" in line
    ]
    assert execute_lines, f"No --execute lines found in body:\n{body}"
    timeout_flag = f"--ExecutePreprocessor.timeout={EXPECTED_TIMEOUT}"
    for line in execute_lines:
        assert timeout_flag in line, (
            f"Execute line missing {timeout_flag!r}:\n{line}"
        )


# ── Subprocess tests (complementary; skipped if `just` is absent) ─────────

_JUST_BIN: Final[str | None] = shutil.which("just")
_JUST_SKIP_REASON: Final[str] = (
    "`just` not on PATH in this test environment; structural assertions "
    "cover recipe shape. Install casey/just to enable subprocess verification."
)


@pytest.mark.skipif(_JUST_BIN is None, reason=_JUST_SKIP_REASON)
def test_just_list_includes_notebooks_recipe() -> None:
    """`just --list` from the worktree root mentions the `notebooks` recipe."""
    result = subprocess.run(
        [_JUST_BIN or "just", "--list"],
        cwd=_WORKTREE_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert "notebooks" in combined, (
        f"`just --list` output did not mention `notebooks`.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.skipif(_JUST_BIN is None, reason=_JUST_SKIP_REASON)
def test_just_dry_run_notebooks_emits_expected_commands() -> None:
    """`just -n notebooks` prints nbconvert invocations for all three notebooks.

    Dry-run mode echoes commands without executing them, so this test does
    not require jupyter or a populated DuckDB.
    """
    result = subprocess.run(
        [_JUST_BIN or "just", "-n", "notebooks"],
        cwd=_WORKTREE_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    # just echoes executed commands to stderr with -n; merge both.
    combined = result.stdout + result.stderr

    for nb_name in NB_NAMES_IN_ORDER:
        assert nb_name in combined, (
            f"Dry-run output missing {nb_name}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    assert "--execute" in combined, (
        f"Dry-run output missing `--execute` flag.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "--to pdf" in combined, (
        f"Dry-run output missing `--to pdf` flag.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert str(EXPECTED_TIMEOUT) in combined, (
        f"Dry-run output missing timeout value {EXPECTED_TIMEOUT}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
