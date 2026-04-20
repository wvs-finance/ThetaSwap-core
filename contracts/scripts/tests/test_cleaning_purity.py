"""CI lint asserting cleaning.py purity — no raw DB queries allowed.

Task 4 of the econ-notebook-implementation plan (Phase 0 infrastructure).
The FX-vol estimation notebooks must route every database read through
``scripts.econ_query_api``. This test defends that invariant statically:

  * A module called ``cleaning.py`` (to be created in Task 13b) will live at
    ``contracts/scripts/cleaning.py`` and hold the notebook-side cleaning
    helpers. Every public function in that module MUST call at least one
    ``econ_query_api`` function, and the module must contain ZERO raw
    database-query patterns.
  * Forbidden substrings (case-sensitive): ``.execute(``, ``.sql(``,
    ``.read_sql(``, ``duckdb.connect(``. These cover DuckDB direct
    execution, generic SQL invocation, pandas SQL reads (``read_sql``
    prefix also catches ``read_sql_query`` / ``read_sql_table``), and
    fresh DB connections.

The lint logic is self-validated against two synthetic fixtures:
  * ``fixtures/cleaning_violator.py`` — imports from ``econ_query_api`` but
    also calls ``conn.execute(...)`` directly. Must be flagged.
  * ``fixtures/cleaning_clean.py`` — wraps ``econ_query_api`` only; no
    raw queries. Must pass.

The real-file assertion against ``scripts/cleaning.py`` is skipped
gracefully with ``pytest.skip(...)`` when that file does not yet exist
(Task 13b has not landed). Once 13b creates it, the real-file test
activates automatically.
"""
from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path
from typing import Final

import pytest

# ── Paths ────────────────────────────────────────────────────────────────────

# This test lives at: contracts/scripts/tests/test_cleaning_purity.py
# ``parents[2]`` from here is ``contracts/``.
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR: Final[Path] = _CONTRACTS_DIR / "scripts"
_FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parent / "fixtures"

_CLEANING_MODULE: Final[Path] = _SCRIPTS_DIR / "cleaning.py"
_VIOLATOR_FIXTURE: Final[Path] = _FIXTURES_DIR / "cleaning_violator.py"
_CLEAN_FIXTURE: Final[Path] = _FIXTURES_DIR / "cleaning_clean.py"


# ── Lint constants ───────────────────────────────────────────────────────────

# Case-sensitive substrings that indicate a raw DB query.
# ``.read_sql(`` is a prefix that also catches ``.read_sql_query(`` and
# ``.read_sql_table(`` (pandas variants).
FORBIDDEN_PATTERNS: Final[tuple[str, ...]] = (
    ".execute(",
    ".sql(",
    ".read_sql(",
    "duckdb.connect(",
)

# Token every public function in cleaning.py must reference. Substring
# match is sufficient — covers both ``from scripts.econ_query_api import ...``
# style AND ``econ_query_api.get_weekly_panel(...)`` style.
API_MODULE_TOKEN: Final[str] = "econ_query_api"


# ── Pure lint helpers ────────────────────────────────────────────────────────

# Python 3.12+ tokenizes f-strings into three distinct token types:
# ``FSTRING_START`` (the ``f"`` prefix), ``FSTRING_MIDDLE`` (the literal
# text between interpolated braces), and ``FSTRING_END`` (the closing
# quote). These token constants do NOT exist on Python 3.11 and earlier,
# where f-strings were emitted as a single ``STRING`` token. We collect
# whichever of these constants exist at runtime so the lint remains
# correct on 3.12+ AND importable on 3.11.
_FSTRING_TOKEN_TYPES: Final[frozenset[int]] = frozenset(
    tok_type
    for tok_type in (
        getattr(tokenize, "FSTRING_START", None),
        getattr(tokenize, "FSTRING_MIDDLE", None),
        getattr(tokenize, "FSTRING_END", None),
    )
    if tok_type is not None
)


