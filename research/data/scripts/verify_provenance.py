#!/usr/bin/env python3
"""Verify integrity of all frozen canonical JSON datasets.

Usage:
    cd /path/to/thetaSwap-core-dev
    uhi8/bin/python research/data/scripts/verify_provenance.py

For academic reviewers: this script verifies SHA-256 hash integrity of all
frozen datasets. Query-backed datasets include Dune/subgraph query references
that can be re-executed independently to reproduce the data.
"""
import hashlib
import json
import sys
from pathlib import Path

FROZEN_DIR = Path(__file__).resolve().parent.parent / "frozen"
QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def verify_hash(frozen: dict, name: str) -> bool:
    """Verify SHA-256 hash of the data payload matches metadata."""
    expected = frozen["metadata"].get("sha256")
    if not expected:
        print(f"  WARNING: {name} has no sha256 in metadata")
        return False
    actual = hashlib.sha256(canon(frozen["data"]).encode()).hexdigest()
    if actual != expected:
        print(f"  FAIL: {name} hash mismatch")
        print(f"    expected: {expected[:32]}...")
        print(f"    actual:   {actual[:32]}...")
        return False
    return True


def main():
    print("Provenance Verification Report")
    print("=" * 40)
    print()

    files = sorted(FROZEN_DIR.glob("*.json"))
    if not files:
        print("ERROR: No frozen JSON files found")
        sys.exit(1)

    passed = 0
    failed = 0

    for path in files:
        name = path.name
        frozen = json.loads(path.read_text())
        meta = frozen.get("metadata", {})
        source = meta.get("source", "unknown")

        ok = verify_hash(frozen, name)

        if ok:
            # Build status line based on source type
            if source == "derived":
                detail = "hash verified (derived, no query)"
            elif source == "frozen_original":
                recon = meta.get("reconstruction_query_id", "?")
                detail = f"hash verified (frozen_original, reconstruction: Dune {recon})"
            elif source == "dune":
                qid = meta.get("query_id", "?")
                row_count = meta.get("row_count", meta.get("event_count", "?"))
                detail = f"hash verified (Dune {qid}, {row_count} records)"
            elif source == "subgraph":
                row_count = meta.get("row_count", "?")
                detail = f"hash verified (GraphQL subgraph, {row_count} records)"
            else:
                detail = f"hash verified (source: {source})"

            print(f"  {name:<40} ✓ {detail}")
            passed += 1
        else:
            print(f"  {name:<40} ✗ HASH MISMATCH")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} datasets")

    if failed > 0:
        print("\nFAILED — hash integrity compromised")
        sys.exit(1)
    else:
        print("\nAll datasets verified successfully.")
        print("\nTo reproduce query-backed datasets:")
        print("  1. Visit https://dune.com/queries/<query_id> for each Dune-backed dataset")
        print("  2. SQL files are in research/data/queries/dune/")
        print("  3. GraphQL queries are in research/data/queries/subgraph/")


if __name__ == "__main__":
    main()
