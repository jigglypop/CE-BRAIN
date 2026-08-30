"""Shared CLI runner for the thin evaluate-and-gate bench entrypoints.

Each ``*_bench.py`` wrapper passes its ``evaluate_*`` callable here; the
runner prints the JSON payload, optionally writes it to ``--output``, and
exits 0 only when the result's ``hard_gate`` is truthy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Mapping


def bench_main(evaluate: Callable[[], Mapping[str, object]]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate()
    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0 if result["hard_gate"] else 2
