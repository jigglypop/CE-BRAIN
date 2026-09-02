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


def find_evidence_file(name: str, *parts: str):
    """Return the first existing copy of ``<run>/<parts>`` in the search order, else None."""
    bases = (_WS / name, _WS / "_archive" / name, _RUNS / "_workspace" / "ce" / "_archive" / name)
    for base in bases:
        candidate = base.joinpath(*parts)
        if candidate.exists():
            return candidate
    return None


def evidence_file(name: str, *parts: str) -> Path:
    """Resolve one file inside a CE run with the same search order as run_dir.

    Unlike run_dir this skips only the calling test, so a module can mix
    evidence-dependent and self-contained tests.
    """
    found = find_evidence_file(name, *parts)
    if found is not None:
        return found
    try:
        import pytest
    except ImportError:
        return (_RUNS / "_workspace" / "ce" / "_archive" / name).joinpath(*parts)
    joined = "/".join(parts)
    pytest.skip(
        f"CE run evidence file '{name}/{joined}' not found "
        "(set CE_RUNS_PATH or clone ce-runs next to this repo)"
    )
