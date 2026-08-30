"""Shared pytest guards for CE run evidence.

Many tests read frozen artifacts from _workspace/ce or the ce-runs evidence
repo. When such a file is absent (fresh checkout, payload never committed),
the test cannot run at all, so report it as an explicit skip instead of a
FileNotFoundError failure. Missing files outside the evidence roots still
fail normally.
"""
from pathlib import Path

import pytest

from _run_paths import _RUNS, _WS

_EVIDENCE_ROOTS = (_WS, _RUNS / "_workspace" / "ce")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except FileNotFoundError as error:
        missing = Path(error.filename) if error.filename else None
        if missing is not None and any(
            str(missing).startswith(str(root)) for root in _EVIDENCE_ROOTS
        ):
            pytest.skip(
                f"CE run evidence file missing: {missing} "
                "(populate ce-runs next to this repo or set CE_RUNS_PATH)"
            )
        raise
