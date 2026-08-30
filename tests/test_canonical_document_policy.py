"""Canonical document policy regression.

Enforces the repository contract in ``.codex/hooks/repository_harness.py``:
``paper/`` is the canonical document root, the retired document root and its
path references stay absent from active surfaces, required harness entrypoints
exist, and the instruction chain stays within budget. A green result here is a
repository-layout check, not a theoretical status.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / ".codex" / "hooks" / "repository_harness.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "repository_harness", HARNESS_PATH
    )
    assert spec is not None and spec.loader is not None, HARNESS_PATH
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_matches_canonical_document_policy():
    harness = _load_harness()
    violations = harness.check_repository(REPO_ROOT)
    assert violations == [], "\n".join(violations)
