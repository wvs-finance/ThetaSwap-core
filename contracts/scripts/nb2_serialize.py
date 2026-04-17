"""Stub for the NB2 Layer 1 → Layer 2 handoff serializer.

Full implementation arrives in Task 22 of the econ-notebook-implementation
plan. That task will atomically write ``nb2_params_point.json`` (schema-
validated) and ``nb2_params_full.pkl`` (residuals + covariance matrices)
via stage-to-temp-then-rename, with handoff metadata including Python /
statsmodels / arch / numpy / pandas versions and the bootstrap-distribution
specification.

This file exists today only to reserve the import path so earlier tasks
(notebook skeletons, path constants in env.py) can reference it without a
dedicated Phase 0 follow-up. Any call raises NotImplementedError with a
Task 22 marker so failures are loud.
"""
from __future__ import annotations


def write_all(*args: object, **kwargs: object) -> None:
    """Placeholder — real implementation arrives in Task 22.

    Raises:
        NotImplementedError: Always. The message identifies Task 22 as the
            implementation target so the calling trace points to the plan.
    """
    raise NotImplementedError(
        "nb2_serialize.write_all Arrives in Task 22 of the "
        "econ-notebook-implementation plan."
    )