def _strip_comments_and_strings(source: str) -> str:
    """Return ``source`` with all comments and string literals removed.

    This prevents false positives when a docstring or comment mentions one
    of the forbidden patterns (e.g. a cleaning-module docstring that lists
    "forbidden substrings: ``.execute(``, ``.sql(``..."). Only executable
    code is linted.

    Uses :mod:`tokenize` for robust Python-aware stripping: comments are
    dropped entirely and string literals are replaced with ``""``. Tokens
    are concatenated with no separator — this keeps dotted-call patterns
    like ``conn.execute(`` intact (tokens ``conn``, ``.``, ``execute``,
    ``(`` concat to ``conn.execute(``) while safely erasing any string or
    comment content. The returned text is not a faithful Python source —
    it is only consumed by substring grepping.

    F-strings receive special handling on Python 3.12+, where they are
    split into ``FSTRING_START`` / ``FSTRING_MIDDLE`` / ``FSTRING_END``
    tokens. The ``FSTRING_MIDDLE`` token carries the literal text between
    interpolated ``{...}`` expressions — without explicit handling, an
    f-string like ``f"use {api}.execute( for debugging"`` would leak the
    substring ``.execute(`` into the cleaned output and falsely flag the
    module. All three fstring token types are dropped (equivalent to
    replacing the whole f-string with ``""``), matching the treatment
    applied to regular ``STRING`` tokens.
    """
    parts: list[str] = []
    readline = io.StringIO(source).readline
    for tok in tokenize.generate_tokens(readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING:
            parts.append('""')
            continue
        # F-string sub-tokens (Python 3.12+): drop all three so that the
        # f-string is completely elided from the cleaned text. Interpolated
        # name references inside ``{...}`` still appear as ordinary NAME
        # tokens, so genuine code paths are preserved.
        if tok.type in _FSTRING_TOKEN_TYPES:
            continue
        # NEWLINE, NL, INDENT, DEDENT, ENCODING, ENDMARKER contribute no
        # characters that affect substring matches; drop them. NAME, OP,
        # NUMBER etc. contribute their literal ``tok.string``.
        if tok.type in (
            tokenize.NEWLINE,
            tokenize.NL,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.ENCODING,
            tokenize.ENDMARKER,
        ):
            continue
        parts.append(tok.string)
    return "".join(parts)


def _find_forbidden_patterns(source: str) -> list[str]:
    """Return every FORBIDDEN_PATTERNS substring that appears in ``source``.

    Strips comments and string literals first so that docstrings mentioning
    forbidden patterns (as documentation) do not produce false positives.
    Pure function — no IO. Case-sensitive substring scan.
    """
    cleaned = _strip_comments_and_strings(source)
    return [pattern for pattern in FORBIDDEN_PATTERNS if pattern in cleaned]


def _public_function_sources(source: str) -> dict[str, str]:
    """Return ``{function_name: function_source_without_strings_or_comments}``.

    Public = name does not start with an underscore. The returned snippet
    is stripped of comments and string literals so a docstring that
    mentions ``econ_query_api`` (as documentation) does not falsely
    satisfy the "flows through API" check — an actual call to an API name
    is required.
    """
    tree = ast.parse(source)
    result: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            segment = ast.get_source_segment(source, node)
            stripped = (
                _strip_comments_and_strings(segment)
                if segment is not None
                else ""
            )
            result[node.name] = stripped
    return result


def _names_imported_from_econ_query_api(source: str) -> frozenset[str]:
    """Return the set of names imported from ``scripts.econ_query_api``.

    Handles both ``from scripts.econ_query_api import get_weekly_panel`` and
    ``from econ_query_api import get_weekly_panel`` (relative-style). When
    the module is imported via ``import scripts.econ_query_api as _api``
    the returned set includes the alias (or ``econ_query_api`` itself).
    """
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            # Accept ``econ_query_api`` at the tail of the dotted module path.
            if mod == API_MODULE_TOKEN or mod.endswith("." + API_MODULE_TOKEN):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == API_MODULE_TOKEN or alias.name.endswith(
                    "." + API_MODULE_TOKEN
                ):
                    # ``import scripts.econ_query_api`` → reference as full dotted
                    # path; ``import scripts.econ_query_api as api`` → reference
                    # as ``api``; ``import econ_query_api`` → ``econ_query_api``.
                    names.add(alias.asname or alias.name.split(".")[-1])
    return frozenset(names)


def _assert_flows_through_api(source: str, module_label: str) -> None:
    """Assert every public function in ``source`` flows through econ_query_api.

    Strict interpretation: EVERY public function must reference either the
    literal ``econ_query_api`` token OR at least one name imported from
    ``scripts.econ_query_api``. This covers both calling styles:
      * ``from scripts.econ_query_api import get_weekly_panel`` →
        function body calls ``get_weekly_panel(...)``.
      * ``import scripts.econ_query_api as api`` →
        function body calls ``api.get_weekly_panel(...)``.
    """
    public_fns = _public_function_sources(source)
    assert public_fns, (
        f"{module_label} declares no public top-level functions; "
        "a cleaning module must expose at least one API-backed helper"
    )

    imported_names = _names_imported_from_econ_query_api(source)
    # Tokens that count as evidence of an API call: the module name itself
    # (handles ``econ_query_api.get_weekly_panel(...)`` style) plus every
    # imported name.
    witness_tokens: frozenset[str] = frozenset({API_MODULE_TOKEN}) | imported_names

    offenders = [
        name
        for name, body in public_fns.items()
        if not any(token in body for token in witness_tokens)
    ]
    assert not offenders, (
        f"{module_label}: public function(s) {offenders} do not flow through "
        f"any econ_query_api name (searched tokens: {sorted(witness_tokens)}); "
        "every public function must call an econ_query_api function before "
        "any pandas post-processing"
    )


# ── Self-validation against synthetic fixtures ───────────────────────────────

def test_violator_fixture_is_flagged() -> None:
    """The violator fixture must trigger at least one forbidden-pattern hit."""
    assert _VIOLATOR_FIXTURE.is_file(), (
        f"violator fixture missing at {_VIOLATOR_FIXTURE}"
    )
    source = _VIOLATOR_FIXTURE.read_text()
    hits = _find_forbidden_patterns(source)
    assert hits, (
        "violator fixture was expected to contain at least one raw-query "
        "pattern but none were found — the lint cannot self-validate"
    )
    # Sanity check: the specific violation we hand-crafted is ``.execute(``.
    assert ".execute(" in hits, (
        "violator fixture should contain '.execute(' as its hand-crafted "
        f"violation; found instead: {hits}"
    )


def test_clean_fixture_is_pure() -> None:
    """The clean fixture must have zero forbidden patterns AND flow through the API."""
    assert _CLEAN_FIXTURE.is_file(), (
        f"clean fixture missing at {_CLEAN_FIXTURE}"
    )
    source = _CLEAN_FIXTURE.read_text()

    hits = _find_forbidden_patterns(source)
    assert not hits, (
        f"clean fixture unexpectedly contains forbidden pattern(s) {hits}; "
        "the fixture must wrap econ_query_api only"
    )

    _assert_flows_through_api(source, "clean fixture")


def test_clean_fixture_imports_econ_query_api() -> None:
    """The clean fixture must import from econ_query_api — the 'flows through' token."""
    source = _CLEAN_FIXTURE.read_text()
    assert API_MODULE_TOKEN in source, (
        f"clean fixture does not reference '{API_MODULE_TOKEN}'; "
        "cannot demonstrate 'flows through API' invariant"
    )


# ── F-string regression (Python 3.12+ safety) ────────────────────────────────

def test_violator_disguised_as_fstring_is_not_flagged() -> None:
    """An f-string whose middle contains ``.execute(`` must be elided.

    Python 3.12+ splits f-strings into ``FSTRING_START`` / ``FSTRING_MIDDLE``
    / ``FSTRING_END`` tokens. Without explicit handling, the literal text
    between interpolated expressions would leak into the cleaned source and
    produce a false positive. This test confirms that a forbidden pattern
    appearing ONLY inside the middle of an f-string is stripped along with
    the rest of the string literal.
    """
    source = (
        "def docstring_only() -> None:\n"
        "    x = 'value'\n"
        "    msg = f\"use {x}.execute( as mock\"\n"
        "    return msg\n"
    )
    cleaned = _strip_comments_and_strings(source)
    assert ".execute(" not in cleaned, (
        "f-string middle was not stripped — forbidden pattern leaked into "
        f"cleaned source: {cleaned!r}"
    )


def test_real_code_with_fstring_execute_survives() -> None:
    """Fix must not over-strip: a real ``conn.execute(...)`` call is still flagged.

    Guards against an over-eager fix that also drops genuine NAME/OP tokens
    that happen to compose ``.execute(``. The module below contains both a
    docstring-as-f-string mentioning ``.execute(`` (must be ignored) AND an
    actual ``conn.execute(...)`` call (must still trigger the lint). If the
    fix were too aggressive (e.g. dropping the NAME ``execute`` token), the
    real call would slip through.
    """
    source = (
        'def describe() -> str:\n'
        '    label = "sql"\n'
        '    doc = f"this helper used to call .execute( in {label} mode"\n'
        '    conn = object()\n'
        '    conn.execute("SELECT 1")\n'
        '    return doc\n'
    )
    hits = _find_forbidden_patterns(source)
    assert ".execute(" in hits, (
        "real conn.execute(...) call was NOT flagged — the f-string stripper "
        f"is over-eager and ate genuine code tokens. Hits: {hits}"
    )


# ── Real-file assertion (skips gracefully until Task 13b lands) ──────────────

def test_real_cleaning_module_is_pure() -> None:
    """The real ``scripts/cleaning.py`` must pass the same lint.

    Skipped with a clear reason when the file does not yet exist —
    Task 13b creates it. Once that task lands, this test activates
    automatically and defends the purity invariant in CI.
    """
    if not _CLEANING_MODULE.is_file():
        pytest.skip(
            f"scripts/cleaning.py not yet created (Task 13b pending); "
            f"expected path: {_CLEANING_MODULE}"
        )
    source = _CLEANING_MODULE.read_text()

    hits = _find_forbidden_patterns(source)
    assert not hits, (
        f"scripts/cleaning.py contains forbidden raw-query pattern(s) {hits}; "
        "every database read must go through scripts.econ_query_api"
    )

    _assert_flows_through_api(source, "scripts/cleaning.py")
