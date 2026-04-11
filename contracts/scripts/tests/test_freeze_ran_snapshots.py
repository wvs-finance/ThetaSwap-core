"""Tests for freeze_ran_snapshots refactoring (Task 6).

Verifies that shared utilities are imported from ran_utils (not duplicated),
tick functions are stubs raising NotImplementedError, and read_storage_at
accepts rpc_url as parameter.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import types
from typing import Final
from unittest.mock import patch, MagicMock

import pytest


# ── B-F1: Import, don't duplicate ────────────────────────────────────────────

_EXTRACTED_NAMES: Final[tuple[str, ...]] = (
    "keccak_mapping_slot",
    "to_hex256",
    "read_storage_at",
)


def _get_module_source(module_name: str) -> str:
    """Return the source code of a module without importing it."""
    spec = importlib.util.find_spec(module_name)
    assert spec is not None and spec.origin is not None
    with open(spec.origin) as f:
        return f.read()


def _local_function_names(source: str) -> set[str]:
    """Return set of top-level function names defined in source via AST."""
    tree = ast.parse(source)
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and isinstance(
            # only top-level defs (parent is Module)
            tree.body[tree.body.index(node)] if node in tree.body else None,
            ast.FunctionDef,
        )
    }


def _top_level_function_names(source: str) -> set[str]:
    """Return set of top-level ``def`` names (direct children of Module)."""
    tree = ast.parse(source)
    return {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }


class TestImportDontDuplicate:
    """B-F1: freeze_ran_snapshots must import shared utils, not define them."""

    def test_no_local_definitions(self) -> None:
        """keccak_mapping_slot, to_hex256, read_storage_at must NOT be
        defined as functions inside freeze_ran_snapshots."""
        source = _get_module_source("scripts.freeze_ran_snapshots")
        local_defs = _top_level_function_names(source)
        for name in _EXTRACTED_NAMES:
            assert name not in local_defs, (
                f"{name} is still defined locally in freeze_ran_snapshots — "
                f"it should be imported from scripts.ran_utils"
            )

    def test_importable_from_ran_utils(self) -> None:
        """The three utilities must be importable from scripts.ran_utils
        (possibly under their ran_utils canonical names)."""
        from scripts import ran_utils

        # derive_pool_rewards_slot replaces keccak_mapping_slot
        assert callable(getattr(ran_utils, "derive_pool_rewards_slot", None))
        # encode_uint256 replaces to_hex256
        assert callable(getattr(ran_utils, "encode_uint256", None))
        # read_storage_at is the same name
        assert callable(getattr(ran_utils, "read_storage_at", None))

    def test_freeze_imports_from_ran_utils(self) -> None:
        """freeze_ran_snapshots must contain an import statement pulling
        from scripts.ran_utils."""
        source = _get_module_source("scripts.freeze_ran_snapshots")
        tree = ast.parse(source)
        imports_from_ran_utils = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and "ran_utils" in node.module
        ]
        assert len(imports_from_ran_utils) > 0, (
            "freeze_ran_snapshots has no 'from ... ran_utils import ...' statement"
        )

        # Verify the three names are imported (directly or aliased)
        imported_names: set[str] = set()
        for imp in imports_from_ran_utils:
            for alias in imp.names:
                imported_names.add(alias.name)
                if alias.asname:
                    imported_names.add(alias.asname)

        # Must import derive_pool_rewards_slot (or alias keccak_mapping_slot)
        assert "derive_pool_rewards_slot" in imported_names or "keccak_mapping_slot" in imported_names
        # Must import encode_uint256 (or alias to_hex256)
        assert "encode_uint256" in imported_names or "to_hex256" in imported_names
        # Must import read_storage_at
        assert "read_storage_at" in imported_names

    def test_read_storage_at_uses_rpc_url_param(self) -> None:
        """read_storage_at must accept rpc_url as a parameter and pass it
        to ``cast storage --rpc-url``."""
        from scripts.ran_utils import read_storage_at

        mock_result = MagicMock()
        mock_result.stdout = "0x" + "0" * 63 + "1"

        with patch("scripts.ran_utils.subprocess.run", return_value=mock_result) as mock_run:
            result = read_storage_at(
                address="0xdeadbeef",
                slot=42,
                block=12345,
                rpc_url="https://eth-mainnet.g.alchemy.com/v2/test-key",
            )
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "cast" in cmd
            assert "storage" in cmd
            assert "--rpc-url" in cmd
            assert "https://eth-mainnet.g.alchemy.com/v2/test-key" in cmd

    def test_main_constructs_rpc_from_alchemy_key(self) -> None:
        """main() must build the RPC URL from ALCHEMY_API_KEY env var,
        not fall back to ETH_RPC_URL."""
        source = _get_module_source("scripts.freeze_ran_snapshots")
        # Must reference ALCHEMY_API_KEY
        assert "ALCHEMY_API_KEY" in source, (
            "main() must use ALCHEMY_API_KEY to construct the RPC URL"
        )
        # Must NOT fall back to ETH_RPC_URL
        tree = ast.parse(source)
        # Check main() function body doesn't reference ETH_RPC_URL
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_source = ast.get_source_segment(source, node)
                assert main_source is not None
                assert "ETH_RPC_URL" not in main_source, (
                    "main() must NOT fall back to ETH_RPC_URL — clean break"
                )


# ── B-U4: Tick functions NOT in ran_utils ────────────────────────────────────

_TICK_NAMES: Final[tuple[str, ...]] = (
    "tick_to_uint24",
    "read_current_tick",
    "compute_growth_inside",
)


class TestTickFunctionsNotInRanUtils:
    """B-U4: tick functions must NOT be importable from scripts.ran_utils."""

    @pytest.mark.parametrize("name", _TICK_NAMES)
    def test_not_in_ran_utils(self, name: str) -> None:
        from scripts import ran_utils

        assert not hasattr(ran_utils, name), (
            f"{name} must NOT exist in ran_utils — tick functions are out of scope"
        )


# ── B-F2: Tick function stubs ────────────────────────────────────────────────


class TestTickFunctionStubs:
    """B-F2: tick functions exist in freeze_ran_snapshots as callables
    that raise NotImplementedError."""

    @pytest.mark.parametrize("name", _TICK_NAMES)
    def test_exists_as_callable(self, name: str) -> None:
        from scripts import freeze_ran_snapshots

        fn = getattr(freeze_ran_snapshots, name, None)
        assert fn is not None, f"{name} must exist in freeze_ran_snapshots"
        assert callable(fn), f"{name} must be callable"

    def test_tick_to_uint24_raises(self) -> None:
        from scripts.freeze_ran_snapshots import tick_to_uint24

        with pytest.raises(NotImplementedError):
            tick_to_uint24(199890)

    def test_read_current_tick_raises(self) -> None:
        from scripts.freeze_ran_snapshots import read_current_tick

        with pytest.raises(NotImplementedError):
            read_current_tick("0xdeadbeef", 12345)

    def test_compute_growth_inside_raises(self) -> None:
        from scripts.freeze_ran_snapshots import compute_growth_inside

        with pytest.raises(NotImplementedError):
            compute_growth_inside(100, 50, 60, 10, -10, 20)
