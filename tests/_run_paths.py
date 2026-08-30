"""Resolve CE run directories across gc-archiving and the ce-runs split.

Search order: live _workspace/ce/<name> -> local _archive -> the ce-runs
evidence repo (CE_RUNS_PATH env var, default: sibling checkout ../ce-runs).
"""
import os
from pathlib import Path

_WS = Path(__file__).resolve().parents[1] / "_workspace" / "ce"
_RUNS = Path(os.environ.get("CE_RUNS_PATH", Path(__file__).resolve().parents[2] / "ce-runs"))


def run_dir(name: str) -> Path:
    live = _WS / name
    if live.exists():
        return live
    local = _WS / "_archive" / name
    if local.exists():
        return local
    external = _RUNS / "_workspace" / "ce" / "_archive" / name
    if external.exists():
        return external
    # Evidence lives only in the ce-runs sibling repo; without that checkout
    # these tests cannot run, so skip instead of failing on a missing file.
    try:
        import pytest
    except ImportError:
        return external
    pytest.skip(
        f"CE run evidence '{name}' not found (set CE_RUNS_PATH or clone ce-runs "
        f"next to this repo; looked in {_WS}, {_WS / '_archive'}, {external.parent})",
        allow_module_level=True,
    )
